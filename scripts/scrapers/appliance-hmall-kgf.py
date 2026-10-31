# -*- coding: utf-8 -*-
"""appliance-hmall-kgf: Hmall 물가안정 프로젝트(소상공인 기획전, sectId=2811083) 가전 품목 수집.
기획전 하위 탭(plansale-ancr-list) 전부를 plansale-ancr-paging API 로 긁어
 - 가전/가구/침구 탭(3129672)은 전 품목
 - 그 외 탭은 대분류 42(가전/디지털) 품목만
담는다. 실행: py -I scripts/scrapers/appliance-hmall-kgf.py
"""
import json, os, time, datetime, requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SID = 'appliance-hmall-kgf'
MAIN = 2811083
APPL_TAB = 3129672
EVENT_URL = 'https://www.hmall.com/md/dpa/searchSpexSectItem?sectId=%d' % MAIN
CACHE = os.path.join(ROOT, 'data', 'cache', 'html', SID)
OUT = os.path.join(ROOT, 'data', 'raw', 'catalog', 'appliance', SID + '.json')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36', 'Referer': EVENT_URL}
API = 'https://www.hmall.com/api/hf/dp/v1/sect-mng/'

def get(path, **p):
    r = requests.get(API + path, params=p, headers=H, timeout=60)
    r.raise_for_status()
    return r.text, r.json()['respData']

def img(it):
    c = it['slitmCd']; n = it.get('itemBaseImgNm') or (c + '_0.jpg')
    return 'https://image.hmall.com/static/%s/%s/%s/%s/%s?RS=300x300' % (c[7], c[6], c[4:6], c[2:4], n)

def main():
    os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
    txt, lst = get('plansale-ancr-list', sectId=MAIN)
    open(os.path.join(CACHE, 'ancr-list.json'), 'w', encoding='utf8').write(txt)
    tabs = [(a['sectId'], a.get('sectLbl') or a.get('sectNm')) for a in lst['ancrList']]
    seen, items, per_tab = {}, [], {}
    for sid, nm in tabs:
        txt, d = get('plansale-ancr-paging', sectId=sid, listSize=3000, searchMode='true', searchYn='Y', brndMallYn='Y')
        open(os.path.join(CACHE, 'sect_%d.json' % sid), 'w', encoding='utf8').write(txt)
        il = d['itemList']; per_tab[nm] = len(il)
        for it in il:
            c = it['slitmCd']
            if c in seen: continue
            if not (sid == APPL_TAB or it.get('itemLCsfCd') == '42'): continue
            seen[c] = 1
            sell, best = it.get('sellPrc') or 0, it.get('bbprc') or 0
            sale = best if best else sell
            orig = sell if sell and sale and sale < sell else None
            pct = round((sell - sale) * 100.0 / sell, 1) if orig else None
            cond = None
            if it.get('copnDcAmt'):
                cond = '쿠폰 적용가(%s%% / %d원 할인 포함)' % (it.get('copnDcRate'), it['copnDcAmt'])
            rv = it.get('reviewCnt')
            rt = it.get('itemEvalEvgScrg')
            items.append({
                'item_id': '%s-%04d' % (SID, len(items) + 1), 'category': 'appliance', 'source_id': SID,
                'unit': None, 'vendor': it.get('brndNm') or it.get('venNm') or '',
                'channel': 'H몰(소상공인 기획전 물가안정 프로젝트·%s)' % nm,
                'product': it['slitmNm'], 'model_code': None,
                'buy_url': 'https://www.hmall.com/md/pda/itemPtc?slitmCd=' + c,
                'image_url': img(it),
                'rating': float(rt) if rt else None,
                'review_count': int(rv) if rv is not None else None,
                'event_url': EVENT_URL,
                'claimed_original_price': orig, 'sale_price': sale or None, 'claimed_discount_pct': pct,
                'conditions': cond,
                'sources': ['https://www.hmall.com/api/hf/dp/v1/sect-mng/plansale-ancr-paging?sectId=%d' % sid, EVENT_URL],
            })
        time.sleep(0.5)
    out = {'category': 'appliance', 'source_id': SID,
           'collected_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'items': items}
    json.dump(out, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    print(per_tab); print(len(items))

if __name__ == '__main__':
    main()
