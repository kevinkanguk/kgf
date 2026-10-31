import requests, re, json, os, html, datetime
from concurrent.futures import ThreadPoolExecutor
SID="appliance-eland-winter"; CAT="appliance"
EV="https://www.etlandmall.co.kr/pc/event/planProductList.do?PLN_MST_IDX=12190"
B="https://www.etlandmall.co.kr"
C=f"E:/090_ETC/kf/data/cache/html/{SID}/"
OUT=f"E:/090_ETC/kf/data/raw/catalog/{CAT}/{SID}.json"
os.makedirs(C,exist_ok=True)
H={"User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest","Referer":EV}
def get(u,**k):
    r=requests.get(u,headers=H,timeout=30,**k); r.encoding='utf-8'; return r.text
def num(s): return int(s.replace(',','')) if s else None
lst=get(EV); open(C+"list.html","w",encoding="utf-8").write(lst)
groups=re.findall(r'planGrpIdx="(\d+)" planGrpCol="(\d+)"',lst)
items=[];seen=set()
for g,col in groups:
    r=requests.post(B+"/pc/event/planProductDetailListAjax.do",headers=H,timeout=30,data={"PLN_MST_IDX":"12190","PLN_GRP_COL":col,"PLN_GRP_IDX":g,"prePlan":"","PLN_MST_SPECIAL_YN":"Y","PLN_MST_PRD_DPL_YN":"Y","PLN_TIME_SALE":"N","PLN_POINT_SALE_YN":"N","chlCode":""})
    r.encoding='utf-8'; t=r.text; open(C+f"g{g}.html","w",encoding="utf-8").write(t)
    for blk in t.split('<a class="components_product_list"')[1:]:
        m=re.search(r'prdMstCd=(\w+)',blk)
        if not m or m.group(1) in seen: continue
        cd=m.group(1); seen.add(cd)
        name=re.search(r'components_product_name">\s*(.*?)</p>',blk,re.S)
        pct=re.search(r'priceGroup_sale">([\d.]+)%',blk)
        pr=re.search(r'priceGroup_price">\s*([\d,]+)',blk)
        img=re.search(r'<img\s+src="([^"]+)"',blk)
        rate=re.search(r'class="star_(\d+)"',blk)
        rv=re.search(r'reivewGroup_total">\(([\d,]+)\)',blk)
        items.append(dict(cd=cd,name=html.unescape(re.sub(r'\s+',' ',name.group(1)).strip()) if name else None,
            pct=float(pct.group(1)) if pct else None,benefit=num(pr.group(1)) if pr else None,
            img=B+img.group(1) if img and img.group(1).startswith('/') else (img.group(1) if img else None),
            rating=round(int(rate.group(1))/10,1) if rate else None,rc=num(rv.group(1)) if rv else None,grp=g))
def detail(it):
    p=C+f"d_{it['cd']}.html"
    if os.path.exists(p): t=open(p,encoding="utf-8").read()
    else:
        try: t=get(f"{B}/pc/product/product.do?prdMstCd={it['cd']}")
        except Exception as e: return it
        open(p,"w",encoding="utf-8").write(t)
    o=re.search(r'price_org.*?class="price">([\d,]+)',t,re.S)
    d=re.search(r'ic_price_equalgreen.*?class="price">([\d,]+)',t,re.S)
    mx=re.search(r'ic_price_equalred.*?class="price">([\d,]+)',t,re.S)
    pt=re.search(r'point_top-value"><span class="value">([\d,]+)',t)
    ld=re.search(r'"price":\s*(\d+)',t)
    it['orig']=num(o.group(1)) if o else None
    it['disc']=num(d.group(1)) if d else (int(ld.group(1)) if ld else None)
    it['max']=num(mx.group(1)) if mx else None
    it['pt']=num(pt.group(1)) if pt else None
    return it
with ThreadPoolExecutor(6) as ex: items=list(ex.map(detail,items))
out=[]
for i,it in enumerate(items,1):
    n=it['name'] or ''
    tag=re.findall(r'\[([^\]]+)\]',n); core=re.sub(r'\[[^\]]*\]','',n).strip()
    vendor=core.split(' ')[0] if core else ''
    mc=re.findall(r'\b[A-Z][A-Z0-9\-]{4,}\b',core)
    cond=[]
    if it.get('max') and it.get('disc') and it['max']!=it['disc']: cond.append(f"e.POINT {it.get('pt') or ''}P 적립 반영 최대혜택가 {it['max']:,}원(목록 표시가)")
    if tag: cond.append("행사태그: "+", ".join(tag))
    sale=it.get('disc') or it['benefit']
    out.append(dict(item_id=f"{SID}-{i:04d}",category=CAT,source_id=SID,unit=None,vendor=vendor,channel="이랜드몰",
        product=n,model_code=mc[-1] if mc else None,buy_url=f"{B}/pc/product/product.do?prdMstCd={it['cd']}",
        image_url=it['img'],rating=it['rating'],review_count=it['rc'],event_url=EV,
        claimed_original_price=it.get('orig'),sale_price=sale,claimed_discount_pct=it['pct'],
        conditions="; ".join(cond) or None,
        sources=[EV,f"{B}/pc/product/product.do?prdMstCd={it['cd']}"]))
res=dict(category=CAT,source_id=SID,collected_at=datetime.datetime.now().isoformat(timespec='seconds'),items=out)
os.makedirs(os.path.dirname(OUT),exist_ok=True)
json.dump(res,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(len(out),sum(1 for x in out if x['claimed_original_price']),sum(1 for x in out if x['rating']))
