# Build EXE Windows per HostPulse
# Esecuzione (PowerShell, dalla cartella progetto):
#   .\build_exe.ps1
# Firma opzionale (Authenticode):
#   $env:HOSTPULSE_SIGN_PFX = 'C:\path\codesign.pfx'
#   $env:HOSTPULSE_SIGN_PASSWORD = '***'
#   .\build_exe.ps1

param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> Version resource"
& $PythonExe ".\scripts\generate_version_info.py"
if ($LASTEXITCODE -ne 0) { throw "generate_version_info failed" }

Write-Host "==> Installazione dipendenze..."
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt pyinstaller

Write-Host "==> Build PyInstaller (onedir, no UPX)..."
& $PythonExe -m PyInstaller --clean --noconfirm --distpath "dist\windows" ".\HostPulse.windows.spec"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller terminato con codice $LASTEXITCODE"
}

$ReleaseDir = Join-Path $Root "dist\windows\HostPulse"
$ExePath = Join-Path $ReleaseDir "HostPulse.exe"
if (-not (Test-Path $ExePath)) {
    throw "EXE non trovato: $ExePath (atteso layout onedir dist\windows\HostPulse\)"
}

Write-Host "==> Firma Authenticode (se configurata)..."
& (Join-Path $Root "scripts\sign_exe.ps1") -ExePath $ExePath

New-Item -ItemType Directory -Path (Join-Path $ReleaseDir "config") -Force | Out-Null
Copy-Item (Join-Path $Root "config\config.example.json") (Join-Path $ReleaseDir "config\config.json") -Force
New-Item -ItemType Directory -Path (Join-Path $ReleaseDir "results") -Force | Out-Null

$hash = (Get-FileHash -Algorithm SHA256 $ExePath).Hash
$hashFile = Join-Path $ReleaseDir "SHA256.txt"
@(
    "HostPulse.exe SHA256",
    $hash,
    "Verify: Get-FileHash -Algorithm SHA256 .\HostPulse.exe",
    "Release: https://github.com/Never-lab/hostpulse/releases/latest"
) | Set-Content -Encoding UTF8 $hashFile

Write-Host ""
Write-Host "Build completata."
Write-Host "  EXE:        $ExePath"
Write-Host "  Pacchetto:  $ReleaseDir  (HostPulse.exe + _internal\)"
Write-Host "  SHA256:     $hash"
Write-Host ""
Write-Host "Distribuisci l'intera cartella HostPulse (non solo l'exe)."
