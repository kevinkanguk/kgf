"""모델명 없는 코그페 품목을 다나와 상품명 검색으로 찾아 같은 상품의 2개월 가격이력(주간 최저가)을 붙인다. Codex 토큰 없이 돈다.

  py -3 scripts/price_crossmall.py --limit 200 --dry     # 시험: 파일은 안 쓰고 .tmp/crossmall_check.tsv 에 판정 표만
  py -3 scripts/price_crossmall.py                       # 남은 품목 전부 (price_todo.py 와 같은 대상)
  py -3 scripts/price_crossmall.py --mark-missing        # 못 찾은 품목에 "이력 없음:" 도 기록 (Codex 가 다시 안 봄)
  py -3 scripts/price_crossmall.py --shard 1/3 & ... --shard 3/3   # 병렬. 다나와 차단을 피하려고 3개 정도까지

같은 상품 판정(하나라도 어긋나면 버림, 2026-11-01):
- 브랜드: [대괄호] 브랜드(없으면 몰 이름이 아닌 판매 업체명)가 다나와 상품명에 있어야 함. 둘 다 없으면 상품명 첫 단어가
  다나와 상품명 첫 단어와 같아야 함.
- 상품명: 품목 낱말이 다나와 상품명에 전부 있고, 다나와에만 있는 낱말은 1개까지(맛·향·품종·라인 다른 상품 제외). 4자 이상은 한 글자 차 표기 허용.
- 구성: '+' 구성 수가 같고, 연도·품위(못난이·가정용, 다나와에만 있어도)·등급(1++·UMF·특대)·호수·과수(5-7과)가 다르면 버림.
- 옵션 상품(1+1·골라담기·500g/1kg·500g, 700g·2~10kg)과 개수 표시가 겹치는 품목(2박스(190ml*32팩))은 안 봄.
- 규격: 품목의 중량·용량(g·ml 환산) 중 하나가 다나와 상품명의 중량·용량과 같아야 함. 규격 없는 품목은 안 봄.
- 개수: 품목 총개수 = 다나와 상품명 개수 × 다나와 개수별 행(1개·5개…).
- 가격: 2개월 중앙값이 할인가의 0.5~2배 (price_danawa.py 와 같은 기준).
결과는 price.md 1번(가격 이력) 형식으로 data/raw/prices/<category>/<source_id>__crossmall.json 에 쓴다.
"""
import html
import json
import re
import statistics
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_report  # noqa: E402
from price_danawa import get, history, model_of  # noqa: E402

SEARCH = "https://search.danawa.com/dsearch.php"
MALL_VENDOR = re.compile(r"우체국|G마켓|지마켓|11번가|판매자|소상공인|오아시스|롯데ON|스토아|SSG|이마트|쿠팡|Hmall|홈쇼핑|마켓$")
OPTION = re.compile(r"1\+1|2\+1|골라|택\s?[1-9]|중\s?택|선택|옵션|모음|균일|외\s|\d종|종류"
                    r"|\d\s*(?:kg|g|ml|l|개|팩|병|봉|통)?\s*/\s*\d"  # 500g/1kg, x1/2/3봉 (어느 규격 값인지 모름)
                    r"|\d\s*~\s*\d+(?:\.\d+)?\s*(?:kg|g)"  # 2~10kg
                    r"|\d\s*(?:kg|g|ml|l)\s*,\s*\d", re.I)  # 500g, 700g
