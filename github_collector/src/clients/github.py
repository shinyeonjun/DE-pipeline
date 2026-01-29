"""GitHub API 클라이언트 모듈 (SRE/Production 기준)"""
from github import Github, Auth, GithubRetry
from src.config import GitHubConfig

class GitHubClient:
    """GitHub API 클라이언트 래퍼
    
    PyGithub의 GithubRetry 오브젝트를 사용하여 API 레이트 리밋 및 일시적인 네트워크 오류에 대응합니다.
    """
    
    def __init__(self, config: GitHubConfig):
        # 재시도 정책 설정: 최대 5회, 백오프 적용, 403(Rate Limit) 및 5xx 에러 대응
        retry_config = GithubRetry(
            total=5, 
            backoff_factor=2, 
            status_forcelist=[403, 500, 502, 503, 504],
            retry_on_403=True
        )
        
        if not config.token:
            # 토큰이 없는 경우 (Unauthenticated - 레이트 리밋 매우 낮음)
            self.client = Github(retry=retry_config, timeout=15)
        else:
            # 토큰 인증 사용
            auth = Auth.Token(config.token)
            self.client = Github(auth=auth, retry=retry_config, timeout=15)
            
    def get_repo(self, repo_full_name: str):
        """특정 리포지토리 객체 반환"""
        return self.client.get_repo(repo_full_name)

    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc"):
        """GitHub 리포지토리 검색 (자율 탐색 모드용)"""
        return self.client.search_repositories(query=query, sort=sort, order=order)
