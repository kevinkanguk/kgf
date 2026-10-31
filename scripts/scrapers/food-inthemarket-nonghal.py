import re, json, os, time, html, requests
SID="food-inthemarket-nonghal"; ROOT="E:/090_ETC/kf"
CACHE=f"{ROOT}/data/cache/html/{SID}"; OUT=f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE="https://inthemarket.co.kr"; EVENT=BASE+"/?pn=product.list&cuid=763"
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
S=requests.Session(); S.headers["User-Agent"]="Mozilla/5.0"
def get(pg):
    f=f"{CACHE}/p{pg}.html"
    if os.path.exists(f) and pg>1 or (pg==1 and os.path.exists(f) and 'item_box' in open(f,encoding='utf8').read()):
        return open(f,encoding='utf8').read()
    for _ in range(3):
        r=S.get(BASE+"/",params={"pn":"product.list","cuid":763,"listpg":pg},timeout=30)
        if r.ok: break
        time.sleep(2)
    r.encoding="utf-8"; open(f,"w",encoding="utf8").write(r.text); time.sleep(0.5); return r.text
num=lambda s:int(re.sub(r"\D","",s)) if s and re.sub(r"\D","",s) else None
def parse(t):
    out=[]
    for blk in t.split('<div class="item_box js_item_box')[1:]:
        pc=re.search(r'data-pcode="([^"]+)"',blk).group(1)
        m=re.search(r'class="item_name">\s*(.*?)\s*</a>',blk,re.S); name=html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip()
        pr=re.search(r'<div class="price">(.*?)</div>\s*</div>|<div class="price">(.*?)<div class="price type_max">',blk,re.S)
        ps=pr.group(0) if pr else ""
        b=re.search(r'class="before"><span class="won">([\d,]+)',ps); a=re.search(r'class="after"><span class="won">([\d,]+)',ps)
        pc_=re.search(r'class="percent">(\d+)%',ps)
        mx=re.search(r'type_max">\s*<div class="after"><span class="won">([\d,]+)',blk)
        cond=[]
        if mx: cond.append(f"최대 할인가 {mx.group(1)}원(쿠폰/카드 등 적용 시)")
        if '농할쿠폰' in blk: cond.append("농할쿠폰 대상")
        if '농식품바우처' in blk: cond.append("농식품바우처 대상")
        if '무료배송' in blk: cond.append("무료배송")
        out.append(dict(pcode=pc,product=name,orig=num(b.group(1)) if b else None,sale=num(a.group(1)) if a else None,
            pct=float(pc_.group(1)) if pc_ else None,cond="; ".join(cond) or None))
    return out
t=get(1); total=num(re.search(r'class="total">전체 <em>([\d,]+)',t).group(1)); pages=-(-total//40)
seen={}; 
for pg in range(1,pages+3):
    its=parse(get(pg))
    if not its: break
    for i in its: seen.setdefault(i["pcode"],i)
items=[]
for n,i in enumerate(seen.values(),1):
    items.append(dict(item_id=f"{SID}-{n:04d}",category="food",source_id=SID,unit=None,vendor="인더마켓(온누리몰) 입점판매자",
      channel="인더마켓(온누리몰) 농할대전",product=i["product"],model_code=i["pcode"],
      buy_url=f"{BASE}/?pn=product.view&cuid=763&pcode={i['pcode']}",event_url=EVENT,
      claimed_original_price=i["orig"],sale_price=i["sale"],claimed_discount_pct=i["pct"],conditions=i["cond"],
      sources=[EVENT]))
json.dump(dict(category="food",source_id=SID,collected_at="2026-10-31",site_total=total,items=items),open(OUT,"w",encoding="utf8"),ensure_ascii=False,indent=2)
print(total,len(items))
