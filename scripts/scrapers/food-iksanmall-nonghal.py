import re, json, os, time, html, datetime, urllib.request
SID = "food-iksanmall-nonghal"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE = "https://www.iksanmall.com"
EVENT_CATES = {"006002": "농식품부할인지원사업", "006008": "농식품부할인지원사업(쌀)"}
os.makedirs(CACHE, exist_ok=True)

def get(url, name):
    p = f"{CACHE}/{name}"
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    s = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    open(p, "w", encoding="utf-8").write(s); time.sleep(0.5)
    return s

def list_items(html_s):
    r = []
    for li in re.split(r'<li\s+>\s*<div class="item_cont">', html_s)[1:]:
        g = re.search(r'goodsNo=(\d+)', li).group(1)
        n = html.unescape(re.search(r'item_name">(.*?)</strong>', li, re.S).group(1).strip())
        r.append((g, n))
    return r

def num(s):
    s = re.sub(r'[^\d]', '', s or '')
    return int(s) if s else None

found = {}  # goodsNo -> (name, set(reasons))
for c, label in EVENT_CATES.items():
    for g, n in list_items(get(f"{BASE}/goods/goods_list.php?cateCd={c}&pageNum=200", f"cat{c}.html")):
        found.setdefault(g, (n, []))[1].append(label)
# [농할] tagged items anywhere in the mall
for c in "001 002 003 004 005 006".split():
    for g, n in list_items(get(f"{BASE}/goods/goods_list.php?cateCd={c}&pageNum=200&page=1", f"cat{c}.html")):
        if "농할" in n:
            found.setdefault(g, (n, []))[1].append("상품명 [농할] 표기")

items = []
for i, g in enumerate(sorted(found, key=lambda x: int(x)), 1):
    name, reasons = found[g]
    url = f"{BASE}/goods/goods_view.php?goodsNo={g}"
    v = get(url, f"view_{g}.html")
    orig = re.search(r'<dt>정가</dt>\s*<dd>\s*<del><span>([\d,]+)</span>', v)
    sale = re.search(r'<dl class="item_price">.*?<strong><strong>([\d,]+)</strong>', v, re.S)
    maker = re.search(r'<dt>제조사</dt>\s*<dd>(.*?)</dd>', v, re.S)
    rv = re.search(r'상품후기 <strong>\((\d+)\)', v)
    img = re.search(r'property="og:image" content="([^"]+)"', v) or re.search(r'data-image-main\s*=\s*"([^"]+)"', v)
    coup = re.search(r'<dt>\s*(농식품할인쿠폰[^<]*)</dt>.*?<span class="c_red">([^<]+)</span>', v, re.S)
    o, s = num(orig.group(1)) if orig else None, num(sale.group(1)) if sale else None
    pct = round((o - s) / o * 100, 1) if o and s and o > s else None
    m = re.search(r'\[농할가\s*([\d,]+)원\]', name)
    cond = []
    if coup: cond.append(f"{coup.group(1).strip()} 발급 시 추가 할인 가능({coup.group(2).strip()})")
    if m: cond.append(f"상품명 표기 농할가 {m.group(1)}원")
    vendor = html.unescape(re.sub(r'<[^>]+>', '', maker.group(1))).strip() if maker else None
    um = re.search(r'(\d+(?:\.\d+)?\s*(?:kg|g|ml)(?:[/~\-]\d+(?:\.\d+)?\s*(?:kg|g))*)', name)
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "food", "source_id": SID,
        "unit": um.group(1) if um else None,
        "vendor": vendor or "익산몰 입점업체", "channel": "익산몰 농할(농식품부 할인지원)",
        "product": name, "model_code": g, "buy_url": url,
        "image_url": html.unescape(img.group(1)) if img else None,
        "rating": None, "review_count": int(rv.group(1)) if rv else None,
        "event_url": f"{BASE}/goods/goods_list.php?cateCd=" + ("006008" if "농식품부할인지원사업(쌀)" in reasons else "006002"),
        "claimed_original_price": o, "sale_price": s, "claimed_discount_pct": pct,
        "conditions": "; ".join(cond) or None,
        "sources": [url] + ([f"{BASE}/goods/goods_list.php?cateCd=006002"] if reasons else []),
    })
json.dump({"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat() if False else "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
