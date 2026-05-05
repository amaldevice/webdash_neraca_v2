# Smoke upload wizard via agent-browser (Fase 5–6).
# Prasyarat: `pip install -r requirements.txt` + `npm i -g agent-browser` + `agent-browser install`
# Jalankan Flask tanpa reloader, mis.: `$env:FLASK_APP='app'; python -m flask run --port 5000`
# Lalu: `powershell -File scripts/agent_browser_upload_smoke.ps1`

$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:5000"
$ab = Get-Command agent-browser -ErrorAction SilentlyContinue
if (-not $ab) {
    Write-Error "agent-browser tidak ada di PATH. Install: npm i -g agent-browser"
}

agent-browser open "$base/upload"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
agent-browser wait --load networkidle
agent-browser snapshot -i

Write-Host "OK: buka /upload. Lanjutkan isi form / klik Pratinjau manual bila perlu (refs dari snapshot)."
