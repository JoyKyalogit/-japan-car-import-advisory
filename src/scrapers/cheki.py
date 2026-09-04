import logging
import re
import time

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.scrapers.local_listing import LocalListingData
from src.utils.helpers import parse_price, parse_vehicle_title

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


class ChekiScraper:
    platform_name = "Cheki Kenya"
    base_url = "https://www.cheki.co.ke"

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, url: str) -> BeautifulSoup:
        logger.info("Fetching %s", url)
        response = self.session.get(url, headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        time.sleep(self.delay)
        return BeautifulSoup(response.content, "lxml")

    def discover_makes(self) -> list[str]:
        soup = self.fetch(f"{self.base_url}/vehicles")
        makes: list[str] = []
        for option in soup.select('select[name="make"] option'):
            value = (option.get("value") or "").strip().lower()
            if value and value not in {"all", "any", ""}:
                makes.append(value)
        return makes or DEFAULT_MAKES

    def build_search_url(self, make_slug: str, page: int = 1) -> str:
        params = (
            f"year_from={settings.min_year}&year_to={settings.max_year}"
            f"&page={page}"
        )
        return f"{self.base_url}/vehicles/{make_slug}?{params}"

    def _parse_condition(self, panel) -> str | None:
        card_root = panel.find_parent("div", class_=lambda value: value and "group" in value)
        if not card_root:
            return None
        for span in card_root.select("span"):
            text = span.get_text(strip=True)
            if "used" in text.lower() or "import" in text.lower():
                return text
        return None

    def _parse_fuel(self, title: str) -> str | None:
        lowered = title.lower()
        for fuel in ("hybrid", "diesel", "petrol", "electric"):
            if fuel in lowered:
                return fuel.title()
        return None

    def parse_listing_page(self, soup: BeautifulSoup) -> list[LocalListingData]:
        listings: list[LocalListingData] = []
        for heading in soup.select("h3[title]"):
            title = heading.get("title") or heading.get_text(" ", strip=True)
            if not re.match(r"^[A-Za-z]", title):
                continue

            panel = heading.find_parent("div", class_="p-5")
            if not panel:
                continue

            price_kes = None
            for candidate in panel.select("p"):
                classes = " ".join(candidate.get("class", []))
                if "font-black" in classes and "22px" in classes:
                    price_kes = parse_price(candidate.get_text(" ", strip=True))
                    break
            if not price_kes:
                continue

            year = None
            for block in panel.select("div[title='Year'] span"):
                year_text = block.get_text(strip=True)
                if year_text.isdigit():
                    year = int(year_text)
                    break

            year_parsed, make, model = parse_vehicle_title(title)
            year = year or year_parsed
            if year and (year < settings.min_year or year > settings.max_year):
                continue

            link = heading.find_parent("a") or panel.select_one('a[href*="/vehicle/"]')
            listing_url = link.get("href") if link else None
            if listing_url and listing_url.startswith("/"):
                listing_url = f"{self.base_url}{listing_url}"

            listings.append(
                LocalListingData(
                    source_platform=self.platform_name,
                    title=title,
                    make=make,
                    model=model,
                    year=year,
                    price_kes=price_kes,
                    fuel_type=self._parse_fuel(title),
                    condition=self._parse_condition(panel),
                    listing_url=listing_url,
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
            url = self.build_search_url(make_slug, page)
            try:
                soup = self.fetch(url)
                page_listings = self.parse_listing_page(soup)
            except Exception as exc:
                logger.error("Cheki %s page %d failed: %s", make_slug, page, exc)
                break
            if not page_listings:
                break
            listings.extend(page_listings)
            logger.info("Cheki %s page %d: %d listings", make_slug, page, len(page_listings))
            page += 1
        return listings

    def scrape(self, makes: list[str] | None = None, max_pages_per_make: int | None = None) -> list[LocalListingData]:
        if makes is None:
            if settings.local_scraper_makes.strip():
                makes = [item.strip().lower() for item in settings.local_scraper_makes.split(",") if item.strip()]
            else:
                makes = self.discover_makes()
        all_listings: list[LocalListingData] = []
        for make_slug in makes:
            logger.info("Scraping Cheki make: %s", make_slug)
            make_listings = self.scrape_make(make_slug, max_pages=max_pages_per_make)
            all_listings.extend(make_listings)
            logger.info("Cheki %s: %d listings (%d total)", make_slug, len(make_listings), len(all_listings))
        return all_listings
