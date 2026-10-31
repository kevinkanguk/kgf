import requests, json, datetime, os
SID='mall-11st-sosang-processed'
EV='https://plan.11st.co.kr/plan/front/exhibitions/2211141'
U=EV+'/themes/1756467/products'
R='E:/090_ETC/kf/'
r=requests.post(U,headers={'Referer':EV,'X-Requested-With':'XMLHttpRequest','User-Agent':'Mozilla/5.0'},timeout=30)
r.encoding='utf-8'
os.makedirs(R+'data/cache/html/'+SID,exist_ok=True)
open(R+'data/cache/html/'+SID+'/p0.json','w',encoding='utf-8').write(r.text)
P=r.json()['themeProducts']
n=lambda s:int(s.replace(',','')) if s else None
items=[]
for i,p in enumerate(P,1):
    fin=n(p['finalPrice']); sell=n(p['sellPrice'])
    pct=float(p['discountRate']) if p['showDiscountRate'] else None
    sc=p.get('satisfactionScore')
    items.append({"item_id":f"{SID}-{i:04d}","category":"mall","source_id":SID,"unit":None,
     "vendor":"11번가 소상공인","channel":"11번가 소상공인 가공식품","product":p['productName'],"model_code":str(p['productNo']),
     "buy_url":p['productLink'],"image_url":p['productImage'],
     "rating":round(sc/20,2) if sc else None,"review_count":n(p['reviewCount']) if p['reviewCount'] else None,
     "event_url":EV,"claimed_original_price":sell,"sale_price":fin,"claimed_discount_pct":pct,"conditions":None,
     "sources":[U,p['productLink']]})
out={"category":"mall","source_id":SID,"collected_at":"2026-10-31","items":items}
os.makedirs(R+'data/raw/catalog/mall',exist_ok=True)
json.dump(out,open(R+'data/raw/catalog/mall/'+SID+'.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
