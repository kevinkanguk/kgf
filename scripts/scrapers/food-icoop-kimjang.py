import requests,re,json,html,os,datetime
URL='https://www.icoop.or.kr/coopmall/goodsmall.phtm?link_code=C050'
BASE='https://www.icoop.or.kr'
CD='E:/090_ETC/kf/data/cache/html/food-icoop-kimjang/'
OUT='E:/090_ETC/kf/data/raw/catalog/food/food-icoop-kimjang.json'
SID='food-icoop-kimjang'
os.makedirs(CD,exist_ok=True);os.makedirs(os.path.dirname(OUT),exist_ok=True)
r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=30);r.encoding='utf8'
t=r.text;open(CD+'p1.html','w',encoding='utf8').write(t)
total=re.search(r'total-count">\s*총\s*<strong>(\d+)',t)
cards=t.split('<div class="product-card-wrap">')[1:]
items=[]
for c in cards:
    m=re.search(r"data-info='(\{.*?\})'",c)
    if not m:continue
    d=json.loads(m.group(1))
    name=d['name']
    mv=re.match(r'\((?:직|제)\)(.*?)\*([^*]*)\*(.*)$',name)
    vendor=mv.group(3) if mv and mv.group(3) else '자연드림'
    href=re.search(r'href="(goodsmall\.phtm\?[^"]*gc=[^"]*)"',c)
    buy=BASE+'/coopmall/'+html.unescape(href.group(1)) if href else URL
    deliv=re.search(r'color:red[^>]*>\s*([^<]+)',c)
    end=re.search(r'data-end-date="([^"]+)"',c)
    badge=re.search(r'badge-mkt">\s*([^<]+?)\s*<',c)
    cond=[]
    if end:cond.append('조합원 특가 ~'+end.group(1))
    if deliv:cond.append(deliv.group(1).strip())
    dp,sp=int(d['defaultPrice']),int(d['specialPrice'])
    items.append(dict(item_id=f'{SID}-{len(items)+1:04d}',category='food',source_id=SID,unit=d.get('unit'),
      vendor=vendor,channel='자연드림(icoop) 김장하기 기획전',product=name,model_code=d['gCode'],buy_url=buy,
      image_url=BASE+d['imgUrl'],rating=None,review_count=None,event_url=URL,
      claimed_original_price=dp,sale_price=sp,claimed_discount_pct=d.get('discountRate'),
      conditions=' / '.join(cond) or None,sources=[URL]))
out=dict(category='food',source_id=SID,collected_at=datetime.date.today().isoformat() if False else '2026-10-31',
  page_total_count=int(total.group(1)) if total else None,items=items)
json.dump(out,open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items),total.group(1) if total else None)
