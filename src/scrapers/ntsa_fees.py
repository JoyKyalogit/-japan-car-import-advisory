"""Download and parse official NTSA fee schedules from Kenya Law PDFs."""

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

TRAFFIC_RULES_URL = "https://new.kenyalaw.org/akn/ke/act/gn/1953/1902/eng@2022-12-31/source"
REGISTRATION_PLATES_URL = "https://new.kenyalaw.org/akn/ke/act/ln/2016/62/eng@2022-12-31/source"

# Fallback values from The Traffic Rules First Schedule (rev. 31 Dec 2022) and
# Traffic (Registration Plates) Rules Second Schedule (LN 62/2016).
DEFAULT_REGISTRATION_TIERS = [
    {"max_cc": 1000, "fee_kes": 1700, "label": "not exceeding 1,000 cc"},
    {"max_cc": 1200, "fee_kes": 2100, "label": "exceeding 1,000 cc but not exceeding 1,200 cc"},
    {"max_cc": 1500, "fee_kes": 2300, "label": "exceeding 1,200 cc but not exceeding 1,500 cc"},
    {"max_cc": 1700, "fee_kes": 2800, "label": "exceeding 1,500 cc but not exceeding 1,700 cc"},
    {"max_cc": 2000, "fee_kes": 3300, "label": "exceeding 1,700 cc but not exceeding 2,000 cc"},
    {"max_cc": 2500, "fee_kes": 5100, "label": "exceeding 2,000 cc but not exceeding 2,500 cc"},
    {"max_cc": 3000, "fee_kes": 7000, "label": "exceeding 2,500 cc but not exceeding 3,000 cc"},
    {"max_cc": None, "fee_kes": 8300, "label": "exceeding 3,000 cc"},
]

DEFAULT_INSPECTION_TIERS = [
    {"max_cc": 3000, "fee_kes": 2600, "label": "up to 3,000 cc"},
    {"max_cc": None, "fee_kes": 3900, "label": "over 3,000 cc"},
]

DEFAULT_PLATE_FEES = {
    "registration_plates_pair_kes": 3000,
    "third_license_kes": 700,
    "motorcycle_single_plate_kes": 1500,
}


