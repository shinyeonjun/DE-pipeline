"""GitHub 리포지토리 README 및 메타데이터 수집 모듈 (SRE/Production 기준)"""
import logging
from typing import Dict, Any
from src.clients.github import GitHubClient

# 프로젝트 표준 로거 설정
logger = logging.getLogger(__name__)

class GitHubCollector:
    """GitHub 데이터 수집기
    
    GitHub API를 통해 리포지토리의 기본 정보(별점, 포크 등)와 
    README 콘텐츠를 수집하여 데이터 웨어하우스 적재용 스키마로 변환합니다.
    """
    
    def __init__(self, client: GitHubClient):
        self.client = client
        
    def collect(self, repo_full_name: str) -> Dict[str, Any]:
        """리포지토리 정보와 README를 수집합니다.
        
        Returns:
            Dict[str, Any]: { "metadata": RepositoryMetadata, "readme": str }
        """
        try:
            logger.info(f"데이터 수집 시작: {repo_full_name}")
            repo = self.client.get_repo(repo_full_name)
            
            # 메타데이터 수집 및 Pydantic 모델을 통한 검증 (src.models 참조)
            from src.models import RepositoryMetadata
            metadata = RepositoryMetadata(
                full_name=repo.full_name,
                name=repo.name,
                description=repo.description,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                language=repo.language,
                topics=repo.get_topics(),
                url=repo.html_url,
                updated_at=repo.updated_at,
                pushed_at=repo.pushed_at,
            )
            
            # README 추출
            readme_raw = ""
            try:
                readme_content = repo.get_readme()
                readme_raw = readme_content.decoded_content.decode('utf-8')
            except Exception as e:
                logger.warning(f"README를 찾을 수 없습니다 ({repo_full_name}): {e}")
                
            return {
                "metadata": metadata,
                "readme": readme_raw
            }
            
        except Exception as e:
            logger.error(f"리포지토리({repo_full_name}) 데이터 수집 실패: {e}")
            raise
