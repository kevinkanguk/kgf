import json, re, html, urllib.request, urllib.parse, os, datetime
BASE = "https://www.samsung.com"
EVENT = BASE + "/sec/event/bespoke-grande-ai/"
SRC = "appliance-samsung-clothcare"
CACHE = "E:/090_ETC/kf/data/cache/html/ss"
OUT = "E:/090_ETC/kf/data/raw/catalog/appliance/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True)

def get(path, params, name):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": EVENT})
    try:
        b = urllib.request.urlopen(req, timeout=30).read()
        open(f"{CACHE}/{name}.json", "wb").write(b)
    except Exception:
        b = open(f"{CACHE}/{name}.json", "rb").read()
    return json.loads(b.decode("utf-8", "replace"))["html"]

page = open("E:/090_ETC/kf/data/cache/html/appliance-samsung-clothcare.html", encoding="utf-8", errors="replace").read()
SALE = {5255041: "인기 모델 AI 콤보", 5255042: "삼성닷컴 추천", 5255043: "타임 세일 4차", 5255044: "에어드레서"}
SUBS = {5255037: "구독 컴포넌트 1", 5255038: "구독 컴포넌트 2", 5255039: "구독 컴포넌트 3"}

def num(s):
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None

def attrs(tag):
    return dict(re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', tag))

def price_tag(h, pat):
    m = re.search(r'<div[^>]*id="%s"[^>]*>' % pat, h, re.S)
    return attrs(m.group(0)) if m else {}

rows = []
for c, nm in SALE.items():
    m = re.search(r'id="prodCard_prodList_%d"[^>]*?data-comp-en-nm\s*=\s*"([^"]*)"' % c, page, re.S)
    en = m.group(1)
    h = get("/sec/cxhr/display/selectComponentGoodsList", dict(compNo=c, compEnNm=en, layoutNo=46, svmnAmtDispYn="Y", lastPrcText="혜택가", ctaMoveStyle=1, ctaWindowStyleClassNm="_self", broadcastId=""), str(c))
    for blk in re.split(r'(?=<div class="box-product-card")', h)[1:]:
        inner = attrs(re.search(r'<div class="inner"[^>]*>', blk, re.S).group(0))
        pt = price_tag(blk, r"gdPrc_\d+_\d+_G\w+")
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        colors = re.findall(r'title|<span class="itm-color-object"[^>]*>([^<]*)</span>', blk)
        colors = [x for x in colors if x]
        rows.append(dict(kind="sale", comp=nm, product=html.unescape(inner.get("data-goods-nm", "")), model=inner.get("data-mo-code") or (mg and mg.group(1)),
                         path=mg and mg.group(2), orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")),
                         benefit=num(pt.get("data-cp-apl-expt-price")), coupon=num(pt.get("data-coupon-price")),
                         cpdc=num(inner.get("data-cp-dc-amt")), colors=colors, ctg=inner.get("data-disp-ctg-en-nm-path")))
for c, nm in SUBS.items():
    h = get("/sec/cxhr/display/selectPrdCtgCompGoodsList", dict(compNo=c, layoutNo=58, compEnNm=nm, order=0, dispTp="001", dispLine=1, moreLine=1), "c%d" % c)
    for blk in re.split(r'(?=<li class="swiper-slide)', h)[1:]:
        pt = price_tag(blk, r"prdCtgCompGoodsPrice_\d+_\d+_G\w+")
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        t = re.search(r'<p data-device="pc"><span>([^<]*)</span>', blk)
        if not mg: continue
        colors = [x for x in re.findall(r'title="색상 선택:([^"]*)"', blk)]
        rows.append(dict(kind="subs", comp=nm, product=html.unescape(t.group(1)) if t else "", model=mg.group(1), path=mg.group(2),
                         orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")), benefit=num(pt.get("data-cp-apl-expt-price")),
                         coupon=num(pt.get("data-coupon-price")), monthly=num(pt.get("data-monthly-prc")), cardben=num(pt.get("data-card-benefit-amt")),
                         months=pt.get("data-cntr-prd"), svc=pt.get("data-svc-tp-cd-nm"), colors=colors))

# dedupe
merged = {}
for r in rows:
    k = (r["kind"], r["model"], r["orig"], r["member"], r["benefit"], r.get("monthly"))
    if k in merged:
        merged[k]["comps"].append(r["comp"])
    else:
        r["comps"] = [r["comp"]]
        merged[k] = r
items = []
for i, r in enumerate(merged.values(), 1):
    path = r["path"] or ""
    buy = BASE + path if path.startswith("/") else EVENT
    comps = "/".join(dict.fromkeys(r["comps"]))
    if r["kind"] == "sale":
        sale = r["benefit"] if r["benefit"] else r["member"]
        cond = f"삼성닷컴 회원가 {r['member']:,}원" if r["member"] else ""
        if r["benefit"] and r["member"] and r["benefit"] != r["member"]:
            cond += f"; 쿠폰 적용 혜택가 {r['benefit']:,}원(쿠폰할인 {r['cpdc']:,}원)" if r["cpdc"] else f"; 혜택가 {r['benefit']:,}원"
        cond += f"; 기획전 컴포넌트: {comps}"
        if r.get("colors"): cond += "; 색상: " + ",".join(r["colors"])
        unit = "1대"
    else:
        sale = r["benefit"] or r["member"]
        cond = f"구매가(회원가) {r['member']:,}원 기준; AI 구독 시 월 {r['monthly']:,}원" if r["monthly"] else "구독 카드"
        if r["months"]: cond += f"(약정 {r['months']}년)"
        if r["svc"]: cond += f", {r['svc']}"
        if r["cardben"]: cond += f"; 삼성카드 혜택 월 {r['cardben']:,}원"
        cond += f"; 기획전 컴포넌트: {comps}"
        if r.get("colors"): cond += "; 색상: " + ",".join(r["colors"])
        unit = "1대"
    pct = round((r["orig"] - sale) / r["orig"] * 100, 1) if r["orig"] and sale and r["orig"] > sale else None
    items.append(dict(item_id=f"{SRC}-{i:04d}", category="appliance", source_id=SRC, unit=unit, vendor="삼성전자", channel="삼성닷컴",
                      product=r["product"], model_code=r["model"], buy_url=buy, event_url=EVENT,
                      claimed_original_price=r["orig"], sale_price=sale, claimed_discount_pct=pct, conditions=cond,
                      price_60d_low=None, price_60d_typical=None, price_history_note=None,
                      sources=[EVENT, buy], verify_status=None, verify_note=None, confidence=None))
json.dump(dict(category="appliance", source_id=SRC, collected_at="2026-10-31", items=items), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(rows), len(items))
