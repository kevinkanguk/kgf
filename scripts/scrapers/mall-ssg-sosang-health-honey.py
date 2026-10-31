import requests, json, os, datetime, time
SID = "mall-ssg-sosang-health-honey"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
URL = "https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain"
EVENT = "https://www.ssg.com/plan/planShop.ssg?dispCmptId=6000465146#tab=health-honey"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
     "Origin": "https://www.ssg.com", "Referer": "https://www.ssg.com/", "Content-Type": "application/json"}

def toint(v):
    try:
        v = str(v).replace(",", "").strip()
        return int(v) if v and v != "null" else None
    except Exception:
        return None

os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
raw = []; page = 1
while True:
    b = {"common": {"viewSiteNo": "6005", "domainSiteNo": "6005"},
         "params": {"dispCmptId": "6000465146", "inflowSiteNo": "6005", "themeId": "7000886052", "page": page, "pageSize": 30}}
    d = requests.post(URL, headers=H, data=json.dumps(b), timeout=30).json()
    if d.get("resultCode") != "200":
        print("error", page, d.get("resultDtlMsg")); break
    x = d["data"]
    json.dump(d, open(f"{CACHE}/api_p{page}.json", "w", encoding="utf8"), ensure_ascii=False)
    raw += x["itemList"]
    print(page, len(x["itemList"]), x["hasNext"])
    if not x["hasNext"] or not x["itemList"]: break
    page += 1; time.sleep(0.3)

items = []; seen = set()
for r in raw:
    iid = r["itemId"]
    if iid in seen: continue
    seen.add(iid)
    sale = toint(r.get("displayPrc")); orig = toint(r.get("strikeOutPrc"))
    pct = toint(r.get("prcChngRate"))
    if orig and sale and not pct and orig > sale: pct = round((orig - sale) / orig * 100, 1)
    rating = None
    try:
        rating = float(r["recompPoint"]) if r.get("recompPoint") else None
    except Exception: pass
    ben = [bb.get("txt") for k in ("benefitGrp0","benefitGrp1","benefitGrp2","benefitGrp3","benefitGrp4","benefitGrp5") for bb in r.get(k, []) if bb.get("type") != "160"]
    ben = [t for t in ben if t]
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}",
        "category": "mall", "source_id": SID,
        "unit": None,
        "vendor": r.get("brandNm") or r.get("splVenNm") or "SSG.COM",
        "channel": "SSG.COM 소상공인 브랜드대전 건강식품/꿀",
        "product": r.get("itemNm"),
        "model_code": None,
        "buy_url": f"https://www.ssg.com/item/itemView.ssg?itemId={iid}&siteNo={r.get('siteNo','6001')}&salestrNo={r.get('salestrNo','6005')}",
        "image_url": r.get("itemImgUrl"),
        "rating": rating,
        "review_count": toint(r.get("recomRegCnt")),
        "event_url": EVENT,
        "claimed_original_price": orig,
        "sale_price": sale,
        "claimed_discount_pct": pct,
        "conditions": ", ".join(ben) or None,
        "sources": [EVENT, URL],
    })
json.dump({"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("saved", len(items), "of raw", len(raw))
