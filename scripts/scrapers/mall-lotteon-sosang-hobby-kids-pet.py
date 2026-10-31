import json, os, re, time, datetime, requests
SID = "mall-lotteon-sosang-hobby-kids-pet"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EVENT = "https://www.lotteon.com/display/planV2/planDetail/112088#tab=hobby-kids-pet"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36",
     "Referer": "https://www.lotteon.com/", "Origin": "https://www.lotteon.com", "Accept": "application/json"}
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2"
SCTN = "208901"  # 취미/유아동/반려 tab
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def page(n, rows=50):
    p = f"{CACHE}/list_{SCTN}_{n}_{rows}.json"
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    for _ in range(4):
        r = requests.get(API, params={"mallNo": "1", "spdpNo": "112088", "sctnNo": SCTN, "pdSortCd": "01",
                                      "pageNo": n, "rowsPerPage": rows}, headers=H, timeout=30)
        if r.status_code == 200:
            j = r.json(); json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False); return j
        time.sleep(2)
    return {}

rows, n, total = [], 1, None
while True:
    j = page(n)
    d = (j.get("data") or {}).get("planPdList") or {}
    total = d.get("totalCount", total)
    dl = d.get("dataList") or []
    if not dl: break
    rows += dl
    if total and len(rows) >= total: break
    n += 1

seen, items = set(), []
for r in rows:
    pid = r["pdNo"]
    if pid in seen: continue
    seen.add(pid)
    sl = int(r["slPrc"]) if r.get("slPrc") else None
    cands = [r.get(k) for k in ("onerFvrPrc", "scndFvrPrc", "frstFvrPrc") if r.get(k)]
    sale = int(min(cands)) if cands else sl
    orig = sl if (sl and sale and sale < sl) else None
    pct = round((1 - sale / sl) * 100, 1) if orig else None
    nm = r["spdNm"]
    cond = []
    m = re.search(r"\[([^\]]*\d+\s*%[^\]]*)\]", nm)
    if m: cond.append(f"상품명 표기 '{m.group(1)}'")
    if r.get("dcVal"): cond.append(f"추가할인 {r['dcVal']}%")
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID,
        "unit": None, "vendor": r.get("brdNm") or r.get("trNm") or "", "channel": "롯데온",
        "product": nm, "model_code": None,
        "buy_url": f"https://www.lotteon.com/p/product/{pid}",
        "image_url": r.get("imgFullUrl"),
        "rating": r.get("stscrAvgScr"), "review_count": r.get("rvCnt"),
        "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": pct, "conditions": "; ".join(cond) or None,
        "sources": [EVENT, f"{API}?mallNo=1&spdpNo=112088&sctnNo={SCTN}"],
    })
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items), "items; total reported", total)
