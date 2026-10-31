"""모델명이 있는 코그페 품목의 최근 2개월 가격을 다나와 가격변동(주간 최저가)에서 가져온다. Codex 토큰 없이 돈다.

  py -3 scripts/price_danawa.py            # 아직 2개월 가격이 없는 품목 전부
  py -3 scripts/price_danawa.py --limit 50

- 다나와 검색에서 상품명에 모델명이 그대로 들어간 상품만 쓴다(부품·호환 액세서리 제외).
- 가격변동 API(period=3)의 주간 최저가 중 2026-09-01 ~ 10-28 구간: 최저=price_60d_low, 중앙값=price_60d_typical.
- 찾은 품목만 data/raw/prices/<category>/<source_id>__danawa.json 에 쓴다. 못 찾은 품목은 Codex(price.md)가 이어서 본다.
"""
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_report  # noqa: E402

CACHE = ROOT / "data" / "cache" / "html" / "danawa"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Referer": "https://www.danawa.com/"}
PERIOD = ("26-09-01", "26-10-28")  # 다나와 Fulldate 형식 YY-MM-DD
MODEL_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z]{1,6}[0-9][A-Z0-9]{3,}(?:-[A-Z0-9]{2,})?)(?![A-Za-z0-9])")


def model_of(it):
    """모델명 후보. 몰 품목의 model_code 는 몰 상품번호(EA1078355 등)라서 가전만 쓰고, 나머지는 상품명에서 찾는다."""
    code = (it.get("model_code") or "").split(".")[0] if it.get("category") == "appliance" else ""
    for text in (code, it.get("product") or ""):
        for m in MODEL_RE.findall(text):
            if len(m) >= 6 and sum(c.isdigit() for c in m) >= 2 and sum(c.isalpha() for c in m) >= 2:
                return m
    return None


def get(url, params, key, headers=UA):
    f = CACHE / key
    if f.exists():
        return f.read_text(encoding="utf-8")
    time.sleep(0.7)
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code in (403, 429):
        raise RuntimeError(f"danawa {r.status_code}")
    r.raise_for_status()
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(r.text, encoding="utf-8")
    return r.text


def find_pcode(model):
    html = get("https://search.danawa.com/dsearch.php", {"query": model}, f"search_{model}.html")
    for m in re.finditer(r'data-product-seq="(\d+)"', html):
        parts = [p.strip() for p in re.sub(r"<[^>]+>", "|", html[m.start():m.start() + 6000]).split("|")]
        parts = [p for p in parts if p and p != "이미지 보기" and not p.startswith("data-product-seq")]
        title = " ".join(parts[:2])  # 상품명 줄. 적용모델 목록(호환 부품)은 그 뒤에 나온다
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(model)}(?![A-Za-z0-9])", title):
            return m.group(1), title
    return None, None


def history(pcode):
    text = get("https://prod.danawa.com/info/ajax/getProductPriceList.ajax.php",
               {"productCode": pcode, "period": 3}, f"hist_{pcode}.json",
               {**UA, "Referer": f"https://prod.danawa.com/info/?pcode={pcode}", "X-Requested-With": "XMLHttpRequest"})
    pts = json.loads(text).get("3", {}).get("result", [])
    return [(p["Fulldate"], int(p["minPrice"])) for p in pts
            if PERIOD[0] <= p["Fulldate"] <= PERIOD[1] and p.get("minPrice")]


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    todo = [it for it in build_report.load() if not it.get("price_60d_typical") and model_of(it)]
    todo = todo[:limit] if limit else todo
    print(f"모델명 있는 미조사 품목 {len(todo)}개", flush=True)
    found, out = 0, {}
    for n, it in enumerate(todo, 1):
        model = model_of(it)
        try:
            pcode, title = find_pcode(model)
            pts = history(pcode) if pcode else []
        except (requests.RequestException, RuntimeError, ValueError) as e:
            print(f"  중단: {e}", flush=True)
            break
        prices = [p for _, p in pts]
        typ = int(statistics.median(prices)) if len(prices) >= 3 else None
        # 할인가의 절반 미만·두 배 초과면 구성(세트·패키지)이 다른 상품이 걸린 것으로 보고 버린다
        # (예: 김치톡톡 Z403MEEF53 할인가 207만 원 vs 다나와 427만 원, 2026-10-31)
        if not typ or not (0.5 <= typ / it["sale_price"] <= 2):
            continue
        found += 1
        url = f"https://prod.danawa.com/info/?pcode={pcode}"
        rec = {k: it.get(k) for k in ("item_id", "category", "source_id", "vendor", "channel", "product", "model_code",
                                      "buy_url", "image_url", "rating", "review_count", "kgf_evidence", "event_url",
                                      "claimed_original_price", "sale_price", "claimed_discount_pct", "conditions", "unit")}
        rec.update(price_60d_low=min(prices), price_60d_typical=typ, confidence="medium",
                   price_history_note=(f"다나와 주간 최저가 {len(prices)}주({pts[0][0]}~{pts[-1][0]}), 모델 {model} · "
                                       f"'{title[:60]}'. 여러 판매처 중 최저가 기준이라 몰 정가보다 낮게 나올 수 있음"),
                   sources=[url, f"https://prod.danawa.com/info/ajax/getProductPriceList.ajax.php?productCode={pcode}&period=3"])
        out.setdefault((it["category"], it["source_id"]), []).append(rec)
        if n % 50 == 0:
            print(f"  {n}/{len(todo)} 확인, {found}개 찾음", flush=True)
    for (cat, sid), items in out.items():
        f = ROOT / "data" / "raw" / "prices" / cat / f"{sid}__danawa.json"
        old = json.loads(f.read_text(encoding="utf-8")).get("items", []) if f.exists() else []
        merged = {i["item_id"]: i for i in old + items}
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"category": cat, "source_id": sid, "collected_at": datetime.now().isoformat(timespec="seconds"),
                                 "items": list(merged.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"다나와 2개월 가격: {found}/{len(todo)}개", flush=True)


if __name__ == "__main__":
    main()
