"""GitHub README 및 메타데이터 수집 모듈"""
import logging
from typing import Dict, Any
from src.clients.github import GitHubClient

logger = logging.getLogger(__name__)

class GitHubCollector:
    """GitHub 데이터 수집기"""
    
    def __init__(self, client: GitHubClient):
        self.client = client
        
    def collect(self, repo_full_name: str) -> Dict[str, Any]:
        """리포지토리 정보 수집"""
        try:
            logger.info(f"수집 시작: {repo_full_name}")
            repo = self.client.get_repo(repo_full_name)
            
            data = {
                "full_name": repo.full_name,
                "name": repo.name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "topics": repo.get_topics(),
                "url": repo.html_url,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            }
            
            try:
                readme = repo.get_readme().decoded_content.decode('utf-8')
                data["readme"] = readme
            except Exception as e:
                logger.warning(f"README 없음 ({repo_full_name}): {e}")
                data["readme"] = ""
                
            return data
            
        except Exception as e:
            logger.error(f"수집 실패 ({repo_full_name}): {e}")
            raise
