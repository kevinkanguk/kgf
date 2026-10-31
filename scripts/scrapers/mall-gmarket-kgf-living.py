# -*- coding: utf-8 -*-
"""G마켓 코그페 생활용품 기획전(exhib=280311) 전체 품목 수집. 실행: py -I scripts/scrapers/mall-gmarket-kgf-living.py"""
import re, json, html, os, math, time, datetime, requests
ROOT = 'E:/090_ETC/kf'
SID = 'mall-gmarket-kgf-living'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/mall/{SID}.json'
EVENT = 'https://rpp.gmarket.co.kr/?exhib=280311'
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36',
     'Accept-Language': 'ko-KR,ko', 'Referer': EVENT}
os.makedirs(CACHE, exist_ok=True)

def get(url, **kw):
    for i in range(3):
        try:
            r = requests.get(url, headers=H, timeout=60, **kw)
            r.raise_for_status(); return r
        except Exception as e:
            err = e; time.sleep(2)
    raise err

pg = f'{CACHE}/page.html'
if os.path.exists(pg):
    t = open(pg, encoding='utf-8').read()
else:
    t = get('https://rpp.gmarket.co.kr/?exhib=280311').text
    open(pg, 'w', encoding='utf-8').write(t)

def img(u):
    if not u: return None
    return 'https:' + u if u.startswith('//') else u
def num(s):
    s = re.sub(r'[^\d]', '', s or '')
    return int(s) if s else None
def clean_url(u):
    return re.sub(r'&utparam-url=.*$', '', html.unescape(u))

items = {}   # goodsNo -> dict
order = []
def add(no, name, image, origin, pct, sale, coupon, tab, mod):
    if no in items: return
    cond = None
    if coupon:
        cond = '쿠폰적용가(G마켓 쿠폰 다운로드 필요; 기획전 쿠폰: 12% 최대1만원, 1만원 이상 구매 시)'
    items[no] = dict(no=no, name=name, image=img(image), origin=origin, pct=pct, sale=sale, cond=cond, tab=tab, mod=mod)
    order.append(no)

# 탭(그룹) 단위 분리: inven_cat_<id> div
groups = []
for m in re.finditer(r'<div id="inven_cat_(\d+)" class="module module_item', t):
    groups.append((m.group(1), m.start()))
# 첫 탭은 inven_cat 래퍼가 없을 수 있으므로 btn_more 기준으로 병행
btns = [(m.start(), m.group(1)) for m in re.finditer(r'getItemList\(this, ([^)]*)\)', t)]
print('groups', len(btns))
bounds = [b[0] for b in btns]
prev = 0
more_params = []
for k, (pos, argstr) in enumerate(btns):
    seg = t[prev:pos]
    prev = pos
    head = re.findall(r'<h3 class="head_tit"><span>([^<]*)</span>', seg)
    tab = html.unescape(head[-1]) if head else ''
    # seg 안의 마지막 ul 블록만 (이전 탭 잔여 제외)
    ulpos = seg.rfind('<ul class="elements products-list')
    seg2 = seg[ulpos:] if ulpos >= 0 else seg
    for li in re.split(r'<li class="elements_item', seg2)[1:]:
        li = li.split('</li>\n')[0] if False else li
        no = re.search(r'data-goods-no="(\d+)"', li).group(1)
        name = html.unescape(re.search(r'class="title[^"]*" id="id_\d+"', li) and re.search(r'id="id_\d+"[\s\S]*?>([^<]+)</a>', li).group(1).strip())
        image = re.search(r'data-original="([^"]+)"', li)
        image = html.unescape(image.group(1)) if image else None
        ul = re.search(r'<ul class="price"[\s\S]*?</ul>', li)
        ul = ul.group(0) if ul else ''
        o = re.search(r'<del class="num">([\d,]+)</del>', ul)
        d = re.search(r'<li class="discount">(\d+)', ul)
        s = re.search(r'<li class="selling">\s*<strong>([\d,]+)</strong>', ul)
        coupon = '적용가' in ul or '쿠폰' in ul
        add(no, name, image, num(o.group(1)) if o else None, float(d.group(1)) if d else None,
            num(s.group(1)) if s else None, coupon, tab, None)
    a = [x.strip().strip("'") for x in argstr.split(',')]
    bm = re.search(r'data-max-goods="(\d+)" data-page-size="(\d+)"', t[pos:pos+1500])
    mm = re.search(r'data-moduleidx="(\d+)" data-moduleidx-total="(\d+)"', t[pos:pos+1500])
    more_params.append((tab, a, int(bm.group(1)) if bm else 0, int(bm.group(2)) if bm else 24, (mm.group(1), mm.group(2)) if mm else (0, 0)))

