import json, re, html, urllib.request, urllib.parse, os
BASE = "https://www.samsung.com"
EVENT = BASE + "/sec/event/air-cleaner/"
SRC = "appliance-samsung-aircleaner"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/appliance/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True)

def fetch(url, name):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": EVENT}), timeout=40).read()
        open(f"{CACHE}/{name}", "wb").write(b)
    except Exception:
        b = open(f"{CACHE}/{name}", "rb").read()
    return b

def api(path, params, name):
    return json.loads(fetch(BASE + path + "?" + urllib.parse.urlencode(params), name + ".json").decode("utf-8", "replace"))["html"]

def num(s):
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None

def attrs(tag):
    return dict(re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', tag))

def img(blk):
    m = re.search(r'data-src="([^"]*images\.samsung\.com[^"]*)"', blk)
    if not m: return None
    u = m.group(1)
    return ("https:" + u) if u.startswith("//") else u

page = fetch(EVENT, "page.html").decode("utf-8", "replace")
sale_comps = re.findall(r'id="prodCard_prodList_(\d+)"\s*data-comp-no\s*=\s*"\d+"\s*data-comp-en-nm\s*=\s*"([^"]*)"', page)
sub_comps = [(c, "x") for c in re.findall(r'id="prdCtgCompo_(\d+)"', page)]
rows = []
for c, en in sale_comps:
    h = api("/sec/cxhr/display/selectComponentGoodsList", dict(compNo=c, compEnNm=en, layoutNo=46, svmnAmtDispYn="Y", lastPrcText="혜택가", ctaMoveStyle=1, ctaWindowStyleClassNm="_self", broadcastId=""), c)
    for blk in re.split(r'(?=<div class="box-product-card")', h)[1:]:
        inner = attrs(re.search(r'<div class="inner"[^>]*>', blk, re.S).group(0))
        pt = attrs(re.search(r'<div[^>]*class="card-price"[^>]*>', blk, re.S).group(0))
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        cmp_ = re.search(r'<input type="hidden" name="cardCompareInfo"[^>]*>', blk, re.S)
        ca = attrs(cmp_.group(0)) if cmp_ else {}
        colors = [x.strip() for x in re.findall(r'<span class="itm-color-object"[^>]*>([^<]*)</span>', blk) if x.strip()]
        rows.append(dict(kind="sale", comp=en, product=html.unescape(inner.get("data-goods-nm", "")),
                         model=inner.get("data-mo-code") or (mg and mg.group(1)), path=mg and mg.group(2),
                         orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")),
                         benefit=num(pt.get("data-cp-apl-expt-price")), cpdc=num(inner.get("data-cp-dc-amt")),
                         colors=colors, image=img(blk),
                         rating=float(ca["data-review-grade"]) if ca.get("data-review-grade") else None,
                         reviews=num(ca.get("data-review-count"))))
for c, en in sub_comps:
    h = api("/sec/cxhr/display/selectPrdCtgCompGoodsList", dict(compNo=c, layoutNo=58, compEnNm=en, order=0, dispTp="001", dispLine=1, moreLine=1), "c" + c)
    for blk in re.split(r'(?=<li class="swiper-slide)', h)[1:]:
        m = re.search(r'<div[^>]*id="prdCtgCompGoodsPrice_[^"]*"[^>]*>', blk, re.S)
        pt = attrs(m.group(0)) if m else {}
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        t = re.search(r'<p data-device="pc"><span>([^<]*)</span>', blk)
        if not mg: continue
        rows.append(dict(kind="subs", comp="구독 컴포넌트", product=html.unescape(t.group(1)) if t else "", model=mg.group(1), path=mg.group(2),
                         orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")), benefit=num(pt.get("data-cp-apl-expt-price")),
                         monthly=num(pt.get("data-monthly-prc")), cardben=num(pt.get("data-card-benefit-amt")),
                         months=pt.get("data-cntr-prd"), svc=pt.get("data-svc-tp-cd-nm"),
                         colors=re.findall(r'title="색상 선택:([^"]*)"', blk), image=img(blk), rating=None, reviews=None))

merged = {}
for r in rows:
    k = (r["kind"], r["model"], r["orig"], r["member"], r["benefit"], r.get("monthly"))
    if k in merged:
        merged[k]["comps"].append(r["comp"])
        for f in ("image", "rating", "reviews"):
            if merged[k].get(f) is None: merged[k][f] = r.get(f)
    else:
        r["comps"] = [r["comp"]]
        merged[k] = r
# fill rating/image for subs cards from sale cards of same model
by_model = {r["model"]: r for r in merged.values() if r["kind"] == "sale"}
for r in merged.values():
    s = by_model.get(r["model"])
    if r["kind"] == "subs" and s:
        for f in ("image", "rating", "reviews"):
            if r.get(f) is None: r[f] = s.get(f)
items = []
for i, r in enumerate(merged.values(), 1):
    path = r["path"] or ""
    buy = BASE + path if path.startswith("/") else EVENT
    comps = "/".join(dict.fromkeys(r["comps"]))
    sale = r["benefit"] or r["member"]
    if r["kind"] == "sale":
        cond = f"삼성닷컴 회원가 {r['member']:,}원" if r["member"] else ""
        if r["benefit"] and r["member"] and r["benefit"] != r["member"]:
            cond += f"; 쿠폰 적용 혜택가 {r['benefit']:,}원" + (f"(쿠폰할인 {r['cpdc']:,}원)" if r["cpdc"] else "")
    else:
        cond = f"구매가(회원가) {r['member']:,}원 기준" if r["member"] else "구독 카드"
        if r.get("monthly"): cond += f"; AI 구독 시 월 {r['monthly']:,}원" + (f"(약정 {r['months']}년)" if r["months"] else "")
        if r.get("svc"): cond += f", {r['svc']}"
        if r.get("cardben"): cond += f"; 삼성카드 혜택 월 {r['cardben']:,}원"
    cond += f"; 기획전 컴포넌트: {comps}"
    if r.get("colors"): cond += "; 색상: " + ",".join(r["colors"])
    pct = round((r["orig"] - sale) / r["orig"] * 100, 1) if r["orig"] and sale and r["orig"] > sale else None
    items.append(dict(item_id=f"{SRC}-{i:04d}", category="appliance", source_id=SRC, unit="1대", vendor="삼성전자", channel="삼성닷컴",
                      product=r["product"], model_code=r["model"], buy_url=buy, image_url=r["image"], rating=r["rating"], review_count=r["reviews"],
                      event_url=EVENT, claimed_original_price=r["orig"], sale_price=sale, claimed_discount_pct=pct, conditions=cond,
                      price_60d_low=None, price_60d_typical=None, price_history_note=None,
                      sources=[EVENT, buy], verify_status=None, verify_note=None, confidence=None))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="appliance", source_id=SRC, collected_at="2026-10-31", items=items), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(rows), len(items))
