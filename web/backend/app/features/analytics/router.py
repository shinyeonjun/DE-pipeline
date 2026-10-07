"""
Analytics Router - 분석 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from app.core.errors import internal_error
from typing import Dict, List
from .service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview_stats() -> Dict:
    """오버뷰 대시보드 통계"""
    try:
        stats = await AnalyticsService.get_overview_stats()
        return stats
    
    except Exception as e:
        raise internal_error("analytics.get_overview_stats") from e


@router.get("/top-channels")
async def get_top_channels(limit: int = 6) -> List[Dict]:
    """상위 채널 (트렌딩 빈도)"""
    try:
        channels = await AnalyticsService.get_top_channels(limit)
        return channels
    
    except Exception as e:
        raise internal_error("analytics.get_top_channels") from e


@router.get("/hourly-trends")
async def get_hourly_trends(hours: int = 24) -> List[Dict]:
    """시간별 트렌드"""
    try:
        trends = await AnalyticsService.get_hourly_trends(hours)
        return trends
    
    except Exception as e:
        raise internal_error("analytics.get_hourly_trends") from e

