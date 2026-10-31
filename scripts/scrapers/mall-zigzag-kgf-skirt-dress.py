"""zigzag.kr 대국민 소비축제 '스커트&원피스' 탭 (group_index=3).
api.zigzag.kr GraphQL(GetCmsProductsPresetProductCardItemList, products_preset_uuid=3065206f-..., group_index=3, limit=50, cursor 페이징)은
requests 직접 호출이 CloudFront 에서 빈 응답으로 막혀, 브라우저 세션(zigzag.kr 원점)에서 같은 API를 페이징해
압축 행(browser_rows.json)으로 저장했다. 이 스크립트는 그 캐시를 표준 출력으로 변환한다(재실행 가능).
행: [shop,title,catalog_id,img_path,review_score,review_count,price,final_price,discount_rate,has_coupon,is_zpay_discount,discount_title]"""
import json, os
SID = "mall-zigzag-kgf-skirt-dress"
ROOT = "E:/090_ETC/kf"
EVENT = "https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat=skirt-dress"
rows = json.load(open(f"{ROOT}/data/cache/html/{SID}/browser_rows.json", encoding="utf8"))
items, seen = [], set()
for s, title, cid, img, score, rc, price, fin, rate, coupon, zpay, dt in rows:
    if cid in seen: continue
    seen.add(cid)
    cond = []
    if coupon: cond.append("쿠폰 적용 가능")
    if zpay: cond.append("직진배송/제페이 할인 포함")
    if dt: cond.append(str(dt))
    items.append({
        "item_id": f"{SID}-{len(items)+1:04d}", "category": "mall", "source_id": SID, "unit": None,
        "vendor": s, "channel": "지그재그", "product": title, "model_code": None,
        "buy_url": f"https://store.zigzag.kr/app/catalog/products/{cid}?browsing_type=NATIVE_BROWSER",
        "image_url": ("https://cf.product-image.s.zigzag.kr/original/" + img + "?width=400&height=400&quality=80&format=jpeg") if img else None,
        "rating": float(score) if score is not None else None, "review_count": rc,
        "event_url": EVENT,
        "claimed_original_price": int(price) if price else None,
        "sale_price": int(fin) if fin else None,
        "claimed_discount_pct": float(rate) if rate is not None else None,
        "conditions": "; ".join(cond) or None,
        "sources": [EVENT],
    })
out = {"category": "mall", "source_id": SID, "collected_at": "2026-10-31", "items": items}
os.makedirs(f"{ROOT}/data/raw/catalog/mall", exist_ok=True)
json.dump(out, open(f"{ROOT}/data/raw/catalog/mall/{SID}.json", "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("saved", len(items))
