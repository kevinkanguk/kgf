# 05 HTML QA 에이전트 — 결과 페이지 동작 테스트

입력: output/index.html
출력: output/qa_report.md

할 일
- `py scripts/qa_html.py` 실행(정적 검사: 행 수 = 데이터 수, 필수 컬럼, 모든 행에 구매링크, 계산값 재검산).
- 브라우저로 output/index.html 을 열어 확인: 렌더링, 검색/카테고리 필터, 컬럼 정렬, 판정 배지, 모바일 폭(375px).
- 구매링크 샘플(카테고리별 2개 이상) 실제로 열리는지 확인. 깨진 링크는 목록화.
- 문제는 qa_report.md 에 PASS/FAIL 목록으로. 스크립트/HTML 버그면 scripts/build_report.py 를 직접 고치고 재생성.
