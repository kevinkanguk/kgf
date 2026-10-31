import requests,json,os,sys,collections
H={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'}
B='https://mfront.homeplus.co.kr/'
CD='E:/090_ETC/kf/data/cache/html/food-homeplus/'
OUT='E:/090_ETC/kf/data/raw/catalog/food/food-homeplus.json'
DT='2026-10-31'
def g(p,**q):
    r=requests.get(B+p,params=q,headers=H,timeout=30);r.raise_for_status();return r.json()
def main():
    os.makedirs(CD,exist_ok=True)
    themes=g('homeTheme.json',dispDt=DT,page=1,perPage=100)['data']
    json.dump(themes,open(CD+'themes.json','w',encoding='utf8'),ensure_ascii=False,indent=1)
    raw=[]
    for t in themes:
        pg=1
        while True:
            d=g('homeThemeItem.json',dispDt=DT,page=pg,perPage=20,themeId=t['themeId'])['data']
            json.dump(d,open(CD+f"theme{t['themeId']}_p{pg}.json",'w',encoding='utf8'),ensure_ascii=False)
            if not d:break
            for x in d:x['_theme']=t
            raw+=d
            if len(d)<20:break
            pg+=1
    seen=set();items=[]
    for x in raw:
        if x.get('themeItemType')!='ITEM' or x['itemNo'] in seen or x.get('rcateNm') in ('제지/위생/뷰티','유아동/완구'):continue  # 식품 외 제외
        seen.add(x['itemNo'])
        n=len(items)+1;nm=x['itemNm']
        ev=x.get('eventInfo') or {};fl=[f['label'] for f in x.get('eventFlagList') or []]
        cond=' / '.join(filter(None,[ (ev.get('eventBtnText') or ''), ' '.join(fl), '테마:'+x['_theme']['themeNm'],
            ('행사종료 '+ev['eventEndDt'][:10]) if ev.get('eventEndDt') else '']))
        img=f"https://image.homeplus.kr/it/{x['itemNo']}s0320?lastmod={x['imgChgDt']}"
        items.append({'item_id':f'food-homeplus-{n:04d}','category':'food','source_id':'food-homeplus',
          'unit':(f"{x['totalUnitQty']:g}{x['unitMeasure']}" if x.get('totalUnitQty') and x.get('unitMeasure') else None),
          'vendor':nm.split()[0],'channel':'홈플러스','product':nm,'model_code':x['itemNo'],
          'buy_url':f"https://front.homeplus.co.kr/item?itemNo={x['itemNo']}",
          'image_url':img,'rating':x.get('grade'),'review_count':x.get('reviewCnt'),
          'event_url':'https://front.homeplus.co.kr/','claimed_original_price':(x['salePrice'] if x.get('dcPrice') else None),
          'sale_price':x.get('dcPrice') or x.get('salePrice'),'claimed_discount_pct':(float(x['dcRate']) if x.get('dcPrice') and x.get('dcRate') else None),'category_path':x.get('rcateNm'),'conditions':cond,
          'sources':[f"{B}homeThemeItem.json?dispDt={DT}&themeId={x['_theme']['themeId']}"],
          'verify_status':None,'verify_note':None,'confidence':None})
    return raw,items
def save(items):
    for i in items:i.pop('category_path',None)
    json.dump({'category':'food','source_id':'food-homeplus','collected_at':'2026-10-31','items':items},open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
if __name__=='__main__':
    raw,items=main()
    print(len(raw),len(items));print(collections.Counter(i['category_path'] for i in items))
    if 'save' in sys.argv:save(items)
