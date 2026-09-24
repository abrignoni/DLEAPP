"""Assets in macOS Photos libraries (Photos.sqlite), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosPhotosAssets": {
        "name": "Photos Library Assets",
        "description": "Assets in each Photos library database (Photos.sqlite): created, added, "
                       "modified and trashed times, file names, type, dimensions, location, "
                       "time zone and the stored trashed, hidden and favorite values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Photos (macOS)",
        "notes": "Reads each Photos library's database/Photos.sqlite, one row per ZASSET "
                 "row (ZGENERICASSET when a database has no ZASSET table; no tested image "
                 "had one), with its ZADDITIONALASSETATTRIBUTES row. Date Created (UTC), "
                 "Date Added (UTC), Modification Date (UTC) and Trashed Date (UTC) are "
                 "ZDATECREATED, ZADDEDDATE, ZMODIFICATIONDATE and ZTRASHEDDATE read as "
                 "seconds since 00:00:00 UTC on 1 January 2001, the reference date Apple "
                 "documents for NSDate; read that way the 116 assets on "
                 "dleapp_macos_bigsur were created between March 2020 and February 2021, "
                 "where the 1970 epoch would place them in 1989 and 1990. File Name, "
                 "Directory, Uniform Type Identifier, Width, Height, Duration and UUID are "
                 "ZFILENAME, ZDIRECTORY, ZUNIFORMTYPEIDENTIFIER, ZWIDTH, ZHEIGHT, "
                 "ZDURATION and ZUUID; Original File Name, Time Zone Name, EXIF Timestamp, "
                 "Original File Size, Imported By and Creator Bundle ID are "
                 "ZORIGINALFILENAME, ZTIMEZONENAME, ZEXIFTIMESTAMPSTRING, "
                 "ZORIGINALFILESIZE, ZIMPORTEDBY and ZCREATORBUNDLEID of the additional "
                 "attributes row; all as stored. Kind is ZKIND as stored: on "
                 "dleapp_macos_bigsur it was 1 on the 5 assets whose type identifier names "
                 "a movie format and 0 on the 111 whose type identifier names an image "
                 "format. Latitude and Longitude are ZLATITUDE and ZLONGITUDE, blank when "
                 "either is missing or the latitude is -180, a value outside the -90 to 90 "
                 "range a latitude can take; 111 of the 116 assets there store -180 for "
                 "both and 5 carry a location. Trashed State, Hidden and Favorite are "
                 "ZTRASHEDSTATE, ZHIDDEN and ZFAVORITE as stored; on dleapp_macos_bigsur 3 "
                 "assets have Trashed State 1 and a Trashed Date, and Hidden and Favorite "
                 "each held one value on all 116 rows. EXIF Timestamp has no value on any "
                 "row of dleapp_macos_bigsur. The public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key) holds 2 assets in a database "
                 "with no ZCREATORBUNDLEID column, so Creator Bundle ID is empty there. On "
                 "the MacBook Pro, Trashed Date has no value on any row and Kind held one "
                 "value on all rows. Its Users/ and System/Volumes/Data/Users/ copies "
                 "differ and both are read, so each asset appears twice, identical in "
                 "every column but Source File. The original and derivative files in the "
                 "library are not read. All rows on each image come from one user, so User "
                 "holds one value there. When a logical extraction holds the same file "
                 "under Users/ and under System/Volumes/Data/Users/, a byte-identical "
                 "second copy is read once and counted in the run log. Reference: Apple, "
                 "'NSDate', https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 116 rows",
                       },
        "paths": ('*.photoslibrary/database/Photos.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava", "kml"],
        "artifact_icon": "image",
    }
}

import os

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources, user_from_path

_LABEL = 'Photos Library Assets'
_ASSET_COLUMNS = ('ZDATECREATED', 'ZADDEDDATE', 'ZMODIFICATIONDATE', 'ZTRASHEDDATE', 'ZFILENAME',
                  'ZDIRECTORY', 'ZUNIFORMTYPEIDENTIFIER', 'ZKIND', 'ZWIDTH', 'ZHEIGHT', 'ZDURATION',
                  'ZLATITUDE', 'ZLONGITUDE', 'ZTRASHEDSTATE', 'ZHIDDEN', 'ZFAVORITE', 'ZUUID',
                  'ZADDITIONALATTRIBUTES')
_EXTRA_COLUMNS = ('Z_PK', 'ZORIGINALFILENAME', 'ZTIMEZONENAME', 'ZEXIFTIMESTAMPSTRING',
                  'ZORIGINALFILESIZE', 'ZIMPORTEDBY', 'ZCREATORBUNDLEID')


def _text(value):
    return '' if value is None else str(value)


def _select(path, table, names):
    columns = ', '.join(name if does_column_exist_in_db(path, table, name) else f'NULL AS {name}'
                        for name in names)
    return get_sqlite_db_records(path, f'SELECT {columns} FROM {table}') or []


def _location(latitude, longitude):
    """The stored pair as text; blank when the latitude is -180, a value no latitude can take."""
    if latitude is None or longitude is None or latitude == -180:
        return '', ''
    return _text(latitude), _text(longitude)


def _rows(path, table):
    extras = {}
    if does_table_exist_in_db(path, 'ZADDITIONALASSETATTRIBUTES'):
        extras = {row[0]: row[1:] for row in _select(path, 'ZADDITIONALASSETATTRIBUTES', _EXTRA_COLUMNS)}
    records = sorted(_select(path, table, _ASSET_COLUMNS),
                     key=lambda row: (row[0] is None, row[0] if isinstance(row[0], (int, float)) else 0))
    for (created, added, modified, trashed, name, directory, uti, kind, width, height, duration,
         latitude, longitude, trashed_state, hidden, favorite, uuid, extra_id) in records:
        original, zone, exif_time, size, imported_by, creator = extras.get(extra_id, (None,) * 6)
        lat, lon = _location(latitude, longitude)
        yield (mac_absolute_utc(created), mac_absolute_utc(added), mac_absolute_utc(modified),
               mac_absolute_utc(trashed), _text(name), _text(original), _text(directory),
               _text(uti), _text(kind), _text(width), _text(height), _text(duration), lat, lon,
               _text(zone), _text(exif_time), _text(size), _text(trashed_state), _text(hidden),
               _text(favorite), _text(imported_by), _text(creator), _text(uuid))


@artifact_processor
def macosPhotosAssets(context):
    data_headers = (('Date Created (UTC)', 'datetime'), ('Date Added (UTC)', 'datetime'),
                    ('Modification Date (UTC)', 'datetime'), ('Trashed Date (UTC)', 'datetime'),
                    'File Name', 'Original File Name', 'Directory', 'Uniform Type Identifier',
                    'Kind (as stored)', 'Width', 'Height', 'Duration (seconds, as stored)',
                    'Latitude', 'Longitude', 'Time Zone Name (as stored)',
                    'EXIF Timestamp (as stored)', 'Original File Size (bytes, as stored)',
                    'Trashed State (as stored)', 'Hidden (as stored)', 'Favorite (as stored)',
                    'Imported By (as stored)', 'Creator Bundle ID', 'UUID', 'User', 'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'Photos.sqlite']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        table = next((t for t in ('ZASSET', 'ZGENERICASSET') if does_table_exist_in_db(path, t)), None)
        if table is None:
            logfunc(f'{_LABEL}: no ZASSET or ZGENERICASSET table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in _rows(path, table)]
        if not found:
            logfunc(f'{_LABEL}: no assets in {relative}')
        data_list.extend(found)
    return data_headers, data_list, '\n'.join(read)
