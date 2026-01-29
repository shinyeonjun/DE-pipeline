import os
import logging
from typing import Set
from google.cloud import storage
from supabase import create_client, Client
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 로드
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "plosind-youtube-raw-data")

def full_retrigger_videos():
    """
    모든 과거 트렌딩 비디오 데이터를 재가공 트리거합니다.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY is missing in .env")
        return

    # GCS 클라이언트 설정
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    logger.info("Starting FULL RE-TRIGGER for all video lists...")
    
    # videos_list 디렉토리 하위의 모든 JSON 파일 리스트업
    blobs = storage_client.list_blobs(GCS_BUCKET_NAME, prefix="raw/youtube/videos_list/")
    
    count = 0
    for blob in blobs:
        # JSON 파일만 트리거 (메타데이터 파일은 제외)
        if blob.name.endswith(".json.gz") or (blob.name.endswith(".json") and "page_" in blob.name):
            try:
                # 자기 자신으로 rewrite하여 GCF 트리거 발생
                # rewrite는 메타데이터를 보존하면서 이벤트를 발생시키는 가장 안전한 방법입니다.
                blob.rewrite(blob)
                count += 1
                if count % 10 == 0:
                    logger.info(f"Triggered {count} files...")
            except Exception as e:
                logger.error(f"Failed to trigger {blob.name}: {e}")

    logger.info(f"Successfully re-triggered TOTAL {count} files.")
    logger.info("The Cloud Function will now process these files in parallel. Check Supabase 'fact_video_snapshots' table in a few minutes.")

if __name__ == "__main__":
    full_retrigger_videos()
