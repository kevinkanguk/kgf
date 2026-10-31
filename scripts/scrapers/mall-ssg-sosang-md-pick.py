import json, os, re, time, datetime, requests
SRC = "mall-ssg-sosang-md-pick"
EVENT = "https://www.ssg.com/plan/planShop.ssg?dispCmptId=6000465146#tab=md-pick"
API = "https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/mall/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
     "Accept": "application/json", "Referer": "https://www.ssg.com/", "Origin": "https://www.ssg.com"}

def page(n):
    p = f"{CACHE}/page{n}.json"
    body = {"common": {"viewSiteNo": "6005"}, "params": {"dispCmptId": "6000465146", "inflowSiteNo": "6005",
            "themeId": "7000886050", "page": n, "pageSize": 30}}
    try:
        r = requests.post(API, json=body, headers=H, timeout=30)
        r.raise_for_status(); b = r.content
        json.loads(b)["data"]["itemList"]
        open(p, "wb").write(b)
    except Exception:
        b = open(p, "rb").read()
    return json.loads(b.decode("utf-8"))["data"]

def iv(x):
    x = re.sub(r"[^\d]", "", str(x or ""))
    return int(x) if x else None

raw, n = [], 1
while True:
    d = page(n); raw += d["itemList"]
    if not d.get("hasNext") or not d["itemList"] or n > 100: break
    n += 1; time.sleep(0.3)
items, seen = [], set()
for o in raw:
    if o["itemId"] in seen: continue
    seen.add(o["itemId"])
    sale = iv(o.get("displayPrc")); orig = iv(o.get("strikeOutPrc"))
    if orig is not None and sale is not None and orig <= sale: orig = None
    pct = round((orig - sale) / orig * 100, 1) if orig and sale else None
    if pct is None and o.get("prcChngRate"):
        try: pct = float(o["prcChngRate"])
        except Exception: pass
    pi = o.get("priceInfo", {}).get("summary", {})
    cond = []
    if pi.get("cpnTxt"): cond.append("쿠폰: " + pi["cpnTxt"])
    if o.get("priceInfo", {}).get("raw", {}).get("tildeDispYn") == "Y": cond.append("옵션별 가격 상이('~' 최저가 표기)")
    if o.get("soldOutYn") == "Y": cond.append("품절")
    try: rating = round(float(o["recompPoint"]), 2) if o.get("recompPoint") not in (None, "") else None
    except Exception: rating = None
    rc = iv(o.get("recomRegCnt")) if o.get("recomRegCnt") not in (None, "") else None
    url = f"https://www.ssg.com/item/itemView.ssg?itemId={o['itemId']}&siteNo={o.get('siteNo','')}&salestrNo={o.get('salestrNo','')}"
    items.append({
        "item_id": "%s-%04d" % (SRC, len(items) + 1), "category": "mall", "source_id": SRC,
        "unit": o.get("sellCapaUnitNmWithUnitCapa") or None,
        "vendor": o.get("brandNm") or o.get("splVenNm") or "SSG", "channel": "SSG닷컴 소상공인 브랜드대전 MD's Pick",
        "product": o["itemNm"], "model_code": None, "buy_url": url,
        "image_url": o.get("itemImgUrl") or None, "rating": rating, "review_count": rc,
        "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None, "sources": [EVENT, API]})
out = {"category": "mall", "source_id": SRC, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(raw), len(items), n)
