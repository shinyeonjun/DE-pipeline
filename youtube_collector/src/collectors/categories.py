"""카테고리 수집기"""
from typing import Any

from src.storage.gcs import GCSStorage
from .base import BaseCollector


class CategoriesCollector(BaseCollector):
    """YouTube 카테고리 수집기"""

    QUOTA_COST = 1

    def collect(self) -> dict[str, Any]:
        """카테고리 목록 수집 및 저장"""
        self.logger.info(f"Starting categories collection - run_id: {self.run_id}")

        region_code = self.config.youtube.region_code

        # 카테고리 조회
        response = self.youtube.get_video_categories(region_code)
        total_items = len(response.get("items", []))

        # 데이터 저장
        path = GCSStorage.build_category_path(region_code)
        uri = self.storage.upload_json(response, path)

        self.logger.info(f"Uploaded categories: {total_items} items -> {uri}")

        result = {
            "status": "success",
            "run_id": self.run_id,
            "total_items": total_items,
            "quota_cost": self.QUOTA_COST,
            "uploaded_file": uri,
        }

        self.logger.info(f"Categories collection completed: {total_items} categories")
        return result
