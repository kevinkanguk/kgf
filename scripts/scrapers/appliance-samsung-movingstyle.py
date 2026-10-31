# samsung.com blocks plain HTTP clients (Akamai 403); the event page was rendered in a browser pane and
# product cards (li#prdCtgCompGoods_*) were extracted to the cache JSON. This script builds the catalog from it.
import json, os
R = 'E:/090_ETC/kf/'
SID = 'appliance-samsung-movingstyle'
EV = 'https://www.samsung.com/sec/event/samsung-movingstyle/'
rows = json.load(open(R + f'data/cache/html/{SID}/browser_extract.json', encoding='utf-8'))
items = []
for i, r in enumerate(rows, 1):
    cond = '쿠폰 적용 예상가(일시불)' if r.get('benefit') and r['benefit'] != r['sale'] else '일시불 기준'
    if r['model'] == 'LS32DM503E-1WE':
        cond = '혜택가 519,000원에서 쿠폰 -20,000원 적용 시 최종 체감가 499,000원'
    elif r.get('tving'):
        cond += '; 구독 시 TVING 프리미엄 3개월(M7/Edge); 혜택가 %s원' % format(r['benefit'], ',')
    items.append({
        'item_id': f'{SID}-{i:04d}', 'category': 'appliance', 'source_id': SID,
        'unit': r['name'].split('(')[1].split(')')[0] if '(' in r['name'] else None,
        'vendor': '삼성전자', 'channel': '삼성닷컴 무빙스타일 10월 쇼핑 대전',
        'product': r['name'], 'model_code': r['model'],
        'buy_url': 'https://www.samsung.com' + r['url'],
        'image_url': ('https:' + r['img']) if r['img'] else None,
        'rating': None, 'review_count': None, 'event_url': EV,
        'claimed_original_price': r['base'], 'sale_price': r['sale'],
        'claimed_discount_pct': r['per'], 'conditions': cond,
        'sources': [EV, 'https://www.samsung.com' + r['url']],
    })
out = {'category': 'appliance', 'source_id': SID, 'collected_at': '2026-10-31', 'items': items}
p = R + f'data/raw/catalog/appliance/{SID}.json'
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
