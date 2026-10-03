"""Cached URL responses in the Cache.db files apps keep under Library/Caches on macOS, for
DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosAppUrlCache": {
        "name": "App URL Cache",
        "description": "Cached URL responses in the Cache.db files apps keep under Library/Caches, "
                       "with the URL, the stored times, the user, where the body is stored, and "
                       "the stored request and response objects.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Web Cache (macOS)",
        "notes": "Reads each Cache.db under a Library/Caches folder, including ones nested below "
                 "an app's own cache folder, that has a cfurl_cache_response table, one row per "
                 "row of that table with its cfurl_cache_blob_data and cfurl_cache_receiver_data "
                 "rows joined by entry_ID; a Cache.db without the table is logged and not read. "
                 "Velociraptor's MacOS.Applications.Cache reads the same three tables in "
                 "/Users/*/Library/Caches/*/Cache.db with inner joins and labels the folder name "
                 "Application "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.Cache.yaml#L13-L14, "
                 "https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.Cache.yaml#L25-L32). "
                 "This artifact also reads caches under /Library/Caches, private/var/root and app "
                 "containers, and keeps a response row whose other rows are missing. Time Stamp "
                 "(UTC) is time_stamp, which the table defines with the default CURRENT_TIMESTAMP, "
                 "a value SQLite writes as the current UTC date and time in the form YYYY-MM-DD "
                 "HH:MM:SS (https://www.sqlite.org/lang_createtable.html#dfltval); a value not in "
                 "that form is left blank and counted in the run log. Response Object Time (UTC) "
                 "is the second element of the response object's Array read as seconds since "
                 "2001-01-01 UTC. It equalled Time Stamp to the second on 1,299 of 1,528 rows on "
                 "dleapp_macos_bigsur and 1,061 of 1,728 on the MacBook Pro extraction below, and "
                 "was earlier or later on the rest, so the two are not the same time. User is the "
                 "folder after Users in the path, root under private/var/root, and blank "
                 "elsewhere, and Cache Path is the folder holding the Cache.db. URL and Partition "
                 "are request_key and partition as stored. Response Object and Request Object are "
                 "response_object and request_object parsed as plists and shown as JSON with data "
                 "in hex, or in hex as stored when they do not parse; proto_props and user_info "
                 "are not reported. When isDataOnFS is 1, Data Stored In is fsCachedData/ followed "
                 "by the name receiver_data holds, and on dleapp_macos_bigsur all 476 such names "
                 "were files in the fsCachedData folder beside the Cache.db; those files are not "
                 "read here. Otherwise Data Stored In is Cache.db and Data Size (bytes) is the "
                 "length of receiver_data. On dleapp_macos_bigsur 44 caches gave 1,528 rows, from "
                 "2020-12-02 15:00:46 to 2021-02-19 19:53:28 UTC, and the Cache.db under "
                 "com.apple.parsecd/EngagedCompletions had no cfurl_cache_response table. On the "
                 "public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) "
                 "60 caches gave 1,728 rows, and 58 copies under System/Volumes/Data "
                 "byte-identical to another were read once and counted in the run log. The request "
                 "objects hold request headers: 967 on dleapp_macos_bigsur included a Cookie "
                 "header and 28 an Authorization header, and on the MacBook Pro extraction 280 and "
                 "492.",
        "paths": ('*/Library/Caches/*/Cache.db*',),
        "output_types": ["standard"],
        "artifact_icon": "world-www",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1528 rows",
        },
    },
}

import json
import os
import plistlib
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db, get_sqlite_db_records,
                               logfunc)
from scripts.macos_plists import canonical_relative, mac_absolute_utc, unique_sources, user_from_path

_QUERY = '''
    SELECT r.entry_ID, r.request_key, r.time_stamp, r.partition, b.response_object,
           b.request_object, d.isDataOnFS, d.receiver_data
    FROM cfurl_cache_response r
    LEFT JOIN cfurl_cache_blob_data b ON b.entry_ID = r.entry_ID
    LEFT JOIN cfurl_cache_receiver_data d ON d.entry_ID = r.entry_ID
    ORDER BY r.entry_ID
'''


def _json_default(value):
    return value.hex() if isinstance(value, (bytes, bytearray)) else str(value)


def decoded(blob):
    """(object, text): a stored plist blob parsed, and as JSON; (None, '') when empty."""
    if not blob:
        return None, ''
    try:
        value = plistlib.loads(bytes(blob))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return None, bytes(blob).hex() if isinstance(blob, (bytes, bytearray)) else str(blob)
    return value, json.dumps(value, default=_json_default, ensure_ascii=False, sort_keys=True)


def utc_text(value):
    """A 'YYYY-MM-DD HH:MM:SS' text as an aware UTC datetime, or ''."""
    try:
        return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def response_time(response):
    """The second element of a response object's Array read as seconds since 2001, or ''."""
    array = response.get('Array') if isinstance(response, dict) else None
    if isinstance(array, list) and len(array) > 1:
        return mac_absolute_utc(array[1])
    return ''


def data_location(on_file_system, data):
    """(where the body is stored, its size in bytes when it is in the database)."""
    if on_file_system == 1:
        name = data.decode('utf-8', 'replace') if isinstance(data, (bytes, bytearray)) else str(data or '')
        return f'fsCachedData/{name}', ''
    if isinstance(data, (bytes, bytearray)):
        return 'Cache.db', len(data)
    return ('Cache.db', '') if data is None else ('Cache.db', len(str(data)))


def cache_rows(records, user, cache_path):
    """The report rows for one Cache.db's records."""
    rows, unparsed = [], 0
    for record in records:
        response, response_text = decoded(record['response_object'])
        _request, request_text = decoded(record['request_object'])
        stamp = utc_text(record['time_stamp'])
        if record['time_stamp'] and not stamp:
            unparsed += 1
        stored_in, size = data_location(record['isDataOnFS'], record['receiver_data'])
        rows.append((stamp, response_time(response), user, cache_path, record['request_key'] or '',
                     record['partition'] or '', stored_in, size, response_text, request_text,
                     record['entry_ID']))
    return rows, unparsed


@artifact_processor
def macosAppUrlCache(context):
    data_headers = (('Time Stamp (UTC)', 'datetime'), ('Response Object Time (UTC)', 'datetime'),
                    'User', 'Cache Path', 'URL', 'Partition', 'Data Stored In',
                    'Data Size (bytes)', 'Response Object', 'Request Object', 'Entry ID')
    data_list, sources = [], []
    databases = [str(f) for f in context.get_files_found() if str(f).endswith('/Cache.db')
                 or str(f).endswith('\\Cache.db')]
    kept, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'),
                                    label='App URL Cache')
    for path in kept:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'cfurl_cache_response'):
            logfunc(f'App URL Cache: {relative} has no cfurl_cache_response table and is not read')
            continue
        records = get_sqlite_db_records(path, _QUERY)
        if not records:
            continue
        cache_path = os.path.dirname(canonical_relative(relative))
        rows, unparsed = cache_rows(records, user_from_path(relative), cache_path)
        if unparsed:
            logfunc(f'App URL Cache: {unparsed} time_stamp value(s) in {relative} not in the '
                    'YYYY-MM-DD HH:MM:SS form, left blank')
        data_list.extend(rows)
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
