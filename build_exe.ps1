# Build EXE Windows per HostPulse
# Esecuzione (PowerShell, dalla cartella progetto):
#   .\build_exe.ps1

param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> Installazione dipendenze..."
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt pyinstaller

Write-Host "==> Build PyInstaller..."
& $PythonExe -m PyInstaller --clean --noconfirm ".\HostPulse.windows.spec"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller terminato con codice $LASTEXITCODE"
}

$DistDir = Join-Path $Root "dist"
$ExePath = Join-Path $DistDir "windows\HostPulse.exe"
if (-not (Test-Path $ExePath)) {
    $ExePath = Join-Path $DistDir "HostPulse.exe"
}
if (-not (Test-Path $ExePath)) {
    throw "EXE non trovato: $ExePath"
}

# Pacchetto distribuzione: exe + config di esempio + cartelle runtime
$ReleaseDir = Join-Path $DistDir "windows\HostPulse"
if (Test-Path $ReleaseDir) {
    Remove-Item -Recurse -Force $ReleaseDir
}
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
Copy-Item $ExePath $ReleaseDir
New-Item -ItemType Directory -Path (Join-Path $ReleaseDir "config") -Force | Out-Null
Copy-Item (Join-Path $Root "config\config.example.json") (Join-Path $ReleaseDir "config\config.json")
New-Item -ItemType Directory -Path (Join-Path $ReleaseDir "results") -Force | Out-Null

Write-Host ""
Write-Host "Build completata."
Write-Host "  EXE:        $ExePath"
Write-Host "  Pacchetto:  $ReleaseDir"
Write-Host ""
Write-Host "Copia la cartella dist\HostPulse sul server Windows e avvia HostPulse.exe."
