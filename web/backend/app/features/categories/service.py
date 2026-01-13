"""
Categories Service - 카테고리 비즈니스 로직
"""
from typing import List, Dict
from collections import defaultdict
from app.core import BaseService
from .schemas import CategoryStats


class CategoryService:
    """카테고리 통계 서비스"""
    
    # 캐시 (같은 스냅샷에 대해 중복 계산 방지)
    _stats_cache: Dict[str, List[CategoryStats]] = {}
    
    @staticmethod
    async def get_category_stats() -> List[CategoryStats]:
        """카테고리별 통계 계산"""
        # 최신 스냅샷 데이터 조회 (중복 쿼리 제거)
        data, latest_time = await BaseService.get_latest_snapshot_data(
            'category_name, view_count, engagement_rate, is_shorts', 
            50
        )
        
        if not data:
            return []
        
        # 캐시 확인
        cache_key = str(latest_time) if latest_time else 'none'
        if cache_key in CategoryService._stats_cache:
            return CategoryService._stats_cache[cache_key]
        
        # 이미 가져온 데이터 사용 (중복 쿼리 제거)
        # 카테고리별 집계
        category_map: Dict[str, dict] = defaultdict(lambda: {
            'count': 0,
            'total_views': 0,
            'total_engagement': 0,
            'shorts_count': 0
        })
        
        for row in data:
            cat = row.get('category_name') or '기타'
            category_map[cat]['count'] += 1
            category_map[cat]['total_views'] += row.get('view_count') or 0
            category_map[cat]['total_engagement'] += row.get('engagement_rate') or 0
            category_map[cat]['shorts_count'] += 1 if row.get('is_shorts') else 0
        
        # 통계 객체 생성
        stats = []
        for cat, cat_data in category_map.items():
            if cat_data['count'] == 0:
                continue
            
            stats.append(CategoryStats(
                category_name=cat,
                video_count=cat_data['count'],
                avg_view_count=int(cat_data['total_views'] / cat_data['count']),
                avg_engagement_rate=round(cat_data['total_engagement'] / cat_data['count'], 2),
                shorts_ratio=round(cat_data['shorts_count'] / cat_data['count'] * 100, 1),
                trend="+0%"  # TODO: 이전 스냅샷과 비교
            ))
        
        # 비디오 수 기준 정렬
        stats.sort(key=lambda x: x.video_count, reverse=True)
        
        # 캐시 저장
        CategoryService._stats_cache[cache_key] = stats
        
        return stats
    
    @staticmethod
    async def get_category_distribution() -> Dict[str, int]:
        """카테고리별 분포 (파이 차트용)"""
        stats = await CategoryService.get_category_stats()
        return {stat.category_name: stat.video_count for stat in stats}

