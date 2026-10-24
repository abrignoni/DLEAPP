"""Apple Account records kept by the AuthKit daemon (akd) on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosAuthKitAuthorizedApps": {
        "name": "AuthKit Authorized Applications",
        "description": "Rows of the authorized_applications table in each user's AuthKit "
                       "authorization.db, joined to authorized_teams and to "
                       "authorized_primary_applications, plus one row per team no application "
                       "names, with creation date, client name and ID, "
                       "the primary app's name, developer and App Store ID, team ID, scopes and "
                       "the stored state values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads authorized_applications in each user's ~/Library/Application "
                 "Support/com.apple.akd/authorization.db, joined to authorized_teams on team_id and to"
                 " authorized_primary_applications on client_id. The primary application is the row's "
                 "Primary Client ID, or the row's own Client ID when Primary Client ID is blank or "
                 "holds the four-letter text NULL. A team that no application row names gets a row of "
                 "its own holding only the team columns. Created is creation_date read as Unix "
                 "seconds. The column is declared NOT NULL DEFAULT 0, and a 0 is reported blank. On "
                 "the public MacBook Pro logical extraction (macOS 15.4, corpus key "
                 "mvs2026_macbookpro_macos15) the 8 values fall on 20 November 2025 (2 rows) and 11 "
                 "December 2025 (6 rows), UTC; read as seconds since 1 January 2001 they would fall in"
                 " 2056. What event creation_date records is not established. App Store ID (adam_id): "
                 "on that image both values return, in Apple's public iTunes lookup "
                 "(https://itunes.apple.com/lookup?id=<value>), an app whose name begins with the "
                 "row's Primary App Name and whose bundle ID equals the Primary Client ID. The 8 rows "
                 "name 8 client IDs under 2 teams and 2 primary apps. Credential State, Transfer State"
                 " and Origin are reported as stored because their values are not documented: "
                 "Credential State (as stored) held 1, Transfer State (as stored) held the text NULL "
                 "and Origin (as stored) held 0 on all 8 rows. Primary Client ID holds the text NULL "
                 "on the 2 rows that are themselves primary apps. Team uid is the authorized_teams uid"
                 " as stored. Team Private Email had no value on any of the 8 rows: private_email is "
                 "NULL in both team rows. All rows on that image come from one user, so User holds one"
                 " value there. Schema version 4 (db_version 4 in the version table, seen on "
                 "dleapp_macos_bigsur, magnet2021_macos_bigsur and evidencelocker_macos14) has no "
                 "creation_date, client_name, private_email or authorized_primary_applications, so "
                 "those columns are blank for it. Every version 4 file in those images holds 0 "
                 "application and 0 team rows, so reading a version 4 file with rows is tested only on"
                 " files built for the unit test. Not reported: the version table and "
                 "authorizedAppListVersion (a schema number and a 64-character hexadecimal value). "
                 "Other akd stores: ~/Library/Caches/com.apple.akd/Cache.db is a URL cache that App "
                 "URL Cache's paths match, and "
                 "~/Library/HTTPStorages/com.apple.akd/httpstorages.sqlite held only an table named "
                 "alt_services on the MacBook Pro and is not reported. Whether a row is removed when "
                 "an authorization is revoked is not tested. User is the folder after Users in the "
                 "source path, or root under private/var/root, and is blank when the input is one "
                 "user's home folder whose path names no user. When a logical extraction holds the "
                 "same file under Users/ and under System/Volumes/Data/Users/, a second copy "
                 "byte-identical to the first is not read again, and is counted in the run log; copies"
                 " that differ are all read, and a row they share is reported once with each file in "
                 "Source File. A database whose akd folder sits in a Library nested inside another "
                 "Library, such as an app's Containers/<id>/Data/Library, is not read and is named in "
                 "the run log. The tables are described in Yogesh Khatri's AKD plugin for mac_apt "
                 "(MIT): "
                 "https://github.com/ydkhatri/mac_apt/blob/b223166e102e6294aed3132c46bc37316e700d64/plugins/akd.py",
        "paths": ('*/Library/Application Support/com.apple.akd/authorization.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 8 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (schema version 4, tables empty)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (schema version 4, tables empty)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (schema version 4, tables empty)",
        },
    },
    "macosAppleAccountDevices": {
        "name": "Apple Account Devices (AuthKit)",
        "description": "Rows of the device_list table in each user's AuthKit devicelist.db, "
                       "with last updated and last cache updated dates, device name, model, OS, "
                       "build, serial number, IMEI where stored, trusted shown as Yes or No for 1 "
                       "and 0, and the circle status and services values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads device_list in each user's ~/Library/Application "
                 "Support/com.apple.akd/devicelist.db, the table iLEAPP's appleAccountDeviceList reads"
                 " on iOS. Last Updated and Last Cache Updated are last_updated_date and "
                 "last_cache_updated_date read as Unix seconds. On the public MacBook Pro logical "
                 "extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) the 2 Last Updated "
                 "values fall on 12 December 2025 and the 2 Last Cache Updated values within 6 ms of "
                 "each other on 24 December 2025, UTC; read as seconds since 1 January 2001 they would"
                 " fall in 2056. When and how akd fills or refreshes the list, and whether it matches "
                 "the account at extraction time, are not established, and a row does not establish "
                 "that the device ever connected to this Mac. IMEI is every imei in the phones array "
                 "of additional_info, read as JSON; 1 of the 2 rows carried one, and the other's "
                 "additional_info held an empty JSON object. Additional Info is the column as text, "
                 "and is kept as text when it is not JSON. Trusted shows 1 and 0 as Yes and No and any"
                 " other value as stored. Circle Status (as stored) held 0 on both rows. dc, clcg, "
                 "clbg, clhs and dec are reported with their database names because their meaning is "
                 "not documented; dc and clcg were identical on both rows (blank on one, 1 on the "
                 "other). No devicelist.db is present on dleapp_macos_bigsur, magnet2021_macos_bigsur "
                 "or evidencelocker_macos14, whose akd folders hold no devicelist.db or "
                 "privateEmails.db, so the table is read on macOS 15.4 only. A column a file's table "
                 "lacks is reported blank rather than costing the row. User is the folder after Users "
                 "in the source path, or root under private/var/root, and is blank when the input is "
                 "one user's home folder whose path names no user. When a logical extraction holds the"
                 " same file under Users/ and under System/Volumes/Data/Users/, a second copy "
                 "byte-identical to the first is not read again, and is counted in the run log; copies"
                 " that differ are all read, and a row they share is reported once with each file in "
                 "Source File. A database whose akd folder sits in a Library nested inside another "
                 "Library, such as an app's Containers/<id>/Data/Library, is not read and is named in "
                 "the run log. The table is described in Yogesh Khatri's AKD plugin for mac_apt (MIT):"
                 " "
                 "https://github.com/ydkhatri/mac_apt/blob/b223166e102e6294aed3132c46bc37316e700d64/plugins/akd.py",
        "paths": ('*/Library/Application Support/com.apple.akd/devicelist.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (no devicelist.db)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (no devicelist.db)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no devicelist.db)",
        },
    },
    "macosAppleAccountDeletedDevices": {
        "name": "Apple Account Deleted Devices (AuthKit)",
        "description": "Rows of the deleted_device_list table in each user's AuthKit "
                       "devicelist.db, with deleted and last updated dates and the reason code "
                       "as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads deleted_device_list in each user's ~/Library/Application "
                 "Support/com.apple.akd/devicelist.db. Deleted and Last Updated are deleted_date and "
                 "last_updated_date read as Unix seconds, the same reading device_list's dates take in"
                 " this file; no stored deleted_date has been seen to confirm it. The reason column is"
                 " an integer code whose values are not documented, so it is reported as stored. The "
                 "table was empty on the only image holding devicelist.db (mvs2026_macbookpro_macos15,"
                 " macOS 15.4), so this artifact is tested only on files built for the unit test. User"
                 " is the folder after Users in the source path, or root under private/var/root, and "
                 "is blank when the input is one user's home folder whose path names no user. When a "
                 "logical extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a second copy byte-identical to the first is not read "
                 "again, and is counted in the run log; copies that differ are all read, and a row "
                 "they share is reported once with each file in Source File. A database whose akd "
                 "folder sits in a Library nested inside another Library, such as an app's "
                 "Containers/<id>/Data/Library, is not read and is named in the run log.",
        "paths": ('*/Library/Application Support/com.apple.akd/devicelist.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (table present but empty)",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (no devicelist.db)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (no devicelist.db)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no devicelist.db)",
        },
    },
    "macosAuthKitPrivateEmails": {
        "name": "AuthKit Private Emails",
        "description": "Rows of the emails table in each user's AuthKit privateEmails.db, with "
                       "the client key and email address as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads the emails table (client_key, email) in each user's ~/Library/Application "
                 "Support/com.apple.akd/privateEmails.db and reports both columns as stored. What the "
                 "addresses are used for, and which client a client_key names, are not established. "
                 "The table was empty on the only image holding privateEmails.db "
                 "(mvs2026_macbookpro_macos15, macOS 15.4), so this artifact is tested only on files "
                 "built for the unit test. The version table is not reported. User is the folder after"
                 " Users in the source path, or root under private/var/root, and is blank when the "
                 "input is one user's home folder whose path names no user. When a logical extraction "
                 "holds the same file under Users/ and under System/Volumes/Data/Users/, a second copy"
                 " byte-identical to the first is not read again, and is counted in the run log; "
                 "copies that differ are all read, and a row they share is reported once with each "
                 "file in Source File. A database whose akd folder sits in a Library nested inside "
                 "another Library, such as an app's Containers/<id>/Data/Library, is not read and is "
                 "named in the run log. The table is described in Yogesh Khatri's AKD plugin for "
                 "mac_apt (MIT): "
                 "https://github.com/ydkhatri/mac_apt/blob/b223166e102e6294aed3132c46bc37316e700d64/plugins/akd.py",
        "paths": ('*/Library/Application Support/com.apple.akd/privateEmails.db*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "mail",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (table present but empty)",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (no privateEmails.db)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (no privateEmails.db)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no privateEmails.db)",
        },
    },
}

import json
import os

from scripts.ilapfuncs import (artifact_processor, convert_unix_ts_to_utc, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path


def _text(value):
    return '' if value is None else str(value)


def _unix(value):
    """Unix seconds as a UTC datetime; '' for NULL and for 0, which creation_date holds by
    default (NOT NULL DEFAULT 0) when no date was written."""
    if value in (None, '', 0, 0.0):
        return ''
    return convert_unix_ts_to_utc(value)


def _yes_no(value):
    """The trusted column: 1 and 0 as Yes and No, anything else as stored."""
    return {1: 'Yes', 0: 'No'}.get(value, _text(value))


_AKD_FOLDER = '/Library/Application Support/com.apple.akd/'


def _in_a_home_library(relative):
    """True when the akd folder is in a home folder's own Library, not in a Library nested
    inside another one, such as an app's Containers/<id>/Data/Library."""
    path = '/' + str(relative).replace('\\', '/').lstrip('/')
    index = path.find(_AKD_FOLDER)
    return index >= 0 and 'Library' not in path[:index].split('/')


