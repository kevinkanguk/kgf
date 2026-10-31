#!/usr/bin/env bash
# 인증표(output/index.html) 자동 갱신 루프. output/ 에 쓰는 프로세스는 이것 하나뿐이어야 한다.
#   INTERVAL 초마다 build_report.py 재실행, COMMIT_EVERY 회마다 data/·output/ 변경분을 로컬 커밋(push 없음)
# Usage: bash scripts/live_refresh.sh [INTERVAL=120] [COMMIT_EVERY=5]
cd "$(dirname "$0")/.." || exit 1
INTERVAL=${1:-120}
COMMIT_EVERY=${2:-5}
n=0
while true; do
  XLSX=""; [ $(((n + 1) % COMMIT_EVERY)) -eq 0 ] && XLSX="--xlsx"
  py scripts/build_report.py $XLSX 2>&1 | tail -1 | sed "s/^/[$(date +%H:%M)] /"
  n=$((n + 1))
  if [ $((n % COMMIT_EVERY)) -eq 0 ] && [ -n "$(git status --porcelain data output scripts/scrapers)" ]; then
    git add data output scripts/scrapers >/dev/null 2>&1
    git commit -qm "Auto: 인증표 갱신 $(date '+%m-%d %H:%M')

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" >/dev/null 2>&1 && echo "[$(date +%H:%M)] committed"
  fi
  [ -f output/.stop ] && { rm -f output/.stop; echo stopped; exit 0; }
  sleep "$INTERVAL"
done
