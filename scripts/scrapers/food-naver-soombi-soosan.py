# Naver brand store returns HTTP 429 (bot block) to plain requests. Writes empty catalog if blocked.
import requests, json, datetime, os
SID="food-naver-soombi-soosan"; URL="https://brand.naver.com/soombi_seafood"
r=requests.get(URL,headers={"User-Agent":"Mozilla/5.0 Chrome/130","Accept-Language":"ko-KR,ko"},timeout=20)
print(r.status_code)
items=[]
out={"category":"food","source_id":SID,"collected_at":datetime.date.today().isoformat(),"items":items}
if r.status_code!=200: print("blocked; no items written"); raise SystemExit(1)
