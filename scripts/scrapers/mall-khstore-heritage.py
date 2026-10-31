import requests, re, json, html, os, datetime, urllib.parse
ROOT = 'E:/090_ETC/kf'
SID = 'mall-khstore-heritage'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/mall/{SID}.json'
BASE = 'https://khstore.or.kr'
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
S = requests.Session(); S.headers.update({'User-Agent': 'Mozilla/5.0'})
def get(u, fn):
    p = f'{CACHE}/{fn}'
    if os.path.exists(p): return open(p, encoding='utf8').read()
    t = S.get(u, timeout=30).content.decode('utf-8', 'replace'); open(p, 'w', encoding='utf8').write(t); return t
def won(s):
    m = re.search(r'([\d,]+)\s*원', s or ''); return int(m.group(1).replace(',', '')) if m else None
def strip(s): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s))).strip()
items, seen = [], set()
page = 1; last = 1
while page <= last:
    t = get(f'{BASE}/product/list.html?cate_no=23&page={page}', f'list_23_{page}.html')
    if page == 1:
        last = max([int(x) for x in re.findall(r'cate_no=23&(?:amp;)?page=(\d+)', t)] or [1])
    for blk in re.split(r'<li class="item column_grid xans-record-">', t)[1:]:
        m = re.search(r'id="anchorBoxId_(\d+)"', blk)
        if not m or m.group(1) in seen: continue
        pid = m.group(1); seen.add(pid)
        href = re.search(r'href="(/product/[^"]+)"', blk).group(1)
        nm = re.search(r'class="prd_name">(.*?)</div>', blk, re.S)
        name = strip(nm.group(1)) if nm else ''
        img = re.search(r'<img src="([^"]+)"', blk)
        imgu = ('https:' + img.group(1) if img.group(1).startswith('//') else BASE + img.group(1)) if img else None
        orig = sale = None
        for li in re.findall(r'<li class=" xans-record-">(.*?)</li>', blk, re.S):
            if 'line-through' in li: orig = won(strip(li))
            else:
                v = won(strip(li)); sale = v if v is not None else sale
        if sale is None:
            pm = re.search(r'<span class="displaynone price">(\d+)</span>', blk); sale = int(pm.group(1)) if pm else None
        pct = round((orig - sale) / orig * 100, 1) if orig and sale and orig > sale else None
        brand = strip(re.search(r'class="prd_brand">(.*?)</div>', blk, re.S).group(1)) or None
        rv = re.search(r'(?:후기|리뷰)\s*:?\s*(\d+)', strip(blk))
        items.append({
            'item_id': f'{SID}-{len(items)+1:04d}', 'category': 'mall', 'source_id': SID, 'unit': None,
            'vendor': brand or 'K-Heritage 스토어', 'channel': 'K-Heritage 스토어(국가유산진흥원)',
            'product': name, 'model_code': None,
            'buy_url': BASE + urllib.parse.quote(href.split('?')[0].rsplit('/category/', 1)[0] + '/', safe='/%'),
            'image_url': imgu, 'rating': None, 'review_count': int(rv.group(1)) if rv else None,
            'event_url': BASE + '/', 'claimed_original_price': orig, 'sale_price': sale,
            'claimed_discount_pct': pct, 'conditions': None, 'sources': [f'{BASE}/product/list.html?cate_no=23&page={page}']})
    page += 1
json.dump({'category': 'mall', 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items},
          open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
print(len(items), last)
