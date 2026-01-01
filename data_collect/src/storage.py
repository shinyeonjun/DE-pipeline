import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime

from gcs_storage import upload_bytes


def extract_base_datetimes(xml_bytes: bytes) -> list[str]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    values = []
    for node in root.findall(".//baseDatetime"):
        if node.text:
            values.append(node.text.strip())
    return values


def parse_base_datetime(value: str) -> datetime | None:
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_eia_period(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def try_parse_json(raw_bytes: bytes) -> dict | None:
    try:
        return json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def split_eia_payload_by_fueltype(payload: dict) -> dict[str, dict]:
    response = payload.get("response") or {}
    data = response.get("data") or []
    grouped: dict[str, list[dict]] = {}
    for item in data:
        fueltype = item.get("fueltype") or "unknown"
        grouped.setdefault(fueltype, []).append(item)
    result: dict[str, dict] = {}
    for fueltype, items in grouped.items():
        new_payload = dict(payload)
        new_response = dict(response)
        new_response["data"] = items
        new_payload["response"] = new_response
        result[fueltype] = new_payload
    return result


def extract_latest_dt_and_fueltypes(raw_bytes: bytes) -> tuple[datetime | None, list[str], dict[str, dict] | None]:
    payload = try_parse_json(raw_bytes)
    if payload:
        response = payload.get("response") or {}
        data = response.get("data") or []
        dts = []
        fueltypes = []
        for item in data:
            period = item.get("period")
            if period:
                dt = parse_eia_period(str(period))
                if dt:
                    dts.append(dt)
            fueltype = item.get("fueltype")
            if fueltype:
                fueltypes.append(str(fueltype))
        latest_dt = max(dts) if dts else None
        grouped = split_eia_payload_by_fueltype(payload)
        return latest_dt, sorted(set(fueltypes)), grouped

    base_values = extract_base_datetimes(raw_bytes)
    base_parsed = [parse_base_datetime(v) for v in base_values]
    base_parsed = [v for v in base_parsed if v is not None]
    latest_dt = max(base_parsed) if base_parsed else None
    return latest_dt, [], None


def save_raw(
    data_dir: str,
    raw_bytes: bytes,
    base_dt: datetime | None,
    gcs_bucket: str | None,
    gcs_prefix: str,
    fueltype_payloads: dict[str, dict] | None,
) -> list[str]:
    now = base_dt or datetime.now()
    date_part = now.strftime("%m-%d")
    time_part = now.strftime("%H")
    paths: list[str] = []

    if fueltype_payloads:
        for fueltype, payload in fueltype_payloads.items():
            filename = f"{time_part}.json"
            prefix = gcs_prefix.strip("/")
            object_name = f"{prefix}/{fueltype}/{date_part}/{filename}"
            payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if gcs_bucket:
                upload_bytes(
                    gcs_bucket, object_name, payload_bytes, content_type="application/json"
                )
                paths.append(f"gs://{gcs_bucket}/{object_name}")
            else:
                base_dir = os.path.join(data_dir, "raw", "eia", fueltype, date_part)
                os.makedirs(base_dir, exist_ok=True)
                path = os.path.join(base_dir, filename)
                if not os.path.exists(path):
                    with open(path, "wb") as f:
                        f.write(payload_bytes)
                paths.append(path)
        return paths

    filename = f"{time_part}.json"

    if gcs_bucket:
        prefix = gcs_prefix.strip("/")
        object_name = f"{prefix}/{date_part}/{filename}"
        upload_bytes(gcs_bucket, object_name, raw_bytes, content_type="application/json")
        return [f"gs://{gcs_bucket}/{object_name}"]

    base_dir = os.path.join(data_dir, "raw", "eia", date_part)
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(raw_bytes)
    return [path]
