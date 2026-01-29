"""Google Cloud Storage(GCS) 업로드 및 경로 관리 모듈 (SRE/Production 기준)"""
import gzip
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from google.cloud import storage
from src.config import GCPConfig

# 프로젝트 표준 로거 설정
logger = logging.getLogger(__name__)

class GCSStorage:
    """GCS 스토리지 엔지니어링 클래스
    
    데이터 적재 시 Hive 스타일의 파티셔닝 구조를 생성하고,
    네트워크 비용 및 저장 효율을 위해 Gzip 압축 업로드를 지원합니다.
    """

    def __init__(self, config: GCPConfig):
        self.config = config
        # Google Cloud Storage 클라이언트 초기화 (애플리케이션 디폴트 인증 활용)
        self._client = storage.Client(project=config.project_id)
        self._bucket = self._client.bucket(config.bucket_name)

    def upload_json(
        self,
        data: Dict[str, Any],
        path: str,
        compress: bool = True,
    ) -> str:
        """JSON 데이터를 GCS 버킷에 업로드합니다."""
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

    def upload_text(
        self,
        content: str,
        path: str,
        content_type: str = "text/markdown",
    ) -> str:
        """일반 텍스트(Markdown 등) 데이터를 GCS 버킷에 업로드합니다."""
        blob = self._bucket.blob(path)
        blob.upload_from_string(content.encode("utf-8"), content_type=content_type)

        logger.info(f"GCS 텍스트 업로드 성공: {path} (Type: {content_type})")
        return f"gs://{self.config.bucket_name}/{path}"

    @staticmethod
    def build_path(
        repo_full_name: str,
        filename: str,
    ) -> str:
        """데이터 분석 최적화를 위한 Hive 스타일 파티셔닝 경로를 생성합니다.
        
        생성 규칙:
            raw/github/repos/repo=리포지토리명/date=YYYY-MM-DD/hour=HH/파일명
        
        Args:
            repo_full_name (str): 리포지토리 전체 이름 (예: owner/repo)
            filename (str): 저장될 파일 이름
            
        Returns:
            str: 생성된 GCS 물리 경로
        """
        # 현재 시간 기준 파티션 정보 추출 (UTC 프로젝트 표준)
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        
        # 파일 시스템에서 안전하게 사용할 수 있도록 경로 구분자(/)를 언더바(_)로 변환
        safe_repo_name = repo_full_name.replace("/", "_")
        
        return f"raw/github/repos/repo={safe_repo_name}/date={date_str}/hour={hour_str}/{filename}"
