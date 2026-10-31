import json, os, re, sys, time, datetime, urllib.request
SID = "mall-hmall-sosang-reco-2"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
API = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page={}"
EVENT = "https://www.hmall.com/md/dpl/index?sectId=2811083"
H = {"Referer": "https://www.hmall.com/", "User-Agent": "Mozilla/5.0"}
LO, HI = 301, 600
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def page(n):
    p = f"{CACHE}/p{n:03d}.json"
    if os.path.exists(p) and os.path.getsize(p) > 500:
        return json.load(open(p, encoding="utf-8"))
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API.format(n), headers=H), timeout=30)
            d = json.loads(r.read().decode("utf-8")); open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False)); return d
        except Exception as e:
            print("retry", n, e, file=sys.stderr); time.sleep(2)
    return None

allitems = []; n = 1
while True:
    d = page(n)
    if not d: print("fail page", n); break
    lst = d["respData"].get("itemList") or []
    if not lst: break
    allitems += lst; n += 1
    if n > 200: break
print("pages", n-1, "items", len(allitems))
from collections import Counter
c = Counter(i.get("sectNm") for i in allitems)
for k, v in c.most_common(): print(v, k)
reco = [i for i in allitems if (i.get("sectNm") or "").startswith("추천상품")]
print("reco", len(reco))
sel = reco[LO-1:HI]
items = []
for k, i in enumerate(sel, 1):
    sell = i.get("sellPrc") or None
    bb = i.get("bbprc") or None
    cond = []
    if i.get("copnDcAmt"): cond.append(f"쿠폰할인 {i['copnDcAmt']}원({i.get('copnDcRate')}%) 적용 시")
    if i.get("soldout"): cond.append("품절")
    sale = bb if bb and sell and bb < sell else sell
    pct = round((sell - sale) / sell * 100, 1) if sell and sale and sale < sell else None
    code = i["slitmCd"]
    items.append({
        "item_id": f"{SID}-{k:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": (i.get("brndNm") or i.get("venNm") or "").strip(),
        "channel": "현대Hmall 소상공인 기획전",
        "product": i["slitmNm"].strip(), "model_code": code,
        "buy_url": f"https://www.hmall.com/pd/pda/itemPtc?slitmCd={code}",
        "event_url": EVENT, "claimed_original_price": sell, "sale_price": sale,
        "claimed_discount_pct": pct, "conditions": "; ".join(cond) or None,
        "sources": [API.format(1).replace("page=1", "page=N")],
    })
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
