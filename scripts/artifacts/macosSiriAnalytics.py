"""events rows from a macOS SiriAnalytics.db database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSiriAnalytics": {
        "name": "Siri Analytics Events",
        "description": "Events in each user's SiriAnalytics.db under a Library/Assistant folder, one row per "
                       "events row: the creation time, the identifiers stored with the event, the stored event "
                       "type and status codes, and the JSON payload.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Siri (macOS)",
        "notes": "Reads SiriAnalytics.db in a Library/Assistant folder and reports one row per row of its events "
                 "table. Date Created (UTC) is the date_created column read as Unix seconds; it carried a value on "
                 "every row of every tested image, where the 2001 epoch would place the Big Sur rows in 2051 and "
                 "2052. Stream UID is the stream_uid column, a UUID-shaped string reported as stored; what it groups "
                 "is not established. Stream UID holds one value on every row of magnet2021_macos_bigsur and "
                 "mvs2026_macbookpro_macos15. Assistant ID is the assistant_id column and Record ID the record_id "
                 "column; the two Big Sur databases have neither column, so both are blank there, while on macOS 14 "
                 "and 15 assistant_id held one value per database and record_id a distinct value on every row. "
                 "Assistant ID is empty on every row of the two Big Sur images and holds one value on every row of "
                 "evidencelocker_macos14 and mvs2026_macbookpro_macos15; Record ID is empty on every row of the two "
                 "Big Sur images; User holds one value on every row of each tested image. Event Type is the type "
                 "column and Status the status column, integer codes reported as stored; the artifact does not map "
                 "either to names. Context Data is the context_data column, a payload stored as a blob and shown as "
                 "UTF-8 text, not parsed into columns; on every tested image context_data_type was 2 on the rows "
                 "with a payload and 0 on the rows without one, every type-2 payload parsed as JSON, and Context "
                 "Data is blank on the type-0 rows. The payloads are JSON objects whose top-level keys name, among "
                 "other things: the system build (systemBuild), network connection metrics and errors (connection "
                 "and error keys), device-configuration records (com.apple.ace.system.DeviceConfiguration keys), and "
                 "assistant sync records (com.apple.ace.sync keys with a sync reason, source list and plugin bundle "
                 "path). User is the folder after Users in the path, or root under private/var/root. The timestamp "
                 "column (an integer that is neither a Unix nor a 2001 epoch time; its unit and origin are not "
                 "established) and the delivery_stream column (0 on every tested row) are not reported. A row records "
                 "that an event was written to this database, not that the user spoke to Siri. Validated on four "
                 "images: dleapp_macos_bigsur (macOS 11) 96 rows from one database, one user, 2 December 2020 to 19 "
                 "February 2021, 27 distinct type codes, Context Data blank on 19; magnet2021_macos_bigsur (macOS "
                 "11) 310 rows, one user, 5 to 6 April 2021, blank on 52; evidencelocker_macos14 (macOS 14) 493 "
                 "rows, one user, 20 to 21 August 2024, blank on 69; mvs2026_macbookpro_macos15 (macOS 15) 63 rows, "
                 "one user, 24 to 25 December 2025, blank on 8. Status was 1 on most rows and 0 on a few on the "
                 "macOS 14 and 15 images and the Magnet image, and 0 on every row of dleapp_macos_bigsur. When a "
                 "logical extraction holds the same database at its own path and again under System/Volumes/Data or "
                 "System/Volumes/Update/mnt1 with identical bytes it is read once, and when the copies differ a row "
                 "both hold is reported once with both files in Source File; on magnet2021_macos_bigsur a "
                 "System/Volumes/Update/mnt1 copy and the Users copy differ, and 284 rows both hold name both files "
                 "in Source File.",
        "paths": ("*/Library/Assistant/SiriAnalytics.db*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 96 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 (Magnet 2021 CTF) | 310 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 493 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 63 rows",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'Siri Analytics Events'
# date_created, type, status and context_data exist on every macOS version seen; assistant_id and record_id
# were added on macOS 14, so they are selected as NULL where the column is absent.
_COLUMNS = ('date_created', 'assistant_id', 'stream_uid', 'record_id', 'type', 'status',
            'context_data_type', 'context_data')


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime; '' for 0 or anything not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds == 0:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _text(value):
    return '' if value is None else str(value)


def _context_text(blob):
    """The context_data payload as text; '' when absent."""
    if blob is None:
        return ''
    if isinstance(blob, (bytes, bytearray)):
        return bytes(blob).decode('utf-8', 'replace')
    return str(blob)


def _rows(path):
    columns = ', '.join(name if does_column_exist_in_db(path, 'events', name) else f'NULL AS {name}'
                        for name in _COLUMNS)
    query = f'SELECT {columns} FROM events ORDER BY date_created, rowid'
    for (date_created, assistant_id, stream_uid, record_id, event_type, status,
         context_data_type, context_data) in (get_sqlite_db_records(path, query) or []):
        yield (_unix_utc(date_created), _text(assistant_id), _text(stream_uid), _text(record_id),
               _text(event_type), _text(status), _text(context_data_type), _context_text(context_data))


@artifact_processor
def macosSiriAnalytics(context):
    data_headers = (('Date Created (UTC)', 'datetime'), 'Assistant ID', 'Stream UID', 'Record ID',
                    'Event Type (as stored)', 'Status (as stored)', 'Context Data Type (as stored)',
                    'Context Data (JSON)', 'User', 'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'SiriAnalytics.db']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'events'):
            logfunc(f'{_LABEL}: no events table read from {relative}')
            continue
        read.append(path)
        data_list.extend(row + (user_from_path(relative), relative) for row in _rows(path))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
