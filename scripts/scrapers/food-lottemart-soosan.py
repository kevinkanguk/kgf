# food-lottemart-soosan: Lotte Mart Zetta (lottemartzetta.com) Suosan-daejeon 20% offers page.
# The page is a React SPA with virtual scrolling, so the rendered cards (73) were collected in a
# browser by scrolling to the end and saved to data/cache/html/food-lottemart-soosan/snapshot_*.txt.
# This script converts the snapshots into the output JSON. Re-runnable.
import json, re, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
C = os.path.join(ROOT, 'data', 'cache', 'html', 'food-lottemart-soosan')
OUT = os.path.join(ROOT, 'data', 'raw', 'catalog', 'food', 'food-lottemart-soosan.json')
SID = 'food-lottemart-soosan'
EVENT = 'https://lottemartzetta.com/offers/23c3f58f-4e7a-43be-b937-3abfa5b47d0e'
IMG = 'https://lottemartzetta.com/images-v3/932dcbc7-fca8-4d43-bcde-f73d1ce3cc7d/%s/300x300.jpg'
num = lambda s: int(s.replace(',', ''))
media = {}
for l in open(os.path.join(C, 'snapshot_media.txt'), encoding='utf-8'):
    p = l.strip().split('|')
    if len(p) == 4:
        media[p[0]] = p
items = []
for l in open(os.path.join(C, 'snapshot_text.txt'), encoding='utf-8'):
    p = l.strip().split('|')
    if len(p) < 3:
        continue
    pid, title, rest = p[0], p[1], p[2:]
    txt = '|'.join(rest)
    price = num(re.search(r'가격\|([\d,]+)원', txt).group(1))
    prev = re.search(r'이전 가격\|([\d,]+)원', txt)
    m = re.match(r'\[수산대전 적용가 ([\d,]+)원\]\s*', title)
    sale = num(m.group(1)) if m else None
    name = title[m.end():] if m else title
    orig = num(prev.group(1)) if prev else price
    unit = None
    mu = re.search(r'\|(\d+(?:\.\d+)?(?:g|kg|ml|l))\|', '|' + txt + '|')
    if mu:
        unit = mu.group(1)
    else:
        pm = re.findall(r'\(([^()]*)\)', name)
        if pm:
            unit = pm[-1]
    extra = [x for x in rest if '할인' in x and x != '수산대전 20% 할인']
    cond = '수산대전 20% 할인(기간 중 ID당 1회, 최대 1만원 할인, 2026.10.29-11.04)'
    if extra:
        cond += '; ' + '; '.join(extra)
    if sale is None:
        cond += '; 목록에 적용가 미표기(20% 할인 대상 표시만 있음)'
    pct = round((orig - sale) / orig * 100, 1) if sale else 20.0
    md = media[pid]
    rating = float(md[2]) if float(md[2]) > 0 else None
    rc = int(md[3]) if rating else None
    items.append({
        'item_id': '%s-%04d' % (SID, len(items) + 1), 'category': 'food', 'source_id': SID,
        'unit': unit, 'vendor': '롯데마트', 'channel': '롯데마트 제타 수산대전',
        'product': name.strip(), 'model_code': pid,
        'buy_url': 'https://lottemartzetta.com/products/%s/details' % pid,
        'image_url': IMG % md[1], 'rating': rating, 'review_count': rc,
        'event_url': EVENT, 'claimed_original_price': orig, 'sale_price': sale,
        'claimed_discount_pct': pct, 'conditions': cond,
        'sources': [EVENT]})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'category': 'food', 'source_id': SID, 'collected_at': '2026-10-31', 'items': items},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
