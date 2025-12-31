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


def save_xml(
    data_dir: str,
    xml_bytes: bytes,
    base_dt: datetime | None,
    gcs_bucket: str | None,
    gcs_prefix: str,
) -> str:
    now = base_dt or datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    time_part = now.strftime("%H%M")
    filename = f"{time_part}.xml"

    if gcs_bucket:
        prefix = gcs_prefix.strip("/")
        object_name = f"{prefix}/dt={date_part}/{filename}"
        upload_bytes(gcs_bucket, object_name, xml_bytes)
        return f"gs://{gcs_bucket}/{object_name}"

    base_dir = os.path.join(data_dir, "raw", "kpx", f"dt={date_part}")
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, filename)
    if os.path.exists(path):
        return path
    with open(path, "wb") as f:
        f.write(xml_bytes)
    return path
