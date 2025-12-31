import argparse
import logging
import os

from config import (
    AppConfig,
    DEFAULT_DATA_DIR,
    DEFAULT_KEY_PARAM,
)
from collector import Collector


def main() -> int:
    log_dir = os.path.join(DEFAULT_DATA_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "collector.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger("collector")

    parser = argparse.ArgumentParser(
        description="Collect KPX current power supply XML once per run."
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Directory to store raw XML (default: data).",
    )
    parser.add_argument(
        "--key-param",
        default=DEFAULT_KEY_PARAM,
        help="Query param name for the API key (default: serviceKey).",
    )
    args = parser.parse_args()

    try:
        config = AppConfig.from_env()
    except ValueError as exc:
        logger.error("config_error=%s", exc)
        return 1

    collector = Collector(
        api_url=config.api_url,
        api_key=config.api_key,
        key_param=args.key_param,
        data_dir=args.data_dir,
        extra_params=config.api_params,
        api_key_encoded=config.api_key_encoded,
        retry_count=config.retry_count,
        retry_backoff_seconds=config.retry_backoff_seconds,
        gcs_bucket=config.gcs_bucket,
        gcs_prefix=config.gcs_prefix,
        timeout_seconds=config.timeout_seconds,
    )

    try:
        path = collector.collect_once(debug=True)
    except Exception as exc:
        logger.exception("collect_failed error=%s", exc)
        return 1
    logger.info("saved=%s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
