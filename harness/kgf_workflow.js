export const meta = {
  name: 'kgf-discount-audit',
  description: 'Korea Grand Festival full sweep: discover sources, extract all items, price+verify in chunks, browser fallback, analyze, QA HTML',
  phases: [
    { title: 'Discover', detail: '00 카테고리별 행사 소스(기획전·탭) 전수 목록' },
    { title: 'Catalog', detail: '01 소스별 모든 품목 추출 (스크래퍼)' },
    { title: 'Pricing', detail: '02 묶음별 주장가 + 2개월 가격' },
    { title: 'Verify', detail: '04 묶음별 독립 재검증' },
    { title: 'Browser', detail: '06 크롤링 실패 품목 브라우저 확인' },
    { title: 'Analysis', detail: '03 비교·정렬·결론 + HTML/CSV/XLSX' },
    { title: 'HTML QA', detail: '05 HTML 동작·링크 테스트' },
  ],
}

const ROOT = 'E:/090_ETC/kf'
const A = args || {}
const CHUNK = A.chunk || 25
const FALLBACK_MAX = A.fallbackMax || 80

// 단계별 모델/추론강도. model undefined = 세션 모델 상속. args.models 로 덮어쓰기 (docs/model_routing.md)
const M = Object.assign({
  discover: { model: 'sonnet', effort: 'medium' },
  catalog: { model: 'sonnet', effort: 'medium' },
  pricing: { model: 'sonnet', effort: 'medium' },
  verify: { model: undefined, effort: 'high' },
  fallback: { model: 'sonnet', effort: 'medium' },
  analysis: { model: 'sonnet', effort: 'medium' },
  qa: { model: 'haiku', effort: 'low' },
}, A.models || {})

const ALL_CATS = [
  { key: 'appliance', name: '가전·디지털', seeds: '삼성전자·LG전자 코그페 행사(냉장고/세탁기/TV 등), 위닉스 등 중견가전, 중소기업 가전(동행축제), 하이마트·전자랜드, 11번가/G마켓/SSG/롯데온/네이버 가전 탭' },
  { key: 'auto', name: '자동차', seeds: '현대차·기아·한국GM·르노코리아·KG모빌리티 차종별 코그페 판매조건, 현대·기아 인증중고차. 비교는 9~10월 월별 판매조건' },
  { key: 'food', name: '식품·농수축산', seeds: '농할(참여 온라인몰·마트·전통시장 각각), 수산대전(참여몰 각각), 소프라이즈 한우, 김장재료, 오아시스·우체국쇼핑·대형마트(이마트·홈플러스·롯데마트) 코그페 행사' },
  { key: 'fashion_beauty', name: '패션·뷰티', seeds: 'K-세일페스타 참여 브랜드/몰, 지그재그, W컨셉, 무신사·29CM·올리브영 참여 여부, 네이버 쇼핑 페스타 패션·뷰티' },
  { key: 'mall', name: '종합몰·생활', seeds: '11번가, G마켓, 롯데온, 네이버, SSG, H몰, NS몰, SK스토아, 그립, 코그페 스토어(/sme)의 생활·가구·기타 탭' },
  { key: 'travel_dutyfree', name: '여행·숙박·면세', seeds: '숙박세일페스타(참여 OTA별), 듀티프리페스타(면세점 25곳 각각), 항공권 특가' },
]
const CATS = A.categories ? ALL_CATS.filter(c => A.categories.includes(c.key)) : ALL_CATS

const LISTS = {
  issues: { type: 'array', items: { type: 'string' } },
  suggestions: { type: 'array', items: { type: 'string' }, description: '하네스·방법 개선 제안' },
  decisions_needed: { type: 'array', items: { type: 'string' }, description: '사용자 결정 필요 사항' },
}
const DISCOVER = {
  type: 'object',
  properties: {
    sources: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          source_id: { type: 'string' }, channel: { type: 'string' }, url: { type: 'string' },
          kind: { type: 'string' }, access: { enum: ['static', 'js', 'login'] }, est_items: { type: 'integer' },
        },
        required: ['source_id', 'channel', 'url', 'access'],
      },
    },
    ...LISTS,
  },
  required: ['sources', 'issues', 'suggestions', 'decisions_needed'],
}
const EXTRACT = {
  type: 'object',
  properties: { file: { type: 'string' }, count: { type: 'integer' }, needs_browser: { type: 'boolean' }, ...LISTS },
  required: ['file', 'count', 'needs_browser', 'issues', 'suggestions', 'decisions_needed'],
}
const REPORT = {
  type: 'object',
  properties: { file: { type: 'string' }, count: { type: 'integer' }, ...LISTS },
  required: ['file', 'count', 'issues', 'suggestions', 'decisions_needed'],
}

