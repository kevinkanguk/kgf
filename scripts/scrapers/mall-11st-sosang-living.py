import json, re, datetime, requests, os
SID='mall-11st-sosang-living'
ROOT='E:/090_ETC/kf'
EV='https://plan.11st.co.kr/plan/front/exhibitions/2211141'
U=EV+'/themes/1757688/products'
r=requests.post(U,headers={'Referer':EV,'X-Requested-With':'XMLHttpRequest','User-Agent':'Mozilla/5.0'},timeout=30)
raw=r.content
os.makedirs(f'{ROOT}/data/cache/html/{SID}',exist_ok=True)
open(f'{ROOT}/data/cache/html/{SID}/p1.json','wb').write(raw)
try: txt=raw.decode('utf-8')
except UnicodeDecodeError: txt=raw.decode('cp949',errors='replace')
d=json.loads(txt)
def n(s):
    s=re.sub(r'[^\d]','',str(s or ''))
    return int(s) if s else None
items=[]
for i,p in enumerate(d['themeProducts'],1):
    fin=n(p.get('finalPrice')); sell=n(p.get('sellPrice'))
    pct=float(p['discountRate']) if p.get('showDiscountRate') and p.get('discountRate') else None
    sc=p.get('satisfactionScore') if p.get('showSatisfactionScore') or p.get('satisfactionScore') else None
    rating=round(sc/20,2) if isinstance(sc,(int,float)) and sc else None
    rc=n(p.get('reviewCount'))
    img=p.get('productImage')
    items.append({'item_id':f'{SID}-{i:04d}','category':'mall','source_id':SID,'unit':None,
      'vendor':'11번가 소상공인','channel':'11번가 2026 소상공인 온라인 판로지원 기획전(리빙/생활문화)',
      'product':p['productName'],'model_code':None,'buy_url':p['productLink'],'image_url':img,
      'rating':rating,'review_count':rc,'event_url':EV,
      'claimed_original_price':sell if (sell and fin and sell>fin) else None,'sale_price':fin,
      'claimed_discount_pct':pct,'conditions':None,'sources':[U,p['productLink']]})
out={'category':'mall','source_id':SID,'collected_at':datetime.date(2026,10,31).isoformat(),'items':items}
os.makedirs(f'{ROOT}/data/raw/catalog/mall',exist_ok=True)
json.dump(out,open(f'{ROOT}/data/raw/catalog/mall/{SID}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
