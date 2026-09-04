"""Scraping module (aliases for src.scrapers)."""

from src.scrapers.aaajapan import AAAJapanScraper
from src.scrapers.beforward import BeForwardScraper
from src.scrapers.carfromjapan import CarFromJapanScraper
from src.scrapers.japanesecartrade import JapaneseCarTradeScraper
from src.scrapers.sbt_japan import SBTJapanScraper

__all__ = [
    "SBTJapanScraper",
    "CarFromJapanScraper",
    "AAAJapanScraper",
    "JapaneseCarTradeScraper",
    "BeForwardScraper",
]
