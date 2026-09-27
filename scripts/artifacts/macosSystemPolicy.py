__artifacts_v2__ = {
    "macosKextLoadHistory": {
        "name": "Kext Load History",
        "description": "Rows of the kext_load_history_v3 table in KextPolicy: kernel extension "
                       "path, bundle and team IDs, boot UUID, and the created and last seen times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the kext_load_history_v3 table of '
            '/private/var/db/SystemPolicyConfiguration/KextPolicy, with its -wal. Path, Bundle '
            'ID, Team ID, Boot UUID, Flags and CDHash are reported as stored, and what Flags '
            'records is not established here. created_at and last_seen are stored as text with no '
            'time zone and are read as UTC, on this evidence: on dleapp_macos_bigsur the '
            'created_at of the two VMware kexts, 2020-12-02 15:16:17 and 15:16:22, falls 17 and '
            "22 seconds after the first VMware Tools Installer line in that Mac's install.log, "
            'stamped 2020-12-02 07:16:00-08 (15:16:00 UTC), and on the public MacBook Pro logical '
            'extraction (macOS 15.4 build 24E248, not a registered corpus key) two of the three '
            'last_seen values, 2025-12-12 15:48:26 and 15:48:27, fall 3 and 4 seconds after the '
            "last 'powerd process is started' record in its power management log (Power "
            "Management Log (ASL)), at 2025-12-12 15:48:23 UTC, while the third equals its row's "
            "created_at. Read in the Mac's own time zone, either pair would be hours apart. What "
            'created_at and last_seen record is not established here. On dleapp_macos_bigsur Last '
            'Seen (UTC), 2021-02-19 19:53:28, and Boot UUID each held one value on all 5 rows; on '
            'the public MacBook Pro extraction Created (UTC), 2025-09-04 00:22:53, and Boot UUID '
            'each held one value on all 3 rows. When a logical extraction holds the database '
            'under private/var and under System/Volumes/Data/private/var, a row both copies hold '
            'is reported once and Source File lists both.'
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/KextPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 5 rows",
        },
    },
    "macosKextPolicy": {
        "name": "Kext Policy",
        "description": "Rows of the kext_policy table in KextPolicy: team ID, bundle ID, "
                       "developer name, and the allowed and flags values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the kext_policy table of /private/var/db/SystemPolicyConfiguration/KextPolicy, '
            'with its -wal. Team ID, Bundle ID, Developer Name, Allowed and Flags are reported as '
            'stored, and what Allowed and Flags record is not established here. The table stores '
            'no time. On dleapp_macos_bigsur it holds 2 rows, both with Developer Name VMware, '
            'Inc., Team ID EG7KH642X6 and Allowed 1, whose bundle IDs are those of the two VMware '
            'kexts in Kext Load History; on the public MacBook Pro logical extraction (macOS 15.4 '
            'build 24E248, not a registered corpus key) it is empty. When a logical extraction '
            'holds the database under private/var and under System/Volumes/Data/private/var, a '
            'row both copies hold is reported once and Source File lists both.'
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/KextPolicy*',),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
        },
    },
    "macosGatekeeperAssessments": {
        "name": "Gatekeeper Assessments",
        "description": "Rows of the object table in the SystemPolicy database: path, operation "
                       "type, allow value, governing rule, hash, and creation, change and "
                       "expiry times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            'Reads the object table of the SystemPolicy database, at /private/var/db/SystemPolicy '
            'on dleapp_macos_bigsur and at /private/var/db/SystemPolicyConfiguration/SystemPolicy '
            'on the public MacBook Pro logical extraction (macOS 15.4 build 24E248, not a '
            "registered corpus key), joined to its authority table for Authority Label. Apple's "
            'syspolicy.sql, the file format of this database, describes the object table as '
            'previously determined outcomes for individual objects, each with an operation type, '
            'a canonical hash of the object, allow as 1 for allow and 0 for deny, the governing '
            'authority rule, and the path of the object at record creation time (Reference: '
            'Apple, Security, syspolicy.sql, '
            'https://github.com/apple-oss-distributions/Security/blob/db15acbe6a7f257a859ad9a3bb86097bfe0679d9/OSX/libsecurity_codesigning/lib/syspolicy.sql#L164-L185), '
            'and says its dates are in julian form, with 5000000 as the value for never '
            '(https://github.com/apple-oss-distributions/Security/blob/db15acbe6a7f257a859ad9a3bb86097bfe0679d9/OSX/libsecurity_codesigning/lib/syspolicy.sql#L29-L30). '
            'Created, Modified and Expires are ctime, mtime and expires read as Julian days, the '
            "fractional days since noon in Greenwich on November 24, 4714 B.C., which SQLite's "
            "JULIANDAY('now'), the default of ctime and mtime in that file, gives in UTC "
            "(Reference: SQLite, 'Date And Time Functions', "
            'https://www.sqlite.org/lang_datefunc.html); Expires is blank for 5000000. Type Name '
            'is the name policydb.h gives the type number '
            '(https://github.com/apple-oss-distributions/Security/blob/db15acbe6a7f257a859ad9a3bb86097bfe0679d9/OSX/libsecurity_codesigning/lib/policydb.h#L75-L78), '
            'and Hash is the stored hash in hexadecimal. On the public MacBook Pro extraction the '
            'table holds 2 rows, both with Type (as stored) 3 (kAuthorityOpenDoc), Allow 1 and '
            "Authority Label Notarized Developer ID, for two disk images in a user's Downloads "
            'folder; Created and Modified are identical on both rows, Expires falls 11.8 and 11.4 '
            'hours after Created, and Remarks is empty on both. The table is empty on '
            'dleapp_macos_bigsur. The authority table is not reported as its own artifact: on '
            'both public images its rules are labelled GKE, Apple System, Apple Installer, Mac '
            'App Store, Developer ID, Notarized Developer ID, Unnotarized Developer ID and No '
            'Matching Rule, with Testflight also on the public MacBook Pro extraction, and none '
            'names a user. The copy under System/Library/Templates/Data is not staged from '
            'dleapp_macos_bigsur, since the raw image reader does not read the compression it is '
            'stored with, as the run log records. When a logical extraction holds the database '
            'under private/var and under System/Volumes/Data/private/var, a row both copies hold '
            'is reported once and Source File lists both.'
        ),
        "paths": ('*/var/db/SystemPolicy', '*/var/db/SystemPolicy-*',
                  '*/var/db/SystemPolicyConfiguration/SystemPolicy',
                  '*/var/db/SystemPolicyConfiguration/SystemPolicy-*'),
        "output_types": ["standard"],
        "artifact_icon": "shield",
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
# The Julian day of 1970-01-01 00:00:00 UTC.
_JULIAN_UNIX_EPOCH = 2440587.5
# syspolicy.sql's canonical "never" expiration.
_NEVER = 5000000
# policydb.h's operation types.
_OPERATION = {0: 'kAuthorityInvalid', 1: 'kAuthorityExecute', 2: 'kAuthorityInstall',
              3: 'kAuthorityOpenDoc'}


