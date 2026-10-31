import json, os, time, urllib.request
ROOT = "E:/090_ETC/kf"
SID = "food-hmall-soosan"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
API = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2829600&sortType=sect_disp&listSize=20&deviceInfo=pc&page={}"
EVENT = "https://www.hmall.com/pd/dpa/searchSpexSectItem?sectId=2829600"
H = {"Referer": "https://www.hmall.com/", "User-Agent": "Mozilla/5.0"}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
rows = []; p = 1
while True:
    fp = f"{CACHE}/p{p}.json"
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        d = json.load(open(fp, encoding="utf-8"))
    else:
        d = json.load(urllib.request.urlopen(urllib.request.Request(API.format(p), headers=H), timeout=30))
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False); time.sleep(0.3)
    il = d.get("respData", {}).get("itemList") or []
    if not il: break
    rows += il; p += 1
    if p > 300: break
seen = set(); items = []
def img(cd, nm):
    if not nm: return None
    c = cd
    return f"https://image.hmall.com/static/{c[7]}/{c[6]}/{c[4:6]}/{c[2:4]}/{nm}?RS=300x300"
for r in rows:
    cd = r["slitmCd"]
    if cd in seen: continue
    seen.add(cd)
    sp = r.get("sellPrc") or None; bb = r.get("bbprc") or None
    cp = r.get("copnDcAmt") or 0
    pct = round((sp - bb) / sp * 100, 1) if sp and bb and sp > bb else None
    cond = f"쿠폰 {cp}원 할인 가능(쿠폰율 {r.get('copnDcRate')}%)" if cp else None
    rc = r.get("reviewCnt") or int(r.get("itemEvalCnt") or 0) or None
    rt = r.get("itemEvalEvgScrg") if rc else None
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID, "unit": None,
        "vendor": r.get("brndNm") or r.get("venNm") or "", "channel": "현대Hmall 대한민국 수산대전",
        "product": r["slitmNm"], "model_code": cd,
        "buy_url": f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={cd}",
        "image_url": img(cd, r.get("itemBaseImgNm")), "rating": rt, "review_count": rc,
        "event_url": EVENT, "claimed_original_price": sp, "sale_price": bb,
        "claimed_discount_pct": pct, "conditions": cond,
        "sources": [API.format("N"), f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={cd}"],
    })
json.dump({"category": "food", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("pages", p - 1, "rows", len(rows), "saved", len(items))
