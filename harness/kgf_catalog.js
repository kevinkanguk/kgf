export const meta = {
  name: 'kgf-catalog-part',
  description: 'KGF: extract every item for one disjoint partition of sources (run several partitions in parallel)',
  phases: [{ title: 'Catalog', detail: '01 소스별 모든 품목 추출' }],
}

// args: { part: "part0", sources: [[category, source_id], ...], model?: {...} }
// 소스 목록은 scripts/partition_sources.py 가 겹치지 않게 나눈다. 같은 소스를 두 워크플로가 받는 일은 없다.
const ROOT = 'E:/090_ETC/kf'
const A = args || {}
const MODEL = A.model || { model: 'sonnet', effort: 'medium' }

const EXTRACT = {
  type: 'object',
  properties: {
    file: { type: 'string' }, count: { type: 'integer' }, needs_browser: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array', items: { type: 'string' } },
    decisions_needed: { type: 'array', items: { type: 'string' } },
  },
  required: ['file', 'count', 'needs_browser', 'issues', 'suggestions', 'decisions_needed'],
}

log(`${A.part}: ${A.sources.length} sources`)
const results = await parallel(A.sources.map(([cat, id]) => () => agent(`프로젝트 루트: ${ROOT}. 먼저 ${ROOT}/CLAUDE.md 와 ${ROOT}/schema/item.schema.json 을 읽어라.
너는 01 Catalog 에이전트다. ${ROOT}/agents/01_catalog.md 지침을 따른다. 소스 하나의 **모든 품목**을 끝까지 수집한다.
소스 정보: ${ROOT}/data/sources/${cat}.json 에서 source_id="${id}" 항목을 읽어라. 이 소스만 처리하고 다른 소스 파일은 건드리지 마라.
출력: ${ROOT}/data/raw/catalog/${cat}/${id}.json (item_id = "${id}-0001" 형식). 스크래퍼: ${ROOT}/scripts/scrapers/${id}.py, 캐시: ${ROOT}/data/cache/html/${id}/
이미 출력 파일이 있고 items 가 비어있지 않으면 아무것도 하지 말고 그 count 를 반환.
웹은 WebFetch/WebSearch 또는 Bash+py(requests). 브라우저가 꼭 필요할 때만 mcp__Claude_Browser__* 를 쓰되, 반드시 tabs_create 로 **자기 탭**을 만들어 모든 호출에 tabId 를 넘기고 끝나면 tabs_close.
count 는 실제 저장한 품목 수. 마지막에 StructuredOutput 반환.`,
  { label: `catalog:${id}`, phase: 'Catalog', schema: EXTRACT, ...MODEL }).then(r => r && { id, cat, ...r })))

const ok = results.filter(Boolean)
const collect = k => ok.flatMap(r => (r[k] || []).map(x => `[${r.id}] ${x}`))
return {
  part: A.part, done: ok.length, failed: A.sources.length - ok.length,
  items: ok.reduce((a, r) => a + (r.count || 0), 0),
  needs_browser: ok.filter(r => r.needs_browser).map(r => r.id),
  issues: collect('issues'), suggestions: collect('suggestions'), decisions_needed: collect('decisions_needed'),
}
