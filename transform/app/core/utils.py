"""
Core Utilities - 경로 파싱, 데이터 변환 유틸리티
"""
import re
import gzip
import json
from typing import Any, Optional
from datetime import datetime, timezone


def extract_metadata_from_path(blob_path: str) -> dict:
    """
    GCS blob 경로에서 메타데이터를 추출합니다.
    
    Example path: raw/youtube/videos_list/region=KR/date=2026-01-05/hour=05/run_id=xxx/page_001.json.gz
    
    Returns:
        dict: region, date, hour, run_id 등의 메타데이터
    """
    metadata = {
        "blob_path": blob_path,
        "extracted_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Hive 스타일 파티션 추출 (key=value)
    patterns = {
        "region": r"region=([^/]+)",
        "date": r"date=(\d{4}-\d{2}-\d{2})",
        "hour": r"hour=(\d{2})",
        "run_id": r"run_id=([^/]+)",
        "video_id": r"video_id=([^/]+)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, blob_path)
        if match:
            metadata[key] = match.group(1)
    
    # 데이터 타입 추출
    if "videos_list" in blob_path:
        metadata["data_type"] = "videos_list"
    elif "comment_threads" in blob_path:
        metadata["data_type"] = "comment_threads"
    elif "video_categories" in blob_path:
        metadata["data_type"] = "video_categories"
    elif "channels" in blob_path:
        metadata["data_type"] = "channels"
    
    return metadata


def parse_duration(duration_str: Optional[str]) -> int:
    """
    ISO 8601 duration 문자열을 초(seconds)로 변환합니다.
    
    Example: "PT1H30M45S" -> 5445
    """
    if not duration_str:
        return 0
    
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds


def safe_int(value: Any, default: int = 0) -> int:
    """안전하게 정수로 변환합니다."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전하게 실수로 변환합니다."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_gcs_json(bucket, blob_path: str) -> dict:
    """
    GCS에서 JSON 파일을 로드합니다. gzip 압축 파일도 자동 처리합니다.
    """
    blob = bucket.blob(blob_path)
    content = blob.download_as_bytes()
    
    if blob_path.endswith(".gz"):
        content = gzip.decompress(content)
    
    return json.loads(content.decode("utf-8"))
