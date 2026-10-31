"""data/{raw,verified}/**/*.json -> output/discount_table.csv, output/data.json, output/index.html

Usage: py scripts/build_report.py   (catalog→prices→verified 단계를 합쳐 진행 중에도 갱신)
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

CATEGORY_LABELS = {
    "appliance": "가전·디지털",
    "auto": "자동차",
    "food": "식품·농수축산",
    "fashion_beauty": "패션·뷰티",
    "mall": "종합몰·생활",
    "travel_dutyfree": "여행·숙박·면세",
}


def pct(num, den):
    if num is None or den in (None, 0):
        return None
    return round(num / den * 100, 1)


def verdict(real):
    if real is None:
        return "판단불가"
    if real >= 20:
        return "진짜 할인"
    if real >= 5:
        return "소폭 할인"
    if real >= 0:
        return "평소가"
    return "할인 아님"


def enrich(it):
    orig, sale = it.get("claimed_original_price"), it.get("sale_price")
    if orig and sale and orig == sale:
        orig = None  # 정가 칸에 판매가를 복사한 경우: 할인 주장이 없는 것으로 본다
    if not it.get("rating") and not it.get("review_count"):
        it["rating"] = None  # 리뷰 없는 0점은 별점 없음
    typ, low = it.get("price_60d_typical"), it.get("price_60d_low")
    it["shown_discount_pct"] = pct(orig - sale, orig) if orig and sale else it.get("claimed_discount_pct")
    it["real_discount_pct"] = pct(typ - sale, typ) if typ and sale else None
    it["vs_low_pct"] = pct(low - sale, low) if low and sale else None
    it["inflation_pct"] = pct(orig - typ, typ) if orig and typ else None
    it["verdict"] = verdict(it["real_discount_pct"])
    it["category_label"] = CATEGORY_LABELS.get(it.get("category"), it.get("category"))
    # 자동차는 실거래가 이력 대신 9~10월 월별 프로모션 조건과 비교하므로 기준이 다름을 표시
    it["basis_note"] = "비교기준: 9~10월 월별 프로모션" if it.get("category") == "auto" else None
    return it


# 진행 단계: 나중 단계가 앞 단계 값을 덮어쓴다. 수집 중에도 인증표에 바로 보이게 하기 위함
STAGES = [("raw/catalog", "수집"), ("raw/prices", "가격조사"), ("verified", "검증")]


def read_docs(sub):
    for f in sorted((ROOT / "data" / sub).rglob("*.json")):
        try:
            yield json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # 에이전트가 쓰는 중인 파일


def load():
    merged = {}
    for sub, stage in STAGES:
        for doc in read_docs(sub):
            for it in doc.get("items", []):
                if not it.get("item_id"):
                    continue
                it.setdefault("category", doc.get("category"))
                it.setdefault("source_id", doc.get("source_id"))
                it["stage"] = stage
                merged[it["item_id"]] = {**merged.get(it["item_id"], {}), **it}
    items = [enrich(it) for it in merged.values()]
    if "--all" not in sys.argv:
        items = kgf_only(items)
    items.sort(key=lambda x: (x["real_discount_pct"] is None, -(x["real_discount_pct"] or 0)))
    return items


def kgf_only(items):
    """코그페 표시(또는 공식 홈 링크) 기획전 품목만 남긴다. 범위: data/kgf_scope.json. 같은 상품 링크는 한 번만."""
    scope = json.loads((ROOT / "data" / "kgf_scope.json").read_text(encoding="utf-8"))["sources"]
    kept, seen = [], set()
    for it in items:
        sc = scope.get(it.get("source_id"))
        if not sc or (sc.get("channel_contains") and sc["channel_contains"] not in (it.get("channel") or "")):
            continue
        if not it.get("sale_price"):  # 할인가 0원·빈 값 = 할인하지 않은 상품 (사용자 정의, 2026-10-31)
            continue
        if it.get("rating") and 5 < it["rating"] <= 10:  # 10점 만점으로 들어온 별점을 5점 만점으로
            it["rating"] = round(it["rating"] / 2, 1)
        key = it.get("buy_url") or it["item_id"]
        if key in seen:
            continue
        seen.add(key)
        it["kgf_scope"] = sc["tier"]
        it["kgf_evidence"] = it.get("kgf_evidence") or sc["evidence"]
        kept.append(it)
    return kept


def progress(items):
    by_src = {}
    for it in items:
        s = by_src.setdefault(it.get("source_id"), {"수집": 0, "가격조사": 0, "검증": 0})
        s[it["stage"]] += 1
    rows = []
    scope = json.loads((ROOT / "data" / "kgf_scope.json").read_text(encoding="utf-8"))["sources"]
    for f in sorted((ROOT / "data" / "sources").glob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for s in doc.get("sources", []):
            c = by_src.get(s["source_id"], {})
            n = sum(c.values())
            status = ("제외(로그인)" if s.get("access") == "login" else
                      "범위 밖(코그페 표시 없음)" if not n and s["source_id"] not in scope else
                      "대기" if not n else "검증완료" if c.get("검증") == n else
                      "가격조사중" if c.get("가격조사") or c.get("검증") else "수집완료")
            rows.append({"source_id": s["source_id"], "category": CATEGORY_LABELS.get(doc.get("category"), doc.get("category")),
                         "channel": s.get("channel"), "url": s.get("url"), "est_items": s.get("est_items"),
                         "items": n, "verified": c.get("검증", 0), "status": status})
    return rows


COLUMNS = [
    ("item_id", "ID"), ("category_label", "분야"), ("vendor", "업체"), ("channel", "판매처"),
    ("product", "상품"), ("unit", "단위"), ("rating", "별점"), ("review_count", "리뷰수"), ("claimed_original_price", "주장정가"), ("sale_price", "할인가"),
    ("shown_discount_pct", "표시할인율%"), ("price_60d_typical", "2개월대표가"),
    ("price_60d_low", "2개월최저가"), ("real_discount_pct", "실질할인율%"),
    ("vs_low_pct", "최저가대비%"), ("inflation_pct", "정가부풀림%"), ("verdict", "판정"),
    ("conditions", "조건"), ("stage", "진행단계"), ("verify_status", "검증"), ("confidence", "신뢰도"),
    ("kgf_scope", "코그페근거"), ("kgf_evidence", "코그페페이지"), ("buy_url", "구매링크"), ("image_url", "이미지"), ("basis_note", "비교기준"), ("verify_note", "검증메모"),
]
PCT_KEYS = {"shown_discount_pct", "real_discount_pct", "vs_low_pct", "inflation_pct"}
WON_KEYS = {"claimed_original_price", "sale_price", "price_60d_typical", "price_60d_low"}


def write_csv(items):
    with open(OUT / "discount_table.csv", "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow([label for _, label in COLUMNS])
        for it in items:
            w.writerow(["" if it.get(k) is None else it.get(k) for k, _ in COLUMNS])


def write_xlsx(items, summary):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    from openpyxl.cell import WriteOnlyCell

    # write_only: 16만 행에서 셀마다 스타일을 거는 일반 모드는 20분 넘게 걸린다
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("할인검증표")
    widths = {"product": 40, "verify_note": 50, "conditions": 28, "basis_note": 24, "buy_url": 40}
    for col, (k, label) in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(col)].width = widths.get(k, max(10, len(label) * 2 + 2))
    ws.freeze_panes = "F2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{len(items) + 1}"

    def cell(value, **style):
        c = WriteOnlyCell(ws, value=value)
        for k, v in style.items():
            setattr(c, k, v)
        return c

    head = dict(font=Font(bold=True, color="FFFFFF"), fill=PatternFill("solid", fgColor="2F5BD3"),
                alignment=Alignment(horizontal="center", vertical="center", wrap_text=True))
    ws.append([cell(label, **head) for _, label in COLUMNS])
    fills = {v: PatternFill("solid", fgColor=c) for v, c in
             {"진짜 할인": "E6F4EC", "소폭 할인": "FDF3E1", "할인 아님": "FBE9E7"}.items()}
    for it in items:
        row = []
        for k, _ in COLUMNS:
            v = it.get(k)
            if k in WON_KEYS:
                row.append(cell(v, number_format='#,##0"원"'))
            elif k in PCT_KEYS:
                row.append(cell(v, number_format='0.0"%"'))
            elif k == "verdict" and v in fills:
                row.append(cell(v, fill=fills[v]))
            else:
                row.append(v)  # 구매링크는 URL 그대로 (엑셀이 링크로 연다)
        ws.append(row)

    s = wb.create_sheet("결론")
    s.column_dimensions["A"].width = 120
    h = WriteOnlyCell(s, value=summary.get("headline", ""))
    h.font = Font(bold=True, size=14)
    s.append([h])
    s.append([])
    for title, key in (("주요 발견", "findings"), ("주의사항", "caveats")):
        c = WriteOnlyCell(s, value=title)
        c.font = Font(bold=True)
        s.append([c])
        for line in summary.get(key, []):
            s.append(["• " + line])
        s.append([])
    wb.save(OUT / "discount_table.xlsx")


# 인증표에 실제로 쓰는 필드만 data.js 로 내보내 페이지 용량을 줄인다
HTML_KEYS = ["item_id", "category_label", "vendor", "channel", "product", "model_code", "unit", "conditions",
             "claimed_original_price", "sale_price", "shown_discount_pct", "price_60d_typical", "price_60d_low",
             "real_discount_pct", "inflation_pct", "verdict", "basis_note", "stage", "verify_status", "verify_note",
             "buy_url", "image_url", "rating", "review_count", "kgf_scope", "kgf_evidence"]


def write_atomic(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)  # 갱신 중에 읽어도 반쯤 쓴 파일이 보이지 않게


PART_SIZE = 20000  # GitHub Pages 파일 한도(100MB) 아래로, 조각당 약 10MB


def write_html(items, summary, sources):
    slim = [{k: it[k] for k in HTML_KEYS if it.get(k) is not None} for it in items]
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    write_atomic(OUT / "data.js", "window.KGF_DATA=" + dump({"items": [], "summary": summary, "sources": sources}) + ";")
    parts = [f"data-{n}.js" for n in range((len(slim) + PART_SIZE - 1) // PART_SIZE)]
    for n, name in enumerate(parts):
        write_atomic(OUT / name, "KGF_DATA.items.push(..." + dump(slim[n * PART_SIZE:(n + 1) * PART_SIZE]) + ");")
    for old in OUT.glob("data-*.js"):
        if old.name not in parts:
            old.unlink()
    tags = '<script src="data.js"></script>' + "".join(f'\n<script src="{p}"></script>' for p in parts)
    html = (ROOT / "scripts" / "template.html").read_text(encoding="utf-8")
    write_atomic(OUT / "index.html", html.replace('<script src="data.js"></script>', tags))


def main():
    OUT.mkdir(exist_ok=True)
    items = load()
    sources = progress(items)
    summary_path = OUT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary["count"] = len(items)
    summary["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    write_html(items, summary, sources)  # 인증표 먼저 (가장 자주 보는 산출물)
    write_atomic(OUT / "data.json", json.dumps(items, ensure_ascii=False, separators=(",", ":")))
    write_atomic(OUT / "sources_progress.json", json.dumps(sources, ensure_ascii=False, indent=1))
    write_csv(items)
    if "--xlsx" in sys.argv:  # 수만 건이면 xlsx 가 오래 걸려서 요청할 때만
        try:
            write_xlsx(items, summary)
        except PermissionError:
            print("xlsx skipped (file open in Excel)")
    print(f"{len(items)} items, {len(sources)} sources -> output/index.html, discount_table.csv/.xlsx")


if __name__ == "__main__":
    main()
