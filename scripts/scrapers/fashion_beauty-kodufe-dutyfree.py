# -*- coding: utf-8 -*-
"""kodufe.kr 한국면세점협회 코듀페: 상품 목록 없음. 면세점 12곳의 행사 혜택 안내를 항목화(가격 null)."""
import re, json, html, os, datetime, requests
SID = "fashion_beauty-kodufe-dutyfree"
URL = "http://kodufe.kr/index_ko.html"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
cache = os.path.join(ROOT, "data/cache/html", SID); os.makedirs(cache, exist_ok=True)
cf = os.path.join(cache, "index_ko.html")
if not os.path.exists(cf):
    r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"}); r.encoding = "utf-8"
    open(cf, "w", encoding="utf8").write(r.text)
t = open(cf, encoding="utf8").read()
m = re.search(r'내용 Start(.*?)내용 End', t, re.S)
body = m.group(1)
blocks = re.split(r'<!--\s*(?=[^<>]*면세점\s*-->)', body)
items = []
pct = {"롯데면세점": 15, "현대면세점": 15, "JDC면세점": 20, "그랜드면세점": 25}
sites = {"롯데면세점": "https://kor.lottedfs.com", "신라면세점": "http://www.shilladfs.com", "신세계면세점": "https://www.ssgdfs.com",
         "현대면세점": "https://www.hddfs.com", "신라아이파크면세점": "https://www.shillaipark.com", "JDC면세점": "https://www.jdcdutyfree.com",
         "JTO면세점": "https://www.jejudfs.com", "경복궁면세점": "https://www.kbkdfs.com/", "시티면세점": "http://www.citydfs.com",
         "그랜드면세점": URL, "부산면세점": "http://www.busandf.com/", "판판면세점": URL}
for b in blocks[1:]:
    name = re.match(r'([^\s-]+)', b.strip()).group(1)
    name = re.match(r'(.+?)\s*-->', b).group(1).strip()
    txt = re.sub(r'<!--.*?-->', ' ', b[b.index('-->')+3:], flags=re.S)
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt)); txt = re.sub(r'\s+', ' ', txt).strip()
    txt = txt[len(name):].strip() if txt.startswith(name) else txt
    n = len(items) + 1
    items.append({"item_id": f"{SID}-{n:04d}", "category": "fashion_beauty", "source_id": SID, "unit": None,
        "vendor": name, "channel": "코리아 듀티프리 페스타(한국면세점협회)", "product": f"{name} 행사 혜택(상품 목록 없음)",
        "model_code": None, "buy_url": sites.get(name, URL), "image_url": None, "rating": None, "review_count": None,
        "event_url": URL, "claimed_original_price": None, "sale_price": None,
        "claimed_discount_pct": pct.get(name), "conditions": txt, "sources": [URL]})
out = os.path.join(ROOT, "data/raw/catalog/fashion_beauty", SID + ".json")
json.dump({"category": "fashion_beauty", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(out, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
