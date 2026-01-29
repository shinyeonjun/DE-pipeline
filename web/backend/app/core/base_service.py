"""
Base Service - 공통 서비스 로직 (캐싱 포함)
"""
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from .database import supabase


class BaseService:
    """공통 서비스 로직 (캐싱 포함)"""
    
    # 클래스 레벨 캐시
    _latest_snapshot_time: Optional[datetime] = None
    _latest_snapshot_data: Optional[List[Dict[str, Any]]] = None
    _cache_timestamp: Optional[datetime] = None
    _CACHE_DURATION_SECONDS = 5  # 5초 캐시
    
    _cached_schema: Optional[str] = None
    _schema_cache_timestamp: Optional[datetime] = None
    _SCHEMA_CACHE_DURATION_HOURS = 1 # 1시간 캐시
    
    @classmethod
    async def get_latest_snapshot_time(cls) -> Optional[datetime]:
        """최신 스냅샷 시간 조회 (캐시 적용)"""
        now = datetime.now()
        
        # 캐시 확인
        if cls._latest_snapshot_time and cls._cache_timestamp:
            elapsed = (now - cls._cache_timestamp).total_seconds()
            if elapsed < cls._CACHE_DURATION_SECONDS:
                return cls._latest_snapshot_time
        
        # DB 조회
        result = supabase.table('fact_video_snapshots')\
            .select('snapshot_at')\
            .order('snapshot_at', desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            snapshot_str = result.data[0]['snapshot_at']
            # ISO 형식 문자열을 datetime으로 변환
            if isinstance(snapshot_str, str):
                cls._latest_snapshot_time = datetime.fromisoformat(snapshot_str.replace('Z', '+00:00'))
            else:
                cls._latest_snapshot_time = snapshot_str
            cls._cache_timestamp = now
            return cls._latest_snapshot_time
        
        return None
    
    @classmethod
    async def get_latest_snapshot_data(cls, fields: str = '*', limit: int = 50) -> Tuple[List[Dict[str, Any]], Optional[datetime]]:
        """최신 스냅샷 데이터 조회 (캐시 적용)"""
        latest_time = await cls.get_latest_snapshot_time()
        
        if not latest_time:
            return [], None
        
        # 캐시 확인 (같은 필드, 같은 limit)
        cache_key = f"{fields}_{limit}"
        now = datetime.now()
        if cls._latest_snapshot_data and cls._cache_timestamp:
            elapsed = (now - cls._cache_timestamp).total_seconds()
            if elapsed < cls._CACHE_DURATION_SECONDS:
                return cls._latest_snapshot_data, latest_time
        
        # DB 조회
        result = supabase.table('fact_video_snapshots')\
            .select(fields)\
            .eq('snapshot_at', latest_time.isoformat() if isinstance(latest_time, datetime) else latest_time)\
            .order('trending_rank')\
            .limit(limit)\
            .execute()
        
        cls._latest_snapshot_data = result.data
        cls._cache_timestamp = now
        
        return result.data, latest_time
    
    @classmethod
    def clear_cache(cls):
        """캐시 초기화"""
        cls._latest_snapshot_time = None
        cls._latest_snapshot_data = None
        cls._cache_timestamp = None
        cls._cached_schema = None
        cls._schema_cache_timestamp = None

    @classmethod
    async def get_ai_view_schema(cls) -> str:
        """AI 관련 View의 스키마 정보를 실시간으로 조회하여 텍스트로 반환 (Self-Healing)"""
        now = datetime.now()
        
        # 캐시 확인
        if cls._cached_schema and cls._schema_cache_timestamp:
            elapsed = (now - cls._schema_cache_timestamp).total_seconds()
            if elapsed < (cls._SCHEMA_CACHE_DURATION_HOURS * 3600):
                return cls._cached_schema

        try:
            # information_schema에서 ai_로 시작하는 뷰의 칼럼 정보 조회
            result = supabase.rpc('get_ai_view_schema_info').execute()
            
            if not result.data:
                return ""
            
            # VIEW_CATALOG에서 설명(description) 매핑을 위해 가져옴 (순환 참조 방지 위해 로컬 임포트)
            from app.features.chat.views import VIEW_CATALOG
            
            schema_lines = []
            for item in result.data:
                table_name = item['table_name']
                columns = item['column_names']
                
                # 기존 카탈로그에서 설명 찾기
                description = "세부 분석 데이터"
                for info in VIEW_CATALOG.values():
                    if info.name == table_name:
                        description = info.description
                        break
                
                schema_lines.append(f"- **{table_name}**: {description}")
                schema_lines.append(f"  컬럼: {', '.join(columns)}")
            
            cls._cached_schema = "\n".join(schema_lines)
            cls._schema_cache_timestamp = now
            return cls._cached_schema
        except Exception as e:
            print(f"[BaseService] 스키마 조회 실패: {e}")
            return ""


