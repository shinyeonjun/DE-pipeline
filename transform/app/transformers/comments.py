"""
Comments Transformer - 댓글 데이터 변환
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.utils import load_gcs_json, safe_int
from app.core.database import insert_records

logger = logging.getLogger(__name__)


def transform_comments(client, bucket, blob_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    댓글 데이터를 변환하여 Supabase에 저장합니다.
    
    Note: 트렌드 분석을 위해 중복 데이터도 INSERT 합니다.
    """
    raw_data = load_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    
    if not items:
        logger.warning(f"No comments found in {blob_path}")
        return {"records_count": 0}
    
    video_id = metadata.get("video_id")
    snapshot_time = datetime.now(timezone.utc).isoformat()
    
    records = []
    for item in items:
        top_comment = item.get("snippet", {}).get("topLevelComment", {})
        snippet = top_comment.get("snippet", {})
        
        text_display = snippet.get("textDisplay", "")[:1000]
        record = {
            "comment_id": top_comment.get("id"),
            "video_id": video_id or snippet.get("videoId"),
            "author_name": snippet.get("authorDisplayName"),
            "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
            "text_display": text_display,
            "text_length": len(text_display),
            "like_count": safe_int(snippet.get("likeCount")),
            "reply_count": safe_int(item.get("snippet", {}).get("totalReplyCount")),
            "published_at": snippet.get("publishedAt"),
            "collected_at": snapshot_time,
            "is_channel_owner": snippet.get("authorIsChannelOwner", False)
        }
        records.append(record)
    
    # INSERT (트렌드 분석을 위해 중복 허용)
    inserted = insert_records(client, "fact_comments", records)
    
    logger.info(f"Transformed {len(records)} comments from {blob_path}")
    return {"records_count": inserted}
