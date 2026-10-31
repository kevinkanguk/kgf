import re, json, os, datetime, requests
SID='food-fsale-offline-markets'
URL='https://www.fsale.kr/bbs/board.php?bo_table=coupon&sca=%EC%98%A4%ED%94%84%EB%9D%BC%EC%9D%B8'
ROOT='E:/090_ETC/kf'
cache=f'{ROOT}/data/cache/html/{SID}/list1.html'
os.makedirs(os.path.dirname(cache),exist_ok=True)
t=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=30).text
open(cache,'w',encoding='utf8').write(t)
KNOWN={'hansalim':'한살림','dure':'두레생협','suhyup':'수협','icoopstore':'아이쿱생협','gsretail':'GS리테일','eland':'이랜드리테일','megamart':'메가마트','thejmart':'더제이마트'}
items=[]
for b in re.findall(r'<li class="gall_li">(.*?)</li>',t,re.S)[::-1]:
    no=re.search(r'sound_only">\s*(\d+)',b).group(1)
    logo=re.search(r'member_image/([^"?]+)',b).group(1)
    mid=re.sub(r'\d+$','',os.path.splitext(logo.split('/')[-1])[0])
    d=re.search(r'class="subj">(.*?)</div>',b,re.S)
    pct=re.search(r'(\d+(?:\.\d+)?)\s*%',re.sub('<.*?>','',d.group(1))) if d else None
    prod=re.sub(r'\s+',' ',re.search(r'bo_cnt">(.*?)</div>',b,re.S).group(1)).strip()
    store=re.search(r'data-image="([^"]+)"[^>]*>\s*행사 참여 점포',b)
    coup=re.search(r'class="popImg" data-image="([^"]+)"',b)
    items.append(dict(item_id=f'{SID}-{len(items)+1:04d}',category='food',source_id=SID,unit=None,
      vendor=KNOWN.get(mid,mid),channel='오프라인 마트(fsale.kr 기획전)',product=prod,model_code=None,buy_url=URL,
      image_url='https://www.fsale.kr/data/member_image/'+logo,rating=None,review_count=None,event_url=URL,
      claimed_original_price=None,sale_price=None,claimed_discount_pct=float(pct.group(1)) if pct else None,
      conditions='최대 할인율(품목별 상이). 참여점포 이미지: '+('https://www.fsale.kr'+store.group(1) if store else '없음'),
      sources=[URL],verify_status=None,verify_note=f'fsale 게시글번호 {no}; vendor 는 로고 파일명 기준',confidence='low'))
out={'category':'food','source_id':SID,'collected_at':datetime.datetime.now().isoformat(timespec='seconds'),'items':items}
p=f'{ROOT}/data/raw/catalog/food/{SID}.json'
os.makedirs(os.path.dirname(p),exist_ok=True)
json.dump(out,open(p,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items))
