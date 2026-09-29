"""Stores an LG webOS TV keeps on its own volumes: downloads, system preferences, web app
Local Storage and installed apps, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "lgWebosDownloadHistory": {
        "name": "LG webOS Download History",
        "description": "Downloads recorded in an LG webOS TV's downloadhistory.db, with their source URL and "
                       "destination, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads var/luna/data/downloadhistory.db, table DownloadHistory, one row per ticket in ticket "
                 "order. Ticket, Owner, Interface and State are the columns as stored; the other columns come "
                 "from the JSON in the history column, reported as stored: url, destPath and destFile, "
                 "mimetype, amountReceived, amountTotal, httpStatus, completionStatusCode, and errorCode with "
                 "errorText where present. A history value that is not a JSON object leaves those columns "
                 "blank. Amount Received equalled Amount Total on every row of the private sample. The table "
                 "records no time. Owner is stored as the name of a service; what each download was for is "
                 "not established. The file sits on the volume an "
                 "LG webOS TV mounts at /mnt/lg/cmn_data (field mapped from a private sample).",
        "sample_data": {},
        "paths": ('*/var/luna/data/downloadhistory.db*',),
        "output_types": "standard",
    },
    "lgWebosSystemPreferences": {
        "name": "LG webOS System Preferences",
        "description": "Key and value pairs in an LG webOS TV's system preferences database, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads var/luna/preferences/systemprefs.db, table Preferences, one row per key in key order, "
                 "with the value as stored. The keys include the time zone, locale, region and time settings; "
                 "what each key controls is not established beyond its name. The file sits on the volume an "
                 "LG webOS TV mounts at /mnt/lg/cmn_data (field mapped from a private sample).",
        "sample_data": {},
        "paths": ('*/var/luna/preferences/systemprefs.db*',),
        "output_types": "standard",
    },
    "lgWebosLocalStorage": {
        "name": "LG webOS Web App Local Storage",
        "description": "Local Storage keys and values an LG webOS TV's web apps and browser kept, one row per "
                       "key.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads the .localstorage files in the Local Storage folders under var/lib/wam and under "
                 "webbrowser/chrome, the browser profile the Chromium artifacts read; each is an SQLite file "
                 "with table ItemTable. Origin is the file name as stored, with the trailing '.localstorage' "
                 "removed. Chromium of that era names the file after the origin's identifier, "
                 "<scheme>_<host>_<port> with a default port written 0 (DOMStorageArea::"
                 "DatabaseFileNameFromOrigin, "
                 "https://github.com/chromium/chromium/blob/4ec79b7f2379a60cdc15599e93255c0fa417f1ed/content/browser/dom_storage/dom_storage_area.cc#L78-L84,"
                 " and GetIdentifierFromOrigin, "
                 "https://github.com/chromium/chromium/blob/4ec79b7f2379a60cdc15599e93255c0fa417f1ed/storage/common/database/database_identifier.cc#L44-L57);"
                 " the files under var/lib/wam in the private sample were named file_<app id>_0, where a "
                 "stock Chromium file: origin has no host. Key is the key as stored. Chromium of that era writes a value as the "
                 "bytes of its UTF-16 string (DOMStorageDatabase::CommitChanges, Chromium 49.0.2623.112, "
                 "https://github.com/chromium/chromium/blob/4ec79b7f2379a60cdc15599e93255c0fa417f1ed/content/browser/dom_storage/dom_storage_database.cc#L106-L110),"
                 " so Value is those bytes decoded as UTF-16LE; Value Encoding held UTF-16LE on every row of "
                 "the private sample this was field mapped from. A value that does not is reported as hexadecimal with "
                 "Value Encoding 'hex'. Local Storage in Chromium's later LevelDB form is not read here. What "
                 "each key means is not established beyond its name.",
        "sample_data": {},
        "paths": ('*/var/lib/wam/*/Local Storage/*.localstorage*', '*/webbrowser/chrome/*/Local Storage/*.localstorage*'),
        "output_types": "standard",
    },
    "lgWebosInstalledApps": {
        "name": "LG webOS Installed Apps",
        "description": "Apps whose appinfo.json an LG webOS TV holds in its applications folders, with id, "
                       "title, version and vendor as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads the appinfo.json directly inside each folder of usr/palm/applications under cryptofs/apps "
                 "and system/apps, one row per app; "
                 "the appinfo.json files deeper in an app's own folders (such as its resources) are not "
                 "read. App ID, Title, Version, Vendor and Type are the file's id, title, version, vendor and "
                 "type as stored, and Area is cryptofs/apps or system/apps, the folders the private sample this "
                 "was field mapped from keeps them in on the volume it mounts at /media. The appinfo.json "
                 "files in the firmware's own usr/palm/applications are not reported, nor are copies of this layout inside any other usr folder (the private sample's firmware "
                 "carries some as test data). Whether an app was "
                 "installed by a person or came with the TV is not established from the file. A file that "
                 "does not read as a JSON object is counted in the run log.",
        "sample_data": {},
        "paths": ('*/cryptofs/apps/usr/palm/applications/*/appinfo.json',
                  '*/system/apps/usr/palm/applications/*/appinfo.json'),
        "output_types": "standard",
    },
}

import json
import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, get_sqlite_db_records, logfunc

HISTORY_FIELDS = ('url', 'destPath', 'destFile', 'mimetype', 'amountReceived', 'amountTotal', 'httpStatus',
                  'completionStatusCode', 'errorCode', 'errorText')


def _db_files(context, name):
    """The staged files named `name`, sidecars excluded, in path order."""
    return sorted(str(p) for p in context.get_files_found()
                  if os.path.basename(str(p)) == name and not os.path.isdir(p))


def history_fields(history):
    """The history JSON's reported fields, in HISTORY_FIELDS order, blank when it is not an object."""
    try:
        data = json.loads(history) if history else None
    except (TypeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return ('',) * len(HISTORY_FIELDS)
    return tuple('' if data.get(k) is None else data.get(k) if isinstance(data.get(k), (str, int, float))
                 else json.dumps(data.get(k)) for k in HISTORY_FIELDS)


@artifact_processor
def lgWebosDownloadHistory(context):
    data_headers = ('Ticket', 'Owner', 'Interface', 'State', 'URL', 'Destination Path', 'Destination File',
                    'MIME Type', 'Amount Received', 'Amount Total', 'HTTP Status', 'Completion Status Code',
                    'Error Code', 'Error Text')
    data_list, read = [], []
    for path in _db_files(context, 'downloadhistory.db'):
        rows = get_sqlite_db_records(path, 'SELECT ticket, owner, interface, state, history FROM DownloadHistory '
                                           'ORDER BY ticket')
        if not rows:
            continue
        for ticket, owner, interface, state, history in rows:
            data_list.append((ticket, owner, interface, state) + history_fields(history))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def lgWebosSystemPreferences(context):
    data_headers = ('Key', 'Value')
    data_list, read = [], []
    for path in _db_files(context, 'systemprefs.db'):
        rows = get_sqlite_db_records(path, 'SELECT key, value FROM Preferences ORDER BY key')
        if not rows:
            continue
        data_list.extend((key, value) for key, value in rows)
        read.append(path)
    return data_headers, data_list, '\n'.join(read)


def decode_value(value):
    """(text, encoding) for a Local Storage value: UTF-16LE text, or hexadecimal when it is not."""
    if isinstance(value, str):
        return value, 'text'
    data = bytes(value or b'')
    try:
        return data.decode('utf-16-le'), 'UTF-16LE'
    except UnicodeDecodeError:
        return data.hex(), 'hex'


@artifact_processor
def lgWebosLocalStorage(context):
    data_headers = ('Origin', 'Key', 'Value', 'Value Encoding', 'Source File')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        name = os.path.basename(path)
        if not name.endswith('.localstorage'):
            continue
        rows = get_sqlite_db_records(path, 'SELECT key, value FROM ItemTable')
        if not rows:
            continue
        origin = name[:-len('.localstorage')]
        relative = context.get_relative_path(path)
        for key, value in rows:
            text, encoding = decode_value(value)
            if encoding == 'hex':
                counts['values that are not UTF-16LE, reported as hex'] += 1
            data_list.append((origin, key, text, encoding, relative))
        read.append(path)
    if counts:
        logfunc('LG webOS Web App Local Storage: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def lgWebosInstalledApps(context):
    data_headers = ('App ID', 'Title', 'Version', 'Vendor', 'Type', 'Area')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        parts = context.get_relative_path(path).replace('\\', '/').split('/')
        area_at = len(parts) - 7
        if area_at < 0 or parts[-1] != 'appinfo.json' or parts[area_at + 2:area_at + 5] != ['usr', 'palm',
                                                                                         'applications']:
            continue
        if 'usr' in parts[:area_at]:
            counts['appinfo.json files inside a usr folder (firmware copies such as test data), not reported'] += 1
            continue
        try:
            with open(path, 'rb') as handle:
                info = json.loads(handle.read().decode('utf-8', 'replace'))
        except (OSError, ValueError):
            info = None
        if not isinstance(info, dict):
            counts['appinfo.json files that are not a JSON object'] += 1
            continue
        data_list.append(tuple('' if info.get(k) is None else str(info.get(k))
                               for k in ('id', 'title', 'version', 'vendor', 'type')) + ('/'.join(parts[area_at:area_at + 2]),))
        read.append(path)
    if counts:
        logfunc('LG webOS Installed Apps: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