const rules = `프로젝트 루트: ${ROOT}. 먼저 ${ROOT}/CLAUDE.md 와 ${ROOT}/schema/item.schema.json 을 읽어라.
웹 조사는 WebSearch/WebFetch(ToolSearch로 로드), 대량 수집은 Bash로 py 스크립트. 기준일 2026-10-31. 숫자는 출처 URL이 있을 때만.
마지막에 요약(StructuredOutput) 반환.`

// ── 00 Discover (barrier: 카테고리 간 소스 중복 제거가 필요)
phase('Discover')
const discovered = await parallel(CATS.map(c => () => agent(`${rules}
너는 00 Discover 에이전트다. ${ROOT}/agents/00_discover.md 지침을 따른다.
카테고리 key="${c.key}" (${c.name}). 출발점: ${c.seeds}. 공식 사이트 https://koreagrandfestival.kr 도 전부 훑어라.
결과를 ${ROOT}/data/sources/${c.key}.json 에도 저장.`, { label: `discover:${c.key}`, phase: 'Discover', schema: DISCOVER, ...M.discover })
  .then(r => r && { ...r, category: c.key })))

const seenUrl = new Set(), sources = [], skipped = []
for (const d of discovered.filter(Boolean)) {
  for (const s of d.sources) {
    const k = s.url.replace(/[?#].*$/, '')
    if (seenUrl.has(k) && !/[?&](tab|cate|ctg|page|exhib|sectId|dispCmptId)=/i.test(s.url)) continue
    seenUrl.add(s.url)
    if (s.access === 'login') { skipped.push(s.source_id); continue }
    sources.push({ ...s, category: d.category })
  }
}
const limited = A.maxSources ? sources.slice(0, A.maxSources) : sources
log(`sources: ${limited.length} (login 제외 ${skipped.length}${A.maxSources && sources.length > A.maxSources ? `, maxSources로 ${sources.length - A.maxSources}개 제외` : ''})`)

// ── 01 → (02 → 04 per chunk) : 소스별로 끝나는 대로 다음 단계
const perSource = await pipeline(
  limited,
  s => agent(`${rules}
너는 01 Catalog 에이전트다. ${ROOT}/agents/01_catalog.md 지침을 따른다. 소스 하나의 **모든 품목**을 끝까지 수집한다.
source: ${JSON.stringify(s)}
출력: ${ROOT}/data/raw/catalog/${s.category}/${s.source_id}.json (item_id = "${s.source_id}-0001" 형식, 순서대로).
count 는 실제 저장한 품목 수.`, { label: `catalog:${s.source_id}`, phase: 'Catalog', schema: EXTRACT, ...M.catalog }),
  (ex, s) => {
    if (!ex || !ex.count) return { source: s, extract: ex, chunks: [] }
    const n = Math.ceil(ex.count / CHUNK)
    return parallel(Array.from({ length: n }, (_, i) => () => {
      const start = i * CHUNK, end = Math.min(ex.count, start + CHUNK)
      const tag = `${s.source_id}__${String(i).padStart(3, '0')}`
      return agent(`${rules}
너는 02 Pricing 에이전트다. ${ROOT}/agents/02_pricing.md 지침을 따른다.
입력: ${ROOT}/data/raw/catalog/${s.category}/${s.source_id}.json 의 items[${start}:${end}] (0-based, end 미포함).
출력: ${ROOT}/data/raw/prices/${s.category}/${tag}.json`, { label: `pricing:${tag}`, phase: 'Pricing', schema: REPORT, ...M.pricing })
        .then(() => agent(`${rules}
너는 04 Verify 에이전트다. ${ROOT}/agents/04_verify.md 지침을 따른다. 앞선 에이전트를 믿지 말고 출처를 직접 다시 열어라.
입력: ${ROOT}/data/raw/prices/${s.category}/${tag}.json
출력: ${ROOT}/data/verified/${s.category}/${tag}.json`, { label: `verify:${tag}`, phase: 'Verify', schema: REPORT, ...M.verify }))
    })).then(chunks => ({ source: s, extract: ex, chunks: chunks.filter(Boolean) }))
  },
)

const done = perSource.filter(Boolean)
const totalItems = done.reduce((a, r) => a + ((r.extract && r.extract.count) || 0), 0)
log(`extracted ${totalItems} items from ${done.length} sources`)

// ── 06 Browser fallback (브라우저 창 하나 공유 → 단일 에이전트 순차)
phase('Browser')
const fallback = await agent(`${rules}
너는 06 Browser Fallback 에이전트다. ${ROOT}/agents/06_browser_fallback.md 지침을 따른다.
${ROOT}/data/verified/**/*.json 에서 sale_price 또는 price_60d_typical 이 null 이거나 verify_status=unverifiable 인 품목을 찾고,
claimed_discount_pct 가 큰 순서로 최대 ${FALLBACK_MAX}개를 내장 브라우저(mcp__Claude_Browser__*, ToolSearch로 로드)로 확인해 같은 파일을 갱신하라.
needs_browser 로 표시된 소스: ${JSON.stringify(done.filter(r => r.extract && r.extract.needs_browser).map(r => r.source.source_id))}.
처리 못 한 개수를 issues 에 적어라. 끝나면 뷰포트를 desktop 으로 복구.`, { label: 'browser-fallback', phase: 'Browser', schema: REPORT, ...M.fallback })

// ── 03 Analysis
phase('Analysis')
const analysis = await agent(`${rules}
너는 03 Analysis 에이전트다. ${ROOT}/agents/03_analysis.md 지침을 따른다.
1) Bash: cd ${ROOT} && py scripts/build_report.py
2) output/data.json 을 분석해 output/summary.json ({"headline","findings":[...],"caveats":[...]}) 저장. findings 8~12개: 실질 할인 TOP, 정가 부풀림 의심, 카테고리별 평균, 행사별(농할·수산대전 등) 비교를 구체 품목명·수치로.
caveats 에 표본 검증 비율(verify_status null 비율)과 수집 제외 소스를 반드시 적어라. 로그인 제외 소스: ${JSON.stringify(skipped)}
3) build_report.py 재실행.`, { label: 'analysis', phase: 'Analysis', schema: REPORT, ...M.analysis })

// ── 05 HTML QA
phase('HTML QA')
const qa = await agent(`${rules}
너는 05 HTML QA 에이전트다. ${ROOT}/agents/05_html_qa.md 지침을 따른다.
1) Bash: cd ${ROOT} && py scripts/qa_html.py
2) 브라우저(mcp__Claude_Browser__*)로 file:///${ROOT}/output/index.html 을 열어 렌더링·검색·필터·정렬·더보기·모바일(375px) 확인. 끝나면 desktop 복구.
3) 카테고리별 buy_url 2개 이상 WebFetch로 열어 확인.
4) HTML/스크립트 버그는 scripts/ 를 고쳐 재생성. 데이터 문제는 기록만.
결과를 ${ROOT}/output/qa_report.md 에 PASS/FAIL 표로 저장.`, { label: 'html-qa', phase: 'HTML QA', schema: REPORT, ...M.qa })

const collect = key => [
  ...discovered.filter(Boolean).flatMap(d => d[key] || []),
  ...done.flatMap(r => [...((r.extract && r.extract[key]) || []), ...r.chunks.flatMap(c => c[key] || [])]),
  ...[fallback, analysis, qa].filter(Boolean).flatMap(r => r[key] || []),
]
return {
  sources: limited.length, skipped, totalItems,
  perSource: done.map(r => ({ id: r.source.source_id, count: r.extract && r.extract.count, chunks: r.chunks.length, needs_browser: r.extract && r.extract.needs_browser })),
  issues: collect('issues'), suggestions: collect('suggestions'), decisions_needed: collect('decisions_needed'),
}
