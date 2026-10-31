CODEX.md 를 읽고 "3. 가격 조사" 단계만 수행하라. 커밋·push 는 하지 마라(스크립트가 한다).

## 대상
- 인증표에 보이는 품목(data/kgf_scope.json 범위) 중 아직 2개월 가격이 없고 `price_history_note` 도 없는 품목.
  목록 뽑기: `.python/python.exe -I -c "import sys; sys.path.insert(0,'scripts'); import build_report; ..."` 로 `build_report.load()` 를 쓰면 범위·중복 제거가 된 품목이 나온다.
- 모델명 있는 가전·공산품은 `scripts/price_danawa.py` 가 이미 처리했다(`<source_id>__danawa.json`). 다시 하지 않는다.
- 표시 할인율이 큰 품목부터. 이번 실행은 **품목 100개**까지만 (20개에 Codex 토큰 약 16만 개가 들었다, 2026-10-31). 나머지는 다음 실행에 남긴다.

## 2개월 가격을 찾는 순서 (위에서 찾으면 아래는 안 한다)
기간: 2026-09-01 ~ 10-28. 같은 상품 = 같은 브랜드·업체 + 같은 규격(중량·개수·용량·사이즈). 규격이 하나라도 다르면 같은 상품이 아니다.

1. **가격 이력 사이트**: 다나와(상품명으로 검색 → 상품명·규격이 같은 상품의 가격변동 API
   `https://prod.danawa.com/info/ajax/getProductPriceList.ajax.php?productCode=<pcode>&period=3`, Referer 를 상품 페이지로),
   에누리 가격추이, 폴센트. 주간/일간 가격의 최저 = `price_60d_low`, 중앙값 = `price_60d_typical`. `confidence`: "medium".
2. **같은 몰의 이전 가격 흔적**: 상품 상세 API·HTML 에 있는 이전 판매가, 가격 변경 이력, 기간 한정 특가의 "행사 전 가격"과 그 날짜.
   날짜가 기간 안이라는 근거가 있을 때만 쓴다. `confidence`: "medium".
3. **다른 몰의 평소 가격**: 같은 상품이 다른 몰(네이버 스마트스토어, 11번가, 쿠팡, 업체 자사몰 등)에서 **코그페 행사 없이** 팔리는 가격.
   2곳 이상이면 중앙값을 `price_60d_typical` 로, `price_60d_low` 는 null.
   2개월 이력이 아니라 현재 가격이므로 `confidence`: "low", `price_history_note` 를 `"타몰 평소가: "` 로 시작하고 몰·가격·URL 을 적는다.
4. **농수축산물(규격 표준품)**: KAMIS 소매가격. 단위·등급이 맞을 때만 환산해 쓰고 환산식을 note 에. 결과를 `data/cache/price_ref/<commodity>_<unit>.json` 에 캐시(있으면 먼저 읽기).
5. **위에서 못 찾으면**: 가격은 null, `price_history_note` 를 `"이력 없음: "` 으로 시작해 무엇을 찾아봤는지 한 줄로(예: `"이력 없음: 다나와·에누리 미등록, 타몰 판매처 없음(업체 단독 상품)"`).
   인증표에서 "이력 없음"으로 따로 분류되고, 다음 실행에서 다시 조사하지 않는다.

- 원래 페이지 접근이 막히면(403·429·로그인) 그 사이트는 이번 실행에서 포기하고 다음 방법으로 넘어간다. web.archive.org 는 이 PC 에서 접속이 안 된다.
- 품목이 많으므로 사람이 페이지를 하나씩 읽지 말고 스크립트로 한다. **먼저 있는 스크립트를 재사용**한다:
  `scripts/scrapers/price_search_batch.py`(다나와·에누리·네이버 검색 증거 모으기), `price_enuri_merchants.py`·`price_merchant_evidence.py`(에누리 판매처별 가격).
  대상 개수·조건만 인자로 바꿔 쓰고, 일회성 스크립트를 새로 늘리지 않는다. 고칠 게 있으면 그 파일을 고친다.

## 쓰기
- `data/raw/prices/<category>/<source_id>__codex<NNN>.json` (NNN 은 001 부터 비어 있는 번호). 최상위 형식은 CLAUDE.md, 품목은 catalog 의 필드를 그대로 두고
  `price_60d_low`, `price_60d_typical`, `price_history_note`, `confidence`, `sources`(근거 URL 전부. 타몰 평소가면 그 몰 상품/판매처 링크를 sources 에도 넣는다)를 채운다. UTF-8 (BOM 없이).
- 실질 할인 20%+, 정가 부풀림 10%+, 표시 할인 40%+ 품목만 agents/04_verify.md 기준으로 재확인해 `data/verified/` 에 쓴다.
  가격을 못 찾은 품목("이력 없음")은 verified 에 쓰지 않는다.
- 숫자를 지어내지 않는다. 출처 URL 없는 가격은 null.
- 마지막에 한 줄 보고: `가격 조사 K개 (이력사이트 a, 같은몰 b, 타몰 c, KAMIS d, 이력 없음 e), 검증 V개, 오류: ...`
