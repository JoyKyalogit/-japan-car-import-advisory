"""Scrape real Kenyan local market prices from Cheki, Jiji, and Autochek."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.database.models import LocalMarketPrice, get_session, init_db
from src.etl.pipeline import save_local_prices_to_db
from src.scrapers.local_market import get_local_market_prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    init_db()
    session = get_session()
    try:
        session.query(LocalMarketPrice).delete()
        session.commit()
        logger.info("Cleared existing local market prices")
    finally:
        session.close()

    summary = get_local_market_prices()
    if summary.empty:
        logger.error("No local prices scraped from Cheki/Jiji/Autochek")
        sys.exit(1)

    session = get_session()
    try:
        count = save_local_prices_to_db(session, summary)
    finally:
        session.close()

    print(
        f"Local market scrape complete: {count} price groups | "
        f"{summary['make'].nunique()} makes | years {int(summary['year'].min())}-{int(summary['year'].max())}"
    )


if __name__ == "__main__":
    main()
