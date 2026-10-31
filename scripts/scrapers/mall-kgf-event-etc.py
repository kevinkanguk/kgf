import json, datetime
# 소스는 경품 이벤트 안내 페이지(소비쿠폰/추첨)이며 가격 품목이 없다. 빈 items 를 기록한다.
out = {"category": "mall", "source_id": "mall-kgf-event-etc",
       "collected_at": datetime.date(2026, 10, 31).isoformat(), "items": [],
       "issues": ["no priced items: sweepstakes/event notice page (https://koreagrandfestival.kr/event/etc)"]}
with open("E:/090_ETC/kf/data/raw/catalog/mall/mall-kgf-event-etc.json", "w", encoding="utf8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
