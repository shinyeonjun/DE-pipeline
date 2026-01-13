"""
Database Operations - Supabase 관련 DB 작업
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def is_file_processed(client, file_path: str) -> bool:
    """
    파일이 이미 처리되었는지 확인합니다.
    
    Note: 트렌드 분석을 위해 중복 데이터가 필요할 수 있으므로,
          이 함수는 기록 확인용으로만 사용하고, 스킵 결정은 호출자가 판단합니다.
    """
    try:
        result = client.table("processed_files").select("file_path").eq("file_path", file_path).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.warning(f"Could not check processed status: {e}")
        return False


def record_processed_file(
    client,
    file_path: str,
    status: str,
    data_type: str,
    records_count: int = 0,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    처리된 파일을 기록합니다.
    """
    try:
        record = {
            "file_path": file_path,
            "status": status,
            "data_type": data_type,
            "records_count": records_count,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if error_message:
            record["error_message"] = error_message
        
        if metadata:
            record["metadata"] = metadata
        
        client.table("processed_files").insert(record).execute()
        logger.info(f"Recorded processed file: {file_path} ({status})")
    except Exception as e:
        logger.error(f"Failed to record processed file: {e}")




def get_category_map(client) -> Dict[str, str]:
    """
    카테고리 ID -> 이름 매핑을 조회합니다.
    
    Returns:
        dict: {"10": "Music", "20": "Gaming", ...}
    """
    try:
        result = client.table("dim_categories").select("category_id, category_name").execute()
        return {str(row["category_id"]): row["category_name"] for row in result.data}
    except Exception as e:
        logger.warning(f"Could not load category map: {e}")
        return {}


def upsert_records(client, table_name: str, records: list, on_conflict: str = "id") -> int:
    """
    레코드를 upsert (insert or update) 합니다.
    
    Returns:
        int: 처리된 레코드 수
    """
    if not records:
        return 0
    
    try:
        result = client.table(table_name).upsert(records, on_conflict=on_conflict).execute()
        return len(result.data)
    except Exception as e:
        logger.error(f"Upsert failed for {table_name}: {e}")
        raise


def insert_records(client, table_name: str, records: list) -> int:
    """
    레코드를 insert 합니다. (중복 허용 - 트렌드 분석용)
    
    Returns:
        int: 삽입된 레코드 수
    """
    if not records:
        return 0
    
    try:
        result = client.table(table_name).insert(records).execute()
        return len(result.data)
    except Exception as e:
        logger.error(f"Insert failed for {table_name}: {e}")
        raise
