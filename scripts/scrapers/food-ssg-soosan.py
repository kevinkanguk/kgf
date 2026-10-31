import requests, re, json, html, time, os, datetime
SID="food-ssg-soosan"; CAT="food"
ROOT="E:/090_ETC/kf"
CACHE=f"{ROOT}/data/cache/html/{SID}"; OUT=f"{ROOT}/data/raw/catalog/{CAT}/{SID}.json"
EVENT="https://event.ssg.com/eventDetail.ssg?nevntId=1000000024632&domainSiteNo=6005"
H={"User-Agent":"Mozilla/5.0","Referer":"https://event.ssg.com/"}
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
def get(url,params=None):
    for i in range(5):
        try:
            r=requests.get(url,params=params,headers=H,timeout=90); r.raise_for_status(); return r.content.decode('utf8')
        except Exception as e:
            time.sleep(3)
    raise RuntimeError(url)
def txt(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()
def num(s):
    m=re.search(r'([\d,]+)\s*원',s or ''); return int(m.group(1).replace(',','')) if m else None
items={}; order=[]
for disp in ['6000401291','6000401292']:
    th=get("https://event.ssg.com/eventDetail/ajaxPlanShopTheme.ssg",dict(dispCmptId=disp,inflowSiteNo='6005',deviceDivCd='10',previewYn='N'))
    open(f"{CACHE}/theme_{disp}.html","w",encoding='utf8').write(th)
    for a in re.findall(r'<a [^>]*cmctg_lnk[^>]*>',th):
        g=lambda k:(re.search(k+r'="([^"]*)"',a) or [None,None])[1]
        cornr,setid,name=g('data-cornr-id'),g('data-cornr-set-id'),html.unescape(g('data-cornr-set-name') or '')
        div,img,tpl=g('data-cornr-set-div-cd'),g('data-item-img-type'),g('data-templ-file-nm')
        page=1
        while True:
            t=get("https://event.ssg.com/eventDetail/ajaxPlanShopThemeItem.ssg",dict(dispCmptId=disp,cornrId=cornr,themeId=setid,cornrSetDivCd=div,itemImgType=img,templFileNm=tpl,page=page,pageSize=80,inflowSiteNo='6005',deviceDivCd='10',previewYn='N'))
            open(f"{CACHE}/items_{disp}_{setid}_p{page}.html","w",encoding='utf8').write(t)
            for blk in re.split(r'(?=<li class="cunit_t)',t)[1:]:
                m=re.search(r'data-react-unit-id="(\d+)"',blk)
                if not m: continue
                iid=m.group(1)
                if iid in items:
                    items[iid]['_themes'].append(name); continue
                href=(re.search(r'href="(https://www\.ssg\.com/item/itemView\.ssg\?itemId=\d+[^"]*)"',blk) or [0,None])[1]
                img_=(re.search(r'<img[^>]*\ssrc="(https?://[^"]+)"',blk) or [0,None])[1]
                brand=txt((re.search(r'ssgitem_tit_brand">(.*?)</div>',blk,re.S) or [0,''])[1])
                pname=txt((re.search(r'ssgitem_tit_name">(.*?)</div>',blk,re.S) or [0,''])[1])
                origin=num((re.search(r'ty_origin">(.*?)</div>',blk,re.S) or [0,''])[1])
                old_blk=(re.search(r'ty_old">(.*?)</div>',blk,re.S) or [0,''])[1]
                old=num(re.search(r'<del>.*?</del>',old_blk,re.S).group(0)) if '<del>' in old_blk else None
                coupon=txt((re.search(r'ssgitem_coupon_text">(.*?)</span>',old_blk,re.S) or [0,''])[1])
                rate=(re.search(r'ssgitem_sale_rate">.*?<span>\s*([\d.]+)\s*%',blk,re.S) or [0,None])[1]
                sale=num((re.search(r'ssgitem_new_price[^>]*>(.*?)</div>',blk,re.S) or [0,''])[1])
                if sale is None:
                    mm=re.search(r'data-react-unit-price=\'(\d+)\'',blk); sale=int(mm.group(1)) if mm else None
                rs=(re.search(r'ssgitem_review_score">(.*?)</div>',blk,re.S) or [0,''])[1]
                rv=re.findall(r'review_text">([^<]*)<',rs)
                rating=float(rv[0]) if rv and re.match(r'^[\d.]+$',rv[0].strip()) else None
                rc=None
                if len(rv)>1:
                    mm=re.search(r'([\d,]+)',rv[1]); rc=int(mm.group(1).replace(',','')) if mm else None
                orig=old if old else origin
                cond=[]
                if coupon: cond.append(coupon)
                if origin and old and origin!=old: cond.append(f"최고판매가 {origin:,}원")
                unit_note=txt((re.search(r'ssgitem_price ty_unit">(.*?)</div>',blk,re.S) or [0,''])[1])
                if unit_note: cond.append(unit_note)
                items[iid]=dict(_iid=iid,_themes=[name],category=CAT,source_id=SID,unit=None,vendor=brand or "SSG.COM",channel="SSG.COM 수산대전",
                  product=pname,model_code=None,buy_url=href or f"https://www.ssg.com/item/itemView.ssg?itemId={iid}",image_url=img_,
                  rating=rating,review_count=rc,event_url=EVENT,claimed_original_price=orig,sale_price=sale,
                  claimed_discount_pct=float(rate) if rate else None,conditions="; ".join(cond) or None,sources=[EVENT,f"https://www.ssg.com/planshop/detail.ssg?dispCmptId={disp}"])
                order.append(iid)
            if 'data-has-next="true"' in t[:600]: page+=1
            else: break
out=[]
for n,iid in enumerate(order,1):
    d=items[iid]; th=d.pop('_themes'); d.pop('_iid')
    d['conditions']="; ".join(filter(None,[d['conditions'],"테마: "+", ".join(dict.fromkeys(th))]))
    out.append({"item_id":f"{SID}-{n:04d}",**d})
json.dump({"category":CAT,"source_id":SID,"collected_at":datetime.date(2026,10,31).isoformat(),"items":out},open(OUT,"w",encoding='utf8'),ensure_ascii=False,indent=2)
print(len(out))
