"""Run live scrapers and load real data into the database."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.database.models import CarListing, LocalMarketPrice, get_session, init_db
from src.etl.pipeline import ETLPipeline
from src.scrapers.beforward import BeForwardScraper
from src.scrapers.local_market import get_local_market_prices
from src.scrapers.sample_data import generate_sample_listings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def clear_database(listings: bool = True, local_prices: bool = True):
    session = get_session()
    try:
        if listings:
            session.query(CarListing).delete()
            logger.info("Cleared existing Japan listings")
        if local_prices:
            session.query(LocalMarketPrice).delete()
            logger.info("Cleared existing local market prices")
        session.commit()
    finally:
        session.close()


def save_raw_listings(listings, filename: str | None = None) -> str:
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    filename = filename or f"scraped_listings_{datetime.utcnow():%Y%m%d_%H%M%S}.csv"
    path = settings.raw_data_dir / filename
    df = pd.DataFrame([item.to_dict() for item in listings])
    df.to_csv(path, index=False)
    logger.info("Saved %d raw listings to %s", len(listings), path)
    return str(path)


def main():
    from src.services.exchange_rate import update_exchange_rate

    try:
        rate = update_exchange_rate(force_refresh=True)
        logger.info("Live USD/KES rate: %s", rate)
    except Exception as exc:
        logger.warning("Could not refresh exchange rate: %s", exc)

    all_listings = []

    # Backward-compatible: SCRAPER_CLEAR_DB still means clear listings.
    clear_listings = settings.scraper_clear_db or settings.scraper_clear_listings
    clear_local = settings.scraper_clear_db and settings.scraper_clear_local_prices

    if settings.scraper_use_sample_data:
        logger.info("Using sample data with full make/model coverage")
        init_db()
        clear_database(listings=True, local_prices=True)
        all_listings = generate_sample_listings(full_coverage=True)
        logger.info(
            "Generated %d listings across %d makes",
            len(all_listings),
            len({listing.make for listing in all_listings}),
        )
    else:
        logger.info(
            "Scraping live BE FORWARD data (all_makes=%s, pages_per_make=%s, delay=%ss, years=%s-%s)",
            settings.scraper_scrape_all_makes,
            settings.scraper_max_pages_per_make or "unlimited",
            settings.scraper_delay_seconds,
            settings.min_year,
            settings.max_year,
        )
        init_db()
        if clear_listings or clear_local:
            clear_database(listings=clear_listings, local_prices=clear_local)

        scraper = BeForwardScraper()
        try:
            all_listings = scraper.scrape()
            logger.info("BE FORWARD total: %d listings", len(all_listings))
        except Exception as exc:
            logger.error("BE FORWARD failed: %s", exc)
            sys.exit(1)

        if not all_listings:
            logger.error("No listings scraped. Check network access and scraper selectors.")
            sys.exit(1)

        save_raw_listings(all_listings)

    if settings.scraper_refresh_local_prices:
        local_prices = get_local_market_prices(all_listings)
    else:
        logger.info("Skipping Kenya local refresh — keeping existing LocalMarketPrice rows")
        local_prices = None

    pipeline = ETLPipeline()
    cleaned = pipeline.run(all_listings, local_prices)
    makes = cleaned["make"].nunique() if not cleaned.empty else 0
    models = cleaned["model"].nunique() if not cleaned.empty else 0
    body_types = cleaned["body_type"].nunique() if "body_type" in cleaned.columns and not cleaned.empty else 0
    print(
        f"Pipeline complete: {len(cleaned)} cleaned records | "
        f"{makes} makes | {models} models | {body_types} body types"
    )


if __name__ == "__main__":
    main()
