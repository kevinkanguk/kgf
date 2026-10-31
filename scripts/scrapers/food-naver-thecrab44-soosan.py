import requests, json, datetime, os
# Naver brand store returns HTTP 429 to non-browser clients; browser pane blocks brand.naver.com. No bypass attempted.
SID = "food-naver-thecrab44-soosan"
URL = "https://brand.naver.com/thecrab44/shoppingstory/detail?id=5003113134&page=1"
r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print(r.status_code)
items = []
if r.status_code == 200:
    open(f"data/cache/html/{SID}/detail.html", "w", encoding="utf-8").write(r.text)
    # TODO: parse items if access ever succeeds
out = {"category": "food", "source_id": SID, "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
os.makedirs("data/raw/catalog/food", exist_ok=True)
json.dump(out, open(f"data/raw/catalog/food/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
