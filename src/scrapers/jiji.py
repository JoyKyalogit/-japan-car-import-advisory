"""Scrape Kenyan local market car prices from Jiji.co.ke JSON API."""

from __future__ import annotations

import logging
import re
import time

import requests
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.scrapers.local_listing import LocalListingData
from src.utils.helpers import parse_year, parse_vehicle_title

logger = logging.getLogger(__name__)

DEFAULT_MAKES = [
    "toyota",
    "nissan",
    "honda",
    "mazda",
    "mitsubishi",
    "subaru",
    "suzuki",
    "bmw",
    "mercedes-benz",
    "audi",
    "volkswagen",
    "ford",
    "land-rover",
    "jeep",
    "lexus",
    "hyundai",
    "kia",
    "isuzu",
    "daihatsu",
    "volvo",
    "peugeot",
]

MAKE_QUERY_ALIASES = {
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "land-rover": "Land Rover",
    "range-rover": "Land Rover",
    "vw": "Volkswagen",
}


def _make_query_value(make_slug: str) -> str:
    key = make_slug.strip().lower()
    if key in MAKE_QUERY_ALIASES:
        return MAKE_QUERY_ALIASES[key]
    return " ".join(part.capitalize() for part in key.replace("_", "-").split("-"))


def _parse_jiji_title(title: str) -> tuple[int | None, str | None, str | None]:
    """Parse titles like 'Toyota Estima 2019 Black' into year, make, model."""
    parts = re.sub(r"\s+", " ", title.strip()).split()
    year_idx = next((i for i, part in enumerate(parts) if re.fullmatch(r"(19|20)\d{2}", part)), None)
    if year_idx is not None and year_idx >= 2:
        year = int(parts[year_idx])
        make = parts[0].title()
        model = " ".join(parts[1:year_idx]).title() or None
        return year, make, model
    year, make, model = parse_vehicle_title(title)
    year = year or parse_year(title)
    if model:
        model = re.sub(r"\b(?:19|20)\d{2}\b", "", model).strip() or None
        model = model.title() if model else None
    return year, make, model


class JijiScraper:
    platform_name = "Jiji Kenya"
    base_url = "https://jiji.co.ke"
    api_url = "https://jiji.co.ke/api_web/v1/listing"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.ua = UserAgent()
        self.delay = settings.scraper_delay_seconds

    def get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-KE,en;q=0.9",
            "Referer": f"{self.base_url}/cars",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_page(self, make_slug: str, page: int = 1) -> dict:
        params = {
            "slug": "cars",
            "page": page,
            "filter_attr_1_make": _make_query_value(make_slug),
        }
        url = self.api_url
        logger.info("Fetching Jiji %s page %d", make_slug, page)
        response = self.session.get(url, params=params, headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        time.sleep(self.delay)
        return response.json()

    def _attr_map(self, advert: dict) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in advert.get("attrs") or []:
            name = item.get("name")
            value = item.get("value")
            if name and value is not None:
                result[str(name)] = str(value)
        return result

    def parse_adverts(self, payload: dict) -> list[LocalListingData]:
        adverts = (payload.get("adverts_list") or {}).get("adverts") or []
        listings: list[LocalListingData] = []
        for advert in adverts:
            title = (advert.get("title") or "").strip()
            if not title:
                continue

            price_obj = advert.get("price_obj") or {}
            price_kes = price_obj.get("value")
            if price_kes is None:
                continue
            try:
                price_kes = float(price_kes)
            except (TypeError, ValueError):
                continue
            if price_kes <= 0:
                continue

            year, make, model = _parse_jiji_title(title)
            if year and (year < settings.min_year or year > settings.max_year):
                continue

            attrs = self._attr_map(advert)
            listing_url = advert.get("url")
            if listing_url and listing_url.startswith("/"):
                listing_url = f"{self.base_url}{listing_url.split('?')[0]}"

            listings.append(
                LocalListingData(
                    source_platform=self.platform_name,
                    title=title,
                    make=make,
                    model=model,
                    year=year,
                    price_kes=price_kes,
                    fuel_type=attrs.get("Fuel") or attrs.get("Fuel Type"),
                    condition=attrs.get("Condition"),
                    listing_url=listing_url,
                    raw_data={"id": advert.get("id"), "guid": advert.get("guid")},
                )
            )
        return listings

    def scrape_make(self, make_slug: str, max_pages: int | None = None) -> list[LocalListingData]:
        max_pages = max_pages if max_pages is not None else settings.local_scraper_max_pages_per_make
        listings: list[LocalListingData] = []
        page = 1
        while True:
            if max_pages > 0 and page > max_pages:
                break
            try:
                payload = self.fetch_page(make_slug, page)
                page_listings = self.parse_adverts(payload)
            except Exception as exc:
                logger.error("Jiji %s page %d failed: %s", make_slug, page, exc)
                break
            if not page_listings:
                break
            listings.extend(page_listings)
            logger.info("Jiji %s page %d: %d listings", make_slug, page, len(page_listings))

            total = (payload.get("adverts_list") or {}).get("count") or 0
            if page * 24 >= int(total):
                break
            page += 1
        return listings

    def scrape(self, makes: list[str] | None = None, max_pages_per_make: int | None = None) -> list[LocalListingData]:
        if makes is None:
            if settings.local_scraper_makes.strip():
                makes = [item.strip().lower() for item in settings.local_scraper_makes.split(",") if item.strip()]
            else:
                makes = DEFAULT_MAKES
        all_listings: list[LocalListingData] = []
        for make_slug in makes:
            logger.info("Scraping Jiji make: %s", make_slug)
            make_listings = self.scrape_make(make_slug, max_pages=max_pages_per_make)
            all_listings.extend(make_listings)
            logger.info("Jiji %s: %d listings (%d total)", make_slug, len(make_listings), len(all_listings))
        return all_listings