for tab, a, mx, ps, (mi, mt) in more_params:
    # a: invenSeq, viewType, compIdx, compName, isPay, goodsExpose, invenLclass, isnova, planid, compUid, tabIdx
    npages = max(2, math.ceil(mx / ps)) if mx else 2
    for p in range(2, npages + 3):
        prm = dict(inven_seq=a[0], page_no=p, page_size=ps, view_type=a[1], comp_index=a[2], comp_name=a[3],
                   is_pay_cnt_expose=a[4], goods_expose_cnt=a[5], inven_lclass_seq=a[6], isnova=a[7],
                   planid=a[8], comp_unique_id=a[9], moduleIdx=mi, moduleIdxTotal=mt)
        if len(a) > 10: prm['tabIndex'] = a[10]
        # moduleIdx 는 버튼의 data-moduleidx 와 동일
        cf = f'{CACHE}/api_{a[0]}_{a[6]}_{p}.json'
        if os.path.exists(cf):
            d = json.load(open(cf, encoding='utf-8'))
        else:
            d = get('https://rpp.gmarket.co.kr/getInventoryItem', params=prm).json()
            json.dump(d, open(cf, 'w', encoding='utf-8'), ensure_ascii=False)
        lst = d.get('inventoryList') or []
        if not lst: break
        for g in lst:
            ca = g.get('couponAppliedPriceInfo') or None
            origin = g.get('sellPrice')
            if ca:
                sale = ca.get('couponAppliedPrice'); pct = ca.get('discountRate')
            else:
                sale = g.get('discountPrice'); pct = g.get('discountRate')
            add(str(g['goodsNo']), g.get('goodsName'), g.get('goodsImageUrl'),
                int(origin) if origin else None, float(pct) if pct else None,
                int(sale) if sale else None, bool(ca), tab, None)
        print(tab, p, len(lst), len(items))

now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')
out = []
for i, no in enumerate(order, 1):
    x = items[no]
    pct = x['pct']
    if pct is None and x['origin'] and x['sale'] and x['origin'] > x['sale']:
        pct = round((1 - x['sale'] / x['origin']) * 100, 1)
    if x['origin'] and x['sale'] and x['origin'] <= x['sale'] and not x['pct']:
        x['origin'] = None; pct = None   # 정가 표기 없음
    buy = f'https://item.gmarket.co.kr/Item?goodscode={no}'
    out.append(dict(
        item_id=f'{SID}-{i:04d}', category='mall', source_id=SID, unit=None,
        vendor='G마켓 판매자', channel='G마켓 코리아그랜드페스타 기획전(생활용품)' + (f' - {x["tab"]}' if x['tab'] else ''),
        product=x['name'], model_code=None, buy_url=buy, image_url=x['image'], rating=None, review_count=None,
        event_url=EVENT, claimed_original_price=x['origin'], sale_price=x['sale'],
        claimed_discount_pct=pct, conditions=x['cond'], sources=[EVENT, buy]))
json.dump(dict(category='mall', source_id=SID, collected_at=now, items=out),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('saved', len(out))
