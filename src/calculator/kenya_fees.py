"""Kenya port, clearing, and NTSA fee schedules."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config import settings
from src.services.exchange_rate import get_usd_to_kes

logger = logging.getLogger(__name__)

# Fallback when KPA PDF has not been downloaded yet.
FALLBACK_KPA_PORT_CHARGES_KES = {
    "Hatchback": 38_500,
    "Sedan": 42_000,
    "Wagon": 44_500,
    "SUV": 52_000,
    "Minivan": 55_000,
    "Van": 58_000,
    "Pickup": 62_000,
    "Coupe": 45_000,
}

# Fallback NTSA bundle when reference JSON is unavailable.
FALLBACK_NTSA_REGISTRATION_KES = {
    "small": 18_500,
    "medium": 22_500,
    "large": 28_500,
}

# Clearing agent fee bands — industry averages, not a government tariff.
CLEARING_FEE_BANDS = [
    (0, 8_000, 28_000),
    (8_001, 15_000, 35_000),
    (15_001, 25_000, 42_000),
    (25_001, 999_999, 50_000),
]

OTHER_CHARGES_KES = 12_500


def _kpa_tariff_path() -> Path:
    return settings.data_dir / "reference" / "kpa_tariff.json"


def _ntsa_fees_path() -> Path:
    return settings.data_dir / "reference" / "ntsa_fees.json"


def load_kpa_tariff() -> dict | None:
    path = _kpa_tariff_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_ntsa_fees() -> dict | None:
    path = _ntsa_fees_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _fee_from_tiers(engine_cc: int, tiers: list[dict]) -> tuple[float, str]:
    cc = max(int(engine_cc or 1500), 0)
    for tier in tiers:
        max_cc = tier.get("max_cc")
        if max_cc is None or cc <= int(max_cc):
            label = tier.get("label", "")
            return float(tier["fee_kes"]), label
    last = tiers[-1]
    return float(last["fee_kes"]), str(last.get("label", ""))


def _normalize_body(body_type: str | None) -> str:
    return (body_type or "Sedan").title()


def port_charges_kes(body_type: str | None = "Sedan") -> tuple[float, str]:
    body = _normalize_body(body_type)
    tariff = load_kpa_tariff()
    if tariff:
        tier_key = tariff.get("body_type_map", {}).get(body, "tier1")
        tier = tariff.get("tiers", {}).get(tier_key)
        if tier:
            total_usd = float(tier["stevedoring_usd"]) + float(tier["wharfage_usd"])
            kes = round(total_usd * get_usd_to_kes(), 0)
            source = tariff.get("source", "KPA Tariff PDF")
            return kes, f"{source} ({tier.get('label', tier_key)})"

    return float(FALLBACK_KPA_PORT_CHARGES_KES.get(body, 45_000)), "Fallback KPA estimate"


def ntsa_registration_kes(engine_cc: int = 1500) -> tuple[float, str]:
    fees = load_ntsa_fees()
    if fees:
        registration, reg_label = _fee_from_tiers(engine_cc, fees.get("registration_tiers", []))
        inspection, insp_label = _fee_from_tiers(engine_cc, fees.get("inspection_tiers", []))
        plate_fees = fees.get("plate_fees", {})
        plates = float(plate_fees.get("registration_plates_pair_kes", 3000))
        third = float(plate_fees.get("third_license_kes", 700))
        total = registration + inspection + plates + third
        source = fees.get("source", "NTSA official fee schedule")
        detail = (
            f"registration KES {registration:,.0f} ({reg_label}), "
            f"inspection KES {inspection:,.0f} ({insp_label}), "
            f"plates KES {plates:,.0f}, third licence KES {third:,.0f}"
        )
        return total, f"{source} — {detail}"

    cc = int(engine_cc or 1500)
    if cc <= 1300:
        return float(FALLBACK_NTSA_REGISTRATION_KES["small"]), "Fallback NTSA estimate (≤1300cc)"
    if cc <= 2000:
        return float(FALLBACK_NTSA_REGISTRATION_KES["medium"]), "Fallback NTSA estimate (1301-2000cc)"
    return float(FALLBACK_NTSA_REGISTRATION_KES["large"]), "Fallback NTSA estimate (>2000cc)"


def clearing_fees_kes(cif_usd: float) -> tuple[float, str]:
    for lower, upper, fee in CLEARING_FEE_BANDS:
        if lower <= cif_usd <= upper:
            return float(fee), "Clearing agent industry average (not government tariff)"
    return float(CLEARING_FEE_BANDS[-1][2]), "Clearing agent industry average (not government tariff)"


def other_charges_kes() -> tuple[float, str]:
    return float(OTHER_CHARGES_KES), "Documentation and pre-delivery allowance"
