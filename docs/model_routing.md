# 단계별 모델 지정 (싼 모델로 돌리기)

Claude Code 에서 서브에이전트마다 모델을 고를 수 있다. 고를 수 있는 값은 아래 세 가지다.

| 별칭 | 모델 | 쓰임 |
|---|---|---|
| `haiku` | Haiku 5.5 | 가장 싸고 빠름. 정해진 검사, 링크 확인, 스크립트 실행 |
| `sonnet` | Sonnet 5.5 | 중간. 웹 조사, 데이터 수집, 스크린샷 읽기 |
| `opus` / 생략 | Opus 5.5 (세션 모델) | 가장 비쌈. 검증·판단처럼 틀리면 안 되는 단계 |

Claude Code 안에서는 Claude 모델만 고를 수 있다. 다른 회사 모델은 MCP 서버로 붙여야 한다(별도 작업).

## 이 프로젝트 기본값

| 단계 | 모델 | effort | 이유 |
|---|---|---|---|
| 00 소스 탐색 | sonnet | medium | 기획전·탭 목록화 |
| 01 수집 | sonnet | medium | 스크래퍼 작성·실행 위주 |
| 02 가격 | sonnet | medium | 같음 |
| 04 검증 | 세션 모델 | high | 마지막 관문이라 정확도 우선 |
| 03 분석 | sonnet | medium | 계산은 스크립트가 함, 결론 문장만 작성 |
| 05 HTML QA | haiku | low | 정해진 체크리스트 |
| 06 브라우저 확인 | sonnet | – | 그래프 스크린샷 판독은 haiku 정확도가 떨어질 수 있음 |

## 방법 1: 워크플로 스크립트 (여러 에이전트를 한 번에)

`harness/kgf_workflow.js` 맨 위의 `M` 객체가 단계별 모델이다. 내부적으로 `agent(prompt, { model: 'haiku', effort: 'low' })` 형태로 들어간다.

Claude 에게 이렇게 말하면 된다.

> harness/kgf_workflow.js 워크플로 돌려줘

실행할 때만 바꾸려면 `args` 로 덮어쓴다. 단계 단위로 통째로 바뀐다.

> harness/kgf_workflow.js 워크플로를 args `{"models": {"pricing": {"model": "haiku", "effort": "low"}}}` 로 돌려줘

그 밖의 args: `categories` (예: `["food"]` 만), `maxSources` (소스 수 상한), `chunk` (가격 조사 묶음 크기, 기본 25), `fallbackMax` (브라우저 확인 상한, 기본 80).

## 방법 2: 서브에이전트 정의 파일 (한 단계만 따로)

`.claude/agents/kgf-*.md` 의 frontmatter `model:` 이 그 에이전트의 모델이다(`haiku` / `sonnet` / `opus` / `inherit`).

> kgf-browser-fallback 에이전트로 food 카테고리 빈 가격 채워줘

새 작업에 응용할 때는 파일 하나 만들면 된다.

```markdown
---
name: my-cheap-checker
description: 링크가 살아있는지 확인
model: haiku
---
지침...
```

## 방법 3: 대화 중 즉석 지정

Claude 에게 "이 조사는 haiku 서브에이전트로 돌려" 라고 하면 Agent 도구의 `model` 파라미터로 지정해서 실행한다.

## 팁
- 싼 모델은 **수집·검사**에 쓰고 **검증**은 강한 모델로 두는 조합이 비용 대비 가장 낫다.
- 싼 모델로 바꾼 뒤에는 04 검증 단계의 `corrected`/`unverifiable` 비율을 비교해 품질이 떨어졌는지 본다(`git diff data/verified`).
- 스크린샷 판독(이미지 비교)은 haiku 도 가능하지만, 그래프 눈금을 읽는 작업은 sonnet 이상을 권장한다.
