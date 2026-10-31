"""Scraper for brand.naver.com/vikingsmarket. Naver returns HTTP 429 to non-browser clients (2026-10-31).
Re-run later; writes items only if the page is reachable. Does not bypass bot detection."""
import requests, json, datetime
SID = "food-naver-vikingsmarket-soosan"
OUT = f"E:/090_ETC/kf/data/raw/catalog/food/{SID}.json"
r = requests.get("https://brand.naver.com/vikingsmarket", headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
items = []
if r.status_code == 200:
    open(f"E:/090_ETC/kf/data/cache/html/{SID}/home.html", "w", encoding="utf-8").write(r.text)
    # TODO: parse product list from __PRELOADED_STATE__ once reachable
else:
    print("blocked", r.status_code)
if items:
    json.dump({"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat(), "items": items},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
