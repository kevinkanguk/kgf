# 베스트샵 이벤트 목록은 상품 가격표가 아닌 이미지 배너/쿠폰/라이브 알림 이벤트뿐이라 품목 0건 (창작 금지).
import json, datetime, os
SID = "appliance-lge-bestshop-events"
OUT = f"E:/090_ETC/kf/data/raw/catalog/appliance/{SID}.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "appliance", "source_id": SID,
           "collected_at": datetime.date(2026, 10, 31).isoformat(),
           "note": "event list (EV11089001 etc.) has image-banner/coupon/live-alert events only; no priced products in static HTML",
           "items": []}, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(0)
