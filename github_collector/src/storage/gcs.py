"""Google Cloud Storage 업로드 모듈 (GitHub 데이터용)"""
import gzip
import json
from datetime import datetime, timezone
from typing import Any
from google.cloud import storage
from src.config import GCPConfig

class GCSStorage:
    """GCS 스토리지 클라이언트"""

    def __init__(self, config: GCPConfig):
        self.config = config
        self._client = storage.Client(project=config.project_id)
        self._bucket = self._client.bucket(config.bucket_name)

    def upload_json(
        self,
        data: dict[str, Any],
        path: str,
        compress: bool = True,
    ) -> str:
        """JSON 데이터를 GCS에 업로드"""
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if compress:
            path = f"{path}.gz" if not path.endswith(".gz") else path
            content = gzip.compress(json_str.encode("utf-8"))
            content_type = "application/gzip"
        else:
            content = json_str.encode("utf-8")
            content_type = "application/json"

        blob = self._bucket.blob(path)
        blob.upload_from_string(content, content_type=content_type)

        return f"gs://{self.config.bucket_name}/{path}"

    @staticmethod
    def build_path(
        repo_full_name: str,
        filename: str,
    ) -> str:
        """GCS 객체 경로 생성 (Hive 스타일 파티셔닝)
        
        예시:
            raw/github/repos/repo=owner_repo/date=2026-01-29/hour=15/metadata.json
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        
        safe_repo_name = repo_full_name.replace("/", "_")
        
        return f"raw/github/repos/repo={safe_repo_name}/date={date_str}/hour={hour_str}/{filename}"
