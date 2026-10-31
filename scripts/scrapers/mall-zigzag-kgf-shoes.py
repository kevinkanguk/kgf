import json, os, subprocess, datetime, time
SID = "mall-zigzag-kgf-shoes"
ROOT = "E:/090_ETC/kf"
PRESET = "3065206f-34b0-46ae-9405-1b86396d8317"
GROUP = 9  # shoes
EVENT = "https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat=shoes"
URL = "https://api.zigzag.kr/api/2/graphql/GetCmsProductsPresetProductCardItemList"
Q = ("fragment P on CmsProductsPresetProductCardItemList { item_list { shop { id main_domain name } product { image_url product_url title discount_rate free_shipping has_coupon price final_price review_score review_count max_price_with_currency { price_without_decimal } catalog_product_id shop_product_no shop_id sellable_status discount_info { title } } } total_count end_cursor has_next_page } "
     "query GetCmsProductsPresetProductCardItemList($input: CmsProductsPresetProductCardItemListSearchInput!) { cms_products_preset_product_card_item_list(input: $input) { ...P } }")
cache = f"{ROOT}/data/cache/html/{SID}"
os.makedirs(cache, exist_ok=True)
# api.zigzag.kr 는 python requests(Mozilla UA) 에 빈 응답 -> curl 사용
rows, after, page, total = [], None, 0, None
while True:
    body = json.dumps({"query": Q, "variables": {"input": {"products_preset_uuid": PRESET, "group_index": GROUP, "limit": 50, "after": after}}})
    bf = f"{cache}/req.json"; open(bf, "w", encoding="utf8").write(body)
    out = subprocess.run(["curl", "-s", "-m", "40", "-X", "POST", URL, "-H", "content-type: application/json", "-H", "origin: https://zigzag.kr", "--data-binary", "@" + bf], capture_output=True).stdout
    j = json.loads(out.decode("utf8"))
    if "errors" in j: print(j["errors"]); break
    d = j["data"]["cms_products_preset_product_card_item_list"]
    json.dump(j, open(f"{cache}/page{page:03d}.json", "w", encoding="utf8"), ensure_ascii=False)
    rows += d["item_list"]; page += 1
    print(page, len(rows), d["total_count"], d["has_next_page"])
    if not d["has_next_page"]: break
    after = d["end_cursor"]; time.sleep(0.3)
items, seen = [], set()
for it in rows:
    p, s = it["product"], it["shop"]
    key = p["product_url"].split("?")[0]
    if key in seen: continue
    seen.add(key)
    sale = p["final_price"]
    orig = (p.get("max_price_with_currency") or {}).get("price_without_decimal") or p.get("price")
    if orig and sale and orig < sale: orig = None
    cond = []
    if p.get("has_coupon"): cond.append("쿠폰 적용가 가능")
    if (p.get("discount_info") or {}).get("title"): cond.append(p["discount_info"]["title"])
    rs, rc = p.get("review_score"), p.get("review_count")
    if rs is not None:
        rs = float(rs)
        if rs > 5: rs = round(rs / 20, 2) if rs > 10 else round(rs / 2, 2)
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": s["name"], "channel": "지그재그", "product": p["title"],
        "model_code": p["product_url"].split("/products/")[-1].split("?")[0],
        "buy_url": p["product_url"], "image_url": p.get("image_url"),
        "rating": rs, "review_count": int(rc) if rc is not None else None,
        "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": p.get("discount_rate"),
        "conditions": ", ".join(cond) or None,
        "sources": [EVENT, URL],
    })
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/mall", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/mall/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("raw", len(rows), "saved", len(items))
