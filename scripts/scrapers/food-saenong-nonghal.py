import re, json, os, time, html, urllib.parse, requests
SID="food-saenong-nonghal"; ROOT="E:/090_ETC/kf"
CACHE=f"{ROOT}/data/cache/html/{SID}"; OUT=f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE="https://www.saenong.com"; EVENT=BASE+"/benefit/nonghwal.html"; CATE=508
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
S=requests.Session(); S.headers["User-Agent"]="Mozilla/5.0"
def fetch(fn,url,params=None):
    f=f"{CACHE}/{fn}"
    if os.path.exists(f): return open(f,encoding="utf8").read()
    for _ in range(3):
        r=S.get(url,params=params,timeout=30)
        if r.ok: break
        time.sleep(2)
    r.encoding="utf-8"; open(f,"w",encoding="utf8").write(r.text); time.sleep(0.4); return r.text
num=lambda s:int(re.sub(r"\D","",s)) if s and re.sub(r"\D","",s) else None
def li(blk,rel):
    m=re.search(r'<li rel="%s"[^>]*>(.*?)</li>'%rel,blk,re.S)
    return html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip() if m else None
def parse(t):
    out=[]
    for blk in re.split(r'(?=<li data-product-no=")',t)[1:]:
        pn=re.match(r'<li data-product-no="(\d+)"',blk).group(1)
        blk=blk.split('</li>\n</ul>')[0] if False else blk
        a=re.search(r'<strong class="name[^"]*"><a href="([^"]+)"[^>]*>(.*?)</a>',blk,re.S)
        name=html.unescape(re.sub(r"<[^>]+>","",a.group(2))).strip()
        img=re.search(r'<img[^>]+src="([^"]+)"[^>]*id="eListPrdImage',blk)
        out.append(dict(pn=pn,href=a.group(1),name=name,img=img.group(1) if img else None,
          orig=num(li(blk,"소비자가")),price=num(li(blk,"판매가")),best=num(li(blk,"최적할인가")),
          code=li(blk,"자체상품코드"),sup=li(blk,"공급사"),soldout='soldout_overlay displaynone' not in blk))
    return out
items={}; pg=1; total=None
while True:
    t=fetch(f"p{pg}.html",BASE+"/product/list.html",{"cate_no":CATE,"page":pg})
    if total is None: total=num(re.search(r'prdCount">[^\d]*(\d+)',t).group(1))
    its=parse(t); new=0
    for i in its:
        if i["pn"] not in items: items[i["pn"]]=i; new+=1
    if not its or not new or len(items)>=total: break
    pg+=1
out=[]
for n,i in enumerate(items.values(),1):
    d=fetch(f"d{i['pn']}.html",BASE+"/product/detail.html",{"product_no":i["pn"],"cate_no":CATE,"display_group":1})
    r=re.search(r'"ratingValue":([\d.]+),"reviewCount":(\d+)',d)
    rating=float(r.group(1)) if r else None; rc=int(r.group(2)) if r else None
    orig,price,best=i["orig"],i["price"],i["best"]
    claimed=orig if orig and price and orig>price else None
    ref=claimed or price
    sale=best or price
    pct=round((1-sale/ref)*100,1) if ref and sale and sale<ref else None
    cond=[]
    if best and best!=price: cond.append(f"판매가 {price:,}원에서 농할 20% 쿠폰 등 적용 시 최적할인가 {best:,}원")
    if i["soldout"]: cond.append("일시품절")
    img=i["img"]; img=("https:"+img) if img and img.startswith("//") else img
    out.append(dict(item_id=f"{SID}-{n:04d}",category="food",source_id=SID,unit=None,
      vendor=i["sup"] or "새농",channel="새농(친환경몰) 농할대전",product=i["name"],model_code=i["code"],
      buy_url=BASE+urllib.parse.quote(i["href"],safe="/%"),image_url=img,rating=rating,review_count=rc,event_url=EVENT,
      claimed_original_price=claimed,sale_price=sale,claimed_discount_pct=pct,conditions="; ".join(cond) or None,
      sources=[f"{BASE}/product/list.html?cate_no={CATE}",EVENT]))
json.dump(dict(category="food",source_id=SID,collected_at="2026-10-31",site_total=total,items=out),open(OUT,"w",encoding="utf8"),ensure_ascii=False,indent=2)
print(total,len(out))
