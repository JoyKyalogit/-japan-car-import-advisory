"""Quick test of live site HTML structure."""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent()
headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}

urls = [
    "https://www.beforward.jp/stocklist/year_from=2018/page=1/sortkey=n",
    "https://www.sbtjapan.com/used-cars/all?page=1&year_from=2018",
    "https://carfromjapan.com/vehicle/search/year-from/2018/page/1",
    "https://www.aaajapan.com/stocklist",
    "https://www.japanesecartrade.com/used-cars?year_from=2018&page=1",
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(r.content, "lxml")
        print(f"\nURL: {url}")
        print(f"Status: {r.status_code} | HTML length: {len(r.text)}")

        selectors = [
            "table.stocklist-table tr",
            ".stock-list-row",
            ".vehicle-item",
            ".car-item",
            ".product-item",
            "div[class*='stock']",
            "div[class*='vehicle']",
        ]
        for sel in selectors:
            n = len(soup.select(sel))
            if n:
                print(f"  {sel}: {n}")

        # Print first few rows with price-like text
        rows = soup.select("table tr")[:5]
        for row in rows:
            text = row.get_text(" ", strip=True)[:120]
            if text:
                print(f"  row: {text}")

    except Exception as e:
        print(f"\nURL: {url}\nERROR: {e}")
