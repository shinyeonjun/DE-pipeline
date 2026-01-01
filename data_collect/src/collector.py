from dataclasses import dataclass
from http_client import build_url, fetch_xml
from storage import extract_latest_dt_and_fueltypes, save_raw


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
    gcs_bucket: str | None
    gcs_prefix: str
    timeout_seconds: int

    def collect_once(self, debug: bool = False) -> str:
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
            timeout_seconds=self.timeout_seconds,
            retry_count=self.retry_count,
            backoff_seconds=self.retry_backoff_seconds,
        )
        latest_base_dt, fueltypes, fueltype_payloads = extract_latest_dt_and_fueltypes(
            xml_bytes
        )
        paths = save_raw(
            self.data_dir,
            xml_bytes,
            latest_base_dt,
            self.gcs_bucket,
            self.gcs_prefix,
            fueltype_payloads,
        )
        if len(paths) > 1:
            print(f"Saved {len(paths)} files (fueltypes={','.join(fueltypes)}).")
        path = paths[0]
        return path
