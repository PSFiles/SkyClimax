<#
.SYNOPSIS
    Install the pinned SkyClimax toolchain into the repository.

.DESCRIPTION
    Downloads each tool from its official source, verifies the SHA-256 when the
    vendor publishes one, and extracts it under .tools/. Idempotent: a tool whose
    recorded version already matches is skipped.

    Nothing is installed outside the repository and no administrator rights are
    required.

.PARAMETER Force
    Reinstall even when the recorded version matches.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/install-tools.ps1
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ToolsDir = Join-Path $RepoRoot '.tools'
$DownloadDir = Join-Path $ToolsDir 'downloads'

# --- pinned versions -------------------------------------------------------
$versionsFile = Join-Path $PSScriptRoot 'versions.env'
if (-not (Test-Path $versionsFile)) { throw "missing $versionsFile" }
Get-Content $versionsFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z0-9_]+)="(.*)"\s*$') {
        Set-Variable -Name $matches[1] -Value $matches[2] -Scope Script
    }
}

function Write-Step([string]$Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Skip([string]$Message) { Write-Host "    skip: $Message" -ForegroundColor DarkGray }

function Get-Verified {
    param([string]$Url, [string]$Destination, [string]$Sha256)

    if (Test-Path $Destination) {
        $existing = (Get-FileHash -Algorithm SHA256 $Destination).Hash.ToLower()
        if ($existing -eq $Sha256) { Write-Skip "$([IO.Path]::GetFileName($Destination)) already verified"; return }
        Remove-Item $Destination -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Write-Host "    downloading $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
    $actual = (Get-FileHash -Algorithm SHA256 $Destination).Hash.ToLower()
    if ($actual -ne $Sha256) {
        Remove-Item $Destination -Force
        throw "checksum mismatch for $Url`n  expected $Sha256`n  actual   $actual"
    }
    Write-Host "    sha256 ok" -ForegroundColor Green
}

New-Item -ItemType Directory -Force -Path $ToolsDir, $DownloadDir | Out-Null

# --- Ghidra ----------------------------------------------------------------
Write-Step "Ghidra $GHIDRA_VERSION"
$ghidraTarget = Join-Path $ToolsDir $GHIDRA_DIR
if ((Test-Path $ghidraTarget) -and -not $Force) {
    Write-Skip "Ghidra already extracted"
} else {
    $zip = Join-Path $DownloadDir $GHIDRA_ZIP
    Get-Verified -Url $GHIDRA_URL -Destination $zip -Sha256 $GHIDRA_SHA256
    Expand-Archive -Path $zip -DestinationPath (Join-Path $ToolsDir 'ghidra') -Force
}

# --- JDK 25 ----------------------------------------------------------------
Write-Step "Temurin JDK $JDK_VERSION"
$jdkTarget = Join-Path $ToolsDir "jdk$JDK_MAJOR"
if ((Test-Path (Join-Path $jdkTarget $JDK_DIR)) -and -not $Force) {
    Write-Skip "JDK already extracted"
} else {
    $zip = Join-Path $DownloadDir $JDK_ZIP
    Get-Verified -Url $JDK_URL -Destination $zip -Sha256 $JDK_SHA256
    Expand-Archive -Path $zip -DestinationPath $jdkTarget -Force
}

# --- Node ------------------------------------------------------------------
Write-Step "Node.js $NODE_VERSION"
$nodeTarget = Join-Path $ToolsDir "node\$NODE_DIR"
if ((Test-Path (Join-Path $nodeTarget 'node.exe')) -and -not $Force) {
    Write-Skip "Node already extracted"
} else {
    $zip = Join-Path $DownloadDir $NODE_ZIP
    Get-Verified -Url $NODE_URL -Destination $zip -Sha256 $NODE_SHA256
    Expand-Archive -Path $zip -DestinationPath (Join-Path $ToolsDir 'node') -Force
}

# --- REA -------------------------------------------------------------------
Write-Step "rea-agents $REA_VERSION"
$reaRoot = Join-Path $ToolsDir 'rea'
$reaPackage = Join-Path $reaRoot "node_modules\rea-agents\package.json"
$reaCurrent = if (Test-Path $reaPackage) { (Get-Content $reaPackage -Raw | ConvertFrom-Json).version } else { $null }
if ($reaCurrent -eq $REA_VERSION -and -not $Force) {
    Write-Skip "rea-agents $REA_VERSION already installed"
} else {
    $env:PATH = "$nodeTarget;$env:PATH"
    $env:npm_config_cache = Join-Path $ToolsDir 'npm-cache'
    & (Join-Path $nodeTarget 'npm.cmd') install --prefix $reaRoot --no-fund --no-audit "rea-agents@$REA_VERSION"
    if ($LASTEXITCODE -ne 0) { throw "npm install rea-agents failed with exit code $LASTEXITCODE" }
}

# --- ps3recomp -------------------------------------------------------------
Write-Step "ps3recomp $PS3RECOMP_VERSION"
$vendorTarget = Join-Path $RepoRoot '.vendor'
$vendorPkg = Join-Path $vendorTarget "ps3recomp-v$PS3RECOMP_VERSION-win-x64"
if ((Test-Path $vendorPkg) -and -not $Force) {
    Write-Skip "ps3recomp already extracted"
} else {
    $localZip = Join-Path $RepoRoot $PS3RECOMP_ZIP
    if (-not (Test-Path $localZip)) {
        throw "place $PS3RECOMP_ZIP in the repository root (binary release, not downloaded automatically)"
    }
    New-Item -ItemType Directory -Force -Path $vendorTarget | Out-Null
    Expand-Archive -Path $localZip -DestinationPath $vendorTarget -Force
}

# --- Python ----------------------------------------------------------------
Write-Step "Python virtual environment"
$venvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $RepoRoot '.venv')
}
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -e "$RepoRoot[dev]"
if ($LASTEXITCODE -ne 0) { throw "pip install failed with exit code $LASTEXITCODE" }

Write-Host ""
Write-Step "Done. Verify with: powershell -ExecutionPolicy Bypass -File scripts/verify-tools.ps1"
