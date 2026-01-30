"""Google Cloud Storage(GCS) 업로드 및 경로 관리 모듈 (SRE/Production 기준)"""
import gzip
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Set, List
from google.cloud import storage
from src.config import GCPConfig

# 프로젝트 표준 로거 설정
logger = logging.getLogger(__name__)

# 수집 이력 파일 경로 (중복 방지용)
COLLECTED_INDEX_PATH = "metadata/collected_repos.json"

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

    def load_collected_repos(self) -> Set[str]:
        """이미 수집된 레포지토리 목록을 GCS에서 로드합니다.
        
        Returns:
            Set[str]: 이미 수집된 레포지토리 이름 집합
        """
        try:
            blob = self._bucket.blob(COLLECTED_INDEX_PATH)
            if blob.exists():
                content = blob.download_as_string().decode("utf-8")
                data = json.loads(content)
                repos = set(data.get("repos", []))
                logger.info(f"수집 이력 로드 완료: {len(repos)}개 레포 존재")
                return repos
            else:
                logger.info("수집 이력 파일 없음 - 새로 시작")
                return set()
        except Exception as e:
            logger.warning(f"수집 이력 로드 실패 (빈 세트로 시작): {e}")
            return set()
    
    def save_collected_repos(self, repos: Set[str]) -> None:
        """수집된 레포지토리 목록을 GCS에 저장합니다.
        
        Args:
            repos: 수집된 레포지토리 이름 집합
        """
        try:
            data = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(repos),
                "repos": sorted(list(repos))  # 정렬하여 저장
            }
            blob = self._bucket.blob(COLLECTED_INDEX_PATH)
            blob.upload_from_string(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type="application/json"
            )
            logger.info(f"수집 이력 저장 완료: {len(repos)}개 레포")
        except Exception as e:
            logger.error(f"수집 이력 저장 실패: {e}")

    def list_existing_repos(self) -> Set[str]:
        """GCS 버킷에서 실제 저장된 레포지토리 목록을 스캔합니다.
        
        Note: 대규모 버킷에서는 비용 발생 가능. 인덱스 파일 우선 권장.
        """
        repos = set()
        try:
            # raw/github/date=*/repo=* 패턴에서 레포명 추출
            blobs = self._bucket.list_blobs(prefix="raw/github/")
            for blob in blobs:
                # 경로: raw/github/date=2026-01-30/repo=owner_name/metadata.json.gz
                parts = blob.name.split("/")
                for part in parts:
                    if part.startswith("repo="):
                        repo_name = part.replace("repo=", "").replace("_", "/", 1)
                        repos.add(repo_name)
                        break
            logger.info(f"GCS 스캔 완료: {len(repos)}개 레포 발견")
        except Exception as e:
            logger.warning(f"GCS 스캔 실패: {e}")
        return repos

    @staticmethod
    def build_path(
        repo_full_name: str,
        filename: str,
        language: str = None,
    ) -> str:
        """데이터 분석 최적화를 위한 Hive 스타일 파티셔닝 경로를 생성합니다.
        
        생성 규칙 (언어 파티션 포함):
            raw/github/lang=언어/date=YYYY-MM-DD/repo=리포지토리명/파일명
        
        Args:
            repo_full_name (str): 리포지토리 전체 이름 (예: owner/repo)
            filename (str): 저장될 파일 이름
            language (str): 프로그래밍 언어 (예: Python, JavaScript)
            
        Returns:
            str: 생성된 GCS 물리 경로
        """
        # 현재 시간 기준 파티션 정보 추출 (UTC 프로젝트 표준)
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        
        # 파일 시스템에서 안전하게 사용할 수 있도록 경로 구분자(/)를 언더바(_)로 변환
        safe_repo_name = repo_full_name.replace("/", "_")
        
        # 언어 정규화 (소문자, 공백 제거, None 처리)
        if language:
            safe_lang = language.lower().replace(" ", "_").replace("#", "sharp")
        else:
            safe_lang = "unknown"
        
        return f"raw/github/lang={safe_lang}/date={date_str}/repo={safe_repo_name}/{filename}"

