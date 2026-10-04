__artifacts_v2__ = {
    "macosExecPolicyScanTargets": {
        "name": "Scan Targets",
        "description": "Rows of the scan_targets_v2 table in ExecPolicy: path, responsible path, "
                       "the library and used values as stored, and the timestamp and measured "
                       "timestamp.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the scan_targets_v2 table of '
            "/private/var/db/SystemPolicyConfiguration/ExecPolicy, with its -wal. Scott Knight's "
            'reverse engineering of syspolicyd on macOS 10.14 found this table written by the '
            "daemon's logExecutable method and, by his reading, by a weekly job that searches "
            'known bundle locations for bundles to scan, and read by a job that runs every three '
            "days to measure the targets (Reference: Scott Knight, 'syspolicyd internals', "
            'https://knight.sc/reverse%20engineering/2019/02/20/syspolicyd-internals.html). On '
            'his reading, then, a row is not by itself evidence that its path was run. Path, '
            'Responsible Path, Is Library and Is Used are reported as stored, and what Is Library '
            "and Is Used record is not established here. The table's own CREATE statement gives "
            "timestamp a default of strftime('%s','now'), the current time as seconds since "
            "1970-01-01 in UTC (Reference: SQLite, 'Date And Time Functions', "
            'https://www.sqlite.org/lang_datefunc.html), and the query Knight quotes for the '
            "measuring job reads measured_timestamp with SQLite's unixepoch modifier, which reads "
            'a number as seconds since 1970. Both are read as Unix seconds, and a time stored as '
            '0 is left blank, as measured_timestamp is on 1 row of the public MacBook Pro logical '
            'extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15). On that '
            'extraction the rows for /Applications/Google Drive.app and for '
            '/Library/Google/GoogleSoftwareUpdate/GoogleSoftwareUpdate.bundle, the second with '
            "Installer.app's executable as Responsible Path, have a Timestamp of 2025-12-09 "
            '21:44:51, the second the Mac\'s install.log records \'Installed "Google Drive"\' '
            '(16:44:51-05), and the row for /Library/Application '
            'Support/Google/GoogleUpdater/PkgStaging/GoogleUpdater.app has a Timestamp of '
            '2025-12-24 22:05:23, the second of a later \'Installed "Google Drive"\' line '
            "(17:05:23-05). On dleapp_macos_bigsur each row's Timestamp equals the Timestamp of "
            "the Gatekeeper Scan Cache row whose Object ID is the inode number of the row's path, "
            'on all 23 rows. The 23 rows there are the VMware Tools daemon, mount_vmhgfs and 21 '
            '.dylib files under the VMware Tools folder, with Timestamps from 2020-12-02 15:17:16 '
            'to 15:18:33. On dleapp_macos_bigsur Responsible Path, the daemon, and Measured '
            'Timestamp, 2021-02-19 19:42:05, each held one value on all 23 rows, and Is Used held '
            '1 on all 23 rows. On the public MacBook Pro extraction Is Library held 0 on all 20 '
            'rows. When a logical extraction holds the database under private/var and under '
            'System/Volumes/Data/private/var, a row both copies hold is reported once and Source '
            "File lists both; the public MacBook Pro extraction's two copies are byte-identical. "
            'The other ExecPolicy tables are not reported: legacy_exec_history_v4, which Knight '
            'found written for 32-bit executables, is empty on dleapp_macos_bigsur and absent on '
            'the public MacBook Pro extraction; old_platform_cache holds 5 rows of a key and a '
            'time on dleapp_macos_bigsur and is absent on the other; policy_scan_cache_by_path '
            'and policy_cache_by_path_meta are empty on both; policy_cache_meta holds a miss '
            'count of 0 on every row of both; historic_gk_overrides, historic_malware_blocks and '
            'staged_samples are empty on the public MacBook Pro extraction and absent on '
            'dleapp_macos_bigsur; and settings holds 4 name and value pairs on '
            'dleapp_macos_bigsur and 8 on the public MacBook Pro extraction.'
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/ExecPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 23 rows",
        },
    },
    "macosExecPolicyMeasurements": {
        "name": "Executable Measurements",
        "description": "Rows of the executable_measurements_v2 table in ExecPolicy: file "
                       "identifier, bundle, team and signing IDs, CDHash, file size, flag values "
                       "as stored, and three times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the executable_measurements_v2 table of '
            "/private/var/db/SystemPolicyConfiguration/ExecPolicy, with its -wal. Scott Knight's "
            'reverse engineering of syspolicyd on macOS 10.14 found a job that runs every three '
            'days and reads Scan Targets to measure them, and a daily job reading this table, '
            "with reported_timestamp read through SQLite's unixepoch modifier, and posting the "
            'rows through the private WirelessDiagnostics framework (Reference: Scott Knight, '
            "'syspolicyd internals', "
            'https://knight.sc/reverse%20engineering/2019/02/20/syspolicyd-internals.html). File '
            'Identifier, Responsible File Identifier, Bundle ID, Bundle Version, Team ID, Signing '
            'ID, CDHash, Main Executable Hash, File Size and the Is Signed, Is Valid, Is '
            'Quarantined, Is Library and Is Used values are reported as stored, and what the five '
            'flag values record is not established here. Its timestamp column has the same '
            "strftime('%s','now') default as Scan Targets' (Reference: SQLite, 'Date And Time "
            "Functions', https://www.sqlite.org/lang_datefunc.html), reported_timestamp is read "
            'as Unix seconds as that query reads it, and executable_timestamp is read as Unix '
            'seconds on this evidence: on dleapp_macos_bigsur it equals the modification time the '
            'image records for the file of that File Identifier under the VMware Tools folder, on '
            'all 23 rows. A time stored as 0 is left blank, and none was found on either image. '
            'On that image, where every row is a VMware Tools file, Timestamp (2020-12-12 '
            '15:44:02), Reported Timestamp (2021-02-19 19:28:51), Responsible File Identifier '
            '(vmware-tools-daemon), Team ID, Main Executable Hash (the text secure-ts), Is '
            'Signed, Is Valid, Is Quarantined and Is Used each held one value on all 23 rows. On '
            'dleapp_macos_bigsur Bundle ID and Bundle Version were empty on every row. On the '
            'public MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15'
            ') Main Executable Hash held 64 hexadecimal digits on all 20 rows, and Is '
            'Library held 0 on all 20 rows. Is Signed and Is Valid were identical on every row of '
            'both images. Every CDHash on dleapp_macos_bigsur, and 15 of the 20 on the public '
            'MacBook Pro extraction, also appears in Gatekeeper Scan Cache. When a logical '
            'extraction holds the database under private/var and under '
            'System/Volumes/Data/private/var, a row both copies hold is reported once and Source '
            "File lists both; the public MacBook Pro extraction's two copies are byte-identical."
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/ExecPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "hash",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 23 rows",
        },
    },
    "macosGatekeeperScanCache": {
        "name": "Gatekeeper Scan Cache",
        "description": "Rows of the policy_scan_cache table in ExecPolicy: bundle, signing and "
                       "team IDs, CDHash, policy match and malware result values as stored, "
                       "volume UUID, object ID and three times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the policy_scan_cache table of '
            '/private/var/db/SystemPolicyConfiguration/ExecPolicy, with its -wal. Brandon Dalton '
            'writes that the scan cache tables in this database are updated with the results of '
            "any scan that occurs (Reference: Brandon Dalton, 'Gatekeeping in macOS: Keeping "
            "adversaries off our Apples', "
            'https://redcanary.com/blog/threat-detection/gatekeeper/). Bundle ID, Signing ID, '
            'Team ID, CDHash, Policy Match, Top Policy Match, Matched Rule Name, Malware Result, '
            'Flags, File System, Volume UUID and Object ID are reported as stored, and what the '
            'numbers record is not established here. A Malware Result of 1 is not by itself a '
            'malware finding: it held 1 on 6 of the 54 rows on dleapp_macos_bigsur and on 24 of '
            'the 51 rows on the public MacBook Pro logical extraction (macOS 15.4 build 24E248, '
            "corpus key mvs2026_macbookpro_macos15), and on both images those include Apple's own XProtect "
            'and Malware Removal Tool (com.apple.XProtect and com.apple.MRT). Timestamp, Mod Time '
            'and Revocation Check Time are read as Unix seconds in UTC, on this evidence: on '
            'dleapp_macos_bigsur the nine rows for the scripts in /private/etc/periodic/daily '
            'have Timestamps from 2021-02-17 16:39:10 to 16:39:12 and the row for '
            "/private/etc/periodic/weekly/999.local 2021-02-19 19:30:06, and that Mac's daily.out "
            'and weekly.out logs record runs starting Wed Feb 17 11:39:10 EST 2021 and Fri Feb 19 '
            '14:30:06 EST 2021 (16:39:10 and 19:30:06 UTC). What Mod Time and Revocation Check '
            'Time record is not established here. A time stored as 0 is left blank, and none was '
            "found on either image. On dleapp_macos_bigsur each of the 52 apfs rows' Object ID is "
            "the inode number of a file or bundle on the image's Data volume: 29 VMware files and "
            "bundles, Apple's XProtect and MRT bundles, 11 iLife Media Browser plug-ins and 10 "
            'periodic scripts; the image holds no volume for its 2 hfs rows. Every one of those '
            'apfs rows whose Bundle ID is NOT_A_BUNDLE resolves to a file, and every other one to '
            'a bundle directory. The macOS 11 table has no top_policy_match or matched_rule_name '
            'column, so Top Policy Match and Matched Rule Name are empty on all 54 rows of '
            'dleapp_macos_bigsur. Matched Rule Name is also empty on all 51 rows of the public '
            'MacBook Pro extraction. When a logical extraction holds the database under '
            'private/var and under System/Volumes/Data/private/var, a row both copies hold is '
            "reported once and Source File lists both; the public MacBook Pro extraction's two "
            'copies are byte-identical.'
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/ExecPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 54 rows",
        },
    },
    "macosExecPolicyProvenance": {
        "name": "Provenance Tracking",
        "description": "Rows of the provenance_tracking table in ExecPolicy: path, bundle, "
                       "signing and team IDs, CDHash, flags, the row's key and link key, the "
                       "path of the row the link key names, and a timestamp.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the provenance_tracking table of '
            '/private/var/db/SystemPolicyConfiguration/ExecPolicy, with its -wal. Howard Oakley '
            'describes provenance tracking on macOS 13.3.1 as the com.apple.provenance extended '
            'attribute, whose 11 bytes hold an 8-byte integer primary key, together with this '
            "table, which also stores the app's cdhash, and describes syspolicyd reporting the "
            "creation of provenance data in the app's entry in this database on the app's first "
            'run, once Gatekeeper has completed its evaluation and the user has approved running '
            "it (Reference: Howard Oakley, 'How macOS now tracks the provenance of apps', "
            'https://eclecticlight.co/2023/05/10/how-macos-now-tracks-the-provenance-of-apps/). '
            "Path is the table's url column, which held a path on all 7 rows of the public "
            'MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15'
            '). Bundle ID, Signing ID, Team ID, CDHash, Flags, PK and Link PK are reported as '
            'stored; Flags held 2 on all 7 rows, and what it and Link PK record is not '
            'established here. Linked Path is the Path of the row in the same copy of the '
            'database whose PK equals Link PK, and is blank for a Link PK of 0 or one that no row '
            'carries. On the public MacBook Pro extraction the 5 non-zero Link PKs all name the '
            '/Applications/Google Chrome.app row, and those 5 rows are three Google updater items '
            '(a GoogleUpdater folder, a GoogleUpdater.app and a GoogleSoftwareUpdate.bundle), a '
            "Google Chat app under a user's Applications folder and a .keystone_install path "
            'under a temporary folder. Timestamp is read as Unix seconds in UTC like the '
            'Gatekeeper Scan Cache times: each of the 4 rows whose CDHash also appears in '
            'Gatekeeper Scan Cache has a Timestamp equal to, or 1 second after, a Timestamp of '
            'that CDHash there. A time stored as 0 is left blank, and none was found. The table '
            'is absent from dleapp_macos_bigsur, and that is logged. When a logical extraction '
            'holds the database under private/var and under System/Volumes/Data/private/var, a '
            'row both copies hold is reported once and Source File lists both; the public MacBook '
            "Pro extraction's two copies are byte-identical."
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/ExecPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
        },
    },
}

