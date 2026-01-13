"""댓글 수집기"""
from typing import Any

from src.storage.gcs import GCSStorage
from .base import BaseCollector


class CommentsCollector(BaseCollector):
    """YouTube 댓글 수집기"""

    DATA_TYPE = "comment_threads"
    QUOTA_COST_PER_REQUEST = 1

    def collect(self) -> dict[str, Any]:
        """트렌딩 영상의 댓글 수집 및 저장"""
        self.logger.info(f"Starting comments collection - run_id: {self.run_id}")

        region_code = self.config.youtube.region_code
        target_video_count = self.config.youtube.comment_target_videos

        # 먼저 트렌딩 영상 목록 가져오기
        video_ids = self._get_trending_video_ids(target_video_count)

        if not video_ids:
            self.logger.warning("No trending videos found")
            return {"status": "no_videos", "run_id": self.run_id}

        results: list[dict[str, Any]] = []
        total_comments = 0
        total_requests = 0

        for video_id in video_ids:
            video_result = self._collect_video_comments(video_id, region_code)
            results.append(video_result)
            total_comments += video_result["total_items"]
            total_requests += video_result["pages"]

        result = {
            "status": "success",
            "run_id": self.run_id,
            "videos_processed": len(video_ids),
            "total_comments": total_comments,
            "quota_cost": total_requests * self.QUOTA_COST_PER_REQUEST,
            "video_results": results,
        }

        self.logger.info(
            f"Comments collection completed: {total_comments} comments from {len(video_ids)} videos"
        )
        return result

    def _get_trending_video_ids(self, limit: int) -> list[str]:
        """트렌딩 영상 ID 목록 가져오기"""
        video_ids: list[str] = []

        for response in self.youtube.get_trending_videos(max_results=limit):
            for item in response.get("items", []):
                video_ids.append(item["id"])
                if len(video_ids) >= limit:
                    return video_ids

        return video_ids

    def _collect_video_comments(
        self,
        video_id: str,
        region_code: str,
    ) -> dict[str, Any]:
        """단일 영상의 댓글 수집"""
        self.logger.info(f"Collecting comments for video: {video_id}")

        uploaded_files: list[str] = []
        total_items = 0
        page_num = 0

        try:
            for page_num, response in enumerate(
                self.youtube.get_video_comments(video_id), start=1
            ):
                items_count = len(response.get("items", []))
                total_items += items_count

                # 페이지 데이터 저장
                path = GCSStorage.build_path(
                    data_type=self.DATA_TYPE,
                    region_code=region_code,
                    run_id=self.run_id,
                    filename=f"page_{page_num:03d}.json",
                    video_id=video_id,
                )
                uri = self.storage.upload_json(response, path)
                uploaded_files.append(uri)

            # 메타데이터 저장
            if page_num > 0:
                metadata = self._create_metadata(
                    endpoint="commentThreads.list",
                    params={"videoId": video_id, "maxResults": 100},
                    total_pages=page_num,
                    total_items=total_items,
                    quota_cost=page_num * self.QUOTA_COST_PER_REQUEST,
                )

                metadata_path = GCSStorage.build_path(
                    data_type=self.DATA_TYPE,
                    region_code=region_code,
                    run_id=self.run_id,
                    filename="_metadata.json",
                    video_id=video_id,
                )
                self.storage.upload_json(metadata, metadata_path, compress=False)

        except Exception as e:
            self.logger.warning(f"Failed to collect comments for {video_id}: {e}")
            return {
                "video_id": video_id,
                "status": "failed",
                "error": str(e),
                "pages": 0,
                "total_items": 0,
            }

        return {
            "video_id": video_id,
            "status": "success",
            "pages": page_num,
            "total_items": total_items,
            "uploaded_files": uploaded_files,
        }
