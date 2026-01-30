"""GitHub Collector 메인 컨트롤러 (V1.1 Hybrid Storage & Cloud Native)
이 모듈은 설정 로드, 클라이언트 초기화, 수집 대상 탐색 및 적재 프로세스를 오케스트레이션합니다.
Cloud Run Jobs의 안정적 종료(SIGTERM) 및 하이브리드 적재(JSON+MD)를 지원합니다.
"""
import logging
import sys
import signal
from datetime import datetime, timezone
from src.config import Config
from src.clients.github import GitHubClient
from src.collectors.github import GitHubCollector
from src.storage.gcs import GCSStorage
from src.models import CollectionSummary

# 프로덕션 서버급 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("GitHubCollector")

# 전역 상태 (Graceful Shutdown 관리를 위함)
is_running = True

def signal_handler(signum, frame):
    """SIGTERM 신호를 처리하여 진행 중인 루프를 안전하게 종료합니다."""
    global is_running
    logger.warning(f"신호 {signum} 수신. Graceful Shutdown을 시작합니다...")
    is_running = False

# SIGTERM 등 종료 신호 등록 (Cloud Run Jobs 대응)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    """GitHub 데이터 수집 파이프라인 (V1.1 Hybrid Storage)"""
    summary = CollectionSummary(start_time=datetime.now(timezone.utc))
    
    logger.info("==========================================")
    logger.info("GitHub Collector Pipeline (V1.1) 시작")
    logger.info("==========================================")

    try:
        config = Config.from_env()
        config.validate()
        
        gh_client = GitHubClient(config.github)
        collector = GitHubCollector(gh_client)
        storage = GCSStorage(config.gcp)
        
    except Exception as e:
        logger.error(f"초기화 실패 (Job 중단): {e}")
        sys.exit(1)

    # 이미 수집된 레포 목록 로드 (실행 간 중복 방지)
    already_collected = storage.load_collected_repos()
    logger.info(f"기존 수집 이력: {len(already_collected)}개")
    
    # 수집 대상 탐색 - 다양한 토픽 로테이션
    target_repos = []
    collected_set = already_collected.copy()  # 기존 이력으로 초기화
    
    # 데이터 엔지니어링 관련 다양한 토픽 리스트
    DISCOVERY_TOPICS = [
        "topic:data-engineering",
        "topic:etl",
        "topic:data-pipeline",
        "topic:apache-airflow",
        "topic:apache-spark",
        "topic:apache-kafka",
        "topic:dbt",
        "topic:data-warehouse",
        "topic:mlops",
        "topic:machine-learning",
        "topic:deep-learning",
        "topic:llm",
        "topic:rag",
        "topic:vector-database",
        "topic:kubernetes",
        "topic:devops",
    ]
    
    if config.github.discovery_enabled:
        try:
            from datetime import timedelta
            import time
            import random
            
            # 최근 7일 내 푸시된 프로젝트만
            days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # 토픽 순서 랜덤화 (매번 다른 토픽 우선순위)
            shuffled_topics = DISCOVERY_TOPICS.copy()
            random.shuffle(shuffled_topics)
            
            repos_per_topic = max(5, config.github.max_repos // len(shuffled_topics))
            
            for topic in shuffled_topics:
                if len(collected_set) >= config.github.max_repos:
                    break
                    
                # 별 수 기준 (인기순)과 최신순 번갈아 검색
                for sort_by in ["stars", "updated"]:
                    if len(collected_set) >= config.github.max_repos:
                        break
                        
                    query = f"{topic} pushed:>={days_ago} stars:>100"
                    logger.info(f"검색 중: {topic} (정렬: {sort_by})")
                    
                    try:
                        search_results = gh_client.search_repositories(query, sort=sort_by)
                        topic_count = 0
                        
                        for repo in search_results:
                            # 이미 수집된 레포는 스킵
                            if repo.full_name not in collected_set:
                                collected_set.add(repo.full_name)
                                target_repos.append(repo.full_name)
                                topic_count += 1
                                logger.debug(f"새 레포 추가: {repo.full_name}")
                                
                            if topic_count >= repos_per_topic // 2:
                                break
                            if len(collected_set) >= config.github.max_repos:
                                break
                                
                        # Rate Limit 방지: 2초 대기 (30 req/min)
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.warning(f"토픽 검색 실패 ({topic}): {e}")
                        continue
                        
            new_repos_count = len(target_repos)
            logger.info(f"다중 토픽 탐색 완료: {new_repos_count}개 신규 발견 (기존 {len(already_collected)}개 제외, 총 토픽 {len(shuffled_topics)}개)")
            
        except Exception as e:
            logger.error(f"탐색 실패: {e}")
            sys.exit(1)
    else:
        target_repos = config.github.repos_to_collect

    summary.total_repos = len(target_repos)

    # 수집 및 하이브리드 적재 루프
    for repo_name in target_repos:
        if not is_running:
            logger.warning("중단 신호 수신으로 인해 루프를 조기 종료합니다.")
            break

        repo_name = repo_name.strip()
        if not repo_name: continue
            
        try:
            # 1. 수집 (Pydantic 모델 기반 메타데이터 + 원문 README)
            result = collector.collect(repo_name)
            metadata = result["metadata"]
            readme_raw = result["readme"]

            # 2. GCS 경로 생성 (Hive-style 공유)
            # build_path는 파일명을 포함하므로 디렉토리 경로만 추출하기 위해 빈 파일명 전달
            base_path = GCSStorage.build_path(repo_name, "")
            
            # 3. 하이브리드 업로드
            # A. 메타데이터 (JSON.gz)
            meta_path = f"{base_path}metadata.json"
            storage.upload_json(metadata.model_dump(mode='json'), meta_path, compress=True)
            
            # B. README 원문 (README.md)
            if readme_raw:
                readme_path = f"{base_path}README.md"
                storage.upload_text(readme_raw, readme_path)
            
            logger.info(f"성공: {repo_name} (Hybrid 적재 완료)")
            summary.success_count += 1
            summary.total_stars += metadata.stars
            
        except Exception as e:
            logger.error(f"리포지토리 처리 실패 ({repo_name}): {e}")
            summary.fail_count += 1

    # 수집 이력 업데이트 (성공한 것만 추가)
    if summary.success_count > 0:
        # 기존 이력 + 새로 성공한 레포
        updated_collected = already_collected.copy()
        for repo_name in target_repos[:summary.success_count]:  # 성공한 만큼만
            updated_collected.add(repo_name)
        storage.save_collected_repos(updated_collected)
    
    # 최종 결과 요약
    summary.end_time = datetime.now(timezone.utc)
    logger.info("==========================================")
    logger.info(f"작업 요약: 성공={summary.success_count}, 실패={summary.fail_count}")
    logger.info(f"총 수집 스타 수: {summary.total_stars}")
    logger.info(f"누적 수집 레포 수: {len(already_collected) + summary.success_count}")
    logger.info(f"소요 시간: {summary.duration_seconds:.2f}초")
    logger.info("GitHub Collector Pipeline 종료")
    logger.info("==========================================")
    
    # 실패가 하나라도 있으면 비정상 종료 코드를 반환하여 Job 재시도 유도 가능
    if summary.fail_count > 0 and summary.success_count == 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
