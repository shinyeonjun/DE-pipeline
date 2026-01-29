"""환경변수 및 애플리케이션 설정 관리 모듈 (SRE/Production 기준)"""
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List

# 프로젝트 표준 로거 설정
logger = logging.getLogger(__name__)

def setup_credentials() -> None:
    """GCP 서비스 어카운트 인증 설정"""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        logger.info(f"인증 파일 경로 설정됨: {creds_path}")

@dataclass
class GitHubConfig:
    """GitHub API 관련 설정 정보를 담는 데이터 클래스"""
    token: str
    repos_to_collect: List[str]
    discovery_enabled: bool = False
    search_query: str = ""
    max_repos: int = 10

@dataclass
class GCPConfig:
    """Google Cloud Platform(GCS) 관련 설정 정보를 담는 데이터 클래스"""
    project_id: str
    bucket_name: str

@dataclass
class Config:
    """애플리케이션의 모든 설정을 통합 관리하는 클래스"""
    github: GitHubConfig
    gcp: GCPConfig

    @classmethod
    def from_env(cls) -> "Config":
        """환경변수(.env)에서 설정값을 읽어와 Config 객체를 생성합니다."""
        load_dotenv()
        setup_credentials()

        # GitHub 상세 설정
        github = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN", ""),
            # 쉼표 구분자 리스트 처리
            repos_to_collect=[r.strip() for r in os.getenv("REPOS_TO_COLLECT", "").split(",") if r.strip()],
            discovery_enabled=os.getenv("GITHUB_DISCOVERY_ENABLED", "false").lower() == "true",
            search_query=os.getenv("GITHUB_SEARCH_QUERY", "topic:data-engineering stars:>1000"),
            max_repos=int(os.getenv("GITHUB_MAX_REPOS", "10")),
        )

        # GCP 상세 설정
        gcp = GCPConfig(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
            bucket_name=os.getenv("GCS_BUCKET_NAME", ""),
        )

        return cls(github=github, gcp=gcp)

    def validate(self) -> None:
        """필수 설정값들이 누락되지 않았는지 검증"""
        # 1. GitHub Token 필수 체크
        if not self.github.token:
            raise ValueError("GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
        
        # 2. GCP Project ID 및 Bucket Name 필수 체크
        if not self.gcp.project_id:
            raise ValueError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")
        if not self.gcp.bucket_name:
            raise ValueError("GCS_BUCKET_NAME 환경변수가 설정되지 않았습니다.")

        # 3. 수집 모드별 상호 보완 체크
        # 자율 탐색 모드가 꺼져있는데 수집할 리스트도 없다면 오류
        if not self.github.discovery_enabled and not self.github.repos_to_collect:
            raise ValueError("수집할 리포지토리 리스트(REPOS_TO_COLLECT)가 비어있거나 자율 탐색 모드가 꺼져있습니다.")
        
        # 자율 탐색 모드인데 검색 쿼리가 없다면 오류
        if self.github.discovery_enabled and not self.github.search_query:
            raise ValueError("자율 탐색 모드가 활성화되었으나 GITHUB_SEARCH_QUERY가 설정되지 않았습니다.")
