# food-oasis-kgf scraper. run: py -I scripts/scrapers/food-oasis-kgf.py
import re, json, os, html, time, datetime
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SID = 'food-oasis-kgf'
CACHE = os.path.join(ROOT, 'data', 'cache', 'html', SID)
OUT = os.path.join(ROOT, 'data', 'raw', 'catalog', 'food', SID + '.json')
BASE = 'https://www.oasis.co.kr'
EVENT = BASE + '/event/2026/koreaGrandFestival_1029'
H = {'User-Agent': 'Mozilla/5.0'}
CATS = {5737: '26년 매칭업체', 124: '소상공인'}  # event "더보기" targets
os.makedirs(CACHE, exist_ok=True)

def get(c, p):
    fp = os.path.join(CACHE, f'{c}_{p}.html')
    if os.path.exists(fp):
        return open(fp, encoding='utf-8').read()
    for i in range(4):
        try:
            r = requests.get(f'{BASE}/product/list', params=dict(categoryId=c, page=p, sort='', direction='', couponType='', rows=60), headers=H, timeout=40)
            if r.status_code == 200:
                open(fp, 'w', encoding='utf-8').write(r.text)
                return r.text
        except Exception:
            pass
        time.sleep(2 + i * 2)
    return ''

def num(s):
    s = re.sub(r'[^\d]', '', s or '')
    return int(s) if s else None

def parse(t, c):
    out = []
    parts = re.split(r'<li class="swiper-slide pListItem', t)[1:]
    for b in parts:
        m = re.search(r'data-productid="(\d+)"', b)
        if not m:
            continue
        pid = m.group(1)
        g = lambda p: (re.search(p, b, re.S) or [None, None])[1]
        title = html.unescape(re.sub(r'\s+', ' ', g(r'class="listTit">(.*?)</a>') or '')).strip()
        img = g(r'<img[^>]*data-src="([^"]+)"') or g(r'<img[^>]*src="([^"]+)"')
        orig = num(g(r'<span class="price_original[^>]*><b>([\d,]+)</b>'))
        sale = num(g(r'<span class="price_discount"><b>([\d,]+)</b>'))
        rate = g(r'class="price_discountRate[^>]*>([\d.]+)%')
        cp = num(g(r'class="info_cpPrice">[^<]*?([\d,]+)원'))
        cpn = g(r'class="info_btmCoupon">\s*([\d.]+)')
        rating = g(r'class="info_reviewLike[^>]*>\s*([\d.]+)\s*<span class="info_reviewNumber">')
        rc = g(r'class="info_reviewNumber">\s*([\d,]+)')
        kw = g(r'class="badge_keyword[^>]*>([^<]*)')
        cond = []
        if cp: cond.append(f'쿠폰적용가 {cp:,}원')
        if cpn: cond.append(f'오아시스 30% 쿠폰(상품 쿠폰 {cpn}%) 다운로드 필요')
        out.append(dict(pid=pid, category=c, product=title, image_url=img, orig=orig, sale=sale,
                        pct=float(rate) if rate else None, rating=float(rating) if rating else None,
                        review=int(rc.replace(',', '')) if rc else None, cond='; '.join(cond) or None, kw=kw))
    return out

def total_pages(t):
    m = re.search(r'name="totalPages" value="(\d*)"', t)
    return int(m.group(1)) if m and m.group(1) else 1

def main():
    allp = []
    issues = []
    for c in CATS:
        t1 = get(c, 1)
        n = total_pages(t1)
        with ThreadPoolExecutor(6) as ex:
            pages = list(ex.map(lambda p: (p, get(c, p)), range(1, n + 1)))
        cnt = 0
        for p, t in pages:
            if not t:
                issues.append(f'cat {c} page {p} fetch failed'); continue
            its = parse(t, c); cnt += len(its); allp += its
        print(c, n, cnt)
    seen = {}
    for x in allp:
        if x['pid'] not in seen:
            seen[x['pid']] = x
    items = []
    for i, x in enumerate(seen.values(), 1):
        sale = x['sale']
        orig = x['orig'] if x['orig'] and sale and x['orig'] > sale else None
        pct = x['pct'] if orig else None
        items.append(dict(
            item_id=f'{SID}-{i:04d}', category='food', source_id=SID, unit=None,
            vendor='오아시스마켓', channel='오아시스마켓 코리아그랜드페스티벌(' + CATS[x['category']] + ')',
            product=x['product'], model_code=None,
            buy_url=f"{BASE}/product/detail/{x['pid']}", image_url=x['image_url'],
            rating=x['rating'], review_count=x['review'], event_url=EVENT,
            claimed_original_price=orig, sale_price=sale, claimed_discount_pct=pct,
            conditions=x['cond'], sources=[f"{BASE}/product/list?categoryId={x['category']}&rows=60", EVENT]))
    dup = len(allp) - len(items)
    if dup: issues.append(f'{dup} duplicate product ids removed')
    data = dict(category='food', source_id=SID,
                collected_at=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00'), issues=issues, items=items)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('items', len(items), issues)

main()
