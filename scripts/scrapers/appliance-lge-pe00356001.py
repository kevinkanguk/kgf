import json, re, os, sys, time, datetime
import requests
SID = "appliance-lge-pe00356001"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/appliance/{SID}.json"
EVENT = "https://www.lge.co.kr/benefits/exhibitions/detail-PE00356001"
BASE = "https://www.lge.co.kr"
H = {"User-Agent": "Mozilla/5.0"}
os.makedirs(f"{CACHE}/c", exist_ok=True)

def num(v):
    if v is None: return None
    s = re.sub(r"[^\d]", "", str(v))
    return int(s) if s else None

main = requests.get(EVENT, headers=H, timeout=30); main.encoding = "utf-8"
open(f"{CACHE}/main.html", "w", encoding="utf-8").write(main.text)
cats = []
for c in re.findall(r'data-category-name\s*="([^"]*)"', main.text):
    if c not in cats: cats.append(c)

seen = {}; items = []
for cat in cats:
    r = requests.get(f"{BASE}/benefits/exhibitions/exhibitionDetailMltpl.lgajax",
        params={"planEventId": "PE00356001", "categoryName": cat, "partnerType": "B2C"}, headers=H, timeout=30)
    r.encoding = "utf-8"
    open(f"{CACHE}/c/{cat.replace('/','_').replace('°','')}.json", "w", encoding="utf-8").write(r.text)
    for p in r.json().get("data", []):
        sku = p.get("sku")
        if sku in seen:
            seen[sku]["_tabs"].append(cat); continue
        p["_tabs"] = [cat]; seen[sku] = p
        time.sleep(0)
    time.sleep(0.3)

def clean(s): return re.sub(r"<[^>]+>", "", s or "").strip()
n = 0
for sku, p in seen.items():
    n += 1
    orig = num(p.get("obsOriginalPrice")); sale = num(p.get("totalPrice")) or p.get("obsSellingPrice")
    pct = round((orig - sale) / orig * 100, 1) if orig and sale and orig > sale else None
    spec = re.search(r"<em[^>]*>(.*?)</em>", p.get("modelDisplayNamePlusSpec") or "")
    cond = []
    if num(p.get("obsMemberPrice")): cond.append(f"LG멤버십 회원가 {num(p['obsMemberPrice']):,}원 할인 반영")
    if num(p.get("obsDiscountPrice")): cond.append(f"추가할인 {num(p['obsDiscountPrice']):,}원")
    if num(p.get("couponDcPrice")): cond.append(f"쿠폰 {num(p['couponDcPrice']):,}원")
    cond.append("다품목(2개 이상) 구매 기획전: 구매금액별 멤버십P/사은품/캐시백은 별도(가격 미반영)")
    cond.append("탭: " + ", ".join(p["_tabs"]))
    img = p.get("mediumImageAddr") or p.get("largeImageAddr")
    if img and img.startswith("/"): img = BASE + img
    url = p.get("modelUrlPath") or ""
    if url.startswith("/"): url = BASE + url
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "appliance", "source_id": SID,
        "unit": clean(spec.group(1)) if spec else None,
        "vendor": "LG전자", "channel": "LGE.COM 다품목 기획전",
        "product": clean(p.get("modelDisplayName")) + " " + (p.get("modelName") or ""),
        "model_code": p.get("modelName"), "buy_url": url or EVENT, "image_url": img,
        "rating": round(p["reviewsScore"], 2) if p.get("reviewsScore") else None,
        "review_count": num(p.get("reviewsCount")),
        "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": pct, "conditions": "; ".join(cond),
        "sources": [f"{BASE}/benefits/exhibitions/exhibitionDetailMltpl.lgajax?planEventId=PE00356001&categoryName={p['_tabs'][0]}", EVENT],
    })
out = {"category": "appliance", "source_id": SID,
       "collected_at": datetime.datetime.now().strftime("%Y-%m-%d"), "items": items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(cats), "tabs", len(items), "items")
