import requests, re, json, html, os, sys, datetime
ROOT = 'E:/090_ETC/kf'
SID = 'appliance-eland-main'
CACHE = f'{ROOT}/data/cache/html/{SID}'
OUT = f'{ROOT}/data/raw/catalog/appliance/{SID}.json'
BASE = 'https://www.etlandmall.co.kr'
H = {'User-Agent': 'Mozilla/5.0'}
os.makedirs(CACHE, exist_ok=True)
# plans excluded as non-appliance (set via EXCLUDE env/const)
EXCLUDE = {'11623', '11875', '12083', '12160', '12178', '12186', '12191', '12158', '12182', '12181'}
S = requests.Session(); S.headers.update(H)

def txt(r): return r.content.decode('utf-8', 'replace')

home = txt(S.get(BASE + '/', timeout=30))
plans = sorted(set(re.findall(r'planProductList\.do\?PLN_MST_IDX=(\d+)', home)))
items, seen, plan_stats = [], {}, {}
for pid in plans:
    purl = f'{BASE}/pc/event/planProductList.do?PLN_MST_IDX={pid}'
    page = txt(S.get(purl, timeout=30))
    title = html.unescape(page[page.find('<title>')+7:page.find('</title>')]).strip()
    groups = re.findall(r'<dt[^>]*planGrpIdx="(\d+)"[^>]*planGrpCol="(\d+)"', page)
    plan_stats[pid] = {'title': title, 'excluded': pid in EXCLUDE, 'n': 0}
    if pid in EXCLUDE: continue
    for gi, gc in groups:
        fn = f'{CACHE}/ajax_{pid}_{gi}.html'
        if os.path.exists(fn): body = open(fn, encoding='utf8').read()
        else:
            r = S.post(BASE + '/pc/event/planProductDetailListAjax.do', data={
                'PLN_MST_IDX': pid, 'PLN_GRP_COL': gc, 'PLN_GRP_IDX': gi, 'prePlan': '',
                'PLN_MST_SPECIAL_YN': 'Y', 'PLN_MST_PRD_DPL_YN': 'Y', 'PLN_TIME_SALE': 'N',
                'PLN_POINT_SALE_YN': 'N', 'chlCode': ''},
                headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': purl}, timeout=30)
            body = txt(r); open(fn, 'w', encoding='utf8').write(body)
        for blk in body.split('<a class="components_product_list"')[1:]:
            m = re.search(r'href="([^"]*prdMstCd=([A-Za-z0-9]+)[^"]*)"', blk)
            if not m: continue
            code = m.group(2)
            if code in seen: continue
            nm = re.search(r'components_product_name">\s*(.*?)</p>', blk, re.S)
            name = html.unescape(re.sub(r'\s+', ' ', nm.group(1))).strip() if nm else None
            if not name: continue
            vendor, model, prod = None, None, name
            mm = re.match(r'\[([^\]/]*)(?:/([^\]]*))?\]\s*(.*)', name)
            if mm: vendor, model, prod = mm.group(1).strip() or None, (mm.group(2) or '').strip() or None, mm.group(3).strip()
            pr = re.search(r'priceGroup_price">\s*([\d,]+)', blk)
            pct = re.search(r'priceGroup_sale">\s*(\d+)\s*%', blk)
            img = re.search(r'<img\s+src="([^"]+)"[^>]*class="product_thum"', blk)
            rt = re.search(r'<i class="star_\d+">[^<]*</i></span>\s*([\d.]+)', blk)
            rc = re.search(r'reivewGroup_total">\s*\(([\d,]+)\)', blk)
            conds = []
            for li in re.findall(r'<li class="components_product_benefit_\w+">(.*?)</li>', blk, re.S):
                t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', li))).strip()
                if t: conds.append(t)
            seen[code] = 1
            plan_stats[pid]['n'] += 1
            items.append({
                'item_id': f'{SID}-{len(items)+1:04d}', 'category': 'appliance', 'source_id': SID,
                'unit': None, 'vendor': vendor or '', 'channel': '전자랜드몰 - ' + title,
                'product': prod, 'model_code': model, 'buy_url': f'{BASE}/pc/product/product.do?prdMstCd={code}',
                'image_url': (BASE + img.group(1)) if img and img.group(1).startswith('/') else (img.group(1) if img else None),
                'rating': float(rt.group(1)) if rt else None,
                'review_count': int(rc.group(1).replace(',', '')) if rc else None,
                'event_url': purl, 'claimed_original_price': None,
                'sale_price': int(pr.group(1).replace(',', '')) if pr else None,
                'claimed_discount_pct': float(pct.group(1)) if pct else None,
                'conditions': ', '.join(conds) or None, 'sources': [purl, f'{BASE}/pc/product/product.do?prdMstCd={code}'],
            })
out = {'category': 'appliance', 'source_id': SID, 'collected_at': '2026-10-31', 'items': items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
json.dump(plan_stats, open(f'{CACHE}/plan_stats.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(len(items))
