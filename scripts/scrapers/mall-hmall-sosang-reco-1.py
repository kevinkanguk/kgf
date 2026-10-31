import json, os, time, collections, urllib.request
ROOT = "E:/090_ETC/kf"
SID = "mall-hmall-sosang-reco-1"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
API = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page={}"
EVENT = "https://www.hmall.com/md/dpl/index?sectId=2811083"
H = {"Referer": "https://www.hmall.com/", "User-Agent": "Mozilla/5.0"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
rows = []
p = 1
while True:
    fp = f"{CACHE}/p{p}.json"
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        d = json.load(open(fp, encoding="utf-8"))
    else:
        d = json.load(urllib.request.urlopen(urllib.request.Request(API.format(p), headers=H), timeout=30))
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.3)
    il = d.get("respData", {}).get("itemList") or []
    if not il: break
    rows += il; p += 1
    if p > 300: break
print("pages", p - 1, "rows", len(rows))
print(collections.Counter(r.get("sectNm") for r in rows).most_common(10))
# group order
seq = []
for r in rows:
    if not seq or seq[-1][0] != r.get("sectNm"): seq.append([r.get("sectNm"), 0])
    seq[-1][1] += 1
print(seq[:20])
json.dump(rows, open(f"{CACHE}/all_rows.json", "w", encoding="utf-8"), ensure_ascii=False)

# ---- build output: first 300 of the "추천상품(소상공인 기획전)" group ----
grp = [r for r in rows if (r.get("sectNm") or "").startswith("추천상품")][:300]
items = []
for i, r in enumerate(grp, 1):
    cd = r["slitmCd"]; sp = r.get("sellPrc") or None; bb = r.get("bbprc") or None
    cp = r.get("copnDcAmt") or 0
    pct = round((sp - bb) / sp * 100, 1) if sp and bb and sp > bb else None
    cond = None
    if cp:
        cond = f"선착순/기획전 쿠폰 {cp}원 할인 가능(쿠폰율 {r.get('copnDcRate')}%)"
        if r.get("slitmNm", "").startswith("[최종가"): cond += "; 상품명에 최종가 표기"
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": r.get("brndNm") or r.get("venNm") or "", "channel": "현대Hmall 소상공인 기획전(물가안정 프로젝트)",
        "product": r["slitmNm"], "model_code": cd,
        "buy_url": f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={cd}",
        "event_url": EVENT, "claimed_original_price": sp, "sale_price": bb,
        "claimed_discount_pct": pct, "conditions": cond,
        "sources": [API.format(1).replace("page=1", "page=N"), f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={cd}"],
    })
json.dump({"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
