import requests, re, json, os, html, datetime
SID='mall-epost-kgf-p8'
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CACHE=os.path.join(ROOT,'data','cache','html',SID); os.makedirs(CACHE,exist_ok=True)
OUT=os.path.join(ROOT,'data','raw','catalog','mall',SID+'.json')
BASE='https://mall.epost.go.kr'
EVENT=BASE+'/fo/display/plnbefDspyNewView.do?plnbefId=10027801#pages=50-56'
def page(n):
    f=os.path.join(CACHE,f'p{n}.html')
    if os.path.exists(f): return open(f,encoding='utf-8').read()
    r=requests.post(BASE+'/fo/display/plnbefDspyNewView.do',data={'plnbefId':'10027801','pageIndex':n,'pageUnit':40},headers={'User-Agent':'Mozilla/5.0'},timeout=30)
    t=r.content.decode('utf-8'); open(f,'w',encoding='utf-8').write(t); return t
def num(s): 
    s=re.sub(r'[^\d]','',s or ''); return int(s) if s else None
items=[]; seen=set()
for n in range(50,57):
    t=page(n)
    a=t.find('<div class="list_box  imglist">'); b=t.find('</ul>',a)
    seg=t[a:]
    for li in re.split(r'<li class="[^"]*">\s*(?=<a href="javaScript:fn_goodsDetailView)',seg)[1:]:
        m=re.search(r"fn_goodsDetailView\('([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'\)",li)
        if not m: continue
        cd,pav,dt,dtl,ct=m.groups()
        img=re.search(r'<div class="goods_img">.*?<img src="([^"]+)" alt="([^"]*)"',li,re.S)
        # skip cert mark imgs: take the last img in goods_img
        imgs=re.findall(r'<img src="([^"]+)" alt="([^"]*)"',li.split('goods_text')[0])
        prod=re.search(r'<p class="tit">(.*?)</p>',li,re.S)
        pt=html.unescape(re.sub(r'<span class="icn_dis">.*?</span>','',prod.group(1),flags=re.S)) if prod else ''
        pt=re.sub(r'<[^>]+>','',pt).strip()
        pct=re.search(r'<span class="icn_dis"><b>([\d.]+)</b>',li)
        prs=re.findall(r'<span class="pr_tit">([^<]*)</span><span><em>([\d,]+)</em>',li)
        d={k.strip():num(v) for k,v in prs}
        orig=d.get('판매가'); sale=d.get('할인가') 
        if sale is None and orig is not None: sale=orig; orig=None if not pct else orig
        star=re.search(r'class="star(\d+)"',li); gun=re.search(r'<span class="gun">([\d,]+)',li)
        sub=re.search(r'<div class="goods_text">.*?</p>\s*<span>(.*?)</span>',li,re.S)
        tips=re.findall(r'<img src="/img/icon_tip_\w+\.gif" alt="([^"]*)"',li)
        cond=[x for x in ([html.unescape(sub.group(1)).strip()] if sub else [])+tips if x]
        if cd in seen: continue
        seen.add(cd)
        items.append(dict(
          item_id=f'{SID}-{len(items)+1:04d}',category='mall',source_id=SID,unit=None,
          vendor='우체국쇼핑 소상공인',channel='우체국쇼핑 소상공인 동행',product=pt,model_code=cd,
          buy_url=f'{BASE}/fo/goods/goodsDetailView.do?goodsCd={cd}&pavlnDivCd={pav}&goodsDispTypeCd={dt}&goodsDispTypeDtlCd={dtl}&ctgryCd={ct}',
          image_url=imgs[-1][0] if imgs else None,
          rating=round(int(star.group(1))/2,2) if star else None,
          review_count=num(gun.group(1)) if gun else None,
          event_url=EVENT,claimed_original_price=orig,sale_price=sale,
          claimed_discount_pct=float(pct.group(1)) if pct else None,
          conditions=' / '.join(cond) or None,
          sources=[EVENT],verify_status=None))
json.dump(dict(category='mall',source_id=SID,collected_at=datetime.date(2026,10,31).isoformat(),items=items),open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
