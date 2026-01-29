"""
Videos Transformer - 트렌딩 영상 데이터 변환
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.utils import load_gcs_json, parse_duration, safe_int
from app.core.database import get_category_map, insert_records

logger = logging.getLogger(__name__)


def transform_videos(client, bucket, blob_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    트렌딩 영상 데이터를 변환하여 Supabase에 저장합니다.
    
    Note: 트렌드 분석을 위해 중복 데이터도 INSERT 합니다 (upsert 아님).
    """
    raw_data = load_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    
    if not items:
        logger.warning(f"No items found in {blob_path}")
        return {"records_count": 0}
    
    # 카테고리 매핑 로드
    category_map = get_category_map(client)
    
    # 스냅샷 시간
    snapshot_time = datetime.now(timezone.utc)
    if metadata.get("date") and metadata.get("hour"):
        try:
            snapshot_time = datetime.strptime(
                f"{metadata['date']} {metadata['hour']}:00:00",
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    
    records = []
    for rank, item in enumerate(items, start=1):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        
        category_id = snippet.get("categoryId", "")
        category_name = category_map.get(str(category_id), "Unknown")
        
        published_at_str = snippet.get("publishedAt")
        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        
        # 업로드 후 경과 시간 (시간 단위)
        hours_since_published = max(1, int((snapshot_time - published_at).total_seconds() / 3600))
        
        view_count = safe_int(statistics.get("viewCount"))
        like_count = safe_int(statistics.get("likeCount"))
        comment_count = safe_int(statistics.get("commentCount"))
        duration_sec = parse_duration(content_details.get("duration"))
        
        # 참여율 (좋아요 + 댓글) / 조회수
        engagement_rate = (like_count + comment_count) / view_count if view_count > 0 else 0
        # 시간당 조회수
        view_velocity = view_count / hours_since_published
        
        record = {
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "channel_id": snippet.get("channelId"),
            "channel_name": snippet.get("channelTitle"),
            "category_id": safe_int(category_id),
            "category_name": category_name,
            "published_at": published_at_str,
            "tags": snippet.get("tags", []),
            "duration_sec": duration_sec,
            "is_shorts": duration_sec <= 60,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "trending_rank": rank,
            "snapshot_at": snapshot_time.isoformat(),
            "hours_since_published": hours_since_published,
            "engagement_rate": engagement_rate,
            "view_velocity": view_velocity,
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url")
        }
        records.append(record)
    
    # INSERT (트렌드 분석을 위해 중복 허용)
    inserted = insert_records(client, "fact_video_snapshots", records)
    
    logger.info(f"Transformed {len(records)} videos from {blob_path}")
    return {"records_count": inserted}
