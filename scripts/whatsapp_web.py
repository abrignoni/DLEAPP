"""Shared readers for WhatsApp Web's browser storage. Author: @AlexisBrignoni, Claude.

WhatsApp Web keeps its data in the IndexedDB and localStorage of the https://web.whatsapp.com
origin. A Chromium browser (Chrome, Edge, Brave, Opera, Vivaldi, or a WebView2 host) holds the
IndexedDB in ``IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb`` and localStorage in the
profile's ``Local Storage/leveldb``; Firefox holds both under
``storage/default/https+++web.whatsapp.com`` (``idb/*.sqlite`` and ``ls/data.sqlite``).

This module finds each browser profile that holds the origin, reads its object stores into
plain Python values, and reads the origin's localStorage. Each profile is read on its own and
never merged with another. What the stores mean is left to the artifacts, which cite
WhatsApp Web's own code for it.
"""

import base64
import glob
import hashlib
import os
import sqlite3
import struct
import urllib.parse

from scripts.ccl import ccl_chromium_indexeddb
from scripts.chromium.local_storage import read_records
from scripts.chromium.simple_cache import read_entry
from scripts.firefox import local_storage_value, snappy_raw_uncompress
from scripts.firefox_indexeddb import NotDecoded, clone_value
from scripts.ilapfuncs import logfunc, open_sqlite_db_readonly
from scripts.macos_plists import canonical_relative

ORIGIN = 'https://web.whatsapp.com'
CHROMIUM_IDB = 'https_web.whatsapp.com_0.indexeddb.leveldb'
FIREFOX_ORIGIN = 'https+++web.whatsapp.com'

# The databases and object stores the artifacts read.
STORES = {
    'model-storage': ('message', 'contact', 'chat', 'group-metadata', 'participant',
                      'reactions', 'blocklist'),
}

_CACHE = {}


class Profile:
    """One browser profile's WhatsApp Web storage."""

    def __init__(self, kind, root, profile_dir):
        self.kind = kind                # 'Chromium' or 'Firefox'
        self.root = root                # the IndexedDB folder (Chromium) or origin folder (Firefox)
        self.profile_dir = profile_dir  # the browser profile folder
        self.stores = {}                # (database, store) -> list of record values
        self.local_storage = {}         # key -> text value
        self.sources = []               # files read, for the located-at list
        self.skipped = 0                # records whose value could not be read
        self.media = None               # filled by media()
        self.media_missing = 0          # cached media entries whose body could not be read


def _plain_chromium(value):
    """A CCL-deserialised value with JavaScript undefined dropped from objects."""
    if type(value).__name__ == '_Undefined':
        return None
    if isinstance(value, dict):
        return {k: _plain_chromium(v) for k, v in value.items()
                if type(v).__name__ != '_Undefined'}
    if isinstance(value, (list, tuple)):
        return [_plain_chromium(v) for v in value]
    return value


def _plain_firefox(value):
    """A firefox_indexeddb clone value with its $-markers turned back into Python values."""
    if isinstance(value, dict):
        if '$typedarray' in value or '$dataview' in value:
            return bytes.fromhex(value.get('hex', value.get('$dataview', '')))
        if '$arraybuffer' in value:
            return bytes.fromhex(value['$arraybuffer'])
        if '$undefined' in value or '$backref' in value:
            return None
        return {k: _plain_firefox(v) for k, v in value.items()
                if not (isinstance(v, dict) and '$undefined' in v)}
    if isinstance(value, list):
        return [_plain_firefox(v) for v in value]
    return value


def _find_profiles(files_found):
    """Profiles keyed by their storage root, from the matched file paths."""
    found = {}
    for path in files_found:
        path = str(path)
        parts = path.replace('\\', '/').split('/')
        if CHROMIUM_IDB in parts:
            index = parts.index(CHROMIUM_IDB)
            sep = '\\' if '\\' in path and '/' not in path else '/'
            root = path[:len(sep.join(parts[:index + 1]))]
            # .../<profile>/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb
            profile_dir = os.path.dirname(os.path.dirname(root))
            found.setdefault(('Chromium', os.path.realpath(root)), Profile('Chromium', root, profile_dir))
        elif FIREFOX_ORIGIN in parts:
            index = parts.index(FIREFOX_ORIGIN)
            root = path[:len('/'.join(parts[:index + 1]))]
            # .../<profile>/storage/default/https+++web.whatsapp.com
            profile_dir = os.path.dirname(os.path.dirname(os.path.dirname(root)))
            found.setdefault(('Firefox', os.path.realpath(root)), Profile('Firefox', root, profile_dir))
    return [found[k] for k in sorted(found)]


