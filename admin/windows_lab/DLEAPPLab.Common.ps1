# DLEAPP Windows corpus laboratory helpers.
# Authors: @AlexisBrignoni, Codex

Set-StrictMode -Version 2.0

function Get-DLEAPPArtifactDefinitions {
    $local = $env:LOCALAPPDATA
    $roaming = $env:APPDATA
    $windows = $env:SystemRoot

    @(
        [pscustomobject]@{
            Artifact = "ActivitiesCache"
            Patterns = @("$local\ConnectedDevicesPlatform\*\ActivitiesCache.db*")
        }
        [pscustomobject]@{
            Artifact = "BetterDiscord Message Logger"
            Patterns = @(
                "$roaming\BetterDiscord\plugins\MessageLoggerV2Data.config.json"
            )
        }
        [pscustomobject]@{
            Artifact = "Box Drive"
            Patterns = @("$local\Box\Box\Data\*.db*")
        }
        [pscustomobject]@{
            Artifact = "Dropbox"
            Patterns = @(
                "$local\Packages\*DROPBOX*\LocalState\users\*\*.sqlite*",
                "$local\Dropbox\instance*\sync_history.db*"
            )
        }
        [pscustomobject]@{
            Artifact = "Facebook Messenger (Legacy)"
            Patterns = @("$local\Packages\FACEBOOK.*\AC\Messenger\msys_*.db*")
        }
        [pscustomobject]@{
            Artifact = "Google Drive"
            Patterns = @("$local\Google\DriveFS\*\metadata_sqlite_db*")
        }
        [pscustomobject]@{
            Artifact = "Windows Firewall"
            Patterns = @("$windows\System32\LogFiles\Firewall\pfirewall.log")
        }
        [pscustomobject]@{
            Artifact = "SetupAPI Device Installation"
            Patterns = @("$windows\INF\setupapi.dev.log")
        }
        [pscustomobject]@{
            Artifact = "Windows Clock and Alarms"
            Patterns = @(
                "$local\Packages\Microsoft.WindowsAlarms_*\LocalState\Alarms\Alarms.json",
                "$local\Packages\Microsoft.WindowsAlarms_*\Settings\settings.dat"
            )
        }
        [pscustomobject]@{
            Artifact = "Cortana DeviceSearchCache (Legacy)"
            Patterns = @(
                "$local\Packages\Microsoft.Windows.Cortana_*\LocalState\DeviceSearchCache\AppCache*.txt"
            )
        }
        [pscustomobject]@{
            Artifact = "Microsoft Edge Legacy"
            Patterns = @("$local\Microsoft\Windows\WebCache\WebCacheV01.dat*")
        }
        [pscustomobject]@{
            Artifact = "Windows Notifications"
            Patterns = @(
                "$local\Microsoft\Windows\Notifications\wpndatabase.db*"
            )
        }
        [pscustomobject]@{
            Artifact = "Windows Photos"
            Patterns = @(
                "$local\Packages\Microsoft.Windows.Photos_*\LocalState\MediaDb*.sqlite*"
            )
        }
        [pscustomobject]@{
            Artifact = "Windows Sticky Notes"
            Patterns = @(
                "$local\Packages\Microsoft.MicrosoftStickyNotes_*\LocalState\plum.sqlite*"
            )
        }
        [pscustomobject]@{
            Artifact = "Phone Link"
            Patterns = @(
                "$local\Packages\Microsoft.YourPhone_*\LocalCache\Indexed\*\System\Database\*",
                "$local\Packages\MicrosoftWindows.CrossDevice_*\LocalState\*"
            )
        }
    )
}

function Get-DLEAPPTargetFiles {
    $seen = @{}
    foreach ($definition in Get-DLEAPPArtifactDefinitions) {
        foreach ($pattern in $definition.Patterns) {
            $matches = @(Get-ChildItem -Path $pattern -Force -File -ErrorAction SilentlyContinue)
            foreach ($file in $matches) {
                $key = $file.FullName.ToLowerInvariant()
                if ($seen.ContainsKey($key)) {
                    continue
                }
                $seen[$key] = $true
                [pscustomobject]@{
                    Artifact = $definition.Artifact
                    Pattern = $pattern
                    File = $file
                }
            }
        }
    }
}

function New-DLEAPPDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function ConvertTo-DLEAPPTsvValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value) {
        return ""
    }
    ([string]$Value).Replace("`t", " ").Replace("`r", " ").Replace("`n", " ")
}

function Get-DLEAPPRelativeCollectionPath {
    param([Parameter(Mandatory = $true)][System.IO.FileInfo]$File)

    $driveName = $File.PSDrive.Name
    $driveRoot = $File.PSDrive.Root
    $relative = $File.FullName.Substring($driveRoot.Length).TrimStart("\")
    Join-Path $driveName $relative
}
