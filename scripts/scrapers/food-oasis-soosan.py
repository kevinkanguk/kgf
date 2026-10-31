import re, json, os, time, html, requests
SID="food-oasis-soosan"; ROOT="E:/090_ETC/kf"
CACHE=f"{ROOT}/data/cache/html/{SID}"; OUT=f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE="https://www.oasis.co.kr"; EVENT=BASE+"/event/2026/soosanKorea_0909"
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
H={"User-Agent":"Mozilla/5.0"}
def get(u,name):
    p=f"{CACHE}/{name}"
    if os.path.exists(p): return open(p,encoding="utf-8").read()
    r=requests.get(u,headers=H,timeout=30); r.encoding="utf-8"; t=r.text
    open(p,"w",encoding="utf-8").write(t); time.sleep(0.5); return t
ev=get(EVENT,"event.html")
tabs=re.findall(r'data-category-id="(\d+)"[^>]*>(.*?)</button>',ev,re.S)
num=lambda s:int(re.sub(r'\D','',s)) if s and re.search(r'\d',s) else None
items=[];seen=set()
for cid,tname in tabs:
    tname=html.unescape(re.sub(r'<.*?>','',tname)).strip()
    for page in range(1,20):
        u=f"{BASE}/product/incList?categoryId={cid}&type=product/incProductList&rows=500&imgSize=999&sort=priority&page={page}"
        h=get(u,f"c{cid}_p{page}.html")
        blocks=re.split(r'(?=<li class="swiper-slide" data-productid)',h)[1:]
        new=0
        for b in blocks:
            m=re.match(r'<li class="swiper-slide" data-productid="(\d+)" data-productpriceid="(\d+)"',b)
            if not m: continue
            pid,ppid=m.groups()
            if pid in seen: continue
            seen.add(pid); new+=1
            g=lambda pat:(re.search(pat,b,re.S) or [None,None])[1]
            title=g(r'class="listTit">(.*?)</a>')
            title=html.unescape(re.sub(r'\s+',' ',re.sub(r'<.*?>','',title or ''))).strip()
            img=g(r'data-src="(https?://[^"]+)"') or g(r'<img[^>]*src="(https?://[^"]+)"')
            sale=num(g(r'class="price_discount"><b>([\d,]+)</b>'))
            orig=num(g(r'class="price_original"><b>([\d,]+)</b>'))
            pct=g(r'class="price_discountRate[^"]*">([\d.]+)%')
            if sale is None and orig is None: sale=num(g(r'class="price_normal[^"]*"[^>]*><b>([\d,]+)'))
            rv=re.search(r'class="info_reviewLike".*?>\s*([\d.]+)\s*\(([\d,]+)\)',b,re.S)
            cp=g(r'class="info_cpPrice">(.*?)</span>')
            unit=re.search(r'\(([^()]*\d+\s*(?:g|kg|ml|L|개|팩|마리|봉|입|미|쪽|장)[^()]*)\)\s*$',title)
            opt=g(r'class="info_option">\s*(.*?)\s*</div>')
            cond=[]
            if cp: cond.append(html.unescape(re.sub(r'\s+',' ',re.sub(r'<.*?>','',cp))).strip())
            if opt: cond.append("단위가격: "+html.unescape(re.sub(r'\s+',' ',re.sub(r'<.*?>','',opt))).strip())
            if sale is None: continue
            url=f"{BASE}/product/detail/{pid}-{ppid}"
            items.append({"item_id":"","category":"food","source_id":SID,"unit":unit.group(1) if unit else None,
              "vendor":"오아시스마켓","channel":"오아시스마켓 대한민국 수산대전 ("+tname+")","product":title,"model_code":pid,
              "buy_url":url,"image_url":img,"rating":round(float(rv.group(1)),2) if rv else None,
              "review_count":num(rv.group(2)) if rv else None,"event_url":EVENT,
              "claimed_original_price":orig,"sale_price":sale,"claimed_discount_pct":float(pct) if pct else None,
              "conditions":"; ".join(cond) or None,"sources":[url,EVENT]})
        if new==0: break
for i,it in enumerate(items,1): it["item_id"]=f"{SID}-{i:04d}"
json.dump({"category":"food","source_id":SID,"collected_at":"2026-10-31","items":items},open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(len(items),[t[0] for t in tabs])
