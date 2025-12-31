from dataclasses import dataclass
from datetime import datetime, timedelta

from config import DATA_INTERVAL_MINUTES
from http_client import build_url, fetch_xml
from storage import (
    extract_base_datetimes,
    load_last_base_datetime,
    parse_base_datetime,
    save_last_base_datetime,
    save_xml,
)


@dataclass
class Collector:
    api_url: str
    api_key: str
    key_param: str
    data_dir: str
    extra_params: list[tuple[str, str]]
    api_key_encoded: bool
    retry_count: int
    retry_backoff_seconds: int

    def collect_once(self, debug: bool = False) -> str:
        last_base_dt = load_last_base_datetime(self.data_dir)
        url = build_url(
            self.api_url,
            self.key_param,
            self.api_key,
            self.extra_params,
            self.api_key_encoded,
        )
        if debug:
            masked_url = url.replace(
                self.api_key, "***" + self.api_key[-4:] if len(self.api_key) > 4 else "***"
            )
            print(f"Request URL: {masked_url}")

        xml_bytes = fetch_xml(
            url,
            retry_count=self.retry_count,
            backoff_seconds=self.retry_backoff_seconds,
        )
        base_dt_values = extract_base_datetimes(xml_bytes)
        base_dt_pairs = [(v, parse_base_datetime(v)) for v in base_dt_values]
        base_dt_pairs = [(v, dt) for v, dt in base_dt_pairs if dt is not None]
        latest_base_dt = max((dt for _, dt in base_dt_pairs), default=None)
        latest_base_dt_str = None
        if latest_base_dt and base_dt_pairs:
            for v, dt in base_dt_pairs:
                if dt == latest_base_dt:
                    latest_base_dt_str = v
                    break

        path = save_xml(self.data_dir, xml_bytes, latest_base_dt)
        if latest_base_dt_str:
            save_last_base_datetime(self.data_dir, latest_base_dt_str)

        if last_base_dt and latest_base_dt and latest_base_dt > last_base_dt:
            expected = set()
            step = timedelta(minutes=DATA_INTERVAL_MINUTES)
            cur = last_base_dt + step
            while cur <= latest_base_dt:
                expected.add(cur)
                cur += step
            got = set(dt for _, dt in base_dt_pairs)
            missing = sorted(expected - got)
            if missing:
                print(
                    f"WARNING: detected {len(missing)} missing intervals "
                    f"between {last_base_dt} and {latest_base_dt}."
                )

        return path
