import json, os, time, collections, urllib.request
ROOT = "E:/090_ETC/kf"
SID = "mall-hmall-sosang-reco-5"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
API = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page={}"
EVENT = "https://www.hmall.com/md/dpl/index?sectId=2811083"
SECT = "추천상품(쿠폰 미적용)"
LO, HI = 1201, 1500
H = {"Referer": "https://www.hmall.com/", "User-Agent": "Mozilla/5.0"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
rows = []; p = 1
while True:
    fp = f"{CACHE}/p{p}.json"
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        d = json.load(open(fp, encoding="utf-8"))
    else:
        for t in range(4):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(API.format(p), headers=H), timeout=30)); break
            except Exception as e:
                time.sleep(2)
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.2)
    il = d.get("respData", {}).get("itemList") or []
    if not il: break
    rows += il; p += 1
    if p > 300: break
print("pages", p - 1, "rows", len(rows))
print(collections.Counter(r.get("sectNm") for r in rows).most_common(10))
reco = [r for r in rows if r.get("sectNm") == SECT]
print("reco total", len(reco))
sel = reco[LO - 1:HI]
items = []
for i, r in enumerate(sel, 1):
    sell = r.get("sellPrc"); fin = r.get("bbprc")
    sell = int(sell) if sell else None; fin = int(fin) if fin else None
    pct = round((sell - fin) / sell * 100, 1) if sell and fin and sell > fin else None
    cond = None
    if r.get("copnDcAmt"):
        cond = f"쿠폰 {r['copnDcAmt']}원({r.get('copnDcRate')}%) 할인 반영된 최종가(bbprc)"
    code = r["slitmCd"]
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": r.get("brndNm") or r.get("venNm") or "현대Hmall",
        "channel": "현대Hmall 소상공인 기획전(물가안정 프로젝트)",
        "product": r.get("slitmNm"), "model_code": code,
        "buy_url": f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={code}",
        "event_url": EVENT,
        "claimed_original_price": sell, "sale_price": fin, "claimed_discount_pct": pct,
        "conditions": cond, "sources": [API.format(1), f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={code}"],
    })
out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
