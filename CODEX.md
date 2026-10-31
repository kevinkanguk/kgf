# CODEX.md — 코그페 할인 인증표 갱신 지침

이 저장소는 2026 코리아 그랜드 페스티벌(10.29~11.15) 할인 품목을 모아 "표시 할인"과 "실제 2개월 가격"을 비교하는 인증표다.
공개 화면: https://kevinkanguk.github.io/kgf/ (GitHub Pages, `main` 브랜치 루트. push 후 1~2분 뒤 반영)

Codex는 실행될 때마다 이 문서를 읽고 아래 순서를 **한 번** 수행한다.
결정적인 일(수집 스크립트 재실행, 표 생성, 검사, 커밋)은 `scripts/`가 한다. Codex가 판단할 일은 **2단계 새 품목·새 소스 찾기**와 **3단계 가격 조사**다.

> **현재 상태 (2026-10-31)**: 준비만 되어 있다. 자동 실행(작업 스케줄러)은 **등록하지 않았다.**
> 손으로 한 번 돌리기: `py -3 scripts/codex_tick.py --dry-run` (무엇을 할지 출력만), `py -3 scripts/codex_tick.py` (실제 실행).
> 자동 실행을 켜려면 `powershell -ExecutionPolicy Bypass -File scripts/install_tick.ps1` (dealbot "DealBot tick"과 같은 방식, 6시간마다).

## 파일 경계

| 경로 | Codex |
| --- | --- |
| `data/sources/*.json` | 2단계에서 새 소스를 **추가만** 한다. 기존 항목은 고치지 않는다 |
| `data/raw/catalog/**` | 수집 스크립트(`scripts/scrapers/*.py`)가 쓴다. 새 소스는 새 스크립트를 만들어 쓴다 |
| `data/raw/prices/**`, `data/verified/**` | 3단계 결과. 형식은 `schema/item.schema.json` |
| `scripts/scrapers/` | 새 소스용 스크립트를 **추가**할 수 있다. 기존 스크립트는 사이트 구조가 바뀌어 깨졌을 때만 고친다 |
| `data/kgf_scope.json` | 인증표에 보일 코그페 소스 목록. 새 코그페 소스를 찾으면 `tier`("코그페 표시" 또는 "코그페 공식 링크"), `why`, `evidence`(근거 URL)와 함께 **추가**한다. 여기 없는 소스 품목은 표에 안 나온다 |
| `output/` | `scripts/build_report.py`만 쓴다. 손으로 고치지 않는다 |
| `scripts/*.py`(scrapers 제외), `scripts/template.html`, `schema/`, `agents/`, 이 문서 | **수정 금지.** 버그는 `.tmp/codex-report.txt`에 적고 넘어간다 |
| `.tmp/`, `data/cache/html/` | 임시. 커밋하지 않는다 (gitignore됨) |

## 수집 범위 규칙 (필수)

`agents/01_catalog.md` 의 "다음 실행부터 지킬 규칙" 1~7을 그대로 따른다. 요약:
- 코그페(코리아 그랜드 페스티벌) 표시가 있는 페이지·품목만. 몰 메인·전체 목록·별도 정부 행사(근거 없는 농할·수산대전·추석전)는 제외.
- koreagrandfestival.kr 참여 업체 목록에서 출발하고, 품목마다 `vendor` 와 `kgf_evidence`(코그페 페이지 URL)를 남긴다.
- 추정치 5배 초과 소스는 범위 확인 전까지 보류. 코그페 표시를 확인 못 하면 건너뛰고 기록.
- 할인가 0원 = 할인하지 않은 상품 → 수집하지 않고, 할인율도 계산하지 않는다.
- 별점은 5점 만점으로 환산.
- 2026-10-31 회차 데이터에는 이 규칙 이전에 모은 몰 전체 목록 품목(약 12.4만 개)이 섞여 있다. 정리할지는 사용자가 정한다. 마음대로 지우지 않는다.

## 실행 환경

