"""코그페 인증표 갱신 1회 실행 (CODEX.md 순서). dealbot 의 codex_tick.py 와 같은 구조.

  1. git pull --rebase
  2. (--refresh) 기존 수집 스크립트 재실행  -> data/raw/catalog
  3. codex exec find.md   -> 새 소스·새 품목 (웹 검색)
  4. codex exec price.md  -> 2개월 가격 조사·검증
  5. build_report --xlsx, qa_html          -> output/
  6. commit "codex: run ..." + push (qa 실패면 push 안 함)

Codex CLI 는 Codex 데스크톱 앱에 들어 있는 %LOCALAPPDATA%/OpenAI/Codex/bin/*/codex.exe 또는 KGF_CODEX.
Log: .tmp/tick.log

  py -3 scripts/codex_tick.py --dry-run    # 무엇을 할지만 출력
  py -3 scripts/codex_tick.py              # 실제 실행
  py -3 scripts/codex_tick.py --refresh    # 기존 사이트도 다시 긁기 (오래 걸림)
  py -3 scripts/codex_tick.py --no-codex   # Codex 없이 재수집·표 생성만
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / ".tmp"
LOG = TMP / "tick.log"
CODEX_TIMEOUT_S = 60 * 60
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
# Codex 샌드박스에서는 py 런처가 시스템 Python 을 못 찾는다(2026-10-31). 저장소 안 .venv 를 쓴다
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
PY_NOTE = ("[실행 환경] 이 PC 에서 Python 은 반드시 `.venv/Scripts/python.exe -I <스크립트>` 로 실행한다 "
           "(`py`, `python` 은 샌드박스에서 안 된다). requests·openpyxl 설치돼 있음. 네트워크 사용 가능.\n\n")


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    TMP.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, timeout=None):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    # stdin 을 닫아야 codex exec 가 추가 입력을 기다리지 않는다
    return subprocess.run([str(c) for c in cmd], cwd=ROOT, env=env, text=True, encoding="utf-8",
                          errors="replace", capture_output=True, timeout=timeout,
                          stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)


def find_codex():
    if os.environ.get("KGF_CODEX"):
        return os.environ["KGF_CODEX"]
    found = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "OpenAI", "Codex", "bin", "*", "codex.exe"))
    found += [p for p in (shutil.which("codex"),) if p]
    return max(found, key=os.path.getmtime) if found else None


def codex(prompt_file, out_file, dry):
    exe = find_codex()
    if not exe:
        log("  codex.exe not found (Codex 데스크톱 앱 설치·로그인 필요)")
        return False
    cmd = [exe, "exec", "--ephemeral", "-C", ROOT, "-s", "workspace-write",
           "-c", 'approval_policy="never"', "-c", 'web_search="live"',
           # 샌드박스 안에서도 사이트 JSON API 수집(requests)이 되게 네트워크를 연다
           "-c", "sandbox_workspace_write.network_access=true", "-o", TMP / out_file,
           PY_NOTE + (ROOT / prompt_file).read_text(encoding="utf-8")]
    if dry:
        log(f"  [dry] {exe} exec ... {prompt_file}")
        return True
    try:
        proc = run(cmd, timeout=CODEX_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        log(f"  codex timed out ({prompt_file})")
        return False
    log(f"  codex {Path(prompt_file).stem}: exit {proc.returncode} · " + " / ".join((proc.stdout or "").strip().splitlines()[-3:])[:300])
    lines = (proc.stdout + proc.stderr).splitlines()
    for i, l in enumerate(lines):  # codex exec 는 "tokens used" 다음 줄에 숫자를 찍는다
        if "tokens used" in l.lower():
            log(f"  codex {Path(prompt_file).stem}: tokens used {(l.split(':')[-1].strip() or (lines[i + 1] if i + 1 < len(lines) else '')).strip()}")
    return proc.returncode == 0


def step(cmd, dry, timeout=None):
    if dry:
        log("  [dry] " + " ".join(map(str, cmd)))
        return 0
    proc = run(cmd, timeout)
    for line in (proc.stdout + proc.stderr).strip().splitlines()[-4:]:
        log("    " + line)
    return proc.returncode


def refresh_scrapers(dry):
    # 수집 스크립트는 data/cache/html 을 재사용하므로, 새로 받으려면 캐시를 지운다
    if not dry:
        shutil.rmtree(ROOT / "data" / "cache" / "html", ignore_errors=True)
    for f in sorted((ROOT / "scripts" / "scrapers").glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            rc = step([VENV_PY if VENV_PY.exists() else sys.executable, "-I", f], dry, timeout=30 * 60)
        except subprocess.TimeoutExpired:
            rc = "timeout"
        if rc:
            log(f"  scraper {f.stem}: {rc}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="기존 수집 스크립트도 다시 실행")
    ap.add_argument("--no-codex", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    dry = a.dry_run
    os.chdir(ROOT)
    log(f"tick start (dry={dry}, refresh={a.refresh}, codex={not a.no_codex})")
    if run(["git", "status", "--porcelain", "--untracked-files=no"]).stdout.strip() and not dry:
        log("  커밋 안 한 변경이 있어 쉰다")
        return 0
    if step(["git", "pull", "--rebase"], dry):
        log("  git pull 실패")
        return 1
    if a.refresh:
        refresh_scrapers(dry)
    if not a.no_codex:
        codex(".github/codex/find.md", "find-report.txt", dry)
        codex(".github/codex/price.md", "price-report.txt", dry)
    step([sys.executable, "scripts/build_report.py", "--xlsx"], dry, timeout=60 * 60)
    qa_failed = step([sys.executable, "scripts/qa_html.py"], dry) != 0
    step(["git", "add", "data", "output", "scripts/scrapers"], dry)
    if step(["git", "commit", "-qm", f"codex: run {datetime.now():%Y-%m-%d %H:%M}"], dry):
        log("  바뀐 것 없음")
    if qa_failed:
        log("  qa_html 실패: push 하지 않음 (.tmp/tick.log 확인)")
        return 1
    if not a.no_push:
        step(["git", "push"], dry)
    log("tick done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
