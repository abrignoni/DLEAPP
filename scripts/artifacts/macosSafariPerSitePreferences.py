__artifacts_v2__ = {
    "macosSafariPerSitePreferences": {
        "name": "Safari Per-Site Preferences",
        "description": "Per-website settings Safari stores in PerSitePreferences.db on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari",
        "notes": (
            "Reads the preference_values table of PerSitePreferences.db: domain, preference and preference_value "
            "as stored. The meaning of a preference_value number is not established and is not labelled. "
            "Timestamp (as stored) is the table's timestamp column, declared as TEXT; the Timestamp (as stored) "
            "column was empty on every tested row, so its format is not known and it is not converted. Value (as "
            "stored) held 0 on all 5 rows read across the tested images. The default_preferences table held no "
            "row on the tested images and is not read, and the sync_data and record_name columns newer versions "
            "add are not read. User is the folder after Users in the path, root under private/var/root, otherwise "
            "blank; it held one value on every row of each tested image, which each hold one user's Safari data. "
            "When a logical extraction holds the same file under Users/ and under System/Volumes/Data/Users/ or "
            "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run log counts "
            "it, and a row that copies with different bytes both hold is reported once with every file that held "
            "it in Source File. "
        ),
        "paths": ('*/Library/Safari/PerSitePreferences.db*',),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 1 row",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (preference_values holds no row)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 3 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 1 row",
        },
    }
}

import os

from scripts.ilapfuncs import artifact_processor, does_table_exist_in_db, get_sqlite_db_records
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_QUERY = 'SELECT timestamp, domain, preference, preference_value FROM preference_values ORDER BY id'


def _text(value):
    if value is None:
        return ''
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)'
    return value


@artifact_processor
def macosSafariPerSitePreferences(context):
    data_headers = ('Timestamp (as stored)', 'Domain', 'Preference', 'Value (as stored)', 'User',
                    'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'PerSitePreferences.db']
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label='Safari Per-Site Preferences')
    rows, read = [], []
    for path in paths:
        if not does_table_exist_in_db(path, 'preference_values'):
            continue
        relative = context.get_relative_path(path)
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(path, _QUERY):
            rows.append((_text(row['timestamp']), _text(row['domain']), _text(row['preference']),
                         _text(row['preference_value']), user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
