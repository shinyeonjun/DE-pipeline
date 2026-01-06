"""
Cloud Function entry point for GCS trigger
Transforms raw YouTube data and loads to Supabase
"""
import os
import re
import json
import gzip
import logging
import functions_framework
from datetime import datetime, timezone
from google.cloud import storage
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== Utility Functions ==============

def parse_duration(duration_str: str) -> int:
    """Convert ISO 8601 duration to seconds (PT3M5S -> 185)"""
    if not duration_str:
        return 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def safe_int(value, default=0):
    if value is None:
        return default
    try:
        return int(value)
    except:
        return default


def read_gcs_json(bucket, blob_path: str) -> dict:
    """Read JSON or JSON.GZ file from GCS"""
    blob = bucket.blob(blob_path)
    content = blob.download_as_bytes()

    if blob_path.endswith(".gz"):
        content = gzip.decompress(content)

    return json.loads(content.decode("utf-8"))


def extract_metadata_from_path(path: str) -> dict:
    """Extract metadata from GCS path"""
    metadata = {}

    date_match = re.search(r"date=(\d{4}-\d{2}-\d{2})", path)
    if date_match:
        metadata["date"] = date_match.group(1)

    hour_match = re.search(r"hour=(\d{2})", path)
    if hour_match:
        metadata["hour"] = hour_match.group(1)

    region_match = re.search(r"region=(\w+)", path)
    if region_match:
        metadata["region"] = region_match.group(1)

    video_id_match = re.search(r"video_id=([^/]+)", path)
    if video_id_match:
        metadata["video_id"] = video_id_match.group(1)

    run_id_match = re.search(r"run_id=([^/]+)", path)
    if run_id_match:
        metadata["run_id"] = run_id_match.group(1)

    if metadata.get("date") and metadata.get("hour"):
        metadata["snapshot_at"] = f"{metadata['date']}T{metadata['hour']}:00:00Z"
    elif metadata.get("date"):
        metadata["snapshot_at"] = f"{metadata['date']}T00:00:00Z"

    metadata["collected_at"] = metadata.get("snapshot_at")
    return metadata


# ============== Category Map (Cached) ==============

CATEGORY_MAP = {}

def get_category_map(supabase_client) -> dict:
    """Get category_id -> category_name mapping from Supabase"""
    global CATEGORY_MAP
    if CATEGORY_MAP:
        return CATEGORY_MAP

    try:
        result = supabase_client.table("dim_categories").select("category_id, category_name").execute()
        for row in result.data:
            CATEGORY_MAP[row["category_id"]] = row["category_name"]
        logger.info(f"Loaded {len(CATEGORY_MAP)} categories")
    except Exception as e:
        logger.warning(f"Could not load category map: {e}")

    return CATEGORY_MAP


# ============== Transform Functions ==============

def transform_videos(supabase_client, bucket, blob_path: str, metadata: dict) -> dict:
    """Transform videos_list -> fact_video_snapshots"""
    raw_data = read_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    snapshot_at = metadata.get("snapshot_at", datetime.now(timezone.utc).isoformat())

    category_map = get_category_map(supabase_client)

    records = []
    for rank, item in enumerate(items, start=1):
        video_id = item.get("id")
        if not video_id:
            continue

        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})
        statistics = item.get("statistics", {})

        published_at = snippet.get("publishedAt")
        duration_sec = parse_duration(content_details.get("duration", ""))
        view_count = safe_int(statistics.get("viewCount"))
        like_count = safe_int(statistics.get("likeCount"))
        comment_count = safe_int(statistics.get("commentCount"))
        category_id = safe_int(snippet.get("categoryId"))

        is_shorts = duration_sec <= 60

        # Hours since published
        hours_since_published = 0
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                hours_since_published = int((now - pub_dt).total_seconds() / 3600)
            except:
                pass

        engagement_rate = (like_count + comment_count) / view_count if view_count > 0 else 0
        view_velocity = view_count / hours_since_published if hours_since_published > 0 else 0

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", {}).get("url")

        records.append({
            "video_id": video_id,
            "snapshot_at": snapshot_at,
            "title": snippet.get("title", "")[:500],
            "channel_id": snippet.get("channelId"),
            "channel_name": snippet.get("channelTitle", "")[:200],
            "category_id": category_id,
            "category_name": category_map.get(category_id, "Unknown"),
            "published_at": published_at,
            "duration_sec": duration_sec,
            "is_shorts": is_shorts,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "trending_rank": rank,
            "thumbnail_url": thumbnail_url,
            "tags": json.dumps(snippet.get("tags", [])),
            "hours_since_published": hours_since_published,
            "engagement_rate": round(engagement_rate, 6),
            "view_velocity": round(view_velocity, 2),
        })

    if records:
        supabase_client.table("fact_video_snapshots").upsert(
            records, on_conflict="video_id,snapshot_at"
        ).execute()

    logger.info(f"Upserted {len(records)} video records")
    return {"table": "fact_video_snapshots", "records_count": len(records)}


