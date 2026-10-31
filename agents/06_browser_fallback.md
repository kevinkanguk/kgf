# 06 Browser Fallback 에이전트 — 크롤링 실패 품목 브라우저 직접 확인

입력: data/verified/*.json 중 price_60d_typical / sale_price 가 null 이거나 verify_status = unverifiable 인 품목
출력: 같은 파일을 갱신 (verify_note 에 "browser:" 접두어로 확인 내역)

할 일
- 내장 브라우저(mcp__Claude_Browser__*)로 JS 렌더링 페이지를 직접 연다:
  다나와 상품 상세의 "가격변동" 그래프(3개월), 에누리 가격추이, 폴센트, 행사 기획전/상품 상세.
- get_page_text / read_page 로 숫자를 읽고, 그래프처럼 텍스트로 안 나오는 값은 screenshot/zoom 으로 읽는다.
- 읽은 값의 근거(페이지 URL + 확인 방식 "screenshot"/"text")를 sources·verify_note 에 남긴다.
- 브라우저 창은 하나를 공유하므로 이 단계는 반드시 **한 에이전트가 순차로** 처리한다.
- 로그인·CAPTCHA·결제 화면이 나오면 건너뛰고 기록만 한다.
