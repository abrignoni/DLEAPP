"""XProtect Behavior Service events in XPdb, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosXProtectBehaviorEvents": {
        "name": "XProtect Behavior Service Events",
        "description": "Rows of the events table in XPdb: the dt time, the violated rule, the "
                       "exec and responsible path, signing ID, team ID, cdhash, sha256 and "
                       "notarized values, reported and profile_hash as stored, and the "
                       "database's schema version.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the events table of XPdb, at /private/var/protected/xprotect/db/XPdb (the '
            'public MacBook Pro logical extraction, macOS 15.4, corpus key '
            'mvs2026_macbookpro_macos15) and at /private/var/protected/xprotect/XPdb, the path '
            '(written /var/protected/xprotect/XPdb) that Stuart Ashenbrenner gives for macOS '
            'Ventura, with its -wal. One row per events row. '
            "Ashenbrenner writes that this database seems to be for behavioral detections "
            "(Reference: Stuart Ashenbrenner, Huntress, 'dmXProtect: Stop, Drop, Shut Malware "
            "Down Before It Opens Up Shop', 28 June 2023, archived at "
            'https://web.archive.org/web/20261009214044/https://www.huntress.com/blog/dmxprotect-stop-drop-shut-malware-down-before-it-opens-up-shop'
            '), and Howard Oakley that, as of June 2024, XProtect Behavior Service and Bastion record suspicious '
            "events in it, report them to Apple and do not intervene (Reference: Howard Oakley, "
            "'What do XProtect BehaviourService and Bastion rules do?', 28 June 2024, archived at "
            'https://web.archive.org/web/20260503013405/https://eclecticlight.co/2024/06/28/what-do-xprotect-behaviourservice-and-bastion-rules-do/'
            '). Neither source defines the columns (Ashenbrenner shows one raw events row '
            'without column names), so a row is not by itself evidence that '
            'the executable was malicious or was blocked, and every column other than Event '
            'Time is reported as stored under a header made from its column name: Event ID is '
            'id, Violated Rule is violated_rule, the Exec columns are exec_path, '
            'exec_signing_id, exec_team_id, exec_cdhash, exec_sha256 and exec_is_notarized, the '
            'Responsible columns the matching responsible_ columns, and Reported and Profile '
            'Hash are reported and profile_hash. A NULL is shown as an empty cell; the public '
            'MacBook Pro extraction held no NULL in any column. What Reported, Profile Hash and the two '
            'notarized values record is not established here. Schema Version is the value of '
            'databaseSchemaVersion in the settings table, the only row that table held on the '
            'public MacBook Pro extraction. Event Time (UTC) is the dt column, stored as text '
            "in the form YYYY-MM-DD HH:MM:SS, read as UTC with no conversion; a value in any "
            "other form is passed on unchanged by this artifact. The table's CREATE statement gives dt a default of "
            "datetime('now'), which SQLite documents as returning that form, in UTC (Reference: "
            "SQLite, 'Date And Time Functions', https://www.sqlite.org/lang_datefunc.html); "
            'whether the writer relies on that default or supplies dt itself is not '
            'established. On the public MacBook Pro extraction the earliest Event Time equals, '
            'to the second, the creation time, and the latest the modification time, that the '
            "acquisition's zip records for XPdb in its NTFS extra field. On that extraction the events table held 150 "
            'rows: Event ID ran from 1 to 150 with no gap, Violated Rule held 10 distinct '
            'values, Exec Team ID was an empty string on 41 rows and Responsible Team ID on 42, '
            'the two notarized values held 0 or 1, and Reported (0), Profile Hash and Schema '
            'Version (1) each held one value on all 150 rows. The extraction holds XPdb under '
            'private/var and again under System/Volumes/Data/private/var, byte-identical with '
            'their -wal, so the second copy is not read again and is counted in the run log, '
            'and Source File names the copy read. When the two copies differ, both are read, '
            'an event both hold is reported once, and Source File lists both. Source File stays '
            'because the two paths and the two folder views can each hold a copy. The -wal '
            'beside both copies held 0 bytes. No events table is found on dleapp_macos_bigsur '
            '(macOS 11.2.1) or on magnet2021_macos_bigsur (macOS 11.2.1), which hold no XPdb, '
            'nor on evidencelocker_macos14 (macOS 14.6.1), whose /private/var/protected/xprotect '
            'folder is empty.'
        ),
        "paths": ('*/var/protected/xprotect/XPdb*', '*/var/protected/xprotect/db/XPdb*'),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 150 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources

_LABEL = 'XProtect Behavior Service Events'
_COLUMNS = ('dt', 'id', 'violated_rule', 'exec_path', 'exec_signing_id', 'exec_team_id',
            'exec_cdhash', 'exec_sha256', 'exec_is_notarized', 'responsible_path',
            'responsible_signing_id', 'responsible_team_id', 'responsible_cdhash',
            'responsible_sha256', 'responsible_is_notarized', 'reported', 'profile_hash')


def _blank(value):
    return '' if value is None else value


def _utc(value):
    """dt as stored, 'YYYY-MM-DD HH:MM:SS' text, read as UTC; any other value as stored."""
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        except ValueError:
            return value
    return _blank(value)


def _select(path, table, columns):
    """A SELECT list of columns, with NULL standing in for a column this copy lacks."""
    present = {row[1] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}
    return ', '.join(column if column in present else f'NULL AS {column}' for column in columns)


def _schema_version(path):
    if not does_table_exist_in_db(path, 'settings'):
        return ''
    rows = get_sqlite_db_records(
        path, "SELECT value FROM settings WHERE name = 'databaseSchemaVersion'")
    return _blank(rows[0][0]) if rows else ''


@artifact_processor
def macosXProtectBehaviorEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Violated Rule', 'Exec Path',
                    'Exec Signing ID', 'Exec Team ID', 'Exec CDHash', 'Exec SHA-256',
                    'Exec Is Notarized (as stored)', 'Responsible Path',
                    'Responsible Signing ID', 'Responsible Team ID', 'Responsible CDHash',
                    'Responsible SHA-256', 'Responsible Is Notarized (as stored)',
                    'Reported (as stored)', 'Profile Hash (as stored)', 'Schema Version',
                    'Source File')
    databases = [str(path) for path in context.get_files_found()
                 if os.path.basename(str(path)) == 'XPdb' and os.path.isfile(str(path))]
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'events'):
            logfunc(f'{_LABEL}: no events table read from {relative}')
            continue
        read.append(path)
        version = _schema_version(path)
        rows = get_sqlite_db_records(
            path, f'SELECT {_select(path, "events", _COLUMNS)} FROM events ORDER BY dt, id')
        if not rows:
            logfunc(f'{_LABEL}: no events in {relative}')
        for row in rows:
            data_list.append((_utc(row[0]),) + tuple(_blank(value) for value in row[1:])
                             + (version, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
