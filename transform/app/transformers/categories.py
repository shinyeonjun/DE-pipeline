"""
Categories Transformer - 카테고리 데이터 변환
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.utils import load_gcs_json
from app.core.database import upsert_records

logger = logging.getLogger(__name__)


def transform_categories(client, bucket, blob_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    카테고리 데이터를 변환하여 Supabase에 저장합니다.
    
    카테고리는 거의 변경되지 않으므로 UPSERT 합니다.
    """
    raw_data = load_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    
    if not items:
        logger.warning(f"No categories found in {blob_path}")
        return {"records_count": 0}
    
    records = []
    for item in items:
        snippet = item.get("snippet", {})
        
        record = {
            "category_id": int(item.get("id", 0)),
            "category_name": snippet.get("title", "Unknown"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        records.append(record)
    
    # UPSERT (카테고리는 변경이 거의 없으므로)
    upserted = upsert_records(client, "dim_categories", records, on_conflict="category_id")
    
    logger.info(f"Transformed {len(records)} categories from {blob_path}")
    return {"records_count": upserted}
