# -*- coding: utf-8 -*-
"""통통수산(tong-susan.com) '수산대전' 검색 목록 전수 수집. 실행: py -I -X utf8 scripts/scrapers/food-tongsusan-soosan.py"""
import json, re, html, time, datetime, pathlib, requests

ROOT = pathlib.Path(r'E:/090_ETC/kf')
SID = 'food-tongsusan-soosan'
BASE = 'https://www.tong-susan.com'
CACHE = ROOT / 'data/cache/html' / SID
OUT = ROOT / 'data/raw/catalog/food' / f'{SID}.json'
CACHE.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

src = [s for s in json.load(open(ROOT / 'data/sources/food.json', encoding='utf-8')) if s['source_id'] == SID][0] \
    if isinstance(json.load(open(ROOT / 'data/sources/food.json', encoding='utf-8')), list) else None
if src is None:
    d = json.load(open(ROOT / 'data/sources/food.json', encoding='utf-8'))
    src = [s for s in d['sources'] if s['source_id'] == SID][0]
LIST_URL = src['url']
SVAL = '수산대전'

S = requests.Session()
S.headers['User-Agent'] = 'Mozilla/5.0'
S.get(LIST_URL, timeout=30)

def params(page, rows=24):
    return dict(tagno=0, cno=0, isview='Y', istime=False, islike=False, sval=SVAL, sortby=0, usortby=12,
                DateDuration=0, eventidx=0, gpg_idx=0, pageType='DEFAULT', listType='DEFAULT',
                listLayoutType='2_DIV1', bannerUseYN='N', bannerIdx=0, bannerType='SLIDE',
                bannerSlideViewType=0, bannerSlideUseYN='Y', bannerSlideAutoTime=3, bannerSlideButtonUseYN='N',
                banner_effect='slide', banner_effect_direction='horizontal', recommendUseYN='N',
                recommendIdxs='', recommendType='DEFAULT', recommendLayoutType='SLIDE',
                recommendPosition='BOTTOM', userLayoutSettingidx='0', recommendUserLayoutSettingidx='0',
                curOS='AOS', sc_idx=0, isgift=False, page=page, rows=rows)

def won(s):
    m = re.search(r'([\d,]+)\s*원', s or '')
    return int(m.group(1).replace(',', '')) if m else None

blocks = []
seen = set()
page = 1
while page < 50:
    r = S.post(BASE + '/Goods/GetGoodsListNew', json=dict(param=params(page), list_template_name='/Views/Templates/LIST/2_DIV.cshtml', item_template_name='', igm_idx='0'),
               headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=30)
    j = r.json()
    (CACHE / f'api_p{page}.json').write_text(r.text, encoding='utf-8')
    h = j['data']['data']
    parts = re.split(r'(?=<div class="col-xs-6 savePage">)', h)
    new = 0
    for p in parts:
        m = re.search(r'data-mgcode="([^"]+)"', p)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1)); blocks.append((m.group(1), p)); new += 1
    if new == 0 or j['data']['cnt'] == 0:
        break
    page += 1

items = []
for n, (code, p) in enumerate(blocks, 1):
    title = html.unescape(re.search(r'<h4 class="prod-title[^>]*>(.*?)</h4>', p, re.S).group(1)).strip()
    org = re.search(r'class="org-price[^>]*>(.*?)</p>', p, re.S)
    pr = re.search(r'<p class="price[^>]*>(.*?)</p>', p, re.S)
    dc = re.search(r'class="dc-rate[^>]*>(.*?)</p>', p, re.S)
    img = re.search(r'data-src="([^"]+)"', p)
    orig = won(org.group(1)) if org else None
    sale = won(pr.group(1)) if pr else None
    pct = None
    if dc:
        m = re.search(r'([\d.]+)\s*%', dc.group(1))
        pct = float(m.group(1)) if m else None
    url = f'{BASE}/Goods/Detail/{code}'
    # detail: rating/review
    cp = CACHE / f'detail_{code}.html'
    if cp.exists():
        dt = cp.read_text(encoding='utf-8')
    else:
        dt = S.get(url, timeout=30).text
        cp.write_text(dt, encoding='utf-8'); time.sleep(0.3)
    rating = review = None
    m = re.search(r'"ratingValue":\s*([\d.]+),\s*"reviewCount":\s*(\d+)', dt)
    if m:
        rating, review = float(m.group(1)), int(m.group(2))
    else:
        m = re.search(r'avgstar[^>]*>\s*<i[^>]*></i>\s*(\d+)', dt)
        if m: review = int(m.group(1))
    ship = re.search(r'배송비</p><p[^>]*>(.*?)</p>', dt, re.S)
    conds = []
    cm = re.search(r'수산대전\s*적용시\s*([\d,]+)\s*원', title)
    if cm:
        conds.append(f'수산대전 적용시 {cm.group(1)}원(제목 표기, 쿠폰/행사 적용 조건)')
    if ship:
        conds.append('배송비 ' + html.unescape(re.sub(r'\s+', ' ', ship.group(1)).strip()))
    um = re.findall(r'\d+(?:\.\d+)?\s*(?:kg|g|KG|Kg|미|팩|마리|개입|개|봉|박스|세트|L|ml)\b|\d+\s*kg', title)
    unit = ' '.join(dict.fromkeys(u.strip() for u in um)) or None
    clean = re.sub(r'[⭐🦐🔥]', '', title).strip()
    items.append(dict(
        item_id=f'{SID}-{n:04d}', category='food', source_id=SID, unit=unit,
        vendor='통통수산', channel=src.get('channel') or '수산대전', product=clean, model_code=code,
        buy_url=url, image_url=img.group(1) if img else None, rating=rating, review_count=review,
        event_url=LIST_URL, claimed_original_price=orig, sale_price=sale, claimed_discount_pct=pct,
        conditions='; '.join(conds) or None, sources=[LIST_URL, url]))

out = dict(category='food', source_id=SID, collected_at=datetime.date(2026, 10, 31).isoformat(), items=items)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(len(items))
