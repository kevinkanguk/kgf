"""auto-kgf-sme: koreagrandfestival.kr/sme 는 지역별 중소·소상공인 입점업체 디렉터리(가격/할인/자동차 품목 없음).
자동차 키워드 업체만 추출해 items 로 만든다. 현재 0건."""
import re, html, json, os, requests, datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CACHE = os.path.join(ROOT, 'data/cache/html/auto-kgf-sme/sme.html')
OUT = os.path.join(ROOT, 'data/raw/catalog/auto/auto-kgf-sme.json')
URL = 'https://koreagrandfestival.kr/sme'
os.makedirs(os.path.dirname(CACHE), exist_ok=True)
if not os.path.exists(CACHE):
    r = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30); r.encoding = 'utf-8'
    open(CACHE, 'w', encoding='utf-8').write(r.text)
t = open(CACHE, encoding='utf-8').read()
cards = re.findall(r'<li class="compy-card-item" data-name="([^"]*)" data-memo="([^"]*)"', t)
kw = re.compile('자동차|모터|오토|타이어|차량|카센터|정비|모빌리티|전기차')
items = []
for n, m in dict.fromkeys(cards):
    if kw.search(n + m):
        items.append({"item_id": f"auto-kgf-sme-{len(items)+1:04d}", "category": "auto", "source_id": "auto-kgf-sme",
                      "unit": None, "vendor": html.unescape(n), "channel": "코리아그랜드페스티벌 코그페 스토어",
                      "product": html.unescape(n), "buy_url": URL, "event_url": URL, "sources": [URL]})
out = {"category": "auto", "source_id": "auto-kgf-sme",
       "collected_at": datetime.date.today().isoformat() if False else "2026-10-31",
       "note": f"/sme 는 중소·소상공인 입점업체 디렉터리({len(set(cards))}곳, 가격·할인·자동차 없음). 자동차 품목 0건.",
       "items": items}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
