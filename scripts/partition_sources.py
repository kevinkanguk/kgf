"""data/sources/*.json 을 겹치지 않는 N개 묶음으로 나눈다 (워크플로 병렬 실행용).

- URL 기준 중복 소스 제거, login 소스 제외
- 이미 data/raw/catalog/<cat>/<source_id>.json 이 있는 소스는 제외 (재실행 시 이어하기)
- est_items 합이 비슷하도록 큰 소스부터 가장 가벼운 묶음에 배정

Usage: py scripts/partition_sources.py [N=3]  -> harness/partitions/part<i>.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seen_url, seen_id, todo, dup, done = set(), set(), [], [], 0
    for f in sorted((ROOT / "data" / "sources").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for s in doc.get("sources", []):
            s["category"] = doc.get("category", f.stem)
            if s.get("access") == "login":
                continue
            if s["url"] in seen_url or s["source_id"] in seen_id:
                dup.append(s["source_id"])
                continue
            seen_url.add(s["url"])
            seen_id.add(s["source_id"])
            if (ROOT / "data" / "raw" / "catalog" / s["category"] / f"{s['source_id']}.json").exists():
                done += 1
                continue
            todo.append(s)

    parts = [{"sources": [], "est": 0} for _ in range(n)]
    for s in sorted(todo, key=lambda x: -(x.get("est_items") or 10)):
        p = min(parts, key=lambda x: x["est"])
        p["sources"].append(s)
        p["est"] += s.get("est_items") or 10

    out = ROOT / "harness" / "partitions"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("part*.json"):
        old.unlink()
    for i, p in enumerate(parts):
        (out / f"part{i}.json").write_text(json.dumps(p["sources"], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"part{i}: {len(p['sources'])} sources, est {p['est']} items")
    print(f"todo {len(todo)}, already done {done}, duplicate removed {len(dup)}")


if __name__ == "__main__":
    main()
