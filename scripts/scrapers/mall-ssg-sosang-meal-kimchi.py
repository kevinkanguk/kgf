import requests, json, re, os, time, datetime
SID = 'mall-ssg-sosang-meal-kimchi'
ROOT = 'E:/090_ETC/kf'
OUT = f'{ROOT}/data/raw/catalog/mall/{SID}.json'
CACHE = f'{ROOT}/data/cache/html/{SID}'
API = 'https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain'
EVENT = 'https://www.ssg.com/plan/planShop.ssg?dispCmptId=6000465146'
H = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://www.ssg.com', 'Referer': 'https://www.ssg.com/'}
os.makedirs(CACHE, exist_ok=True)

def fetch(page, size=30):
    body = {'common': {'aplVer': '', 'osCd': '', 'ts': time.strftime('%Y%m%d%H%M%S'), 'mobilAppNo': '99',
                       'dispDvicDivCd': '10', 'viewSiteNo': '6005'},
            'params': {'dispCmptId': '6000465146', 'inflowSiteNo': '6005', 'themeId': '7000886051',
                       'page': page, 'pageSize': size}}
    for _ in range(3):
        r = requests.post(API, json=body, headers=H, timeout=30)
        if r.status_code == 200:
            return r.json()['data']
        time.sleep(2)
    raise RuntimeError(r.status_code)

def num(v):
    try:
        return int(str(v).replace(',', ''))
    except Exception:
        return None

raw, seen, page = [], set(), 1
while True:
    d = fetch(page)
    json.dump(d, open(f'{CACHE}/page{page}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    for it in d.get('itemList', []):
        if it['itemId'] not in seen:
            seen.add(it['itemId']); raw.append(it)
    if not d.get('hasNext') or not d.get('itemList') or page > 100:
        break
    page += 1

items = []
for i, it in enumerate(raw, 1):
    sale = num(it.get('displayPrc')); orig = num(it.get('strikeOutPrc')) or None
    rate = (it.get('priceInfo') or {}).get('raw', {}).get('discountRate')
    pct = float(rate) if rate not in (None, '') else None
    if pct is None and orig and sale and orig > sale:
        pct = round((orig - sale) / orig * 100, 1)
    rp = it.get('recompPoint'); rc = it.get('recomRegCnt')
    rating = float(rp) if rp not in (None, '') else None
    if rating is not None and rating > 5:
        rating = round(rating / 20, 2)  # 100-point scale
    cond = []
    if it.get('soldOutYn') == 'Y': cond.append('품절')
    if (it.get('priceInfo') or {}).get('raw', {}).get('tildeDispYn') == 'Y': cond.append('가격 ~표시(옵션별 상이)')
    if (it.get('priceInfo') or {}).get('summary', {}).get('cpnTxt'): cond.append(it['priceInfo']['summary']['cpnTxt'])
    url = it.get('itemLnkd') or ''
    items.append({
        'item_id': f'{SID}-{i:04d}', 'category': 'mall', 'source_id': SID,
        'unit': it.get('sellCapaUnitNmWithUnitCapa') or None,
        'vendor': it.get('brandNm') or it.get('splVenNm') or '',
        'channel': 'SSG닷컴 소상공인 브랜드대전(간편식/김치/반찬)',
        'product': it['itemNm'], 'model_code': it['itemId'],
        'buy_url': url, 'image_url': it.get('itemImgUrl') or None,
        'rating': rating, 'review_count': num(rc),
        'event_url': EVENT + '&trackingId=7000886051',
        'claimed_original_price': orig, 'sale_price': sale, 'claimed_discount_pct': pct,
        'conditions': ', '.join(cond) or None,
        'sources': [EVENT, API],
    })
out = {'category': 'mall', 'source_id': SID,
       'collected_at': datetime.datetime.now().isoformat(timespec='seconds'), 'items': items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items), 'pages', page)
