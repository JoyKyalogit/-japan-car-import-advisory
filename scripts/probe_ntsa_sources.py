"""Probe NTSA and Kenya Law for official fee PDFs."""

import re
import urllib3
import requests

urllib3.disable_warnings()

headers = {"User-Agent": "Mozilla/5.0"}

urls = [
    "https://ntsa.go.ke/downloads.php?pid=Notices",
    "https://www.ntsa.go.ke/downloads",
    "https://kenyalaw.org/kl/index.php?id=11742",
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=30, verify=False)
        print("\n===", url, r.status_code, len(r.text))
        pdfs = re.findall(r'href=["\']([^"\']+\.pdf)["\']', r.text, re.I)
        for pdf in pdfs[:20]:
            print(" ", pdf)
        if "3050" in r.text or "2600" in r.text:
            print("  contains fee amounts in HTML")
    except Exception as exc:
        print(url, "ERR", exc)
