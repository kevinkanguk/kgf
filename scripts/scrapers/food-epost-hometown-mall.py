import re, json, os, time, html, datetime, requests
SID = "food-epost-hometown-mall"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
B = "https://mall.epost.go.kr"
s = requests.Session(); s.headers.update(UA)

def get(url, cache):
    p = f"{CACHE}/{cache}"
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    for i in range(4):
        try:
            r = s.get(url, timeout=40)
            if r.status_code == 200:
                r.encoding = "utf-8"
                open(p, "w", encoding="utf-8").write(r.text); return r.text
        except Exception: pass
        time.sleep(2)
    return ""

main = get(B + "/fo/main/main.do", "main.html")
leaves = re.findall(r"fn_categoryAllMenuLink\('(\d+)', '(\d+)', 3\)\">([^<]*)<", main)
leaves = [l for l in leaves if (l[0][:3] in ("101","102","103","104","105","111")) and not l[0].startswith("105202")]
seen = {}; issues = []
li_re = re.compile(r"<li>\s*<a href=\"javascript:fn_goodsDetailView\('([^']+)','[^']*','[^']*','([^']*)','(\d*)'\);\">(.*?)</li>", re.S)
for cc, hc, nm in leaves:
    prev = None
    for pg in range(1, 80):
        url = f"{B}/display/viewSCategory.do?ctgryCd={cc}&hrnkCtgryCd={hc}&currentPage={pg}&rowsperPage=45&goodsStus=01&orderBy=PUCHAS"
        t = get(url, f"c{cc}_p{pg}.html")
        if not t: issues.append(f"fetch fail {cc} p{pg}"); break
        blk = t[t.find('id="goodsList"'):]
        its = li_re.findall(blk)
        codes = [i[0] for i in its]
        if not codes or codes == prev: break
        prev = codes
        for code, pav, ctg, body in its:
            if code in seen: continue
            title = re.search(r'alt="([^"]*)"\s*/>\s*</div>', body)
            title = html.unescape(title.group(1)) if title else None
            tit = re.search(r'<p class="tit">\s*(.*?)</p>', body, re.S)
            product = html.unescape(re.sub(r"\s+", " ", tit.group(1)).strip()) if tit else title
            unit = re.search(r'</p>\s*<span>\s*([^<]*?)\s*</span>', body)
            pr = re.search(r'<div class="price">(.*?)</div>', body, re.S)
            orig = sale = pct = None
            if pr:
                ph = pr.group(1)
                ph = re.sub(r"<[^>]+>(?=[\d,]+<)", "", ph) if False else ph
                pm = re.search(r"<em>(\d+)</em>%", ph)
                ph2 = re.sub(r"<em>\d+</em>%", "", ph)
                nums = [int(x.replace(",", "")) for x in re.findall(r"([\d,]{3,})(?:</em>)?원", ph2)]
                if pm and len(nums) >= 2:
                    orig, sale, pct = nums[0], nums[1], float(pm.group(1))
                elif nums:
                    sale = nums[0]
            tips = re.findall(r'<img src="[^"]*icon_tip[^"]*" alt="([^"]*)"', body)
            seen[code] = dict(code=code, pav=pav, ctg=ctg, product=product, unit=unit.group(1) if unit else None,
                              orig=orig, sale=sale, pct=pct, tips=tips, cat=nm)
    print(cc, nm, len(seen), flush=True)

items = []
for n, (code, d) in enumerate(seen.items(), 1):
    url = f"{B}/fo/goods/goodsDetailView.do?goodsCd={code}&pavlnDivCd={d['pav']}&ctgryCd={d['ctg']}"
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "food", "source_id": SID,
        "unit": d["unit"], "vendor": "우체국쇼핑", "channel": "우체국쇼핑 지역특산물",
        "product": d["product"], "model_code": code, "buy_url": url,
        "event_url": B + "/fo/main/main.do",
        "claimed_original_price": d["orig"], "sale_price": d["sale"], "claimed_discount_pct": d["pct"],
        "conditions": ", ".join(d["tips"]) or None, "sources": [url], "category_path": d["cat"]})
out = {"category": "food", "source_id": SID, "collected_at": datetime.date.today().isoformat(), "items": items}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("count", len(items), issues)
