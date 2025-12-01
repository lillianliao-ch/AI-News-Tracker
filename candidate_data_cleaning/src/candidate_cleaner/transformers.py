from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Dict, Optional

import pandas as pd

PHONE_PATTERN = re.compile(r"[^+\d]")


def normalize_phone(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    digits = PHONE_PATTERN.sub("", text)
    if len(digits) < 10:
        return None
    return digits


def normalize_datetime(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).isoformat(timespec="seconds")
        except ValueError:
            continue
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    if isinstance(parsed, pd.Timestamp):
        return parsed.isoformat(timespec="seconds")
    return None


NORMALIZERS: Dict[str, Callable[[object], Optional[str]]] = {
    "phone": normalize_phone,
    "datetime": normalize_datetime,
}
