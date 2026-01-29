"""
Trending Service - 트렌딩 비디오 비즈니스 로직
"""
from typing import List, Optional
from datetime import datetime
from app.core import supabase, BaseService
from .schemas import VideoSnapshot


class TrendingService:
    """트렌딩 비디오 서비스"""
    
    @staticmethod
    async def get_current_trending(limit: int = 50) -> tuple[List[VideoSnapshot], datetime]:
        """현재 트렌딩 TOP N"""
        data, latest_time = await BaseService.get_latest_snapshot_data('*', limit)
        
        if not data:
            return [], None
        
        videos = [VideoSnapshot(**video) for video in data]
        return videos, latest_time
    
    @staticmethod
    async def get_video_by_id(video_id: str) -> Optional[VideoSnapshot]:
        """특정 비디오 최신 정보"""
        result = supabase.table('fact_video_snapshots')\
            .select('*')\
            .eq('video_id', video_id)\
            .order('snapshot_at', desc=True)\
            .limit(1)\
            .execute()
        
        return VideoSnapshot(**result.data[0]) if result.data else None
    
    @staticmethod
    async def get_rising_videos(limit: int = 10) -> List[VideoSnapshot]:
        """급상승 비디오 (view_velocity 기준)"""
        latest_time = await BaseService.get_latest_snapshot_time()
        
        if not latest_time:
            return []
        
        # datetime을 ISO 형식 문자열로 변환
        snapshot_str = latest_time.isoformat() if isinstance(latest_time, datetime) else str(latest_time)
        
        result = supabase.table('fact_video_snapshots')\
            .select('*')\
            .eq('snapshot_at', snapshot_str)\
            .not_.is_('view_velocity', 'null')\
            .order('view_velocity', desc=True)\
            .limit(limit)\
            .execute()
        
        return [VideoSnapshot(**video) for video in result.data]

