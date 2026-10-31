import requests, re, json, html, os, time
SID = "auto-hyundai-certified-used"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/auto/{SID}.json"
BASE = "https://certified.hyundai.com/"
os.makedirs(CACHE, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest",
                  "Referer": BASE + "p/search/vehicle"})

def params(page, start):
    return dict(ntcSeq="", type="PLP", pageIdx=page, rowsPerPage=15, startNo=start, listCnt=15,
                sortType="basic", srchType="srchWord", searchWord="", sdStatCd="", selectedCodeList="",
                lowPrice=0, highPrice=0, lowMileage="", highMileage="", lowModelYear="", highModelYear="",
                carGubunList="", fuelList="", exteriorColorList="", optionList="", keywordList="",
                filtered="false", posNoList="")

def post(path, page, start, name):
    f = f"{CACHE}/{name}.html"
    if os.path.exists(f):
        return open(f, encoding="utf-8").read()
    for _ in range(3):
        r = S.post(BASE + path, data=params(page, start), timeout=60)
        if r.status_code == 200:
            r.encoding = "utf-8"
            open(f, "w", encoding="utf-8").write(r.text)
            return r.text
        time.sleep(2)
    return ""

def num(s):
    return int(s.replace(",", "")) if s else None

def parse(txt, seen, items):
    n = 0
    for blk in re.findall(r'<li class="type02">(.*?)</li>\s*(?=<li|</ul>|\s*$)', txt, re.S):
        pass
    parts = re.split(r'<li class="type02(?: soldout)?">', txt)[1:]
    for b in parts:
        m = re.search(r"goodsDeatil\(&#39;(\w+)&#39;\)", b)
        if not m: continue
        gid = m.group(1)
        if gid in seen: continue
        seen.add(gid)
        name = html.unescape(re.search(r'<div class="name">(.*?)</div>', b, re.S).group(1)).strip()
        img = re.search(r'<img src="([^"]+)"', b)
        drive = [html.unescape(x).strip() for x in re.findall(r"<span>(.*?)</span>", re.search(r'<div class="drive">(.*?)</div>', b, re.S).group(1))] if '<div class="drive">' in b else []
        pm = re.search(r'<span class="txt pay"><em>([\d,]+)</em>', b)
        dm = re.search(r'<del class="txt del"\s*><em>([\d,]+)</em>', b)
        sale = num(pm.group(1)) * 10000 if pm else None
        orig = num(dm.group(1)) * 10000 if dm else None
        flags = [html.unescape(x).strip() for x in re.findall(r'<span class="flag_[^"]*">(.*?)</span>', b)]
        pct = round((orig - sale) / orig * 100, 1) if orig and sale and orig > sale else None
        sold = 'soldout' in txt[max(0, txt.find(b) - 40):txt.find(b)]
        cond = " / ".join(x for x in [", ".join(drive), ", ".join(flags), "판매완료" if sold else ""] if x) or None
        brand = "제네시스" if re.search(r"\bG[V]?\d{2}\b|GV\d+|제네시스", name) else "현대"
        items.append(dict(
            item_id="", category="auto", source_id=SID, unit="1대(중고차)", vendor=brand,
            channel="현대 인증중고차", product=name, model_code=gid,
            buy_url=f"{BASE}p/goods/goodsDetail.do?goodsNo={gid}",
            image_url=img.group(1) if img else None, rating=None, review_count=None,
            event_url=BASE + "p/search/vehicle", claimed_original_price=orig, sale_price=sale,
            claimed_discount_pct=pct, conditions=cond,
            sources=[BASE + "p/search/vehicle", f"{BASE}p/goods/goodsDetail.do?goodsNo={gid}"]))
        n += 1
    return n

def main():
    items, seen = [], set()
    t = post("p/search/vehicle/list", 1, 0, "list_p1")
    total = num(re.search(r'id="totalVehicleCnt">([\d,]+)', t).group(1))
    parse(t, seen, items)
    page, start, empty = 1, 0, 0
    while len(items) < total and empty < 3:
        page += 1
        start += 14 if start == 0 else 15
        t = post("p/search/vehicle/element", page, start, f"el_p{page}")
        k = parse(t, seen, items)
        empty = empty + 1 if k == 0 else 0
    for i, it in enumerate(items, 1):
        it["item_id"] = f"{SID}-{i:04d}"
    json.dump(dict(category="auto", source_id=SID, collected_at="2026-10-31", total_reported=total, items=items),
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(total, len(items))

main()
