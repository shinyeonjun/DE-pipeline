import os
import xml.etree.ElementTree as ET
from datetime import datetime


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


def load_last_base_datetime(data_dir: str) -> datetime | None:
    path = os.path.join(data_dir, "raw", "kpx", "last_base_datetime.txt")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if not raw:
        return None
    return parse_base_datetime(raw)


def save_last_base_datetime(data_dir: str, base_dt_str: str) -> None:
    path = os.path.join(data_dir, "raw", "kpx", "last_base_datetime.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(base_dt_str)


def save_xml(data_dir: str, xml_bytes: bytes, base_dt: datetime | None) -> str:
    now = base_dt or datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    time_part = now.strftime("%H%M")
    base_dir = os.path.join(data_dir, "raw", "kpx", f"dt={date_part}")
    os.makedirs(base_dir, exist_ok=True)
    filename = f"{time_part}.xml"
    path = os.path.join(base_dir, filename)
    if os.path.exists(path):
        return path
    with open(path, "wb") as f:
        f.write(xml_bytes)
    return path

