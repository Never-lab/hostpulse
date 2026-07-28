# Sign HostPulse.exe with Authenticode (optional — reduces SmartScreen / Defender friction).
# Usage:
#   $env:HOSTPULSE_SIGN_PFX = 'C:\path\cert.pfx'
#   $env:HOSTPULSE_SIGN_PASSWORD = 'secret'
#   .\scripts\sign_exe.ps1 -ExePath dist\windows\HostPulse\HostPulse.exe
param(
    [Parameter(Mandatory = $true)]
    [string]$ExePath,
    [string]$PfxPath = $env:HOSTPULSE_SIGN_PFX,
    [string]$Password = $env:HOSTPULSE_SIGN_PASSWORD,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $ExePath)) { throw "EXE not found: $ExePath" }
if (-not $PfxPath -or -not (Test-Path $PfxPath)) {
    Write-Host "Skip signing: HOSTPULSE_SIGN_PFX not set or file missing."
    exit 0
}
if (-not $Password) { throw "HOSTPULSE_SIGN_PASSWORD required when signing." }

function Find-SignTool {
    $sdk = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
    if (Test-Path $sdk) {
        $hit = Get-ChildItem -Path $sdk -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'x64\\signtool\.exe$' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$signtool = Find-SignTool
if (-not $signtool) { throw "signtool.exe not found (install Windows SDK)." }

Write-Host "==> Signing $ExePath"
& $signtool sign /fd SHA256 /f $PfxPath /p $Password /tr $TimestampUrl /td SHA256 $ExePath
if ($LASTEXITCODE -ne 0) { throw "signtool failed with $LASTEXITCODE" }
Write-Host "Signed OK."
