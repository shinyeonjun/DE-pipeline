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
    
    # 수집 대상 탐색 - 인기순 + 제외 토픽
    target_repos = []
    collected_set = already_collected.copy()  # 기존 이력으로 초기화
    
    # 제외할 토픽 (개발자에게 실질적 가치가 낮은 분야)
    EXCLUDE_TOPICS = [
        # 게임/엔터테인먼트
        "game", "games", "unity", "godot", "unreal-engine", "gamedev",
        "game-development", "game-engine", "pygame", "phaser",
        "minecraft", "roblox", "steam", "emulator", "rom",
        
        # 개인 설정/환경
        "dotfiles", "config", "configuration", "vim", "neovim", "emacs",
        "zsh", "bash", "fish-shell", "tmux", "i3", "polybar",
        
        # 목록형/이벤트성
        "awesome", "awesome-list", "curated-list", "resources",
        "hacktoberfest", "interview", "interview-questions",
        "cheatsheet", "cheat-sheet", "roadmap",
        
        # 교육/튜토리얼 (실제 프로젝트가 아닌 것)
        "tutorial", "tutorials", "course", "learning", "education",
        "coding-challenges", "leetcode", "algorithm-challenges",
        
        # 기타 제외
        "windows", "macos", "linux-desktop", "theme", "themes",
        "icons", "wallpaper", "font", "fonts",
        "telegram-bot", "discord-bot", "twitter-bot",
        "scraper", "crawler", "spider",  # 스크래퍼류
    ]
    
    # 수집할 언어 우선순위 (개발자 실무 언어)
    PRIORITY_LANGUAGES = [
        "python", "javascript", "typescript", "go", "rust",
        "java", "kotlin", "swift", "c", "cpp"
    ]
    
    if config.github.discovery_enabled:
        try:
            from datetime import timedelta
            import time
            import random
            
            # 언어 순서 랜덤화 (매 실행마다 다른 언어 우선순위)
            shuffled_langs = PRIORITY_LANGUAGES.copy()
            random.shuffle(shuffled_langs)
            logger.info(f"언어 검색 순서: {', '.join(shuffled_langs[:5])}...")
            
            # 제외 토픽 쿼리 생성
            exclude_query = " ".join([f"-topic:{t}" for t in EXCLUDE_TOPICS[:15]])  # API 쿼리 길이 제한
            
            # 탐색 조건 단계별 완화 (stars 기준, pushed 기간)
            DISCOVERY_TIERS = [
                {"stars": 500, "days": 7},    # Tier 1: 매우 인기 + 최신
                {"stars": 200, "days": 14},   # Tier 2: 인기 + 2주
                {"stars": 100, "days": 30},   # Tier 3: 중간 + 1달
            ]
            
            for tier_idx, tier in enumerate(DISCOVERY_TIERS):
                if len(target_repos) >= config.github.max_repos:
                    break
                    
                days_ago = (datetime.now(timezone.utc) - timedelta(days=tier["days"])).strftime("%Y-%m-%d")
                min_stars = tier["stars"]
                
                logger.info(f"=== 탐색 Tier {tier_idx + 1}: stars>{min_stars}, pushed>={tier['days']}일 ===")
                
                # 언어별로 검색 (다양성 확보)
                for lang in shuffled_langs:
                    if len(target_repos) >= config.github.max_repos:
                        break
                    
                    # 인기순 검색 (토픽 없이)
                    query = f"language:{lang} stars:>{min_stars} pushed:>={days_ago} {exclude_query}"
                    logger.info(f"검색 중: {lang} (Tier {tier_idx + 1})")
                    
                    try:
                        search_results = gh_client.search_repositories(query, sort="stars")
                        new_count = 0
                        
                        for repo in search_results:
                            if len(target_repos) >= config.github.max_repos:
                                break
                            
                            # 이미 수집된 레포는 스킵
                            if repo.full_name in collected_set:
                                continue
                            
                            # 제외 토픽 추가 필터링 (API 쿼리 제한 우회)
                            try:
                                repo_topics = repo.get_topics()
                                if any(t in EXCLUDE_TOPICS for t in repo_topics):
                                    continue
                            except:
                                pass  # 토픽 조회 실패 시 무시
                                
                            collected_set.add(repo.full_name)
                            target_repos.append(repo.full_name)
                            new_count += 1
                            logger.debug(f"새 레포 추가: {repo.full_name}")
                            
                        if new_count > 0:
                            logger.info(f"  → {new_count}개 신규 발견 (현재 총 {len(target_repos)}개)")
                            
                        # Rate Limit 방지: 2초 대기 (30 req/min)
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.warning(f"언어 검색 실패 ({lang}): {e}")
                        continue
                        
            new_repos_count = len(target_repos)
            logger.info(f"인기순 탐색 완료: {new_repos_count}개 신규 발견 (기존 {len(already_collected)}개 제외)")
            
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

            # 2. GCS 경로 생성 (Hive-style + 언어 파티션)
            # build_path는 파일명을 포함하므로 디렉토리 경로만 추출하기 위해 빈 파일명 전달
            base_path = GCSStorage.build_path(repo_name, "", language=metadata.language)
            
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
