"""
Trigger Missing Transforms Utility
Supabase에 기록이 없는(에러 후 삭제된) GCS 파일들만 골라서 다시 처리합니다.
"""
import os
import logging
from typing import List, Set
from supabase import create_client, Client
from google.cloud import storage
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 로드
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "plosind-youtube-raw-data")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "deproject-482905")

def trigger_missing_files():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY is missing in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # GCS 클라이언트 설정 (자동 프로젝트 감지 시도)
    try:
        import google.auth
        _, auto_project_id = google.auth.default()
        used_project_id = GCP_PROJECT_ID or auto_project_id
        logger.info(f"Using GCS Project ID: {used_project_id}")
        storage_client = storage.Client(project=used_project_id)
    except Exception as e:
        logger.warning(f"Auto project detection failed: {e}. Falling back to default.")
        storage_client = storage.Client()

    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    # 1. Supabase에서 성공한 파일 목록 가져오기 (메모리 최적화를 위해 경로셋 확보)
    logger.info("Fetching processed file paths from Supabase...")
    # 전체를 가져오기보다 최근 날짜 위주로 필터링
    response = supabase.table("processed_files").select("file_path").execute()
    processed_paths: Set[str] = {item["file_path"] for item in response.data}
    logger.info(f"Loaded {len(processed_paths)} processed paths from Supabase.")

    # 2. GCS에서 1월 12~13일 데이터 리스트업
    target_dates = ["2026-01-12", "2026-01-13"]
    missing_files = []

    logger.info(f"Scanning GCS for target dates: {target_dates}")
    # raw/youtube/ 하위의 모든 파일을 훑습니다.
    blobs = storage_client.list_blobs(GCS_BUCKET_NAME, prefix="raw/youtube/")
    
    for blob in blobs:
        # 경로에 타겟 날짜가 포함되어 있고
        if any(date_str in blob.name for date_str in target_dates):
            # Supabase 기록에 없으면 (즉, 에러였거나 누락된 경우)
            if blob.name not in processed_paths:
                missing_files.append(blob.name)

    if not missing_files:
        logger.info("No missing files found for the target dates.")
        return

    logger.info(f"Found {len(missing_files)} missing files. Starting re-trigger...")

    # 3. 트리거 (Rewrite)
    for file_path in missing_files:
        try:
            blob = bucket.blob(file_path)
            blob.rewrite(blob)
            logger.info(f"Successfully re-triggered: {file_path}")
        except Exception as e:
            logger.error(f"Failed to re-trigger {file_path}: {e}")

    logger.info(f"Completed re-triggering {len(missing_files)} files.")

if __name__ == "__main__":
    trigger_missing_files()
