import logging
from datetime import datetime

import pandas as pd

from src.config import settings
from src.scrapers.autochek import AutochekScraper
from src.scrapers.base import CarListingData
from src.scrapers.cheki import ChekiScraper
from src.scrapers.jiji import JijiScraper
from src.scrapers.local_listing import LocalListingData
from src.scrapers.sample_data import generate_local_market_prices

logger = logging.getLogger(__name__)

SOURCE_SCRAPERS = {
    "cheki": ChekiScraper,
    "jiji": JijiScraper,
    "autochek": AutochekScraper,
}


def _selected_sources() -> list[str]:
    raw = settings.local_scraper_sources.strip()
    if not raw:
        return ["cheki", "jiji", "autochek"]
    sources = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return [source for source in sources if source in SOURCE_SCRAPERS] or ["cheki"]


def listings_to_market_prices(listings: list[LocalListingData]) -> pd.DataFrame:
    if not listings:
        return pd.DataFrame()

    df = pd.DataFrame([item.to_dict() for item in listings])
    df = df[df["make"].notna() & df["model"].notna() & df["year"].notna() & df["price_kes"].notna()]
    if df.empty:
        return df

    grouped = (
        df.groupby(["make", "model", "year"], as_index=False)
        .agg(
            avg_price_kes=("price_kes", "mean"),
            min_price_kes=("price_kes", "min"),
            max_price_kes=("price_kes", "max"),
            listing_count=("price_kes", "count"),
            sources=("source_platform", lambda values: ", ".join(sorted(set(values)))),
        )
    )
    grouped["avg_price_kes"] = grouped["avg_price_kes"].round(0)
    grouped["min_price_kes"] = grouped["min_price_kes"].round(0)
    grouped["max_price_kes"] = grouped["max_price_kes"].round(0)
    grouped["source"] = grouped["sources"]
    grouped["updated_at"] = datetime.utcnow()
    return grouped.drop(columns=["sources"])


def scrape_real_local_prices(
    makes: list[str] | None = None,
    max_pages_per_make: int | None = None,
) -> tuple[list[LocalListingData], pd.DataFrame]:
    sources = _selected_sources()
    all_listings: list[LocalListingData] = []

    for source in sources:
        scraper_cls = SOURCE_SCRAPERS[source]
        scraper = scraper_cls()
        logger.info("Starting local scraper: %s", scraper.platform_name)
        try:
            listings = scraper.scrape(makes=makes, max_pages_per_make=max_pages_per_make)
            all_listings.extend(listings)
            logger.info("%s returned %d listings", scraper.platform_name, len(listings))
        except Exception as exc:
            logger.error("%s failed: %s", scraper.platform_name, exc)

    summary = listings_to_market_prices(all_listings)
    return all_listings, summary


def get_local_market_prices(japan_listings: list[CarListingData] | None = None) -> pd.DataFrame:
    """Return real multi-source Kenya prices when enabled, otherwise fall back to estimates."""
    if not settings.scraper_use_real_local_prices:
        if japan_listings:
            return generate_local_market_prices(japan_listings)
        return pd.DataFrame()

    listings, summary = scrape_real_local_prices()
    if summary.empty and japan_listings:
        logger.warning("Local scrapers returned no prices; using estimates as fallback")
        return generate_local_market_prices(japan_listings)

    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    if listings:
        raw_path = settings.raw_data_dir / f"kenya_listings_{stamp}.csv"
        pd.DataFrame([item.to_dict() for item in listings]).to_csv(raw_path, index=False)
        logger.info("Saved %d Kenya listings to %s", len(listings), raw_path)
    if not summary.empty:
        summary_path = settings.raw_data_dir / f"local_market_prices_{stamp}.csv"
        summary.to_csv(summary_path, index=False)
        logger.info("Saved %d local market price groups to %s", len(summary), summary_path)
    return summary
