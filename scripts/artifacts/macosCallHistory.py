"""Calls recorded in the macOS CallHistory database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosCallHistory": {
        "name": "Call History",
        "description": "Call records in each user's CallHistoryDB stores "
                       "(CallHistory.storedata and CallHistoryTemp.storedata): start time, "
                       "duration, address, service provider and the stored call type, "
                       "originated and answered values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Call History (macOS)",
        "notes": "Reads ZCALLRECORD in each user's CallHistory.storedata and "
                 "CallHistoryTemp.storedata under ~/Library/Application "
                 "Support/CallHistoryDB, one row per record. Call Start (UTC) is ZDATE "
                 "read as seconds since 00:00:00 UTC on 1 January 2001, the reference date "
                 "Apple documents for NSDate; on dleapp_macos_bigsur that places the 25 "
                 "calls between 18 December 2020 and 19 February 2021, where the 1970 "
                 "epoch would place them in 1989 and 1990. Call End (UTC) is Call Start "
                 "plus ZDURATION and is blank when the stored duration is 0, as it was on "
                 "14 of the 25 calls. Duration (seconds) is ZDURATION rounded to three "
                 "decimal places. Address, Name, Service Provider, ISO Country Code, "
                 "Location and Unique ID are ZADDRESS, ZNAME, ZSERVICE_PROVIDER, "
                 "ZISO_COUNTRY_CODE, ZLOCATION and ZUNIQUE_ID as stored. Call Type, "
                 "Originated, Answered, Read and Disconnected Cause are ZCALLTYPE, "
                 "ZORIGINATED, ZANSWERED, ZREAD and ZDISCONNECTED_CAUSE as stored, with 1 "
                 "and 0 shown as Yes and No for the three flags; their meanings are not "
                 "established here. On dleapp_macos_bigsur every com.apple.Telephony call "
                 "stored type 1 and the com.apple.FaceTime calls stored 8 or 16, the 7 "
                 "calls with Originated Yes all stored Answered No, and Read held one "
                 "value on all 25 rows. Name, Location and Disconnected Cause have no "
                 "value on any of the 25 rows there, and ISO Country Code held one value "
                 "on all 25 rows. The public MacBook Pro logical extraction (macOS 15.4, "
                 "not a registered corpus key) holds a CallHistory.storedata with no call "
                 "records. All rows on dleapp_macos_bigsur come from one user, so User "
                 "holds one value there. When a logical extraction holds the same file "
                 "under Users/ and under System/Volumes/Data/Users/, a second copy whose "
                 "database and -wal file are both byte-identical to the first is not read again, "
                 "and is counted in the run log. Reference: Apple, "
                 "'NSDate', https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 25 rows",
                       },
        "paths": ('*/Library/Application Support/CallHistoryDB/CallHistory*.storedata*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "phone-call",
    },
}

from datetime import timedelta

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources, user_from_path

_COLUMNS = ('ZDATE', 'ZDURATION', 'ZADDRESS', 'ZNAME', 'ZSERVICE_PROVIDER', 'ZCALLTYPE',
            'ZORIGINATED', 'ZANSWERED', 'ZREAD', 'ZDISCONNECTED_CAUSE', 'ZISO_COUNTRY_CODE',
            'ZLOCATION', 'ZUNIQUE_ID')


def _yes_no(value):
    return {1: 'Yes', 0: 'No'}.get(value, '' if value is None else str(value))


def _text(value):
    return '' if value is None else str(value)


@artifact_processor
def macosCallHistory(context):
    data_headers = (('Call Start (UTC)', 'datetime'), ('Call End (UTC)', 'datetime'),
                    'Duration (seconds)', 'Address', 'Name', 'Service Provider',
                    'Call Type (as stored)', 'Originated (as stored)', 'Answered (as stored)',
                    'Read (as stored)', 'Disconnected Cause (as stored)', 'ISO Country Code',
                    'Location', 'Unique ID', 'User', 'Source File')
    data_list = []
    read = []
    stores = [p for p in context.get_files_found() if str(p).endswith('.storedata')]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label='Call History')
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ZCALLRECORD'):
            logfunc(f'Call History: no ZCALLRECORD table read from {relative}')
            continue
        read.append(path)
        columns = [c if does_column_exist_in_db(path, 'ZCALLRECORD', c) else f'NULL AS {c}'
                   for c in _COLUMNS]
        records = get_sqlite_db_records(path, f'SELECT {", ".join(columns)} FROM ZCALLRECORD ORDER BY ZDATE')
        if not records:
            logfunc(f'Call History: no call records in {relative}')
            continue
        for row in records:
            start = mac_absolute_utc(row[0])
            duration = row[1] if isinstance(row[1], (int, float)) else None
            end = start + timedelta(seconds=duration) if start and duration else ''
            data_list.append((start, end, '' if duration is None else round(duration, 3),
                              _text(row[2]), _text(row[3]), _text(row[4]), _text(row[5]),
                              _yes_no(row[6]), _yes_no(row[7]), _yes_no(row[8]), _text(row[9]),
                              _text(row[10]), _text(row[11]), _text(row[12]),
                              user_from_path(relative), relative))
    return data_headers, data_list, '\n'.join(read)
