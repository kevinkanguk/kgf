# 코그페 인증표 갱신(scripts/codex_tick.py)을 Windows 작업 스케줄러에 등록한다. dealbot install_tick.ps1 과 같은 방식.
# 아직 등록하지 않았다(준비만). 켜고 싶을 때 실행:
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_tick.ps1              # 등록 (6시간마다)
#   powershell -ExecutionPolicy Bypass -File scripts\install_tick.ps1 -Hours 12
#   powershell -ExecutionPolicy Bypass -File scripts\install_tick.ps1 -Uninstall
#   schtasks /Change /TN "KGF tick" /DISABLE    (또는 /ENABLE)
param([switch]$Uninstall, [int]$Hours = 6)

$ErrorActionPreference = "Stop"
$name = "KGF tick"
$repo = Split-Path -Parent $PSScriptRoot

if ($Uninstall) {
    schtasks /Delete /TN $name /F
    exit $LASTEXITCODE
}

$pyw = (Get-Command pyw -ErrorAction SilentlyContinue).Source
if (-not $pyw) { throw "pyw (Python launcher) not found" }
$script = Join-Path $repo "scripts\codex_tick.py"

# 로그인한 동안만 실행(/IT) — git 과 Codex 가 사용자 자격 증명을 쓴다
schtasks /Create /TN $name /SC HOURLY /MO $Hours /TR "`"$pyw`" -3 `"$script`"" /IT /F | Out-Null
if ($LASTEXITCODE -ne 0) { throw "schtasks failed ($LASTEXITCODE)" }
Write-Output "installed: $name (every $Hours h) -> $pyw $script"
