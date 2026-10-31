import re, json, os, time, html, datetime, requests
SID = "food-nurimarket-nonghal-all"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE = "https://nurimarket.co.kr/shop/list.php?ca_id=nh&sort=it_sum_qty&sortodr=desc&page="
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0"}
num = lambda s: int(s.replace(",", "")) if s else None

def get(p):
    f = f"{CACHE}/page{p}.html"
    if os.path.exists(f):
        return open(f, encoding="utf-8").read()
    r = requests.get(BASE + str(p), headers=H, timeout=30); r.encoding = "utf-8"
    open(f, "w", encoding="utf-8").write(r.text); time.sleep(0.5)
    return r.text

items, seen = [], set()
first = get(1)
last = max(int(x) for x in re.findall(r'page=(\d+)', first))
for p in range(1, last + 1):
    t = get(p)
    blocks = t.split('class="swiper-slide swiper-slide-list-nh"')[1:]
    for b in blocks:
        m = re.search(r'item\.php\?it_id=(\d+)', b)
        if not m or m.group(1) in seen: continue
        iid = m.group(1); seen.add(iid)
        title = re.search(r'main_list_tit"><a[^>]*>(.*?)</a>', b, re.S)
        title = html.unescape(re.sub(r'<[^>]+>', '', title.group(1))).strip() if title else None
        img = re.search(r'<img src="(https://nurimarket\.co\.kr/data/item/[^"]+)"', b)
        pct = re.search(r'main_list_price_li1[^>]*>([\d.]+)%', b)
        sale = re.search(r'main_list_price_li2[^>]*>([\d,]+)원', b)
        orig = re.search(r'<strike>([\d,]+)원', b)
        cpct = re.search(r'쿠폰</span>.*?>([\d.]+)%</span>.*?적용가</span>.*?>([\d,]+)</span>', b, re.S)
        star = re.search(r's_star(\d(?:_\d)?)\.png', b)
        rc = re.search(r'main_list_star_cnt[^>]*>\((\d[\d,]*)\)', b)
        rating = float(star.group(1).replace("_", ".")) if star else None
        cond = None
        if cpct: cond = f"쿠폰 {cpct.group(1)}% 적용가 {cpct.group(2)}원"
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
            "unit": None, "vendor": "비케이물산", "channel": "온누리마켓(비케이물산)",
            "product": title, "model_code": iid,
            "buy_url": f"https://nurimarket.co.kr/shop/item.php?it_id={iid}",
            "image_url": img.group(1) if img else None,
            "rating": rating, "review_count": num(rc.group(1)) if rc else None,
            "event_url": "https://nurimarket.co.kr/shop/list.php?ca_id=nh",
            "claimed_original_price": num(orig.group(1)) if orig else None,
            "sale_price": num(sale.group(1)) if sale else None,
            "claimed_discount_pct": float(pct.group(1)) if pct else None,
            "conditions": cond,
            "sources": [f"{BASE}{p}"],
        })
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat() if False else "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items), "pages", last)
