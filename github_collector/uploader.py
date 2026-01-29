import os
import logging
from google.cloud import storage
from typing import Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GCSUploader:
    """
    수집된 데이터를 Google Cloud Storage에 업로드하는 클래스
    """
    def __init__(self, bucket_name: Optional[str] = None):
        self.client = storage.Client()
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME")
        
    def upload_data(self, data: str, destination_blob_name: str, content_type: str = 'application/json'):
        """
        문자열 형식의 데이터를 GCS에 파일로 업로드합니다.
        
        Args:
            data (str): 업로드할 데이터 내용
            destination_blob_name (str): GCS 내 대상 경로 (예: 'raw/github/repo_info.json')
            content_type (str): 파일의 Content-Type
        """
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME이 설정되지 않았습니다.")
            
        try:
            logger.info(f"GCS 업로드 시작: {destination_blob_name} (Bucket: {self.bucket_name})")
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_string(data, content_type=content_type)
            logger.info(f"GCS 업로드 성공: {destination_blob_name}")
            
        except Exception as e:
            logger.error(f"GCS 업로드 중 오류 발생: {str(e)}")
            raise

if __name__ == "__main__":
    # 로컬 테스트용 코드 (GCP 환경이 활성화된 경우만 동작)
    from dotenv import load_dotenv
    load_dotenv()
    
    uploader = GCSUploader()
    try:
        uploader.upload_data('{"test": "data"}', 'test/test_upload.json')
    except Exception as e:
        print(f"테스트 실패 (GCP 인증 필요): {e}")
