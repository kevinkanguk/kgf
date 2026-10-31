# Source is a press release (no product list). Fetches page, caches it, writes empty catalog.
import requests, json, pathlib
U='https://www.lge.co.kr/story/newsroom/236223'
r=requests.get(U,headers={'User-Agent':'Mozilla/5.0'},timeout=30); r.encoding='utf-8'
pathlib.Path('data/cache/html/appliance-lge-newsroom').mkdir(parents=True,exist_ok=True)
open('data/cache/html/appliance-lge-newsroom/236223.html','w',encoding='utf-8').write(r.text)
out={"category":"appliance","source_id":"appliance-lge-newsroom","collected_at":"2026-10-31",
"note":"Press release only: coupon packs (LGE.COM up to 1M KRW, Bestshop up to 1.04M KRW). No individual products/prices.","items":[]}
json.dump(out,open('data/raw/catalog/appliance/appliance-lge-newsroom.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
