import argparse
import time

from config import (
    AppConfig,
    DEFAULT_DATA_DIR,
    DEFAULT_INTERVAL_MINUTES,
    DEFAULT_KEY_PARAM,
)
from collector import Collector


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect KPX current power supply XML at a fixed interval."
    )
    parser.add_argument("--once", action="store_true", help="Run a single collection and exit.")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help="Interval in minutes (default: 15).",
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
        print(f"ERROR: {exc}")
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
    )

    def run_collection():
        path = collector.collect_once(debug=True)
        print(f"Saved: {path}")

    if args.once:
        run_collection()
        return 0

    interval_seconds = max(60, args.interval_minutes * 60)
    print(
        f"Starting collection every {args.interval_minutes} minutes. "
        f"Saving to {args.data_dir}."
    )
    while True:
        start = time.time()
        try:
            run_collection()
        except Exception as exc:
            print(f"ERROR: {exc}")
        elapsed = time.time() - start
        sleep_seconds = max(5, interval_seconds - elapsed)
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
