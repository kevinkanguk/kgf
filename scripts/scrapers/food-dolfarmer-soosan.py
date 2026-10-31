# -*- coding: utf-8 -*-
"""food-dolfarmer-soosan: 돌쇠네농산물 대한민국 수산대전 쿠폰 대상 상품 전수 수집.
POST /Goods/GetCouponPageGoodsList (JSON) + vreview public review_summary API. 실행: py -I scripts/scrapers/<this>.py"""
import re, json, html, os, datetime, requests

ROOT = 'E:/090_ETC/kf'
SID = 'food-dolfarmer-soosan'
BASE = 'https://www.dolfarmer.com'
EVENT = BASE + '/Goods/Coupon_New?cp_idx=22'
VRID = '64577d14-1e81-4544-b44c-85ad40611814'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
s.get(EVENT, timeout=30)
items_html = []
page, rows = 1, 80
while True:
    r = s.post(BASE + '/Goods/GetCouponPageGoodsList',
               json={'param': {'page': page, 'rows': rows, 'cp_idx': 22, 'listType': 'DIV2'}},
               headers={'Referer': EVENT, 'X-Requested-With': 'XMLHttpRequest'}, timeout=60)
    d = r.json()
    open(f'{CACHE}/api_page{page}.json', 'wb').write(r.content)
    data = d['data']
    if not data['cnt']:
        break
    items_html.append(data['data'])
    total = int(d.get('dataTotalCount') or 0)
    if page * rows >= total:
        break
    page += 1

blocks = []
for h in items_html:
    blocks += re.findall(r'<div class="itemrows" data-mgcode="(\w+)">(.*?)(?=<div class="itemrows"|\Z)', h, re.S)

def num(x):
    m = re.search(r'[\d,]+', x or '')
    return int(m.group().replace(',', '')) if m else None

seen, parsed = set(), []
for code, b in blocks:
    if code in seen:
        continue
    seen.add(code)
    title = re.search(r'class="prod-title">(.*?)</', b, re.S)
    title = html.unescape(re.sub(r'\s+', ' ', title.group(1))).strip() if title else None
    img = re.search(r'<img[^>]+src="(https?://[^"]+)"', b)
    org = re.search(r'class="org-price">(.*?)<', b, re.S)
    sale = re.search(r'class="price text-danger">(.*?)<', b, re.S)
    rate = re.search(r'class="dc-rate[^"]*">([\d.]+)%', b)
    labels = [html.unescape(x).strip() for x in re.findall(r'class="\w+_lab[^"]*">(.*?)<', b, re.S)]
    parsed.append(dict(code=code, title=title, img=img.group(1) if img else None,
                       org=num(org.group(1)) if org else None, sale=num(sale.group(1)) if sale else None,
                       rate=float(rate.group(1)) if rate else None, labels=labels))

rev = {}
codes = [p['code'] for p in parsed]
for i in range(0, len(codes), 50):
    r = requests.get(f'https://one.vreview.tv/api/embed/v2/{VRID}/products/review_summary',
                     params={'product_remote_ids': ','.join(codes[i:i+50])},
                     headers={'Origin': BASE, 'Referer': BASE + '/', 'User-Agent': 'Mozilla/5.0'}, timeout=30)
    for e in r.json():
        rev[e['remote_id']] = e
    open(f'{CACHE}/vreview_{i}.json', 'wb').write(r.content)

COND = ('[수산대전] 11월 특별전 1회차 20% 할인쿠폰(해당 상품 전용, 2026-10-27~11-03, 주문금액 제한없음) 다운로드 시 적용. '
        '표시 sale_price 는 목록 노출가이며 쿠폰 적용 전/후 여부는 상품 페이지에서 확인 필요')
items = []
for n, p in enumerate(parsed, 1):
    rv = rev.get(p['code'])
    pct = p['rate']
    if pct is None and p['org'] and p['sale'] and p['org'] > p['sale']:
        pct = round((1 - p['sale'] / p['org']) * 100, 1)
    um = re.search(r'(\d+(?:\.\d+)?\s?(?:kg|g|ml|L|l|개입|팩|마리|미|봉|박스|포|족|장|입))\b', p['title'] or '')
    items.append({
        'item_id': f'{SID}-{n:04d}',
        'category': 'food',
        'source_id': SID,
        'unit': um.group(1) if um else None,
        'vendor': '돌쇠네농산물',
        'channel': '돌쇠네농산물 대한민국 수산대전',
        'product': p['title'],
        'model_code': p['code'],
        'buy_url': f"{BASE}/Goods/Detail/{p['code']}",
        'image_url': p['img'],
        'rating': rv['total_rating_average'] if rv and rv['review_total_count'] else None,
        'review_count': rv['review_total_count'] if rv else None,
        'event_url': EVENT,
        'claimed_original_price': p['org'],
        'sale_price': p['sale'],
        'claimed_discount_pct': pct,
        'conditions': COND + (' / 라벨: ' + ','.join(p['labels']) if p['labels'] else ''),
        'sources': [EVENT, f"{BASE}/Goods/Detail/{p['code']}"],
    })

out = {'category': 'food', 'source_id': SID,
       'collected_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'items': items}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
