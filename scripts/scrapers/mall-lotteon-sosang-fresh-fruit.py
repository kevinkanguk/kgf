import json, os, urllib.request, urllib.parse, datetime
SRC = "mall-lotteon-sosang-fresh-fruit"
EVENT = "https://www.lotteon.com/display/planV2/planDetail/112088#tab=fresh-fruit"
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/mall/%s.json" % SRC
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
     "Referer": "https://www.lotteon.com/", "Accept": "application/json"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def page(n):
    q = dict(mallNo=1, spdpNo=112088, sctnNo=110885, pdSortCd="01", pageNo=n, rowsPerPage=100)
    fn = "%s/p%d.json" % (CACHE, n)
    try:
        b = urllib.request.urlopen(urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers=H), timeout=30).read()
        open(fn, "wb").write(b)
    except Exception:
        b = open(fn, "rb").read()
    return json.loads(b)["data"]["planPdList"]

rows, n, total = [], 1, None
while True:
    d = page(n); total = d.get("totalCount")
    rows += d["dataList"]
    if not d["dataList"] or len(rows) >= (total or 0): break
    n += 1
seen, items = set(), []
for r in rows:
    k = r["spdNo"]
    if k in seen: continue
    seen.add(k)
    orig = int(r["slPrc"]) if r.get("slPrc") else None
    sale = r.get("onerFvrPrc") or r.get("scndFvrPrc") or r.get("frstFvrPrc")
    sale = int(sale) if sale else None
    pct = round((orig - sale) * 100 / orig, 1) if orig and sale and sale < orig else (0 if orig and sale else None)
    cond = []
    if r.get("emblNm"): cond.append("엠블럼: " + r["emblNm"])
    if r.get("slStatCd") and r["slStatCd"] != "SALE": cond.append("판매상태 " + r["slStatCd"])
    unit = None
    pass  # stdCapa is a unit-price basis (e.g. per 100g), not pack size; leave null
    items.append({
        "item_id": "%s-%04d" % (SRC, len(items) + 1), "category": "mall", "source_id": SRC,
        "unit": unit, "vendor": r.get("brdNm") or r.get("trNm") or "", "channel": "롯데온 소상공인 함께하는 가을맞이 쇼핑특별전(신선식품 과일/채소/쌀)",
        "product": r["spdNm"], "model_code": r.get("pdNo"),
        "buy_url": "https://www.lotteon.com/p/product/" + r["spdNo"], "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None,
        "sources": [EVENT, API + "?spdpNo=112088&sctnNo=110885"]})
json.dump({"category": "mall", "source_id": SRC, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "total_count_reported": total, "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(rows), total, len(items))
