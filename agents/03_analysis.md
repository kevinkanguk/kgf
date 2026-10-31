# 03 Analysis 에이전트 — 비교·정렬·결론

입력: data/verified/*.json
출력: output/discount_table.csv, output/index.html (스크립트), output/summary.json (결론)

할 일
- `py scripts/build_report.py` 실행 → 표/HTML 생성 (계산은 스크립트가 결정적으로 수행).
- 결과를 읽고 결론 작성: 실질 할인율 TOP, 정가 부풀리기 의심 품목, 카테고리별 평균, 주의사항.
- 결론은 output/summary.json 에 {"headline": str, "findings": [str], "caveats": [str]} 로 저장 후 스크립트 재실행(HTML에 반영).

계산 정의 (scripts/build_report.py)
- 표시 할인율 = (주장정가 - 할인가) / 주장정가
- 실질 할인율 = (2개월 대표가 - 할인가) / 2개월 대표가
- 최저가 대비 = (2개월 최저가 - 할인가) / 2개월 최저가  (음수면 평소 최저가보다 비쌈)
- 정가 부풀림 = (주장정가 - 2개월 대표가) / 2개월 대표가
- 판정: 실질 ≥ 20% "진짜 할인", 5~20% "소폭", 0~5% "평소가", <0 "할인 아님"