def _read_chromium(profile):
    blob = profile.root[:-len('.leveldb')] + '.blob'
    wrapper = ccl_chromium_indexeddb.WrappedIndexDB(profile.root, blob if os.path.isdir(blob) else None)

    def bad(_key, _value):
        profile.skipped += 1

    for info in wrapper.database_ids:
        db = wrapper[info.dbid_no]
        wanted = STORES.get(db.name)
        if not wanted:
            continue
        for name in wanted:
            if name not in db.object_store_names:
                continue
            latest = {}
            for record in db[name].iterate_records(bad_deserializer_data_handler=bad):
                if not record.is_live or not isinstance(record.value, dict):
                    continue
                key = record.key.raw_key
                if key not in latest or record.ldb_seq_no > latest[key][0]:
                    latest[key] = (record.ldb_seq_no, record.value)
            profile.stores[(db.name, name)] = [_plain_chromium(v) for _, v in latest.values()]
    profile.sources.append(profile.root)

    ls_dir = os.path.join(profile.profile_dir, 'Local Storage', 'leveldb')
    if os.path.isdir(ls_dir):
        newest = {}
        for record in read_records(ls_dir):
            if record.origin != ORIGIN or not record.is_live:
                continue
            if record.key not in newest or record.sequence > newest[record.key][0]:
                newest[record.key] = (record.sequence, record.value)
        profile.local_storage = {k: v for k, (_, v) in newest.items()}
        profile.sources.append(ls_dir)


def _read_firefox(profile):
    for path in sorted(glob.glob(os.path.join(glob.escape(profile.root), 'idb', '*.sqlite'))):
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            row = db.execute('SELECT name FROM database LIMIT 1').fetchone()
            wanted = STORES.get(row[0] if row else None)
            if not wanted:
                continue
            ids = dict(db.execute('SELECT name, id FROM object_store').fetchall())
            for name in wanted:
                if name not in ids:
                    continue
                values = []
                for (data,) in db.execute('SELECT data FROM object_data WHERE object_store_id = ?',
                                          (ids[name],)):
                    try:
                        if not isinstance(data, (bytes, bytearray, memoryview)):
                            raise NotDecoded('stored in a file')
                        value, _trailing = clone_value(snappy_raw_uncompress(data))
                    except (NotDecoded, ValueError, TypeError, struct.error, UnicodeDecodeError):
                        profile.skipped += 1
                        continue
                    value = _plain_firefox(value)
                    if isinstance(value, dict):
                        values.append(value)
                profile.stores[(row[0], name)] = values
            profile.sources.append(path)
        except sqlite3.Error as exc:
            logfunc(f'WhatsApp Web: could not read {path}: {exc}')
        finally:
            db.close()

    ls_path = os.path.join(profile.root, 'ls', 'data.sqlite')
    if os.path.isfile(ls_path):
        db = open_sqlite_db_readonly(ls_path)
        if db is not None:
            try:
                for key, value, conversion, compression in db.execute(
                        'SELECT key, value, conversion_type, compression_type FROM data'):
                    try:
                        profile.local_storage[key] = local_storage_value(value, conversion, compression)
                    except (ValueError, TypeError, UnicodeDecodeError):
                        continue
                profile.sources.append(ls_path)
            except sqlite3.Error as exc:
                logfunc(f'WhatsApp Web: could not read {ls_path}: {exc}')
            finally:
                db.close()


def _tree_digest(folder):
    """SHA-256 over a folder's file names and bytes, in sorted order."""
    digest = hashlib.sha256()
    for parent, dirs, names in os.walk(folder):
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(parent, name)
            digest.update(os.path.relpath(path, folder).encode('utf-8', 'surrogateescape') + b'|')
            with open(path, 'rb') as handle:
                for block in iter(lambda h=handle: h.read(1 << 20), b''):
                    digest.update(block)
            digest.update(b'|')
    return digest.hexdigest()


def _one_per_view(context, found):
    """Profiles less byte-identical copies of one profile under two macOS volume views.

    A logical extraction of a Mac can hold the same folder under Users/ and under
    System/Volumes/Data/Users/ (see macos_plists.canonical_relative). A profile whose path
    differs from one already kept only by those folder runs, and whose storage folder holds
    identical files, is not read again; copies that differ are all kept.
    """
    kept, seen, skipped = [], set(), 0
    for profile in sorted(found, key=lambda p: (len(p.root), p.root)):
        key = (profile.kind, canonical_relative(context.get_relative_path(profile.root)),
               _tree_digest(profile.root))
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        kept.append(profile)
    if skipped:
        logfunc(f'WhatsApp Web: {skipped} byte-identical profile copy(ies) under System/Volumes/Data '
                'or System/Volumes/Update/mnt1 not read again')
    return kept


