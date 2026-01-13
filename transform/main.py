"""
Cloud Function entry point for GCS trigger
Transforms raw YouTube data and loads to Supabase
"""
import os
import json
import logging
import functions_framework
from google.cloud import storage
from supabase import create_client

from app.core.utils import extract_metadata_from_path
from app.core.database import is_file_processed, record_processed_file, get_category_map
from app.transformers import get_transformer_for_path, transform_categories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== Dependency Processing ==============

def ensure_categories_processed(supabase_client, bucket, metadata: dict):
    """
    Ensure categories are processed before videos.
    Videos need category_name mapping from dim_categories.
    """
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
