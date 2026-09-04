import re
import urllib3
import requests

urllib3.disable_warnings()

headers = {"User-Agent": "Mozilla/5.0"}
js = requests.get(
    "https://www.ntsa.go.ke/build/assets/app-DeC-fKBB.js",
    timeout=30,
    verify=False,
    headers=headers,
).text
print("js len", len(js))
for amount in ["3050", "2600", "3900", "1050", "700"]:
    print(amount, js.count(amount))

urls = set(re.findall(r'"(/api[^"]+)"', js))
print("api paths", sorted(urls)[:25])

pdf_url = "https://roadsensekenya.wordpress.com/wp-content/uploads/2024/04/mvi-rules-2022.pdf"
r = requests.get(pdf_url, timeout=60, headers=headers)
print("mvi pdf", r.status_code, len(r.content))
