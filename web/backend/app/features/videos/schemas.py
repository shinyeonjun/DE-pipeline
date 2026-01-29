"""
Videos Schemas - 비디오 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class VideoHistoryPoint(BaseModel):
    """비디오 히스토리 포인트"""
    snapshot_at: datetime
    trending_rank: int
    view_count: int
    like_count: int
    comment_count: int
    view_growth: Optional[int] = None
    rank_change: Optional[int] = None


class VideoHistory(BaseModel):
    """비디오 성장 히스토리"""
    video_id: str
    title: str
    channel_name: str
    history: List[VideoHistoryPoint]
    insights: Dict

