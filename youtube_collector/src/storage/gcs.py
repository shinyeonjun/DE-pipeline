"""Google Cloud Storage 업로드 모듈"""
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
        """JSON 데이터를 GCS에 업로드

        Args:
            data: 업로드할 데이터
            path: GCS 객체 경로 (예: raw/youtube/videos_list/...)
            compress: gzip 압축 여부

        Returns:
            업로드된 GCS URI
        """
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
        data_type: str,
        region_code: str,
        run_id: str,
        filename: str,
        video_id: str | None = None,
    ) -> str:
        """GCS 객체 경로 생성 (Hive 스타일 파티셔닝)

        예시:
            raw/youtube/videos_list/region=KR/date=2026-01-05/hour=14/run_id=xxx/page_001.json
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")

        base_path = f"raw/youtube/{data_type}/region={region_code}/date={date_str}/hour={hour_str}"

        if video_id:
            return f"{base_path}/video_id={video_id}/{filename}"
        else:
            return f"{base_path}/run_id={run_id}/{filename}"

    @staticmethod
    def build_category_path(region_code: str) -> str:
        """카테고리 데이터 경로 (날짜별로만 저장)"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        return f"raw/youtube/video_categories/region={region_code}/date={date_str}/categories.json"

    @staticmethod
    def build_channels_path(run_id: str) -> str:
        """채널 데이터 경로"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        return f"raw/youtube/channels/date={date_str}/run_id={run_id}/channels.json"
