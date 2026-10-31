CODEX.md 를 읽고 "2. 새 품목·소스 찾기" 단계만 수행하라. 커밋·push 는 하지 마라(스크립트가 한다).

- **먼저 이어서 하기:** data/kgf_scope.json 에 있지만 data/raw/catalog 에 결과가 없는(지난 실행에서 못 끝낸) 소스부터 수집한다. 그다음 새 소스를 찾는다.
- 2026 코리아 그랜드 페스티벌(코그페, 10.29~11.15) 참여 행사 중 data/sources/*.json 에 아직 없는 것을 웹에서 찾는다. 공식 사이트 koreagrandfestival.kr 의 참여기업·기획전 목록을 먼저 본다.
- 찾은 소스를 해당 카테고리 파일의 sources 배열에 추가한다(기존 항목은 고치지 않는다).
- 추가한 소스마다 agents/01_catalog.md 규칙대로 모든 품목을 data/raw/catalog/<category>/<source_id>.json 에 수집한다. 20개가 넘으면 scripts/scrapers/<source_id>.py 를 만들어 `py -I` 로 돌린다.
- 이번 실행은 새 소스 5개까지만. 로그인·캡차가 필요한 곳은 access: "login" 으로만 기록하고 수집하지 않는다.
- CODEX.md "수집 범위 규칙"을 반드시 지킨다: 코그페 표시가 있는 것만, 참여 업체 목록에서 출발, 품목마다 kgf_evidence, 할인가 0원(=할인 안 함) 제외, 별점 5점 환산.
- 새로 추가한 코그페 소스는 data/kgf_scope.json 의 sources 에도 넣는다 (tier·why·evidence). 넣지 않으면 인증표에 나오지 않는다.
- 숫자를 지어내지 않는다. 모르는 값은 null.
- 마지막에 한 줄 보고: `새 소스 N개, 새 품목 M개, 오류: ...`
