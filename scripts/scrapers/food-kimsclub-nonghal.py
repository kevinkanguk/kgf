import re, json, os, sys, html, time, requests
BASE='https://kimsclub.elandmall.co.kr'
H={'User-Agent':'Mozilla/5.0'}
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CACHE=os.path.join(ROOT,'data','cache','html','food-kimsclub-nonghal')
OUT=os.path.join(ROOT,'data','raw','catalog','food','food-kimsclub-nonghal.json')
os.makedirs(CACHE,exist_ok=True)
def get(url,name):
    p=os.path.join(CACHE,name)
    if os.path.exists(p): return open(p,encoding='utf-8').read()
    r=requests.get(url,headers=H,timeout=30); r.encoding='utf-8'
    open(p,'w',encoding='utf-8').write(r.text); time.sleep(0.3); return r.text
def num(s): 
    s=re.sub(r'[^\d]','',s or ''); return int(s) if s else None
def parse(t,cat):
    out=[]
    for blk in re.split(r'<li>\s*<div class="ui-item ',t)[1:]:
        m=re.search(r'data-item-no="(\d+)"',blk)
        if not m: continue
        no=m.group(1)
        lv=re.search(r'lowerVendNo=(\w+)',blk)
        name=re.search(r'<p class="prd">\s*(.*?)\s*</p>',blk,re.S)
        brand=re.search(r'<strong class="brand">(.*?)</strong>',blk)
        img=re.search(r'data-src="(https://item[^"]+?)(?:\?[^"]*)?"',blk)
        orig=re.search(r'<span class="original">.*?<em>([\d,]+)</em>',blk,re.S)
        price=re.search(r'<span class="price">.*?<em>([\d,]+)</em>',blk,re.S)
        per=re.search(r'<span class="per">.*?<em>([\d.]+)</em>',blk,re.S)
        star=re.search(r'class="star"><span style="width:([\d.]+)%',blk)
        rv=re.search(r'class="review">.*?\((\d+)\)',blk,re.S)
        out.append(dict(no=no,lv=lv.group(1) if lv else None,
          name=html.unescape(name.group(1)) if name else None,
          brand=html.unescape(brand.group(1)) if brand else None,
          img=html.unescape(img.group(1)) if img else None,
          orig=num(orig.group(1)) if orig else None,price=num(price.group(1)) if price else None,
          per=float(per.group(1)) if per else None,
          rating=round(float(star.group(1))/20,1) if star else None,
          rv=int(rv.group(1)) if rv else None,cat=cat))
    return out
def main():
    home=get(BASE+'/','home.html')
    cats=list(dict.fromkeys(re.findall(r'/c/ctg\?dispCategoryNo=(\d+)',home)))
    seen=set(); i=0
    while i<len(cats):
        c=cats[i]; i+=1
        t=get(f'{BASE}/c/ctg?dispCategoryNo={c}',f'ctg_{c}.html')
        for x in re.findall(r'/c/ctg\?dispCategoryNo=(\d+)',t)+re.findall(r'<option value="(\d{10})"',t):
            if x not in cats: cats.append(x)
        tot=re.search(r'total:\s*(\d+),\s*size:\s*(\d+)',t)
        if tot and int(tot.group(1))>int(tot.group(2)):
            T,S=int(tot.group(1)),int(tot.group(2))
            for pg in range(2,(T+S-1)//S+1):
                get(f'{BASE}/c/ctg?dispCategoryNo={c}&page={pg}&size={S}&from={(pg-1)*S}',f'ctg_{c}_p{pg}.html')
    print('categories',len(cats))
    items={}
    for c in cats:
        t=open(os.path.join(CACHE,f'ctg_{c}.html'),encoding='utf-8').read()
        tot=re.search(r'data-total="(\d+)"',t)
        its=parse(t,c)
        for pf in sorted(f for f in os.listdir(CACHE) if f.startswith(f'ctg_{c}_p')):
            its+=parse(open(os.path.join(CACHE,pf),encoding='utf-8').read(),c)
        u=set(x['no'] for x in its)
        print(c,'total',tot.group(1) if tot else None,'rendered',len(u))
        for x in its: items.setdefault(x['no'],x)
    res=[]
    for n,x in enumerate(items.values(),1):
        pct=x['per']
        if pct is None and x['orig'] and x['price'] and x['orig']>x['price']: pct=round((1-x['price']/x['orig'])*100,1)
        buy=f"{BASE}/i/item?itemNo={x['no']}"+(f"&lowerVendNo={x['lv']}" if x['lv'] else '')
        res.append(dict(item_id=f'food-kimsclub-nonghal-{n:04d}',category='food',source_id='food-kimsclub-nonghal',
          unit=None,vendor=x['brand'] or '킴스클럽',channel='킴스클럽(이랜드몰)',product=x['name'],model_code=x['no'],
          buy_url=buy,image_url=x['img'],rating=x['rating'],review_count=x['rv'],event_url=f"{BASE}/c/ctg?dispCategoryNo={x['cat']}",
          claimed_original_price=x['orig'],sale_price=x['price'],claimed_discount_pct=pct,conditions=None,
          sources=[buy]))
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    json.dump(dict(category='food',source_id='food-kimsclub-nonghal',collected_at=time.strftime('%Y-%m-%d'),items=res),open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print('items',len(res))
main()
