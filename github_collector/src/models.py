"""GitHub 리포지토리 데이터 모델 및 스키마 정의 (Pydantic v2)"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field

class RepositoryMetadata(BaseModel):
    """GCS에 JSON으로 저장될 리포지토리 메타데이터 스키마"""
    full_name: str = Field(..., description="리포지토리 전체 이름 (owner/repo)")
    name: str = Field(..., description="리포지토리 이름")
    description: Optional[str] = Field(None, description="리포지토리 설명")
    stars: int = Field(default=0, description="스타 수")
    forks: int = Field(default=0, description="포크 수")
    language: Optional[str] = Field(None, description="주요 사용 언어")
    topics: List[str] = Field(default_factory=list, description="리포지토리 토픽 리스트")
    url: HttpUrl = Field(..., description="GitHub 리포지토리 HTML URL")
    updated_at: Optional[datetime] = Field(None, description="최종 업데이트 시간")
    pushed_at: Optional[datetime] = Field(None, description="최종 푸시 시간")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="수집 시간 (UTC)")

class CollectionSummary(BaseModel):
    """배치 작업 종료 시 요약 보고를 위한 모델"""
    total_repos: int = 0
    success_count: int = 0
    fail_count: int = 0
    total_stars: int = 0
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
