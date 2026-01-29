"""
Trending Schemas - 트렌딩 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class VideoSnapshot(BaseModel):
    """비디오 스냅샷 데이터"""
    video_id: str
    snapshot_at: datetime
    title: str
    channel_id: str
    channel_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    published_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    is_shorts: bool = False
    view_count: int
    like_count: int
    comment_count: int
    trending_rank: int
    thumbnail_url: Optional[str] = None
    hours_since_published: Optional[int] = None
    engagement_rate: Optional[float] = None
    view_velocity: Optional[float] = None
    
    class Config:
        from_attributes = True


class TrendingResponse(BaseModel):
    """트렌딩 응답"""
    total: int
    snapshot_at: datetime
    videos: List[VideoSnapshot]