def profiles(context):
    """Every WhatsApp Web profile among the matched files, read once per run."""
    found = _find_profiles(context.get_files_found())
    key = tuple((p.kind, os.path.realpath(p.root)) for p in found)
    if key in _CACHE:
        return _CACHE[key]
    found = _one_per_view(context, found)
    for profile in found:
        try:
            if profile.kind == 'Chromium':
                _read_chromium(profile)
            else:
                _read_firefox(profile)
        except (OSError, ValueError, KeyError) as exc:
            logfunc(f'WhatsApp Web: could not read {profile.root}: {exc}')
        if profile.skipped:
            logfunc(f'WhatsApp Web: {profile.skipped} record(s) in {profile.root} could not be read')
    _CACHE[key] = found
    return found


MEDIA_PREFIX = 'https://_media_cache_v2_.whatsapp.com/lru-media-array-buffer-cache_'


def _unframe_snappy(data):
    """Snappy's framing format: per chunk a type byte and a 3-byte little-endian length.

    Type 0x00 holds a CRC and a raw Snappy block, 0x01 a CRC and plain bytes; the stream
    identifier (0xff) and padding or skippable chunks carry no data.
    """
    out, pos = bytearray(), 0
    while pos + 4 <= len(data):
        kind = data[pos]
        length = int.from_bytes(data[pos + 1:pos + 4], 'little')
        chunk = data[pos + 4:pos + 4 + length]
        if len(chunk) != length:
            raise ValueError('truncated Snappy frame')
        pos += 4 + length
        if kind == 0x00:
            out += snappy_raw_uncompress(chunk[4:])
        elif kind == 0x01:
            out += chunk[4:]
    return bytes(out)


def _media_firefox(profile):
    cache = os.path.join(profile.root, 'cache')
    db = open_sqlite_db_readonly(os.path.join(cache, 'caches.sqlite'))
    if db is None:
        return
    try:
        entries = db.execute('SELECT request_url_no_query, response_body_id FROM entries').fetchall()
    except sqlite3.Error as exc:
        logfunc(f'WhatsApp Web: could not read {cache}: {exc}')
        return
    finally:
        db.close()
    for url, body_id in entries:
        if not isinstance(url, str) or not url.startswith(MEDIA_PREFIX) or not body_id:
            continue
        files = glob.glob(os.path.join(glob.escape(cache), 'morgue', '*', glob.escape(body_id) + '.final'))
        if not files:
            profile.media_missing += 1
            continue
        with open(files[0], 'rb') as handle:
            raw = handle.read()
        try:
            body = _unframe_snappy(raw) if raw[:1] == b'\xff' else raw
        except ValueError:
            profile.media_missing += 1
            continue
        yield url[len(MEDIA_PREFIX):], files[0], body


def _media_chromium(profile):
    root = os.path.join(profile.profile_dir, 'Service Worker', 'CacheStorage')
    for folder, _dirs, names in os.walk(root):
        for name in sorted(names):
            if not name.endswith('_0'):
                continue
            path = os.path.join(folder, name)
            entry = read_entry(path)
            if entry is None or MEDIA_PREFIX not in (entry.key or ''):
                continue
            body = entry.read_body()
            if not body:
                profile.media_missing += 1
                continue
            yield entry.key.split(MEDIA_PREFIX, 1)[1], path, body


def media(profile):
    """{SHA-256 (base64, as WhatsApp stores it): (cache file, bytes)} for the profile's cached media.

    WhatsApp Web keys each cached file by a hash; an entry is kept only when the SHA-256 of
    its bytes equals that key, so every file returned is the one its key names.
    """
    if profile.media is not None:
        return profile.media
    profile.media, mismatched = {}, 0
    reader = _media_chromium if profile.kind == 'Chromium' else _media_firefox
    try:
        for key, path, body in reader(profile):
            key = urllib.parse.unquote(key)
            if base64.b64encode(hashlib.sha256(body).digest()).decode() != key:
                mismatched += 1
                continue
            if key not in profile.media:
                profile.media[key] = (path, body)
                profile.sources.append(path)
    except OSError as exc:
        logfunc(f'WhatsApp Web: could not read the media cache of {profile.root}: {exc}')
    if mismatched:
        logfunc(f'WhatsApp Web: {mismatched} cached media file(s) in {profile.root} did not hash to their key')
    if profile.media_missing:
        logfunc(f'WhatsApp Web: {profile.media_missing} cached media entr(ies) in {profile.root} had no readable body')
    return profile.media


def records(profile, store, database='model-storage'):
    return profile.stores.get((database, store), [])


def jid(value):
    """A WhatsApp id as its string form, whether stored as text or as a Wid object."""
    if isinstance(value, dict):
        return value.get('_serialized') or ''
    return value if isinstance(value, str) else ''
