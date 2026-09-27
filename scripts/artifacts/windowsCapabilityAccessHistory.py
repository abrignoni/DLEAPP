"""Windows CapabilityAccessManager.db parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads ProgramData\\Microsoft\\Windows\\CapabilityAccessManager\\CapabilityAccessManager.db,
the SQLite database where Windows 11 keeps earlier capability access events
(camera, microphone, location and others) after the registry ConsentStore has
moved on to a newer one. The usage history tables name their capability, app
and user through lookup tables, joined here. Sources are in the notes.
"""

__artifacts_v2__ = {
    "capabilityAccessHistory": {
        "name": "Capability Access History",
        "description": "Capability access events (camera, microphone, location and others) kept "
                       "in the Windows 11 CapabilityAccessManager.db database: start and stop "
                       "time, capability, app, user SID and, for non-packaged apps, the file "
                       "and program IDs.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from "
                 "ProgramData\\Microsoft\\Windows\\CapabilityAccessManager\\CapabilityAccessManager.db "
                 "together with its write-ahead log; Source File names the database each row came from, "
                 "since the declared path can match more than one copy. 51 of the 131 rows on "
                 "pc_mus_001_win11 were in the write-ahead log, and the database file alone held 80. Cyber "
                 "Sundae DFIR found the database on Windows 11 22H2 and 23H2 and not on the Windows 10 "
                 "machines tested, describes its times as Windows FILETIME values, and reports that the "
                 "registry ConsentStore keeps each app's newest access event while the earlier one moves "
                 "into the database when a newer equivalent event arrives, rows being kept for about 30 "
                 "days (Reference: Cyber Sundae DFIR, 'Capability Access Manager Forensics in Windows 11', "
                 "https://medium.com/@cyber.sundae.dfir/capability-access-manager-forensics-in-windows-11-f586ef8aac79). "
                 "Each row is one row of PackagedUsageHistory (App Type Packaged, App the package family "
                 "name) or NonPackagedUsageHistory (App Type NonPackaged, App the executable path), with "
                 "Capability, App, User SID, File ID and Program ID read from the Capabilities, "
                 "PackageFamilyNames, BinaryFullPaths, Users, FileIDs and ProgramIDs tables the row's "
                 "numbers point to (Reference: Cyber Sundae DFIR, 'CapabilityAccessManager.db Deep Dive, "
                 "Part 1', "
                 "https://medium.com/@cyber.sundae.dfir/capabilityaccessmanager-db-deep-dive-part-1-ff49f69c58af). "
                 "Start Time (UTC) and Stop Time (UTC) are LastUsedTimeStart and LastUsedTimeStop read as "
                 "FILETIME values, which the Part 1 post describes as the moments the app started and "
                 "stopped using the capability rather than when the app was opened. On pc_mus_001_win11 "
                 "Start Time ran from 2022-12-08 03:00 to 2023-01-06 17:03 UTC, about 30 days, and Stop "
                 "Time equalled Start Time on all 59 contacts rows. Access Blocked (as stored) is "
                 "AccessBlocked as stored, which the Part 1 post reads as whether the access was blocked, "
                 "adding that a blocked row has a zero start time and that its author could not produce "
                 "one. Access Blocked was 0 on every row of pc_mus_001_win11, and User SID held one value "
                 "on every row there. File ID and Program ID are filled on NonPackaged rows. Cyber Sundae "
                 "DFIR found that the FileID comes from AmCache when an event moves from the registry into "
                 "the database, so a row can carry the FileID the executable had at the next equivalent "
                 "event rather than at its own (Reference: Cyber Sundae DFIR, 'CapabilityAccessManager.db "
                 "Deep Dive, Part 3', "
                 "https://medium.com/@cyber.sundae.dfir/capabilityaccessmanager-db-deep-dive-part-3-801092e1ead9). "
                 "On pc_mus_001_win11 the msedge.exe rows' File ID and Program ID equal the FileId and "
                 "ProgramId of that path's InventoryApplicationFile entry in its Amcache.hve. Record ID is "
                 "the row's ID in its own table, which the Part 1 post found increments and is not reused "
                 "after old rows are removed; on pc_mus_001_win11 the PackagedUsageHistory ids ran from 51 "
                 "to 180 with 77 absent, and the NonPackagedUsageHistory ids were 2 and 3. Read the "
                 "Capability Access Manager artifact, which reports the registry ConsentStore, beside this "
                 "one. On pc_mus_001_win11 the user's hive held last-use times for five app and capability "
                 "pairs: three are not in the database, one equals the latest database row for its pair "
                 "and one an earlier row. That hive is dirty, its primary and secondary sequence numbers "
                 "differing (Reference: Maxim Suhanov, 'Windows registry file format specification', "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L728), "
                 "and DLEAPP reads hives without replaying their transaction logs, so the registry values "
                 "reported there can predate writes held in those logs.",
        "paths": ('*/ProgramData/Microsoft/Windows/CapabilityAccessManager/CapabilityAccessManager.db*',),
        "output_types": "standard",
        "artifact_icon": "video",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 131 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "capabilityAccessIdentities": {
        "name": "Capability Access Program Identities",
        "description": "Non-packaged executables listed in the NonPackagedIdentityRelationship "
                       "table of the Windows 11 CapabilityAccessManager.db database, with the "
                       "stored observed time and the file and program IDs.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the NonPackagedIdentityRelationship table of "
                 "ProgramData\\Microsoft\\Windows\\CapabilityAccessManager\\CapabilityAccessManager.db, with "
                 "its write-ahead log; Source File names the database each row came from, since the "
                 "declared path can match more than one copy. Each row is one non-packaged executable path "
                 "and FileID, with Binary Path, File ID and Program ID read from the BinaryFullPaths, "
                 "FileIDs and ProgramIDs tables the row's numbers point to (Reference: Cyber Sundae DFIR, "
                 "'CapabilityAccessManager.db Deep Dive, Part 1', "
                 "https://medium.com/@cyber.sundae.dfir/capabilityaccessmanager-db-deep-dive-part-1-ff49f69c58af). "
                 "Last Observed Time (UTC) is LastObservedTime read as a FILETIME value, the format the "
                 "same author gives for the usage times (Reference: Cyber Sundae DFIR, 'Capability Access "
                 "Manager Forensics in Windows 11', "
                 "https://medium.com/@cyber.sundae.dfir/capability-access-manager-forensics-in-windows-11-f586ef8aac79); "
                 "that reading is not otherwise established for this column. Despite its name, the Part 1 "
                 "post found it holds the earliest time the app was observed within the period the "
                 "database keeps, not the latest. On pc_mus_001_win11 the one row, for msedge.exe, held "
                 "2022-12-04 00:40 UTC, earlier than both of that path's rows in Capability Access History "
                 "(2023-01-05). File ID comes from AmCache, as the Capability Access History notes "
                 "describe, and on pc_mus_001_win11 File ID and Program ID equal the FileId and ProgramId "
                 "of msedge.exe's InventoryApplicationFile entry in its Amcache.hve. Record ID is the "
                 "row's ID in the table.",
        "paths": ('*/ProgramData/Microsoft/Windows/CapabilityAccessManager/CapabilityAccessManager.db*',),
        "output_types": "standard",
        "artifact_icon": "hash",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import sqlite3

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.windows_registry import filetime_utc

_DATABASE = 'CapabilityAccessManager.db'

_PACKAGED = '''
    SELECT h.LastUsedTimeStart, h.LastUsedTimeStop, c.StringValue, p.StringValue,
           u.StringValue, h.AccessBlocked, NULL, NULL, h.ID
    FROM PackagedUsageHistory h
    LEFT JOIN Capabilities c ON c.ID = h.Capability
    LEFT JOIN PackageFamilyNames p ON p.ID = h.PackageFamilyName
    LEFT JOIN Users u ON u.ID = h.UserSid'''

_NON_PACKAGED = '''
    SELECT h.LastUsedTimeStart, h.LastUsedTimeStop, c.StringValue, b.StringValue,
           u.StringValue, h.AccessBlocked, f.StringValue, g.StringValue, h.ID
    FROM NonPackagedUsageHistory h
    LEFT JOIN Capabilities c ON c.ID = h.Capability
    LEFT JOIN BinaryFullPaths b ON b.ID = h.BinaryFullPath
    LEFT JOIN Users u ON u.ID = h.UserSid
    LEFT JOIN FileIDs f ON f.ID = h.FileID
    LEFT JOIN ProgramIDs g ON g.ID = h.ProgramID'''

_IDENTITIES = '''
    SELECT i.LastObservedTime, b.StringValue, f.StringValue, g.StringValue, i.ID
    FROM NonPackagedIdentityRelationship i
    LEFT JOIN BinaryFullPaths b ON b.ID = i.BinaryFullPath
    LEFT JOIN FileIDs f ON f.ID = i.FileID
    LEFT JOIN ProgramIDs g ON g.ID = i.ProgramID
    ORDER BY i.ID'''


def _databases(context):
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.basename(path) == _DATABASE and os.path.isfile(path):
            yield path, context.get_relative_path(path)


def _read(path, relative, label, queries):
    """The rows of each (name, query) pair, or None when the database cannot be read."""
    db = open_sqlite_db_readonly(path)
    if db is None:
        return None
    results = {}
    try:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for name, query in queries:
            if name not in tables:
                logfunc(f'{label}: {relative} has no {name} table')
                results[name] = []
                continue
            results[name] = db.execute(query).fetchall()
    except sqlite3.Error as exc:
        logfunc(f'{label}: could not read {relative}: {exc}')
        return None
    finally:
        db.close()
    return results


@artifact_processor
def capabilityAccessHistory(context):
    label = 'Capability Access History'
    data_headers = (('Start Time (UTC)', 'datetime'), ('Stop Time (UTC)', 'datetime'), 'Capability',
                    'App Type', 'App', 'User SID', 'Access Blocked (as stored)', 'File ID',
                    'Program ID', 'Record ID', 'Source File')
    data_list, sources = [], []
    for path, relative in _databases(context):
        results = _read(path, relative, label, (('PackagedUsageHistory', _PACKAGED),
                                                ('NonPackagedUsageHistory', _NON_PACKAGED)))
        if results is None:
            continue
        sources.append(path)
        rows = [('Packaged',) + row for row in results['PackagedUsageHistory']]
        rows += [('NonPackaged',) + row for row in results['NonPackagedUsageHistory']]
        rows.sort(key=lambda r: (r[1] or 0, r[0], r[9]))
        for app_type, start, stop, capability, app, sid, blocked, file_id, program_id, record in rows:
            data_list.append((filetime_utc(start), filetime_utc(stop), capability or '', app_type,
                              app or '', sid or '', blocked, file_id or '', program_id or '', record,
                              relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def capabilityAccessIdentities(context):
    label = 'Capability Access Program Identities'
    data_headers = (('Last Observed Time (UTC)', 'datetime'), 'Binary Path', 'File ID', 'Program ID',
                    'Record ID', 'Source File')
    data_list, sources = [], []
    for path, relative in _databases(context):
        results = _read(path, relative, label, (('NonPackagedIdentityRelationship', _IDENTITIES),))
        if results is None:
            continue
        sources.append(path)
        for observed, binary, file_id, program_id, record in results['NonPackagedIdentityRelationship']:
            data_list.append((filetime_utc(observed), binary or '', file_id or '', program_id or '',
                              record, relative))
    return data_headers, data_list, '\n'.join(sources)
