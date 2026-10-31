# -*- coding: utf-8 -*-
"""food-onnuri-sijang-kgf: 온누리 전통시장(현대이지웰) 식품 전 품목 수집. 실행: py -I scripts/scrapers/food-onnuri-sijang-kgf.py"""
import requests, re, json, os, html, time, datetime
from concurrent.futures import ThreadPoolExecutor

ROOT = 'E:/090_ETC/kf'
SID = 'food-onnuri-sijang-kgf'
BASE = 'https://www.onnuri-sijang.com'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/food/{SID}.json'
H = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}
PAGE = 200
# 식품 대분류(lv1) + 테마전(중복은 goodsCd 로 제거)
CATS = [(100100001, '농산'), (100100018, '수입산 수산'), (100101676, '국내산 수산'), (100100034, '축산'),
        (100100053, '반찬/즉석식'), (100100068, '가공식품'), (100100089, '건강식품(건강/홍삼)'),
        (100100859, '테마전>수산대전 상품권'), (100101387, '테마전>당일/새벽배송')]
os.makedirs(CACHE, exist_ok=True)
s = requests.Session()
s.get(BASE + '/onnuri/main', headers=H, timeout=30)

def fetch(c, p):
    fn = f'{CACHE}/cat{c}_p{p}.html'
    if os.path.exists(fn):
        return open(fn, encoding='utf-8').read()
    for a in range(5):
        try:
            r = s.get(BASE + '/onnuri/goods/goodsListItem', params=dict(ctgCd=c, subCtgCd=c, pageIndex=p, pageRecordCount=PAGE), headers=H, timeout=60)
            r.encoding = 'utf-8'
            if r.status_code == 200:
                open(fn, 'w', encoding='utf-8').write(r.text)
                return r.text
        except Exception:
            time.sleep(2)
    raise RuntimeError(f'fail {c} {p}')

UNIT = re.compile(r'(\d+(?:\.\d+)?\s?(?:kg|KG|Kg|g|G|ml|mL|ML|L|l|개입|개|팩|봉|포|박스|세트|병|캔|입|마리|장|ea|EA)(?:\s?[x×*]\s?\d+)?)')

def parse(t, cname):
    out = []
    for blk in re.findall(r'<li  >(.*?)</li>', t, re.S):
        m = re.search(r"fn_goGoodsDetail\('(\d+)'\s*,\s*'(\d+)'", blk)
        if not m: continue
        gc, cc = m.groups()
        img = re.search(r'data-src="([^"]+)"', blk)
        v = re.search(r'<dt>(.*?)</dt>', blk, re.S)
        n = re.search(r'<dd class="ellipsis_2">(.*?)</dd>', blk, re.S)
        pr = re.search(r'<p class="price"><span>([\d,]+)</span>', blk)
        ptxt = re.search(r'<p class="price">(.*?)</p>', blk, re.S)
        tags = [x.strip() for x in re.findall(r'<span class="hash_tag[^>]*>([^<]*)<', blk) if x.strip()]
        if 'fish_coupon' in blk: tags.append('수산 쿠폰 공동구매')
        prod = html.unescape(re.sub(r'\s+', ' ', n.group(1))).strip() if n else ''
        cond = []
        if ptxt and '~' in ptxt.group(1): cond.append('옵션별 가격(최저가 표시 "~")')
        if tags: cond.append('태그: ' + ', '.join(tags))
        pct = None
        for tg in tags:
            mm = re.search(r'(\d+)\s*%', tg)
            if mm: pct = float(mm.group(1))
        um = UNIT.search(prod)
        out.append(dict(
            gc=gc, category='food', source_id=SID,
            unit=um.group(1) if um else None,
            vendor=html.unescape(v.group(1)).strip() if v else '',
            channel='온누리 전통시장(현대이지웰)',
            product=prod, model_code=None,
            buy_url=f'{BASE}/onnuri/goods/detail?goodsCd={gc}&ctgCd={cc}',
            image_url=img.group(1) if img else None,
            rating=None, review_count=None,
            event_url=f'{BASE}/onnuri/goods/list?ctgCd={cc}&subCtgCd={cc}',
            claimed_original_price=None,
            sale_price=int(pr.group(1).replace(',', '')) if pr else None,
            claimed_discount_pct=pct,
            conditions='; '.join(cond) or None,
            sources=[f'{BASE}/onnuri/goods/goodsListItem?ctgCd={cname}'] ))
    return out

def main():
    seen, items, issues = {}, [], []
    for c, cname in CATS:
        t = fetch(c, 1)
        total = int(re.search(r'id="goodsCount" value="(\d+)"', t).group(1))
        pages = (total + PAGE - 1) // PAGE
        with ThreadPoolExecutor(4) as ex:
            texts = list(ex.map(lambda p: fetch(c, p), range(1, pages + 1)))
        got = 0
        for tx in texts:
            for it in parse(tx, cname):
                got += 1
                if it['gc'] in seen: continue
                seen[it['gc']] = 1
                items.append(it)
        print(cname, total, got, len(items), flush=True)
        if got != total: issues.append(f'{cname}: 목록 {total} vs 파싱 {got}')
    for i, it in enumerate(items, 1):
        it.pop('gc'); it['sources'] = [it['buy_url']]
        items[i-1] = {'item_id': f'{SID}-{i:04d}', **it}
    json.dump({'category': 'food', 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('saved', len(items), issues)

if __name__ == '__main__':
    main()
