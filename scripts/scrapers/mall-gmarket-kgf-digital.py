# -*- coding: utf-8 -*-
"""G마켓 코그페 디지털/가전(상품리스트 4, 탭 없음) (exhib=280311, 모듈 inven_seq=407666) 전수 수집.
정적 HTML 첫 24개/탭 + /getInventoryItem 더보기 API(page_no 2..N). 실행: py -I scripts/scrapers/mall-gmarket-kgf-digital.py"""
import re, json, html, os, sys, time, datetime, urllib.parse as up
import requests

ROOT = r'E:/090_ETC/kf'
SID = 'mall-gmarket-kgf-digital'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/mall/{SID}.json'
EVENT = 'https://rpp.gmarket.co.kr/?exhib=280311#comp_27870410'
INVEN = '406317'
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36',
     'Referer': 'https://rpp.gmarket.co.kr/?exhib=280311', 'X-Requested-With': 'XMLHttpRequest',
     'Accept-Language': 'ko-KR,ko'}
os.makedirs(CACHE, exist_ok=True)

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=H, timeout=90, **kw)
            if r.status_code == 200: return r
        except Exception as e:
            print('retry', e)
        time.sleep(2 * (i + 1))
    raise RuntimeError(url)

pp = f'{CACHE}/page.html'
if os.path.exists(pp): page = open(pp, encoding='utf-8').read()
else:
    page = get('https://rpp.gmarket.co.kr/?exhib=280311').text
    open(pp, 'w', encoding='utf-8').write(page)

# 탭 정의: getItemList(this, inv,2,comp,'name',true, expose, lclass, false, 0, 'uid', tab)
tabs = []
for m in re.finditer(r"getItemList\(this, (\d+),2,(\d+),'([^']*)',true, (\d+), (\d+), false, 0, '(\w+)'\);\"[^>]*?data-max-goods=\"(\d+)\"", page):
    if m.group(1) == INVEN:
        tabs.append(dict(comp=m.group(2), name=m.group(3), expose=m.group(4), lclass=m.group(5), uid=m.group(6), tab=0, maxg=int(m.group(7)), pos=m.start()))
tabs.sort(key=lambda t: t['tab'])
print('tabs', [(t['tab'], t['lclass'], t['maxg']) for t in tabs])

def utp(url):
    try:
        q = up.unquote(up.unquote(html.unescape(url).split('utparam-url=')[1]))
    except Exception:
        return {}
    d = {}
    for k in ('origin_price', 'promotion_price', 'coupon_price'):
        m = re.search(r'"%s":"?(\d*)' % k, q)
        d[k] = int(m.group(1)) if m and m.group(1) else None
    return d

def absu(u):
    if not u: return None
    return 'https:' + u if u.startswith('//') else u

recs = []  # (tabname, goodsNo, name, image, brand, utp, delivery)
tabnames = {}
for t in tabs:
    # 정적 HTML
    ulp = page.rfind('<ul class="elements products-list', 0, t['pos'])
    seg = page[ulp:t['pos']]
    static_n = 0
    for li in re.split(r'<li class="elements_item', seg)[1:]:
        gm = re.search(r'data-goods-no="(\d+)"', li)
        if not gm: continue  # handlebars 템플릿 조각
        if static_n >= min(24, t['maxg']): break  # 마지막 탭 구간에 다음 모듈 상품이 섞임
        static_n += 1
        gn = gm.group(1)
        iv = re.search(r'data-item-value="([^"]*)"', li)
        iv = json.loads(html.unescape(iv.group(1))) if iv else {}
        href = re.search(r'href="(https://item\.gmarket\.co\.kr/Item\?[^"]*)"', li)
        recs.append(dict(tab=t['tab'], no=gn, name=iv.get('itemName'), img=absu(iv.get('imageUrl')), brand=iv.get('brandName') or '',
                         utp=utp(href.group(1)) if href else {}, ship=(re.search(r'<span class="box">([^<]*)</span>', li) or [None, None])[1]))
    # 더보기 API
    pg = 2
    while (pg - 1) * 24 < t['maxg']:
        cf = f'{CACHE}/more_t{t["tab"]}_p{pg}.json'
        if os.path.exists(cf): d = json.load(open(cf, encoding='utf-8'))
        else:
            last = sum(1 for r in recs if r['tab'] == t['tab']) - 1
            p = dict(inven_seq=INVEN, page_no=pg, page_size=24, view_type=2, comp_index=t['comp'], comp_name=t['name'],
                     is_pay_cnt_expose='true', goods_expose_cnt=t['expose'], inven_lclass_seq=t['lclass'], isnova='false', planid=0,
                     comp_unique_id=t['uid'], moduleIdx=0, moduleIdxTotal=0, lastListNo=last)
            d = get('https://rpp.gmarket.co.kr/getInventoryItem', params=p).json()
            json.dump(d, open(cf, 'w', encoding='utf-8'), ensure_ascii=False)
            time.sleep(0.5)
        for g in d.get('inventoryList', []):
            iv = g.get('itemValue') or {}
            recs.append(dict(tab=t['tab'], no=str(g['goodsNo']), name=g.get('goodsName'), img=absu(g.get('goodsImageUrl')),
                             brand=iv.get('brandName') or '', utp=utp(g.get('landingUrl', '')), ship=g.get('deliveryInfo')))
        print('tab', t['tab'], 'page', pg, len(d.get('inventoryList', [])), 'next', d.get('hasNextPage'))
        if not d.get('inventoryList'): break
        pg += 1

seen = set(); items = []; dup = 0
for r in recs:
    if r['no'] in seen: dup += 1; continue
    seen.add(r['no'])
    u = r['utp']; orig = u.get('origin_price'); promo = u.get('promotion_price'); cp = u.get('coupon_price')
    sale = cp if cp and (promo is None or cp < promo) else (promo or orig)
    cond = None
    if sale is not None and cp and sale == cp:
        cond = f"G마켓 쿠폰적용가(쿠폰 적용 시){'; 쿠폰 전 판매가 %s원' % format(promo, ',') if promo else ''}"
    pct = round((orig - sale) * 100 / orig, 1) if orig and sale is not None and orig > 0 else None
    n = len(items) + 1
    items.append({
        'item_id': f'{SID}-{n:04d}', 'category': 'mall', 'source_id': SID, 'unit': None,
        'vendor': r['brand'] or 'G마켓 판매자', 'channel': 'G마켓 코그페 디지털/가전', 'product': r['name'], 'model_code': None,
        'buy_url': f'https://item.gmarket.co.kr/Item?goodscode={r["no"]}', 'image_url': r['img'], 'rating': None, 'review_count': None,
        'event_url': EVENT, 'claimed_original_price': orig, 'sale_price': sale, 'claimed_discount_pct': pct, 'conditions': cond,
        'price_60d_low': None, 'price_60d_typical': None, 'price_history_note': None,
        'sources': [EVENT, 'https://rpp.gmarket.co.kr/getInventoryItem'], 'verify_status': None, 'verify_note': None, 'confidence': None})
out = {'category': 'mall', 'source_id': SID, 'collected_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00'), 'items': items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('total recs', len(recs), 'dups', dup, 'items', len(items), 'expected', sum(t['maxg'] for t in tabs))
