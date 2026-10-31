import json, os, re, sys, time, datetime, html, subprocess
SID = "mall-epost-kgf-p2"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
BASE = "https://mall.epost.go.kr"
URL = BASE + "/fo/display/plnbefDspyNewView.do"
EVENT = URL + "?plnbefId=10027801"
PAGES = range(8, 15)
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def page(n):
    p = f"{CACHE}/p{n}.html"
    if os.path.exists(p) and os.path.getsize(p) > 50000:
        return open(p, encoding="utf-8").read()
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({"plnbefId": "10027801", "pageIndex": n, "pageUnit": 40}).encode()
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(URL, data=data, headers={"User-Agent": "Mozilla/5.0"}), timeout=40)
            t = r.read().decode("utf-8", "replace"); open(p, "w", encoding="utf-8").write(t); return t
        except Exception as e:
            print("retry", n, e, file=sys.stderr); time.sleep(2)
    return ""

num = lambda s: int(re.sub(r"\D", "", s)) if s and re.sub(r"\D", "", s) else None
items = []
for n in PAGES:
    t = page(n)
    for li in re.findall(r"<li class=\"[^\"]*\">\s*<a href=\"javaScript:fn_goodsDetailView\(.*?</li>", t, re.S):
        m = re.search(r"fn_goodsDetailView\('([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'", li)
        code, pav, typ, dtl, cat = m.groups()
        img = re.search(r'<img src="(https?://[^"]+)" alt="([^"]*)"', li)
        title = html.unescape(re.search(r'<p class="tit">(.*?)</p>', li, re.S).group(1))
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r"^\d+%\s*", "", title)
        pct_m = re.search(r'icn_dis"><b>([\d.]+)</b>', li)
        unit = re.search(r'</p>\s*<span>(.*?)</span>', li, re.S)
        orig = re.search(r'판매가</span><span><em>([\d,]+)</em>', li)
        disc = re.search(r'할인가</span><span><em>([\d,]+)</em>', li)
        star = re.search(r'class="star(\d+)"', li)
        gun = re.search(r'class="gun">([\d,]+)', li)
        o = num(orig.group(1)) if orig else None
        d = num(disc.group(1)) if disc else None
        sale = d if d else o
        if d and o and d >= o: d = None
        bm = re.match(r"\[([^\]]+)\]", title)
        tips = re.findall(r'goods_tip.*?</div>', li, re.S)
        tipalts = re.findall(r'alt="([^"]+)"', tips[0]) if tips else []
        cond = ", ".join(tipalts) or None
        if 'soldout' in li.lower() or '품절' in li: cond = ((cond + ", ") if cond else "") + "품절표시"
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID,
            "unit": html.unescape(unit.group(1)).strip() if unit else None,
            "vendor": bm.group(1) if bm else "우체국쇼핑", "channel": "우체국쇼핑",
            "product": title, "model_code": code,
            "buy_url": f"{BASE}/fo/goods/goodsDetailView.do?goodsCd={code}&pavlnDivCd={pav}&goodsDispTypeCd={typ}&goodsDispTypeDtlCd={dtl}&ctgryCd={cat}",
            "image_url": img.group(1) if img else None,
            "rating": round(int(star.group(1)) / 2, 1) if star else None,
            "review_count": num(gun.group(1)) if gun else None,
            "event_url": EVENT,
            "claimed_original_price": o if d else (o if pct_m else o), "sale_price": sale,
            "claimed_discount_pct": float(pct_m.group(1)) if pct_m else None,
            "conditions": cond, "sources": [f"{URL}?plnbefId=10027801 (POST pageIndex={n}&pageUnit=40)"],
        })
    print("page", n, len(items))
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
