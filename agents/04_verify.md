# 04 Verify 에이전트 — 묶음 독립 재검증

입력: data/raw/prices/<category>/<source_id>__<chunk>.json
출력: data/verified/<category>/<source_id>__<chunk>.json (입력의 모든 품목 포함)

검증 우선순위 (회의적으로, 출처를 직접 다시 연다)
1. **전수 확인**: 실질 할인율 ≥ 20% 이거나 정가 부풀림 ≥ 10% 이거나 표시 할인율 ≥ 40% 인 품목 — 결론에 영향이 큰 품목.
2. **표본 확인**: 나머지는 최소 5개 중 1개 이상 무작위로 확인. 표본이 틀리면 그 묶음 전체를 확인.
3. 확인 안 한 품목은 verify_status = null, verify_note = "미표본".

판정
- confirmed(맞음) / corrected(값 수정) / unverifiable(확인 불가 — confidence low)
- buy_url 이 열리지 않거나 다른 상품이면 수정, 행사 품목이 아니면 제외하고 issues 에 기록.
- 출처 없는 숫자는 null 처리.
- 2개월 가격은 별도 소스 1곳 이상과 교차확인.
