"""수집기 베이스 클래스"""
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from src.config import Config
from src.clients.youtube import YouTubeClient
from src.storage.gcs import GCSStorage


class BaseCollector(ABC):
    """수집기 베이스 클래스"""

    def __init__(self, config: Config):
        self.config = config
        self.youtube = YouTubeClient(config.youtube)
        self.storage = GCSStorage(config.gcp)
        self.run_id = self._generate_run_id()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _generate_run_id() -> str:
        """실행 ID 생성 (타임스탬프 + UUID)"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"{timestamp}_{short_uuid}"

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """데이터 수집 실행

        Returns:
            수집 결과 요약
        """
        pass

    def _create_metadata(
        self,
        endpoint: str,
        params: dict[str, Any],
        total_pages: int,
        total_items: int,
        quota_cost: int = 1,
    ) -> dict[str, Any]:
        """수집 메타데이터 생성"""
        return {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "endpoint": endpoint,
            "params": params,
            "total_pages": total_pages,
            "total_items": total_items,
            "quota_cost": quota_cost,
        }
