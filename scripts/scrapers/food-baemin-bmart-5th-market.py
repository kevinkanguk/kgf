# B마트 11월 5일장: 앱 전용, woowahan.com 은 403 -> 웹에서 품목 목록 수집 불가. 빈 결과를 기록한다.
import json, os
out = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'catalog', 'food', 'food-baemin-bmart-5th-market.json')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump({"category": "food", "source_id": "food-baemin-bmart-5th-market", "collected_at": "2026-10-31",
               "note": "needs_browser/app-only: no public item list; woowahan.com 403", "items": []}, f, ensure_ascii=False, indent=2)