PLUS = re.compile(r"[0-9a-z가-힣)]\s*\+\s*(?=[0-9가-힣])(?!등급)", re.I)  # 500g+500g, 참기름+들기름 (1+등급 제외)
TAGS = {  # 둘 다 있는데 값이 다르면 다른 상품 (연도는 다나와에만 있어도 다름: 지난해산 목록)
    "연도": re.compile(r"(?<!\d)(?:20)?(2[0-9])(?=\s*년)|(?<!\d)20(2[0-9])(?![\d.a-z가-힣])"),  # 26년, 2025
    "등급": re.compile(r"(1\+\+|1\+(?!\+)|투뿔|원뿔|umf\s*\d+|mgo\s*\d+|특특대|특대|왕특|약초|특초|상초|대과|중과|소과)", re.I),
    "품위": re.compile(r"(못난이|흠과|가정용|선물용|정품)"),  # 다나와에만 있어도 다름 (정품형 vs 못난이)
    "호수": re.compile(r"(\d+)\s*호(?![가-힣])"),
    "과수": re.compile(r"(\d+\s*[-~]?\s*\d*)\s*(?:과|미)(?![가-힣])"),
}
PROMO = re.compile(r"쿠폰|증정|%|특가|무료|단독|신선|행사|할인|배송|접속|기프티콘|당일|출고|최저|한정|인기|품질|보장|직송|정품|공식|본사|추천|best", re.I)
NOT_BRAND = {"국내산", "국산", "수입산", "햇", "신선", "프리미엄", "대용량", "정품", "산지직송", "당일", "특가", "명품", "고급",
             "1등급", "1+등급", "무항생제", "친환경", "유기농", "선물세트", "선물", "추석", "명절", "가정용", "업소용", "new", "NEW"}
AMOUNT = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g|mg|ml|l|리터|키로)(?![a-wyz])", re.I)  # 20gx10 의 x 는 허용
COUNT = re.compile(r"(\d+)\s*(개입|개|입|팩|병|봉|포|매|롤|구|캔|박스|box|ea|세트|set|장|미|마리|통|알|정|캡슐|스틱)(?![가-힣a-z])", re.I)
SCALE = {"kg": 1000, "키로": 1000, "g": 1, "mg": 0.001, "l": 1000, "리터": 1000, "ml": 1}


def norm(s):
    return re.sub(r"[^0-9a-z가-힣]", "", (s or "").lower())


def amounts(text):
    return {round(float(n) * SCALE[u.lower()], 3) for n, u in AMOUNT.findall(text)}


def count_of(text):
    """총개수. 개수 표시 없음=1, 'A x B' 곱, 그 밖에 개수 표시가 둘 이상이면 모름(None)."""
    text = AMOUNT.sub(" @ ", text)
    m = re.search(r"@\s*[x×*]\s*(\d+)", text, re.I)  # 1L x 5개
    if m:  # 2박스(190ml*32팩) 처럼 다른 개수 표시가 또 있으면 모름
        others = {int(n) for n, _ in COUNT.findall(text[:m.start()] + text[m.end():])} - {1}
        return None if others else int(m.group(1))
    m = re.search(r"(\d+)\s*[가-힣a-z]*\s*[x×*]\s*(\d+)", text, re.I)  # 3입 x 2개
    if m:
        return int(m.group(1)) * int(m.group(2))
    cs = {int(n) for n, _ in COUNT.findall(text)}
    return 1 if not cs else cs.pop() if len(cs) == 1 else None


def brands(it):
    name = it.get("product") or ""
    out = [b for b in re.findall(r"\[([^\]]+)\]", name) if not PROMO.search(b)]  # [브랜드] 가 판매 업체명보다 먼저
    v = (it.get("vendor") or "").split("(")[0].strip()
    if v and not MALL_VENDOR.search(v):
        out.append(v)
    out = [b for b in dict.fromkeys(norm(b) for b in out) if len(b) >= 2]
    words = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", name).split()
    if not out and words and words[0] not in NOT_BRAND and not re.search(r"\d", words[0]) and len(norm(words[0])) >= 2:
        return [norm(words[0])], True  # 상품명 첫 단어: 브랜드인지 모르므로 다나와 상품명 첫 단어와 같아야 인정
    return out, False


def words(text):
    """상품명 낱말(괄호·규격·개수·연도·홍보 문구 빼고 2자 이상). 귀리렌틸혼합17곡 처럼 숫자 섞인 이름은 남긴다."""
    text = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", text)
    text = TAGS["연도"].sub(" ", COUNT.sub(" ", AMOUNT.sub(" ", text)))
    return {norm(w) for w in re.split(r"[\s,/+&]+", text)
            if len(re.sub(r"[^가-힣a-z]", "", w.lower())) >= 2 and not PROMO.search(w) and w not in NOT_BRAND}


