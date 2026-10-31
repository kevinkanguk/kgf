import json, os, datetime, requests, time
SID='appliance-ssg-kgf'; CAT='appliance'; ROOT='E:/090_ETC/kf'
DID='6000465146'; URL=f'https://www.ssg.com/plan/planShop.ssg?dispCmptId={DID}'
API='https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain'
H={'User-Agent':'Mozilla/5.0 Chrome/124','Origin':'https://www.ssg.com','Referer':'https://www.ssg.com/'}
cdir=f'{ROOT}/data/cache/html/{SID}'; os.makedirs(cdir,exist_ok=True)
THEMES=[('7000886050',"MD's Pick"),('7000886052','건강식품/꿀'),('7000886054','축산/수산/건식품'),('7000886063','채소/과일/양곡'),
        ('7000886055','음료/커피차/유제품'),('7000949389','과자/베이커리/떡'),('7000886051','간편식/김치/반찬'),('7000886053','조미료/면/통조림')]
def call(th,p):
    f=f'{cdir}/theme_{th}_p{p}.json'
    if os.path.exists(f): return json.load(open(f,encoding='utf8'))
    body={'common':{'aplVer':'','osCd':'','ts':'20261031120000','mobilAppNo':'99','dispDvicDivCd':'10','viewSiteNo':'6005'},
          'params':{'dispCmptId':DID,'inflowSiteNo':'6005','themeId':th,'page':p,'pageSize':30}}
    d=requests.post(API,json=body,headers=H,timeout=30).json()
    json.dump(d,open(f,'w',encoding='utf8'),ensure_ascii=False); time.sleep(0.3); return d
def toint(x):
    try: return int(str(x).replace(',','')) if str(x).strip() not in('','null','0') else None
    except: return None
items=[]; seen=set(); issues=[]
for th,name in THEMES:
    p=1
    while True:
        d=call(th,p).get('data') or {}
        for i in d.get('itemList',[]):
            iid=i['itemId']
            if iid in seen: continue
            seen.add(iid)
            raw=i.get('priceInfo',{}).get('raw',{}); summ=i.get('priceInfo',{}).get('summary',{})
            sale=toint(i.get('displayPrc')); orig=toint(i.get('strikeOutPrc'))
            rate=toint(raw.get('discountRate'))
            conds=[]; pct=None
            if orig and sale: pct=float(rate) if rate else round((orig-sale)/orig*100,1)
            if summ.get('suffixTxt')=='외' or summ.get('priceTxt','').endswith('~'): conds.append('옵션/묶음 상품: 표시가는 최저가 기준, 옵션별 가격 상이')
            if summ.get('discountTxt') and not orig: conds.append(f"목록 표기 할인율 {summ['discountTxt']}(최대치, 정가 미표기)")
            if summ.get('cpnTxt'): conds.append(summ['cpnTxt'])
            if i.get('soldOutYn')=='Y' or i.get('abstExpsrTypeNm')=='매진': conds.append('목록상 매진 표시')
            rc=toint(i.get('recomRegCnt')); rt=None
            try: rt=float(i['recompPoint']) if i.get('recompPoint') else None
            except: pass
            img=i.get('itemImgUrl') or None
            items.append(dict(item_id=f'{SID}-{len(items)+1:04d}',category=CAT,source_id=SID,
                unit=i.get('sellCapaUnitNmWithUnitCapa') or None,vendor=i.get('brandNm') or 'SSG 판매자',
                channel='SSG 소상공인 브랜드대전',product=i['itemNm'],model_code=None,buy_url=i['itemLnkd'],
                image_url=img,rating=rt,review_count=rc if rt is not None else None,event_url=URL,
                claimed_original_price=orig,sale_price=sale,claimed_discount_pct=pct,
                conditions='; '.join(conds) or None,sources=[URL,API+f' (theme {name})']))
        if not d.get('hasNext') or not d.get('itemList'): break
        p+=1
out=dict(category=CAT,source_id=SID,collected_at=datetime.date(2026,10,31).isoformat(),items=items)
os.makedirs(f'{ROOT}/data/raw/catalog/{CAT}',exist_ok=True)
json.dump(out,open(f'{ROOT}/data/raw/catalog/{CAT}/{SID}.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items))
