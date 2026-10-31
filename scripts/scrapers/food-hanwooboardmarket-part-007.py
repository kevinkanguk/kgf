# makeshop 카테고리 xcode=040&mcode=007 상품(branduid) 추출. 재실행 가능.
import re, json, time, requests, datetime, pathlib
B = "https://www.hanwooboardmarket.com"
SID = "food-hanwooboardmarket-part-007"
URL = B + "/shop/shopbrand.html?type=N&xcode=040&mcode=007"
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / f"data/raw/catalog/food/{SID}.json"
CACHE = ROOT / f"data/cache/html/{SID}"; CACHE.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
ids = []
for pg in range(1, 30):
    t = S.get(URL + f"&page={pg}", timeout=40).content.decode("cp949", "replace")
    (CACHE / f"p{pg}.html").write_text(t, encoding="utf-8")
    new = [i for i in dict.fromkeys(re.findall(r'shopdetail\.html\?branduid=(\d+)', t)) if i not in ids]
    ids += new
    if not new: break
    time.sleep(0.3)
items = []  # 상품이 생기면 파싱 구현 (2026-10-31 기준 전체상품 0개)
OUT.parent.mkdir(parents=True, exist_ok=True)
json.dump({"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat(),
           "issues": [] if ids else ["카테고리 xcode=040&mcode=007 전체상품 0개 (서버렌더 HTML에 shopdetail 링크 없음; 오픈 전 추정; JS 렌더 여부 미확인 needs_browser 가능)"],
           "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(ids))