def has(w, text):
    """낱말이 text 에 있음. 4자 이상은 한 글자 차 표기 차이(플래티늄/플레티늄)까지 같다고 본다."""
    if w in text:
        return True
    return len(w) >= 4 and any(SequenceMatcher(None, w, text[i:i + len(w)]).ratio() >= 0.75
                               for i in range(len(text) - len(w) + 1))


def tags(rx, text):
    return {re.sub(r"\s", "", "".join(v) if isinstance(v, tuple) else v).replace("~", "-") for v in rx.findall(text.lower())}


def query_of(it, brand):
    words = [w for w in re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", it.get("product") or "").split()
             if not PROMO.search(w) and w not in NOT_BRAND and norm(w) != brand]
    core = [w for w in words if not re.search(r"\d", w)][:2]
    spec = next((w for w in words if AMOUNT.search(w)), "")
    return " ".join([brand] + core + [spec]).strip()


def products(page):
    """다나와 검색결과 → [(상품명, [(개수, pcode, 최저가, 몰수), ...])]."""
    out = []
    blocks = re.split(r'data-product-seq="\d+"', page)[1:]
    for blk in blocks:
        m = re.search(r'<img alt="([^"]+)"', blk)
        if not m:
            continue
        title = re.sub(r"<[^>]+>", "", html.unescape(m.group(1)))
        rows = []
        for r in re.finditer(r">(\d+)개</span>.*?pcode=(\d+)[^>]*>.*?>([\d,]+)원</span>.*?>(\d+)<!-- -->몰", blk, re.S):
            rows.append((int(r.group(1)), r.group(2), int(r.group(3).replace(",", "")), int(r.group(4))))
        out.append((title, rows))
    return out


def judge(it):
    """(판정, 상세). 판정: match / skip / none."""
    text = f"{it.get('product') or ''} {it.get('unit') or ''}"
    if OPTION.search(text) or (len(amounts(text)) > 1 and not re.search(r"[x×*(+]", text, re.I)):  # 100ml 250ml
        return "skip", "옵션 상품"
    amts, cnt, (bs, weak) = amounts(text), count_of(text), brands(it)
    if not amts or cnt is None or not bs:
        return "skip", f"규격{sorted(amts)} 개수{cnt} 브랜드{bs}"
    tried, iw, nitem = [], words(it.get("product") or ""), norm(text)
    for brand in bs[:2]:
        q = query_of(it, brand)
        tried.append(q)
        page = get(SEARCH, {"query": q}, f"xm_{norm(q)[:80]}.html")
        for title, rows in products(page):
            nt = norm(title)
            # 오매칭 사례(2026-11-01 380건 검토, 오매칭 22·애매 78): '[진우담] 투뿔한우' vs '소돈가 투뿔한우',
            # '오리진' vs '골드녹용' 홍삼, 호박고구마 vs 꿀고구마, 26년산 vs 2025년, 1+ 1호 vs 1++ 12호, 5-7과 vs 8~9과
            if bs[0] not in nt or OPTION.search(title) or (weak and norm((title.split() or [""])[0]) != bs[0]):
                continue
            if not all(has(w, nt) for w in iw):  # 품목 낱말은 다나와 상품명에 전부 있어야 (맛·향·품종·라인)
                continue
            extra = [w for w in words(title) if not has(w, nitem) and not any(b in w for b in bs)]
            if len(extra) > 1:  # 다나와에만 있는 낱말은 1개(약산성 등)까지: '양배추 브로콜리', '최씨네참기름 들기름' 버림
                continue
            if len(PLUS.findall(text)) != len(PLUS.findall(title)):  # 500g+500g, 참기름+들기름(+생들기름)
                continue
            if any(tags(t, title) - tags(t, text) for k, t in TAGS.items()
                   if k in ("연도", "품위") or tags(t, text)):  # 연도·등급·호수·과수 다름
                continue
            tamts = amounts(title)
            if not tamts & amts:
                continue
            tcnt = count_of(title) or 1
            for qty, pcode, price, malls in rows:
                if tcnt * qty != cnt:
                    continue
                pts = history(pcode)
                prices = [p for _, p in pts]
                typ = int(statistics.median(prices)) if len(prices) >= 3 else None
                if typ and 0.5 <= typ / it["sale_price"] <= 2:
                    return "match", dict(title=title, qty=qty, pcode=pcode, pts=pts, typ=typ, low=min(prices), query=q,
                                         why=f"브랜드 {'/'.join(b for b in bs if b in nt)}, 규격 {sorted(tamts & amts)}, 개수 {cnt}")
    return "none", tried


