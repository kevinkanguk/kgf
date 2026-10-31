import re, json, os, datetime, requests
SID = "food-foodnuri-nonghal-weekly"
URL = "https://sale.foodnuri.go.kr/ft/ftSale/list.do"
ROOT = "E:/090_ETC/kf"
cache = f"{ROOT}/data/cache/html/{SID}/list.html"
os.makedirs(os.path.dirname(cache), exist_ok=True)
if os.path.exists(cache):
    t = open(cache, encoding="utf8").read()
else:
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30); r.encoding = "utf-8"
    t = r.text; open(cache, "w", encoding="utf8").write(t)
weeks = {}
for cls in ("thisweek", "nextweek"):
    m = re.search(r'salebox %s.*?class="date">([^<]+)</p>.*?<ul>(.*?)</ul>' % cls, t, re.S)
    date = m.group(1).strip()
    weeks[cls] = (date, [x.strip() for x in re.findall(r"<li>(.*?)</li>", m.group(2))])
order, wk = [], {}
for cls, (date, names) in weeks.items():
    for n in names:
        if n not in wk: order.append(n); wk[n] = []
        wk[n].append(date)
items = []
for i, n in enumerate(order, 1):
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "food", "source_id": SID, "unit": None,
        "vendor": "한국농수산식품유통공사(aT) 농축산물 할인지원", "channel": "농할 주간 할인품목(참여 유통사별 상이)",
        "product": n, "model_code": None, "buy_url": URL, "image_url": None, "rating": None, "review_count": None,
        "event_url": URL, "claimed_original_price": None, "sale_price": None, "claimed_discount_pct": None,
        "conditions": "할인기간: " + " / ".join(wk[n]) + ". 유통사·지점별 할인율/품목 상이, 정부 할인지원(공지에 가격 없음)",
        "sources": [URL]})
out = {"category": "food", "source_id": SID, "collected_at": "2026-10-31", "items": items}
p = f"{ROOT}/data/raw/catalog/food/{SID}.json"
json.dump(out, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
