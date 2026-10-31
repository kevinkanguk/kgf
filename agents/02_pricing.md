# 02 Pricing 에이전트 — 품목 묶음의 주장 정가/할인가 + 최근 2개월 가격

입력: data/raw/catalog/<category>/<source_id>.json 의 items[start:end] (호출자가 범위 지정)
출력: data/raw/prices/<category>/<source_id>__<chunk>.json (해당 범위 전 항목 + 가격 필드 보강)

할 일
- claimed_original_price / sale_price / conditions 재확인.
- 최근 2개월(2026-09-01 ~ 10-28):
  - 공산품(모델명 있음): 다나와 가격변동, 에누리 가격추이, 폴센트(쿠팡), 네이버 가격비교, 같은 몰 과거가.
  - 신선식품·농수축산: 같은 몰 동일상품 과거가가 없으면 KAMIS 소매가격(같은 품목·등급·단위로 환산)을 쓴다.
    먼저 data/cache/price_ref/ 에 같은 품목 시세가 있는지 보고, 없으면 조회해서 저장(다른 에이전트 재사용).
    단위가 다르면 unit 기준으로 환산하고 price_history_note 에 환산식을 남긴다.
  - 숙박·항공: 같은 상품의 9~10월 가격 기록이 없으면 null + note.
- price_60d_low(최저가), price_60d_typical(중앙값/가장 오래 유지된 가격), price_history_note, confidence.
- 반복 조회가 많으면 스크립트(scripts/scrapers/)로 처리해도 된다.
