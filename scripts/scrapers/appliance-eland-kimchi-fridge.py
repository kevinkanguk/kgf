import re, json, os, html, requests, datetime
SID='appliance-eland-kimchi-fridge'
ROOT='E:/090_ETC/kf/'
CACHE=ROOT+f'data/cache/html/{SID}/'
OUT=ROOT+f'data/raw/catalog/appliance/{SID}.json'
EV='https://www.etlandmall.co.kr/pc/event/planProductList.do?PLN_MST_IDX=12192'
H={'User-Agent':'Mozilla/5.0','Referer':EV}
os.makedirs(CACHE,exist_ok=True)
def get(url,fn,post=None):
    p=CACHE+fn
    if os.path.exists(p): return open(p,encoding='utf-8').read()
    r=requests.post(url,headers=H,data=post) if post else requests.get(url,headers=H)
    r.encoding='utf-8'; open(p,'w',encoding='utf-8').write(r.text); return r.text
main=get(EV,'main.html')
pages=[main]
for g,c in re.findall(r'planGrpIdx="(\d+)" planGrpCol="(\d+)"',main):
    pages.append(get('https://www.etlandmall.co.kr/pc/event/planProductDetailListAjax.do',f'grp{g}.html',
      {"PLN_MST_IDX":"12192","PLN_GRP_COL":c,"PLN_GRP_IDX":g,"prePlan":"","PLN_MST_SPECIAL_YN":"Y","PLN_MST_PRD_DPL_YN":"Y","PLN_TIME_SALE":"N","PLN_POINT_SALE_YN":"N","chlCode":""}))
cards={}
def tx(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s))).strip()
for pg in pages:
    for blk in re.findall(r'<a class="components_product_list".*?</a>',pg,re.S):
        code=re.search(r'prdMstCd=(S\d+)',blk).group(1)
        if code in cards: continue
        name=re.search(r'components_product_name">(.*?)</p>',blk,re.S)
        pct=re.search(r'priceGroup_sale">\s*([\d.]+)%',blk)
        pr=re.search(r'priceGroup_price">\s*([\d,]+)',blk)
        img=re.search(r'<img\s+src="([^"]+)"\s+alt=""\s+class="product_thum"',blk)
        st=re.search(r'</span>\s*([\d.]+)</span>\s*<span class="components_product_reivewGroup_total">\(([\d,]+)\)',blk)
        ben=[tx(x) for x in re.findall(r'<li class="components_product_benefit_(?:coupon|point|gifts)">(.*?)</li>',blk,re.S)]
        cards[code]=dict(name=tx(name.group(1)),pct=float(pct.group(1)) if pct else None,
          price=int(pr.group(1).replace(',','')) if pr else None,
          img=('https://www.etlandmall.co.kr'+img.group(1)) if img else None,
          rating=float(st.group(1)) if st else None,rc=int(st.group(2).replace(',','')) if st else None,ben=ben)
items=[]
for i,(code,c) in enumerate(cards.items(),1):
    url=f'https://www.etlandmall.co.kr/pc/product/product.do?prdMstCd={code}'
    d=get(url,f'{code}.html')
    org=re.search(r'<span class="price_org"><em>([\d,]+)</em>',d)
    brand=re.search(r'"brand":\s*\{\s*"@type":\s*"Brand",\s*"name":\s*"([^"]*)"',d)
    mpn=re.search(r'"mpn":\s*"([^"]*)"',d)
    sale=re.search(r'<span class="price_sale"><em>([\d,]+)</em>',d)
    ul=re.search(r'(\d+(?:\.\d+)?\s*L)\b',c['name'])
    items.append(dict(item_id=f'{SID}-{i:04d}',category='appliance',source_id=SID,
      unit=ul.group(1).replace(' ','') if ul else None,
      vendor=html.unescape(brand.group(1)) if brand and brand.group(1) else None,
      channel='이랜드몰 김치냉장고 특가 ON',product=c['name'],
      model_code=(mpn.group(1) or None) if mpn else None,buy_url=url,image_url=c['img'],
      rating=c['rating'],review_count=c['rc'],event_url=EV,
      claimed_original_price=int(org.group(1).replace(',','')) if org else None,
      sale_price=c['price'] if c['price'] else (int(sale.group(1).replace(',','')) if sale else None),
      claimed_discount_pct=c['pct'],conditions=' / '.join(c['ben']) or None,
      sources=[EV,url]))
for it in items:
    if not it['vendor']: it['vendor']=it['product'].split()[0]
json.dump(dict(category='appliance',source_id=SID,collected_at=datetime.date.today().isoformat(),items=items),open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
