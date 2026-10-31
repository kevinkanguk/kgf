# food-kurly scraper: Kurly main page 특가/인기랭킹 컬렉션 전 페이지 수집 (사이트 JSON API)
import requests, json, re, os, datetime
ROOT = 'E:/090_ETC/kf'
SID = 'food-kurly'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/food/{SID}.json'
H = {'User-Agent': 'Mozilla/5.0'}
COLLECTIONS = [('sale231107', '지금 가장 많이 담는 특가'), ('ranking123', '실시간 인기랭킹')]
os.makedirs(CACHE, exist_ok=True)

def fetch(code):
    seen, allp = set(), []
    for page in range(1, 60):
        u = f'https://api.kurly.com/collection/v2/home/sites/market/product-collections/{code}/products'
        r = requests.get(u, params={'sort_type': 1, 'page': page}, headers=H, timeout=30)
        r.raise_for_status()
        data = r.json().get('data') or []
        json.dump(data, open(f'{CACHE}/{code}_p{page}.json', 'w', encoding='utf-8'), ensure_ascii=False)
        new = [p for p in data if p['no'] not in seen]
        if not new: break
        for p in new: seen.add(p['no'])
        allp += new
    return allp

items, nos = [], set()
for code, title in COLLECTIONS:
    for p in fetch(code):
        if p['no'] in nos: continue
        nos.add(p['no'])
        name = p['name']
        m = re.match(r'\[([^\]]+)\]\s*(.*)', name)
        vendor = m.group(1) if m else '컬리'
        sp, dp = p.get('sales_price'), p.get('discounted_price')
        sale = dp if dp else sp
        orig = sp if (dp and sp and dp < sp) else None
        items.append({
            'item_id': f'{SID}-{len(items)+1:04d}', 'category': 'food', 'source_id': SID,
            'unit': None, 'vendor': vendor, 'channel': '마켓컬리', 'product': name, 'model_code': None,
            'buy_url': f"https://www.kurly.com/goods/{p['no']}",
            'image_url': p.get('list_image_url'), 'rating': None, 'review_count': None if p.get('review_count') in (None, '') else int(re.sub(r'\D', '', str(p['review_count'])) or 0),
            'event_url': f'https://www.kurly.com/collections/{code}',
            'claimed_original_price': orig, 'sale_price': sale,
            'claimed_discount_pct': p.get('discount_rate') if orig else None,
            'conditions': None, 'sources': [f'https://api.kurly.com/collection/v2/home/sites/market/product-collections/{code}/products'],
        })
out = {'category': 'food', 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items))
