import requests, json, os, datetime
SID = "food-foodnuri-nonghal-voucher"
URL = "https://sale.foodnuri.go.kr/ft/market/list.do"
API = "https://sale.foodnuri.go.kr/ft/market/getMarkerList.json"
ROOT = "E:/090_ETC/kf"
cache = f"{ROOT}/data/cache/html/{SID}"
os.makedirs(cache, exist_ok=True)
r = requests.post(API, data={"pageIndex": 1}, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
r.raise_for_status()
raw = r.content.decode("utf-8")
open(f"{cache}/getMarkerList.json", "w", encoding="utf8").write(raw)
rows = json.loads(raw)["resultList"]
items = []
for x in rows:
    n = len(items) + 1
    name = (x.get("merchantNm") or x.get("marketNm") or "").strip()
    market = (x.get("marketNm") or "").strip()
    region = (x.get("regionNm") or "").strip()
    addr = (x.get("addr") or "").strip()
    tel = (x.get("tel") or "").strip()
    cond = f"농할상품권 사용 가능 가맹점(가격 없음); 지역={region}; 시장/상가={market or '-'}; 주소={addr}" + (f"; 전화={tel}" if tel else "")
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "food", "source_id": SID,
        "unit": None, "vendor": name or market or "(미상)",
        "channel": f"농할상품권 사용처({region})",
        "product": f"{name} 농할상품권 사용 가맹점" if name else "농할상품권 사용 가맹점",
        "model_code": x.get("bsnsNum") or None,
        "buy_url": URL, "image_url": None, "rating": None, "review_count": None,
        "event_url": URL, "claimed_original_price": None, "sale_price": None,
        "claimed_discount_pct": None, "conditions": cond, "sources": [URL],
    })
out = {"category": "food", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/food", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/food/{SID}.json", "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
