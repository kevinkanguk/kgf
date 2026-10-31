import re, json, time, os, html, requests
ROOT = "E:/090_ETC/kf"
SID = "mall-epost-kgf-p6"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
BASE = "https://mall.epost.go.kr"
EVENT = f"{BASE}/fo/display/plnbefDspyNewView.do?plnbefId=10027801"
PAGES = range(36, 43)
s = requests.Session(); s.headers.update({"User-Agent": "Mozilla/5.0"})
os.makedirs(CACHE, exist_ok=True)

def get(p):
    path = f"{CACHE}/p{p}.html"
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return open(path, encoding="utf8").read()
    for _ in range(4):
        try:
            r = s.post(f"{BASE}/fo/display/plnbefDspyNewView.do",
                       data={"plnbefId": "10027801", "pageIndex": p, "pageUnit": 40}, timeout=40)
            r.encoding = "utf-8"
            if r.status_code == 200 and "fn_goodsDetailView('" in r.text:
                open(path, "w", encoding="utf8").write(r.text); time.sleep(0.4)
                return r.text
        except Exception:
            pass
        time.sleep(2)
    return None

num = lambda t: int(t.replace(",", ""))
items, seen, issues = [], set(), []
for p in PAGES:
    h = get(p)
    if h is None:
        issues.append(f"fetch fail page {p}"); continue
    for x in re.split(r"<li class=.{0,3}>\s*<a href=.javaScript:fn_goodsDetailView", h.split('class="list_box  imglist"')[-1])[1:]:
        m = re.search(r"\('([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'", x)
        gc, pav, dt, dd, ct = m.groups()
        if gc in seen: continue
        seen.add(gc)
        img = re.search(r'<div class="goods_img">.*?<img src="([^"]+)" alt="[^"]*" />\s*</div>', x, re.S)
        tit = re.search(r'<p class="tit">(.*?)</p>', x, re.S).group(1)
        pct = re.search(r'icn_dis"><b>([\d.]+)</b>', tit)
        tit = re.sub(r'<span class="icn_dis">.*?</span>', "", tit, flags=re.S)
        tit = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", tit))).strip()
        um = re.search(r'</p>\s*<span>(.*?)</span>\s*<div class="price">', x, re.S)
        unit = html.unescape(um.group(1)).strip() if um else None
        pr = re.search(r'<div class="price">(.*?)</div>', x, re.S).group(1)
        vals = [num(v) for v in re.findall(r'<em>([\d,]+)</em>', pr)]
        orig = sale = None
        if len(vals) >= 2: orig, sale = vals[0], vals[1]
        elif len(vals) == 1: sale = vals[0]
        else: issues.append(f"no price {gc}")
        st = re.search(r'class="star(\d+)"', x)
        rating = round(int(st.group(1)) / 2, 1) if st else None
        rc = re.search(r'class="gun">([\d,]+)', x)
        rv = num(rc.group(1)) if rc else None
        if not rv: rating = None if st is None or int(st.group(1)) == 0 else rating
        dp = float(pct.group(1)) if pct else None
        if dp is None and orig and sale and orig > sale:
            dp = round((orig - sale) / orig * 100, 1)
        items.append({
            "item_id": None, "category": "mall", "source_id": SID, "unit": unit or None,
            "vendor": "우체국쇼핑", "channel": "우체국쇼핑 코리아그랜드페스타", "product": tit, "model_code": gc,
            "buy_url": f"{BASE}/fo/goods/goodsDetailView.do?goodsCd={gc}&pavlnDivCd={pav}&goodsDispTypeCd={dt}&goodsDispTypeDtlCd={dd}&ctgryCd={ct}",
            "image_url": img.group(1) if img else None, "rating": rating, "review_count": rv,
            "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale,
            "claimed_discount_pct": dp, "conditions": None,
            "sources": [EVENT + f"#pages={p}"],
            "verify_status": None, "verify_note": f"우체국쇼핑 기획전 10027801 {p}페이지(40개/페이지)", "confidence": None})
for i, it in enumerate(items, 1):
    it["item_id"] = f"{SID}-{i:04d}"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("TOTAL", len(items), issues)
