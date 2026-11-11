__artifacts_v2__ = {
    "macosWebKitLocalStorage": {
        "name": "WebKit Local Storage",
        "description": "Web local storage keys and values kept by Safari and by other macOS apps that show web "
                       "content with WebKit.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari",
        "notes": (
            "Reads the ItemTable of two generations of WebKit local storage. Current: localstorage.sqlite3 under "
            "an app's Library/WebKit folder, one database per origin, with a file named origin beside the "
            "LocalStorage folder. Origin and Top Origin are decoded from that file as WebKit writes it (top "
            "origin then client origin, each a protocol string, a host string and an optional port; WebKit "
            "source, WebCorePersistentCoders.cpp and StorageUtilities.cpp at commit ab66a42). Origin and Top "
            "Origin were identical on every row of the two tested images with this layout (macOS 15.4 and 26.2), "
            "so storage partitioned under a different top site has not been exercised. Older: "
            "Library/Safari/LocalStorage/<name>.localstorage, where Origin is the file name as stored with "
            ".localstorage removed and the Top Origin column was empty on every row (the two macOS 11.2.1 "
            "images). Value is the stored BLOB decoded as UTF-16 little endian, which is how WebKit writes it "
            "(SQLiteStorageArea.cpp, same commit); Value Size (bytes) is the BLOB length. A key shows that a page "
            "from the origin stored a value; the table has no timestamps. App Folder is the container folder or "
            "the folder under Library/WebKit, or Safari for the older layout; App Folder held one value on three of the four tested images with rows and two on mvs2026_macbookpro_macos15, where 102 of the 219 rows came from a "
            "third-party app's WebKit store. Roblox's WebKit store, when present, is also reported by the Roblox "
            "artifacts. IndexedDB, service worker and cache storage in the same folders are not read. User is the "
            "folder after Users in the path, root under private/var/root, otherwise blank; it held one value on "
            "every row of each tested image, which each hold one user's Safari data. When a logical extraction "
            "holds the same file under Users/ and under System/Volumes/Data/Users/ or "
            "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run log counts "
            "it, and a row that copies with different bytes both hold is reported once with every file that held "
            "it in Source File. "
        ),
        "paths": ('*/Library/WebKit/*/LocalStorage/localstorage.sqlite3*',
                  '*/Library/WebKit/*/origin',
                  '*/Library/Safari/LocalStorage/*.localstorage*'),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 149 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 116 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 219 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 649 rows",
        },
    }
}

import os
import struct

from scripts.ilapfuncs import artifact_processor, does_table_exist_in_db, get_sqlite_db_records
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'WebKit Local Storage'
_LEGACY_SUFFIX = '.localstorage'
_NEW_NAME = 'localstorage.sqlite3'
_NULL_STRING = 0xFFFFFFFF


class _Short(Exception):
    """The origin file ended before the value being read."""


def _take(data, offset, size):
    if offset + size > len(data):
        raise _Short
    return data[offset:offset + size], offset + size


def _string(data, offset):
    """One WTF persistence String: uint32 length, a one-byte 8-bit flag, then the characters."""
    raw, offset = _take(data, offset, 4)
    length = struct.unpack('<I', raw)[0]
    if length == _NULL_STRING:
        return '', offset
    flag, offset = _take(data, offset, 1)
    if flag[0]:
        raw, offset = _take(data, offset, length)
        return raw.decode('latin-1'), offset
    raw, offset = _take(data, offset, length * 2)
    return raw.decode('utf-16-le', 'replace'), offset


def _security_origin(data, offset):
    """protocol, host and optional port of one origin, as 'protocol://host[:port]'."""
    protocol, offset = _string(data, offset)
    host, offset = _string(data, offset)
    has_port, offset = _take(data, offset, 1)
    port = ''
    if has_port[0]:
        raw, offset = _take(data, offset, 2)
        port = f':{struct.unpack("<H", raw)[0]}'
    return (f'{protocol}://{host}{port}' if protocol or host else ''), offset


def read_origin_file(path):
    """(top origin, origin) from a WebKit 'origin' file, or ('', '') when it cannot be read."""
    try:
        with open(path, 'rb') as handle:
            data = handle.read(65536)
    except OSError:
        return '', ''
    try:
        top, offset = _security_origin(data, 0)
        client, _offset = _security_origin(data, offset)
    except _Short:
        return '', ''
    return top, client


def _value(blob):
    """A stored value as text. WebKit writes the string's UTF-16 code units into the BLOB."""
    if blob is None:
        return ''
    if isinstance(blob, str):
        return blob
    return bytes(blob).decode('utf-16-le', 'replace')


def _size(blob):
    if isinstance(blob, (bytes, bytearray)):
        return len(blob)
    return ''


def _app(relative):
    """The app that owns the store: the container folder, or the folder under Library/WebKit, or Safari."""
    parts = str(relative).replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part == 'Containers' and index + 1 < len(parts) - 1:
            return parts[index + 1]
    for index, part in enumerate(parts[:-2]):
        if part == 'Library' and parts[index + 1] == 'WebKit':
            return parts[index + 2]
        if part == 'Library' and parts[index + 1] == 'Safari':
            return 'Safari'
    return ''


@artifact_processor
def macosWebKitLocalStorage(context):
    data_headers = ('Origin', 'Top Origin', 'Key', 'Value', 'Value Size (bytes)', 'App Folder', 'User', 'Source File')
    found = [str(p) for p in context.get_files_found()]
    stores = [p for p in found if os.path.basename(p) == _NEW_NAME or os.path.basename(p).endswith(_LEGACY_SUFFIX)]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label=_LABEL)
    rows, read = [], []
    for path in paths:
        if not does_table_exist_in_db(path, 'ItemTable'):
            continue
        relative = context.get_relative_path(path)
        name = os.path.basename(path)
        if name == _NEW_NAME:
            # <top origin hash>/<origin hash>/LocalStorage/localstorage.sqlite3, with the origin file beside LocalStorage
            top, origin = read_origin_file(os.path.join(os.path.dirname(os.path.dirname(path)), 'origin'))
        else:
            top, origin = '', name[:-len(_LEGACY_SUFFIX)]
        read.append(path)
        user = user_from_path(relative)
        app = _app(relative)
        for row in get_sqlite_db_records(path, 'SELECT key, value FROM ItemTable ORDER BY rowid'):
            key = row['key']
            rows.append((origin, top, '' if key is None else key, _value(row['value']), _size(row['value']), app,
                         user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
