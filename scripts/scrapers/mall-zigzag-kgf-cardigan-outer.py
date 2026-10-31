import json, os, urllib.request, datetime
SID = "mall-zigzag-kgf-cardigan-outer"
ROOT = "E:/090_ETC/kf"
EVENT = "https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat=cardigan-outer"
PRESET = "3065206f-34b0-46ae-9405-1b86396d8317"
GROUP = 0
URL = "https://api.zigzag.kr/api/2/graphql/GetCmsProductsPresetProductCardItemList"
Q = ("fragment P on CmsProductsPresetProductCardItemList { item_list { shop { id main_domain name } product { image_url product_url title discount_rate free_shipping has_coupon price final_price max_price_with_currency { price_without_decimal } catalog_product_id shop_product_no shop_id sellable_status discount_info { title } } } total_count end_cursor has_next_page } "
     "query GetCmsProductsPresetProductCardItemList($input: CmsProductsPresetProductCardItemListSearchInput!) { cms_products_preset_product_card_item_list(input: $input) { ...P } }")
# api.zigzag.kr 는 requests/urllib 직접 호출 시 빈 응답 -> 브라우저(zigzag.kr 탭)에서 GraphQL(위 Q, group_index=0, limit=50, after=end_cursor 반복)을
# 호출해 받은 item_list 를 api_items.json 으로 캐시하고, 이 스크립트는 캐시를 파싱한다.
raw = json.load(open(f"{ROOT}/data/cache/html/{SID}/api_items.json", encoding="utf-8"))
items, seen = [], set()
for it in raw:
    p, s = it["product"], it["shop"]
    key = p["product_url"].split("?")[0]
    if key in seen: continue
    seen.add(key)
    sale = p["final_price"]
    orig = (p.get("max_price_with_currency") or {}).get("price_without_decimal")
    orig = orig if orig else p.get("price")
    if orig and sale and orig < sale: orig = None
    cond = []
    if p.get("has_coupon"): cond.append("쿠폰 적용가 가능")
    if (p.get("discount_info") or {}).get("title"): cond.append(p["discount_info"]["title"])
    n = len(items) + 1
    items.append({
        "item_id": f"{SID}-{n:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": s["name"], "channel": "지그재그", "product": p["title"],
        "model_code": p["product_url"].split("/products/")[-1].split("?")[0],
        "buy_url": p["product_url"], "event_url": EVENT,
        "claimed_original_price": orig, "sale_price": sale,
        "claimed_discount_pct": p.get("discount_rate"),
        "conditions": ", ".join(cond) or None,
        "sources": [EVENT, URL],
    })
out = {"category": "mall", "source_id": SID, "collected_at": datetime.date(2026,10,31).isoformat(), "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/mall", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/mall/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(raw), len(items))
