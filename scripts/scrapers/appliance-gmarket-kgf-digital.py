import re, json, html, datetime, os, requests
SID='appliance-gmarket-kgf-digital'; CAT='appliance'
URL='https://rpp.gmarket.co.kr/?exhib=280311'
ROOT='E:/090_ETC/kf'
cache=f'{ROOT}/data/cache/html/{SID}/page.html'
if os.path.exists(cache): t=open(cache,encoding='utf8').read()
else:
    t=requests.get(URL,headers={'User-Agent':'Mozilla/5.0 Chrome/124','Accept-Language':'ko-KR,ko'},timeout=30).text
    os.makedirs(os.path.dirname(cache),exist_ok=True); open(cache,'w',encoding='utf8').write(t)
i=t.find('id="comp_27870410"'); e=t.find('class="module ',i+100)
s=t[i:e if e>0 else None]
items=[]; seen=set()
for p in re.split(r'<li class="elements_item',s)[1:]:
    m=re.search(r'data-goods-no="(\d+)"',p)
    if not m or m.group(1) in seen: continue
    g=m.group(1); seen.add(g)
    iv=re.search(r'data-item-value="([^"]*)"',p)
    d=json.loads(html.unescape(iv.group(1))) if iv else {}
    name=d.get('itemName') or html.unescape(re.search(r'class="title[^>]*>([^<]+)<',p).group(1)).strip()
    img=d.get('imageUrl') or ''
    if img.startswith('//'): img='https:'+img
    def num(x): return int(x.replace(',','')) if x else None
    orig=re.search(r'<del class="num">([\d,]+)',p)
    disc=re.search(r'<li class="discount">\s*([\d.]+)',p)
    sell=re.search(r'class="selling">\s*<strong>([\d,]+)',p)
    dp=re.search(r'data-discount-price="(\d+)"',p)
    o=num(orig.group(1)) if orig else None; sp=num(sell.group(1)) if sell else (int(dp.group(1)) if dp else None)
    prom=int(dp.group(1)) if dp else None
    cond=None
    if prom and sp and prom!=sp: cond=f'쿠폰 적용가(쿠폰 적용 전 판매가 {prom:,}원)'
    items.append(dict(item_id=f'{SID}-{len(items)+1:04d}',category=CAT,source_id=SID,unit=None,
      vendor=d.get('brandName') or '지마켓 판매자',channel='지마켓 코리아그랜드세일페스타',product=name,model_code=None,
      buy_url=f'https://item.gmarket.co.kr/Item?goodscode={g}',image_url=img or None,rating=None,review_count=None,
      event_url=URL,claimed_original_price=o,sale_price=sp,claimed_discount_pct=float(disc.group(1)) if disc else None,
      conditions=cond,sources=[URL]))
out=dict(category=CAT,source_id=SID,collected_at=datetime.date(2026,10,31).isoformat(),items=items)
os.makedirs(f'{ROOT}/data/raw/catalog/{CAT}',exist_ok=True)
json.dump(out,open(f'{ROOT}/data/raw/catalog/{CAT}/{SID}.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items))
