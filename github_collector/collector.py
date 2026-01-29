import os
from github import Github, Auth
from typing import Dict, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubCollector:
    """
    GitHub 리포지토리 정보를 수집하고 README를 추출하는 클래스
    """
    def __init__(self, token: Optional[str] = None):
        # 토큰이 없으면 환경 변수에서 가져옴
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("GITHUB_TOKEN이 설정되지 않았습니다. API 레이트 리밋에 주의하세요.")
            self.g = Github()
        else:
            auth = Auth.Token(self.token)
            self.g = Github(auth=auth)

    def collect_repository_info(self, repo_full_name: str) -> Dict[str, Any]:
        """
        특정 리포지토리의 기본 정보와 README 내용을 수집합니다.
        
        Args:
            repo_full_name (str): 리포지토리 전체 이름 (예: 'owner/repo')
            
        Returns:
            Dict[str, Any]: 수집된 리포지토리 정보 및 README
        """
        try:
            logger.info(f"리포지토리 정보 수집 시작: {repo_full_name}")
            repo = self.g.get_repo(repo_full_name)
            
            # 기본 메타데이터 추출
            repo_info = {
                "full_name": repo.full_name,
                "name": repo.name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "topics": repo.get_topics(),
                "url": repo.html_url,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            }
            
            # README 추출
            try:
                readme_content = repo.get_readme().decoded_content.decode('utf-8')
                repo_info["readme"] = readme_content
                logger.info(f"README 추출 성공: {repo_full_name}")
            except Exception as e:
                logger.warning(f"README를 찾을 수 없습니다 ({repo_full_name}): {str(e)}")
                repo_info["readme"] = ""

            return repo_info

        except Exception as e:
            logger.error(f"리포지토리 정보 수집 중 오류 발생 ({repo_full_name}): {str(e)}")
            raise

if __name__ == "__main__":
    # 로컬 테스트용 코드
    import json
    from dotenv import load_dotenv
    load_dotenv()
    
    collector = GitHubCollector()
    # 예시 리포지토리 (본인 리포지토리나 유명한 오픈소스 등)
    test_repo = "shinyeonjun/DE-pipeline"
    try:
        data = collector.collect_repository_info(test_repo)
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
    except Exception as e:
        print(f"테스트 실패: {e}")
