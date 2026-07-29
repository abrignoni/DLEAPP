# Create and open a controlled local image for Windows Photos validation.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [string]$KnownImagePath = "",
    [string]$Token = "DLEAPP-PHOTOS-WAVE2-001"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

$journalScript = Join-Path $PSScriptRoot "Write-DLEAPPAction.ps1"
if ([string]::IsNullOrWhiteSpace($KnownImagePath)) {
    $KnownImagePath = Join-Path $PSScriptRoot "..\..\assets\DLEAPP_logo.png"
}
if (-not (Test-Path -LiteralPath $KnownImagePath)) {
    throw "Known image does not exist: $KnownImagePath"
}

$destination = Join-Path $env:USERPROFILE ("Pictures\{0}.png" -f $Token)
Copy-Item -LiteralPath $KnownImagePath -Destination $destination -Force
$hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash

& $journalScript `
    -Artifact "Windows Photos" `
    -Action "Copied controlled image into Pictures" `
    -Token $Token `
    -Details ("Path={0}; SHA256={1}" -f $destination, $hash)

$photos = Get-StartApps |
    Where-Object Name -Match "^Photos$|Microsoft Photos" |
    Select-Object -First 1
if ($null -eq $photos) {
    throw "Microsoft Photos is not registered in the Start menu."
}

Start-Process "explorer.exe" -ArgumentList (
    "shell:AppsFolder\{0}" -f $photos.AppID
)
& $journalScript `
    -Artifact "Windows Photos" `
    -Action "Launched Photos after controlled image copy" `
    -Token ($Token -replace "-001$", "-LAUNCH-001") `
    -Details $photos.AppID

Write-Output ("Controlled Photos input: {0}; SHA256={1}" -f $destination, $hash)
