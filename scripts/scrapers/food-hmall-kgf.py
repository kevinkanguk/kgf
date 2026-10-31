"""food-hmall-kgf: H몰 코그페(정부지원사업 통합관, sectId=3107994) 전수 수집. 실행: py -I scripts/scrapers/food-hmall-kgf.py"""
import json, os, time, datetime, requests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SID = 'food-hmall-kgf'; SECT = 3107994
CACHE = os.path.join(ROOT, 'data', 'cache', 'html', SID)
OUT = os.path.join(ROOT, 'data', 'raw', 'catalog', 'food', SID + '.json')
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.hmall.com/'}
EVENT = f'https://www.hmall.com/md/dpa/searchSpexSectItem?sectId={SECT}'
API = 'https://www.hmall.com/api/hf/dp/v1/sect-mng/'
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def get(ep, **p):
    r = requests.get(API + ep, params=p, headers=H, timeout=30); r.raise_for_status()
    return r.json()['respData']

raw = []
# 1) 앵커(하위 기획전 묶음) 전체 페이징
page = 1
while True:
    d = get('plansale-ancr-paging', sectId=SECT, sortType='sect_disp', listSize=20, deviceInfo='mobile', page=page)
    json.dump(d, open(os.path.join(CACHE, f'ancr_p{page}.json'), 'w', encoding='utf8'), ensure_ascii=False)
    its = d.get('itemList') or []
    if not its: break
    raw += [(i, 'ancr') for i in its]
    page += 1; time.sleep(0.3)
    if page > 200: break
# 2) 메인 MD 추천(dealprod01) 상품
d = get('spex-sect-item-search', sectId=SECT, page=1, listSize=100)
for blk in d['holiInfo'].get('dealprod01List') or []:
    for i in blk.get('itemList') or []:
        raw.append((i, 'dealprod01'))

import re as _re
def _owned():
    p = os.path.join(ROOT, 'data', 'raw', 'catalog', 'food', 'food-hmall-soosan.json')
    try:
        d = json.load(open(p, encoding='utf8'))['items']
    except Exception:
        return set()
    return {m.group(1) for i in d for m in [_re.search(r'slitmCd=(\d+)', i.get('buy_url') or '')] if m}
OWNED = _owned()  # 수산대전 소스와 중복되는 상품은 그쪽에서 담당
raw = [(i, s) for i, s in raw if i['slitmCd'] not in OWNED]
seen = {}; order = []
for i, src in raw:
    c = i['slitmCd']
    if c not in seen: seen[c] = (i, src); order.append(c)

def num(v):
    try: return int(v)
    except Exception: return None
items = []
for n, c in enumerate(order, 1):
    i, src = seen[c]
    sell = num(i.get('sellPrc')); orig = num(i.get('bbprc'))
    if not orig: orig = None
    if not sell: sell = None
    pct = round((orig - sell) / orig * 100, 1) if orig and sell and orig > sell else None
    img = i.get('itemBaseImgNm') or i.get('orglImgNm')
    img_url = f'https://image.hmall.com/static/{c[7]}/{c[6]}/{c[4:6]}/{c[2:4]}/{img}?RS=300x300' if img and len(c) == 10 else None
    sc = i.get('itemEvalEvgScrg'); rc = num(i.get('reviewCnt') or i.get('itemEvalCnt'))
    items.append({
        'item_id': f'{SID}-{n:04d}', 'category': 'food', 'source_id': SID,
        'unit': None, 'vendor': i.get('brndNm') or i.get('venNm') or '',
        'channel': '현대Hmall 코그페' + (f" - {i['sectNm']}" if i.get('sectNm') else ''),
        'product': i.get('slitmNm'), 'model_code': c,
        'buy_url': f'https://www.hmall.com/pd/pda/itemPtc?slitmCd={c}',
        'image_url': img_url, '_img': img,
        'rating': round(float(sc), 2) if sc not in (None, '') and rc else None,
        'review_count': rc,
        'event_url': EVENT, 'claimed_original_price': orig, 'sale_price': sell,
        'claimed_discount_pct': pct, 'conditions': i.get('webExpsPrmoNm', None) and i['webExpsPrmoNm'].strip() or None,
        'sources': [f'{API}plansale-ancr-paging?sectId={SECT}' if src == 'ancr' else f'{API}spex-sect-item-search?sectId={SECT}'],
        '_sect': i.get('sectId'), '_sectNm': i.get('sectNm'), '_hmall_dc': (i.get('dcRate'), i.get('dcAmt'), i.get('copnDcAmt')),
    })
for x in items:
    x.pop('_img', None); x.pop('_hmall_dc', None)
    x['channel'] = x['channel']
out = {'category': 'food', 'source_id': SID, 'collected_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'items': [{k: v for k, v in x.items() if not k.startswith('_')} for x in items]}
json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
json.dump(items, open(os.path.join(CACHE, 'items_raw.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(len(raw), len(items))