def _blank(value):
    return '' if value is None else value


def _databases(context, name):
    """Staged copies of the database called name (not its sidecars or directories)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == name and not os.path.isdir(str(path))})


def _text_time(value):
    """A stored 'YYYY-MM-DD HH:MM:SS' text read as UTC, or the stored value when it is not
    in that form."""
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        except ValueError:
            return value
    return _blank(value)


def _julian_time(value):
    """A stored Julian day as a UTC datetime; blank for no value and for 5000000, the
    value syspolicy.sql uses for "never"."""
    if value is None or value == _NEVER:
        return ''
    try:
        return _UNIX_EPOCH + timedelta(seconds=(float(value) - _JULIAN_UNIX_EPOCH) * 86400)
    except (TypeError, ValueError, OverflowError):
        return value


def _hex(value):
    return value.hex() if isinstance(value, bytes) else _blank(value)


def _collect(context, name, table, query, build):
    """Rows built from table in every staged copy of the database called name; a row that
    more than one copy holds is reported once, with every copy listed."""
    records = []
    read = []
    for path in _databases(context, name):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, table):
            logfunc(f'{name}: no {table} table in {relative}')
            continue
        rows = get_sqlite_db_records(path, query)
        if rows:
            read.append(path)
        for row in rows:
            records.append((build(row), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_list, '\n'.join(read)


@artifact_processor
def macosKextLoadHistory(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Last Seen (UTC)', 'datetime'), 'Path',
                    'Bundle ID', 'Team ID', 'Boot UUID', 'Flags (as stored)', 'CDHash',
                    'Source File')

    def build(row):
        return (_text_time(row['created_at']), _text_time(row['last_seen']),
                _blank(row['path']), _blank(row['bundle_id']), _blank(row['team_id']),
                _blank(row['boot_uuid']), _blank(row['flags']), _blank(row['cdhash']))

    data_list, source = _collect(
        context, 'KextPolicy', 'kext_load_history_v3',
        'SELECT created_at, last_seen, path, bundle_id, team_id, boot_uuid, flags, cdhash '
        'FROM kext_load_history_v3 ORDER BY created_at, path', build)
    return data_headers, data_list, source


@artifact_processor
def macosKextPolicy(context):
    data_headers = ('Team ID', 'Bundle ID', 'Developer Name', 'Allowed (as stored)',
                    'Flags (as stored)', 'Source File')

    def build(row):
        return (_blank(row['team_id']), _blank(row['bundle_id']), _blank(row['developer_name']),
                _blank(row['allowed']), _blank(row['flags']))

    data_list, source = _collect(
        context, 'KextPolicy', 'kext_policy',
        'SELECT team_id, bundle_id, developer_name, allowed, flags FROM kext_policy '
        'ORDER BY team_id, bundle_id', build)
    return data_headers, data_list, source


@artifact_processor
def macosGatekeeperAssessments(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'),
                    ('Expires (UTC)', 'datetime'), 'Path', 'Type (as stored)', 'Type Name',
                    'Allow (as stored)', 'Authority ID', 'Authority Label', 'Hash', 'Remarks',
                    'Source File')

    def build(row):
        return (_julian_time(row['ctime']), _julian_time(row['mtime']),
                _julian_time(row['expires']), _blank(row['path']), _blank(row['type']),
                _OPERATION.get(row['type'], ''), _blank(row['allow']), _blank(row['authority']),
                _blank(row['label']), _hex(row['hash']), _blank(row['remarks']))

    data_list, source = _collect(
        context, 'SystemPolicy', 'object',
        'SELECT object.ctime, object.mtime, object.expires, object.path, object.type, '
        'object.allow, object.authority, authority.label, object.hash, object.remarks '
        'FROM object LEFT JOIN authority ON authority.id = object.authority '
        'ORDER BY object.ctime, object.id', build)
    return data_headers, data_list, source
