import requests, json, os, datetime, time
SID="food-kakao-soosan"; PID=2435
ROOT="E:/090_ETC/kf"; CACHE=f"{ROOT}/data/cache/html/{SID}"
OUT=f"{ROOT}/data/raw/catalog/food/{SID}.json"
EVENT=f"https://store.kakao.com/promotion/{PID}?ad=0401_sales_fishmarket&area=br"
H={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
prods=[]; seen=set(); page=0
while True:
    r=requests.get(f"https://store.kakao.com/a/f-s/promotions/{PID}",params={"page":page,"anchor":"","anchorGroupId":""},headers=H,timeout=30)
    d=r.json()["data"]; ps=d.get("products") or []
    json.dump(r.json(),open(f"{CACHE}/p{page}.json","w",encoding="utf8"),ensure_ascii=False)
    new=[p for p in ps if p["productId"] not in seen]
    if not new: break
    for p in new: seen.add(p["productId"]); prods.append(p)
    page+=1; time.sleep(0.3)
mx={}
ids=[p["productId"] for p in prods]
for i in range(0,len(ids),20):
    try:
        r=requests.get("https://store.kakao.com/a/discounts/api/max-discount",params={"productIds":ids[i:i+20]},headers=H,timeout=30)
        json.dump(r.json(),open(f"{CACHE}/max{i//20}.json","w",encoding="utf8"),ensure_ascii=False)
        j=r.json(); arr=j.get("data",j) if isinstance(j,dict) else j
        if isinstance(arr,dict): arr=arr.get("prices") or []
        for a in arr or []:
            if isinstance(a,dict) and "productId" in a: mx[a["productId"]]=a
    except Exception as e: print("max err",e)
items=[]
for n,p in enumerate(prods,1):
    orig=p.get("originalPrice")
    on=p.get("groupDiscountStatus")=="ON_SALE" and p.get("groupDiscountedPrice")
    sale=p.get("groupDiscountedPrice") if on else p.get("discountedPrice")
    cond=[]
    if on: cond.append("톡딜가(공동구매, 기간 %s~%s)"%(p["groupDiscountPeriod"]["from"],p["groupDiscountPeriod"]["to"]) if p.get("groupDiscountPeriod") else "톡딜가")
    m=mx.get(p["productId"])
    if m:
        v=m.get("maxDiscountPrice") or m.get("maxBenefitPrice") or m.get("price")
        if v: cond.append(f"최대혜택가 {v}원(쿠폰 등 조건)")
    if p.get("hasAdditionalOptionPrice") or "~" : pass
    pct=None
    if orig and sale: pct=round((orig-sale)/orig*100,1)
    pp=p.get("productPositivePercentage")
    items.append({
     "item_id":f"{SID}-{n:04d}","category":"food","source_id":SID,
     "unit":None,"vendor":p.get("storeName"),"channel":"카카오 톡딜",
     "product":p["productName"],"model_code":str(p["productId"]),
     "buy_url":"https://store.kakao.com"+p["linkPath"].split("?")[0],
     "image_url":p.get("productImageOrigin") or p.get("productImage"),
     "rating":round(pp/20,2) if pp is not None else None,
     "review_count":p.get("reviewCount"),
     "event_url":EVENT,"claimed_original_price":orig,"sale_price":sale,
     "claimed_discount_pct":pct,"conditions":"; ".join(cond) or None,
     "sources":[EVENT,f"https://store.kakao.com/a/f-s/promotions/{PID}"]})
json.dump({"category":"food","source_id":SID,"collected_at":datetime.date(2026,10,31).isoformat(),"items":items},open(OUT,"w",encoding="utf8"),ensure_ascii=False,indent=2)
print(len(items),len(mx))
