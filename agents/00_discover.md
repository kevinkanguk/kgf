# 00 Discover 에이전트 — 행사 소스 전수 목록

입력: 카테고리 1개 + 출발점 키워드
출력: data/sources/<category>.json  `{"category", "sources": [...]}`

source 항목: `{source_id, category, channel, url, kind, est_items, access, note}`
- source_id: `<category>-<channel영문>-<행사영문>` (소문자, 하이픈). 전역 유일.
- kind: listing(상품 목록 기획전) | brand_event(브랜드 자체 행사 페이지) | notice(가격표/보도자료)
- access: static(HTML/JSON으로 긁힘) | js(브라우저 필요) | login(로그인 필요 → 수집 제외)
- est_items: 목록 상품 수 추정치

할 일
- koreagrandfestival.kr(/discountcate, /sme, /event/regional) 의 모든 링크, 각 플랫폼 코그페 기획전의 **하위 탭·카테고리 페이지**까지 개별 소스로 쪼갠다.
- 정부 행사(농할, 수산대전, 소프라이즈, 김장, 동행축제, K-세일페스타, 숙박세일페스타, 듀티프리페스타)는 참여 몰/참여처마다 소스를 만든다.
- 소스 하나가 상품 수백 개면 탭/카테고리 단위로 나눈다(소스당 300개 이하 권장).
- 품목을 직접 수집하지는 않는다. 목록만.
