import logging
import re
import time
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from src.config import settings
from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import (
    infer_body_type,
    parse_engine_cc,
    parse_mileage,
    parse_price,
    parse_vehicle_title,
    parse_year,
    usd_to_jpy,
)

logger = logging.getLogger(__name__)

TRANSMISSION_MAP = {
    "AT": "Automatic",
    "MT": "Manual",
    "CVT": "CVT",
}

# Scrape high-volume Japanese brands first (Toyota has 85k+ listings alone).
MAKE_PRIORITY = [
    "1", "3", "2", "7", "10", "4", "5", "94", "8", "103", "68",
    "106", "83", "47", "48", "50", "52", "57", "72", "205", "79",
    "73", "44", "313", "244", "263",
]


class BeForwardScraper(BaseScraper):
    platform_name = "BE FORWARD"
    base_url = "https://www.beforward.jp"

    def build_search_url(self, page: int = 1, make_id: str | None = None) -> str:
        year_filter = f"/year_from={settings.min_year}/year_to={settings.max_year}"
        if make_id:
            return f"{self.base_url}/stocklist/make={make_id}/page={page}{year_filter}/sortkey=n"
        return f"{self.base_url}/stocklist/page={page}{year_filter}/sortkey=n"

    def discover_makes(self) -> dict[str, str]:
        soup = self.fetch(
            f"{self.base_url}/stocklist/page=1/year_from={settings.min_year}"
            f"/year_to={settings.max_year}/sortkey=n"
        )
        makes: dict[str, str] = {}
        for link in soup.select('a[href*="make="]'):
            href = link.get("href", "")
            match = re.search(r"make=(\d+)", href)
            if not match:
                continue
            make_id = match.group(1)
            label = re.sub(r"\s*\([\d,]+\)\s*$", "", link.get_text(" ", strip=True)).strip()
            if label and make_id not in makes:
                makes[make_id] = label.title()
        return dict(sorted(makes.items(), key=lambda item: item[1]))

    def _order_makes(self, makes: dict[str, str]) -> list[tuple[str, str]]:
        ordered: list[tuple[str, str]] = []
        seen: set[str] = set()
        for make_id in MAKE_PRIORITY:
            if make_id in makes:
                ordered.append((make_id, makes[make_id]))
                seen.add(make_id)
        for make_id, make_name in sorted(makes.items(), key=lambda item: item[1]):
            if make_id not in seen:
                ordered.append((make_id, make_name))
        return ordered

    def _spec_value(self, row, css_class: str) -> str | None:
        cell = row.select_one(f"td.{css_class} .val")
        return cell.get_text(strip=True) if cell else None

    def _detailed_spec(self, row, label: str) -> str | None:
        for spec_row in row.select(".table-detailed-spec tr"):
            cells = spec_row.select("td")
            for idx, cell in enumerate(cells):
                if cell.get_text(strip=True).lower() == label.lower() and idx + 1 < len(cells):
                    return cells[idx + 1].get_text(strip=True)
        return None

    def _parse_seats(self, row) -> int | None:
        seats_text = self._detailed_spec(row, "Seats")
        if not seats_text:
            return None
        match = re.search(r"(\d+)", seats_text)
        return int(match.group(1)) if match else None

    def _parse_row(self, row) -> CarListingData | None:
        if "sold" in row.get("class", []) or row.select_one(".sold-label, .sold-out"):
            return None

        title_el = row.select_one(".make-model a, .description-col a.vehicle-url-link")
        title = re.sub(r"\s+", " ", title_el.get_text(" ", strip=True)) if title_el else None
        if not title:
            return None

        year, make, model = parse_vehicle_title(title)
        year_text = self._spec_value(row, "year")
        if year_text:
            year = parse_year(year_text) or year

        if year is not None and (year < settings.min_year or year > settings.max_year):
            return None

        price_el = row.select_one(".vehicle-price .price, .price-col .price")
        price_usd = parse_price(price_el.get_text() if price_el else "")
        if not price_usd:
            return None

        cf_el = row.select_one(".total-price .price, p.total-price span:not(.currency-label)")
        if not cf_el:
            cf_el = row.select_one("p.total-price")
        cf_price_usd = parse_price(cf_el.get_text() if cf_el else "")
        if cf_price_usd and cf_price_usd < price_usd:
            cf_price_usd = None

        dest_el = row.select_one(".destination-port")
        destination_port = dest_el.get_text(strip=True) if dest_el else None

        link = title_el.get("href") if title_el else None
        if not link:
            link_el = row.select_one("a.vehicle-url-link, .photo-col a")
            link = link_el.get("href") if link_el else None
        if link and link.startswith("/"):
            link = f"{self.base_url}{link}"

        listing_id = None
        ref_el = row.select_one(".veh-stock-no")
        if ref_el:
            ref_match = re.search(r"Ref No\.\s*(\S+)", ref_el.get_text(" ", strip=True))
            if ref_match:
                listing_id = ref_match.group(1)
        if not listing_id and link:
            id_match = re.search(r"/id/(\d+)", link)
            listing_id = id_match.group(1) if id_match else link.rstrip("/").split("/")[-1]

        mileage = parse_mileage(self._spec_value(row, "mileage") or "")
        engine_cc = parse_engine_cc(self._spec_value(row, "engine") or "")
        trans_raw = self._spec_value(row, "trans") or ""
        transmission = TRANSMISSION_MAP.get(trans_raw.upper(), trans_raw.title() if trans_raw else None)
        fuel_type = self._detailed_spec(row, "Fuel")
        location = self._spec_value(row, "location") or "Japan"
        seats = self._parse_seats(row)
        body_type = infer_body_type(title, model, seats)

        img_el = row.select_one(".photo-col img")
        image_url = img_el.get("src") if img_el else None
        if image_url and image_url.startswith("//"):
            image_url = f"https:{image_url}"

        return CarListingData(
            source_platform=self.platform_name,
            listing_id=listing_id,
            title=title,
            make=make,
            model=model,
            year=year,
            mileage_km=mileage,
            engine_cc=engine_cc,
            fuel_type=fuel_type,
            transmission=transmission,
            body_type=body_type,
            price_jpy=usd_to_jpy(price_usd),
            price_usd=price_usd,
            cf_price_usd=cf_price_usd,
            destination_port=destination_port,
            currency="USD",
            location=location,
            listing_url=link,
            image_url=image_url,
        )

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        for row in soup.select(".stocklist-row"):
            try:
                listing = self._parse_row(row)
                if listing:
                    listings.append(listing)
            except Exception as exc:
                logger.debug("BE FORWARD parse error: %s", exc)
        return listings

    def _save_make_batch(self, make_id: str, make_name: str, listings: list[CarListingData]) -> None:
        if not listings:
            return
        settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^\w\-]+", "_", make_name.lower())
        path = settings.raw_data_dir / f"beforward_{make_id}_{safe_name}.csv"
        pd.DataFrame([item.to_dict() for item in listings]).to_csv(path, index=False)
        logger.info("Saved %d %s listings to %s", len(listings), make_name, path)

    def _scrape_make(self, make_id: str, make_name: str, max_pages: int) -> list[CarListingData]:
        listings: list[CarListingData] = []
        page = 1
        consecutive_block_failures = 0
        page_retries = max(1, settings.scraper_page_retries)

        while True:
            if max_pages > 0 and page > max_pages:
                break
            url = self.build_search_url(page, make_id=make_id)
            page_listings = None
            last_error: Exception | None = None

            for attempt in range(page_retries):
                try:
                    soup = self.fetch(url)
                    page_listings = self.parse_listing_page(soup)
                    consecutive_block_failures = 0
                    break
                except Exception as exc:
                    last_error = exc
                    wait_s = min(60, 15 * (attempt + 1))
                    logger.warning(
                        "%s page %d failed (attempt %d/%d: %s), waiting %ss",
                        make_name,
                        page,
                        attempt + 1,
                        page_retries,
                        exc,
                        wait_s,
                    )
                    time.sleep(wait_s)

            if page_listings is None:
                consecutive_block_failures += 1
                logger.error("%s page %d failed after retries: %s", make_name, page, last_error)
                # Cool down and try this page one more soft-cycle before abandoning make.
                cooldown = settings.scraper_block_cooldown_seconds
                logger.info(
                    "Possible BE FORWARD rate limit. Cooling down %ss before next attempt...",
                    cooldown,
                )
                time.sleep(cooldown)
                try:
                    soup = self.fetch(url)
                    page_listings = self.parse_listing_page(soup)
                    consecutive_block_failures = 0
                except Exception as exc:
                    logger.error("%s still blocked on page %d: %s — skipping remaining pages for make", make_name, page, exc)
                    break

            if not page_listings:
                logger.info("%s page %d empty — done", make_name, page)
                break

            listings.extend(page_listings)
            logger.info(
                "%s: page %d -> %d listings (%d total for make)",
                make_name,
                page,
                len(page_listings),
                len(listings),
            )
            page += 1

        return listings

    def scrape_all_makes(self, max_pages_per_make: int | None = None) -> list[CarListingData]:
        max_pages_per_make = (
            settings.scraper_max_pages_per_make if max_pages_per_make is None else max_pages_per_make
        )
        makes = self.discover_makes()
        logger.info("Discovered %d makes on BE FORWARD", len(makes))

        all_listings: list[CarListingData] = []
        seen_ids: set[str] = set()
        zero_make_streak = 0

        for index, (make_id, make_name) in enumerate(self._order_makes(makes)):
            if index > 0 and settings.scraper_make_pause_seconds > 0:
                logger.info(
                    "Pausing %.0fs between makes to reduce rate limiting...",
                    settings.scraper_make_pause_seconds,
                )
                time.sleep(settings.scraper_make_pause_seconds)

            logger.info("Scraping %s (make=%s)...", make_name, make_id)
            make_listings = self._scrape_make(make_id, make_name, max_pages_per_make)
            unique_make_listings = []
            for listing in make_listings:
                key = listing.listing_id or listing.listing_url or listing.title
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                unique_make_listings.append(listing)

            self._save_make_batch(make_id, make_name, unique_make_listings)
            all_listings.extend(unique_make_listings)
            logger.info(
                "%s complete: %d listings (%d total across all makes)",
                make_name,
                len(unique_make_listings),
                len(all_listings),
            )

            if not unique_make_listings:
                zero_make_streak += 1
            else:
                zero_make_streak = 0

            # If several makes in a row return nothing, take a longer break once.
            if zero_make_streak >= 3:
                cooldown = max(settings.scraper_block_cooldown_seconds, 180.0)
                logger.warning(
                    "%d makes returned 0 listings — cooling down %ss before continuing",
                    zero_make_streak,
                    cooldown,
                )
                time.sleep(cooldown)
                zero_make_streak = 0

        return all_listings

    def scrape(self, max_pages: int | None = None) -> list[CarListingData]:
        if settings.scraper_scrape_all_makes:
            return self.scrape_all_makes()
        return super().scrape(max_pages=max_pages)
