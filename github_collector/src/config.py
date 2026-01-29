"""환경변수 설정 관리 모듈"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List

def setup_credentials() -> None:
    """GCP 인증 설정"""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

@dataclass
class GitHubConfig:
    """GitHub API 설정"""
    token: str
    repos_to_collect: List[str]

@dataclass
class GCPConfig:
    """GCP 설정"""
    project_id: str
    bucket_name: str

@dataclass
class Config:
    """전체 설정"""
    github: GitHubConfig
    gcp: GCPConfig

    @classmethod
    def from_env(cls) -> "Config":
        """환경변수에서 설정 로드"""
        load_dotenv()
        setup_credentials()

        github = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN", ""),
            repos_to_collect=os.getenv("REPOS_TO_COLLECT", "shinyeonjun/DE-pipeline").split(","),
        )

        gcp = GCPConfig(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
            bucket_name=os.getenv("GCS_BUCKET_NAME", ""),
        )

        return cls(github=github, gcp=gcp)

    def validate(self) -> None:
        """필수 설정 검증"""
        if not self.github.token:
            # 토큰이 없더라도 공개 리포지토리는 수집 가능할 수 있으나, 가급적 필수로 설정
            pass
        if not self.gcp.project_id:
            raise ValueError("GCP_PROJECT_ID is required")
        if not self.gcp.bucket_name:
            raise ValueError("GCS_BUCKET_NAME is required")
