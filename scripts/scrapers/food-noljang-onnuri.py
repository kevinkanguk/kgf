import requests, json, os, time, datetime
SID='food-noljang-onnuri'
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CACHE=os.path.join(ROOT,'data','cache','html',SID)
OUT=os.path.join(ROOT,'data','raw','catalog','food',SID+'.json')
H={'User-Agent':'Mozilla/5.0'}
API='https://api.noljang.co.kr/api/v1/search/market-code/slice'
CODES=['09','10','12','29','30','35','36','37','38','40','41']
os.makedirs(CACHE,exist_ok=True)
def get(code,page):
    for _ in range(3):
        try:
            r=requests.get(API,params={'marketCode':code,'page':page,'size':100},headers=H,timeout=30)
            return r.json()['result']
        except Exception: time.sleep(2)
    raise RuntimeError((code,page))
prods={}
order=[]
for code in CODES:
    page=0
    while True:
        res=get(code,page)
        json.dump(res,open(os.path.join(CACHE,f'api_{code}_{page}.json'),'w',encoding='utf-8'),ensure_ascii=False)
        for p in res['content']:
            pid=p['productId']
            if pid not in prods:
                prods[pid]=(code,p,[]); order.append(pid)
            prods[pid][2].append(p.get('marketCodeDescription') or code)
        if res.get('last') or not res['content']: break
        page+=1
items=[]
for n,pid in enumerate(order,1):
    code,p,descs=prods[pid]
    pd_=p.get('predictDiscount') or {}
    orig=p.get('productPrice')
    best=pd_.get('bestPredictPrice')
    sale=best if best is not None else (p.get('discountPrice') if p.get('discountPrice') is not None else orig)
    pct=round((orig-sale)/orig*100,1) if orig and sale is not None and orig>0 else None
    cond=[]
    if pd_.get('eventNames'): cond.append('; '.join(pd_['eventNames']))
    if pd_.get('minimumPaymentPrice'): cond.append(f"최소결제 {pd_['minimumPaymentPrice']}원")
    labels=[l['text'] for l in (p.get('paymentLabels') or [])]
    if labels: cond.append('라벨: '+','.join(labels))
    items.append({
        'item_id':f'{SID}-{n:04d}','category':'food','source_id':SID,
        'unit':None,'vendor':p.get('storeNm') or '', 'channel':f"놀장(온누리) {p.get('marketNm')} / {'·'.join(dict.fromkeys(descs))}",
        'product':p.get('productNm'),'model_code':None,
        'buy_url':f"https://mall.noljang.co.kr/market/{code}/product/{pid}",
        'image_url':p.get('productThumbnail'),'rating':None,'review_count':None,
        'event_url':f"https://mall.noljang.co.kr/market/{code}",
        'claimed_original_price':orig,'sale_price':sale,'claimed_discount_pct':pct,
        'conditions':' | '.join(cond) or None,
        'sources':[f"{API}?marketCode={code}",f"https://mall.noljang.co.kr/market/{code}/product/{pid}"],
    })
json.dump({'category':'food','source_id':SID,'collected_at':datetime.date(2026,10,31).isoformat(),'items':items},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
