import json, os, time, datetime, urllib.request, urllib.parse
SRC = "mall-hmall-sosang-reco-4"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/mall/%s.json" % SRC
SECT = "추천상품(쿠폰 미적용)"
LO, HI = 901, 1200
EVENT = "https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page=1"
os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def get(p):
    f = "%s/p%03d.json" % (CACHE, p)
    if os.path.exists(f) and os.path.getsize(f) > 100:
        return json.load(open(f, encoding="utf-8"))
    q = urllib.parse.urlencode(dict(url="/api/hf/dp/v1/sect-mng/plansale-ancr-paging", sectId=2811083, sortType="sect_disp", listSize=20, deviceInfo="pc", page=p))
    for t in range(3):
        try:
            req = urllib.request.Request("https://www.hmall.com/md/api/cache?" + q, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.hmall.com/"})
            b = urllib.request.urlopen(req, timeout=30).read()
            open(f, "wb").write(b)
            return json.loads(b.decode("utf-8"))
        except Exception:
            time.sleep(2)
    return {}

allrows, p = [], 1
while True:
    d = get(p)
    lst = ((d.get("respData") or {}).get("itemList")) or []
    if not lst:
        break
    allrows += lst
    p += 1
    if p > 300: break
sel = [r for r in allrows if r.get("sectNm") == SECT]
print("pages", p - 1, "all", len(allrows), "sect", len(sel))
sel = sel[LO - 1:HI]
items = []
for i, r in enumerate(sel, 1):
    sp, bb = r.get("sellPrc"), r.get("bbprc")
    sale = bb if bb else sp
    pct = round((sp - sale) * 100.0 / sp, 1) if sp and sale and sp > sale else None
    cond = "섹션 '추천상품(쿠폰 미적용)'"
    if r.get("copnDcAmt"): cond += "; 쿠폰할인 %d원(%s%%) 반영된 최종가" % (r["copnDcAmt"], r.get("copnDcRate"))
    items.append({
        "item_id": "%s-%04d" % (SRC, i), "category": "mall", "source_id": SRC, "unit": None,
        "vendor": r.get("brndNm") or r.get("venNm") or "", "channel": "현대Hmall 소상공인 기획전(물가안정 프로젝트)",
        "product": r.get("slitmNm"), "model_code": r.get("slitmCd"),
        "buy_url": "https://www.hmall.com/pd/pda/itemPtc?slitmCd=%s" % r.get("slitmCd"),
        "event_url": EVENT, "claimed_original_price": sp, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": cond, "sources": [EVENT + "&page=%d" % 1]})
json.dump({"category": "mall", "source_id": SRC, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
