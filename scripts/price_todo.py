"""Codex 가격 조사 대상 목록을 미리 뽑는다 -> .tmp/price_todo.json. Codex 가 대상을 찾느라 토큰을 쓰지 않게 하기 위함.

  py -3 scripts/price_todo.py            # 100개 (KGF_PRICE_BATCH 로 바꿈)

대상: 인증표 범위 품목 중 2개월 가격도, price_history_note 도 없고, 다나와 스크립트 대상(모델명)이 아닌 것. 표시 할인율 큰 순.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_report  # noqa: E402
from price_danawa import model_of  # noqa: E402

KEYS = ("item_id", "category", "source_id", "vendor", "product", "unit", "claimed_original_price", "sale_price",
        "shown_discount_pct", "buy_url")


def main():
    n = int(os.environ.get("KGF_PRICE_BATCH", "100"))
    todo = [it for it in build_report.load()
            if not it.get("price_60d_typical") and not it.get("price_history_note") and not model_of(it)]
    todo.sort(key=lambda it: -(it.get("shown_discount_pct") or 0))
    out = ROOT / ".tmp" / "price_todo.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"remaining": len(todo), "items": [{k: it.get(k) for k in KEYS} for it in todo[:n]]},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"가격 조사 대상 {min(n, len(todo))}개 / 남은 {len(todo)}개 -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
