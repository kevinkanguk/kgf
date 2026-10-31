# SSG.COM 소상공인 브랜드대전 '축산/수산/건식품' 테마 전 페이지 수집 (frontapi.ssg.com JSON API)
import requests, json, os, datetime, time
ROOT = 'E:/090_ETC/kf'
SID = 'mall-ssg-sosang-meat-fish'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/mall/{SID}.json'
DISP, THEME, SITE = '6000465146', '7000886054', '6005'
EVENT = f'https://www.ssg.com/plan/planShop.ssg?dispCmptId={DISP}#tab=meat-fish'
API = 'https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain'
H = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'https://www.ssg.com', 'Referer': 'https://www.ssg.com/'}
os.makedirs(CACHE, exist_ok=True)

def toint(v):
    try:
        s = str(v).replace(',', '').strip()
        return int(s) if s and s != 'null' else None
    except ValueError:
        return None

raw, seen, page = [], set(), 1
while page < 100:
    body = {'common': {'aplVer': '', 'osCd': '', 'ts': '20261031120000', 'mobilAppNo': '99', 'dispDvicDivCd': '10', 'viewSiteNo': SITE},
            'params': {'dispCmptId': DISP, 'inflowSiteNo': SITE, 'themeId': THEME, 'page': page, 'pageSize': 30}}
    r = requests.post(API, headers=H, json=body, timeout=30)
    r.raise_for_status()
    d = r.json()['data']
    json.dump(d, open(f'{CACHE}/theme_{THEME}_p{page}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    for it in d['itemList']:
        k = (it['itemId'], it.get('uitemId'))
        if k in seen: continue
        seen.add(k); raw.append(it)
    if not d.get('hasNext') or not d['itemList']: break
    page += 1; time.sleep(0.3)

items = []
for it in raw:
    pr = it.get('priceInfo', {}).get('raw', {})
    sale = toint(pr.get('displayPrc')) or toint(it.get('displayPrc'))
    orig = toint(it.get('strikeOutPrc'))
    if orig is not None and sale is not None and orig <= sale: orig = None
    rate = toint(pr.get('discountRate'))
    pct = round((1 - sale / orig) * 100, 1) if orig and sale else None
    conds = []
    if pr.get('tildeDispYn') == 'Y' or it.get('tildeDispYn') == 'Y': conds.append('옵션/딜 상품: 표시가는 최저가 기준(~)')
    if rate and not orig: conds.append(f'목록 표기 할인율 {rate}% (정가 미표기)')
    cp = it.get('priceInfo', {}).get('summary', {}).get('cpnTxt')
    if cp: conds.append(f'쿠폰: {cp}')
    rc = toint(it.get('recomRegCnt'))
    try: rt = round(float(it['recompPoint']), 2) if it.get('recompPoint') not in (None, '') else None
    except ValueError: rt = None
    url = it.get('itemLnkd') or f"https://www.ssg.com/item/itemView.ssg?itemId={it['itemId']}"
    items.append({
        'item_id': f'{SID}-{len(items)+1:04d}', 'category': 'mall', 'source_id': SID,
        'unit': None, 'vendor': it.get('brandNm') or 'SSG.COM', 'channel': 'SSG.COM 소상공인 브랜드대전',
        'product': it['itemNm'], 'model_code': None, 'buy_url': url,
        'image_url': it.get('itemImgUrl'), 'rating': rt, 'review_count': rc,
        'event_url': EVENT, 'claimed_original_price': orig, 'sale_price': sale,
        'claimed_discount_pct': pct if pct is not None else (float(rate) if rate else None),
        'conditions': '; '.join(conds) or None,
        'sources': [API + f'?themeId={THEME}', EVENT],
    })
out = {'category': 'mall', 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(items), 'pages', page)