def main():
    args = sys.argv
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    dry, mark = "--dry" in args, "--mark-missing" in args
    todo = [it for it in build_report.load()
            if not it.get("price_60d_typical") and not it.get("price_history_note") and not model_of(it)]
    todo.sort(key=lambda it: -(it.get("shown_discount_pct") or 0))
    if "--shard" in args:  # --shard 1/3: 소스 단위로 나눠 여러 프로세스가 같은 파일을 동시에 쓰지 않게 한다
        k, total = map(int, args[args.index("--shard") + 1].split("/"))
        sids = sorted({it["source_id"] for it in todo})
        mine = set(sids[k - 1::total])
        todo = [it for it in todo if it["source_id"] in mine]
    todo = todo[:limit] if limit else todo
    print(f"대상 {len(todo)}개", flush=True)
    out, check, tally = {}, [], {"match": 0, "skip": 0, "none": 0}
    for n, it in enumerate(todo, 1):
        try:
            kind, d = judge(it)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code >= 500:  # 특정 검색어만 500 (예: '... /쇼핑백포함') → 그 품목만 건너뜀
                tally["skip"] += 1
                continue
            print(f"  중단: {e}", flush=True)
            break
        except (requests.RequestException, RuntimeError, ValueError) as e:
            print(f"  중단: {e}", flush=True)
            break
        tally[kind] += 1
        rec = None
        if kind == "match":
            pts = d["pts"]
            rec = dict(item_id=it["item_id"], price_60d_low=d["low"], price_60d_typical=d["typ"], confidence="medium",
                       price_history_note=(f"다나와 주간 최저가 {len(pts)}주({pts[0][0]}~{pts[-1][0]}), "
                                           f"'{d['title'][:50]}' {d['qty']}개 · 같은 상품 판정: {d['why']}. "
                                           "여러 판매처 중 최저가 기준"),
                       sources=[f"https://prod.danawa.com/info/?pcode={d['pcode']}",
                                f"https://prod.danawa.com/info/ajax/getProductPriceList.ajax.php?productCode={d['pcode']}&period=3"])
            check.append([it["item_id"], it["product"], it.get("unit") or "", it["sale_price"], d["title"], d["qty"], d["typ"]])
        elif kind == "none" and mark:
            rec = dict(item_id=it["item_id"], price_60d_low=None, price_60d_typical=None, confidence="low",
                       price_history_note=f"이력 없음: 다나와 상품명 검색({' / '.join(d)})에 같은 브랜드·규격·개수 상품 없음",
                       sources=[f"{SEARCH}?{urlencode({'query': q})}" for q in d])
        if rec:
            out.setdefault((it["category"], it["source_id"]), []).append(rec)
        if n % 50 == 0:
            print(f"  {n}/{len(todo)} {tally}", flush=True)
    tag = args[args.index("--shard") + 1].replace("/", "of") if "--shard" in args else ""
    tsv = ROOT / ".tmp" / f"crossmall_check{tag}.tsv"
    tsv.parent.mkdir(exist_ok=True)
    tsv.write_text("\n".join("\t".join(map(str, r)) for r in
                             [["item_id", "품목", "단위", "할인가", "다나와 상품명", "개수", "2개월 중앙값"]] + check), encoding="utf-8")
    if not dry:
        for (cat, sid), items in out.items():
            f = ROOT / "data" / "raw" / "prices" / cat / f"{sid}__crossmall.json"
            old = json.loads(f.read_text(encoding="utf-8")).get("items", []) if f.exists() else []
            merged = {i["item_id"]: i for i in old + items}
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({"category": cat, "source_id": sid,
                                     "collected_at": datetime.now().isoformat(timespec="seconds"),
                                     "items": list(merged.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"타몰(다나와) 2개월 가격: 찾음 {tally['match']}, 못 찾음 {tally['none']}, 판정 불가 {tally['skip']} "
          f"{'(시험, 파일 안 씀)' if dry else ''} -> 판정 표 {tsv.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
