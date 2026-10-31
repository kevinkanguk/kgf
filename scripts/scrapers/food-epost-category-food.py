import re, json, time, os, html, requests
ROOT = "E:/090_ETC/kf"
SID = "food-epost-category-food"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
BASE = "https://mall.epost.go.kr"
H = {"User-Agent": "Mozilla/5.0"}
FOOD_PREFIX = ("101", "102", "103", "104", "105")  # 농산물/수산물/축산물/가공식품/건강식품
s = requests.Session(); s.headers.update(H)

def get(url, cache_name):
    p = f"{CACHE}/{cache_name}"
    if os.path.exists(p):
        return open(p, encoding="utf8").read()
    for i in range(4):
        try:
            r = s.get(url, timeout=40)
            r.encoding = "utf-8"
            if r.status_code == 200 and len(r.text) > 5000:
                open(p, "w", encoding="utf8").write(r.text)
                time.sleep(0.3)
                return r.text
        except Exception:
            pass
        time.sleep(2)
    return None

def num(t):
    return int(t.replace(",", "")) if t else None

main = get(BASE + "/fo/main/main.do", "main.html")
cats = []
for m in re.finditer(r"fn_categoryAllMenuLink\('(\d+)', '', 2\)\">([^<]*)<", main):
    if m.group(1).startswith(FOOD_PREFIX):
        cats.append((m.group(1), m.group(2).strip()))
items, seen, issues = [], set(), []
for cd, name in cats:
    page, got_cat, total = 1, 0, None
    while True:
        url = f"{BASE}/display/viewMCategory.do?ctgryCd={cd}&hrnkCtgryCd=&currentPage={page}&rowsperPage=100&showGoodsList=I"
        h = get(url, f"M{cd}_p{page}.html")
        if h is None:
            issues.append(f"fetch fail {cd} p{page}"); break
        if total is None:
            t = re.search(r'class="active"><a[^>]*>전체<em>\(([\d,]+)\)', h)
            total = num(t.group(1)) if t else 0
        lis = re.findall(r'<li>\s*<a href="javascript:fn_goodsDetailView.*?</li>', h, re.S)
        new = 0
        for x in lis:
            m = re.search(r"fn_goodsDetailView\('([^']*)','[^']*','[^']*','([^']*)'", x)
            gc, pav = m.group(1), m.group(2)
            key = gc
            if key in seen: continue
            seen.add(key); new += 1
            title = html.unescape(re.sub(r"\s+", " ", re.search(r'<p class="tit">(.*?)</p>', x, re.S).group(1))).strip()
            title = re.sub(r"<[^>]+>", "", title).strip()
            um = re.search(r'</p>\s*<span>\s*([^<]*?)\s*</span>', x, re.S)
            unit = um.group(1).strip() if um and um.group(1).strip() else None
            pr = re.search(r'<div class="price">(.*?)</div>', x, re.S).group(1)
            orig = sale = pct = None
            m1 = re.search(r'<p><span>([\d,]+)원</span></p>\s*<p><span><em>(\d+)</em>%</span>\s*<i>([\d,]+)원</i>', pr)
            m2 = re.search(r'<em>([\d,]+)</em>원', pr)
            if m1:
                orig, pct, sale = num(m1.group(1)), float(m1.group(2)), num(m1.group(3))
            elif m2:
                sale = num(m2.group(1))
            else:
                issues.append(f"no price {gc}")
            bm = re.match(r"\[([^\]]+)\]", title)
            vendor = "우체국쇼핑"
            items.append({
                "item_id": None, "category": "food", "source_id": SID, "unit": unit,
                "vendor": vendor, "channel": "우체국쇼핑", "product": title, "model_code": gc,
                "buy_url": f"{BASE}/fo/goods/goodsDetailView.do?goodsCd={gc}&pavlnDivCd={pav}",
                "event_url": url if False else f"{BASE}/display/viewMCategory.do?ctgryCd={cd}&hrnkCtgryCd=",
                "claimed_original_price": orig, "sale_price": sale, "claimed_discount_pct": pct,
                "conditions": None, "sources": [f"{BASE}/display/viewMCategory.do?ctgryCd={cd}&hrnkCtgryCd="],
                "verify_status": None, "verify_note": f"우체국쇼핑 카테고리 {name}({cd}) 목록", "confidence": None,
            })
        got_cat += new
        if not lis or len(lis) < 100 or page >= 80:
            break
        page += 1
    print(cd, name, "total", total, "listed_new", got_cat, flush=True)
for i, it in enumerate(items, 1):
    it["item_id"] = f"{SID}-{i:04d}"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "food", "source_id": SID, "collected_at": "2026-10-31", "items": items},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("TOTAL", len(items), "issues", issues[:10], len(issues))
