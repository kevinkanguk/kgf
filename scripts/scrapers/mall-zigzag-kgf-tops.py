import requests, json, os, time, datetime
SID = "mall-zigzag-kgf-tops"
ROOT = "E:/090_ETC/kf"
PRESET = "3065206f-34b0-46ae-9405-1b86396d8317"
GROUP = 4  # "상의"
EVENT = "https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat=tops"
API = "https://api.zigzag.kr/api/2/graphql/GetCmsProductCardItemList"
FR = """fragment P on CmsProductsPresetProductCardItemList { item_list { shop { id main_domain name } product { product_url title discount_rate price final_price catalog_product_id shop_product_no shop_id sellable_status has_coupon free_shipping zpay is_zpay_discount discount_info { title } } } total_count end_cursor exposure_order_type has_next_page }
query GetCmsProductCardItemList($input: CmsProductCardItemListInput!) { cms_product_card_item_list(input: $input) { ...P } }"""
cache = f"{ROOT}/data/cache/html/{SID}"
os.makedirs(cache, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Origin": "https://zigzag.kr", "Referer": "https://zigzag.kr/"}
rows, after, page, total = [], None, 0, None
while True:
    inp = {"products_preset_uuid": PRESET, "group_index": GROUP, "limit": 60, "after": after, "order_type": "MD_RECOMMEND"}
    r = requests.post(API, headers=H, json={"query": FR, "variables": {"input": inp}}, timeout=30)
    j = r.json()
    if "errors" in j: print(j["errors"]); break
    d = j["data"]["cms_product_card_item_list"]
    json.dump(j, open(f"{cache}/page{page:03d}.json", "w", encoding="utf8"), ensure_ascii=False)
    rows += d["item_list"]; total = d["total_count"]; page += 1
    print(page, len(rows), total)
    if not d["has_next_page"]: break
    after = d["end_cursor"]; time.sleep(0.3)
items, seen = [], set()
for it in rows:
    p, s = it["product"], it["shop"]
    key = (p["shop_id"], p["shop_product_no"], p["product_url"])
    if key in seen: continue
    seen.add(key)
    price, fin = p.get("price"), p.get("final_price")
    cond = []
    if p.get("has_coupon"): cond.append("쿠폰 적용 가능")
    if p.get("is_zpay_discount"): cond.append("직진배송/제페이 할인 포함")
    di = p.get("discount_info")
    if di and di.get("title"): cond.append(str(di["title"]))
    url = p["product_url"] or ""
    if url.startswith("/"): url = "https://zigzag.kr" + url
    pct = p.get("discount_rate")
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": s["name"], "channel": "지그재그", "product": p["title"], "model_code": None,
        "buy_url": url or f"https://zigzag.kr/catalog/products/{p['catalog_product_id']}",
        "event_url": EVENT,
        "claimed_original_price": int(price) if price else None,
        "sale_price": int(fin) if fin else None,
        "claimed_discount_pct": float(pct) if pct is not None else None,
        "conditions": "; ".join(cond) or None,
        "sources": [EVENT],
    })
out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "api_total_count": total, "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/mall", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/mall/{SID}.json", "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("saved", len(items), "of", total)
