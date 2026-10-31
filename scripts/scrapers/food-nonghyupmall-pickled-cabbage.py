import requests, re, json, html, os, datetime
SID = "food-nonghyupmall-pickled-cabbage"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
URL = "https://www.nonghyupmall.com/BC19030R/exhPlanDetailList.nh?crnC=004943&chanC=1101&mediaD=00&mbT=00&ctgrStp="
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
p = f"{CACHE}/page1.html"
if os.path.exists(p):
    t = open(p, encoding='utf8').read()
else:
    r = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30); r.encoding = 'utf8'
    t = r.text; open(p, 'w', encoding='utf8').write(t)
# 사전 JS 템플릿 이전의 정적 렌더 영역(코너 div.tab-cont.division)만
def num(s): return int(re.sub(r'[^\d]', '', s)) if s and re.search(r'\d', s) else None
items = []; seen = set()
for sec in re.finditer(r'<div id="(\d+)" class="tab-cont division">.*?<h4 class="title2">(.*?)</h4>(.*?)(?=<div id="\d+" class="tab-cont division">|<div class="basic-more|</section>)', t, re.S):
    corner = html.unescape(sec.group(2)).strip()
    for b in sec.group(3).split('<li class="prd-list-item">')[1:]:
        m = re.search(r'class="prd-img" href="#none" data-wrs-c="(\d+)"', b)
        if not m: continue
        wc = m.group(1)
        if wc in seen: continue
        seen.add(wc)
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)" class=""', b)
        title = re.search(r'<p class="title">\s*(.*?)</p>', b, re.S)
        name = html.unescape(re.sub(r'\s+', ' ', title.group(1))).strip() if title else html.unescape(img.group(2))
        orig = re.search(r'<del>\s*([\d,]+)원', b)
        price = re.search(r'<strong class="price">\s*([\d,]+)원', b)
        star = re.search(r'data-star-rating="([\d.]+)"', b)
        rev = re.search(r'상품평(?:&nbsp;|\s)*([\d,]+)건', b)
        bul = [html.unescape(x) for x in re.findall(r"<span class=['\"]txt-bullet[^>]*>(.*?)</span>", b)]
        pb = [html.unescape(x) for x in re.findall(r"alt='([^']+)'><", b)]
        op, sp = (num(orig.group(1)) if orig else None), (num(price.group(1)) if price else None)
        bm = re.match(r'\[([^\]]+)\]\s*(.*)', name)
        vendor = bm.group(1) if bm else ''
        if not vendor or vendor in ('도착일지정',):
            m2 = re.search(r'\]\s*([^\s\]]+(?:농협|김치|영농|조합)[^\s]*)', name) or re.match(r'([^\s]+)', name.split(']')[-1].strip())
            vendor = m2.group(1) if m2 else 'NH농협몰'
        unit = re.search(r'(\d+(?:\.\d+)?\s*(?:kg|Kg|KG|g|L|ml)(?:\s*\(?\d*\s*(?:박스|봉|팩|개)\)?)?(?:\s*[xX*]\s*\d+\s*(?:박스|봉|팩|개)?)?)', name)
        cond = [corner] + bul + pb
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
            "unit": unit.group(1).strip() if unit else None,
            "vendor": vendor, "channel": "NH농협몰 26년 절임배추 특가전", "product": name, "model_code": wc,
            "buy_url": f"https://www.nonghyupmall.com/BC14010R/viewDetailPage.nh?wrsC={wc}&chanC=1101",
            "image_url": img.group(1) if img else None,
            "rating": round(float(star.group(1)) / 2, 2) if star else None,
            "review_count": num(rev.group(1)) if rev else None,
            "event_url": URL, "claimed_original_price": op, "sale_price": sp,
            "claimed_discount_pct": round((op - sp) / op * 100, 1) if op and sp and op > sp else None,
            "conditions": ", ".join(dict.fromkeys(cond)),
            "sources": [URL],
        })
out = {"category": "food", "source_id": SID, "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
print(len(items))
