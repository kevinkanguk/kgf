import re, json, html, time, os, requests
SID='food-nurimarket-hanwoo'
BASE='https://nurimarket.co.kr/shop/list.php?ca_id=5010'
ROOT='E:/090_ETC/kf'
CACHE=f'{ROOT}/data/cache/html/{SID}'
OUT=f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(CACHE,exist_ok=True)
H={'User-Agent':'Mozilla/5.0'}
def get(p):
    f=f'{CACHE}/p{p}.html'
    if os.path.exists(f):
        return open(f,'rb').read().decode('utf-8','replace')
    r=requests.get(BASE+(f'&page={p}' if p>1 else ''),headers=H,timeout=30)
    open(f,'wb').write(r.content); time.sleep(0.5)
    return r.content.decode('utf-8','replace')
def num(s):
    s=re.sub(r'[^\d]','',s or ''); return int(s) if s else None
def parse(t):
    out=[]
    for blk in t.split('<div class="swiper-slide swiper-slide-list-5010">')[1:]:
        m=re.search(r'it_id=(\w+)',blk)
        if not m: continue
        it=m.group(1)
        img=re.search(r'<img src="([^"]*/data/item/[^"]+)"[^>]*alt="([^"]*)"',blk)
        tit=re.search(r'class="font-pretendard-R cut2">(.*?)</a>',blk,re.S)
        name=html.unescape(tit.group(1)).strip() if tit else (html.unescape(img.group(2)) if img else None)
        pct=re.search(r'main_list_price_li1[^>]*>([\d.]+)%',blk)
        sale=re.search(r'main_list_price_li2[^>]*>([^<]*)<',blk)
        orig=re.search(r'<strike>([^<]*)</strike>',blk)
        cp=re.search(r'쿠폰.*?(\d+)%.*?적용가.*?>([\d,]+)</span>',blk,re.S)
        star=re.search(r's_star(\d+)\.png',blk)
        cnt=re.search(r'main_list_star_cnt[^>]*>\(([\d,]+)\)',blk)
        ico=re.findall(r'list_ico_\d[^>]*>([^<]+)<',blk)
        cond=[]
        if cp: cond.append(f'쿠폰 {cp.group(1)}% 적용가 {cp.group(2)}원')
        if ico: cond.append('표시: '+', '.join(i.strip() for i in ico))
        out.append(dict(it=it,name=name,img=img.group(1) if img else None,
            pct=float(pct.group(1)) if pct else None,sale=num(sale.group(1)) if sale else None,
            orig=num(orig.group(1)) if orig else None,star=int(star.group(1)) if star else None,
            cnt=num(cnt.group(1)) if cnt else None,cond='; '.join(cond) or None))
    return out
t=get(1)
pages=[int(x) for x in re.findall(r'[?&;]page=(\d+)',t)]
maxp=max(pages) if pages else 1
rows={};p=1
while p<=maxp:
    t=get(p) if p>1 else t
    for r in parse(t):
        rows.setdefault(r['it'],r)
    ps=[int(x) for x in re.findall(r'[?&;]page=(\d+)',t)]
    if ps: maxp=max(maxp,max(ps))
    p+=1
items=[]
for n,r in enumerate(rows.values(),1):
    url=f"https://nurimarket.co.kr/shop/item.php?it_id={r['it']}"
    items.append(dict(item_id=f'{SID}-{n:04d}',category='food',source_id=SID,unit=None,vendor='누리마켓',
        channel='누리마켓(농할마켓)',product=r['name'],model_code=r['it'],buy_url=url,image_url=r['img'],
        rating=float(r['star']) if r['star'] is not None else None,review_count=r['cnt'],
        event_url=BASE,claimed_original_price=r['orig'],sale_price=r['sale'],claimed_discount_pct=r['pct'],
        conditions=r['cond'],sources=[url,BASE]))
json.dump(dict(category='food',source_id=SID,collected_at='2026-10-31',items=items),open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items),maxp)
