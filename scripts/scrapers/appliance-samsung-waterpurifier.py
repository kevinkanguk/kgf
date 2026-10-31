import json, re, html, os, urllib.request, urllib.parse
BASE = "https://www.samsung.com"
EVENT = BASE + "/sec/event/ai-subs-kitchen/water-purifier/"
SRC = "appliance-samsung-waterpurifier"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/appliance/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120", "Accept-Language": "ko-KR,ko;q=0.9", "Referer": EVENT}

def fetch(url, name):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
        if b"Access Denied" in b[:300]: raise IOError("denied")
        open(f"{CACHE}/{name}", "wb").write(b)
    except Exception:
        b = open(f"{CACHE}/{name}", "rb").read()
    return b

def num(s):
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None

def attrs(tag):
    return dict(re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', tag))

page = fetch(EVENT, "page.html").decode("utf-8", "replace")
comps = re.findall(r'id="prdCtgCompo_(\d+)"', page)
rows = []
for c in comps:
    en = re.search(r'id="prdCtgCompo_%s".*?data-comp-en-nm="([^"]*)"' % c, page, re.S).group(1)
    q = dict(compNo=c, layoutNo=58, compEnNm="x", order=0, dispTp="002", dispLine=1, moreLine=1)
    h = json.loads(fetch(BASE + "/sec/cxhr/display/selectPrdCtgCompGoodsList?" + urllib.parse.urlencode(q), "c%s.json" % c).decode("utf-8", "replace"))["html"]
    for blk in re.split(r'(?=<li class="swiper-slide)', h)[1:]:
        m = re.search(r'<div[^>]*id="prdCtgCompGoodsPrice_[^"]*"[^>]*>', blk, re.S)
        pt = attrs(m.group(0)) if m else {}
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        t = re.search(r'<p data-device="pc"><span>([^<]*)</span>', blk)
        im = re.search(r'data-src="([^"]*images\.samsung\.com[^"]*)"', blk)
        if not mg: continue
        u = im.group(1) if im else None
        if u and u.startswith("//"): u = "https:" + u
        rows.append(dict(comp=en, product=html.unescape(t.group(1)).strip() if t else "", model=mg.group(1), path=mg.group(2),
                         orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")), benefit=num(pt.get("data-cp-apl-expt-price")),
                         monthly=num(pt.get("data-monthly-prc")), cardben=num(pt.get("data-card-benefit-amt")),
                         months=pt.get("data-cntr-prd"), svc=pt.get("data-svc-tp-cd-nm"),
                         colors=re.findall(r'title="색상 선택:([^"]*)"', blk), image=u))
merged = {}
for r in rows:
    k = (r["model"], r["orig"], r["member"], r["benefit"], r["monthly"])
    if k in merged: merged[k]["comps"].append(r["comp"])
    else:
        r["comps"] = [r["comp"]]; merged[k] = r

def rating(path, model):
    url = BASE + path.split("?")[0]
    try:
        t = fetch(url, "p_%s.html" % model).decode("utf-8", "replace")
    except Exception:
        return None, None
    a = re.search(r'ratingValue"\s*:\s*"?([\d.]+)', t); b = re.search(r'ratingCount"\s*:\s*"?(\d+)', t)
    return (float(a.group(1)) if a else None), (int(b.group(1)) if b else None)

items = []
for i, r in enumerate(merged.values(), 1):
    path = r["path"] or ""
    buy = BASE + path if path.startswith("/") else EVENT
    rt, rc = rating(path, r["model"]) if path.startswith("/") else (None, None)
    sale = r["benefit"] or r["member"]
    cond = f"구매가(회원가) {r['member']:,}원 기준" if r["member"] else "구독 카드"
    if r["benefit"] and r["member"] and r["benefit"] != r["member"]: cond += f"; 쿠폰 적용 혜택가 {r['benefit']:,}원"
    if r["monthly"]: cond += f"; AI 구독 시 월 {r['monthly']:,}원" + (f"(약정 {r['months']}년)" if r["months"] else "")
    if r["svc"]: cond += f", {r['svc']}"
    if r["cardben"]: cond += f"; 삼성카드 혜택 월 {r['cardben']:,}원"
    cond += "; 기획전 컴포넌트: " + "/".join(dict.fromkeys(r["comps"]))
    if r["colors"]: cond += "; 색상: " + ",".join(r["colors"])
    pct = round((r["orig"] - sale) / r["orig"] * 100, 1) if r["orig"] and sale and r["orig"] > sale else None
    items.append(dict(item_id=f"{SRC}-{i:04d}", category="appliance", source_id=SRC, unit="1대", vendor="삼성전자", channel="삼성닷컴",
                      product=r["product"], model_code=r["model"], buy_url=buy, image_url=r["image"], rating=rt, review_count=rc,
                      event_url=EVENT, claimed_original_price=r["orig"], sale_price=sale, claimed_discount_pct=pct, conditions=cond,
                      price_60d_low=None, price_60d_typical=None, price_history_note=None,
                      sources=[EVENT, buy], verify_status=None, verify_note=None, confidence=None))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="appliance", source_id=SRC, collected_at="2026-10-31", items=items), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(rows), len(items))
