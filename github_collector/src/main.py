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

    # 수집 대상 탐색
    target_repos = []
    if config.github.discovery_enabled:
        try:
            search_results = gh_client.search_repositories(config.github.search_query)
            count = 0
            for repo in search_results:
                if count >= config.github.max_repos: break
                target_repos.append(repo.full_name)
                count += 1
            logger.info(f"자율 탐색 완료: {len(target_repos)}개 발견")
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

    # 최종 결과 요약
    summary.end_time = datetime.now(timezone.utc)
    logger.info("==========================================")
    logger.info(f"작업 요약: 성공={summary.success_count}, 실패={summary.fail_count}")
    logger.info(f"총 수집 스타 수: {summary.total_stars}")
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
