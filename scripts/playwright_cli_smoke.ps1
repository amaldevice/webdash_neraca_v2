# Smoke test via @playwright/cli (agent-friendly browser automation).
# Prerequisite: pip install -r requirements.txt; npx @playwright/cli install-browser chromium
# Usage (from repo root): pwsh -File scripts/playwright_cli_smoke.ps1
# Stops Flask when done (single-process, no debug reloader).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$runner = Join-Path $env:TEMP "webdash_flask_smoke_$PID.py"
@'
from app import app
app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
'@ | Set-Content -Path $runner -Encoding UTF8

$flask = Start-Process -FilePath python -ArgumentList @($runner) -WorkingDirectory $root -PassThru -WindowStyle Hidden

function Stop-Flask {
    if ($null -ne $flask -and -not $flask.HasExited) {
        Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -Path $runner -Force -ErrorAction SilentlyContinue
}

try {
    $ready = $false
    foreach ($i in 1..40) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "Flask did not respond on http://127.0.0.1:5000/ (is the port free?)"
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $root ".playwright-cli") | Out-Null
    $session = "webdash_smoke_$PID"

    & npx --yes @playwright/cli@latest "-s=$session" open http://127.0.0.1:5000/
    if ($LASTEXITCODE -ne 0) { throw "playwright-cli open failed" }

    & npx --yes @playwright/cli@latest "-s=$session" snapshot --filename=.playwright-cli/smoke-home.yml
    if ($LASTEXITCODE -ne 0) { throw "playwright-cli snapshot home failed" }

    & npx --yes @playwright/cli@latest "-s=$session" click e18
    if ($LASTEXITCODE -ne 0) { throw "playwright-cli click e18 (Unggah Data) failed" }

    & npx --yes @playwright/cli@latest "-s=$session" snapshot --filename=.playwright-cli/smoke-after-nav-upload.yml

    & npx --yes @playwright/cli@latest "-s=$session" eval "window.location.pathname"
    if ($LASTEXITCODE -ne 0) { throw "playwright-cli eval failed" }

    & npx --yes @playwright/cli@latest "-s=$session" close
}
finally {
    Stop-Flask
}

Write-Host "playwright-cli smoke finished OK."
