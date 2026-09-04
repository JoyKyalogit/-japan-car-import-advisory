"""Download and parse the official KPA Tariff Book PDF."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pdfplumber
import requests

from src.config import settings

logger = logging.getLogger(__name__)

KPA_TARIFF_URL = (
    "https://portal.kpa.co.ke/web-uploads/documents/"
    "80299801-e056-4c46-a3dd-2454c8a42a33.pdf"
)

# Map app body types to KPA tariff weight classes (Clause 13.3 + 17.15, domestic import).
BODY_TO_KPA_TIER = {
    "Hatchback": "tier1",
    "Sedan": "tier1",
    "Coupe": "tier1",
    "Wagon": "tier1",
    "Minivan": "tier2",
    "SUV": "tier2",
    "Pickup": "tier2",
    "Van": "tier2",
}

DEFAULT_TIERS = {
    "tier1": {
        "label": "Saloon, Station Wagon, Van, CUV not exceeding 1.5 MT",
        "stevedoring_usd": 80.0,
        "wharfage_usd": 75.0,
    },
    "tier2": {
        "label": "Station Wagon, Pick-up, SUV, CUV not exceeding 2.0 MT",
        "stevedoring_usd": 105.0,
        "wharfage_usd": 90.0,
    },
    "tier3": {
        "label": "Mid sized Truck, Minibus, Tractor not exceeding 5.0 MT",
        "stevedoring_usd": 200.0,
        "wharfage_usd": 200.0,
    },
}


def download_kpa_tariff_pdf(url: str = KPA_TARIFF_URL) -> bytes:
    logger.info("Downloading KPA tariff PDF from %s", url)
    response = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content


def _extract_tier_rates(text: str) -> dict[str, dict[str, float | str]]:
    tiers = {key: value.copy() for key, value in DEFAULT_TIERS.items()}

    patterns = {
        "tier1": r"Saloon, Station Wagon, Van, CUV not exceeding 1\.5 MT\s+\$?([\d.]+)",
        "tier2": r"Station Wagon, Pick-up, SUV, CUV not exceeding 2\.0 MT\s+\$?([\d.]+)",
        "tier3": r"Mid[- ]sized Truck, Minibus, Tractor not exceeding 5\.0 MT\s+\$?([\d.]+)",
    }

    stevedoring_block = re.search(
        r"13\.3 Loading and discharging of Motor Vehicles.*?13\.4",
        text,
        re.S | re.I,
    )
    wharfage_block = re.search(
        r"17\.15 Self-Propelled Units.*?17\.16",
        text,
        re.S | re.I,
    )

    if stevedoring_block:
        block = stevedoring_block.group(0)
        for tier, pattern in patterns.items():
            match = re.search(pattern, block, re.I)
            if match:
                tiers[tier]["stevedoring_usd"] = float(match.group(1))

    if wharfage_block:
        block = wharfage_block.group(0)
        for tier, pattern in patterns.items():
            match = re.search(pattern, block, re.I)
            if match:
                tiers[tier]["wharfage_usd"] = float(match.group(1))

    return tiers


def parse_kpa_tariff_pdf(content: bytes) -> dict:
    text_parts: list[str] = []
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts)
    tiers = _extract_tier_rates(text)
    return {
        "source": "KPA Tariff Book PDF",
        "url": KPA_TARIFF_URL,
        "updated_at": datetime.utcnow().isoformat(),
        "tiers": tiers,
        "body_type_map": BODY_TO_KPA_TIER,
        "notes": (
            "Port charge = stevedoring (Clause 13.3) + wharfage (Clause 17.15) "
            "for RoRo self-propelled units. Storage first 5 days free for domestic imports."
        ),
    }


def save_kpa_tariff(data: dict, path: Path | None = None) -> Path:
    path = path or settings.data_dir / "reference" / "kpa_tariff.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved KPA tariff data to %s", path)
    return path


def fetch_and_save_kpa_tariff(url: str = KPA_TARIFF_URL) -> dict:
    content = download_kpa_tariff_pdf(url)
    parsed = parse_kpa_tariff_pdf(content)
    save_kpa_tariff(parsed)
    raw_path = settings.data_dir / "reference" / "kpa_tariff_2025.pdf"
    raw_path.write_bytes(content)
    logger.info("Saved raw KPA PDF to %s", raw_path)
    return parsed
