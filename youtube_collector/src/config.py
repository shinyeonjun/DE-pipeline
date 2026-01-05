"""환경변수 설정 관리 모듈"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


def setup_credentials() -> None:
    """GCP 인증 설정"""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path


@dataclass
class YouTubeConfig:
    """YouTube API 설정"""
    api_key: str
    region_code: str
    max_results: int
    snapshot_interval_minutes: int
    comment_target_videos: int
    comment_max_pages: int


@dataclass
class GCPConfig:
    """GCP 설정"""
    project_id: str
    bucket_name: str


@dataclass
class Config:
    """전체 설정"""
    youtube: YouTubeConfig
    gcp: GCPConfig

    @classmethod
    def from_env(cls) -> "Config":
        """환경변수에서 설정 로드"""
        load_dotenv()
        setup_credentials()

        youtube = YouTubeConfig(
            api_key=os.getenv("YOUTUBE_API_KEY", ""),
            region_code=os.getenv("YOUTUBE_REGION_CODE", "KR"),
            max_results=int(os.getenv("YOUTUBE_MAX_RESULTS", "50")),
            snapshot_interval_minutes=int(os.getenv("YOUTUBE_SNAPSHOT_INTERVAL_MINUTES", "60")),
            comment_target_videos=int(os.getenv("YOUTUBE_COMMENT_TARGET_VIDEOS_PER_SNAPSHOT", "5")),
            comment_max_pages=int(os.getenv("YOUTUBE_COMMENT_MAX_PAGES_PER_VIDEO", "2")),
        )

        gcp = GCPConfig(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
            bucket_name=os.getenv("GCS_BUCKET_NAME", ""),
        )

        return cls(youtube=youtube, gcp=gcp)

    def validate(self) -> None:
        """필수 설정 검증"""
        if not self.youtube.api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        if not self.gcp.project_id:
            raise ValueError("GCP_PROJECT_ID is required")
        if not self.gcp.bucket_name:
            raise ValueError("GCS_BUCKET_NAME is required")
