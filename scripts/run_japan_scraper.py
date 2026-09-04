"""Safer Japan-only BE FORWARD scrape that preserves Kenya local prices."""

import importlib.util
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    # Force a Japan-focused safe run without wiping Kenya prices.
    settings.scraper_use_sample_data = False
    settings.scraper_clear_db = False
    settings.scraper_clear_listings = True
    settings.scraper_clear_local_prices = False
    settings.scraper_refresh_local_prices = False
    settings.scraper_scrape_all_makes = True

    if settings.scraper_max_pages_per_make <= 0:
        settings.scraper_max_pages_per_make = 8
    if settings.scraper_delay_seconds < 3:
        settings.scraper_delay_seconds = 4.0
    if settings.scraper_make_pause_seconds < 5:
        settings.scraper_make_pause_seconds = 10.0
    if settings.scraper_block_cooldown_seconds < 60:
        settings.scraper_block_cooldown_seconds = 180.0

    logger.info(
        "Japan-only safe scrape: pages_per_make=%s delay=%ss make_pause=%ss cooldown=%ss",
        settings.scraper_max_pages_per_make,
        settings.scraper_delay_seconds,
        settings.scraper_make_pause_seconds,
        settings.scraper_block_cooldown_seconds,
    )

    scrapers_path = Path(__file__).with_name("run_scrapers.py")
    spec = importlib.util.spec_from_file_location("run_scrapers_module", scrapers_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