def _sources(context, name, label):
    """The named database in each user's akd folder, less byte-identical copies of one file
    under a second volume view."""
    databases = []
    for path in context.get_files_found():
        if os.path.basename(str(path)) != name:
            continue
        if not _in_a_home_library(context.get_relative_path(path)):
            logfunc(f'{label}: {context.get_relative_path(path)} is not in a home folder\'s '
                    'Library/Application Support/com.apple.akd, not read')
            continue
        databases.append(path)
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=label)
    return paths


def _columns(path, table):
    return {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}


def _column(columns, table_alias, column):
    """table_alias.column AS column when the file has it, else NULL AS column, so a file
    written by an older schema still returns its rows."""
    if column in columns:
        return f'{table_alias}.{column} AS {column}'
    return f'NULL AS {column}'


def _apps_queries(path):
    """The applications query, and the query for teams no application names, for the
    columns and tables this file holds.

    Schema version 4 (db_version in the version table) has no creation_date or client_name
    in authorized_applications, no private_email in authorized_teams and no
    authorized_primary_applications table; version 8 has all of them."""
    apps = _columns(path, 'authorized_applications')
    teams = _columns(path, 'authorized_teams')
    primary = _columns(path, 'authorized_primary_applications')
    fields = [_column(apps, 'a', c) for c in (
        'creation_date', 'client_name', 'client_id', 'primary_client_id', 'team_id', 'scopes',
        'credential_state', 'transfer_state', 'origin')]
    fields += [_column(teams, 't', c) for c in ('uid', 'private_email')]
    fields += [_column(primary, 'p', c) for c in ('app_name', 'app_developer_name', 'adam_id')]
    joins = ''
    if teams:
        joins += ' LEFT JOIN authorized_teams t ON t.team_id = a.team_id'
    if primary:
        joins += (" LEFT JOIN authorized_primary_applications p ON p.client_id = "
                  "CASE WHEN a.primary_client_id IS NULL OR a.primary_client_id IN ('', 'NULL') "
                  "THEN a.client_id ELSE a.primary_client_id END")
    order = 'a.creation_date, a.client_id' if 'creation_date' in apps else 'a.client_id'
    apps_query = (f'SELECT {", ".join(fields)} FROM authorized_applications a{joins} '
                  f'ORDER BY {order}')
    teams_query = ''
    if teams:
        teams_query = ('SELECT t.team_id AS team_id, t.uid AS uid, '
                       f'{_column(teams, "t", "private_email")} FROM authorized_teams t '
                       'WHERE NOT EXISTS (SELECT 1 FROM authorized_applications a '
                       'WHERE a.team_id = t.team_id) ORDER BY t.team_id')
    return apps_query, teams_query


