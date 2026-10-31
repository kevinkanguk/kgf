import requests, json, os, datetime
SID = "food-megamart-kimjang"
ROOT = "E:/090_ETC/kf"
EVENT = "https://www.megamart.com/exhibition/1905864"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
H = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
IMG = "https://static.megamart.com"
os.makedirs(CACHE, exist_ok=True)

def toint(v):
    try:
        return int(str(v).strip())
    except Exception:
        return None

docs, page = [], 1
while True:
    r = requests.post("https://www.megamart.com/api/search/exhibition", headers=H, timeout=30, data={
        "exhbnCateId": "", "sort": "recommend", "exhbnId": "1905864", "rowsPerPage": "40",
        "prFirstComeFlag": "0", "cornType": "", "pageNum": str(page)})
    r.raise_for_status()
    open(f"{CACHE}/api_p{page}.json", "w", encoding="utf8").write(r.text)
    resp = r.json()["data"]["response"]
    got = resp["docs"]
    new = [d for d in got if d["PRODUCT_CODE"] not in {x["PRODUCT_CODE"] for x in docs}]
    docs += new
    if not new or len(docs) >= int(resp["numFound"]):
        break
    page += 1

items = []
for i, d in enumerate(docs, 1):
    org, sale = toint(d["ORG_SALE_PRICE"]), toint(d["DISCOUNT_PRICE"])
    rate = d.get("DISCOUNT_RATE")
    try:
        rate = float(rate)
    except Exception:
        rate = round((1 - sale / org) * 100, 1) if org and sale else None
    star = d.get("STAR_POINT")
    try:
        star = float(star)
    except Exception:
        star = None
    if not star:
        star = None
    cond = "; ".join(x for x in [d.get("CARD_COUPON_DESC"), d.get("MORE_COUPON_DESC")] if x) or None
    img = d.get("IMG_PC") or d.get("IMG_MOB")
    code = d["PRODUCT_CODE"]
    url = f"https://www.megamart.com/product/{code}"
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "food", "source_id": SID,
        "unit": d.get("PRODUCT_GAGE") or None,
        "vendor": d.get("VENDOR_NAME") or "", "channel": "메가마트",
        "product": d["PRODUCT_NAME"], "model_code": code, "buy_url": url,
        "image_url": IMG + img if img else None,
        "rating": star, "review_count": toint(d.get("REVIEW_CNT")),
        "event_url": EVENT, "claimed_original_price": org, "sale_price": sale,
        "claimed_discount_pct": rate, "conditions": cond,
        "sources": [EVENT, "https://www.megamart.com/api/search/exhibition"],
    })
out = {"category": "food", "source_id": SID,
       "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items}
json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
