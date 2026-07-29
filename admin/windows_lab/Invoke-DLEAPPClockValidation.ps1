# Launch Windows Clock and journal the controlled validation session.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [string]$Token = "DLEAPP-ALARM-WAVE2-001"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

$journalScript = Join-Path $PSScriptRoot "Write-DLEAPPAction.ps1"
$clock = Get-StartApps |
    Where-Object Name -Match "^Clock$|Alarm" |
    Select-Object -First 1
if ($null -eq $clock) {
    throw "Windows Clock is not registered in the Start menu."
}

& $journalScript `
    -Artifact "Windows Clock" `
    -Action "Started controlled alarm validation" `
    -Token $Token `
    -Details ("AppUserModelId={0}; create through app UI" -f $clock.AppID)

Start-Process "explorer.exe" -ArgumentList (
    "shell:AppsFolder\{0}" -f $clock.AppID
)

Write-Output (
    "Clock launched. Create alarm token through the app UI: {0}" -f $Token
)
