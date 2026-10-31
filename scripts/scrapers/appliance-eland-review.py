import re, json, os, html, time, datetime, requests
SID = "appliance-eland-review"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/appliance/{SID}.json"
EVENT = "https://www.etlandmall.co.kr/pc/event/planProductList.do?PLN_MST_IDX=12186"
UA = {"User-Agent": "Mozilla/5.0", "Referer": EVENT, "X-Requested-With": "XMLHttpRequest"}
os.makedirs(CACHE, exist_ok=True)

def get_plan():
    p = f"{CACHE}/plan.html"
    if not os.path.exists(p):
        open(p, "w", encoding="utf-8").write(requests.get(EVENT, headers=UA, timeout=60).text)
    return open(p, encoding="utf-8").read()

def get_group(g, col):
    p = f"{CACHE}/g{g}.html"
    if not os.path.exists(p) or os.path.getsize(p) < 100:
        for _ in range(3):
            try:
                r = requests.post("https://www.etlandmall.co.kr/pc/event/planProductDetailListAjax.do", headers=UA, timeout=90,
                    data={"PLN_MST_IDX": "12186", "PLN_GRP_COL": col, "PLN_GRP_IDX": g, "prePlan": "", "PLN_MST_SPECIAL_YN": "N",
                          "PLN_MST_PRD_DPL_YN": "Y", "PLN_TIME_SALE": "N", "PLN_POINT_SALE_YN": "N", "chlCode": ""})
                open(p, "w", encoding="utf-8").write(r.text); break
            except Exception as e:
                time.sleep(3)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

def parse(h, group):
    items = []
    for blk in re.split(r'(?=<a class="components_product_list")', h)[1:]:
        blk = blk.split("</a>")[0]
        m = re.search(r'prdMstCd=([A-Za-z0-9]+)', blk)
        if not m: continue
        code = m.group(1)
        name = re.search(r'components_product_name">\s*(.*?)</p>', blk, re.S)
        name = html.unescape(re.sub(r'\s+', ' ', name.group(1))).strip() if name else None
        img = re.search(r'<img\s+src="([^"]+)"', blk)
        price = re.search(r'priceGroup_price">\s*([\d,]+)', blk)
        pct = re.search(r'priceGroup_sale">\s*([\d.]+)%', blk)
        star = re.search(r'reivewGroup_star">.*?</span>\s*([\d.]+)\s*</span>', blk, re.S)
        rc = re.search(r'reivewGroup_total">\(([\d,]+)\)', blk)
        cond = []
        pt = re.search(r'([\d,]+)P 적립', blk)
        if pt: cond.append(f"e.POINT {pt.group(1)}P 적립")
        if "benefit_coupon" in blk:
            c = re.search(r'benefit_coupon">(.*?)</li>', blk, re.S)
            t = html.unescape(re.sub(r'<[^>]+>|\s+', ' ', c.group(1))).strip() if c else ""
            cond.append("쿠폰: " + t if t else "쿠폰 있음")
        if "무료배송" in blk: cond.append("무료배송")
        if "online_exclusive" in blk: cond.append("온라인 단독")
        items.append(dict(code=code, name=name, img=img.group(1) if img else None,
            price=int(price.group(1).replace(",", "")) if price else None,
            pct=float(pct.group(1)) if pct else None,
            rating=float(star.group(1)) if star else None,
            rc=int(rc.group(1).replace(",", "")) if rc else None,
            cond=cond, group=group))
    return items

def main():
    plan = get_plan()
    groups = []
    for m in re.finditer(r'<dt id="focusProduct\d+" planGrpIdx="(\d+)" planGrpCol="(\d+)">\s*<strong>(.*?)</strong>', plan, re.S):
        groups.append((m.group(1), m.group(2), re.sub(r'<[^>]+>|\s+', ' ', m.group(3)).strip()))
    raw = []
    for g, col, title in groups:
        raw += parse(get_group(g, col), title)
    seen, items = set(), []
    for r in raw:
        if r["code"] in seen: continue
        seen.add(r["code"])
        name = r["name"] or ""
        vm = re.match(r'\[([^\]/]+)(?:/([^\]]+))?\]\s*(.*)', name)
        vendor = vm.group(1).strip() if vm else "이랜드몰"
        model = vm.group(2).strip() if vm and vm.group(2) else None
        img = r["img"]
        if img and img.startswith("/"): img = "https://www.etlandmall.co.kr" + img
        conds = list(r["cond"]); 
        if r["group"]: conds.append("그룹: " + r["group"])
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "appliance", "source_id": SID,
            "unit": None, "vendor": vendor, "channel": "이랜드몰", "product": name, "model_code": model,
            "buy_url": f"https://www.etlandmall.co.kr/pc/product/product.do?prdMstCd={r['code']}",
            "image_url": img, "rating": r["rating"], "review_count": r["rc"], "event_url": EVENT,
            "claimed_original_price": None, "sale_price": r["price"], "claimed_discount_pct": r["pct"],
            "conditions": "; ".join(conds) or None,
            "sources": [EVENT]})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"category": "appliance", "source_id": SID, "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
               "groups": len(groups), "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(len(groups), "groups,", len(raw), "raw,", len(items), "items")
main()
