import re, json, html, os, requests
SID = "food-nonghyupmall-main-nonghal"
BASE = "E:/090_ETC/kf"
URL = "https://www.nonghyupmall.com/"
cache = f"{BASE}/data/cache/html/{SID}/main.html"
if os.path.exists(cache):
    t = open(cache, encoding="utf-8", errors="replace").read()
else:
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30); r.encoding = "utf-8"; t = r.text
    open(cache, "w", encoding="utf-8").write(t)
num = lambda s: int(re.sub(r"[^\d]", "", s)) if s and re.search(r"\d", s) else None
blocks = re.split(r'<li class="item-box[^"]*">', t)[1:]
items, seen = [], set()
for b in blocks:
    w = re.search(r'data-wrs-c="(\d+)"', b)
    if not w or w.group(1) in seen: continue
    wid = w.group(1)
    img = re.search(r'class="prd-img".*?<img src="([^"]+)" alt="([^"]*)"', b, re.S)
    if not img: continue
    # 농할대전 표시 상품만
    bullets = [html.unescape(x) for x in re.findall(r"<img src='[^']*ico_pbullet[^']*' alt='([^']*)'", b)]
    if not any("농할" in x for x in bullets): continue
    seen.add(wid)
    title = html.unescape(img.group(2)).strip()
    tt = re.search(r'<p class="title">\s*(.*?)</p>', b, re.S)
    price = re.search(r'<strong class="price">\s*([\d,]+)', b)
    orig = re.search(r'<del>\s*([\d,]+)', b)
    pct = re.search(r'([\d.]+)\s*<[^>]*>\s*%|class="[^"]*(?:per|rate|sale)[^"]*"[^>]*>\s*([\d.]+)', b)
    rv = re.search(r'(?:review|리뷰)[^\d<]*\(?\s*([\d,]+)', b)
    um = re.search(r'(\d+(?:\.\d+)?\s?(?:kg|g|ml|mL|L|입|개|팩|봉|포|박스|세트))', title)
    img_url = img.group(1)
    sp, op = (num(price.group(1)) if price else None), (num(orig.group(1)) if orig else None)
    listed = sp
    nh = re.search(r"농할가\s*([\d,]+)\s*원", title)
    cond = "표기: " + ", ".join(bullets)
    if nh:
        sp = num(nh.group(1))
        cond += f"; 상품명 표기 농할가 {sp:,}원 (목록 표시가 {listed:,}원, 농할 쿠폰/할인 적용가 추정 아님-상품명 표기 그대로)" if listed else f"; 상품명 표기 농할가 {sp:,}원"
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
        "unit": um.group(1) if um else None, "vendor": "농협몰", "channel": "농협몰 메인(농할대전 표시)",
        "product": title, "model_code": wid,
        "buy_url": f"https://www.nonghyupmall.com/BC14010R/viewDetailPage.nh?wrsC={wid}&chanC=1101",
        "image_url": img_url if img_url.startswith("http") else None,
        "rating": None, "review_count": None, "event_url": URL,
        "claimed_original_price": op, "sale_price": sp,
        "claimed_discount_pct": round((1 - sp / op) * 100, 1) if sp and op and op > sp else None,
        "conditions": cond,
        "sources": [URL],
    })
out = {"category": "food", "source_id": SID, "collected_at": "2026-10-31", "items": items}
os.makedirs(f"{BASE}/data/raw/catalog/food", exist_ok=True)
json.dump(out, open(f"{BASE}/data/raw/catalog/food/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(blocks), len(items))
