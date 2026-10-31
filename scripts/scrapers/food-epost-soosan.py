import re, json, os, time, html, datetime, requests
SID = "food-epost-soosan"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
B = "https://mall.epost.go.kr"
EV = B + "/fo/display/plnbefDspyNewView.do?plnbefId=10027888"
s = requests.Session(); s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
os.makedirs(CACHE, exist_ok=True)

def page(pg):
    p = f"{CACHE}/p{pg}.html"
    if os.path.exists(p): return open(p, encoding="utf-8").read()
    for i in range(4):
        try:
            r = s.post(EV, data={"pageIndex": pg, "pageUnit": 40, "listType": "imglist"}, timeout=40)
            if r.status_code == 200:
                r.encoding = "utf-8"; open(p, "w", encoding="utf-8").write(r.text); return r.text
        except Exception: pass
        time.sleep(2)
    return ""

li_re = re.compile(r"<li class=\"[^\"]*\">\s*<a href=\"[jJ]ava[sS]cript:fn_goodsDetailView\('([^']+)','([^']*)','([^']*)','([^']*)','(\d*)'\);\">(.*?)</li>", re.S)
seen = {}; issues = []; prev = None
for pg in range(1, 60):
    t = page(pg)
    if not t: issues.append(f"fetch fail p{pg}"); break
    its = li_re.findall(t)
    codes = [i[0] for i in its]
    if not codes or codes == prev: break
    prev = codes
    for code, pav, dt, dd, ctg, body in its:
        if code in seen: continue
        img = re.search(r'<img src="([^"]*goods[^"]*)" alt="([^"]*)"', body)
        tit = re.search(r'<p class="tit">(.*?)</p>', body, re.S)
        product = None
        if tit:
            product = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", tit.group(1))).strip())
            product = re.sub(r"^\d+\s*%\s*", "", product)
        elif img: product = html.unescape(img.group(2))
        unit = re.search(r'</p>\s*<span>\s*([^<]*?)\s*</span>', body)
        pct = re.search(r'<b>(\d+)</b>%', body)
        orig = re.search(r'판매가</span><span><em>([\d,]+)</em>', body)
        sale = re.search(r'할인가</span><span><em>([\d,]+)</em>', body)
        if not sale:
            m = re.findall(r'<em>([\d,]+)</em>원', body)
            sale_v = int(m[-1].replace(",", "")) if m else None
        else: sale_v = int(sale.group(1).replace(",", ""))
        o = int(orig.group(1).replace(",", "")) if orig else None
        if o is not None and sale_v == o and not sale: o = None
        star = re.search(r'평점 ([\d.]+)점', body)
        gun = re.search(r'<span class="gun">([\d,]+)건', body)
        tips = re.findall(r'icon_tip[^"]*" alt="([^"]*)"', body)
        seen[code] = dict(pav=pav, dt=dt, dd=dd, ctg=ctg, product=product, unit=unit.group(1) if unit else None,
            img=img.group(1) if img else None, orig=o, sale=sale_v, pct=float(pct.group(1)) if pct else None,
            rating=round(float(star.group(1)) / 2, 2) if star else None,
            rc=int(gun.group(1).replace(",", "")) if gun else None, tips=tips)
    print(pg, len(seen), flush=True)

items = []
for n, (code, d) in enumerate(seen.items(), 1):
    url = f"{B}/fo/goods/goodsDetailView.do?goodsCd={code}&pavlnDivCd={d['pav']}&goodsDispTypeCd={d['dt']}&goodsDispTypeDtlCd={d['dd']}&ctgryCd={d['ctg']}"
    items.append({"item_id": f"{SID}-{n:04d}", "category": "food", "source_id": SID,
        "unit": d["unit"], "vendor": "우체국쇼핑", "channel": "우체국쇼핑 수산대전", "product": d["product"],
        "model_code": code, "buy_url": url, "image_url": d["img"], "rating": d["rating"], "review_count": d["rc"],
        "event_url": EV, "claimed_original_price": d["orig"], "sale_price": d["sale"],
        "claimed_discount_pct": d["pct"], "conditions": ", ".join(d["tips"]) or None, "sources": [url]})
out = {"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat(), "items": items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("count", len(items), issues)
