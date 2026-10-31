import json, re, os, datetime, requests
SID = "mall-11st-sosang-beauty"
ROOT = "E:/090_ETC/kf"
EV = "https://plan.11st.co.kr/plan/front/exhibitions/2211141/themes/1757689"
r = requests.post(EV + "/products", headers={"Referer": EV, "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0"}, timeout=30)
r.raise_for_status()
os.makedirs(f"{ROOT}/data/cache/html/{SID}", exist_ok=True)
open(f"{ROOT}/data/cache/html/{SID}/p1.json", "w", encoding="utf-8").write(r.text)
num = lambda s: int(re.sub(r"[^\d]", "", s)) if s and re.sub(r"[^\d]", "", s) else None
items = []
for i, p in enumerate(r.json()["themeProducts"], 1):
    sell, fin = num(p.get("sellPrice")), num(p.get("finalPrice"))
    sc = p.get("satisfactionScore")
    cond = []
    if p.get("deliveryInfo"): cond.append(p["deliveryInfo"])
    pr = (p.get("benefit") or {}).get("pntRsvRt")
    if pr: cond.append("적립 " + pr)
    try: dr = float(p.get("discountRate")) if p.get("discountRate") else None
    except ValueError: dr = None
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": "11번가 소상공인 뷰티/헬스", "channel": "11번가 소상공인 온라인 판매전",
        "product": p["productName"], "model_code": str(p["productNo"]),
        "buy_url": p["productLink"], "image_url": p.get("productImage"),
        "rating": round(sc / 20, 2) if isinstance(sc, (int, float)) and sc else None,
        "review_count": num(p.get("reviewCount")), "event_url": EV,
        "claimed_original_price": sell, "sale_price": fin, "claimed_discount_pct": dr,
        "conditions": ", ".join(cond) or None, "sources": [EV + "/products", p["productLink"]],
    })
out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/mall", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/mall/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items))