def transform_comments(supabase_client, bucket, blob_path: str, metadata: dict) -> dict:
    """Transform comment_threads -> fact_comments"""
    raw_data = read_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    collected_at = datetime.now(timezone.utc).isoformat()

    records = []
    for item in items:
        comment_id = item.get("id")
        if not comment_id:
            continue

        snippet = item.get("snippet", {})
        top_comment = snippet.get("topLevelComment", {}).get("snippet", {})

        video_id = metadata.get("video_id") or top_comment.get("videoId")
        text_display = top_comment.get("textDisplay", "")
        author_name = top_comment.get("authorDisplayName", "")
        author_channel_id = top_comment.get("authorChannelId", {}).get("value")

        video_channel_id = snippet.get("channelId")
        is_channel_owner = author_channel_id == video_channel_id if author_channel_id and video_channel_id else False

        records.append({
            "comment_id": comment_id,
            "video_id": video_id,
            "author_name": author_name[:200] if author_name else None,
            "author_channel_id": author_channel_id,
            "text_display": text_display,
            "like_count": safe_int(top_comment.get("likeCount")),
            "reply_count": safe_int(snippet.get("totalReplyCount")),
            "published_at": top_comment.get("publishedAt"),
            "is_channel_owner": is_channel_owner,
            "text_length": len(text_display),
            "collected_at": collected_at,
        })

    if records:
        supabase_client.table("fact_comments").upsert(
            records, on_conflict="comment_id"
        ).execute()

    logger.info(f"Upserted {len(records)} comment records")
    return {"table": "fact_comments", "records_count": len(records)}


def transform_categories(supabase_client, bucket, blob_path: str, metadata: dict) -> dict:
    """Transform video_categories -> dim_categories"""
    raw_data = read_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])

    records = []
    for item in items:
        category_id = item.get("id")
        if not category_id:
            continue

        snippet = item.get("snippet", {})
        records.append({
            "category_id": safe_int(category_id),
            "category_name": snippet.get("title", "Unknown")[:100],
        })

    if records:
        supabase_client.table("dim_categories").upsert(
            records, on_conflict="category_id"
        ).execute()

        # Reset cache
        global CATEGORY_MAP
        CATEGORY_MAP = {}

    logger.info(f"Upserted {len(records)} category records")
    return {"table": "dim_categories", "records_count": len(records)}


def transform_channels(supabase_client, bucket, blob_path: str, metadata: dict) -> dict:
    """Transform channels -> dim_channels"""
    raw_data = read_gcs_json(bucket, blob_path)
    items = raw_data.get("items", [])
    updated_at = datetime.now(timezone.utc).isoformat()

    records = []
    for item in items:
        channel_id = item.get("id")
        if not channel_id:
            continue

        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", {}).get("url")

        records.append({
            "channel_id": channel_id,
            "channel_name": snippet.get("title", "")[:200],
            "custom_url": snippet.get("customUrl", "")[:100] if snippet.get("customUrl") else None,
            "description": snippet.get("description"),
            "subscriber_count": safe_int(statistics.get("subscriberCount")),
            "total_view_count": safe_int(statistics.get("viewCount")),
            "video_count": safe_int(statistics.get("videoCount")),
            "country": snippet.get("country", "")[:10] if snippet.get("country") else None,
            "channel_created_at": snippet.get("publishedAt"),
            "thumbnail_url": thumbnail_url,
            "updated_at": updated_at,
        })

    if records:
        supabase_client.table("dim_channels").upsert(
            records, on_conflict="channel_id"
        ).execute()

    logger.info(f"Upserted {len(records)} channel records")
    return {"table": "dim_channels", "records_count": len(records)}


# ============== Router ==============

TRANSFORMERS = {
    "videos_list": transform_videos,
    "comment_threads": transform_comments,
    "video_categories": transform_categories,
    "channels": transform_channels,
}


def get_transformer_for_path(path: str):
    """Determine which transformer to use based on GCS path"""
    for key, transformer in TRANSFORMERS.items():
        if f"/{key}/" in path:
            return transformer, key
    return None, None


# ============== File Processing Tracking ==============

def is_file_processed(supabase_client, file_path: str) -> bool:
    """Check if file has already been processed successfully"""
    try:
        result = supabase_client.table("processed_files").select("status").eq("file_path", file_path).execute()
        if result.data:
            return result.data[0]["status"] == "success"
    except Exception as e:
        logger.warning(f"Could not check processed status: {e}")
    return False


def record_processed_file(supabase_client, file_path: str, status: str, data_type: str,
                          records_count: int = 0, error_message: str = None, metadata: dict = None):
    """Record file processing result"""
    try:
        supabase_client.table("processed_files").upsert({
            "file_path": file_path,
            "status": status,
            "data_type": data_type,
            "records_count": records_count,
            "error_message": error_message,
            "metadata": json.dumps(metadata) if metadata else None,
        }, on_conflict="file_path").execute()
    except Exception as e:
        logger.error(f"Could not record processed file: {e}")


