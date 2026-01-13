"""
Analytics Service - 대시보드 분석 비즈니스 로직
"""
from typing import Dict, List
from datetime import datetime
from app.core import supabase, BaseService


class AnalyticsService:
    """대시보드 분석 서비스"""
    
    @staticmethod
    async def get_overview_stats() -> Dict:
        """오버뷰 통계"""
        data, latest_time = await BaseService.get_latest_snapshot_data('*', 50)
        
        if not data:
            return {}
        
        # 직접 데이터 사용 (불필요한 객체 생성 제거)
        total_views = sum(v.get('view_count') or 0 for v in data)
        total_likes = sum(v.get('like_count') or 0 for v in data)
        total_comments = sum(v.get('comment_count') or 0 for v in data)
        
        engagement_rates = [v['engagement_rate'] for v in data if v.get('engagement_rate')]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
        
        shorts_count = sum(1 for v in data if v.get('is_shorts'))
        shorts_ratio = (shorts_count / len(data)) * 100 if data else 0
        
        return {
            'total_videos': len(data),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'avg_engagement_rate': round(avg_engagement, 2),
            'shorts_ratio': round(shorts_ratio, 1),
            'snapshot_at': latest_time.isoformat() if isinstance(latest_time, datetime) else latest_time
        }
    
    @staticmethod
    async def get_top_channels(limit: int = 6) -> List[Dict]:
        """상위 채널 (트렌딩 빈도 기준)"""
        data, _ = await BaseService.get_latest_snapshot_data('channel_id, channel_name, view_count', 50)
        
        if not data:
            return []
        
        # 직접 데이터 사용
        channel_stats = {}
        for row in data:
            ch_id = row.get('channel_id')
            if not ch_id:
                continue
                
            if ch_id not in channel_stats:
                channel_stats[ch_id] = {
                    'channel_id': ch_id,
                    'channel_name': row.get('channel_name', 'Unknown'),
                    'video_count': 0,
                    'total_views': 0
                }
            
            channel_stats[ch_id]['video_count'] += 1
            channel_stats[ch_id]['total_views'] += row.get('view_count') or 0
        
        # 평균 계산 및 정렬
        for ch in channel_stats.values():
            ch['avg_views'] = int(ch['total_views'] / ch['video_count']) if ch['video_count'] > 0 else 0
        
        top_channels = sorted(channel_stats.values(), key=lambda x: x['video_count'], reverse=True)[:limit]
        return top_channels
    
    @staticmethod
    async def get_hourly_trends(hours: int = 24) -> List[Dict]:
        """시간별 트렌드 (최근 N시간)"""
        result = supabase.table('fact_video_snapshots')\
            .select('snapshot_at, view_count, like_count')\
            .order('snapshot_at', desc=True)\
            .limit(hours * 50)\
            .execute()
        
        if not result.data:
            return []
        
        hourly_map = {}
        for row in result.data:
            hour = row['snapshot_at'][:13]
            if hour not in hourly_map:
                hourly_map[hour] = {
                    'time': hour,
                    'total_views': 0,
                    'total_likes': 0,
                    'count': 0
                }
            
            hourly_map[hour]['total_views'] += row['view_count'] or 0
            hourly_map[hour]['total_likes'] += row['like_count'] or 0
            hourly_map[hour]['count'] += 1
        
        trends = []
        for hour, data in sorted(hourly_map.items()):
            trends.append({
                'time': hour,
                'avg_views': int(data['total_views'] / data['count']),
                'avg_likes': int(data['total_likes'] / data['count'])
            })
        
        return trends[-hours:]

