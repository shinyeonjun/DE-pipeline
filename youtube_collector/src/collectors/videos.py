"""트렌딩 영상 수집기"""
from typing import Any

from src.storage.gcs import GCSStorage
from .base import BaseCollector


class VideosCollector(BaseCollector):
    """YouTube 트렌딩 영상 수집기"""

    DATA_TYPE = "videos_list"
    QUOTA_COST_PER_REQUEST = 1

    def collect(self) -> dict[str, Any]:
        """트렌딩 영상 수집 및 저장"""
        self.logger.info(f"Starting videos collection - run_id: {self.run_id}")

        region_code = self.config.youtube.region_code
        uploaded_files: list[str] = []
        total_items = 0
        page_num = 0

        for page_num, response in enumerate(self.youtube.get_trending_videos(), start=1):
            items_count = len(response.get("items", []))
            total_items += items_count

            # 페이지 데이터 저장
            path = GCSStorage.build_path(
                data_type=self.DATA_TYPE,
                region_code=region_code,
                run_id=self.run_id,
                filename=f"page_{page_num:03d}.json",
            )
            uri = self.storage.upload_json(response, path)
            uploaded_files.append(uri)

            self.logger.info(f"Uploaded page {page_num}: {items_count} items -> {uri}")

        # 메타데이터 저장
        metadata = self._create_metadata(
            endpoint="videos.list",
            params={
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": self.config.youtube.max_results,
            },
            total_pages=page_num,
            total_items=total_items,
            quota_cost=page_num * self.QUOTA_COST_PER_REQUEST,
        )

        metadata_path = GCSStorage.build_path(
            data_type=self.DATA_TYPE,
            region_code=region_code,
            run_id=self.run_id,
            filename="_metadata.json",
        )
        self.storage.upload_json(metadata, metadata_path, compress=False)

        result = {
            "status": "success",
            "run_id": self.run_id,
            "total_pages": page_num,
            "total_items": total_items,
            "uploaded_files": uploaded_files,
        }

        self.logger.info(f"Videos collection completed: {total_items} items in {page_num} pages")
        return result
