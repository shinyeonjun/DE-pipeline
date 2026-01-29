"""GitHub Collector 메인 실행 모듈"""
import logging
from src.config import Config
from src.clients.github import GitHubClient
from src.collectors.github import GitHubCollector
from src.storage.gcs import GCSStorage

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GitHubCollector")

def main():
    """메인 실행 함수"""
    # 1. 설정 로드
    config = Config.from_env()
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        return

    # 2. 클라이언트 및 스토리지 초기화
    gh_client = GitHubClient(config.github)
    collector = GitHubCollector(gh_client)
    storage = GCSStorage(config.gcp)

    # 3. 수집 시작
    logger.info(f"수집 시작 대상: {config.github.repos_to_collect}")
    
    for repo_name in config.github.repos_to_collect:
        repo_name = repo_name.strip()
        if not repo_name:
            continue
            
        try:
            # 데이터 수집
            data = collector.collect(repo_name)
            
            # GCS 경로 생성 및 업로드
            path = GCSStorage.build_path(repo_name, "readme_info.json")
            uri = storage.upload_json(data, path, compress=True)
            
            logger.info(f"수집 및 업로드 완료: {repo_name} -> {uri}")
            
        except Exception as e:
            logger.error(f"리포지토리 처리 실패 ({repo_name}): {e}")

if __name__ == "__main__":
    main()
