import json, os, time, urllib.request, gzip, datetime
ROOT = "E:/090_ETC/kf"
SID = "mall-lotteon-sosang-fresh-meat"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
SCTN = 116932  # 신선식품(수산/정육/계란) tab = #tab=fresh-meat
EVENT = "https://www.lotteon.com/display/planV2/planDetail/112088#tab=fresh-meat"
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2?mallNo=1&spdpNo=112088&sctnNo=%d&pdSortCd=01&pageNo=%d&rowsPerPage=60"
H = {"Referer": "https://www.lotteon.com/", "User-Agent": "Mozilla/5.0 Chrome/124", "Accept-Encoding": "gzip"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def get(p):
    fp = f"{CACHE}/p{p}.json"
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        return json.load(open(fp, encoding="utf-8"))
    for _ in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API % (SCTN, p), headers=H), timeout=30)
            b = r.read()
            if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
            d = json.loads(b.decode("utf-8"))
            json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(0.4)
            return d
        except Exception as e:
            print("retry", p, e); time.sleep(2)
    raise SystemExit("failed page %d" % p)

rows, p = [], 1
while True:
    d = get(p)["data"]["planPdList"]
    dl = d.get("dataList") or []
    rows += dl
    if not dl or len(rows) >= d["totalCount"]: break
    p += 1
seen, items = set(), []
for x in rows:
    if x["spdNo"] in seen: continue
    seen.add(x["spdNo"])
    orig, final = x.get("slPrc"), x.get("scndFvrPrc") or x.get("frstFvrPrc") or x.get("slPrc")
    orig = int(orig) if orig else None; final = int(final) if final else None
    pct = round((orig - final) * 100 / orig, 1) if orig and final is not None and orig > 0 else None
    cond = []
    if x.get("emblNm"): cond.append("엠블럼: " + x["emblNm"])
    try:
        for c in json.loads(x.get("crdPrLst") or "[]"):
            nm = c.get("coco_nm") or c.get("sp_py_nm")
            if nm: cond.append(f"{nm} 추가 {c.get('dc_rt')}%")
    except Exception: pass
    if x.get("frstFvrPrc") and x["frstFvrPrc"] != x.get("slPrc"): cond.append(f"1차할인가 {int(x['frstFvrPrc'])}원")
    if x.get("slStatCd") != "SALE": cond.append("판매상태 " + str(x.get("slStatCd")))
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID,
        "unit": None, "vendor": x.get("brdNm") or x.get("trNm") or "", "channel": "롯데ON 소상공인 가을맞이 쇼핑특별전(신선식품 수산/정육/계란)",
        "product": x["spdNm"], "model_code": x["spdNo"],
        "buy_url": f"https://www.lotteon.com/p/product/{x['spdNo']}", "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": final, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None,
        "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
        "sources": [API % (SCTN, 1)], "verify_status": None, "verify_note": None, "confidence": None})
out = {"category": "mall", "source_id": SID, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("rows", len(rows), "items", len(items))
