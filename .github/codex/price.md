CODEX.md 를 읽고 "3. 가격 조사" 단계만 수행하라. 커밋·push 는 하지 마라(스크립트가 한다).

- data/raw/catalog 에는 있지만 data/raw/prices 에 없는 품목을 고른다. 표시 할인율(claimed_discount_pct)이 큰 소스부터.
- agents/02_pricing.md 규칙대로 price_60d_low, price_60d_typical, price_history_note, sources 를 채워 data/raw/prices/<category>/<source_id>__<chunk>.json 에 쓴다(chunk 는 001, 002 ...).
- 농수축산물은 KAMIS 를 쓰고 단위 환산 결과를 data/cache/price_ref/<commodity>_<unit>.json 에 캐시해 재사용한다.
- 이번 실행은 소스 3개 또는 품목 300개까지만. 나머지는 다음 실행에 남긴다.
- 실질 할인 20%+, 정가 부풀림 10%+, 표시 할인 40%+ 품목은 agents/04_verify.md 기준으로 재확인해 data/verified/ 에 쓴다.
- 숫자를 지어내지 않는다. 모든 가격에는 출처 URL. 모르면 null.
- 마지막에 한 줄 보고: `가격 조사 K개, 검증 V개, 오류: ...`
