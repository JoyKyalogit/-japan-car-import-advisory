import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

headers = {"User-Agent": UserAgent().random}
r = requests.get("https://www.beforward.jp/stocklist/page=1/sortkey=n", headers=headers, timeout=30)
soup = BeautifulSoup(r.content, "lxml")

for a in soup.select("a[href*='stocklist/']"):
    href = a.get("href", "")
    text = a.get_text(" ", strip=True)
    if re.search(r"(sedan|suv|van|wagon|hatch|truck|bus|coupe|pickup|mini)", text, re.I):
        print(text[:40], "->", href)

# body type param search
for a in soup.select("a"):
    href = a.get("href") or ""
    if "body" in href.lower() or "stype" in href.lower():
        print(a.get_text(" ", strip=True)[:30], href[:80])
