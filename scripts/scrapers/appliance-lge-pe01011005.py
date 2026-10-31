import re, json, requests, datetime, os
SID = "appliance-lge-pe01011005"
EV = "https://www.lge.co.kr/benefits/exhibitions/detail-PE01011005"
BASE = "https://www.lge.co.kr"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/appliance/{SID}.json"
H = {"User-Agent": "Mozilla/5.0", "Origin": BASE, "Referer": BASE + "/"}
API = "https://apiv2.lge.co.kr/itemsvc/ajax/v1/model/retrieveMultipleModelInfo"
os.makedirs(CACHE, exist_ok=True)
html = requests.get(EV, headers=H, timeout=30).text
open(f"{CACHE}/page.html", "w", encoding="utf-8").write(html)
ids = list(dict.fromkeys(re.findall(r'data-prdvalue="(MD\d+)"', html)))
r = requests.post(API, json={"modelList": ids}, headers=H, timeout=30)
open(f"{CACHE}/api.json", "w", encoding="utf-8").write(r.text)
data = {x["modelId"]: x for x in r.json()["data"]}
items = []
for md in ids:
    x = data.get(md)
    if not x:
        continue
    p = x["priceInfo"]
    orig, sell, best, cp = p["obsOriginalPrice"], p["obsSellingPrice"], p["lastBenefitPrc"], p["couponPrice"]
    pct = round((orig - sell) / orig * 100, 1) if orig and sell else None
    cond = []
    if cp and best and best < sell:
        cond.append(f"쿠폰 {cp:,}원 적용 시 최대혜택가 {best:,}원")
    if x["modelStatusCode"] != "ACTIVE":
        cond.append(f"상태 {x['modelStatusCode']}")
    d = x.get("dealProductModel") or {}
    if d.get("endDate"):
        cond.append(f"딜 {d['startDate'][:10]}~{d['endDate'][:10]}, 한정수량 {d.get('dealInventoryQty')}")
    img = x.get("largeImageAddr")
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "appliance", "source_id": SID,
        "unit": x.get("keywds"), "vendor": "LG전자", "channel": "LGE.COM",
        "product": f"{x['modelDisplayName']} {x['salesModelCode']}".strip(),
        "model_code": x["sku"], "buy_url": BASE + x["modelUrlPath"],
        "image_url": BASE + img if img else None,
        "rating": x.get("reviewsScore"), "review_count": x.get("reviewsCount"),
        "event_url": EV, "claimed_original_price": orig or None, "sale_price": sell or None,
        "claimed_discount_pct": pct, "conditions": "; ".join(cond) or None,
        "sources": [EV, API],
    })
out = {"category": "appliance", "source_id": SID,
       "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
