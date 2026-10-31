# 코그페 할인 검증 하네스

2026 코리아 그랜드 페스티벌(10.29~11.15) 할인 품목의 "표시 할인율"과 최근 2개월 실거래가 기준 "실질 할인율"을 비교한다.

| 단계 | 에이전트 | 산출물 |
|---|---|---|
| 0 | agents/00_discover.md | data/sources/*.json |
| 1 | agents/01_catalog.md | data/raw/catalog/<cat>/<source>.json |
| 2 | agents/02_pricing.md | data/raw/prices/<cat>/<source>__<chunk>.json |
| 4 | agents/04_verify.md | data/verified/<cat>/<source>__<chunk>.json |
| 6 | agents/06_browser_fallback.md | data/verified (갱신) |
| 3 | agents/03_analysis.md | output/index.html, discount_table.csv, summary.json |
| 5 | agents/05_html_qa.md | output/qa_report.md |

```bash
py scripts/build_report.py   # 표·HTML 재생성
py scripts/qa_html.py        # 정적 검사
```
각 단계 결과는 별도 커밋으로 남겨 `git diff`로 회차별 가격 변화를 추적한다.

모델 지정(싼 모델로 돌리기): docs/model_routing.md · 워크플로 재실행: harness/kgf_workflow.js · 단계별 서브에이전트: .claude/agents/kgf-*.md

## 공개 화면 (GitHub Pages)

- https://kevinkanguk.github.io/kgf/ → `output/` (인증표). dealbot 과 같은 방식: `main` 브랜치 루트, `.nojekyll`.
- 표 데이터는 `output/data.js`(요약·진행 현황) + `output/data-N.js`(품목 2만 개씩 조각)로 나뉜다. `output/data.json`(전체 필드, 160MB)은 GitHub 한도를 넘어 커밋하지 않는다(`py scripts/build_report.py`로 다시 만든다).
- 로컬 `local-history` 브랜치는 100MB 넘는 파일이 든 작업 기록이라 push 하지 않는다.

## 다음 갱신은 Codex로 (준비만 됨)

- 지침: [CODEX.md](CODEX.md) · 프롬프트: `.github/codex/find.md`(새 소스·품목), `.github/codex/price.md`(2개월 가격 조사)
- 손으로 1회: `py -3 scripts/codex_tick.py --dry-run` → `py -3 scripts/codex_tick.py`
- 자동 실행(미등록): `powershell -ExecutionPolicy Bypass -File scripts\install_tick.ps1`
