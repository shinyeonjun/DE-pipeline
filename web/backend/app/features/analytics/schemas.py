"""
Analytics Schemas - 분석 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OverviewStats(BaseModel):
    """오버뷰 통계"""
    total_videos: int
    total_views: int
    total_likes: int
    total_comments: int
    avg_engagement_rate: float
    shorts_ratio: float
    snapshot_at: Optional[str] = None


class ChannelStat(BaseModel):
    """채널 통계"""
    channel_id: str
    channel_name: str
    video_count: int
    total_views: int
    avg_views: int


class HourlyTrend(BaseModel):
    """시간별 트렌드"""
    time: str
    avg_views: int
    avg_likes: int

