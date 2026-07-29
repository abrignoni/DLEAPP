# Inventory modern Windows app storage without modifying app data.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9_-]+$")]
    [string]$Phase,

    [string]$OutputRoot = "C:\DLEAPP_Lab\AppStorageInventory",

    [long]$MaximumHashBytes = 67108864
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

$collectedUtc = [DateTime]::UtcNow
$phaseRoot = Join-Path $OutputRoot $Phase
New-DLEAPPDirectory -Path $phaseRoot

$targets = @(
    [pscustomobject]@{
        Artifact = "Windows Photos"
        PackagePattern = "Microsoft.Windows.Photos_*"
    }
    [pscustomobject]@{
        Artifact = "Windows Clock"
        PackagePattern = "Microsoft.WindowsAlarms_*"
    }
)

$packagesRoot = Join-Path $env:LOCALAPPDATA "Packages"
$packageRows = @()
$fileRows = @()

foreach ($target in $targets) {
    $packageDirectories = @(
        Get-ChildItem -LiteralPath $packagesRoot -Directory -Force `
            -ErrorAction SilentlyContinue |
            Where-Object Name -Like $target.PackagePattern
    )

    foreach ($packageDirectory in $packageDirectories) {
        $package = Get-AppxPackage |
            Where-Object PackageFamilyName -eq $packageDirectory.Name |
            Select-Object -First 1

        $packageRows += [pscustomobject][ordered]@{
            CollectedUtc = $collectedUtc.ToString("o")
            Artifact = $target.Artifact
            PackageFamilyName = $packageDirectory.Name
            PackageName = if ($null -ne $package) { $package.Name } else { "" }
            PackageVersion = if ($null -ne $package) {
                $package.Version.ToString()
            }
            else {
                ""
            }
            PackagePath = $packageDirectory.FullName
        }

        $files = @(
            Get-ChildItem -LiteralPath $packageDirectory.FullName -File `
                -Recurse -Force -ErrorAction SilentlyContinue
        )
        foreach ($file in $files) {
            $relativePath = $file.FullName.Substring(
                $packageDirectory.FullName.Length
            ).TrimStart("\")
            $hash = ""
            $hashStatus = "Not attempted"
            if ($file.Length -le $MaximumHashBytes) {
                try {
                    $hash = (
                        Get-FileHash -LiteralPath $file.FullName `
                            -Algorithm SHA256 -ErrorAction Stop 2>$null
                    ).Hash
                    $hashStatus = "Hashed"
                }
                catch {
                    $hashStatus = $_.Exception.Message
                }
            }
            else {
                $hashStatus = "Skipped: file exceeds MaximumHashBytes"
            }

            $fileRows += [pscustomobject][ordered]@{
                ModifiedUtc = $file.LastWriteTimeUtc.ToString("o")
                CreatedUtc = $file.CreationTimeUtc.ToString("o")
                CollectedUtc = $collectedUtc.ToString("o")
                Artifact = $target.Artifact
                PackageFamilyName = $packageDirectory.Name
                RelativePath = $relativePath
                Extension = $file.Extension
                Length = $file.Length
                SHA256 = $hash
                HashStatus = $hashStatus
            }
        }
    }
}

$packageRows |
    Sort-Object Artifact, PackageFamilyName |
    Export-Csv -LiteralPath (Join-Path $phaseRoot "packages.tsv") `
        -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$fileRows |
    Sort-Object Artifact, PackageFamilyName, RelativePath |
    Export-Csv -LiteralPath (Join-Path $phaseRoot "files.tsv") `
        -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    CollectedUtc = $collectedUtc.ToString("o")
    Phase = $Phase
    PackageCount = $packageRows.Count
    FileCount = $fileRows.Count
    OutputRoot = $phaseRoot
    MaximumHashBytes = $MaximumHashBytes
}
$summary |
    ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $phaseRoot "summary.json") `
        -Encoding UTF8

Write-Output (
    "App storage inventory '{0}' written to {1}; packages={2}; files={3}" -f
        $Phase, $phaseRoot, $packageRows.Count, $fileRows.Count
)
