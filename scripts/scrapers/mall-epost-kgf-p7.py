import re, json, os, time, html, subprocess, datetime
import requests
SID = "mall-epost-kgf-p7"
BASE = "https://mall.epost.go.kr"
PLN = "10027801"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EVENT = f"{BASE}/fo/display/plnbefDspyNewView.do?plnbefId={PLN}"
os.makedirs(CACHE, exist_ok=True)
s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
def num(t): return int(t.replace(",", "")) if t else None
items = []; seen = set()
for p in range(43, 50):
    f = f"{CACHE}/p{p}.html"
    if os.path.exists(f) and p != 1 or (p == 1 and os.path.exists(f)):
        h = open(f, encoding="utf-8").read()
    else:
        h = s.post(BASE + "/fo/display/plnbefDspyNewView.do", data={"plnbefId": PLN, "pageIndex": p, "pageUnit": 40}).text
        open(f, "w", encoding="utf-8").write(h); time.sleep(0.5)
    for li in re.findall(r"<li class=\"\">(.*?)</li>", h, re.S):
        m = re.search(r"fn_goodsDetailView\('([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'\)", li)
        if not m: continue
        cd, pav, typ, dtl, cat = m.groups()
        if cd in seen: continue
        seen.add(cd)
        img = re.search(r'<img src="(https?://[^"]+)" alt="([^"]*)"', li)
        pct = re.search(r'icn_dis"><b>([\d.]+)</b>', li)
        sub = re.search(r'<p class="tit">.*?</p>\s*<span>(.*?)</span>', li, re.S)
        name = html.unescape(img.group(2)).strip() if img else cd
        orig = re.search(r'판매가</span><span><em>([\d,]+)', li)
        disc = re.search(r'할인가</span><span><em>([\d,]+)', li)
        star = re.search(r'class="star(\d+)"', li)
        gun = re.search(r'class="gun">([\d,]+)건', li)
        o = num(orig.group(1)) if orig else None
        d = num(disc.group(1)) if disc else None
        if d is not None:
            original, sale = o, d
        else:
            original, sale = None, o
        title = re.search(r'<p class="tit">(.*?)</p>', li, re.S)
        brand = html.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else name
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}",
            "category": "mall", "source_id": SID,
            "unit": html.unescape(sub.group(1)).strip() if sub else None,
            "vendor": "우체국쇼핑", "channel": "우체국쇼핑 코그페 기획전",
            "product": name, "model_code": cd,
            "buy_url": f"{BASE}/fo/goods/goodsDetailView.do?goodsCd={cd}&pavlnDivCd={pav}&goodsDispTypeCd={typ}&goodsDispTypeDtlCd={dtl}&ctgryCd={cat}",
            "image_url": img.group(1) if img else None,
            "rating": (round(int(star.group(1)) / 2, 1) if star and int(star.group(1)) > 0 else None),
            "review_count": num(gun.group(1)) if gun else None,
            "event_url": EVENT,
            "claimed_original_price": original, "sale_price": sale,
            "claimed_discount_pct": float(pct.group(1)) if pct else None,
            "conditions": None,
            "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
            "sources": [EVENT], "verify_status": None, "verify_note": None, "confidence": None})
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
