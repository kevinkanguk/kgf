import re, json, html, requests, datetime, os
SID="food-hnsmall-soosan"; CAT="food"
URL="https://m.hnsmall.com/category/planshop/2026087149"
D=f"E:/090_ETC/kf/data/cache/html/{SID}/"
OUT=f"E:/090_ETC/kf/data/raw/catalog/{CAT}/{SID}.json"
H={"User-Agent":"Mozilla/5.0 (iPhone)","X-Requested-With":"XMLHttpRequest"}
s=requests.Session()
_r=s.get(URL,headers=H,timeout=30); _r.encoding="utf-8"; page=_r.text
open(D+"page.html","w",encoding="utf8").write(page)
pd=lambda k:re.search(r'"%s"\s*:\s*"([^"]*)"'%k,page).group(1)
tabs=re.findall(r'sub_banner_code="(\d+)"><a[^>]*><span>([^<]+)</span>',page)
frags=[]  # (tabname, html)
for sub,name in tabs:
    for cp in range(1,30):
        r=s.post("https://m.hnsmall.com/category/nextPlanGoods",headers=H,data={
          "planCode":pd("plan_code"),"areaCode":pd("area_code"),"bannerCode":pd("banner_code"),
          "subBannerCode":sub,"currentPage":cp,"subCateFlag":"true","viewType":1,"rowsPerPage":20,
          "planclassCode":pd("planclass_code"),"templateCode":pd("template_code"),"trackingCode":""},timeout=30)
        r.encoding="utf-8"; txt=r.text
        open(D+f"tab_{sub}_p{cp}.html","w",encoding="utf8").write(txt)
        if not txt.strip() or "goods/view/" not in txt: break
        frags.append((name,txt))
        if len(re.findall(r"goPage\('/goods/view/\d+",txt))<40 and len(set(re.findall(r"goods/view/(\d+)",txt)))<20: break
# first page's static blocks too (coupon list + first tab)
frags.insert(0,("쿠폰특가",page))
items=[];seen=set()
for tab,t in frags:
    blocks=re.split(r'(?=<li[\s>])',t)
    for li in blocks:
        m=re.search(r"goPage\('(/goods/view/(\d+))",li)
        if not m or 'goods-benefit' not in li and 'goods-price' not in li: continue
        gid=m.group(2)
        if gid in seen: continue
        seen.add(gid)
        g=lambda p:(lambda x:x.group(1) if x else None)(re.search(p,li,re.S))
        name=html.unescape((g(r'class="tit"[^>]*>(.*?)</(?:a|div)>') or "")).strip()
        img=g(r'data-original="([^"]+)"') or g(r'<span class="img">\s*<img[^>]*?src="([^"]+)"')
        if img and img.startswith("//"): img="https:"+img
        price=g(r'<strong>([\d,]+)</strong>')
        pct=g(r'goods-benefit-num">~?<em>([\d.]+)</em>')
        sc=g(r'<span class="num">([\d.]+)점')
        rc=g(r'<span class="count">\(([\d,]+)\)')
        if rc is None:
            rc=g(r'class="review">\s*<span class="tit"[^>]*>상품평</span>\s*<span class="count">([\d,]+)</span>')
        brand=g(r'data-ga-brand="([^"]*)"')
        flags=re.findall(r'<em class="flag[^"]*">([^<]+)</em>',li)
        cond="최종혜택가(쿠폰·카드 등 혜택 적용가, '~' 최저가 표기)"
        if flags: cond+=". 플래그: "+", ".join(flags)
        items.append({
         "item_id":f"{SID}-{len(items)+1:04d}","category":CAT,"source_id":SID,
         "unit":None,"vendor":(brand or "홈앤쇼핑"),"channel":"홈앤쇼핑 수산대전","product":name,"model_code":gid,
         "buy_url":"https://m.hnsmall.com/goods/view/"+gid,"image_url":img,
         "rating":round(float(sc)/20,2) if sc else None,
         "review_count":int(rc.replace(",","")) if rc else None,
         "event_url":URL,"claimed_original_price":None,
         "sale_price":int(price.replace(",","")) if price else None,
         "claimed_discount_pct":float(pct) if pct else None,
         "conditions":cond+f" [탭:{tab}]","sources":[URL]})
os.makedirs(os.path.dirname(OUT),exist_ok=True)
json.dump({"category":CAT,"source_id":SID,"collected_at":datetime.datetime.now().isoformat(timespec="seconds"),"items":items},open(OUT,"w",encoding="utf8"),ensure_ascii=False,indent=2)
print(len(items),tabs)
