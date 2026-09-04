"""Fetch and cache live USD/KES exchange rates."""

import json
import logging
from datetime import datetime, timedelta

import requests

from src.config import settings

logger = logging.getLogger(__name__)

CACHE_FILE = settings.data_dir / "reference" / "exchange_rate.json"
CACHE_TTL_HOURS = 12


def _load_cache() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(rate: float, source: str) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "usd_to_kes": rate,
        "source": source,
        "fetched_at": datetime.utcnow().isoformat(),
    }
    CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _fetch_from_open_er_api() -> tuple[float, str]:
    response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=15)
    response.raise_for_status()
    data = response.json()
    rate = float(data["rates"]["KES"])
    return rate, "open.er-api.com"


def _fetch_from_exchangerate_host() -> tuple[float, str]:
    response = requests.get(
        "https://api.exchangerate.host/latest",
        params={"base": "USD", "symbols": "KES"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    rate = float(data["rates"]["KES"])
    return rate, "exchangerate.host"


def fetch_live_usd_to_kes() -> tuple[float, str]:
    errors: list[str] = []
    for fetcher in (_fetch_from_open_er_api, _fetch_from_exchangerate_host):
        try:
            rate, source = fetcher()
            if rate > 0:
                return round(rate, 4), source
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError(f"Could not fetch USD/KES rate: {'; '.join(errors)}")


def get_usd_to_kes(force_refresh: bool = False) -> float:
    """Return cached live rate when enabled, otherwise the configured fallback."""
    if not settings.use_live_exchange_rate:
        return settings.usd_to_kes

    cache = None if force_refresh else _load_cache()
    if cache:
        fetched_at = datetime.fromisoformat(cache["fetched_at"])
        if datetime.utcnow() - fetched_at < timedelta(hours=CACHE_TTL_HOURS):
            return float(cache["usd_to_kes"])

    try:
        rate, source = fetch_live_usd_to_kes()
        _save_cache(rate, source)
        logger.info("Updated USD/KES rate: %s (%s)", rate, source)
        return rate
    except Exception as exc:
        logger.warning("Live FX fetch failed (%s); using fallback %.2f", exc, settings.usd_to_kes)
        if cache and cache.get("usd_to_kes"):
            return float(cache["usd_to_kes"])
        return settings.usd_to_kes


def update_exchange_rate(force_refresh: bool = True) -> float:
    return get_usd_to_kes(force_refresh=force_refresh)
