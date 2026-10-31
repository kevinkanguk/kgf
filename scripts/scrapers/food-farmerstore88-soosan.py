import re, json, html, os, time, datetime, requests
SID = "food-farmerstore88-soosan"; CAT = "food"
BASE = "https://www.farmerstore88.com"
EVENT = BASE + "/Goods/List?cno=460&pageType=DEFAULT&ch_idx=407"
OUT = f"E:/090_ETC/kf/data/raw/catalog/{CAT}/{SID}.json"
CACHE = f"E:/090_ETC/kf/data/cache/html/{SID}"
H = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json; charset=utf-8", "Referer": EVENT}
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
s = requests.Session(); s.get(EVENT, headers=H, timeout=30)
def won(x):
    m = re.search(r'([\d,]+)\s*원', x or ''); return int(m.group(1).replace(',', '')) if m else None
blocks = []; page = 1
while True:
    p = dict(tagno=0, cno=460, isview='Y', istime=0, islike=False, sval='', sortby=0, usortby=5, DateDuration=1,
             eventidx=0, gpg_idx=0, pageType='DEFAULT', listType='CHANGE', listLayoutType='5_DIV1', curOS='AOS', sc_idx=0, page=page, rows=24)
    r = s.post(BASE + '/Goods/GetGoodsListNew', data=json.dumps({'param': p, 'list_template_name': '/Views/Templates/LIST/5_DIV.cshtml', 'item_template_name': '', 'igm_idx': '0'}), headers=H, timeout=30)
    d = r.json(); open(f"{CACHE}/api{page}.json", 'w', encoding='utf-8').write(r.text)
    h = d['data']['data']; n = d['data']['cnt']
    blocks += re.split(r'<div class="product-type3">', h)[1:]
    if n < 24: break
    page += 1
items = []; seen = set()
for b in blocks:
    code = re.search(r'data-mgcode="([^"]+)"', b).group(1)
    if code in seen: continue
    seen.add(code)
    name = html.unescape(re.search(r"class='product-name'>\s*(.*?)\s*</div>", b, re.S).group(1)).strip()
    img = re.search(r"class='product-image' data-src=\"([^\"]+)\"", b)
    orig = re.search(r"<p class='price-from'><s>([^<]*)</s>", b)
    dc = re.search(r"<p class='dc'>\s*([\d.]+)%", b)
    price = re.search(r"<p class='price'>([^<]*)</p>", b)
    url = f"{BASE}/Goods/Detail/{code}"
    unit = None
    fp = f"{CACHE}/{code}.html"
    try:
        if not os.path.exists(fp):
            t = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).content.decode('utf-8', 'replace')
            open(fp, 'w', encoding='utf-8').write(t); time.sleep(0.3)
        else: t = open(fp, encoding='utf-8').read()
        m = re.search(r'상품구성 및 내용량</th>\s*<td>(.*?)</td>', t, re.S)
        if m: unit = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))).strip()[:200] or None
    except Exception: pass
    o = won(orig.group(1)) if orig else None
    items.append({"item_id": f"{SID}-{len(items)+1:04d}", "category": CAT, "source_id": SID, "unit": unit,
        "vendor": "파머스토어88(우리동네)", "channel": "파머스토어 수산대전", "product": name, "model_code": code,
        "buy_url": url, "image_url": img.group(1) if img else None, "rating": None, "review_count": None,
        "event_url": EVENT, "claimed_original_price": o, "sale_price": won(price.group(1)) if price else None,
        "claimed_discount_pct": float(dc.group(1)) if dc else None, "conditions": None, "sources": [EVENT, url]})
out = {"category": CAT, "source_id": SID, "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
