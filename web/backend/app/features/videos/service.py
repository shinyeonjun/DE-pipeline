"""
Videos Service - 비디오 상세 비즈니스 로직
"""
from typing import Optional
from app.core import supabase
from .schemas import VideoHistory, VideoHistoryPoint


class VideoService:
    """비디오 상세 정보 서비스"""
    
    @staticmethod
    async def get_video_history(video_id: str) -> Optional[VideoHistory]:
        """비디오 성장 히스토리 (시계열)"""
        result = supabase.table('fact_video_snapshots')\
            .select('snapshot_at, trending_rank, view_count, like_count, comment_count, title, channel_name')\
            .eq('video_id', video_id)\
            .order('snapshot_at')\
            .execute()
        
        if not result.data:
            return None
        
        # 히스토리 포인트 생성
        history_points = []
        for i, snapshot in enumerate(result.data):
            point = VideoHistoryPoint(
                snapshot_at=snapshot['snapshot_at'],
                trending_rank=snapshot['trending_rank'],
                view_count=snapshot['view_count'],
                like_count=snapshot['like_count'],
                comment_count=snapshot['comment_count']
            )
            
            # 성장률 계산
            if i > 0:
                prev = result.data[i-1]
                point.view_growth = snapshot['view_count'] - prev['view_count']
                point.rank_change = prev['trending_rank'] - snapshot['trending_rank']
            
            history_points.append(point)
        
        # 인사이트 계산
        first = result.data[0]
        last = result.data[-1]
        
        insights = {
            'peak_rank': min([s['trending_rank'] for s in result.data]),
            'total_view_growth': last['view_count'] - first['view_count'],
            'hours_in_trending': len(result.data),
            'avg_hourly_views': int((last['view_count'] - first['view_count']) / len(result.data)) if len(result.data) > 0 else 0
        }
        
        return VideoHistory(
            video_id=video_id,
            title=last['title'],
            channel_name=last['channel_name'],
            history=history_points,
            insights=insights
        )

