"""Download official KRA CRSP and refresh reference data."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scrapers.kpa_tariff import fetch_and_save_kpa_tariff
from src.scrapers.kra_crsp import fetch_and_save_kra_crsp
from src.scrapers.ntsa_fees import fetch_and_save_ntsa_fees
from src.services.exchange_rate import update_exchange_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    rate = update_exchange_rate(force_refresh=True)
    logger.info("USD/KES rate: %s", rate)

    crsp = fetch_and_save_kra_crsp()
    logger.info("CRSP records: %d", len(crsp))

    kpa = fetch_and_save_kpa_tariff()
    logger.info("KPA tiers loaded: %s", list(kpa.get("tiers", {}).keys()))

    ntsa = fetch_and_save_ntsa_fees()
    logger.info(
        "NTSA fee tiers: registration=%d, inspection=%d",
        len(ntsa.get("registration_tiers", [])),
        len(ntsa.get("inspection_tiers", [])),
    )

    print(
        f"Reference data updated: FX={rate}, CRSP={len(crsp)} records, "
        f"KPA tiers={len(kpa.get('tiers', {}))}, "
        f"NTSA registration tiers={len(ntsa.get('registration_tiers', []))}"
    )


if __name__ == "__main__":
    main()
