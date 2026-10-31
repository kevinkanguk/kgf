# makeshop 카테고리 목록(xcode=040/041/042)에서 branduid 상품 추출. 재실행 가능.
import re, json, time, requests, datetime, pathlib
B = "https://www.hanwooboardmarket.com"
SID = "food-hanwooboardmarket-online"
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / f"data/raw/catalog/food/{SID}.json"
CACHE = ROOT / f"data/cache/html/{SID}"
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
def get(u):
    r = S.get(B + u, timeout=40); return r.content.decode("cp949", "replace")
home = get("/")
cats = sorted(set(re.findall(r'/shop/shopbrand\.html\?type=N&xcode=\d+(?:&mcode=\d+)?(?:&scode=\d+)?', home)))
ids = {}
for c in cats:
    for pg in range(1, 30):
        t = get(c + f"&page={pg}")
        found = re.findall(r'shopdetail\.html\?branduid=(\d+)', t)
        new = [i for i in found if i not in ids]
        for i in new: ids[i] = c
        if not new: break
        time.sleep(0.3)
items = []  # 상품 파싱은 목록에 상품이 생기면 구현 (2026-10-31 기준 전 카테고리 0개)
OUT.parent.mkdir(parents=True, exist_ok=True)
json.dump({"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat(),
           "issues": [f"카테고리 {len(cats)}개 모두 전체상품 0개 (11/1 오픈 전, 홈 상품영역 비어있음)"] if not ids else [],
           "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(cats), len(ids))
