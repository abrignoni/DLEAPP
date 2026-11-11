__artifacts_v2__ = {
    "macosSafariFavicons": {
        "name": "Safari - Favicons (macOS)",
        "description": "Favicon cache entries (page URL, icon URL, dimensions and icon timestamp) from each user's "
                       "Library/Safari/Favicon Cache/favicons.db.",
        "author": "@abrignoni, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Ported from iLEAPP's Safari Browser - Favicons artifact (@abrignoni), which reads the "
                 "same tables in the iOS Favicons.db. Reads icon_info joined to page_url by uuid in each "
                 "Library/Safari/Favicon Cache/favicons.db, with its -wal, one row per page URL and icon "
                 "pair; an icon_info row with no page_url row is kept with a blank Page URL (none on the "
                 "tested images). User is the folder after Users in the path, root under "
                 "private/var/root, otherwise blank. Icon Timestamp is icon_info.timestamp read as "
                 "seconds since 2001-01-01 UTC, or as Unix seconds when the value is above 978307200, as "
                 "in the iLEAPP artifact; every tested value was below that and read from 2001. On the "
                 "tested images 50 of the 63 page URLs were also in the same user's Safari History.db, "
                 "and for 33 of those an icon timestamp was within an hour of a visit_time of the same "
                 "URL, which this comparison read as seconds since 2001-01-01, the reading DLEAPP's "
                 "Safari browsing artifact uses, and the other 17 were more than a day from every visit "
                 "of that URL; the other 13 page URLs were not in History.db. What sets the icon "
                 "timestamp is not established. When a logical extraction holds the same file under "
                 "Users/ and under System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a "
                 "byte-identical copy is not read again and the run log counts it. The rejected_resources "
                 "table is reported by the Safari Rejected Favicons artifact. The icon images are not read.",
        "paths": ('*/Library/Safari/Favicon Cache/favicons.db*',),
        "output_types": "standard",
        "artifact_icon": "photo",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 34 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 29 rows",
        },
    },
    "macosSafariRejectedFavicons": {
        "name": "Safari Rejected Favicons",
        "description": "Page and icon URL pairs in the rejected_resources table of Safari's favicon cache on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari",
        "notes": (
            "Reads the rejected_resources table of favicons.db: page_url and icon_url as stored. Timestamp is the "
            "table's timestamp column read as seconds since 2001-01-01 UTC, or as Unix seconds when the value is "
            "above 978307200, as in the Safari Favicons artifact; every tested value was below that. What makes "
            "Safari record a pair here, and what sets the timestamp, is not established. A row shows that "
            "Safari's favicon cache recorded the page URL. User is the folder after Users in the path, root under "
            "private/var/root, otherwise blank; it held one value on every row of each tested image, which each "
            "hold one user's Safari data. When a logical extraction holds the same file under Users/ and under "
            "System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read "
            "again and the run log counts it, and a row that copies with different bytes both hold is reported "
            "once with every file that held it in Source File. "
        ),
        "paths": ('*/Library/Safari/Favicon Cache/favicons.db*',),
        "output_types": "standard",
        "artifact_icon": "photo",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 5 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (rejected_resources holds no row)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 5 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 13 rows",
        },
    }
}

import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, does_table_exist_in_db, get_sqlite_db_records
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'Safari Favicons'
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
# Unix seconds for any date after 2001-01-01 are above this; Cocoa seconds stay below it until 2032.
_COCOA_LIMIT = 978307200

_QUERY = '''
SELECT icon_info.timestamp, page_url.url AS page, icon_info.url AS icon, icon_info.width, icon_info.height,
       icon_info.has_generated_representations
FROM icon_info LEFT JOIN page_url ON icon_info.uuid = page_url.uuid
ORDER BY icon_info.timestamp, page_url.url
'''


def _time(value):
    """Seconds since 2001-01-01, or Unix seconds when above 978307200; blank when absent."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return ''
    try:
        return (_UNIX_EPOCH if value > _COCOA_LIMIT else _MAC_EPOCH) + timedelta(seconds=value)
    except (OverflowError, ValueError):
        return ''


def _text(value):
    return '' if value is None else value


@artifact_processor
def macosSafariFavicons(context):
    data_headers = (('Icon Timestamp', 'datetime'), 'Page URL', 'Icon URL', 'Width', 'Height',
                    'Generated Representations (as stored)', 'User', 'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'favicons.db']
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label=_LABEL)
    rows, read = [], []
    for path in paths:
        if not (does_table_exist_in_db(path, 'icon_info') and does_table_exist_in_db(path, 'page_url')):
            continue
        relative = context.get_relative_path(path)
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(path, _QUERY):
            rows.append((_time(row['timestamp']), _text(row['page']), _text(row['icon']), _text(row['width']),
                         _text(row['height']), _text(row['has_generated_representations']), user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosSafariRejectedFavicons(context):
    data_headers = (('Timestamp', 'datetime'), 'Page URL', 'Icon URL', 'User', 'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'favicons.db']
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label='Safari Rejected Favicons')
    rows, read = [], []
    for path in paths:
        if not does_table_exist_in_db(path, 'rejected_resources'):
            continue
        relative = context.get_relative_path(path)
        read.append(path)
        user = user_from_path(relative)
        query = 'SELECT timestamp, page_url, icon_url FROM rejected_resources ORDER BY timestamp, page_url'
        for row in get_sqlite_db_records(path, query):
            rows.append((_time(row['timestamp']), _text(row['page_url']), _text(row['icon_url']), user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
