import requests,re,json,html,os,datetime
SID='food-nurimarket-nonghal-nh60'
H={'User-Agent':'Mozilla/5.0'}
CD='E:/090_ETC/kf/data/cache/html/'+SID+'/'
OUT='E:/090_ETC/kf/data/raw/catalog/food/'+SID+'.json'
BASE='https://nurimarket.co.kr/shop/list.php?ca_id=nh60&sort=it_sum_qty&sortodr=desc&page=%d'
EVENT='https://nurimarket.co.kr/shop/list.php?ca_id=nh60'
os.makedirs(CD,exist_ok=True)
def get(p):
    f=CD+'p%d.html'%p
    if os.path.exists(f):
        return open(f,encoding='utf8').read()
    r=requests.get(BASE%p,headers=H,timeout=30);r.encoding='utf8'
    open(f,'w',encoding='utf8').write(r.text);return r.text
def num(s):
    s=re.sub(r'[^\d]','',s or '');return int(s) if s else None
def parse(t):
    out=[]
    for blk in t.split('<div class="swiper-slide swiper-slide-list-nh60">')[1:]:
        blk=re.split(r'<!--\s*(?:\S+\s+)?\}|<div class="cb">\s*</div>\s*</div>\s*</div>',blk)[0] if False else blk
        m=re.search(r'item\.php\?it_id=(\d+)',blk)
        if not m:continue
        iid=m.group(1)
        img=re.findall(r'<img src="(https?://[^"]*?/data/item/[^"]+)"',blk)
        title=re.search(r'class="font-pretendard-R cut2">(.*?)</a>',blk,re.S)
        title=html.unescape(re.sub(r'<[^>]+>','',title.group(1))).strip() if title else None
        pct=re.search(r'main_list_price_li1[^>]*>([\d.]+)%',blk)
        sale=re.search(r'main_list_price_li2[^>]*>([\d,]+)',blk)
        orig=re.search(r'<strike>([\d,]+)',blk)
        coup=re.search(r'쿠폰</span>.*?>([\d.]+)%</span>.*?적용가</span>.*?>([\d,]+)</span>',blk,re.S)
        star=re.search(r's_star(\d+(?:\.\d+)?)\.png',blk)
        cnt=re.search(r'main_list_star_cnt[^>]*>\(([\d,]+)\)',blk)
        out.append(dict(iid=iid,title=title,img=img[0] if img else None,pct=float(pct.group(1)) if pct else None,
            sale=num(sale.group(1)) if sale else None,orig=num(orig.group(1)) if orig else None,
            coup=(coup.group(1),num(coup.group(2))) if coup else None,
            star=float(star.group(1)) if star else None,cnt=num(cnt.group(1)) if cnt else None,
            soldout='soldout' in blk.lower() or '품절' in blk))
    return out
def main():
    allr={};p=1
    while p<=50:
        t=get(p);rows=parse(t);print(p,len(rows))
        n0=len(allr)
        for r in rows:allr.setdefault(r['iid'],r)
        if len(allr)==n0:break
        p+=1
    items=[]
    for n,r in enumerate(allr.values(),1):
        title=r['title'] or ''
        m=re.match(r'\(([^)]+)\)',title)
        vendor=m.group(1) if m else '농협몰 입점업체'
        cond=None
        if r['coup']:cond='쿠폰 %s%% 적용가 %s원'%(r['coup'][0],format(r['coup'][1],','))
        if r['soldout']:cond=(cond+'; ' if cond else '')+'품절 표시'
        sale,orig=r['sale'],r['orig']
        pct=r['pct']
        if pct is None and sale and orig and orig>sale:pct=round((1-sale/orig)*100,1)
        items.append({"item_id":"%s-%04d"%(SID,n),"category":"food","source_id":SID,"unit":None,
          "vendor":vendor,"channel":"온누리마켓(농협몰) 농할","product":title,"model_code":r['iid'],
          "buy_url":"https://nurimarket.co.kr/shop/item.php?it_id="+r['iid'],"image_url":r['img'],
          "rating":r['star'],"review_count":r['cnt'],"event_url":EVENT,
          "claimed_original_price":orig,"sale_price":sale,"claimed_discount_pct":pct,"conditions":cond,
          "sources":[EVENT]})
    d={"category":"food","source_id":SID,"collected_at":"2026-10-31","items":items}
    json.dump(d,open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
    print('saved',len(items))
if __name__=='__main__':main()
