import requests, re, json, html, os, datetime
SID='food-nurimarket-nonghal-nh75'
ROOT='E:/090_ETC/kf'
BASE='https://nurimarket.co.kr/shop/list.php?ca_id=nh75'
CACHE=f'{ROOT}/data/cache/html/{SID}'
OUT=f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(CACHE,exist_ok=True)
H={'User-Agent':'Mozilla/5.0'}
def num(s): return int(re.sub(r'\D','',s)) if s and re.sub(r'\D','',s) else None
def clean(s): return html.unescape(re.sub(r'<[^>]+>','',s)).strip()
items=[];seen=set();page=1
while True:
    url=BASE+(f'&page={page}' if page>1 else '')
    r=requests.get(url,headers=H,timeout=30); r.encoding='utf-8'
    open(f'{CACHE}/p{page}.html','w',encoding='utf8').write(r.text)
    blocks=r.text.split('<div class="swiper-slide swiper-slide-list-nh75">')[1:]
    new=0
    for b in blocks:
        m=re.search(r'item\.php\?it_id=(\d+)',b)
        if not m or m.group(1) in seen: continue
        seen.add(m.group(1)); new+=1
        iid=m.group(1)
        imgs=re.findall(r'<img src="([^"]+/data/item/[^"]+)"',b)
        title=clean(re.search(r'class="font-pretendard-R cut2">(.*?)</a>',b,re.S).group(1))
        sale=re.search(r'main_list_price_li2[^>]*>([^<]*)<',b)
        orig=re.search(r'<strike>([^<]*)</strike>',b)
        pct=re.search(r'main_list_price_li1[^>]*>([\d.]+)%',b)
        coup=re.search(r'font-size:13px;">([^<]*)</span><span[^>]*></span><span[^>]*>([\d.]+)%</span><span[^>]*></span><span[^>]*>([^<]*)</span><span[^>]*></span><span[^>]*>([\d,]+)</span>',b)
        star=re.search(r's_star(\d+(?:_\d+)?)\.png',b)
        rc=re.search(r'main_list_star_cnt[^>]*>\(([\d,]+)\)',b)
        rating=None
        if star:
            rating=float(star.group(1).replace('_','.'))
        cond=None
        if coup:
            cond=f'{coup.group(1)} {coup.group(2)}% {coup.group(3)} {coup.group(4)}원'
        so=num(orig.group(1)) if orig else None
        sp=num(sale.group(1)) if sale else None
        d=float(pct.group(1)) if pct else None
        uni=re.search(r'(\d+(?:\.\d+)?\s*(?:kg|Kg|KG|g|ml|L|개입|개|봉|박스|팩|입|포))',title)
        items.append({
          'item_id':f'{SID}-{len(items)+1:04d}','category':'food','source_id':SID,
          'unit':uni.group(1) if uni else None,'vendor':'누리마켓(농협)' ,'channel':'누리마켓(농할마켓)',
          'product':title,'model_code':iid,'buy_url':f'https://nurimarket.co.kr/shop/item.php?it_id={iid}',
          'image_url':imgs[-1] if imgs else None,'rating':rating,'review_count':num(rc.group(1)) if rc else None,
          'event_url':BASE,'claimed_original_price':so,'sale_price':sp,'claimed_discount_pct':d,
          'conditions':cond,'sources':[BASE,f'https://nurimarket.co.kr/shop/item.php?it_id={iid}']})
    if new==0 or page>30: break
    page+=1
json.dump({'category':'food','source_id':SID,'collected_at':datetime.datetime.now().isoformat(timespec='seconds'),'items':items},open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items),page)
