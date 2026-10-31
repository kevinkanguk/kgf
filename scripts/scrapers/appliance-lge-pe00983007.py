import re, json, os, datetime, requests
SID = "appliance-lge-pe00983007"
EV = "https://www.lge.co.kr/benefits/exhibitions/detail-PE00983007"
CACHE = f"E:/090_ETC/kf/data/cache/html/{SID}/"
OUT = f"E:/090_ETC/kf/data/raw/catalog/appliance/{SID}.json"
H = {"User-Agent": "Mozilla/5.0"}
def get(url, name):
    p = CACHE + name
    if os.path.exists(p):
        return open(p, encoding="utf8").read()
    r = requests.get(url, headers=H, timeout=30)
    os.makedirs(CACHE, exist_ok=True)
    open(p, "w", encoding="utf8").write(r.text)
    return r.text if r.status_code == 200 else ""
page = get(EV, "page.html")
models = re.search(r"대상 제품:</strong>\s*([^<]+)", page).group(1).split(",")
models = [m.strip() for m in models]
items = []
blocks = re.findall(r'<a class="product-list" href="([^"]+)">(.*?)</a>', page, re.S)
for i, (href, body) in enumerate(blocks, 1):
    name = re.search(r"<div>([^<]+)</div>", body).group(1)
    nums = re.search(r"정상 구독가 ([\d,]+)원 \(TV 단독 구독 ([\d,]+)원 \+ 넷플[^\d]*([\d,]+)원", body)
    orig = int(nums.group(1).replace(",", ""))
    sale = int(re.search(r"구독 혜택가: ([\d,]+)원", body).group(1).replace(",", ""))
    slug = href.split("?")[0].rsplit("/", 1)[1]
    code = next((m for m in models if m.split(".")[0].lower() + "-wall" == slug), None)
    url = "https://www.lge.co.kr" + href
    img = rating = rc = None
    h = get(url.split("?")[0], slug + ".html")
    if h:
        m = re.search(r'og:image" content="([^"]+)', h)
        img = m.group(1) if m else None
        m = re.search(r'ratingValue\\":\\"([\d.]+)\\",\\"reviewCount\\":\\"(\d+)', h)
        if m: rating, rc = float(m.group(1)), int(m.group(2))
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "appliance", "source_id": SID,
        "unit": "72개월 구독(월)", "vendor": "LG전자", "channel": "LGE.COM",
        "product": f"LG TV {name} 엘지넷플팩 (TV 구독+넷플릭스 프리미엄)",
        "model_code": code, "buy_url": url, "image_url": img, "rating": rating,
        "review_count": rc, "event_url": EV,
        "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": round((orig - sale) / orig * 100, 1),
        "conditions": f"월 구독료. 정상가=TV 단독 {nums.group(2)}원+넷플 {nums.group(3)}원. 72개월 구독+넷플릭스 결합, 가입 2~7개월차 6개월간 할인, 약정 중 넷플 해지 불가",
        "sources": [EV, url],
    })
json.dump({"category": "appliance", "source_id": SID,
           "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
