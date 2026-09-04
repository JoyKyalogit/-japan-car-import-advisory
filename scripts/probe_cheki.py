import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

headers = {"User-Agent": UserAgent().random}
url = "https://www.cheki.co.ke/vehicles/toyota?year_from=2018&year_to=2026"
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.content, "lxml")

items = []
for heading in soup.select("h3[title]"):
    title = heading.get("title") or heading.get_text(" ", strip=True)
    if not re.match(r"^[A-Za-z]", title):
        continue
    panel = heading.find_parent("div", class_="p-5")
    if not panel:
        continue
    price_el = None
    for candidate in panel.select("p"):
        classes = " ".join(candidate.get("class", []))
        if "font-black" in classes and "22px" in classes:
            price_el = candidate
            break
    price_text = price_el.get_text(" ", strip=True) if price_el else ""
    year_span = None
    for block in panel.select("div[title='Year'] span"):
        year_span = block
        break
    link = heading.find_parent("a") or panel.select_one('a[href*="/vehicle/"]')
    href = link.get("href") if link else ""
    card_root = panel.find_parent("div", class_=lambda value: value and "group" in value)
    condition = ""
    if card_root:
        badge = card_root.find("span", string=re.compile("Used", re.I))
        condition = badge.get_text(strip=True) if badge else ""
    items.append((title, price_text, year_span.get_text(strip=True) if year_span else "", condition, href))

print("count", len(items))
for item in items[:10]:
    print(item)
