"""YouTube 데이터 수집기 진입점"""
import argparse
import json
import logging
import sys

from src.config import Config
from src.collectors import (
    VideosCollector,
    CommentsCollector,
    CategoriesCollector,
    ChannelsCollector,
)


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# 수집기 매핑
COLLECTORS = {
    "videos": VideosCollector,
    "comments": CommentsCollector,
    "categories": CategoriesCollector,
    "channels": ChannelsCollector,
}


def parse_args() -> argparse.Namespace:
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="YouTube Data Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --job=videos      # 트렌딩 영상 수집
  python -m src.main --job=comments    # 댓글 수집
  python -m src.main --job=categories  # 카테고리 수집
  python -m src.main --job=channels    # 채널 정보 수집
        """,
    )

    parser.add_argument(
        "--job",
        type=str,
        required=True,
        choices=list(COLLECTORS.keys()),
        help="실행할 수집 작업 유형",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 저장 없이 테스트 실행",
    )

    return parser.parse_args()


def main() -> int:
    """메인 함수"""
    args = parse_args()

    logger.info(f"Starting YouTube Collector - job: {args.job}")

    try:
        # 설정 로드 및 검증
        config = Config.from_env()
        config.validate()

        # 수집기 실행
        collector_class = COLLECTORS[args.job]
        collector = collector_class(config)

        if args.dry_run:
            logger.info("Dry run mode - skipping actual collection")
            return 0

        result = collector.collect()

        # 결과 출력
        logger.info(f"Collection result:\n{json.dumps(result, indent=2, ensure_ascii=False)}")

        return 0 if result.get("status") == "success" else 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Collection failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
