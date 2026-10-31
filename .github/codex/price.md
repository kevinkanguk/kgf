가격 조사만 한다. 이 지시만으로 충분하니 CODEX.md·agents/·schema/ 를 다시 읽지 마라. 커밋·push 하지 마라.

## 입력
`.tmp/price_todo.json` 의 `items` (스크립트가 뽑은 조사 대상, 표시 할인 큰 순). 이 목록 밖의 품목은 보지 않는다.

## 품목마다 2개월(2026-09-01~10-28) 가격 찾기 — 위에서 찾으면 아래는 안 한다
같은 상품 = 같은 브랜드·업체 + 같은 규격(중량·개수·용량·사이즈). 하나라도 다르면 다른 상품이다.
1. 가격 이력: 다나와 상품명 검색 → 같은 상품의 `https://prod.danawa.com/info/ajax/getProductPriceList.ajax.php?productCode=<pcode>&period=3`
   (Referer 를 상품 페이지로), 에누리 가격추이. 기간 안 값의 최저 = low, 중앙값 = typical, confidence "medium".
2. 같은 몰의 이전 판매가 흔적(날짜가 기간 안이라는 근거가 있을 때만). confidence "medium".
3. 다른 몰 평소가(코그페 행사 아닌 판매처 2곳 이상의 중앙값 → typical, low 는 null). confidence "low", note 는 `"타몰 평소가: "` 로 시작해 몰·가격 적기.
4. 농수축산 표준품: KAMIS, 단위·등급이 맞을 때만. `data/cache/price_ref/` 캐시 먼저 읽고 새 값은 저장.
5. 못 찾으면 가격 null, note 는 `"이력 없음: "` + 찾아본 곳 한 줄.

## 방법 (토큰 절약)
- 품목 페이지를 하나씩 읽지 말고 스크립트로 일괄 처리한다. 있는 스크립트를 재사용·수정한다:
  `scripts/scrapers/price_search_batch.py`(다나와·에누리·네이버 검색), `price_enuri_merchants.py`·`price_merchant_evidence.py`(에누리 판매처 가격).
  새 일회성 스크립트를 늘리지 않는다. 실행: `.python/python.exe -I <스크립트>`.
- 스크립트 출력은 요약(품목별 한 줄)만 보고, 애매한 품목만 자세히 본다. HTML 원문을 통째로 출력하지 않는다.
- 403·429·로그인이면 그 사이트는 이번 실행에서 포기. web.archive.org 는 접속 안 됨.

## 출력
- `data/raw/prices/<category>/<source_id>__codex<NNN>.json` (NNN 은 비어 있는 다음 번호), UTF-8(BOM 없이), 들여쓰기 2칸.
  `{"category","source_id","collected_at","items":[...]}`. 품목에는 **`item_id` 와 가격 필드만** 쓴다 (나머지는 표 만들 때 catalog 에서 합쳐진다):
  `item_id, price_60d_low, price_60d_typical, price_history_note, confidence, sources`(근거 URL 전부).
- 실질 할인 20%+ 또는 정가 부풀림 10%+ 품목만 근거를 한 번 더 열어 확인하고 같은 형식으로 `data/verified/<category>/<같은 파일명>` 에 쓰며
  `verify_status`("confirmed"/"corrected"/"unverifiable"), `verify_note` 를 더한다. "이력 없음" 은 verified 에 쓰지 않는다.
- 숫자를 지어내지 않는다. 출처 URL 없는 가격은 null.
- 마지막 한 줄: `가격 조사 K개 (이력사이트 a, 같은몰 b, 타몰 c, KAMIS d, 이력 없음 e), 검증 V개, 오류: ...`
