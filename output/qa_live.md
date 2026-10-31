# 코그페 인증표 라이브 QA (1회차, 2026-10-31 11:0x)

범위: 스냅샷 시점 index.html 임베드 4,609건 / data.json 4,609건 / 원천(data/raw) 약 6.7천건 (수집이 계속 늘어나는 중).

## 결과 요약

| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| 1 | `py scripts/qa_html.py` | FAIL (1건) | food-inthemarket-nonghal-0381: 할인가 45,900 > 주장정가 44,900 (원천 데이터 문제) |
| 2a | 무작위 15건 원천 vs data.json vs html (상품명/정가/할인가/표시할인율/buy_url/image_url/rating/stage) | PASS | html에 포함된 항목은 전부 일치. 원천에만 있고 html에 아직 없는 건은 갱신 지연(아래 #5) |
| 2b | html 임베드 전수(4,609) vs 원천 | PASS (주의) | 차이는 product 47건뿐: 원천(농협몰 대전)에서 말줄임 "..." 이 이후 수정됨. 빌드 이후 원천이 바뀐 것이라 인증표 버그 아님 |
| 2c | 데이터 품질: image_url | FAIL | 전 소스 전 품목 image_url 없음 (CLAUDE.md는 필수 수집) |
| 2d | 데이터 품질: rating / review_count | FAIL | 전 소스 전 품목 null |
| 2e | 데이터 품질: 정가=할인가 | FAIL(의심) | 표시할인율 0%가 되는 품목 약 1,550건. hmall reco-1~5 는 86%(154~265/300), lotteon fruit 159/438 등. 정가 칸에 할인가를 복사한 것으로 의심 |
| 2f | 데이터 품질: 할인가>정가 | FAIL | 1건 (위 #1) |
| 2g | 데이터 품질: 정가 null | 참고 | nonghyupmall 133건 전부, epost-kgf-p1 62건, inthemarket 3건 |
| 2h | buy_url 빈값/상대경로, 별점 스케일 | PASS | 빈값·상대경로 0건. rating 이 전부 null 이라 스케일 검증은 불가 |
| 2i | 실질할인율/판정/검증 | 미검증 | 가격조사·검증 단계 데이터가 아직 0건: 전 품목 stage=수집, verdict=판단불가, KPI 실질할인 0개 |
| 3 | 내장 브라우저 UI (검색/필터/정렬/더 보기/진행현황/썸네일/별점/375px) | NOT RUN | `tabs_create`(tab-15)는 성공했으나 `navigate file:///E:/090_ETC/kf/output/index.html` 이 2회 모두 "couldn't open file ... declined access" 로 거부됨(파일은 존재, 5.0MB). 우회(로컬 서버 등)는 하지 않음. 탭 닫음, viewport 변경 없음 |
| 4 | 정적 코드 점검(template.html) | PASS (읽기만) | 필터/검색/더 보기(300 단위)/정렬/모바일 CSS 로직은 코드상 이상 없음. 실제 렌더 미확인 |
| 5 | 갱신 일관성 | FAIL | 아래 상세 |
| 6 | 진행 현황 | PASS (데이터 기준) | sources 318개 임베드. status 계산 로직 정상(수집만 있어서 "수집완료"/"대기"만 나옴) |

## 재현 방법
- #1: `py scripts/qa_html.py`
- #2: 스크래치 스크립트로 data/raw/**·verified/** 를 build_report.load() 와 같은 규칙으로 병합 후 item_id 별 비교 (html 의 `const DATA = ...` 를 JSON 파싱).
- #2c/2d/2e: 원천 JSON 에서 `image_url`, `rating` 이 비었거나 `claimed_original_price == sale_price` 인 건수를 source_id 별로 집계.
- #5: 빌드 중 `ls -l --time-style=full-iso output` 반복: data.json/csv 가 11:06:50 인데 index.html 은 11:04:35 -> 11:07:51 에 갱신. 그 사이 data.json 은 4,609건, html 은 2,187건.

## 원인 추정 / 수정 제안

### A. 갱신 지연·불일치 (build_report.py)
`main()` 순서가 data.json -> csv -> xlsx -> html 이다. openpyxl xlsx 쓰기가 5천건에서 약 60초(건수에 비례) 걸려, 그동안 html 이 한 단계 뒤처지고, 4만건이면 2분 주기를 넘길 가능성이 크다. data.json 도 비원자적 write 라 읽는 쪽이 중간 파일을 볼 수 있다. 제안:

```diff
-    (OUT / "data.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
-    (OUT / "sources_progress.json").write_text(...)
-    write_csv(items)
-    try:
-        write_xlsx(items, summary)
-    except PermissionError:
-        print("xlsx skipped (file open in Excel)")
-    write_html(items, summary, sources)
+    write_html(items, summary, sources)          # 사용자에게 가장 중요한 것을 먼저
+    atomic_write(OUT / "data.json", json.dumps(items, ensure_ascii=False))   # tmp -> replace, indent 제거로 용량 절반
+    atomic_write(OUT / "sources_progress.json", ...)
+    write_csv(items)
+    if os.environ.get("XLSX_EVERY", "5") and run_count % 5 == 0:   # xlsx 는 N회에 1번
+        try: write_xlsx(items, summary)
+        except PermissionError: print("xlsx skipped (file open in Excel)")
```

### B. 이미지·별점 전부 null
스크래퍼가 목록 API 응답의 이미지/평점 필드를 저장하지 않는 것으로 보인다(소스 JSON 단계에서 이미 null). 템플릿은 정상(썸네일 자리표시 + onerror 제거). hmall `plansale-ancr-paging` 응답, inthemarket 목록 HTML, lotteon API 에서 image/rating 필드를 매핑하도록 scripts/scrapers/<source_id>.py 수정 필요(수집 워크플로 쪽 과제).

### C. 정가=할인가
정가를 모르는 소스에서 정가 칸에 판매가를 복사한 듯하다. CLAUDE.md "추정 금지" 에 따라 정가를 알 수 없으면 `claimed_original_price: null`. 표시/정가부풀림 지표가 0% 로 왜곡된다. 빌드 쪽 방어(수정 제안):

```diff
-    it["shown_discount_pct"] = pct(orig - sale, orig) if orig and sale else it.get("claimed_discount_pct")
+    it["shown_discount_pct"] = pct(orig - sale, orig) if orig and sale and orig != sale else it.get("claimed_discount_pct")
```
(근본 해결은 스크래퍼에서 null 처리)

### D. 규모 대응 (template.html)
인라인 JSON 이 이미 5MB(4,609건). 4만건이면 40MB 이상이라 file:// 로드·모바일에서 느려질 수 있다. 제안: 임베드는 표시 필수 필드만 남기거나(`sources`, `conditions` 제외), 첫 N건만 임베드하고 나머지는 data.json fetch. `render()` 가 입력마다 전체 필터+정렬하므로 검색 입력에 debounce(150ms) 추가 권장.

### E. 기타
- `output/summary.json` 이 없어 결론 박스가 숨겨짐(정상 동작이나 03_analysis 단계 미실행).
- live_refresh.sh 의 git 커밋은 이 디렉터리가 git 저장소가 아니라 조용히 실패한다(해가 없음).
- 다음 회차: 브라우저 파일 접근 허용 후 3번 항목 재수행 필요. 가격조사/검증 데이터가 들어오면 실질할인율·판정·KPI 재검증.
