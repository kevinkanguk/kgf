import requests,json,re,html,os,datetime
ROOT='E:/090_ETC/kf'
SID='food-mggoon-soosan'
LIST_URL='https://mggoon.co.kr/Goods/List?cno=38&pageType=DEFAULT'
CACHE=f'{ROOT}/data/cache/html/{SID}'
OUT=f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(CACHE,exist_ok=True);os.makedirs(os.path.dirname(OUT),exist_ok=True)
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0'
s.get(LIST_URL)
def num(x):
    x=re.sub(r'[^\d]','',x or '');return int(x) if x else None
items=[];seen=set();page=1;total=None;stars=set()
while True:
    p=dict(tagno=0,cno=38,isview='Y',istime=False,islike=False,sval='',sortby=0,usortby=4,DateDuration=7,eventidx=0,gpg_idx=0,pageType='DEFAULT',listType='DEFAULT',listLayoutType='3_DIV1',bannerUseYN='Y',bannerIdx=7,bannerType='SLIDE',recommendUseYN='N',recommendIdxs='',userLayoutSettingidx='0',recommendUserLayoutSettingidx='0',curOS='AOS',sc_idx=0,isgift=False,page=page,rows=24)
    r=s.post('https://mggoon.co.kr/Goods/GetGoodsListNew',json={'param':p,'list_template_name':'/Views/Templates/LIST/3_DIV.cshtml','igm_idx':'12'},headers={'X-Requested-With':'XMLHttpRequest'})
    j=r.json();open(f'{CACHE}/api_p{page}.json','w',encoding='utf8').write(r.text)
    if total is None: total=j.get('dataTotalCount')
    d=j['data'];h=d['data'] if d else ''
    blocks=h.split('data-mgcode="')[1:]
    new=0
    for b in blocks:
        code=b.split('"')[0]
        if code in seen: continue
        seen.add(code);new+=1
        m=re.search(r'data-src="([^"]+)"',b);img=m.group(1) if m else None
        m=re.search(r'<h4 class="prod-title[^>]*>(.*?)</h4>',b,re.S);name=html.unescape(m.group(1).strip()) if m else None
        m=re.search(r'org-price.*?</span>(.*?)</p>',b,re.S);org=num(re.sub(r'<[^>]+>','',m.group(1))) if m else None
        m=re.search(r'<p class="price[ "].*?>\s*([\d,]+)원',b,re.S);sale=num(m.group(1)) if m else None
        m=re.search(r'class="dc-rate[^>]*>.*?</span>\s*([\d.]+)%',b,re.S);pct=float(m.group(1)) if m else None
        m=re.search(r'class="avgstar".*?</p>',b,re.S);rating=None;rc=None
        if m:
            seg=m.group(0)
            full=len(re.findall(r'class="fa fa-star"',seg));stars.add(tuple(sorted(set(re.findall(r'class="(fa[^"]*star[^"]*)"',seg)))))
            m2=re.search(r'<span[^>]*>\s*([\d,]+)\s*</span>',seg);rc=num(m2.group(1)) if m2 else None
            rating=float(full) if full else None
        if pct is None and org and sale: pct=round((org-sale)/org*100,1)
        items.append(dict(item_id=f'{SID}-{len(items)+1:04d}',category='food',source_id=SID,unit=None,vendor='맛꾼',channel='맛꾼(mggoon) 수산',product=name,model_code=code,buy_url=f'https://mggoon.co.kr/Goods/Detail/{code}',image_url=img,rating=rating,review_count=rc,event_url=LIST_URL,claimed_original_price=org,sale_price=sale,claimed_discount_pct=pct,conditions=None,sources=[LIST_URL]))
    print(page,len(blocks),new,total)
    if d is None or d.get('cnt',0)<24 or new==0 or page>200: break
    page+=1
print('stars variants',stars)
json.dump(dict(category='food',source_id=SID,collected_at='2026-10-31',items=items),open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items))
