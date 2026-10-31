import urllib.request, json, os, time, datetime
SID='mall-hmall-sosang-reco-3'
ROOT='E:/090_ETC/kf'
CACHE=f'{ROOT}/data/cache/html/{SID}'
OUT=f'{ROOT}/data/raw/catalog/mall/{SID}.json'
BASE='https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc&page='
LO,HI=601,900
os.makedirs(CACHE,exist_ok=True)
def get(p):
    f=f'{CACHE}/page_{p:03d}.json'
    if os.path.exists(f):
        return json.load(open(f,encoding='utf8'))
    for _ in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(BASE+str(p),headers={'Referer':'https://www.hmall.com/','User-Agent':'Mozilla/5.0'}),timeout=30)
            t=r.read().decode('utf8'); j=json.loads(t)
            open(f,'w',encoding='utf8').write(t); return j
        except Exception as e:
            time.sleep(2)
    raise RuntimeError(p)
allit=[]; p=1
while True:
    l=get(p)['respData'].get('itemList') or []
    if not l: break
    allit+=l; p+=1
    if p>200: break
reco=[i for i in allit if '추천상품' in (i.get('sectNm') or '')]
print('pages',p-1,'all',len(allit),'reco',len(reco))
sel=reco[LO-1:HI]
items=[]
for n,i in enumerate(sel,1):
    sp=i.get('sellPrc') or None; bb=i.get('bbprc') or None
    pct=round((sp-bb)/sp*100,1) if sp and bb and bb<sp else None
    cond=None
    if i.get('copnDcAmt'): cond=f"쿠폰할인 {i['copnDcAmt']}원({i.get('copnDcRate')}%) 반영 최종가(bbprc)"
    items.append({
      'item_id':f'{SID}-{n:04d}','category':'mall','source_id':SID,'unit':None,
      'vendor':i.get('brndNm') or i.get('venNm') or '', 'channel':'현대Hmall 소상공인 기획전(추천상품)',
      'product':i.get('slitmNm'),'model_code':i.get('slitmCd'),
      'buy_url':f"https://www.hmall.com/p/pda/itemPtc.do?slitmCd={i['slitmCd']}",
      'event_url':'https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083',
      'claimed_original_price':sp,'sale_price':bb or sp,'claimed_discount_pct':pct,
      'conditions':cond,'sources':[BASE+'1']})
os.makedirs(os.path.dirname(OUT),exist_ok=True)
json.dump({'category':'mall','source_id':SID,'collected_at':'2026-10-31','items':items},open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print('saved',len(items))
