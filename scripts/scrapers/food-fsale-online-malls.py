import requests,re,json,html,os,sys
from urllib.parse import urlparse
H={'User-Agent':'Mozilla/5.0'}
SID='food-fsale-online-malls'
CD='E:/090_ETC/kf/data/cache/html/'+SID+'/'
OUT='E:/090_ETC/kf/data/raw/catalog/food/'+SID+'.json'
BASE='https://www.fsale.kr/bbs/board.php?bo_table=coupon&sca=%EC%98%A8%EB%9D%BC%EC%9D%B8%EC%87%BC%ED%95%91%EB%AA%B0'
os.makedirs(CD,exist_ok=True)
def get(u,**k):
    r=requests.get(u,headers=H,timeout=30,**k);r.encoding='utf8';return r
t=get(BASE).text;open(CD+'list.html','w',encoding='utf8').write(t)
cards=re.split(r'<li class="gall_li">',t)[1:]
rows=[]
for c in cards:
    logo=re.search(r'member_image/\w+/(\w+?)\d*\.gif',c)
    pct=re.search(r'<div class="subj"><span>[^<]*</span>\s*([\d.]+)%',c)
    desc=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',re.search(r'<div class="bo_cnt">(.*?)</div>',c,re.S).group(1)))).strip()
    wid=re.search(r'wr_id=(\d+)',c)
    img=re.search(r'<img src="([^"]+member_image[^"]+)"',c)
    rows.append((int(wid.group(1)) if wid else None,logo.group(1) if logo else None,float(pct.group(1)) if pct else None,desc,img.group(1) if img else None,'ready' in c and 'cover_none ready' in c))
NAMES={'kakao':'카카오톡 선물하기','lotte':'롯데온','nsshopping':'NS홈쇼핑','naver':'네이버쇼핑','hmallfish':'현대Hmall','fullhit':'풀무원/풀핏','gsshopfood':'GS샵','koreanssan':None}
out=[];k=0
for wid,logo,pct,desc,img,ready in rows:
    if wid is None: print('skip no link',logo,desc);continue
    k+=1
    link='https://www.fsale.kr/bbs/link.php?bo_table=coupon&wr_id=%d&no=1&sca=%%EC%%98%%A8%%EB%%9D%%BC%%EC%%9D%%B8%%EC%%87%%BC%%ED%%95%%91%%EB%%AA%%B0'%wid
    view='https://www.fsale.kr/bbs/board.php?bo_table=coupon&wr_id=%d'%wid
    loc=None
    try:
        r=requests.get(link,headers=H,timeout=30,allow_redirects=False);loc=r.headers.get('location')
        v=get(view).text;open(CD+'v%d.html'%wid,'w',encoding='utf8').write(v)
    except Exception as e: print('err',wid,e)
    dom=urlparse(loc).netloc if loc else None
    mall=dom or logo
    out.append({"item_id":"%s-%04d"%(SID,k),"category":"food","source_id":SID,"unit":desc or None,
      "vendor":mall,"channel":"대한민국 수산대전 온라인쇼핑몰 기획전",
      "product":"%s 수산대전 기획전 (최대 %s%% 할인) %s"%(mall,('%g'%pct) if pct is not None else '?',desc),
      "model_code":None,"buy_url":loc or view,"image_url":img,"rating":None,"review_count":None,"event_url":view,
      "claimed_original_price":None,"sale_price":None,"claimed_discount_pct":pct,
      "conditions":"몰 단위 기획전(개별 상품 아님). 최대 할인율 %s%%. 게시글 wr_id %d. %s"%(('%g'%pct) if pct is not None else '?',wid,'오픈 준비중(링크 없음)' if ready else '바로가기 링크: '+link),
      "sources":[BASE,view]+([link] if loc else [])})
json.dump({"category":"food","source_id":SID,"collected_at":"2026-10-31","items":out},open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(out),len(rows))
