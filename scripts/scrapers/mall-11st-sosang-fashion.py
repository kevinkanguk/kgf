import re, json, os, time, datetime, requests
SID = "mall-11st-sosang-fashion"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EXHS = {"2211141": "2026 소상공인 온라인 의류/유아용품/장난감 기획전"}
UA = {"User-Agent": "Mozilla/5.0"}
os.makedirs(CACHE, exist_ok=True)
S = requests.Session(); S.headers.update(UA)

def num(s):
    s = re.sub(r"[^\d]", "", str(s or ""))
    return int(s) if s else None

items, seen, issues = [], {}, []
for exh, title in EXHS.items():
    url = f"https://plan.11st.co.kr/plan/front/exhibitions/{exh}/detail"
    html = S.get(url, timeout=30).text
    open(f"{CACHE}/e{exh}.html", "w", encoding="utf8").write(html)
    themes = {}
    for m in re.finditer(r'<h4 class="plan_subject_bar[^"]*" name="themeBar" id="P_(\d+)">(.*?)</h4>', html):
        themes[m.group(1)] = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    for idx, name in themes.items():
        if not re.search(rf'name="themeNo_{idx}" value="1757690"', html): continue
        g = lambda k: (re.search(rf'name="{k}_{idx}" value="([^"]*)"', html) or [None, ""])[1]
        data = dict(templateType=g("templateType"), page=0, size=g("countOfProducts"), themeIndex=idx,
                    productSortCode=g("productSortCode"), deliveryType="", isUsableProductNetFunnel="false",
                    recommendedProducts="", recommendRequestId="", isAcme=g("isAcme"))
        r = S.post(f"https://plan.11st.co.kr/plan/front/exhibitions/{exh}/themes/{g('themeNo')}/products",
                   data=data, headers={"Referer": url, "X-Requested-With": "XMLHttpRequest"}, timeout=30)
        try:
            j = r.json()
        except Exception:
            issues.append(f"{exh} theme {idx} {name}: bad response {r.status_code}"); continue
        open(f"{CACHE}/t{exh}_{idx}.json", "w", encoding="utf8").write(r.text)
        ps = j.get("themeProducts") or []
        exp = num(g("countOfProducts"))
        if exp and len(ps) < exp: issues.append(f"{exh} theme {idx} {name}: got {len(ps)} of {exp}")
        for p in ps:
            pn = p["productNo"]
            if pn in seen: continue
            seen[pn] = 1
            sell, fin = num(p.get("sellPrice")), num(p.get("finalPrice"))
            rate = p.get("discountRate")
            sc = p.get("satisfactionScore")
            items.append(dict(
                item_id=None, category="mall", source_id=SID, unit=None,
                vendor=None, channel="11번가", product=p["productName"], model_code=None,
                buy_url=p["productLink"], image_url=p.get("productImage"),
                rating=round(sc / 20, 2) if sc and num(p.get("reviewCount")) else None,
                review_count=num(p.get("reviewCount")),
                event_url=url,
                claimed_original_price=sell if p.get("showSellPrice") else None,
                sale_price=fin,
                claimed_discount_pct=float(rate) if p.get("showDiscountRate") and rate else None,
                conditions=None, sources=[url], _theme=f"{title} / {name}"))
    time.sleep(0.3)
for i, it in enumerate(items, 1):
    it["item_id"] = f"{SID}-{i:04d}"
    it["vendor"] = "11번가"
    it["conditions"] = "기획전 주제: " + it.pop("_theme")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="mall", source_id=SID, collected_at=datetime.date(2026,10,31).isoformat(), items=items),
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items), issues)
