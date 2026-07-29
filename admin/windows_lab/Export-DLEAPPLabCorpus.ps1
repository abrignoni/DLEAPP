# Copy discovered artifacts into a path-preserving, hashed corpus stage.
# Authors: @AlexisBrignoni, Codex

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$DestinationRoot,
    [ValidatePattern("^[A-Za-z0-9._-]+$")][string]$Stage = "baseline",
    [string]$LabRoot = "C:\DLEAPP_Lab"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
. "$PSScriptRoot\DLEAPPLab.Common.ps1"

$stageRoot = Join-Path $DestinationRoot $Stage
$fileRoot = Join-Path $stageRoot "files"
New-DLEAPPDirectory -Path $fileRoot

$manifestRows = @()
foreach ($match in Get-DLEAPPTargetFiles) {
    $file = $match.File
    $relativePath = Get-DLEAPPRelativeCollectionPath -File $file
    $destination = Join-Path $fileRoot $relativePath
    New-DLEAPPDirectory -Path (Split-Path -Parent $destination)

    $copied = $false
    $errorText = ""
    $sourceHash = ""
    $destinationHash = ""
    try {
        $sourceHash = (
            Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256 `
                -ErrorAction Stop 2>$null
        ).Hash
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
        $destinationHash = (
            Get-FileHash -LiteralPath $destination -Algorithm SHA256 `
                -ErrorAction Stop 2>$null
        ).Hash
        if ($sourceHash -ne $destinationHash) {
            throw "Source and destination hashes differ."
        }
        $copied = $true
    }
    catch {
        $errorText = $_.Exception.Message
    }

    $manifestRows += [pscustomobject]@{
        Artifact = $match.Artifact
        SourcePath = $file.FullName
        CollectedPath = $destination
        Length = $file.Length
        CreatedUtc = $file.CreationTimeUtc.ToString("o")
        ModifiedUtc = $file.LastWriteTimeUtc.ToString("o")
        SHA256 = $sourceHash
        Copied = $copied
        CollectionError = $errorText
    }
}

$manifestRows |
    Sort-Object Artifact, SourcePath |
    Export-Csv -LiteralPath (Join-Path $stageRoot "collection-manifest.tsv") `
        -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$metadata = [ordered]@{
    CollectedUtc = [DateTime]::UtcNow.ToString("o")
    Stage = $Stage
    HostLabel = "windows11_arm_parallels"
    FileCount = @($manifestRows | Where-Object Copied).Count
    FailedCount = @($manifestRows | Where-Object { -not $_.Copied }).Count
    SourceCollection = "Logical copy from controlled Windows VM"
}
$metadata |
    ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $stageRoot "collection-metadata.json") `
        -Encoding UTF8

foreach ($supportName in @("Inventory", "action-journal.tsv")) {
    $supportPath = Join-Path $LabRoot $supportName
    if (Test-Path -LiteralPath $supportPath) {
        Copy-Item -LiteralPath $supportPath -Destination $stageRoot `
            -Recurse -Force
    }
}

Write-Output ("Corpus stage written to {0}" -f $stageRoot)
Write-Output (
    "Copied: {0}; failed: {1}" -f
    $metadata.FileCount, $metadata.FailedCount
)
