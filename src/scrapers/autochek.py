"""Scrape Kenyan local market car prices from Autochek (Next.js page data)."""

from __future__ import annotations

import json
import logging
import math
import re
import time

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.scrapers.local_listing import LocalListingData
from src.utils.helpers import parse_vehicle_title

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

MAKE_PATH_ALIASES = {
    "mercedes": "mercedes-benz",
    "range-rover": "land-rover",
}


class AutochekScraper:
    platform_name = "Autochek Kenya"
    base_url = "https://autochek.africa"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.ua = UserAgent()
        self.delay = settings.scraper_delay_seconds

    def get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-KE,en;q=0.9",
        }

    def _make_path(self, make_slug: str) -> str:
        key = make_slug.strip().lower()
        return MAKE_PATH_ALIASES.get(key, key)

    def build_search_url(self, make_slug: str | None, page: int = 1) -> str:
        if make_slug:
            path = f"/ke/cars-for-sale/{self._make_path(make_slug)}"
        else:
            path = "/ke/cars-for-sale"
        return (
            f"{self.base_url}{path}"
            f"?page_number={page}&year_from={settings.min_year}&year_to={settings.max_year}"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_cars_payload(self, make_slug: str | None, page: int = 1) -> dict:
        url = self.build_search_url(make_slug, page)
        logger.info("Fetching Autochek %s", url)
        response = self.session.get(url, headers=self.get_headers(), timeout=40)
        response.raise_for_status()
        time.sleep(self.delay)
        soup = BeautifulSoup(response.content, "lxml")
        node = soup.select_one("#__NEXT_DATA__")
        if not node or not node.string:
            raise ValueError("Autochek page missing __NEXT_DATA__")
        data = json.loads(node.string)
        return data.get("props", {}).get("pageProps", {}).get("cars") or {}

    def _make_from_url(self, website_url: str | None) -> str | None:
        if not website_url:
            return None
        match = re.search(r"/car-for-sale/[^/]+/([^/]+)/", website_url)
        if not match:
            return None
        return match.group(1).replace("-", " ").title()

    def parse_cars(self, cars_payload: dict) -> list[LocalListingData]:
        listings: list[LocalListingData] = []
        for car in cars_payload.get("result") or []:
            title = (car.get("title") or "").strip()
            year = car.get("year")
            price_kes = car.get("marketplacePrice")
            if not title or price_kes is None:
                continue
            try:
                year = int(year) if year is not None else None
                price_kes = float(price_kes)
            except (TypeError, ValueError):
                continue
            if price_kes <= 0:
                continue
            if year and (year < settings.min_year or year > settings.max_year):
                continue

            website_url = car.get("websiteUrl")
            make = self._make_from_url(website_url)
            model = None
            titled = title
            if make:
                make_lower = make.lower()
                if titled.lower().startswith(make_lower):
                    model = titled[len(make) :].strip(" -") or None
                else:
                    model = titled
            else:
                # Titles are often "MAKE Model" without a leading year.
                parts = titled.split()
                if len(parts) >= 2:
                    make = parts[0].title()
                    model = " ".join(parts[1:]).strip() or None
                else:
                    _, make, model = parse_vehicle_title(f"{year or ''} {titled}".strip())

            fuel = car.get("fuelType")
            if isinstance(fuel, str):
                fuel = fuel.title()

            listings.append(
                LocalListingData(
                    source_platform=self.platform_name,
                    title=f"{year} {title}".strip() if year else title,
                    make=make.title() if make else None,
                    model=model.title() if model else None,
                    year=year,
                    price_kes=price_kes,
                    fuel_type=fuel,
                    condition=car.get("sellingCondition"),
                    listing_url=website_url,
                    raw_data={"id": car.get("id"), "mileage": car.get("mileage")},
                )
            )
        return listings

    def scrape_make(self, make_slug: str | None, max_pages: int | None = None) -> list[LocalListingData]:
        max_pages = max_pages if max_pages is not None else settings.local_scraper_max_pages_per_make
        listings: list[LocalListingData] = []
        page = 1
        total_pages = None
        while True:
            if max_pages > 0 and page > max_pages:
                break
            try:
                payload = self.fetch_cars_payload(make_slug, page)
                page_listings = self.parse_cars(payload)
            except Exception as exc:
                logger.error("Autochek %s page %d failed: %s", make_slug or "all", page, exc)
                break
            if not page_listings:
                break
            listings.extend(page_listings)

            pagination = payload.get("pagination") or {}
            total = pagination.get("total") or 0
            page_size = pagination.get("pageSize") or len(page_listings) or 23
            if total_pages is None and total and page_size:
                total_pages = max(1, math.ceil(int(total) / int(page_size)))
            logger.info(
                "Autochek %s page %d: %d listings",
                make_slug or "all",
                page,
                len(page_listings),
            )
            if total_pages is not None and page >= total_pages:
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
            logger.info("Scraping Autochek make: %s", make_slug)
            make_listings = self.scrape_make(make_slug, max_pages=max_pages_per_make)
            all_listings.extend(make_listings)
            logger.info(
                "Autochek %s: %d listings (%d total)",
                make_slug,
                len(make_listings),
                len(all_listings),
            )
        return all_listings
