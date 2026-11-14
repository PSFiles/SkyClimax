<#
.SYNOPSIS
    Verify every pinned SkyClimax tool and print the result table.

.DESCRIPTION
    Runs each tool's version command and compares the output with the value
    recorded in scripts/tools.lock.json. Exits non-zero when any tool is missing
    or reports a different version, so CI can gate on it.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/verify-tools.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$lock = Get-Content (Join-Path $PSScriptRoot 'tools.lock.json') -Raw | ConvertFrom-Json
$results = @()

function Add-Result([string]$Tool, [string]$Expected, [string]$Actual, [bool]$Ok) {
    $script:results += [pscustomobject]@{
        Tool     = $Tool
        Expected = $Expected
        Actual   = $Actual
        Status   = if ($Ok) { 'OK' } else { 'FAIL' }
    }
}

function Invoke-Probe {
    param([string]$Tool, [string]$Exe, [string[]]$Arguments, [string]$Expect)
    if (-not (Test-Path $Exe)) {
        Add-Result $Tool $Expect "not found: $Exe" $false
        return
    }
    # Native tools such as `java -version` write to stderr. With
    # $ErrorActionPreference = 'Stop' that becomes a terminating error, so the
    # preference is relaxed for the duration of the call only.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & $Exe @Arguments 2>&1 | Out-String
    } catch {
        Add-Result $Tool $Expect "failed to run: $($_.Exception.Message)" $false
        return
    } finally {
        $ErrorActionPreference = $previous
    }
    $first = ($output -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()
    # stderr records arrive prefixed with the executable name; strip it.
    $first = $first -replace '^[^:\\/]+\.exe\s*:\s*', ''
    Add-Result $Tool $Expect $first ($first -like "*$Expect*")
}

$jdk = Join-Path $RepoRoot ".tools\jdk25\jdk-25.0.5+8"
$node = Join-Path $RepoRoot ".tools\node\node-v24.22.3-win-x64\node.exe"
$rea = Join-Path $RepoRoot ".tools\rea\node_modules\rea-agents\scripts\rea.mjs"
$venv = Join-Path $RepoRoot '.venv\Scripts\python.exe'

Invoke-Probe 'java' (Join-Path $jdk 'bin\java.exe') @('-version') 'openjdk version "25.0.5"'
Invoke-Probe 'node' $node @('--version') 'v24.22.3'
Invoke-Probe 'rea' $node @($rea, '--version') '6.9.0'
Invoke-Probe 'python' $venv @('-V') 'Python 3.13'

$ghidraProps = Join-Path $RepoRoot '.tools\ghidra\ghidra_12.2_PUBLIC\Ghidra\application.properties'
if (Test-Path $ghidraProps) {
    $ver = (Select-String -Path $ghidraProps -Pattern '^application.version=').Line -replace '.*=', ''
    Add-Result 'ghidra' '12.2' $ver ($ver -eq '12.2')
} else {
    Add-Result 'ghidra' '12.2' 'not extracted' $false
}

$vendorVersion = Join-Path $RepoRoot '.vendor\ps3recomp-v0.19.0-win-x64\VERSION.txt'
if (Test-Path $vendorVersion) {
    $line = (Get-Content $vendorVersion | Select-Object -First 1).Trim()
    Add-Result 'ps3recomp' 'ps3recomp v0.19.0' $line ($line -eq 'ps3recomp v0.19.0')
} else {
    Add-Result 'ps3recomp' 'ps3recomp v0.19.0' 'not extracted' $false
}

"{0,-11} {1,-30} {2,-42} {3}" -f 'TOOL', 'EXPECTED', 'ACTUAL', 'STATUS'
"{0,-11} {1,-30} {2,-42} {3}" -f ('-' * 11), ('-' * 30), ('-' * 42), ('-' * 6)
foreach ($r in $results) {
    "{0,-11} {1,-30} {2,-42} {3}" -f $r.Tool, $r.Expected, $r.Actual, $r.Status
}

$failed = @($results | Where-Object { $_.Status -eq 'FAIL' })
if ($failed.Count -gt 0) {
    Write-Host "$($failed.Count) tool(s) failed verification." -ForegroundColor Red
    exit 1
}
Write-Host "All $($results.Count) tools verified." -ForegroundColor Green
exit 0
