# 지그재그 코그페 기획전 '가디건&아우터' 탭 전수 수집 (api.zigzag.kr GraphQL). 실행: py -I 이 파일
import subprocess, json, os, datetime
ROOT = 'E:/090_ETC/kf'
SID = 'fashion_beauty-zigzag-kgf-outer'
EVENT = 'https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059'
PRESET = '3065206f-34b0-46ae-9405-1b86396d8317'
GROUP = 0
FRAG = ("fragment P on CmsProductsPresetProductCardItemList { item_list { shop { id main_domain name } product { product_url title discount_rate free_shipping zpay has_coupon price final_price catalog_product_id shop_product_no shop_id sellable_status is_brand discount_info { title } } } total_count end_cursor has_next_page } "
        "query Q($input: CmsProductsPresetProductCardItemListSearchInput!) { cms_products_preset_product_card_item_list(input: $input) { ...P } }")
def gql(var):
    p = subprocess.run(['curl', '-sL', '-m', '60', '-H', 'content-type: application/json', '-d', '@-', 'https://api.zigzag.kr/api/2/graphql'],
                       input=json.dumps({'query': FRAG, 'variables': var}).encode(), capture_output=True)
    return json.loads(p.stdout)
def main():
    cache = f'{ROOT}/data/cache/html/{SID}'; os.makedirs(cache, exist_ok=True)
    rows, after, pg = [], None, 0
    while True:
        inp = {'products_preset_uuid': PRESET, 'group_index': GROUP, 'limit': 50}
        if after: inp['after'] = after
        d = gql({'input': inp})
        if 'errors' in d and not d.get('data'):
            print(d['errors']); break
        r = d['data']['cms_products_preset_product_card_item_list']
        json.dump(d, open(f'{cache}/page{pg:03d}.json', 'w', encoding='utf8'), ensure_ascii=False)
        rows += r['item_list']; pg += 1
        print(pg, len(rows), r['total_count'])
        if not r['has_next_page'] or not r['end_cursor']: break
        after = r['end_cursor']
    items, seen = [], set()
    for it in rows:
        p, s = it['product'], it['shop']
        key = p['product_url'] or (p['shop_id'], p['title'])
        if key in seen: continue
        seen.add(key)
        price, final = p.get('price'), p.get('final_price')
        orig = price if (price and final and price > final) else None
        url = p['product_url'] or ''
        if url.startswith('/'): url = 'https://zigzag.kr' + url
        cond = []
        if p.get('has_coupon'): cond.append('쿠폰 적용 가능')
        if p.get('zpay'): cond.append('Z결제')
        if p.get('discount_info') and p['discount_info'].get('title'): cond.append(p['discount_info']['title'])
        n = len(items) + 1
        items.append({
            'item_id': f'{SID}-{n:04d}', 'category': 'fashion_beauty', 'source_id': SID, 'unit': None,
            'vendor': s['name'], 'channel': '지그재그 코리아그랜드페스타(가디건&아우터)', 'product': p['title'],
            'model_code': str(p['shop_product_no']) if p.get('shop_product_no') else None,
            'buy_url': url or EVENT, 'event_url': EVENT,
            'claimed_original_price': orig, 'sale_price': final,
            'claimed_discount_pct': p.get('discount_rate') if orig else None,
            'conditions': ', '.join(cond) or None,
            'sources': [EVENT, 'https://api.zigzag.kr/api/2/graphql cms_products_preset_product_card_item_list'],
        })
    out = {'category': 'fashion_beauty', 'source_id': SID, 'collected_at': datetime.date(2026, 10, 31).isoformat(), 'items': items}
    json.dump(out, open(f'{ROOT}/data/raw/catalog/fashion_beauty/{SID}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    print('saved', len(items))
main()