import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_powerlog import merge_sources

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _blank(value):
    return '' if value is None else value


def _databases(context):
    """Staged copies of ExecPolicy (not its sidecars or directories)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == 'ExecPolicy' and not os.path.isdir(str(path))})


def _unix_time(value):
    """Unix seconds as a UTC datetime; blank for no value and for 0; the stored value when it
    is not a number."""
    if value is None or value == 0:
        return ''
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    try:
        return _UNIX_EPOCH + timedelta(seconds=value)
    except OverflowError:
        return value


def _select(path, table, columns):
    """A SELECT of columns from table, with NULL standing in for a column this copy lacks."""
    present = {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}
    return ', '.join(column if column in present else f'NULL AS {column}' for column in columns)


def _rows(context, table, columns, order):
    """(path, relative path, rows) for every staged ExecPolicy holding table; a copy without
    it is logged and skipped."""
    for path in _databases(context):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, table):
            logfunc(f'ExecPolicy: no {table} table in {relative}')
            continue
        query = f'SELECT {_select(path, table, columns)} FROM {table} ORDER BY {order}'
        yield path, relative, get_sqlite_db_records(path, query)


def _report(records, read):
    """Rows held by more than one copy reported once, with every copy listed."""
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_list, '\n'.join(read)


@artifact_processor
def macosExecPolicyScanTargets(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), ('Measured Timestamp (UTC)', 'datetime'),
                    'Path', 'Responsible Path', 'Is Library (as stored)', 'Is Used (as stored)',
                    'Source File')
    columns = ('timestamp', 'measured_timestamp', 'path', 'responsible_path', 'is_library',
               'is_used')
    records, read = [], []
    for path, relative, rows in _rows(context, 'scan_targets_v2', columns, 'timestamp, path'):
        if rows:
            read.append(path)
        for row in rows:
            records.append(((_unix_time(row['timestamp']), _unix_time(row['measured_timestamp']),
                             _blank(row['path']), _blank(row['responsible_path']),
                             _blank(row['is_library']), _blank(row['is_used'])), relative))
    data_list, source = _report(records, read)
    return data_headers, data_list, source


@artifact_processor
def macosExecPolicyMeasurements(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), ('Reported Timestamp (UTC)', 'datetime'),
                    ('Executable Timestamp (UTC)', 'datetime'), 'File Identifier',
                    'Responsible File Identifier', 'Bundle ID', 'Bundle Version', 'Team ID',
                    'Signing ID', 'CDHash', 'Main Executable Hash', 'File Size',
                    'Is Signed (as stored)', 'Is Valid (as stored)', 'Is Quarantined (as stored)',
                    'Is Library (as stored)', 'Is Used (as stored)', 'Source File')
    columns = ('timestamp', 'reported_timestamp', 'executable_timestamp', 'file_identifier',
               'responsible_file_identifier', 'bundle_identifier', 'bundle_version',
               'team_identifier', 'signing_identifier', 'cdhash', 'main_executable_hash',
               'file_size', 'is_signed', 'is_valid', 'is_quarantined', 'is_library', 'is_used')
    records, read = [], []
    for path, relative, rows in _rows(context, 'executable_measurements_v2', columns,
                                      'timestamp, file_identifier, cdhash'):
        if rows:
            read.append(path)
        for row in rows:
            records.append(((_unix_time(row['timestamp']), _unix_time(row['reported_timestamp']),
                             _unix_time(row['executable_timestamp']))
                            + tuple(_blank(row[column]) for column in columns[3:]), relative))
    data_list, source = _report(records, read)
    return data_headers, data_list, source


@artifact_processor
def macosGatekeeperScanCache(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), ('Mod Time (UTC)', 'datetime'),
                    ('Revocation Check Time (UTC)', 'datetime'), 'Bundle ID', 'Signing ID',
                    'Team ID', 'CDHash', 'Policy Match (as stored)', 'Top Policy Match (as stored)',
                    'Matched Rule Name', 'Malware Result (as stored)', 'Flags (as stored)',
                    'File System', 'Volume UUID', 'Object ID', 'Source File')
    columns = ('timestamp', 'mod_time', 'revocation_check_time', 'bundle_id', 'signing_identifier',
               'team_identifier', 'cdhash', 'policy_match', 'top_policy_match', 'matched_rule_name',
               'malware_result', 'flags', 'fs_type_name', 'volume_uuid', 'object_id')
    records, read = [], []
    for path, relative, rows in _rows(context, 'policy_scan_cache', columns, 'timestamp, pk'):
        if rows:
            read.append(path)
        for row in rows:
            records.append(((_unix_time(row['timestamp']), _unix_time(row['mod_time']),
                             _unix_time(row['revocation_check_time']))
                            + tuple(_blank(row[column]) for column in columns[3:]), relative))
    data_list, source = _report(records, read)
    return data_headers, data_list, source


@artifact_processor
def macosExecPolicyProvenance(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Path', 'Bundle ID', 'Signing ID', 'Team ID',
                    'CDHash', 'Flags (as stored)', 'PK', 'Link PK', 'Linked Path', 'Source File')
    columns = ('timestamp', 'url', 'bundle_id', 'signing_identifier', 'team_identifier', 'cdhash',
               'flags', 'pk', 'link_pk')
    records, read = [], []
    for path, relative, rows in _rows(context, 'provenance_tracking', columns, 'timestamp, pk'):
        if rows:
            read.append(path)
        # A link key names a row of the same copy.
        paths_by_key = {row['pk']: row['url'] for row in rows}
        for row in rows:
            link = row['link_pk']
            linked = _blank(paths_by_key.get(link)) if link else ''
            records.append(((_unix_time(row['timestamp']),)
                            + tuple(_blank(row[column]) for column in columns[1:]) + (linked,),
                            relative))
    data_list, source = _report(records, read)
    return data_headers, data_list, source
