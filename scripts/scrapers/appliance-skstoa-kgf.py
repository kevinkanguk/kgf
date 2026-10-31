# -*- coding: utf-8 -*-
"""SK스토아 코그페 기획전(2026103519) 가전/디지털 탭(planGoodsGb=04) -> catalog JSON.
라이브 API(/plan/planDetail/more)는 requests 로는 400 이라 브라우저 탭 fetch 결과를
data/cache/html/appliance-skstoa-kgf/planDetail_more_gb04.json 에 저장해 두고 이를 파싱한다.
다른 탭(식품/가구·리빙/생활·주방/패션·뷰티)은 타 카테고리 소스 담당이므로 제외."""
import json, re, datetime
ROOT = 'E:/090_ETC/kf/'
CACHE = ROOT + 'data/cache/html/appliance-skstoa-kgf/planDetail_more_gb04.json'
OUT = ROOT + 'data/raw/catalog/appliance/appliance-skstoa-kgf.json'
SID = 'appliance-skstoa-kgf'
EVENT = 'https://www.skstoa.com/plan/event/detail/2026103519'
BRANDS = [('신일', '신일'), ('매직쉐프', '매직쉐프'), ('트루리빙', '트루리빙'), ('코나에코홈', '코나에코홈'),
          ('베이직', '베이직스'), ('스마트카라', '스마트카라'), ('한경희', '한경희생활과학'), ('한일', '한일전기'),
          ('모즈스웨덴', '모즈스웨덴'), ('MOZ', '모즈스웨덴'), ('우들', '우들'), ('윈드에어', '윈드에어'),
          ('노멀라이프', '노멀라이프'), ('레이캅', '레이캅'), ('홍두깨', '홍두깨'), ('유니맥스', '유니맥스')]

def vendor_of(name, model):
    for k, v in BRANDS:
        if k in name:
            return v
    if model and re.match(r'(SMX|SVC)-', model):
        return '신일'  # 모델코드 접두어 기준(상품명에 브랜드 미표기)
    return 'SK스토아'

def model_of(name):
    toks = re.findall(r'[A-Za-z][A-Za-z0-9\-/+]*\d[A-Za-z0-9\-/+]*|\d+[A-Za-z][A-Za-z0-9\-/+]*', name)
    toks = [t for t in toks if re.search(r'[A-Za-z]', t) and re.search(r'\d', t) and len(t) >= 5 and '-' in t or re.fullmatch(r'V1', t)]
    return toks[-1].rstrip('+') if toks else None

def main():
    d = json.load(open(CACHE, encoding='utf8'))
    cols = d['_cols']; items = []
    for n, row in enumerate(d['rows'], 1):
        r = dict(zip(cols, row))
        name = re.sub(r'\s+', ' ', r['goodsName']).strip()
        m = re.search(r'\(정상가\s*([\d,]+)원\)', name)
        listed = r['salePrice']; best = r['bestPrice']
        conds = []
        if m:
            orig = int(m.group(1).replace(',', '')); sale = listed
            pct = round((orig - sale) * 100 / orig, 1)
            conds.append("원가는 상품명 표기 '정상가 %s원'(판매자 주장)" % format(orig, ','))
        elif r['couponRate'] and best < listed:
            orig = listed; sale = best; pct = float(r['couponRate'])
            conds.append('목록 표기 할인율 %d%% 적용가(쿠폰/즉시할인 등 조건은 상품 페이지 확인)' % r['couponRate'])
        else:
            orig = None; sale = listed; pct = None
        if r['saleGb'] != '00':
            conds.append('saleGb=%s (판매상태 코드, 품절/일시중지 가능성 미확인)' % r['saleGb'])
        pname = re.sub(r'^\(정상가\s*[\d,]+원\)\s*', '', name)
        model = model_of(name)
        cnt = r['commentCnt'] or 0
        rating = r['argCommentSumDouble'] if cnt and r['argCommentSumDouble'] else None
        items.append({
            'item_id': '%s-%04d' % (SID, n), 'category': 'appliance', 'source_id': SID,
            'unit': None, 'vendor': vendor_of(name, model), 'channel': 'SK스토아 코리아그랜드페스티벌',
            'product': pname, 'model_code': model,
            'buy_url': 'https://www.skstoa.com/display/goods/%s' % r['goodsCode'],
            'image_url': 'https://imagecdn.skstoa.com' + r['imagePath'],
            'rating': rating, 'review_count': cnt, 'event_url': EVENT,
            'claimed_original_price': orig, 'sale_price': sale, 'claimed_discount_pct': pct,
            'conditions': '; '.join(conds) or None,
            'sources': [EVENT, 'https://www.skstoa.com/plan/planDetail/more?planCode=2026103519&planGoodsGb=04'],
            'tab_category': r['categoryName'].replace('^', ' > ')})
    out = {'category': 'appliance', 'source_id': SID,
           'collected_at': datetime.datetime(2026, 10, 31).isoformat() + '+09:00', 'items': items}
    json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    print(len(items))

if __name__ == '__main__':
    main()
