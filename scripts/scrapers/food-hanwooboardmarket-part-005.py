import requests, re, json, os, datetime
SID = "food-hanwooboardmarket-part-005"
BASE = "https://www.hanwooboardmarket.com"
ROOT = "E:/090_ETC/kf"
H = {"User-Agent": "Mozilla/5.0"}
urls = ["/shop/shopbrand.html?type=N&xcode=040&mcode=005"] + \
       ["/shop/shopbrand.html?type=N&xcode=040&mcode=005&scode=%03d" % i for i in range(1, 9)]
items, seen, issues = [], set(), []
os.makedirs(f"{ROOT}/data/cache/html/{SID}", exist_ok=True)
for n, u in enumerate(urls):
    page = 1
    while True:
        r = requests.get(BASE + u + f"&page={page}", headers=H, timeout=30)
        t = r.content.decode("euc-kr", "ignore")
        open(f"{ROOT}/data/cache/html/{SID}/u{n}_p{page}.html", "w", encoding="utf-8").write(t)
        total = re.search(r"전체상품\s*(\d+)", t)
        pids = [p for p in re.findall(r"shopdetail\.html\?[^\"']*branduid=(\d+)", t) if p not in seen]
        if not pids:
            break
        for p in pids:
            seen.add(p)
            items.append({"branduid": p})  # TODO: parse fields if the shop ever lists products
        page += 1
        if page > 50: break
out = {"category": "food", "source_id": SID,
       "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": items}
json.dump(out, open(f"{ROOT}/data/raw/catalog/food/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
