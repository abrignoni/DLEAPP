# Prepare controlled, non-account Windows corpus inputs and a native toast.
# This script does not alter firewall/security settings or app databases.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [string]$LabRoot = "C:\DLEAPP_Lab",
    [string]$KnownImagePath = (
        Join-Path $PSScriptRoot "..\..\assets\DLEAPP_logo.png"
    ),
    [switch]$LaunchApplications
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

$journalScript = Join-Path $PSScriptRoot "Write-DLEAPPAction.ps1"
$knownInputRoot = Join-Path $LabRoot "KnownInputs"
New-DLEAPPDirectory -Path $knownInputRoot

& $journalScript `
    -Artifact "Corpus Lab" `
    -Action "Wave initialized" `
    -Token "DLEAPP-WAVE1-START-001" `
    -Details "Non-account Windows artifact wave"

$knownText = Join-Path $knownInputRoot "DLEAPP-KNOWN-FILE-001.txt"
@(
    "DLEAPP controlled Windows corpus input"
    "Token: DLEAPP-KNOWN-FILE-001"
    ("Created UTC: {0}" -f [DateTime]::UtcNow.ToString("o"))
) | Set-Content -LiteralPath $knownText -Encoding UTF8
& $journalScript `
    -Artifact "Known Input" `
    -Action "Created text file" `
    -Token "DLEAPP-KNOWN-FILE-001" `
    -Details $knownText

if (Test-Path -LiteralPath $KnownImagePath) {
    $knownImage = Join-Path $env:USERPROFILE `
        "Pictures\DLEAPP-CORPUS-PHOTO-001.png"
    Copy-Item -LiteralPath $KnownImagePath -Destination $knownImage -Force
    & $journalScript `
        -Artifact "Windows Photos" `
        -Action "Copied known image into Pictures" `
        -Token "DLEAPP-PHOTOS-COPY-001" `
        -Details $knownImage
}
else {
    & $journalScript `
        -Artifact "Windows Photos" `
        -Action "Known image unavailable" `
        -Token "DLEAPP-PHOTOS-COPY-FAIL-001" `
        -Details $KnownImagePath
}

$toastToken = "DLEAPP-NOTIFICATION-TOAST-001"
$toastResult = "Not attempted"
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    $startApp = Get-StartApps |
        Where-Object { $_.Name -match "PowerShell|Terminal" } |
        Select-Object -First 1
    if ($null -eq $startApp) {
        throw "No registered PowerShell or Terminal AppUserModelID was found."
    }

    $toastXml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $toastXml.LoadXml(
        "<toast><visual><binding template=`"ToastGeneric`">" +
        "<text>DLEAPP Corpus Lab</text><text>$toastToken</text>" +
        "</binding></visual></toast>"
    )
    $toast = New-Object Windows.UI.Notifications.ToastNotification $toastXml
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::
        CreateToastNotifier($startApp.AppID)
    $notifier.Show($toast)
    $toastResult = "Shown through $($startApp.AppID)"
    & $journalScript `
        -Artifact "Windows Notifications" `
        -Action "Displayed controlled toast" `
        -Token $toastToken `
        -Details $toastResult
}
catch {
    $toastResult = $_.Exception.Message
    & $journalScript `
        -Artifact "Windows Notifications" `
        -Action "Controlled toast failed" `
        -Token "DLEAPP-NOTIFICATION-TOAST-FAIL-001" `
        -Details $toastResult
}

if ($LaunchApplications) {
    $launchTargets = @(
        [pscustomobject]@{
            Artifact = "Windows Photos"
            Expression = "Photos"
            Token = "DLEAPP-PHOTOS-LAUNCH-001"
        }
        [pscustomobject]@{
            Artifact = "Windows Sticky Notes"
            Expression = "Sticky"
            Token = "DLEAPP-STICKY-LAUNCH-001"
        }
        [pscustomobject]@{
            Artifact = "Windows Clock and Alarms"
            Expression = "Clock|Alarm"
            Token = "DLEAPP-CLOCK-LAUNCH-001"
        }
    )
    foreach ($target in $launchTargets) {
        $application = Get-StartApps |
            Where-Object Name -match $target.Expression |
            Select-Object -First 1
        if ($null -eq $application) {
            & $journalScript `
                -Artifact $target.Artifact `
                -Action "Application not registered" `
                -Token ($target.Token -replace "-001$", "-FAIL-001") `
                -Details $target.Expression
            continue
        }
        Start-Process "explorer.exe" -ArgumentList (
            "shell:AppsFolder\{0}" -f $application.AppID
        )
        & $journalScript `
            -Artifact $target.Artifact `
            -Action "Application launched" `
            -Token $target.Token `
            -Details $application.AppID
    }
}

Write-Output ("Wave one prepared. Toast result: {0}" -f $toastResult)
