import requests, json, re, os, time, datetime
SID = "mall-ssg-sosang-drink-dairy"
DISP = "6000465146"; SITE = "7018"; THEME = "7000886055"  # 음료/커피/유제품
ROOT = "E:/090_ETC/kf"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
CACHE = f"{ROOT}/data/cache/html/{SID}"
EVENT = f"https://www.ssg.com/plan/planShop.ssg?dispCmptId={DISP}#tab=drink-dairy"
API = "https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain"
H = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://www.ssg.com', 'Referer': 'https://www.ssg.com/', 'Content-Type': 'application/json'}
UNIT = re.compile(r'(\d+(?:\.\d+)?\s*(?:kg|g|ml|mL|L|l|개입|개|입|팩|봉|포|매|ea|EA|구)(?:\s*[xX*]\s*\d+\s*(?:개|입|팩|봉|포)?)?)\s*$')

def toint(v):
    try:
        n = int(str(v).replace(',', ''))
        return n if n > 0 else None
    except Exception:
        return None

def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    raw, page = [], 1
    while True:
        b = {"common": {"aplVer": "", "osCd": "", "ts": datetime.datetime.now().strftime("%Y%m%d%H%M%S"), "mobilAppNo": "99", "dispDvicDivCd": "10", "viewSiteNo": SITE},
             "params": {"dispCmptId": DISP, "inflowSiteNo": SITE, "themeId": THEME, "page": page, "pageSize": 30}}
        for _ in range(3):
            r = requests.post(API, json=b, headers=H, timeout=30)
            if r.status_code == 200: break
            time.sleep(2)
        r.raise_for_status()
        open(f"{CACHE}/page{page:03d}.json", "w", encoding="utf8").write(r.text)
        d = r.json()["data"]
        raw += d["itemList"]
        if not d.get("hasNext") or not d["itemList"] or page > 100: break
        page += 1; time.sleep(0.3)
    items, seen = [], set()
    for x in raw:
        iid = x["itemId"]
        if iid in seen: continue
        seen.add(iid)
        name = x["itemNm"].strip()
        sale = toint(x.get("displayPrc"))
        orig = toint(x.get("strikeOutPrc"))
        pi = (x.get("priceInfo") or {})
        rate = toint((pi.get("raw") or {}).get("discountRate"))
        cpn = (pi.get("summary") or {}).get("cpnTxt") or ""
        cond = []
        if cpn: cond.append(cpn)
        if x.get("minOnetOrdPsblQty") not in (None, "", "1"): cond.append("최소주문 " + x["minOnetOrdPsblQty"] + "개")
        if x.get("soldOutYn") == "Y": cond.append("품절")
        m = UNIT.search(name)
        rc = toint(x.get("recomRegCnt")) or 0
        try: rating = float(x["recompPoint"]) if rc else None
        except Exception: rating = None
        link = x.get("itemLnkd") or ""
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID,
            "unit": m.group(1) if m else None,
            "vendor": (x.get("brandNm") or x.get("splVenNm") or "").strip() or "SSG",
            "channel": "SSG닷컴 소상공인 브랜드관(음료/커피/유제품)",
            "product": name, "model_code": None,
            "buy_url": link or f"https://www.ssg.com/item/itemView.ssg?itemId={iid}",
            "image_url": x.get("twiceItemImgUrl") or x.get("itemImgUrl") or None,
            "rating": rating, "review_count": rc if x.get("recomRegCnt") not in (None, "") else None,
            "event_url": EVENT,
            "claimed_original_price": orig, "sale_price": sale,
            "claimed_discount_pct": float(rate) if rate else None,
            "conditions": ", ".join(cond) or None,
            "price_60d_low": None, "price_60d_typical": None, "price_history_note": None,
            "sources": [EVENT, API],
            "verify_status": None, "verify_note": None, "confidence": None})
    out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items}
    json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    print(len(raw), len(items))
if __name__ == "__main__": main()
