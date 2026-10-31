# 01 Catalog 에이전트 — 소스 1개의 모든 품목 추출

입력: source 1개 (data/sources/<category>.json 의 항목)
출력: data/raw/catalog/<category>/<source_id>.json

할 일
- 해당 소스 페이지의 **모든 품목**을 수집한다. 페이지네이션·더보기·하위 탭 끝까지.
- 품목이 20개를 넘으면 직접 읽지 말고 scripts/scrapers/<source_id>.py 를 작성해 긁는다.
  - 페이지가 내부적으로 부르는 JSON API(네트워크 요청)를 찾으면 그걸 쓰는 게 가장 정확하다.
  - 스크립트는 결과를 위 출력 경로에 바로 쓰게 하고, 재실행 가능하게 둔다.
- 품목별: vendor, channel, product, model_code, unit(용량/수량), buy_url, **image_url(대표 이미지), rating(5점 환산 별점), review_count**, event_url, claimed_original_price, sale_price, claimed_discount_pct, conditions, sources.
- access=js 라서 정적으로 안 긁히면 수집 가능한 만큼 하고 issues 에 "needs_browser" 기록.
- 숫자 창작 금지. 못 찾은 값은 null.
