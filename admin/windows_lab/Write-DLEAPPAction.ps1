# Append a controlled action to the DLEAPP Windows corpus journal.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Artifact,
    [Parameter(Mandatory = $true)][string]$Action,
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$Details = "",
    [string]$JournalPath = "C:\DLEAPP_Lab\action-journal.tsv"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

if ($Token -notmatch "^DLEAPP-[A-Z0-9-]+$") {
    throw "Token must start with DLEAPP- and contain only A-Z, 0-9, and hyphens."
}

New-DLEAPPDirectory -Path (Split-Path -Parent $JournalPath)
if (-not (Test-Path -LiteralPath $JournalPath)) {
    "TimestampUtc`tTimestampLocal`tUtcOffset`tArtifact`tAction`tToken`tDetails" |
        Set-Content -LiteralPath $JournalPath -Encoding UTF8
}

$now = Get-Date
$row = @(
    $now.ToUniversalTime().ToString("o"),
    $now.ToString("o"),
    [TimeZoneInfo]::Local.GetUtcOffset($now).ToString(),
    (ConvertTo-DLEAPPTsvValue $Artifact),
    (ConvertTo-DLEAPPTsvValue $Action),
    (ConvertTo-DLEAPPTsvValue $Token),
    (ConvertTo-DLEAPPTsvValue $Details)
) -join "`t"
Add-Content -LiteralPath $JournalPath -Value $row -Encoding UTF8

Write-Output $row
