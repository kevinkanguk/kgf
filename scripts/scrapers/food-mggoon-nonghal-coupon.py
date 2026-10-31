# -*- coding: utf-8 -*-
"""mggoon.co.kr cno=39 (농할쿠폰) 전체 품목 수집. 사이트 JSON API /Goods/GetGoodsListNew 사용. 실행: py -I 이 파일"""
import requests, json, re, html, os, datetime
ROOT = 'E:/090_ETC/kf'
SID = 'food-mggoon-nonghal-coupon'
BASE = 'https://mggoon.co.kr'
EVENT = BASE + '/Goods/List?cno=39&pageType=DEFAULT'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
s = requests.Session(); s.headers['User-Agent'] = 'Mozilla/5.0'
s.get(EVENT, timeout=30)
tok = s.cookies.get('csrftoken')
ROWS = 24
def params(page):
    return dict(page=page, rows=ROWS, tagno=0, cno=39, isview='Y', istime=False, islike=False, sval='',
                sortby=0, usortby=4, DateDuration=7, eventidx=0, gpg_idx=0, pageType='DEFAULT',
                listType='DEFAULT', listLayoutType='2_DIV1', bannerUseYN='Y', bannerIdx=19,
                recommendUseYN='N', recommendIdxs='', recommendType='DEFAULT', recommendLayoutType='2_DIV1',
                recommendPosition='BOTTOM', userLayoutSettingidx='0', recommendUserLayoutSettingidx='0',
                curOS='AOS', sc_idx=0, isgift=False)
def num(x):
    x = re.sub(r'[^\d]', '', x or '')
    return int(x) if x else None
items = []; seen = set(); page = 1; total = None
while True:
    body = {'param': params(page), 'list_template_name': '/Views/Templates/LIST/2_DIV.cshtml', 'item_template_name': '', 'igm_idx': '0'}
    r = s.post(BASE + '/Goods/GetGoodsListNew', json=body, headers={'X-CSRFToken': tok or '', 'X-Requested-With': 'XMLHttpRequest', 'Referer': EVENT}, timeout=60)
    j = r.json()
    open(f'{CACHE}/page{page}.json', 'w', encoding='utf8').write(json.dumps(j, ensure_ascii=False))
    d = j.get('data') if isinstance(j, dict) else None
    if isinstance(d, dict): d = d.get('data', d)
    if not isinstance(d, str):
        print('unexpected', str(j)[:300]); break
    open(f'{CACHE}/page{page}.html', 'w', encoding='utf8').write(d)
    blocks = d.split('savePage')[1:]
    new = 0
    for b in blocks:
        m = re.search(r'data-mgcode="([^"]+)"', b)
        if not m or m.group(1) in seen: continue
        code = m.group(1); seen.add(code); new += 1
        t = re.search(r'prod-title[^>]*>(.*?)</h4>', b, re.S)
        img = re.search(r'data-src="([^"]+)"', b)
        org = re.search(r'org-price[^>]*>([^<]*)</p>', b, re.S)
        pr = re.search(r'class="price [^"]*"[^>]*>([^<]*)</p>', b, re.S)
        dc = re.search(r'dc-rate[^>]*>([^<]*)</p>', b, re.S)
        av = re.search(r'avgstar">(.*?)</p>', b, re.S)
        stars = rc = None
        if av:
            stars = len(re.findall(r'fa-star"', av.group(1)))
            rc = num(re.sub(r'<[^>]+>', '', av.group(1)))
        items.append(dict(code=code, product=html.unescape(re.sub(r'\s+', ' ', t.group(1)).strip()) if t else None,
                          img=img.group(1) if img else None, org=num(org.group(1)) if org else None,
                          sale=num(pr.group(1)) if pr else None, dc=num(dc.group(1)) if dc else None,
                          rating=stars, rc=rc))
    cnt = j.get('cnt') if isinstance(j, dict) else None
    print('page', page, 'blocks', len(blocks), 'new', new)
    if new == 0 or len(blocks) < ROWS: break  # 첫 페이지 9건 < rows(24) 이면 종료 (dataTotalCount=9)
    page += 1
out = []
for i, it in enumerate(items, 1):
    o, sp = it['org'], it['sale']
    pct = it['dc'] if it['dc'] is not None else (round((o - sp) / o * 100, 1) if o and sp and o > sp else None)
    out.append(dict(item_id=f'{SID}-{i:04d}', category='food', source_id=SID, unit=None, vendor='돌쇠네(mggoon)',
        channel='돌쇠네(mggoon) 농할쿠폰', product=it['product'], model_code=it['code'],
        buy_url=f"{BASE}/Goods/Detail/{it['code']}", image_url=it['img'], rating=it['rating'], review_count=it['rc'],
        event_url=EVENT, claimed_original_price=o, sale_price=sp, claimed_discount_pct=pct, conditions=None,
        sources=[EVENT], verify_status=None, verify_note=None, confidence=None))
json.dump(dict(category='food', source_id=SID, collected_at=datetime.date.today().isoformat() if False else '2026-10-31', items=out),
          open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
print('saved', len(out))