@artifact_processor
def macosAuthKitAuthorizedApps(context):
    data_headers = (('Created', 'datetime'), 'Client Name', 'Client ID', 'Primary App Name',
                    'Primary App Developer', 'App Store ID (adam_id)', 'Primary Client ID',
                    'Team ID', 'Team uid', 'Team Private Email', 'Scopes',
                    'Credential State (as stored)', 'Transfer State (as stored)',
                    'Origin (as stored)', 'User', 'Source File')
    data_list = []
    read = []
    for path in _sources(context, 'authorization.db', 'AuthKit Authorized Applications'):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'authorized_applications'):
            logfunc(f'AuthKit Authorized Applications: no authorized_applications table in {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        apps_query, teams_query = _apps_queries(path)
        for row in get_sqlite_db_records(path, apps_query):
            data_list.append((
                _unix(row['creation_date']), _text(row['client_name']), _text(row['client_id']),
                _text(row['app_name']), _text(row['app_developer_name']), _text(row['adam_id']),
                _text(row['primary_client_id']), _text(row['team_id']), _text(row['uid']),
                _text(row['private_email']), _text(row['scopes']),
                _text(row['credential_state']), _text(row['transfer_state']),
                _text(row['origin']), user, relative,
            ))
        if teams_query:
            for row in get_sqlite_db_records(path, teams_query):
                data_list.append((
                    '', '', '', '', '', '', '', _text(row['team_id']), _text(row['uid']),
                    _text(row['private_email']), '', '', '', '', user, relative,
                ))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


def _decode_additional_info(blob):
    """(IMEIs, text) for additional_info.

    On the tested image the blob is UTF-8 JSON, {} or {"phones": [{"imei": ..., "slotID": ...}]}.
    Anything that is not JSON is kept as text so nothing is dropped.
    """
    if not blob:
        return '', ''
    text = blob.decode('utf-8', 'replace') if isinstance(blob, bytes) else str(blob)
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return '', text
    imeis = []
    if isinstance(parsed, dict):
        for phone in parsed.get('phones') or []:
            if isinstance(phone, dict) and phone.get('imei'):
                imeis.append(str(phone['imei']))
    return ', '.join(imeis), text


_DEVICE_COLUMNS = ('last_updated_date', 'last_cache_updated_date', 'name', 'model', 'os',
                   'os_version', 'build_number', 'serial_number', 'additional_info', 'trusted',
                   'circle_status', 'services', 'mid', 'altDSID', 'dc', 'clcg', 'clbg', 'clhs',
                   'dec')
_DELETED_COLUMNS = ('deleted_date', 'last_updated_date', 'reason', 'mid', 'altDSID')


def _select(path, table, columns, order):
    """SELECT of columns from table, NULL for any this file's table lacks."""
    present = _columns(path, table)
    order = ', '.join(c for c in order if c in present) or 'rowid'
    return (f'SELECT {", ".join(_column(present, "x", c) for c in columns)} '
            f'FROM "{table}" x ORDER BY {order}')


@artifact_processor
def macosAppleAccountDevices(context):
    data_headers = (('Last Updated', 'datetime'), ('Last Cache Updated', 'datetime'),
                    'Device Name', 'Model', 'OS', 'OS Version', 'Build Number', 'Serial Number',
                    'IMEI', 'Trusted', 'Circle Status (as stored)', 'Services',
                    'mid', 'altDSID', 'dc', 'clcg', 'clbg', 'clhs', 'dec',
                    'Additional Info', 'User', 'Source File')
    data_list = []
    read = []
    for path in _sources(context, 'devicelist.db', 'Apple Account Devices'):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'device_list'):
            logfunc(f'Apple Account Devices: no device_list table in {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(
                path, _select(path, 'device_list', _DEVICE_COLUMNS, ('last_updated_date', 'mid'))):
            imei, additional_info = _decode_additional_info(row['additional_info'])
            data_list.append((
                _unix(row['last_updated_date']), _unix(row['last_cache_updated_date']),
                _text(row['name']), _text(row['model']), _text(row['os']),
                _text(row['os_version']), _text(row['build_number']),
                _text(row['serial_number']), imei, _yes_no(row['trusted']),
                _text(row['circle_status']), _text(row['services']), _text(row['mid']),
                _text(row['altDSID']), _text(row['dc']), _text(row['clcg']), _text(row['clbg']),
                _text(row['clhs']), _text(row['dec']), additional_info, user, relative,
            ))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosAppleAccountDeletedDevices(context):
    data_headers = (('Deleted', 'datetime'), ('Last Updated', 'datetime'),
                    'Reason Code (as stored)', 'mid', 'altDSID', 'User',
                    'Source File')
    data_list = []
    read = []
    for path in _sources(context, 'devicelist.db', 'Apple Account Deleted Devices'):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'deleted_device_list'):
            logfunc(f'Apple Account Deleted Devices: no deleted_device_list table in {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(
                path, _select(path, 'deleted_device_list', _DELETED_COLUMNS, ('deleted_date', 'mid'))):
            data_list.append((
                _unix(row['deleted_date']), _unix(row['last_updated_date']),
                _text(row['reason']), _text(row['mid']), _text(row['altDSID']), user, relative,
            ))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosAuthKitPrivateEmails(context):
    data_headers = ('Email', 'Client Key', 'User', 'Source File')
    data_list = []
    read = []
    for path in _sources(context, 'privateEmails.db', 'AuthKit Private Emails'):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'emails'):
            logfunc(f'AuthKit Private Emails: no emails table in {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(
                path, _select(path, 'emails', ('email', 'client_key'), ('email',))):
            data_list.append((_text(row['email']), _text(row['client_key']), user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
