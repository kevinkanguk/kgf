import requests, re, json, html, os, datetime
SID = "food-foodnuri-nonghal-participants"
URL = "https://sale.foodnuri.go.kr/ft/ftCmpn/list.do"
ROOT = "E:/090_ETC/kf"
cache = f"{ROOT}/data/cache/html/{SID}"
os.makedirs(cache, exist_ok=True)
r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
t = r.content.decode("utf-8")
open(f"{cache}/p1.html", "w", encoding="utf8").write(t)
sec = t[t.find('class="company_list_sub"'):]
items = []
for dl in re.findall(r"<dl>(.*?)</dl>", sec, re.S):
    grp = html.unescape(re.search(r"<dt>(.*?)</dt>", dl, re.S).group(1)).strip()
    for href, src, alt in re.findall(r'<li><a href="([^"]*)"[^>]*><img src="([^"]*)" alt="([^"]*)"', dl):
        href = html.unescape(href).strip(); alt = html.unescape(alt).strip()
        n = len(items) + 1
        items.append({
            "item_id": f"{SID}-{n:04d}", "category": "food", "source_id": SID,
            "unit": None, "vendor": alt, "channel": f"농산물 나눔축제 참여업체({grp})",
            "product": alt, "model_code": None,
            "buy_url": href or URL,
            "image_url": "https://sale.foodnuri.go.kr" + html.unescape(src),
            "rating": None, "review_count": None, "event_url": URL,
            "claimed_original_price": None, "sale_price": None, "claimed_discount_pct": None,
            "conditions": "참여업체 목록(가격 없음)" + ("" if href else "; 업체 링크 없음, buy_url=목록 페이지"),
            "sources": [URL],
        })
out = {"category": "food", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
p = f"{ROOT}/data/raw/catalog/food/{SID}.json"
json.dump(out, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
