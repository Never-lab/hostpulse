# Local verify for HostPulse (dev machine).
# Usage (from repo root):
#   .\scripts\verify_local.ps1
#   .\scripts\verify_local.ps1 -BuildExe

param(
    [switch]$BuildExe,
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Install deps"
& $PythonExe -m pip install -q -r requirements.txt -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

Write-Host "==> Ruff"
& $PythonExe -m ruff check bin tests
if ($LASTEXITCODE -ne 0) { throw "ruff failed" }

Write-Host "==> compileall"
& $PythonExe -m compileall -q bin
if ($LASTEXITCODE -ne 0) { throw "compileall failed" }

Write-Host "==> Pytest"
& $PythonExe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "==> Import smoke (PYTHONPATH=bin)"
$env:PYTHONPATH = (Join-Path $Root "bin")
& $PythonExe -c "import app_paths, engine, reporter_generator, version, ui_benchmark; print('imports ok', version.__version__)"
if ($LASTEXITCODE -ne 0) { throw "import smoke failed" }

if ($BuildExe) {
    Write-Host "==> PyInstaller build"
    & (Join-Path $Root "build_exe.ps1") -PythonExe $PythonExe
    if ($LASTEXITCODE -ne 0) { throw "build_exe failed" }
    $exe = Join-Path $Root "dist\windows\HostPulse\HostPulse.exe"
    if (-not (Test-Path $exe)) {
        $exe = Join-Path $Root "dist\windows\HostPulse.exe"
    }
    if (-not (Test-Path $exe)) { throw "EXE not found after build" }
    Write-Host "EXE ok: $exe"
}

Write-Host ""
Write-Host "verify_local OK"