def _download_pdf(url: str) -> bytes:
    logger.info("Downloading NTSA reference PDF from %s", url)
    response = requests.get(url, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content


def _pdf_text(content: bytes) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _parse_amount(value: str) -> int:
    return int(value.replace(",", ""))


def _parse_registration_tiers(text: str) -> list[dict]:
    tiers: list[dict] = []
    patterns = [
        (r"\(a\)\s+not exceeding 1,?000\s+([\d,]+)", 1000, "not exceeding 1,000 cc"),
        (
            r"\(b\)\s+exceeding 1,?000 cc\s+([\d,]+)\s+but not exceeding 1,?200",
            1200,
            "exceeding 1,000 cc but not exceeding 1,200 cc",
        ),
        (
            r"\(c\)\s+exceeding 1,?200 cc\s+([\d,]+)\s+but not exceeding 1,?500",
            1500,
            "exceeding 1,200 cc but not exceeding 1,500 cc",
        ),
        (
            r"\(d\)\s+exceeding 1,?500 cc\s+([\d,]+)",
            1700,
            "exceeding 1,500 cc but not exceeding 1,700 cc",
        ),
        (
            r"\(e\)\s+exceeding 1,?700 cc\s+([\d,]+)\s+but not exceeding 2,?000",
            2000,
            "exceeding 1,700 cc but not exceeding 2,000 cc",
        ),
        (
            r"\(f\)\s+exceeding 2,?000 cc\s+([\d,]+)\s+but not exceeding 2,?500",
            2500,
            "exceeding 2,000 cc but not exceeding 2,500 cc",
        ),
        (
            r"\(g\)\s+exceeding 2,?500 cc\s+([\d,]+)\s+but not exceeding 3,?000",
            3000,
            "exceeding 2,500 cc but not exceeding 3,000 cc",
        ),
        (r"\(h\)\s+exceeding 3,?000\s+([\d,]+)", None, "exceeding 3,000 cc"),
    ]

    for pattern, max_cc, label in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            tiers.append({"max_cc": max_cc, "fee_kes": _parse_amount(match.group(1)), "label": label})

    return tiers if len(tiers) == 8 else [tier.copy() for tier in DEFAULT_REGISTRATION_TIERS]


def _parse_inspection_tiers(text: str) -> list[dict]:
    tiers: list[dict] = []
    up_to = re.search(
        r"Inspection of three-?\s*wheelers and vehicles\s+([\d,]+)\s+with engine capacities of\s+up to 3,?000 cc",
        text,
        re.I | re.S,
    )
    over = re.search(
        r"Inspection of vehicles\s+([\d,]+)\s+with engine capacities of\s+over 3,?000 cc",
        text,
        re.I | re.S,
    )
    if up_to:
        tiers.append(
            {
                "max_cc": 3000,
                "fee_kes": _parse_amount(up_to.group(1)),
                "label": "up to 3,000 cc",
            }
        )
    if over:
        tiers.append(
            {
                "max_cc": None,
                "fee_kes": _parse_amount(over.group(1)),
                "label": "over 3,000 cc",
            }
        )
    return tiers if len(tiers) == 2 else [tier.copy() for tier in DEFAULT_INSPECTION_TIERS]


def _parse_plate_fees(text: str) -> dict:
    fees = DEFAULT_PLATE_FEES.copy()
    pair = re.search(
        r"Fee for an application for or replacement of front and\s+([\d,]+)",
        text,
        re.I,
    )
    third = re.search(
        r"Fee for an application for or replacement of third\s+([\d,]+)",
        text,
        re.I,
    )
    if pair:
        fees["registration_plates_pair_kes"] = _parse_amount(pair.group(1))
    if third:
        fees["third_license_kes"] = _parse_amount(third.group(1))
    return fees


def parse_ntsa_fees(traffic_rules_pdf: bytes, registration_plates_pdf: bytes) -> dict:
    traffic_text = _pdf_text(traffic_rules_pdf)
    plates_text = _pdf_text(registration_plates_pdf)

    registration_tiers = _parse_registration_tiers(traffic_text)
    inspection_tiers = _parse_inspection_tiers(traffic_text)
    plate_fees = _parse_plate_fees(plates_text)

    return {
        "source": "Kenya Law — Traffic Rules + Registration Plates Rules",
        "traffic_rules_url": TRAFFIC_RULES_URL,
        "registration_plates_url": REGISTRATION_PLATES_URL,
        "updated_at": datetime.utcnow().isoformat(),
        "registration_tiers": registration_tiers,
        "inspection_tiers": inspection_tiers,
        "plate_fees": plate_fees,
        "notes": (
            "Import registration total = original registration fee (Traffic Rules s.6) "
            "+ reflective plates + third licence sticker (LN 62/2016) + pre-registration "
            "inspection (Traffic Rules s.7)."
        ),
    }


def save_ntsa_fees(data: dict, path: Path | None = None) -> Path:
    path = path or settings.data_dir / "reference" / "ntsa_fees.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved NTSA fee data to %s", path)
    return path


def fetch_and_save_ntsa_fees() -> dict:
    traffic_pdf = _download_pdf(TRAFFIC_RULES_URL)
    plates_pdf = _download_pdf(REGISTRATION_PLATES_URL)
    parsed = parse_ntsa_fees(traffic_pdf, plates_pdf)
    save_ntsa_fees(parsed)

    ref_dir = settings.data_dir / "reference"
    (ref_dir / "traffic_rules.pdf").write_bytes(traffic_pdf)
    (ref_dir / "registration_plates_rules.pdf").write_bytes(plates_pdf)
    logger.info("Saved raw NTSA reference PDFs to %s", ref_dir)
    return parsed
