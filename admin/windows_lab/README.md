# DLEAPP Windows corpus laboratory

These scripts create a documented logical corpus from a controlled Windows VM.
They do not modify application databases directly. Normal application actions
must create the evidence being studied.

Authors: `@AlexisBrignoni, Codex`

## Forensic constraints

- Use only the laboratory VM clone. Keep the source VM powered off.
- Record the Windows build, architecture, time zone, app version, and every
  action that is intended to produce evidence.
- Use synthetic tokens beginning with `DLEAPP-` rather than personal data.
- Close the relevant application before collection where practical.
- Collect SQLite databases with `-wal` and `-shm` sidecars.
- Treat a missing row as an observation, not proof that an action did not occur.
- Findings from the initial VM apply to Windows 11 ARM under Parallels until
  validated on other Windows architectures and builds.

## Passive inventory

Run from Windows PowerShell:

```powershell
powershell.exe -ExecutionPolicy Bypass -File `
  "\\Mac\Home\Documents\GitHub\DLEAPP\admin\windows_lab\Get-DLEAPPLabInventory.ps1"
```

The inventory is written to `C:\DLEAPP_Lab\Inventory`. It records the operating
system and time-zone context, relevant AppX packages and Start applications,
candidate artifact paths, file timestamps, sizes, and SHA-256 hashes.

## Action journal

Record an action immediately before or after performing it:

```powershell
& "\\Mac\Home\Documents\GitHub\DLEAPP\admin\windows_lab\Write-DLEAPPAction.ps1" `
  -Artifact "Windows Sticky Notes" `
  -Action "Created note" `
  -Token "DLEAPP-STICKY-CREATE-001" `
  -Details "Synthetic note created through the normal UI"
```

The first column in `C:\DLEAPP_Lab\action-journal.tsv` is the UTC timestamp.
The local timestamp and recorded UTC offset follow it.

## First non-account wave

```powershell
powershell.exe -ExecutionPolicy Bypass -File `
  "\\Mac\Home\Documents\GitHub\DLEAPP\admin\windows_lab\Invoke-DLEAPPWaveOne.ps1" `
  -LaunchApplications
```

This creates a known text file, copies the DLEAPP logo into the Windows Pictures
folder, attempts a native controlled toast, and optionally launches Photos,
Sticky Notes, and Clock. It does not create notes or alarms by writing their
databases; those actions must be completed through the applications.

The script intentionally does not enable firewall logging. That is a
security-sensitive system setting and should be handled as a separately
documented test.

## Logical collection

Choose a destination visible to Windows, such as a Parallels shared directory:

```powershell
powershell.exe -ExecutionPolicy Bypass -File `
  "\\Mac\Home\Documents\GitHub\DLEAPP\admin\windows_lab\Export-DLEAPPLabCorpus.ps1" `
  -DestinationRoot "\\Mac\Home\Documents\GitHub\DLEAPP\.lab-output" `
  -Stage "baseline"
```

The collector preserves Windows paths beneath `files\C`, includes discovered
SQLite sidecars, hashes source and destination copies, and writes a manifest
with any collection errors. Corpus output is excluded from Git.

## Live SQLite snapshot for parser testing

Some Windows databases remain open while the user is signed in. A failed raw
copy is valuable acquisition information and must remain in the collection
manifest. For a separate parser-testing input, Python's SQLite backup API can
create a transactionally consistent database containing committed WAL data:

```powershell
py "\\Mac\Home\Documents\GitHub\DLEAPP\admin\windows_lab\Snapshot-DLEAPPLiveSqlite.py" `
  --destination-root "\\Mac\Home\Documents\GitHub\DLEAPP\.lab-output" `
  --stage "live-sqlite-snapshots"
```

The snapshot manifest places its creation timestamp first and records source
file timestamps, sizes, snapshot SHA-256, SQLite quick-check result, page count,
user version, and the acquisition method. These outputs are examiner-derived
logical snapshots. They are useful for reproducible parser tests, but they are
not substitutes for byte-for-byte acquired source files and sidecars.
