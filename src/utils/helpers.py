import math
import re
from typing import Any

import pandas as pd

from src.config import settings


def jpy_to_usd(amount_jpy: float) -> float:
    return round(amount_jpy * settings.jpy_to_usd, 2)


def usd_to_jpy(amount_usd: float) -> float:
    return round(amount_usd / settings.jpy_to_usd, 0)


def usd_to_kes(amount_usd: float) -> float:
    from src.services.exchange_rate import get_usd_to_kes

    return round(amount_usd * get_usd_to_kes(), 2)


def parse_price(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(text).replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_mileage(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"([\d,]+)", str(text))
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_engine_cc(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d{3,4})", str(text))
    if match:
        return int(match.group(1))
    return None


def parse_year(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(19\d{2}|20\d{2})", str(text))
    if match:
        year = int(match.group(1))
        if 1980 <= year <= 2030:
            return year
    return None


def infer_body_type(title: str | None, model: str | None = None, seats: int | None = None) -> str | None:
    text = " ".join(filter(None, [title, model])).lower()
    if not text:
        return None

    rules = [
        ("Pickup", ("pickup", "hilux", "d-max", "ranger", "navara", "fighter", "truck", "dump")),
        ("Van", ("van", "hiace", "regiusace", "caravan", "voxy", "noah", "esquire", "alphard", "vellfire", "serena", "nv200", "stepwgn", "h1", "bus")),
        ("Minivan", ("minivan", "sienta", "roomy", "tank")),
        ("SUV", ("suv", "crossover", "rav4", "cr-v", "hr-v", "forester", "x-trail", "outlander", "pajero", "land cruiser", "prado", "harrier", "cx-5", "cx-30", "cx-3", "x5", "x3", "x1", "qashqai", "juke", "wrangler", "cherokee", "outback", "asx", "vitara", "escudo")),
        ("Wagon", ("wagon", "estate", "touring", "fielder", "levorg", "legacy touring")),
        ("Hatchback", ("hatch", "note", "fit", "aqua", "vitz", "demio", "march", "swift", "leaf", "mirage", "iQ", "bB")),
        ("Coupe", ("coupe", "convertible", "roadster", "86", "brz", "mx-5", "miata")),
        ("Sedan", ("sedan", "camry", "corolla", "civic", "accord", "mark x", "premio", "allion", "altis", "axio", "lancer")),
    ]
    for body_type, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return body_type

    if seats and seats >= 7:
        return "Van"
    return None


def normalize_make_model(title: str) -> tuple[str | None, str | None]:
    if not title:
        return None, None
    parts = title.strip().split()
    if len(parts) >= 2:
        return parts[0].title(), " ".join(parts[1:3]).title()
    if parts:
        return parts[0].title(), None
    return None, None


def parse_vehicle_title(title: str) -> tuple[int | None, str | None, str | None]:
    """Parse titles like '2009 TOYOTA VOXY ZS KIRAMEKI' into year, make, model."""
    if not title:
        return None, None, None
    parts = re.sub(r"\s+", " ", title.strip()).split()
    if len(parts) >= 3 and re.match(r"20\d{2}", parts[0]):
        return int(parts[0]), parts[1].title(), " ".join(parts[2:]).title()
    make, model = normalize_make_model(title)
    return parse_year(title), make, model


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, "", "N/A"):
            return data[key]
    return default


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def json_safe(value: Any) -> Any:
    """Convert pandas/numpy missing values and non-JSON floats to JSON-safe values."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if is_missing(value):
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value
