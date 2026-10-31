import json, os, re, time, collections, urllib.request
from concurrent.futures import ThreadPoolExecutor
ROOT = "E:/090_ETC/kf"
SID = "mall-hmall-sosang-reco-6"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
API = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page={}"
EVENT = "https://www.hmall.com/md/dpl/index?sectId=2811083"
SECT = "추천상품(쿠폰 미적용)"
LO, HI = 1501, 1739
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
IMGC = f"{CACHE}/img"; os.makedirs(IMGC, exist_ok=True)
def get_img(code):
    fp = f"{IMGC}/{code}.txt"
    if os.path.exists(fp): return open(fp, encoding="utf-8").read() or None
    url = None
    for t in range(3):
        try:
            h = urllib.request.urlopen(urllib.request.Request(f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={code}", headers=H), timeout=30).read().decode("utf8", "ignore")
            m = re.search(r"https://image\.hmall\.com/static/[^\"'\s]*?" + code + r"_0\.\w+[^\"'\s]*", h)
            url = m.group(0).replace("&amp;", "&") if m else None
            break
        except Exception:
            time.sleep(2)
    open(fp, "w", encoding="utf-8").write(url or "")
    return url
with ThreadPoolExecutor(6) as ex:
    imgs = dict(zip([r["slitmCd"] for r in sel], ex.map(get_img, [r["slitmCd"] for r in sel])))
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
        "image_url": imgs.get(code), "rating": (float(r["itemEvalEvgScrg"]) if r.get("itemEvalEvgScrg") else None), "review_count": (int(r["reviewCnt"]) if r.get("reviewCnt") is not None else None), "conditions": cond, "sources": [API.format(1), f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={code}"],
    })
out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
