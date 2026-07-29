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
| `windowsPhotos.py` | Photos; Photos Folders | 3 media rows; 6 folder rows | Replaces the obsolete `MediaDb.v1.sqlite` target with the verified modern `LocalState/shared.sqlite`. A controlled image and folder addition produced recoverable ingestion, scan, file, path, dimension, and timestamp metadata. |
| `windowsAlarms.py` | Alarms | 2 rows | Parses both the packaged-app `settings.dat` hive and legacy `Alarms.json`. A controlled alarm recovered its exact name, scheduled local time, enabled/repeat state, snooze, chime resource, record ID, and FILETIME creation/update values. The predecessor's ad-hoc structure extraction was replaced with the read-only `python-registry` parser. |

The focused profiles are `windows-system.dlprofile` and
`windows-apps.dlprofile`.

## Retest when a representative artifact is available

| WLEAPP module | Lab observation | Required next evidence |
|---|---|---|
| `betterDiscord.py` | BetterDiscord MessageLoggerV2 data was not present. | A consented test profile with that specific third-party plugin and known messages. |
| `box.py` | Box databases were not present. | Current Box Drive installation, app version, and controlled local/cloud file actions. |
| `dropbox.py` | Dropbox databases were not present. | Current Dropbox installation and controlled sync/history actions. |
| `googleDrive.py` | DriveFS metadata database was not present. | Current Google Drive for desktop installation and controlled sync actions. |
| `pfirewall.py` | `pfirewall.log` was absent. | A separately approved test that enables firewall logging, records its policy state, and produces known allowed/blocked traffic. |
| `windowsEdge.py` | `WebCacheV01.dat` existed but was live-locked. Its evidentiary scope is legacy Edge/Internet Explorer rather than current Chromium Edge. | An offline byte-for-byte copy and known legacy-WebCache activity. Do not present it as current Edge browsing history. |
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

The second-wave Photos database is also an examiner-derived SQLite backup. The
Clock hive was copied only after Clock was closed. No new SetupAPI event was
generated: the available Parallels device menu exposed the mounted corpus/data
storage and an installation ISO, but no dedicated disposable virtual device.
Disconnecting those devices solely to manufacture coverage would risk the
test data or VM state and would be detrimental to the forensic purpose.
