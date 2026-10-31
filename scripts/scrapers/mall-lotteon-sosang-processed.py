import urllib.request, json, os, re, time, datetime
SID = "mall-lotteon-sosang-processed"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EVENT = "https://www.lotteon.com/display/planV2/planDetail/112088#tab=processed"
H = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.lotteon.com", "Referer": "https://www.lotteon.com/"}
SCTN = 110886
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2"

def get(u):
    for i in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf8"))
        except Exception as e:
            time.sleep(2 * (i + 1))
    raise RuntimeError(u)

def num(x):
    return int(round(x)) if isinstance(x, (int, float)) else None

os.makedirs(CACHE, exist_ok=True)
rows, page, total = [], 1, None
while True:
    u = f"{API}?mallNo=1&spdpNo=112088&sctnNo={SCTN}&pdSortCd=01&pageNo={page}&rowsPerPage=60"
    d = get(u)["data"]["planPdList"]
    total = d["totalCount"]
    open(f"{CACHE}/page_{page:03d}.json", "w", encoding="utf8").write(json.dumps(d, ensure_ascii=False))
    rows += d["dataList"]
    if not d["dataList"] or len(rows) >= total:
        break
    page += 1
    time.sleep(0.3)

seen, items = set(), []
for p in rows:
    if p["spdNo"] in seen:
        continue
    seen.add(p["spdNo"])
    orig, sale, best = num(p.get("slPrc")), num(p.get("scndFvrPrc")), num(p.get("dcAplyTotAmt"))
    if sale is None:
        sale = orig
    pct = round((orig - sale) / orig * 100, 1) if orig and sale is not None and orig > 0 else None
    cond = None
    if best is not None and sale is not None and best < sale:
        cond = f"추가할인 적용가 {best}원 (쿠폰/카드 등 조건)"
    url = f"https://www.lotteon.com/product/{p['spdNo']}"
    if p.get("sitmNo"):
        url += f"?sitmNo={p['sitmNo']}"
    n = len(items) + 1
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "mall", "source_id": SID,
        "unit": None, "vendor": (p.get("brdNm") or p.get("trNm") or "").strip(),
        "channel": "롯데온 소상공인 가을맞이 쇼핑특별전", "product": p["spdNm"], "model_code": None,
        "buy_url": url, "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": cond, "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
        "sources": [f"{API}?spdpNo=112088&sctnNo={SCTN}", url],
        "verify_status": None, "verify_note": None, "confidence": None,
    })
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("total", total, "rows", len(rows), "items", len(items))
