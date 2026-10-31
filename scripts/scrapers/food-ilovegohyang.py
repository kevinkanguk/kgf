import requests, json, os, time, datetime
SID = "food-ilovegohyang"
ROOT = "E:/090_ETC/kf"
BASE = "https://www.ilovegohyang.go.kr"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
H = {"User-Agent": "Mozilla/5.0", "Referer": BASE + "/goods/index-main.html"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def fetch(sort, page, n=500):
    for t in range(4):
        try:
            r = requests.get(BASE + "/api/item/list/list-new", headers=H, timeout=60,
                params={"page": page, "itemsPerPage": n, "keyword": "", "searchGbn": "C", "sortType": sort})
            r.raise_for_status(); return r.json()
        except Exception as e:
            time.sleep(2)
    raise RuntimeError("fail")

seen = {}
for sort in ["NEW", "LOW_PRICE"]:
    p = 1
    while True:
        d = fetch(sort, p)
        json.dump(d, open(f"{CACHE}/{sort}_{p}.json", "w", encoding="utf-8"), ensure_ascii=False)
        for c in d["content"]:
            seen.setdefault(c["itemId"], c)
        if p >= d["totalPages"]: break
        p += 1
    total = d["totalElements"]
    print(sort, len(seen), total)
    if len(seen) >= total: break

items = []
for i, c in enumerate(sorted(seen.values(), key=lambda x: x["itemId"]), 1):
    sale = c.get("presentPrice"); orig = c.get("salePrice")
    sale = int(sale) if isinstance(sale, (int, float)) else None
    orig = int(orig) if isinstance(orig, (int, float)) else None
    if orig is not None and sale is not None and orig <= sale: orig = None
    rate = c.get("discountRate") or None
    cond = "기부금(답례품 가격 구조)" + (" / 품절" if c.get("itemSoldOutFlag") == "Y" else "")
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "food", "source_id": SID, "unit": None,
        "vendor": c.get("locgovNm") or "", "channel": "고향사랑e음 답례품",
        "product": c["itemName"], "model_code": c["itemUserCode"],
        "buy_url": f"{BASE}/items/details.html?code={c['itemUserCode']}",
        "event_url": BASE + "/goods/index-main.html",
        "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": rate,
        "conditions": cond, "sources": [BASE + "/api/item/list/list-new"],
    })
json.dump({"category": "food", "source_id": SID,
           "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
