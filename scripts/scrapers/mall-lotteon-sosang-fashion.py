import json, os, urllib.request, datetime
SRC = "mall-lotteon-sosang-fashion"
EVENT = "https://www.lotteon.com/display/planV2/planDetail/112088#tab=fashion"
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2?mallNo=1&spdpNo=112088&sctnNo=110880&pdSortCd=01&pageNo=%d&rowsPerPage=60"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/mall/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
     "Accept": "application/json", "Referer": "https://www.lotteon.com/", "Origin": "https://www.lotteon.com"}

def page(n):
    p = f"{CACHE}/page{n}.json"
    try:
        b = urllib.request.urlopen(urllib.request.Request(API % n, headers=H), timeout=30).read()
        open(p, "wb").write(b)
    except Exception:
        b = open(p, "rb").read()
    return json.loads(b.decode("utf-8"))["data"]["planPdList"]

def iv(x):
    return int(x) if x not in (None, "") else None

raw, n = [], 1
while True:
    l = page(n); raw += l["dataList"]
    if not l["dataList"] or len(raw) >= l["totalCount"] or n > 40: break
    n += 1
items, seen = [], set()
for o in raw:
    if o["spdNo"] in seen: continue
    seen.add(o["spdNo"])
    orig, sale = iv(o.get("slPrc")), iv(o.get("onerFvrPrc") or o.get("scndFvrPrc") or o.get("slPrc"))
    pct = round((orig - sale) / orig * 100, 1) if orig and sale is not None and orig > sale else None
    cond = []
    if o.get("dcVal"): cond.append("롯데온 표기 할인율 %s%% (쿠폰/즉시할인 포함 가능)" % o["dcVal"])
    if o.get("emblNm"): cond.append("엠블럼: " + o["emblNm"])
    if o.get("onnuriYn") == "Y": cond.append("온누리상품권 사용 가능")
    unit = "%s%s" % (o["stdCapa"], o.get("stdUtNm") or "") if o.get("stdCapa") else None
    url = "https://www.lotteon.com/p/product/" + o["spdNo"]
    items.append({
        "item_id": "%s-%04d" % (SRC, len(items) + 1), "category": "mall", "source_id": SRC,
        "unit": unit, "vendor": o.get("brdNm") or o.get("trNm") or "", "channel": "롯데온 소상공인 가을맞이 쇼핑특별전(패션/잡화)",
        "product": o["spdNm"], "model_code": o.get("sitmNo"), "buy_url": url, "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None,
        "sources": [EVENT, API % 1], "verify_status": None})
json.dump({"category": "mall", "source_id": SRC, "collected_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"), "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items), len(raw))
