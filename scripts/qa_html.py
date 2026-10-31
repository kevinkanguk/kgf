"""output/index.html 정적 검사. 실패 시 exit 1.

Usage: py scripts/qa_html.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"


def main():
    fails, warns = [], []  # fails: 페이지·표가 깨짐(push 막음) / warns: 원천 데이터 빈칸 등
    if 'src="data.js"' not in (OUT / "index.html").read_text(encoding="utf-8"):
        print("FAIL: index.html does not load data.js")
        sys.exit(1)
    slim_ids = []
    for p in sorted(OUT.glob("data-*.js"), key=lambda f: int(f.stem.split("-")[1])):
        js = p.read_text(encoding="utf-8")
        slim_ids += [i["item_id"] for i in json.loads(js[len("KGF_DATA.items.push(..."):].rstrip().rstrip(";").rstrip(")"))]
    items = json.loads((OUT / "data.json").read_text(encoding="utf-8"))  # 내용 검사는 전체 필드로
    if slim_ids != [i["item_id"] for i in items]:
        fails.append("data.js and data.json item order/ids differ")
    csv_rows = (OUT / "discount_table.csv").read_text(encoding="utf-8-sig").strip().splitlines()[1:]

    if not items:
        fails.append("no items embedded")
    if len(csv_rows) < len(items):
        fails.append(f"csv rows {len(csv_rows)} < items {len(items)}")
    ids = [i["item_id"] for i in items]
    if len(ids) != len(set(ids)):
        fails.append("duplicate item_id")
    for i in items:
        tag = i.get("item_id")
        if not re.match(r"^https?://", i.get("buy_url") or ""):
            warns.append(f"{tag}: buy_url missing/invalid")
        for k in ("vendor", "channel", "product"):
            if not i.get(k):
                warns.append(f"{tag}: {k} empty")
        typ, sale = i.get("price_60d_typical"), i.get("sale_price")
        if typ and sale:
            exp = round((typ - sale) / typ * 100, 1)
            if abs(exp - (i.get("real_discount_pct") or 0)) > 0.11:
                fails.append(f"{tag}: real_discount_pct {i.get('real_discount_pct')} != {exp}")
        if (i.get("claimed_original_price") or 0) and sale and sale > i["claimed_original_price"]:
            warns.append(f"{tag}: sale_price > claimed_original_price")
        if not i.get("sources"):
            warns.append(f"{tag}: no sources")

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"items={len(items)} checks_failed={len(fails)} warnings={len(warns)}")
    for f in fails[:50]:
        print("FAIL:", f)
    for w in warns[:20]:
        print("WARN:", w)
    if len(warns) > 20:
        print(f"... and {len(warns) - 20} more warnings")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
