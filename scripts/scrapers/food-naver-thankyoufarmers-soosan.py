# Naver brand store listing scraper. As of 2026-10-31 Naver returns HTTP 429 to requests; no items collected.
import requests
URL = "https://brand.naver.com/thankyoufarmers/category/6053b3e1a75d4e1ab5d47bef739d4c16?cp=1"
r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
print(r.status_code)
if r.status_code != 200:
    raise SystemExit("blocked: %d (needs_browser)" % r.status_code)
