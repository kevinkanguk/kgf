import re, json, os, datetime, requests
SID = "appliance-lge-pe01003006"
EVENT = "https://www.lge.co.kr/benefits/exhibitions/detail-PE01003006"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "data", "cache", "html", SID)
OUT = os.path.join(ROOT, "data", "raw", "catalog", "appliance", SID + ".json")
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0"}

def get(url, name):
    p = os.path.join(CACHE, name)
    if os.path.exists(p):
        return open(p, encoding="utf8").read()
    t = requests.get(url, headers=H, timeout=30).text
    open(p, "w", encoding="utf8").write(t)
    return t

def num(rx, h):
    m = re.search(rx, h)
    return int(float(m.group(1))) if m else None

page = get(EVENT, "page.html")
slugs = []
for s in re.findall(r'href="/notebook/([a-z0-9.-]+)"', page):
    if s not in slugs:
        slugs.append(s)
items = []
for i, s in enumerate(slugs, 1):
    url = "https://www.lge.co.kr/notebook/" + s
    h = get(url, s + ".html").replace('\\"', '"')
    model = re.search(r'"model":"([^"]+)"', h).group(1)
    name = re.search(r'"@type":"Product".*?"name":"([^"]+)"', h).group(1)
    img = re.search(r'"@type":"Product".*?"image":"([^"]+)"', h).group(1)
    orig = num(r'"obsOriginalPrice":(\d+)', h) or num(r'"grandPrice":"(\d+)"', h)
    sale = num(r'"obsSellingPrice":(\d+)', h) or num(r'"discountedPrice":"(\d+)"', h) or num(r'"@type":"Offer".*?"price":"(\d+)"', h)
    rating = re.search(r'"ratingValue":"([\d.]+)"', h)
    rc = num(r'"reviewCount":"(\d+)"', h)
    scr = re.search(r'"keywords":\["(\d+(?:\.\d+)?cm)"', h)
    pct = round((orig - sale) / orig * 100, 1) if orig and sale and orig > sale else None
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "appliance", "source_id": SID,
        "unit": scr.group(1) if scr else None, "vendor": "LG전자", "channel": "LGE.COM",
        "product": f"{name} {model}", "model_code": model, "buy_url": "https://www.lge.co.kr/product/notebook/" + s,
        "image_url": img, "rating": float(rating.group(1)) if rating else None, "review_count": rc,
        "event_url": EVENT, "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
        "conditions": "LGE.COM 판매가 기준(카드/쿠폰 추가혜택 별도)", "price_60d_low": None, "price_60d_typical": None,
        "price_history_note": None, "sources": [url], "verify_status": None, "verify_note": None, "confidence": None})
json.dump({"category": "appliance", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
