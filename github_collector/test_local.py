"""GitHub Collector 로컬 테스트 (GCS 대신 로컬 파일 저장)
GCS 연동 없이 수집 로직만 테스트합니다.
수집된 데이터는 ./output 폴더에 저장됩니다.
"""
import os
import json
import gzip
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# 부모 경로 추가 (src 패키지 import를 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github import GitHubClient
from src.collectors.github import GitHubCollector
from src.models import CollectionSummary

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("LocalTest")


class LocalStorage:
    """GCS 대신 로컬 파일시스템에 저장하는 테스트용 스토리지"""
    
    def __init__(self, base_dir: str = "output"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"로컬 출력 디렉토리: {self.base_dir.absolute()}")
    
    @staticmethod
    def build_path(repo_full_name: str, filename: str) -> str:
        """Hive-style 경로 생성 (GCS와 동일한 로직)"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        safe_repo_name = repo_full_name.replace("/", "_")
        return f"raw/github/repos/repo={safe_repo_name}/date={date_str}/hour={hour_str}/{filename}"
    
    def upload_json(self, data: dict, path: str, compress: bool = True) -> str:
        """JSON 데이터를 로컬에 저장"""
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if compress:
            full_path = Path(f"{full_path}.gz" if not str(full_path).endswith(".gz") else full_path)
            with gzip.open(full_path, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        logger.info(f"저장 완료: {full_path}")
        return str(full_path)
    
    def upload_text(self, content: str, path: str) -> str:
        """텍스트 파일을 로컬에 저장"""
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"저장 완료: {full_path}")
        return str(full_path)


def main():
    """로컬 테스트 메인 함수"""
    summary = CollectionSummary(start_time=datetime.now(timezone.utc))
    
    logger.info("==========================================")
    logger.info("GitHub Collector 로컬 테스트 시작")
    logger.info("==========================================")
    
    try:
        config = Config.from_env()
        # GCS 설정 검증 스킵 (로컬 테스트이므로)
        if not config.github.token:
            raise ValueError("GITHUB_TOKEN 환경변수가 필요합니다.")
        
        gh_client = GitHubClient(config.github)
        collector = GitHubCollector(gh_client)
        storage = LocalStorage("output")  # 로컬 스토리지 사용
        
    except Exception as e:
        logger.error(f"초기화 실패: {e}")
        sys.exit(1)
    
    # 수집 대상 (테스트용: 3개만)
    if config.github.discovery_enabled:
        try:
            search_results = gh_client.search_repositories(config.github.search_query)
            target_repos = []
            for i, repo in enumerate(search_results):
                if i >= min(config.github.max_repos, 3):  # 테스트는 최대 3개
                    break
                target_repos.append(repo.full_name)
            logger.info(f"탐색 완료: {len(target_repos)}개")
        except Exception as e:
            logger.error(f"탐색 실패: {e}")
            sys.exit(1)
    else:
        target_repos = config.github.repos_to_collect[:3]  # 테스트는 최대 3개
    
    summary.total_repos = len(target_repos)
    
    # 수집 및 로컬 저장 루프
    for repo_name in target_repos:
        repo_name = repo_name.strip()
        if not repo_name:
            continue
            
        try:
            logger.info(f"수집 중: {repo_name}")
            result = collector.collect(repo_name)
            metadata = result["metadata"]
            readme_raw = result["readme"]
            
            # 로컬 저장 경로 생성
            base_path = LocalStorage.build_path(repo_name, "")
            
            # 메타데이터 저장 (JSON.gz)
            meta_path = f"{base_path}metadata.json"
            storage.upload_json(metadata.model_dump(mode='json'), meta_path, compress=True)
            
            # README 저장
            if readme_raw:
                readme_path = f"{base_path}README.md"
                storage.upload_text(readme_raw, readme_path)
            
            logger.info(f"✅ 성공: {repo_name} (⭐ {metadata.stars})")
            summary.success_count += 1
            summary.total_stars += metadata.stars
            
        except Exception as e:
            logger.error(f"❌ 실패 ({repo_name}): {e}")
            summary.fail_count += 1
    
    # 결과 요약
    summary.end_time = datetime.now(timezone.utc)
    logger.info("==========================================")
    logger.info(f"테스트 결과: 성공={summary.success_count}, 실패={summary.fail_count}")
    logger.info(f"총 스타 수: {summary.total_stars}")
    logger.info(f"소요 시간: {summary.duration_seconds:.2f}초")
    logger.info(f"출력 위치: {Path('output').absolute()}")
    logger.info("==========================================")


if __name__ == "__main__":
    main()
