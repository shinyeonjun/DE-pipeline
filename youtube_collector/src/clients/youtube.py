"""YouTube Data API v3 클라이언트"""
from typing import Any, Generator
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import YouTubeConfig


class YouTubeClient:
    """YouTube Data API v3 클라이언트"""

    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, config: YouTubeConfig):
        self.config = config
        self._client = build(
            self.API_SERVICE_NAME,
            self.API_VERSION,
            developerKey=config.api_key,
        )

    def get_trending_videos(
        self,
        region_code: str | None = None,
        max_results: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """트렌딩 영상 목록 조회 (페이지네이션 지원)"""
        region = region_code or self.config.region_code
        limit = max_results or self.config.max_results
        page_token = None

        while True:
            try:
                response = self._client.videos().list(
                    part="snippet,contentDetails,statistics",
                    chart="mostPopular",
                    regionCode=region,
                    maxResults=min(limit, 50),
                    pageToken=page_token,
                ).execute()

                yield response

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as e:
                raise YouTubeAPIError(f"Failed to fetch trending videos: {e}") from e

    def get_video_comments(
        self,
        video_id: str,
        max_pages: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """영상 댓글 조회 (페이지네이션 지원)"""
        pages = max_pages or self.config.comment_max_pages
        page_token = None
        page_count = 0

        while page_count < pages:
            try:
                response = self._client.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=100,
                    pageToken=page_token,
                    textFormat="plainText",
                ).execute()

                yield response
                page_count += 1

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as e:
                if e.resp.status == 403:
                    # 댓글 비활성화된 영상
                    break
                raise YouTubeAPIError(f"Failed to fetch comments for {video_id}: {e}") from e

    def get_video_categories(
        self,
        region_code: str | None = None,
    ) -> dict[str, Any]:
        """영상 카테고리 목록 조회"""
        region = region_code or self.config.region_code

        try:
            response = self._client.videoCategories().list(
                part="snippet",
                regionCode=region,
            ).execute()

            return response

        except HttpError as e:
            raise YouTubeAPIError(f"Failed to fetch categories: {e}") from e

    def get_channels(
        self,
        channel_ids: list[str],
    ) -> dict[str, Any]:
        """채널 정보 조회 (최대 50개)"""
        try:
            response = self._client.channels().list(
                part="snippet,statistics,contentDetails",
                id=",".join(channel_ids[:50]),
            ).execute()

            return response

        except HttpError as e:
            raise YouTubeAPIError(f"Failed to fetch channels: {e}") from e


class YouTubeAPIError(Exception):
    """YouTube API 호출 에러"""
    pass
