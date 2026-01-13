"""
Categories Schemas - 카테고리 관련 데이터 모델
"""
from pydantic import BaseModel


class CategoryStats(BaseModel):
    """카테고리 통계"""
    category_name: str
    video_count: int
    avg_view_count: int
    avg_engagement_rate: float
    shorts_ratio: float
    trend: str  # "+12%", "-5%"

