# WLEAPP to DLEAPP modernization audit

Authors: `@AlexisBrignoni, Codex`

This audit compares the 15 artifact modules in the local WLEAPP repository at
commit `7690aa4` with observations from the controlled Windows VM corpus. It is
an implementation and test-status record, not a claim that an artifact is
absent from Windows generally.

The lab observation applies to a Parallels ARM virtual machine running Windows
build `26200.8457`, display version `25H2`. The Windows registry value collected
as `ProductName` says `Windows 10 Pro`; the build, display version, architecture,
and captured UI are therefore reported separately rather than treating that
single registry label as the operating-system name.

## Migrated and corpus-validated

| WLEAPP module | DLEAPP artifact | Corpus result | Modernization value |
|---|---|---:|---|
| `activitiesCache.py` | ActivitiesCache | 5 rows | Preserves non-JSON payloads that the predecessor discarded, exposes application identifiers, and reports Unix timestamps in UTC with the primary start time first. |
| `windowsNotification.py` | Notifications | 3 rows | Adds handler identity, payload type, extracted text, payload size and SHA-256, retains the raw payload, and reports FILETIME values in UTC. The controlled toast token was recovered. |
| `windowsStickyNotes.py` | Sticky Notes | 2 rows | Retains empty notes with metadata, removes the internal text marker, adds note identifiers and window state, and reports updated/created/deleted .NET-tick times first in UTC. The controlled note token was recovered. |
| `setupapiDev.py` | SetupAPI Sections | 1 row | Parses complete SetupAPI sections rather than assuming every timestamp is a device's first connection. Times are labeled device-local because the log does not record a UTC offset. |

The focused profile is `windows-system.dlprofile`.

## Retest when a representative artifact is available

| WLEAPP module | Lab observation | Required next evidence |
|---|---|---|
| `betterDiscord.py` | BetterDiscord MessageLoggerV2 data was not present. | A consented test profile with that specific third-party plugin and known messages. |
| `box.py` | Box databases were not present. | Current Box Drive installation, app version, and controlled local/cloud file actions. |
| `dropbox.py` | Dropbox databases were not present. | Current Dropbox installation and controlled sync/history actions. |
| `googleDrive.py` | DriveFS metadata database was not present. | Current Google Drive for desktop installation and controlled sync actions. |
| `pfirewall.py` | `pfirewall.log` was absent. | A separately approved test that enables firewall logging, records its policy state, and produces known allowed/blocked traffic. |
| `windowsAlarms.py` | Clock `11.2605.10.0` requested an update. `settings.dat` existed, but no controlled alarm could be created. The WLEAPP parser contains a structure TODO and requires `pyregf`, which DLEAPP does not currently require. | A usable Clock build, known alarms, the JSON/registry-store variants, and dependency review. |
| `windowsEdge.py` | `WebCacheV01.dat` existed but was live-locked. Its evidentiary scope is legacy Edge/Internet Explorer rather than current Chromium Edge. | An offline byte-for-byte copy and known legacy-WebCache activity. Do not present it as current Edge browsing history. |
| `windowsPhotos.py` | Photos `2026.11020.20001.0` was present, but the WLEAPP target `MediaDb.v1.sqlite` was not found after a known image was placed in Pictures and Photos was opened. | Storage discovery and schema research for this Photos version before porting the old query. |
| `windowsYourPhone.py` | Current Phone Link and CrossDevice packages were installed, but the targeted databases were not present in the unpaired profile. | A dedicated synthetic phone/account pairing. Personal accounts or devices should not be used merely to obtain parser coverage. |

## Legacy candidates

| WLEAPP module | Reason to avoid a blind port |
|---|---|
| `facebookMessenger.py` | The parser targets the retired Facebook Messenger UWP storage layout, and no matching package or database was present. Preserve it only with a representative legacy corpus. |
| `windowsCortana.py` | The parser targets legacy Cortana `DeviceSearchCache` text files, and no matching package or files were present. Preserve it only with a representative legacy corpus. |

## Acquisition note

ActivitiesCache and Notifications could not be copied byte-for-byte while the
Windows user session was active. Their raw-copy failures and error messages are
retained in the collection manifest. For parser testing only, the SQLite backup
API produced read-only-source logical snapshots containing committed WAL data;
each snapshot passed `PRAGMA quick_check` and was hashed. Those snapshots are
examiner-derived and must not be described as original acquired files.