# ============== Dependency Processing ==============

def ensure_categories_processed(supabase_client, bucket, metadata: dict):
    """
    Ensure categories are processed before videos.
    Videos need category_name mapping from dim_categories.
    """
    global CATEGORY_MAP

    # If category map already has data, skip
    if CATEGORY_MAP:
        return

    # Try to load from Supabase first
    category_map = get_category_map(supabase_client)
    if category_map:
        return

    # No categories in DB - try to find and process category file
    logger.info("No categories found in DB. Looking for category file to process first...")

    try:
        # Find category file in the same date partition
        date = metadata.get("date")
        region = metadata.get("region", "KR")

        if date:
            prefix = f"raw/youtube/video_categories/region={region}/date={date}/"
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=1))

            if blobs:
                cat_blob_path = blobs[0].name
                if not is_file_processed(supabase_client, cat_blob_path):
                    logger.info(f"Processing category file first: {cat_blob_path}")
                    cat_metadata = extract_metadata_from_path(cat_blob_path)
                    result = transform_categories(supabase_client, bucket, cat_blob_path, cat_metadata)
                    record_processed_file(
                        supabase_client, cat_blob_path, "success", "video_categories",
                        records_count=result.get("records_count", 0),
                        metadata=cat_metadata
                    )
                    logger.info(f"Category file processed: {result}")
    except Exception as e:
        logger.warning(f"Could not pre-process categories: {e}")


# ============== Cloud Function Entry Point ==============

@functions_framework.cloud_event
def transform_handler(cloud_event):
    """
    Cloud Function triggered by GCS file upload

    Triggered by:
    - gs://plosind-youtube-raw-data/raw/youtube/videos_list/...
    - gs://plosind-youtube-raw-data/raw/youtube/comment_threads/...
    - gs://plosind-youtube-raw-data/raw/youtube/video_categories/...
    - gs://plosind-youtube-raw-data/raw/youtube/channels/...
    """
    data = cloud_event.data
    bucket_name = data["bucket"]
    blob_path = data["name"]

    logger.info(f"Processing file: gs://{bucket_name}/{blob_path}")

    # Skip metadata files and non-json files
    if blob_path.endswith("_metadata.json"):
        logger.info(f"Skipping metadata file: {blob_path}")
        return {"status": "skipped", "reason": "metadata file"}

    if not (blob_path.endswith(".json") or blob_path.endswith(".json.gz")):
        logger.info(f"Skipping non-json file: {blob_path}")
        return {"status": "skipped", "reason": "not json"}

    # Get transformer
    transformer_func, data_type = get_transformer_for_path(blob_path)
    if not transformer_func:
        logger.warning(f"No transformer found for path: {blob_path}")
        return {"status": "skipped", "reason": "no transformer"}

    # Initialize clients
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    gcp_project = os.environ.get("GCP_PROJECT_ID", "deproject-482905")

    gcs_client = storage.Client(project=gcp_project)
    bucket = gcs_client.bucket(bucket_name)
    supabase_client = create_client(supabase_url, supabase_key)

    # Check if already processed
    if is_file_processed(supabase_client, blob_path):
        logger.info(f"File already processed: {blob_path}")
        return {"status": "skipped", "reason": "already processed"}

    # Extract metadata from path
    metadata = extract_metadata_from_path(blob_path)
    logger.info(f"Extracted metadata: {metadata}")

    # Ensure categories are processed before videos (for category_name mapping)
    if data_type == "videos_list":
        ensure_categories_processed(supabase_client, bucket, metadata)

    # Transform and load
    try:
        result = transformer_func(supabase_client, bucket, blob_path, metadata)

        # Record success
        record_processed_file(
            supabase_client, blob_path, "success", data_type,
            records_count=result.get("records_count", 0),
            metadata=metadata
        )

        logger.info(f"Transform complete: {result}")
        return {"status": "success", **result}
    except Exception as e:
        # Record error
        record_processed_file(
            supabase_client, blob_path, "error", data_type,
            error_message=str(e),
            metadata=metadata
        )

        logger.error(f"Transform failed: {e}")
        return {"status": "error", "error": str(e)}


# ============== Local Testing ==============

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python main.py <gcs_blob_path>")
        print("Example: python main.py raw/youtube/videos_list/region=KR/date=2026-01-05/hour=05/run_id=xxx/page_001.json.gz")
        sys.exit(1)

    blob_path = sys.argv[1]
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "plosind-youtube-raw-data")

    # Simulate cloud event
    class FakeCloudEvent:
        data = {"bucket": bucket_name, "name": blob_path}

    result = transform_handler(FakeCloudEvent())
    print(f"Result: {result}")
