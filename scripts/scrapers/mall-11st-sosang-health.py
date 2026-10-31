import re, json, os, time, datetime, requests
SID = "mall-11st-sosang-health"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EXH, THEME = "2211141", "1756468"
EVENT = f"https://plan.11st.co.kr/plan/front/exhibitions/{EXH}/themes/{THEME}/products"
os.makedirs(CACHE, exist_ok=True)
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0"})

def num(s):
    s = re.sub(r"[^\d]", "", str(s or ""))
    return int(s) if s else None

issues = []
durl = f"https://plan.11st.co.kr/plan/front/exhibitions/{EXH}/detail"
html = S.get(durl, timeout=30).text
open(f"{CACHE}/detail.html", "w", encoding="utf8").write(html)
idx = None
for m in re.finditer(r'name="themeNo_(\d+)" value="([^"]*)"', html):
    if m.group(2) == THEME: idx = m.group(1)
if idx is None:
    raise SystemExit("theme index not found")
g = lambda k: (re.search(rf'name="{k}_{idx}" value="([^"]*)"', html) or [None, ""])[1]
expected = num(g("countOfProducts"))
data = dict(templateType=g("templateType"), page=0, size=expected or 500, themeIndex=idx,
            productSortCode=g("productSortCode"), deliveryType="", isUsableProductNetFunnel="false",
            recommendedProducts="", recommendRequestId="", isAcme=g("isAcme"))
r = S.post(EVENT, data=data, headers={"Referer": durl, "X-Requested-With": "XMLHttpRequest"}, timeout=30)
open(f"{CACHE}/theme_{THEME}.json", "w", encoding="utf8").write(r.text)
ps = r.json().get("themeProducts") or []
if expected and len(ps) < expected: issues.append(f"got {len(ps)} of {expected}")
items, seen = [], set()
for p in ps:
    pn = p["productNo"]
    if pn in seen: continue
    seen.add(pn)
    sell, fin = num(p.get("sellPrice")), num(p.get("finalPrice"))
    rate = p.get("discountRate"); sc = p.get("satisfactionScore")
    items.append(dict(
        item_id=f"{SID}-{len(items)+1:04d}", category="mall", source_id=SID, unit=None,
        vendor="11번가 소상공인", channel="11번가", product=p["productName"], model_code=None,
        buy_url=p["productLink"], image_url=p.get("productImage"),
        rating=round(sc / 20, 2) if sc and num(p.get("reviewCount")) else None,
        review_count=num(p.get("reviewCount")), event_url=EVENT,
        claimed_original_price=sell if p.get("showSellPrice") else None,
        sale_price=fin,
        claimed_discount_pct=float(rate) if p.get("showDiscountRate") and rate else None,
        conditions="기획전 주제: 건강/다이어트식품/의료용품", sources=[EVENT]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="mall", source_id=SID, collected_at="2026-10-31", items=items),
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items), issues)
