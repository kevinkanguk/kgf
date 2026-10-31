import sys, json, re, time, os, datetime, requests
sys.stdout.reconfigure(encoding='utf8')
SID = 'appliance-11st-kgf'
EV = 'https://plan.11st.co.kr/plan/front/exhibitions/2211141/detail'
CACHE = 'E:/090_ETC/kf/data/cache/html/' + SID
OUT = 'E:/090_ETC/kf/data/raw/catalog/appliance/' + SID + '.json'
H = {'User-Agent': 'Mozilla/5.0', 'Referer': EV, 'X-Requested-With': 'XMLHttpRequest'}
THEMES = [(1, 1756462, 75), (2, 1756467, 75), (3, 1756468, 85), (4, 1756469, 78), (5, 1757688, 25), (6, 1757689, 30), (7, 1757690, 33)]
# 이 기획전은 식품/건강/리빙/뷰티/패션 탭뿐(가전 탭 없음). 전 테마(401개)를 캐시한 뒤 전자기기성 품목만 가전 카테고리로 채택.
KW = re.compile(r'전기 온열|온열안대|홈캠|홈카메라|CCTV|충전식 2만루멘|충전식 센서 LED|산소발생기')
os.makedirs(CACHE, exist_ok=True)
seen, items = set(), []
for i, n, c in THEMES:
    fp = f'{CACHE}/theme_{i}.json'
    if os.path.exists(fp):
        j = json.load(open(fp, encoding='utf8'))
    else:
        r = requests.post(f'https://plan.11st.co.kr/plan/front/exhibitions/2211141/themes/{n}/products',
            data=dict(templateType=4, page=0, size=c + 50, themeIndex=i, productSortCode='', deliveryType='',
                      isUsableProductNetFunnel='false', recommendedProducts='', recommendRequestId='', isAcme='false'), headers=H)
        open(fp, 'w', encoding='utf8').write(r.text); j = r.json(); time.sleep(.5)
    for p in j['themeProducts']:
        if p['productNo'] in seen or not KW.search(p['productName']): continue
        seen.add(p['productNo'])
        money = lambda s: int(s.replace(',', '')) if s else None
        sale, orig = money(p['finalPrice']), money(p['sellPrice'])
        pct = float(p['discountRate']) if p.get('showDiscountRate') else None
        items.append(dict(
            item_id=f'{SID}-{len(items)+1:04d}', category='appliance', source_id=SID, unit=None,
            vendor='11번가 입점업체', channel='11번가 2026 소상공인 온라인 판로지원', product=p['productName'].strip(),
            model_code=None, buy_url=p['productLink'], image_url=p['productImage'],
            rating=round(p['satisfactionScore'] / 20, 2) if p.get('satisfactionScore') else None,
            review_count=money(p['reviewCount']) if p.get('showReviewCount') else None,
            event_url=EV, claimed_original_price=orig, sale_price=sale, claimed_discount_pct=pct, conditions=None,
            sources=[EV, p['productLink']]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category='appliance', source_id=SID, collected_at='2026-10-31', items=items), open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
print(len(items))
