# Record a passive Windows/app/artifact inventory for the DLEAPP corpus lab.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [string]$OutputRoot = "C:\DLEAPP_Lab\Inventory"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

New-DLEAPPDirectory -Path $OutputRoot

$currentVersion = Get-ItemProperty `
    -LiteralPath "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
$operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem
$computerSystem = Get-CimInstance -ClassName Win32_ComputerSystem
$timeZone = Get-TimeZone
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()

$systemInventory = [ordered]@{
    CollectedUtc = [DateTime]::UtcNow.ToString("o")
    ProductName = $currentVersion.ProductName
    DisplayVersion = $currentVersion.DisplayVersion
    CurrentBuild = $currentVersion.CurrentBuild
    UBR = $currentVersion.UBR
    BuildLabEx = $currentVersion.BuildLabEx
    OSArchitecture = $operatingSystem.OSArchitecture
    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    ProcessorArchitecture = $env:PROCESSOR_ARCHITECTURE
    ComputerModel = $computerSystem.Model
    Manufacturer = $computerSystem.Manufacturer
    TimeZoneId = $timeZone.Id
    UtcOffset = $timeZone.GetUtcOffset([DateTime]::Now).ToString()
    UserSid = $identity.User.Value
    UserProfileName = Split-Path -Leaf $env:USERPROFILE
}
$systemInventory |
    ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $OutputRoot "system-inventory.json") `
        -Encoding UTF8

$targetPackageExpression = (
    "StickyNotes|WindowsAlarms|Windows\.Photos|YourPhone|CrossDevice|" +
    "Cortana|Dropbox|Box|GoogleDrive|Messenger"
)
$packages = @(
    Get-AppxPackage |
        Where-Object {
            $_.Name -match $targetPackageExpression -or
            $_.PackageFamilyName -match $targetPackageExpression
        } |
        Sort-Object Name |
        Select-Object Name, PackageFullName, PackageFamilyName, Version,
            Architecture, InstallLocation, Status, PublisherId
)
$packages |
    ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $OutputRoot "target-appx-packages.json") `
        -Encoding UTF8

$startApplications = @(
    Get-StartApps |
        Where-Object {
            $_.Name -match (
                "Sticky|Clock|Alarm|Photos|Phone Link|Your Phone|" +
                "Dropbox|Box|Google Drive|Messenger|PowerShell|Terminal"
            )
        } |
        Sort-Object Name
)
$startApplications |
    ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $OutputRoot "target-start-apps.json") `
        -Encoding UTF8

$artifactRows = @()
foreach ($match in Get-DLEAPPTargetFiles) {
    $file = $match.File
    $hash = ""
    $hashError = ""
    try {
        $hash = (
            Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256 `
                -ErrorAction Stop 2>$null
        ).Hash
    }
    catch {
        $hashError = $_.Exception.Message
    }
    $artifactRows += [pscustomobject]@{
        Artifact = $match.Artifact
        Path = $file.FullName
        Length = $file.Length
        CreatedUtc = $file.CreationTimeUtc.ToString("o")
        ModifiedUtc = $file.LastWriteTimeUtc.ToString("o")
        SHA256 = $hash
        HashError = $hashError
        MatchedPattern = $match.Pattern
    }
}
$artifactRows |
    Sort-Object Artifact, Path |
    Export-Csv -LiteralPath (Join-Path $OutputRoot "artifact-paths.tsv") `
        -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$definitions = @(
    foreach ($definition in Get-DLEAPPArtifactDefinitions) {
        [pscustomobject]@{
            Artifact = $definition.Artifact
            Patterns = $definition.Patterns
            Matches = @(
                $artifactRows |
                    Where-Object Artifact -eq $definition.Artifact |
                    Select-Object -ExpandProperty Path
            )
        }
    }
)
$definitions |
    ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $OutputRoot "artifact-coverage.json") `
        -Encoding UTF8

$journalPath = "C:\DLEAPP_Lab\action-journal.tsv"
if (-not (Test-Path -LiteralPath $journalPath)) {
    New-DLEAPPDirectory -Path (Split-Path -Parent $journalPath)
    "TimestampUtc`tTimestampLocal`tUtcOffset`tArtifact`tAction`tToken`tDetails" |
        Set-Content -LiteralPath $journalPath -Encoding UTF8
}

Write-Output ("Inventory written to {0}" -f $OutputRoot)
Write-Output ("Target files found: {0}" -f $artifactRows.Count)
