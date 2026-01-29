"""
Retrigger Failed Transforms Utility
가공에 실패한(status='error') 파일들을 다시 처리하도록 GCS 이벤트를 발생시킵니다.
"""
import os
import logging
from typing import List
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
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "DE-project-447511") # 프로젝트 ID 추가

def retrigger_failed_files():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY is missing in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    storage_client = storage.Client(project=GCP_PROJECT_ID) # 프로젝트 ID 명시
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    # 1. 실패한 파일 목록 조회
    logger.info("Fetching failed files from Supabase...")
    response = supabase.table("processed_files").select("file_path").eq("status", "error").execute()
    failed_files = response.data

    if not failed_files:
        logger.info("No failed files found. Everything is clean!")
        return

    logger.info(f"Found {len(failed_files)} failed files. Starting re-triggering...")

    for item in failed_files:
        file_path = item["file_path"]
        
        # 2. Supabase에서 해당 에러 기록 삭제 (GCF가 새로운 기록을 insert할 수 있게 함)
        try:
            supabase.table("processed_files").delete().eq("file_path", file_path).execute()
            logger.info(f"Cleared error record for: {file_path}")
        except Exception as e:
            logger.error(f"Failed to clear record for {file_path}: {e}")
            continue

        # 3. GCS 파일 Rewrite (Cloud Function 트리거 발생)
        try:
            # blob_path는 GCS 내의 경로여야 함. file_path가 전체 경로인 경우 버킷명 제외 필요
            # 보통 file_path는 raw/youtube/... 형식으로 저장됨
            blob = bucket.blob(file_path)
            if blob.exists():
                blob.rewrite(blob) # 자기 자신으로 rewrite하여 finalized 이벤트 발생
                logger.info(f"Retriggered GCF for: {file_path}")
            else:
                logger.warning(f"File not found in GCS: {file_path}")
        except Exception as e:
            logger.error(f"Failed to retrigger {file_path}: {e}")

    logger.info("Re-triggering process completed.")

if __name__ == "__main__":
    retrigger_failed_files()
