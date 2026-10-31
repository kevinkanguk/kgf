import requests, re, json, os, datetime
SID='food-hanwooboardmarket-part-002'
URL='https://www.hanwooboardmarket.com/shop/shopbrand.html?type=N&xcode=040&mcode=002'
root='E:/090_ETC/kf'
os.makedirs(f'{root}/data/cache/html/{SID}',exist_ok=True)
r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=30)
open(f'{root}/data/cache/html/{SID}/p1.html','wb').write(r.content)
t=r.content.decode('cp949','replace')
total=re.findall(r'전체상품\s*(\d+)',t)
links=sorted(set(re.findall(r'branduid=(\d+)',t)))
print('total',total,'links',len(links))
out={'category':'food','source_id':SID,'collected_at':datetime.date.today().isoformat(),'items':[],
     'issues':['server-rendered page reports 전체상품 0개 (xcode=040 category empty/hidden from nav; duplicates brand 042)']}
os.makedirs(f'{root}/data/raw/catalog/food',exist_ok=True)
json.dump(out,open(f'{root}/data/raw/catalog/food/{SID}.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
