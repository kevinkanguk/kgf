# Zigzag KGF denim section. The page is JS-rendered (virtuoso grid) and a plain HTTP fetch returns an empty body,
# so rows.tsv was harvested from the rendered page in the browser pane (click "more", scroll the grid).
# This script converts the cached rows.tsv into the catalog JSON. Run with: py -I <this file>
import json, datetime, os

R = 'E:/090_ETC/kf'
SID = 'mall-zigzag-kgf-denim'
EV = 'https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat=denim'
items = []
for ln in open(f'{R}/data/cache/html/{SID}/rows.tsv', encoding='utf-8'):
    ln = ln.rstrip('\n')
    if not ln:
        continue
    pid, img, vendor, prod, rest = ln.split('\t')
    parts = rest.split('|')
    pct = None
    if parts[0].endswith('%'):
        pct = float(parts.pop(0)[:-1])
    pr = parts.pop(0)
    frm = pr.endswith('~')
    price = int(pr.rstrip('~').replace(',', ''))
    rating = float(parts[0]) if parts else None
    rc = int(parts[1].strip('()').replace(',', '')) if len(parts) > 1 else None
    url = f'https://zigzag.kr/catalog/products/{pid}'
    items.append({
        'item_id': f'{SID}-{len(items)+1:04d}', 'category': 'mall', 'source_id': SID,
        'unit': None, 'vendor': vendor, 'channel': '지그재그', 'product': prod, 'model_code': pid,
        'buy_url': url, 'image_url': img, 'rating': rating, 'review_count': rc, 'event_url': EV,
        'claimed_original_price': None, 'sale_price': price, 'claimed_discount_pct': pct,
        'conditions': '표시가는 최저 옵션가(~)' if frm else None, 'sources': [EV, url]})
out = {'category': 'mall', 'source_id': SID,
       'collected_at': datetime.datetime(2026, 10, 31).isoformat(), 'items': items}
p = f'{R}/data/raw/catalog/mall/{SID}.json'
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
