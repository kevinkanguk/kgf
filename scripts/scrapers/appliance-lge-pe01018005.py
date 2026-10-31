import re, json, html, urllib.request, datetime, os, sys
ROOT = "E:/090_ETC/kf"
SRC = "appliance-lge-pe01018005"
URL = "https://www.lge.co.kr/benefits/exhibitions/detail-PE01018005"
API = "https://apiv2.lge.co.kr/itemsvc/ajax/v1/model/retrieveMultipleModelInfo"
UA = {"User-Agent": "Mozilla/5.0"}
cache = f"{ROOT}/data/cache/html/{SRC}/page.html"
if "--fetch" in sys.argv or not os.path.exists(cache):
    open(cache, "wb").write(urllib.request.urlopen(urllib.request.Request(URL, headers=UA)).read())
page = open(cache, encoding="utf-8").read()

# ordered unique model ids with section label (nearest preceding h2/h3 title) and list type
ids = {}
for m in re.finditer(r'data-prdvalue="(MD\d+)"', page):
    mid = m.group(1)
    if mid in ids: continue
    before = page[:m.start()]
    lt = re.findall(r'c-product__list--([a-z-]+)', before[-60000:])
    titles = re.findall(r'<h[23][^>]*class="[^"]*(?:banner_title_title|c-title)[^"]*"[^>]*>(.*?)</h[23]>', before[-60000:], re.S)
    sec = re.sub(r'<[^>]+>|\s+', ' ', titles[-1]).strip() if titles else None
    ids[mid] = {"list": lt[-1] if lt else None, "section": sec}
print("unique ids", len(ids))

def call(batch):
    req = urllib.request.Request(API, data=json.dumps({"modelList": batch}).encode(),
        headers={**UA, "Content-Type": "application/json", "Origin": "https://www.lge.co.kr"})
    return json.load(urllib.request.urlopen(req))["data"]
data = {}
keys = list(ids)
for i in range(0, len(keys), 20):
    for d in call(keys[i:i+20]): data[d["modelId"]] = d
json.dump(data, open(f"{ROOT}/data/cache/html/{SRC}/api.json", "w", encoding="utf-8"), ensure_ascii=False)

items = []
for mid in keys:
    d = data.get(mid)
    if not d: continue
    p = d.get("priceInfo") or {}
    ctx = ids[mid]
    orig = p.get("obsOriginalPrice") or None
    sell = p.get("obsSellingPrice") or None
    benefit = p.get("lastBenefitPrc") or None
    bundle = p.get("bundleDiscountPrice") or None
    cond = []
    if p.get("couponPrice"): cond.append(f"쿠폰 {p['couponPrice']:,}원 적용 시 {benefit:,}원" if benefit else f"쿠폰 {p['couponPrice']:,}원")
    if bundle and sell and bundle != sell: cond.append(f"번들(묶음) 구매 시 {bundle:,}원")
    if p.get("obsMemberPrice"): cond.append(f"멤버 할인액 {p['obsMemberPrice']:,}원(정가 대비 판매가 반영)")
    dm = d.get("dealProductModel")
    if dm: cond.append(f"선착순 특가 {dm.get('startDate','')[:10]}~{dm.get('endDate','')[:10]} 한정수량 {dm.get('dealInventoryQty')}")
    if ctx["section"]: cond.append(f"섹션: {ctx['section']}")
    if ctx["list"]: cond.append(f"목록유형: {ctx['list']}")
    pct = round((orig - sell) / orig * 100, 1) if orig and sell and orig > sell else None
    url = "https://www.lge.co.kr" + (d.get("modelUrlPath") or "")
    items.append({
        "category": "appliance", "source_id": SRC, "unit": None,
        "vendor": "LG전자", "channel": "LGE.COM",
        "product": re.sub(r'<[^>]+>', '', f"{d.get('modelDisplayName')} {d.get('modelName')}").strip(),
        "model_code": d.get("sku") or d.get("modelName"),
        "image_url": ("https://www.lge.co.kr" + d["largeImageAddr"]) if d.get("largeImageAddr") else None,
        "rating": d.get("reviewsScore") if d.get("reviewsCount") else None,
        "review_count": d.get("reviewsCount") if d.get("reviewsCount") else None,
        "buy_url": url, "event_url": URL,
        "claimed_original_price": orig, "sale_price": sell, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None,
        "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
        "sources": [URL, API + " (modelId=%s)" % mid],
        "verify_status": None, "verify_note": None, "confidence": None,
        "_model_id": mid, "_category": d.get("categoryName"), "_status": d.get("modelStatusCode"),
        "_final_benefit_price": benefit, "_bundle_price": bundle,
        "_obsControlPrice": p.get("obsControlPrice"),
    })
for n, it in enumerate(items, 1): it["item_id"] = f"{SRC}-{n:04d}"
out = {"category": "appliance", "source_id": SRC, "collected_at": "2026-10-31", "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/appliance", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/appliance/{SRC}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items), "missing", len(keys)-len(items))
