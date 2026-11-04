"""Read the Local Storage and Service Worker LevelDB folders of Chromium browser profiles.

Used by scripts/artifacts/chromiumWebStorage.py. Sources, chromium
33f34ef179f55596f6c2fc8a55878b7ccf6276e4:

* Local Storage keeps one "META:<storage key>" record per storage key, a
  LocalStorageAreaWriteMetaData {last_modified, size_bytes}, and one
  "METAACCESS:<storage key>" record, a LocalStorageAreaAccessMetaData
  {last_accessed}, both times serialized by base::Time::ToInternalValue():
  components/services/storage/dom_storage/leveldb/local_storage_database.proto
  and local_storage_leveldb.cc. The values a site stores are
  "_<storage key>\\x00<key>" records (scripts/chromium/local_storage.py).
* A storage key is serialized as the origin, then "/^0" and the top-level site
  when it is partitioned, or other "^<n>" attributes:
  third_party/blink/common/storage_key/storage_key.cc, lines 31 to 100.
* The Service Worker database keeps one "REG:<storage key>\\x00<registration id>"
  record per registration, a ServiceWorkerRegistrationData message:
  components/services/storage/service_worker/service_worker_database.cc,
  lines 50 to 90, and service_worker_database.proto, lines 26 and 239 to 279.
"""

import hashlib
import os

from scripts.ccl import ccl_leveldb

CHROMIUM_COMMIT = '33f34ef179f55596f6c2fc8a55878b7ccf6276e4'

LOCAL_STORAGE = 'Local Storage/leveldb'
SERVICE_WORKER = 'Service Worker/Database'


class ProtoError(ValueError):
    """A value that does not decode as the message it is read as."""


def _varint(data, position):
    result = 0
    shift = 0
    while True:
        if position >= len(data):
            raise ProtoError('truncated varint')
        byte = data[position]
        position += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, position
        shift += 7
        if shift > 63:
            raise ProtoError('varint longer than ten bytes')


def proto_fields(data):
    """{field number: last value} of one encoded message: an int for a varint, bytes otherwise."""
    out = {}
    position = 0
    size = len(data)
    while position < size:
        key, position = _varint(data, position)
        number, wire_type = key >> 3, key & 7
        if number == 0:
            raise ProtoError('field number 0')
        if wire_type == 0:
            value, position = _varint(data, position)
        elif wire_type == 1:
            value, position = data[position:position + 8], position + 8
        elif wire_type == 2:
            length, position = _varint(data, position)
            value, position = data[position:position + length], position + length
        elif wire_type == 5:
            value, position = data[position:position + 4], position + 4
        else:
            raise ProtoError(f'unsupported wire type {wire_type}')
        if position > size:
            raise ProtoError('field runs past the end')
        out[number] = value
    return out


def signed64(value):
    """An int64 field, written as a 64-bit varint, as a signed number."""
    value &= (1 << 64) - 1
    return value - (1 << 64) if value >> 63 else value


def split_storage_key(serialized):
    """(origin, top-level site, other attributes) of a serialized StorageKey.

    An unpartitioned key is the origin alone. "<origin>/^0<site>" names the
    top-level site; any other "^<n>" attribute (a nonce, the ancestor chain bit,
    an opaque top-level site) is returned as stored in the third element.
    """
    origin, separator, attributes = serialized.partition('/^')
    if not separator:
        return serialized, '', ''
    attributes = '^' + attributes
    if attributes.startswith('^0') and '^' not in attributes[2:]:
        return origin, attributes[2:], ''
    return origin, '', attributes


def newest_versions(folder):
    """(newest {key: (seq, state, value)}, earlier {key: [(seq, value)] of live puts}, records read)."""
    newest = {}
    puts = {}
    records = 0
    database = ccl_leveldb.RawLevelDb(folder)
    try:
        for record in database.iterate_records_raw():
            records += 1
            key = bytes(record.user_key)
            value = bytes(record.value or b'')
            if record.state == ccl_leveldb.KeyState.Live:
                puts.setdefault(key, []).append((record.seq, value))
            held = newest.get(key)
            if held is None or record.seq > held[0]:
                newest[key] = (record.seq, record.state, value)
    finally:
        database.close()
    return newest, puts, records


def is_deleted(state):
    return state == ccl_leveldb.KeyState.Deleted


def _folder_digest(folder):
    digest = hashlib.sha256()
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        digest.update(name.encode('utf-8', 'surrogateescape') + b'\x00')
        with open(path, 'rb') as handle:
            while True:
                chunk = handle.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
        digest.update(b'\x00')
    return digest.hexdigest()


def profile_folders(context, store_name, label=''):
    """The located Store of each `store_name` folder (LOCAL_STORAGE, SERVICE_WORKER) a browser profile holds.

    `store_name` can also be a function of the folder's path inside the profile that
    returns True for the folders wanted.

    Grouped from the staged files the patterns matched, so a folder is read once
    however many of its files matched. Only folders inside a known browser user
    data folder are returned (browser_profiles.BROWSER_ROOTS); an Electron or
    WebView2 folder with the same layout is not. A folder whose copy under
    System/Volumes/Data or System/Volumes/Update/mnt1 holds the same files with
    the same bytes is returned once; copies that differ are both returned.
    """
    from scripts.chromium.browser_profiles import Store, locate
    from scripts.ilapfuncs import logfunc
    from scripts.macos_plists import canonical_relative
    folders = {}
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        folder = os.path.dirname(path)
        if folder in folders:
            continue
        relative = context.get_relative_path(folder)
        located = locate(canonical_relative(relative))
        if located is None:
            continue
        browser, profile, user, container, name = located
        if not (store_name(name) if callable(store_name) else name == store_name):
            continue
        folders[folder] = Store(folder, relative, browser, profile, user, container, name)
    kept, seen, skipped = [], set(), 0
    for folder in sorted(folders, key=lambda f: (len(folders[f].relative), folders[f].relative)):
        key = (canonical_relative(folders[folder].relative), _folder_digest(folder))
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        kept.append(folders[folder])
    if skipped and label:
        folder_label = getattr(store_name, 'folder_label', store_name)
        logfunc(f'{label}: {skipped} byte-identical {folder_label} folder copy(ies) under '
                f'System/Volumes/Data or System/Volumes/Update/mnt1 not read again')
    return sorted(kept, key=lambda store: store.relative)
