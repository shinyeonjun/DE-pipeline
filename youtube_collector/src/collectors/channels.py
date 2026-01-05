"""채널 수집기"""
from typing import Any

from src.storage.gcs import GCSStorage
from .base import BaseCollector


class ChannelsCollector(BaseCollector):
    """YouTube 채널 정보 수집기"""

    QUOTA_COST_PER_REQUEST = 1

    def collect(self) -> dict[str, Any]:
        """트렌딩 영상의 채널 정보 수집 및 저장"""
        self.logger.info(f"Starting channels collection - run_id: {self.run_id}")

        # 트렌딩 영상에서 채널 ID 추출
        channel_ids = self._get_channel_ids_from_trending()

        if not channel_ids:
            self.logger.warning("No channels found")
            return {"status": "no_channels", "run_id": self.run_id}

        # 채널 정보 조회 (50개씩 분할)
        all_channels: list[dict[str, Any]] = []
        request_count = 0

        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i : i + 50]
            response = self.youtube.get_channels(batch)
            all_channels.extend(response.get("items", []))
            request_count += 1

        # 병합된 응답 생성
        merged_response = {
            "kind": "youtube#channelListResponse",
            "items": all_channels,
        }

        # 데이터 저장
        path = GCSStorage.build_channels_path(self.run_id)
        uri = self.storage.upload_json(merged_response, path)

        self.logger.info(f"Uploaded channels: {len(all_channels)} items -> {uri}")

        # 메타데이터 저장
        metadata = self._create_metadata(
            endpoint="channels.list",
            params={"part": "snippet,statistics,contentDetails"},
            total_pages=request_count,
            total_items=len(all_channels),
            quota_cost=request_count * self.QUOTA_COST_PER_REQUEST,
        )

        metadata_path = path.replace("channels.json", "_metadata.json")
        self.storage.upload_json(metadata, metadata_path, compress=False)

        result = {
            "status": "success",
            "run_id": self.run_id,
            "total_channels": len(all_channels),
            "unique_channels": len(set(channel_ids)),
            "quota_cost": request_count * self.QUOTA_COST_PER_REQUEST,
            "uploaded_file": uri,
        }

        self.logger.info(f"Channels collection completed: {len(all_channels)} channels")
        return result

    def _get_channel_ids_from_trending(self) -> list[str]:
        """트렌딩 영상에서 고유 채널 ID 추출"""
        channel_ids: set[str] = set()

        for response in self.youtube.get_trending_videos():
            for item in response.get("items", []):
                channel_id = item.get("snippet", {}).get("channelId")
                if channel_id:
                    channel_ids.add(channel_id)

        return list(channel_ids)
