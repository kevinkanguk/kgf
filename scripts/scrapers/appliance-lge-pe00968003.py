import re, json, html, os, sys, datetime, requests
SID = "appliance-lge-pe00968003"
EVENT = "https://www.lge.co.kr/benefits/exhibitions/detail-PE00968003"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "data", "cache", "html", SID)
OUT = os.path.join(ROOT, "data", "raw", "catalog", "appliance", SID + ".json")
UA = {"User-Agent": "Mozilla/5.0"}
os.makedirs(CACHE, exist_ok=True)

def get(url, name):
    p = os.path.join(CACHE, name)
    if os.path.exists(p) and os.path.getsize(p) > 10000:
        return open(p, encoding="utf-8").read()
    r = requests.get(url, headers=UA, timeout=30); r.encoding = "utf-8"
    open(p, "w", encoding="utf-8").write(r.text)
    return r.text

page = get(EVENT, "page.html").lstrip("\ufeff")
seen = {}
for m in re.finditer(r'data-prdvalue="(\w+)".*?href="([^"]+)".*?data-ec-product="([^"]+)"', page, re.S):
    mid, href, ec = m.group(1), m.group(2), html.unescape(m.group(3))
    if mid in seen: continue
    parts = [x.strip() for x in json.loads(ec)["model_name"].split(" / ")]
    parts = [re.sub(r"<br>", "", x).strip() for x in parts if x.strip()]
    seen[mid] = (href, parts)
cond = "LG전자 10월 기획전(10/1~10/31): 제휴카드 청구할인 등 카드혜택 별도(페이지 내 혜택 안내 참조)"
items = []
for n, (mid, (href, parts)) in enumerate(seen.items(), 1):
    pname = next((x for x in parts if x.startswith("LG ")), parts[0])
    code = parts[-1]
    pr = get("https://www.lge.co.kr/product" + href + "?modelId=" + mid + "&pdpType=PURCHASE", mid + ".html")
    orig = sale = None
    mo = re.search(r'obsOriginalPrice\*":(\d+),\*"obsSellingPrice\*":(\d+)', pr)
    if mo: orig, sale = int(mo.group(1)), int(mo.group(2))
    img = rating = rc = None
    for l in re.findall(r'application/ld\+json[^>]*>(.*?)</script>', pr, re.S):
        try: j = json.loads(l)
        except Exception: continue
        if j.get("@type") == "Product":
            img = j.get("image")
            if sale is None and j.get("offers", {}).get("price"): sale = int(j["offers"]["price"])
            ar = j.get("aggregateRating")
            if ar: rating = float(ar["ratingValue"]); rc = int(ar["reviewCount"])
    if orig is None: orig = sale
    pct = round((orig - sale) / orig * 100, 1) if orig and sale else None
    url = "https://www.lge.co.kr/product" + href + "?modelId=" + mid
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "appliance", "source_id": SID,
        "unit": "1개", "vendor": "LG전자", "channel": "LGE.COM",
        "product": pname, "model_code": code, "buy_url": url,
        "image_url": img, "rating": rating, "review_count": rc if rating is not None else None,
        "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": pct, "conditions": cond,
        "sources": [EVENT, url],
    })
out = {"category": "appliance", "source_id": SID,
       "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
