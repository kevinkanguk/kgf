import requests, re, json, os, html, time, datetime, collections
SID = "fashion_beauty-epost-kgf-apparel-beauty"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/fashion_beauty/{SID}.json"
PID = "10027801"
URL = f"https://mall.epost.go.kr/fo/display/plnbefDspyNewView.do?plnbefId={PID}"
CAT_PREFIX = "106"  # 의류/뷰티/잡화
os.makedirs(CACHE, exist_ok=True)
s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"

def page(n):
    fp = f"{CACHE}/page_{n:03d}.html"
    if os.path.exists(fp):
        return open(fp, encoding="utf-8").read()
    for _ in range(3):
        r = s.post(URL, data={"pageIndex": n, "pageUnit": 60, "listType": "imglist", "orderKey": "", "searchMCtgryCd": "", "searchSCtgryCd": "", "srchGoodsNm": "", "pavlnDivCd": ""}, timeout=40)
        if r.status_code == 200: break
        time.sleep(2)
    r.encoding = "utf-8"
    open(fp, "w", encoding="utf-8").write(r.text)
    time.sleep(0.3)
    return r.text

def num(t):
    t = re.sub(r"[^\d]", "", t or "")
    return int(t) if t else None

def parse(h):
    out = []
    for li in re.findall(r"<li class=\"\">\s*<a href=\"javaScript:fn_goodsDetailView.*?</li>", h, re.S):
        m = re.search(r"fn_goodsDetailView\('([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'\)", li)
        code, pav, dt, ev, ct = m.groups()
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)"', li)
        tit = re.search(r'<p class="tit">(.*?)</p>', li, re.S)
        disc = re.search(r'<b>(\d+(?:\.\d+)?)</b>%', tit.group(1)) if tit else None
        name = html.unescape(re.sub(r"<[^>]+>", "", tit.group(1)).strip()) if tit else None
        name = re.sub(r"^\d+(\.\d+)?%\s*", "", name or "")
        sub = re.search(r"</p>\s*<span>(.*?)</span>", li, re.S)
        orig = re.search(r"판매가</span><span><em>([\d,]+)</em>", li)
        sale = re.search(r"할인가</span><span><em>([\d,]+)</em>", li)
        star = re.search(r"평점 ([\d.]+)점", li)
        gun = re.search(r'class="gun">([\d,]+)건', li)
        out.append(dict(code=code, pav=pav, ev=ev, ct=ct,
            image=img.group(1) if img else None, alt=html.unescape(img.group(2)) if img else None,
            name=name, sub=html.unescape(sub.group(1).strip()) if sub else None,
            orig=num(orig.group(1)) if orig else None, sale=num(sale.group(1)) if sale else None,
            disc=float(disc.group(1)) if disc else None,
            star=float(star.group(1)) if star else None, gun=num(gun.group(1)) if gun else None))
    return out

allit = []; seen = set(); n = 1
while True:
    h = page(n)
    its = parse(h)
    if not its: break
    new = [i for i in its if i["code"] not in seen]
    if not new: break
    for i in new: seen.add(i["code"]); allit.append(i)
    print(n, len(its), len(allit), flush=True)
    n += 1
print("total", len(allit), collections.Counter(i["ct"][:3] for i in allit))
json.dump(allit, open(f"{CACHE}/all_parsed.json", "w", encoding="utf-8"), ensure_ascii=False)
sel = [i for i in allit if i["ct"].startswith(CAT_PREFIX)]
def vendor(i):
    fp = f"{CACHE}/detail_{i['code']}.html"
    if os.path.exists(fp):
        h = open(fp, encoding="utf-8").read()
    else:
        r = s.get(f"https://mall.epost.go.kr/fo/goods/goodsDetailView.do?goodsCd={i['code']}&pavlnDivCd={i['pav']}&goodsDispTypeCd=03&goodsDispTypeDtlCd={i['ev']}&ctgryCd={i['ct']}", timeout=40)
        r.encoding = "utf-8"; h = r.text
        open(fp, "w", encoding="utf-8").write(h); time.sleep(0.3)
    m = re.search(r'공급업체</div>\s*<div class="txt">\s*<p>\s*([^<]+?)\s*<a', h)
    return html.unescape(m.group(1)).strip() if m else None

items = []
for k, i in enumerate(sel, 1):
    sp = i["sale"]; op = i["orig"]
    if sp is None and op is not None: sp, op = op, None  # 할인 없음: 판매가만 존재
    pct = i["disc"]
    if pct is None and op and sp and op > sp: pct = round((op - sp) / op * 100, 1)
    rating = round(i["star"] / 2, 1) if i["star"] else None  # 사이트 평점은 10점 만점
    items.append({
        "item_id": f"{SID}-{k:04d}", "category": "fashion_beauty", "source_id": SID,
        "unit": i["sub"], "vendor": vendor(i) or "우체국쇼핑 입점업체", "channel": "우체국쇼핑 코그페 소상공인 브랜드관(소상공인 동행)",
        "product": i["name"] or i["alt"], "model_code": i["code"],
        "buy_url": f"https://mall.epost.go.kr/fo/goods/goodsDetailView.do?goodsCd={i['code']}&pavlnDivCd={i['pav']}&goodsDispTypeCd=03&goodsDispTypeDtlCd={i['ev']}&ctgryCd={i['ct']}",
        "image_url": i["image"], "rating": rating, "review_count": i["gun"],
        "event_url": URL, "claimed_original_price": op, "sale_price": sp,
        "claimed_discount_pct": pct, "conditions": None, "sources": [URL],
    })
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "fashion_beauty", "source_id": SID, "collected_at": "2026-10-31", "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", len(items))
