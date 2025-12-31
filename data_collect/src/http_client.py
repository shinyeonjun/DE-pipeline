import time
from urllib.parse import parse_qsl, quote_plus, urlparse, urlunparse
from urllib.request import Request, urlopen


def build_url(
    base_url: str,
    key_param: str,
    api_key: str,
    extra_params: list[tuple[str, str]],
    api_key_encoded: bool,
) -> str:
    parsed = urlparse(base_url)
    base_params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)]
    merged_params = [
        (k, v) for k, v in (base_params + extra_params) if k != key_param
    ]
    query_parts = [f"{k}={quote_plus(str(v))}" for k, v in merged_params]
    if api_key_encoded:
        query_parts.append(f"{key_param}={api_key}")
    else:
        query_parts.append(f"{key_param}={quote_plus(api_key)}")
    new_query = "&".join(query_parts)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


def fetch_xml(
    url: str,
    timeout_seconds: int = 30,
    retry_count: int = 2,
    backoff_seconds: int = 2,
) -> bytes:
    attempt = 0
    while True:
        try:
            req = Request(url, headers={"User-Agent": "DE-collector/1.0"})
            with urlopen(req, timeout=timeout_seconds) as resp:
                return resp.read()
        except Exception:
            attempt += 1
            if attempt > retry_count:
                raise
            time.sleep(backoff_seconds)
