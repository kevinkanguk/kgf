import json, os, time, urllib.request, gzip, datetime
ROOT = "E:/090_ETC/kf"
SID = "food-lotteon-soosan"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
SPDP = 116786
EVENT = f"https://www.lotteon.com/display/planV2/planDetail/{SPDP}"
SCT = f"https://pbf.lotteon.com/display/o/v2/plan/seltPlanSctnListV2?mallNo=1&spdpNo={SPDP}"
API = "https://pbf.lotteon.com/display/o/v2/plan/seltPlanProductListV2?mallNo=1&spdpNo=%d&sctnNo=%d&pdSortCd=01&pageNo=%d&rowsPerPage=60"
H = {"Referer": "https://www.lotteon.com/", "User-Agent": "Mozilla/5.0 Chrome/124", "Accept-Encoding": "gzip"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def fetch(url, fp):
    if os.path.exists(fp) and os.path.getsize(fp) > 200:
        return json.load(open(fp, encoding="utf-8"))
    for _ in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30)
            b = r.read()
            if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
            d = json.loads(b.decode("utf-8"))
            json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(0.4); return d
        except Exception as e:
            print("retry", fp, e); time.sleep(2)
    raise SystemExit("failed " + url)

sections = fetch(SCT, f"{CACHE}/sections.json")["data"]["sctnDetail"]
rows = []
for s in sections:
    p = 1
    while True:
        d = fetch(API % (SPDP, s["sctnNo"], p), f"{CACHE}/s{s['sctnNo']}_p{p}.json")["data"]["planPdList"]
        dl = d.get("dataList") or []
        for x in dl: x["_sctn"] = s["sctnNm"]
        rows += dl
        if not dl or sum(1 for _ in dl) < 60 or p * 60 >= (d.get("totalCount") or 0): break
        p += 1
seen, items = set(), []
for x in rows:
    if x["spdNo"] in seen: continue
    seen.add(x["spdNo"])
    orig, final = x.get("slPrc"), x.get("scndFvrPrc") or x.get("frstFvrPrc") or x.get("slPrc")
    orig = int(orig) if orig else None; final = int(final) if final else None
    pct = round((orig - final) * 100 / orig, 1) if orig and final is not None and orig > 0 else None
    cond = ["섹션: " + x["_sctn"]]
    if x.get("emblNm"): cond.append("엠블럼: " + x["emblNm"])
    try:
        for c in json.loads(x.get("crdPrLst") or "[]"):
            nm = c.get("coco_nm") or c.get("sp_py_nm")
            if nm: cond.append(f"{nm} 추가 {c.get('dc_rt')}%")
    except Exception: pass
    if x.get("frstFvrPrc") and x["frstFvrPrc"] != x.get("slPrc"): cond.append(f"1차할인가 {int(x['frstFvrPrc'])}원")
    if x.get("slStatCd") != "SALE": cond.append("판매상태 " + str(x.get("slStatCd")))
    img = x.get("imgFullUrl") or x.get("wdthImgUrl")
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
        "unit": None, "vendor": x.get("brdNm") or x.get("trNm") or "", "channel": "롯데ON 수산대전(소상공인)",
        "product": x["spdNm"], "model_code": x["spdNo"],
        "buy_url": f"https://www.lotteon.com/p/product/{x['spdNo']}",
        "image_url": img, "rating": (float(x["stscrAvgScr"]) if x.get("stscrAvgScr") else None), "review_count": (int(x["rvCnt"]) if x.get("rvCnt") is not None else None), "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": final, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond),
        "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
        "sources": [SCT], "verify_status": None, "verify_note": None, "confidence": None, "_raw_keys": None})
    items[-1].pop("_raw_keys")
    items[-1]["_x"] = x
json.dump({"category": "food", "source_id": SID, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": [{k: v for k, v in i.items() if k != "_x"} for i in items]}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("rows", len(rows), "items", len(items), "sections", len(sections))
if items: print(sorted(items[0]["_x"].keys()))
