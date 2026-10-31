import re, json, requests, datetime
SID="food-hanwooboardmarket-part-001"
URL="https://www.hanwooboardmarket.com/shop/shopbrand.html?type=N&xcode=040&mcode=001"
r=requests.get(URL,headers={"User-Agent":"Mozilla/5.0"},timeout=30)
t=r.content.decode("cp949",errors="replace")
open(f"data/cache/html/{SID}/p1.html","w",encoding="utf8").write(t)
m=re.search(r'item-total">\s*[^\d<]*(\d+)',t)
total=int(m.group(1)) if m else None
links=sorted(set(re.findall(r'shopdetail\.html\?branduid=\d+',t)))
items=[]
for i,l in enumerate(links,1):
    items.append({"item_id":f"{SID}-{i:04d}","category":"food","source_id":SID,"vendor":"한우보드마켓","channel":"한우보드마켓","product":None,"buy_url":"https://www.hanwooboardmarket.com/shop/"+l,"sources":[URL]})
out={"category":"food","source_id":SID,"collected_at":datetime.date.today().isoformat(),"items":items,"issues":[f"category page reports total items={total}; no products listed (empty category, brand 042 duplicates)"]}
json.dump(out,open(f"data/raw/catalog/food/{SID}.json","w",encoding="utf8"),ensure_ascii=False,indent=2)
print(len(items))
