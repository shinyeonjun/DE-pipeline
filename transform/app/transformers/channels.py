"""
Channels Transformer - 채널 정보 데이터 변환
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.utils import load_gcs_json, safe_int
from app.core.database import insert_records

logger = logging.getLogger(__name__)


def transform_channels(client, bucket, blob_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    채널 데이터를 변환하여 Supabase에 저장합니다.
    
    Note: 채널 성장 분석을 위해 중복 데이터도 INSERT 합니다.
    """
    raw_data = load_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    
    if not items:
        logger.warning(f"No channels found in {blob_path}")
        return {"records_count": 0}
    
    snapshot_time = datetime.now(timezone.utc).isoformat()
    
    records = []
    for item in items:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        
        record = {
            "channel_id": item.get("id"),
            "channel_name": snippet.get("title"),
            "description": snippet.get("description", "")[:500],  # 500자 제한
            "custom_url": snippet.get("customUrl"),
            "channel_created_at": snippet.get("publishedAt"),
            "country": snippet.get("country"),
            "subscriber_count": safe_int(statistics.get("subscriberCount")),
            "total_view_count": safe_int(statistics.get("viewCount")),
            "video_count": safe_int(statistics.get("videoCount")),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        records.append(record)
    
    # UPSERT (최신 채널 정보 유지)
    inserted = upsert_records(client, "dim_channels", records, on_conflict="channel_id")
    
    logger.info(f"Transformed {len(records)} channels from {blob_path}")
    return {"records_count": inserted}
