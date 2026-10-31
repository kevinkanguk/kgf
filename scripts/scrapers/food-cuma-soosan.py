# -*- coding: utf-8 -*-
"""food-cuma-soosan: cuma.co.kr 대한민국수산대전 (main=270 -> display category 271). Run: py -I scripts/scrapers/food-cuma-soosan.py"""
import json, os, re, datetime, requests

SID = "food-cuma-soosan"
ROOT = "E:/090_ETC/kf"
API = "https://service.cuma.co.kr"
H = {"User-Agent": "Mozilla/5.0"}
EVENT_URL = "https://www.cuma.co.kr/?main=270"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/food/{SID}.json"


def get(path):
    r = requests.get(API + path, headers=H, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    groups = get("/v4/display-category/groups/270?take=100")
    gids = [g["id"] for g in groups["list"]]
    prods, seen, issues = [], set(), []
    for gid in gids:
        cursor = None
        while True:
            q = f"/v4/display-category/{gid}/display-products?take=50" + (f"&cursor={cursor}" if cursor else "")
            d = get(q)
            for p in d["list"]:
                if p["id"] not in seen:
                    seen.add(p["id"]); prods.append(p)
            cursor = d.get("page", {}).get("nextPage")
            if not cursor:
                break
    json.dump(prods, open(f"{CACHE}/list.json", "w", encoding="utf-8"), ensure_ascii=False)
    items = []
    for i, p in enumerate(prods, 1):
        pid = p["id"]
        det = get(f"/v1/products/{pid}")
        opt = get(f"/v2/products/{pid}/options")
        json.dump({"detail": det, "options": opt}, open(f"{CACHE}/p{pid}.json", "w", encoding="utf-8"), ensure_ascii=False)
        pp = det["productPrice"]
        combos = opt["productDetail"]["productOptionCombinations"]
        # cheapest purchasable option = representative unit
        best = None
        for c in combos:
            sp = c["productOptionPrice"].get("specialSalePrice")
            if sp is None: continue
            if best is None or sp < best[0]:
                best = (sp, c)
        unit = None
        if best:
            unit = re.sub(r"^\d+월\s*\d+일\(.\)\s*출고/", "", best[1]["name"])
        sale = pp.get("specialSalePrice")
        lst = pp.get("listPrice")
        pct = round((1 - sale / lst) * 100, 1) if sale and lst else None
        name = re.sub(r"^\[대한민국수산대전\]\s*", "", det["name"]).strip()
        items.append({
            "item_id": f"{SID}-{i:04d}",
            "category": "food",
            "source_id": SID,
            "unit": unit,
            "vendor": (det.get("distributor") or p.get("distributor") or {}).get("name") or "쿠마",
            "channel": "쿠마(cuma) 대한민국수산대전",
            "product": name,
            "model_code": None,
            "buy_url": f"https://www.cuma.co.kr/product/{pid}",
            "image_url": det.get("representImageBucketUrl") or p.get("representImageBucketUrl"),
            "rating": det.get("scoreAverage"),
            "review_count": det.get("reviewCount"),
            "event_url": EVENT_URL,
            "claimed_original_price": lst,
            "sale_price": sale,
            "claimed_discount_pct": pct,
            "conditions": f"API productPrice: price={pp.get('price')}, listPrice={lst}, specialSalePrice={sale}; 대표옵션(최저가) 기준" + (f", 기타 옵션 {len(combos)}종" if len(combos) > 1 else "") + f"; 배송비 {det.get('productShippingFee',{}).get('shippingFee')}원 별도",
            "sources": [f"{API}/v1/products/{pid}", f"{API}/v4/display-category/{gids[0]}/display-products", f"https://www.cuma.co.kr/product/{pid}"],
        })
    out = {"category": "food", "source_id": SID,
           "collected_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"), "items": items}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(len(items), "items")


if __name__ == "__main__":
    main()
