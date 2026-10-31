import re, json, requests, os
R='E:/090_ETC/kf/'
r=requests.get('https://koreagrandfestival.kr/discountcate',headers={'User-Agent':'Mozilla/5.0'},timeout=30)
t=r.content.decode('euc-kr','replace')
os.makedirs(R+'data/cache/html/auto-kgf-discountcate',exist_ok=True)
open(R+'data/cache/html/auto-kgf-discountcate/discountcate.html','w',encoding='utf8').write(t)
# auto banner links are empty-href placeholders -> no items
items=[]
json.dump({"category":"auto","source_id":"auto-kgf-discountcate","collected_at":"2026-10-31","items":items},open(R+'data/raw/catalog/auto/auto-kgf-discountcate.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(items))
