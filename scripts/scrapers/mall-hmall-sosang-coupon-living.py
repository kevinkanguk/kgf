import requests, json, os, time, datetime, collections
SID = 'mall-hmall-sosang-coupon-living'
ROOT = 'E:/090_ETC/kf'
API = 'https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page=%d'
EVENT = 'https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083'
H = {'Referer': 'https://www.hmall.com/', 'User-Agent': 'Mozilla/5.0'}
cache = f'{ROOT}/data/cache/html/{SID}'
os.makedirs(cache, exist_ok=True)
# 이 소스 담당 섹션 (뷰티, 패션/패션잡화는 beauty-fashion 소스 담당)
MINE = {'생활용품', '반려동물용품/취미', '반려동물 용품/취미', '가전/가구/침구', '스포츠/레저', '선착순 할인 쿠폰'}

def img(c, name):
    return f'https://image.hmall.com/static/{c[7]}/{c[6]}/{c[4:6]}/{c[2:4]}/{name}?RS=300x300'

raw = []
p = 1
while p <= 200:
    fn = f'{cache}/p{p}.json'
    if os.path.exists(fn):
        d = json.load(open(fn, encoding='utf-8'))
    else:
        r = requests.get(API % p, headers=H, timeout=30)
        r.raise_for_status()
        open(fn, 'wb').write(r.content)
        d = r.json()
        time.sleep(0.3)
    lst = d['respData']['itemList']
    if not lst:
        break
    raw += lst
    p += 1

print('sections', collections.Counter(i.get('sectNm') for i in raw))
seen = set(); items = []
for it in raw:
    if it.get('sectNm') not in MINE:
        continue
    c = it['slitmCd']
    if c in seen:
        continue
    seen.add(c)
    n = len(items) + 1
    sell = it.get('sellPrc') or None
    bb = it.get('bbprc') or None
    copn = it.get('copnDcAmt') or 0
    conds = []
    if copn: conds.append(f"쿠폰 {copn}원 할인 포함(copnDcAmt, 최적가 기준)")
    if it.get('soldout'): conds.append('품절')
    sect = it.get('sectNm')
    rating = it.get('itemEvalEvgScrg')
    rc = it.get('reviewCnt')
    pct = round((sell - bb) / sell * 100, 1) if sell and bb and sell > bb else None
    items.append({
        'item_id': f'{SID}-{n:04d}',
        'category': 'mall',
        'source_id': SID,
        'unit': None,
        'vendor': it.get('mstBrndNm') or it.get('brndNm') or it.get('venNm') or '',
        'channel': '현대Hmall 소상공인 쿠폰 기획전' + (f' - {sect}' if sect else ''),
        'product': it['slitmNm'],
        'model_code': c,
        'buy_url': f'https://www.hmall.com/md/pda/itemPtc?slitmCd={c}',
        'image_url': img(c, it.get('itemBaseImgNm') or f'{c}_0.jpg'),
        'rating': float(rating) if rating else None,
        'review_count': int(rc) if rc else None,
        'event_url': 'https://www.hmall.com/md/dpc/index?sectId=2811083',
        'claimed_original_price': sell if bb and sell and sell > bb else None,
        'sale_price': bb or sell,
        'claimed_discount_pct': pct,
        'conditions': '; '.join(conds) or None,
        'sources': [EVENT],
    })
out = {'category': 'mall', 'source_id': SID,
       'collected_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00'), 'items': items}
os.makedirs(f'{ROOT}/data/raw/catalog/mall', exist_ok=True)
json.dump(out, open(f'{ROOT}/data/raw/catalog/mall/{SID}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(raw), len(items), p)
