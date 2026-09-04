import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CarListingData:
    source_platform: str
    listing_id: str | None = None
    title: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    engine_cc: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    body_type: str | None = None
    price_jpy: float | None = None
    price_usd: float | None = None
    cf_price_usd: float | None = None
    destination_port: str | None = None
    currency: str = "JPY"
    location: str | None = None
    listing_url: str | None = None
    image_url: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_platform": self.source_platform,
            "listing_id": self.listing_id,
            "title": self.title,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "mileage_km": self.mileage_km,
            "engine_cc": self.engine_cc,
            "fuel_type": self.fuel_type,
            "transmission": self.transmission,
            "body_type": self.body_type,
            "price_jpy": self.price_jpy,
            "price_usd": self.price_usd,
            "cf_price_usd": self.cf_price_usd,
            "destination_port": self.destination_port,
            "currency": self.currency,
            "location": self.location,
            "listing_url": self.listing_url,
            "image_url": self.image_url,
        }


class BaseScraper(ABC):
    platform_name: str = "unknown"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.ua = UserAgent()
        self.delay = settings.scraper_delay_seconds

    def get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.beforward.jp/",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def fetch(self, url: str) -> BeautifulSoup:
        logger.info("Fetching %s", url)
        response = self.session.get(url, headers=self.get_headers(), timeout=45)
        if response.status_code in {403, 429, 503}:
            response.raise_for_status()
        response.raise_for_status()
        time.sleep(self.delay)
        return BeautifulSoup(response.content, "lxml")

    @abstractmethod
    def build_search_url(self, page: int = 1) -> str:
        pass

    @abstractmethod
    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        pass

    def scrape(self, max_pages: int | None = None) -> list[CarListingData]:
        max_pages = settings.scraper_max_pages if max_pages is None else max_pages
        all_listings: list[CarListingData] = []
        page = 1

        while True:
            if max_pages > 0 and page > max_pages:
                break
            try:
                url = self.build_search_url(page)
                soup = self.fetch(url)
                listings = self.parse_listing_page(soup)
                if not listings:
                    logger.warning("%s: no listings on page %d", self.platform_name, page)
                    break
                all_listings.extend(listings)
                logger.info("%s: scraped %d listings from page %d", self.platform_name, len(listings), page)
                page += 1
            except Exception as exc:
                logger.error("%s page %d failed: %s", self.platform_name, page, exc)
                break

        return all_listings
