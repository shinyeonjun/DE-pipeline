"""GitHub API 클라이언트 모듈"""
from github import Github, Auth
from src.config import GitHubConfig

class GitHubClient:
    """GitHub API 클라이언트 래퍼"""
    
    def __init__(self, config: GitHubConfig):
        if not config.token:
            self.client = Github()
        else:
            auth = Auth.Token(config.token)
            self.client = Github(auth=auth)
            
    def get_repo(self, repo_full_name: str):
        return self.client.get_repo(repo_full_name)