- Python 은 `.python/python.exe -I <스크립트>` 로 실행한다. Codex 샌드박스는 AppData 의 Python 실행을 막아서 `py`·`python`·venv 가 모두 안 된다.
  `.python/` 은 설치된 Python 3.13 폴더를 통째로 복사한 것이다 (requests·openpyxl 포함, gitignore). 새 PC 에서는 `%LOCALAPPDATA%\Programs\Python\Python313` 을 `.python` 으로 복사하고 `.python\python.exe -m pip install -r requirements.txt`.
- `scripts/codex_tick.py` 가 Codex 를 네트워크 허용(`sandbox_workspace_write.network_access=true`)으로 부른다.
- Codex 는 Codex 데스크톱 앱의 ChatGPT 로그인을 쓴다. GitHub 시크릿·API 키는 필요 없다. push 는 이 PC 의 git 로그인으로 한다.

## 실행 순서

### 1. 최신화

```bash
git pull --rebase
mkdir -p .tmp
```

### 2. 새 품목·소스 찾기 (판단 ①) — 프롬프트: `.github/codex/find.md`

- `data/sources/*.json`에 없는 코그페 참여 행사 페이지(기획전, 브랜드관, 지역 특산물전 등)를 웹에서 찾아 추가한다. `source_id`는 `<category>-<site>-<slug>` 형식, `access`는 `static`/`js`/`login` 중 하나.
- 새 소스는 `agents/01_catalog.md` 규칙대로 **모든 품목**을 수집한다. 20개가 넘으면 `scripts/scrapers/<source_id>.py`를 만들어 돌린다(가능하면 사이트 JSON API 사용).
- 이미지(`image_url`), 별점(5점 환산 `rating`), 리뷰수(`review_count`)는 있으면 반드시 넣는다.
- 기존 수집 스크립트 재실행은 `scripts/codex_tick.py`가 한다(`--refresh` 일 때 HTML 캐시를 지우고 다시 받음).

### 3. 가격 조사 (판단 ②) — 프롬프트: `.github/codex/price.md`

- 먼저 `scripts/price_danawa.py`(스크립트, 토큰 없음)가 모델명 있는 품목의 다나와 주간 최저가 2개월치를 채운다 (`<source_id>__danawa.json`).
- 나머지는 Codex 가 price.md 순서대로: 가격 이력 사이트 → 같은 몰 이전 가격 → 다른 몰 평소가(confidence low, note "타몰 평소가:") → KAMIS → 못 찾으면 note "이력 없음:".
  "이력 없음" 품목은 인증표에서 따로 분류되고 다시 조사하지 않는다.
- 한 번에 품목 100개까지만 한다. 나머지는 다음 실행에서 이어간다.
- 실질 할인 20% 이상, 정가 부풀림 10% 이상, 표시 할인 40% 이상은 `agents/04_verify.md` 기준으로 재확인해 `data/verified/`에 쓴다.

### 4. 표 만들기·검사

```bash
py scripts/build_report.py --xlsx
py scripts/qa_html.py
```

`qa_html.py`가 실패하면(종료 코드 1, `FAIL:` 줄) **push하지 않는다.** `WARN:` 줄(빈 업체명, 정가<할인가 4건 등 원천 데이터 빈칸)은 push를 막지 않는다. 둘 다 보고에 적는다.

### 5. 커밋·푸시

```bash
git add data output scripts/scrapers
git commit -m "codex: run <YYYY-MM-DD HH:MM> (+<새 품목 수> items, +<가격 조사 수> priced)"
git push
```

- push가 거절되면 `git pull --rebase` 후 다시 push. 충돌이 나면 `git rebase --abort` 후 멈추고 보고한다.

마지막에 한 줄로 보고한다: `새 소스 N개, 새 품목 M개, 가격 조사 K개, 오류: [...] 또는 없음`

## 금지

- 숫자 지어내기. 모든 가격에는 출처 URL(`sources`)이 있어야 한다. 모르면 `null`.
- 로그인, 캡차, 프록시, 차단 우회. 403·429면 그 사이트는 이번 실행에서 포기.
- 토큰·쿠키·개인정보를 저장소에 쓰기.
- 50MB 넘는 파일 커밋 (`output/data.json`은 gitignore됨. 표 데이터는 `output/data-N.js` 조각으로 나뉜다).
