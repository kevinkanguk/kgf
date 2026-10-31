"""food-hanwooboardmarket-part-006: hanwooboardmarket.com xcode=040 mcode=006 (euc-kr, server-rendered)."""
import requests, re, json, datetime, os
SID = "food-hanwooboardmarket-part-006"
BASE = "https://www.hanwooboardmarket.com"
URL = BASE + "/shop/shopbrand.html?type=N&xcode=040&mcode=006"
ROOT = "E:/090_ETC/kf"
H = {"User-Agent": "Mozilla/5.0"}
items, page = [], 1
seen = set()
while True:
    r = requests.get(URL + f"&page={page}", headers=H, timeout=30)
    t = r.content.decode("euc-kr", "replace")
    os.makedirs(f"{ROOT}/data/cache/html/{SID}", exist_ok=True)
    open(f"{ROOT}/data/cache/html/{SID}/p{page}.html", "w", encoding="utf8").write(t)
    ids = [i for i in dict.fromkeys(re.findall(r"branduid=(\d+)", t)) if i not in seen]
    if not ids:
        break
    for b in ids:
        seen.add(b)
        items.append({"item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
                      "vendor": None, "channel": "hanwooboardmarket", "product": None,
                      "buy_url": f"{BASE}/shop/shopdetail.html?branduid={b}"})
    page += 1
    if page > 50: break
# NOTE: page chrome lists nav/home links; with "전체상품 0개" no items found.
out = {"category": "food", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/food", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/food/{SID}.json", "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
