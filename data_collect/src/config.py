import os
from dataclasses import dataclass
from urllib.parse import parse_qsl


DEFAULT_INTERVAL_MINUTES = 15
DEFAULT_DATA_DIR = "data"
DEFAULT_KEY_PARAM = "serviceKey"
DEFAULT_API_KEY_ENCODED = False
DATA_INTERVAL_MINUTES = 5
DEFAULT_RETRY_COUNT = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 2
DEFAULT_GCS_PREFIX = "raw/kpx"


def load_dotenv(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            data[key] = value
    return data


def find_env_file() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, ".env")
    return env_path


def parse_api_params(params_raw: str | None) -> list[tuple[str, str]]:
    if not params_raw:
        return []
    params_raw = params_raw.strip()
    if not params_raw:
        return []
    return [(k, v) for k, v in parse_qsl(params_raw, keep_blank_values=True)]


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_url: str
    key_param: str
    data_dir: str
    api_params: list[tuple[str, str]]
    api_key_encoded: bool
    retry_count: int
    retry_backoff_seconds: int
    gcs_bucket: str | None
    gcs_prefix: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        env_path = find_env_file()
        dotenv = load_dotenv(env_path)
        api_key = os.environ.get("API_KEY") or dotenv.get("API_KEY")
        api_url = os.environ.get("API_URL") or dotenv.get("API_URL")
        api_params_raw = os.environ.get("API_PARAMS") or dotenv.get("API_PARAMS")
        api_key_encoded_raw = os.environ.get("API_KEY_ENCODED") or dotenv.get("API_KEY_ENCODED")
        gcs_bucket = os.environ.get("GCS_BUCKET") or dotenv.get("GCS_BUCKET")
        gcs_prefix = os.environ.get("GCS_PREFIX") or dotenv.get("GCS_PREFIX") or DEFAULT_GCS_PREFIX
        if not api_key:
            raise ValueError("API_KEY is missing. Set it in .env or environment variables.")
        if not api_url:
            raise ValueError("API_URL is missing. Set it in .env or environment variables.")
        return cls(
            api_key=api_key,
            api_url=api_url,
            key_param=DEFAULT_KEY_PARAM,
            data_dir=DEFAULT_DATA_DIR,
            api_params=parse_api_params(api_params_raw),
            api_key_encoded=parse_bool(api_key_encoded_raw, DEFAULT_API_KEY_ENCODED),
            retry_count=DEFAULT_RETRY_COUNT,
            retry_backoff_seconds=DEFAULT_RETRY_BACKOFF_SECONDS,
            gcs_bucket=gcs_bucket,
            gcs_prefix=gcs_prefix,
        )
