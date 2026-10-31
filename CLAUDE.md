# 코리아 그랜드 페스티벌(코그페) 할인 검증 하네스

## 목적
2026 코리아 그랜드 페스티벌(2026-10-29 ~ 11-15, 약 4만 개 기업, 공식 사이트 https://koreagrandfestival.kr)에서
업체가 주장하는 "정가 → 할인가"가 실제로 얼마의 할인인지, 최근 2개월(약 2026-09-01 ~ 10-28) 실거래가와 비교해 검증한다.
**행사 품목은 대표 몇 개가 아니라 가능한 한 전부 수집한다** (기획전 목록·페이지네이션·하위 탭까지).

## 파이프라인 (에이전트별 역할은 agents/*.md)
0. 00_discover : 카테고리별 행사 소스(기획전/목록 페이지) 전수 목록 → data/sources/<category>.json
1. 01_catalog  : 소스 1개의 모든 품목 추출          → data/raw/catalog/<category>/<source_id>.json
2. 02_pricing  : 품목 묶음(chunk)별 2개월 가격     → data/raw/prices/<category>/<source_id>__<chunk>.json
4. 04_verify   : 묶음별 독립 재검증                → data/verified/<category>/<source_id>__<chunk>.json
6. 06_browser_fallback : 크롤링 실패 품목 브라우저 확인 (같은 verified 파일 갱신)
3. 03_analysis : scripts/build_report.py + 결론     → output/
5. 05_html_qa  : output/index.html 테스트          → output/qa_report.md

## 데이터 규칙 (모든 에이전트 공통)
- 스키마: schema/item.schema.json. 필드명을 바꾸지 말 것.
- 가격은 원(KRW) 정수. 모르면 null. **추정·창작 금지** — 출처 URL이 없는 숫자는 넣지 않는다.
- 모든 가격 값에는 출처(sources[])를 남긴다.
- buy_url 은 실제 구매 가능한 상품 페이지 URL(검색결과보다 상품 상세 우선).
- 목록에 있으면 image_url(대표 이미지 절대 URL), rating(5점 만점 환산), review_count 도 반드시 채운다. 없으면 null.
- item_id 는 `<source_id>-<4자리번호>` (예: food-11st-nonghal-0001). 단계 간 동일하게 유지.
- 품목이 많은 페이지는 사람이 읽지 말고 스크립트로 긁는다: scripts/scrapers/<source_id>.py (py, requests/정규식/사이트 JSON API).
  다운로드한 HTML/JSON 은 data/cache/html/ 에 저장하고 스크립트는 scripts/scrapers/ 에만 둔다. 실행은 `py -I`.
- 신선식품 등 공통 시세는 data/cache/price_ref/<commodity>_<unit>.json 에 저장해 다른 에이전트가 재사용한다(있으면 먼저 읽기).
- 기준일: 2026-10-31. 자동차는 9~10월 월별 프로모션과 비교(비교기준 다름).
- JSON 파일은 UTF-8, 들여쓰기 2칸, 최상위는 `{"category": "...", "source_id": "...", "collected_at": "...", "items": [...]}`.
- 로그인·CAPTCHA·결제 화면은 우회하지 않는다. 건너뛰고 issues 에 기록.
