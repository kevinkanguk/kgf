# -*- coding: utf-8 -*-
"""남도장터 수산대전 추석 특별전 3주차 (promotionSeq=308) 전체 품목 수집. 실행: py -I scripts/scrapers/food-jnmall-soosan.py"""
import json, os, re, time, datetime, requests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SID, CAT, SEQ = 'food-jnmall-soosan', 'food', 308
EVENT = 'https://www.jnmall.kr/category/promotion/exhibition?&code=0d4tUTg4&name=%EC%88%98%EC%82%B0%EB%8C%80%EC%A0%84%20%EC%B6%94%EC%84%9D%20%ED%8A%B9%EB%B3%84%EC%A0%84-3%EC%A3%BC%EC%B0%A8&promotionSeq=308'
API = 'https://api.jnmall.kr/user/api/products/exhibition'
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.jnmall.kr/'}
CACHE = os.path.join(ROOT, 'data', 'cache', 'html', SID)
OUT = os.path.join(ROOT, 'data', 'raw', 'catalog', CAT, SID + '.json')
UNIT = re.compile(r'\d+(?:\.\d+)?\s*(?:kg|g|ml|L|㎏|미|마리|개입|개|팩|박스|봉|세트|속|포)', re.I)

def page(pn):
    f = os.path.join(CACHE, 'api_p%03d.json' % pn)
    if os.path.exists(f):
        return json.load(open(f, encoding='utf-8'))
    p = {'pageNumber': pn, 'pageSize': 30, 'minPrice': 1, 'maxPrice': 9999999999, 'promotionSeq': SEQ,
         'sort': 1, 'searchKeyword': '', 'productKeyword': ''}
    for _ in range(3):
        try:
            r = requests.get(API, params=p, headers=H, timeout=30); r.raise_for_status()
            d = r.json()['data']; break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError('fail page %d' % pn)
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
    return d

def main():
    os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
    d = page(1); total = d['pagination']['totalPages']
    rows = list(d['contents'])
    for pn in range(2, total + 1):
        rows += page(pn)['contents']
    items, seen = [], set()
    for x in rows:
        key = (x['productSeq'], x.get('subProductSeq'))
        if key in seen: continue
        seen.add(key)
        ipm = (x.get('infoPurchaseMethod') or [{}])[0]
        sale, cons = ipm.get('salesPrice'), ipm.get('consumerPrice')
        if not sale and x.get('infoProductOption'):
            sale = x['infoProductOption'][0].get('salesPrice')
        pct = round((cons - sale) / cons * 100, 1) if sale and cons and cons > sale else None
        files = (x.get('fileGroup') or {}).get('files') or []
        img = next((f['url'] for f in files if f.get('url')), None)
        name = x['productName']
        m = UNIT.search(name)
        rc = x.get('reviewCount')
        rating = x.get('starRatingAvg')
        url = 'https://www.jnmall.kr/product/%s-%s?promotionSeq=%d' % (x['productSeq'], x['subProductSeq'], SEQ) if x.get('subProductSeq') else 'https://www.jnmall.kr/product/%s?promotionSeq=%d' % (x['productSeq'], SEQ)
        items.append({
            'item_id': '%s-%04d' % (SID, len(items) + 1), 'category': CAT, 'source_id': SID,
            'unit': m.group(0) if m else None,
            'vendor': x.get('sellerBusinessName') or '', 'channel': '남도장터 수산대전',
            'product': name, 'model_code': x.get('productCode'), 'buy_url': url, 'image_url': img,
            'rating': rating if rc else None, 'review_count': rc if rc is not None else None,
            'event_url': EVENT, 'claimed_original_price': cons, 'sale_price': sale,
            'claimed_discount_pct': pct, 'conditions': None,
            'sources': [EVENT, API + '?promotionSeq=%d' % SEQ],
        })
    out = {'category': CAT, 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(len(rows), len(items))

if __name__ == '__main__':
    main()
