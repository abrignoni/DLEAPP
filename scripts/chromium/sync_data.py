"""Read the Sync Data/LevelDB store of a Chromium browser profile.

Author: @AlexisBrignoni, Claude.

Chromium keeps the data and metadata of each sync data type in one LevelDB
database, Sync Data/LevelDB in the profile folder. Its keys are
<root tag>-dt-<storage key> for a data record, <root tag>-md-<storage key> for
that record's sync metadata and <root tag>-GlobalMetadata for the type's sync
state, with A- in front of all three for data held in account storage
(components/sync/model/blocking_data_type_store_impl.cc, lines 26 to 63, and
lines 172 to 183, at chromium 5926523bcfedb77ba2533ace1dd93b477673f72a:
https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L26-L63
https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L172-L183
).

The store is read with the vendored ccl_leveldb, which returns every version
of a key that is still in the table and log files. LevelDB numbers each write
and orders the versions of a key by decreasing sequence number, the newest first
(db/dbformat.cc, lines 47 to 63, at leveldb bb74ef739973:
https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63
). Only the newest version of each key is kept; when it is a deletion nothing is
kept for the key. Earlier versions are counted and not returned.

Values are protocol buffers. They are decoded here against the field numbers
and types of the messages Chromium publishes in components/sync/protocol,
transcribed into the tables below, not by guessing at field types. A field
the tables do not name is skipped. A value whose wire type disagrees with the
table raises ProtoError, and the caller logs the record and leaves it out.
"""

import hashlib
import os
import re
import struct

from scripts.ccl import ccl_leveldb

CHROMIUM_COMMIT = '5926523bcfedb77ba2533ace1dd93b477673f72a'


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


def _fields(data):
    """(field number, wire type, value) for each field of one encoded message."""
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
            if position + 8 > size:
                raise ProtoError('truncated 64-bit field')
            value = data[position:position + 8]
            position += 8
        elif wire_type == 2:
            length, position = _varint(data, position)
            if position + length > size:
                raise ProtoError('length-delimited field runs past the end')
            value = data[position:position + length]
            position += length
        elif wire_type == 5:
            if position + 4 > size:
                raise ProtoError('truncated 32-bit field')
            value = data[position:position + 4]
            position += 4
        else:
            raise ProtoError(f'unsupported wire type {wire_type}')
        yield number, wire_type, value


def _signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


# Field kinds and the wire type each is written with.
_WIRE = {'string': 2, 'bytes': 2, 'int64': 0, 'int32': 0, 'uint32': 0, 'uint64': 0,
         'bool': 0, 'enum': 0, 'fixed32': 5}


def _scalar(kind, wire_type, value):
    if kind in ('string', 'bytes'):
        if kind == 'bytes':
            return bytes(value)
        return bytes(value).decode('utf-8', 'replace')
    if kind == 'fixed32':
        return struct.unpack('<I', value)[0]
    if kind == 'int64':
        return _signed(value, 64)
    if kind in ('int32', 'enum'):
        # An int32 or enum is written as the sign-extended 64-bit varint.
        return _signed(value, 64)
    if kind == 'bool':
        return bool(value)
    if wire_type == 0:
        return value
    raise ProtoError(f'unhandled kind {kind}')


def decode(data, message):
    """Decode `data` as `message`, a name in SCHEMAS. Returns a dict by field name.

    Repeated fields are lists; absent fields are absent from the dict.
    """
    schema = SCHEMAS[message]
    out = {}
    for number, wire_type, value in _fields(bytes(data)):
        field = schema.get(number)
        if field is None:
            continue
        name, kind, repeated = field
        if kind.startswith('message:'):
            if wire_type != 2:
                raise ProtoError(f'{message}.{name}: wire type {wire_type}, expected 2')
            item = decode(value, kind[8:])
        elif wire_type == 2 and _WIRE.get(kind) == 0 and repeated:
            # A packed repeated scalar.
            items = []
            position = 0
            while position < len(value):
                number_value, position = _varint(value, position)
                items.append(_scalar(kind, 0, number_value))
            out.setdefault(name, []).extend(items)
            continue
        else:
            if _WIRE.get(kind) != wire_type:
                raise ProtoError(f'{message}.{name}: wire type {wire_type}, '
                                 f'expected {_WIRE.get(kind)}')
            item = _scalar(kind, wire_type, value)
        if repeated:
            out.setdefault(name, []).append(item)
        else:
            out[name] = item
    return out


# Field tables, (name, kind, repeated) by field number, transcribed from the
# .proto files under components/sync/protocol and components/send_tab_to_self/proto
# at CHROMIUM_COMMIT. Only the fields the artifacts read are listed.
SCHEMAS = {
    # device_info_specifics.proto
    'DeviceInfoSpecifics': {
        1: ('cache_guid', 'string', False),
        2: ('client_name', 'string', False),
        3: ('device_type', 'enum', False),
        4: ('sync_user_agent', 'string', False),
        5: ('chrome_version', 'string', False),
        7: ('signin_scoped_device_id', 'string', False),
        8: ('last_updated_timestamp', 'int64', False),
        11: ('model', 'string', False),
        12: ('manufacturer', 'string', False),
        17: ('chrome_version_info', 'message:ChromeVersionInfo', False),
        19: ('os_type', 'enum', False),
        20: ('device_form_factor', 'enum', False),
    },
    'ChromeVersionInfo': {1: ('version_number', 'string', False)},
    # session_specifics.proto
    'SessionSpecifics': {
        1: ('session_tag', 'string', False),
        2: ('header', 'message:SessionHeader', False),
        3: ('tab', 'message:SessionTab', False),
        4: ('tab_node_id', 'int32', False),
    },
    'SessionHeader': {
        2: ('window', 'message:SessionWindow', True),
        3: ('client_name', 'string', False),
        4: ('device_type', 'enum', False),
        5: ('device_form_factor', 'enum', False),
        6: ('session_start_time_unix_epoch_millis', 'int64', False),
    },
    'SessionWindow': {
        1: ('window_id', 'int32', False),
        2: ('selected_tab_index', 'int32', False),
        3: ('browser_type', 'enum', False),
        4: ('tab', 'int32', True),
    },
    'SessionTab': {
        1: ('tab_id', 'int32', False),
        2: ('window_id', 'int32', False),
        3: ('tab_visual_index', 'int32', False),
        4: ('current_navigation_index', 'int32', False),
        5: ('pinned', 'bool', False),
        6: ('extension_app_id', 'string', False),
        7: ('navigation', 'message:TabNavigation', True),
        13: ('browser_type', 'enum', False),
        14: ('last_active_time_unix_epoch_millis', 'int64', False),
    },
    # tab_navigation.proto
    'TabNavigation': {
        2: ('virtual_url', 'string', False),
        3: ('referrer', 'string', False),
        4: ('title', 'string', False),
        6: ('page_transition', 'enum', False),
        7: ('redirect_type', 'enum', False),
        8: ('unique_id', 'int32', False),
        9: ('timestamp_msec', 'int64', False),
        10: ('navigation_forward_back', 'bool', False),
        11: ('navigation_from_address_bar', 'bool', False),
        12: ('navigation_home_page', 'bool', False),
        15: ('global_id', 'int64', False),
        17: ('favicon_url', 'string', False),
        20: ('http_status_code', 'int32', False),
    },
    # send_tab_to_self.proto (components/send_tab_to_self/proto)
    'SendTabToSelfLocal': {
        1: ('specifics', 'message:SendTabToSelfSpecifics', False),
    },
    # send_tab_to_self_specifics.proto
    'SendTabToSelfSpecifics': {
        1: ('title', 'string', False),
        2: ('url', 'string', False),
        3: ('shared_time_usec', 'int64', False),
        4: ('device_name', 'string', False),
        5: ('guid', 'string', False),
        7: ('target_device_sync_cache_guid', 'string', False),
        8: ('opened', 'bool', False),
        9: ('notification_dismissed', 'bool', False),
        13: ('received_time_windows_epoch_micros', 'int64', False),
        14: ('opened_time_windows_epoch_micros', 'int64', False),
        16: ('activated_time_windows_epoch_micros', 'int64', False),
    },
    # data_type_state.proto, the value of a -GlobalMetadata key
    'DataTypeState': {
        5: ('cache_guid', 'string', False),
    },
}

# sync_enums.proto
DEVICE_TYPES = {0: 'TYPE_UNSET', 1: 'TYPE_WIN', 2: 'TYPE_MAC', 3: 'TYPE_LINUX', 4: 'TYPE_CROS',
                5: 'TYPE_OTHER', 6: 'TYPE_PHONE', 7: 'TYPE_TABLET'}
OS_TYPES = {0: 'OS_TYPE_UNSPECIFIED', 1: 'OS_TYPE_WINDOWS', 2: 'OS_TYPE_MAC', 3: 'OS_TYPE_LINUX',
            4: 'OS_TYPE_CHROME_OS_ASH', 5: 'OS_TYPE_ANDROID', 6: 'OS_TYPE_IOS',
            7: 'OS_TYPE_CHROME_OS_LACROS', 8: 'OS_TYPE_FUCHSIA'}
FORM_FACTORS = {0: 'DEVICE_FORM_FACTOR_UNSPECIFIED', 1: 'DEVICE_FORM_FACTOR_DESKTOP',
                2: 'DEVICE_FORM_FACTOR_PHONE', 3: 'DEVICE_FORM_FACTOR_TABLET',
                4: 'DEVICE_FORM_FACTOR_AUTOMOTIVE', 5: 'DEVICE_FORM_FACTOR_WEARABLE',
                6: 'DEVICE_FORM_FACTOR_TV'}
BROWSER_TYPES = {0: 'BROWSER_TYPE_UNKNOWN', 1: 'TYPE_TABBED', 2: 'TYPE_POPUP',
                 3: 'TYPE_CUSTOM_TAB', 4: 'TYPE_AUTH_TAB'}
PAGE_TRANSITIONS = {0: 'LINK', 1: 'TYPED', 2: 'AUTO_BOOKMARK', 3: 'AUTO_SUBFRAME',
                    4: 'MANUAL_SUBFRAME', 5: 'GENERATED', 6: 'AUTO_TOPLEVEL', 7: 'FORM_SUBMIT',
                    8: 'RELOAD', 9: 'KEYWORD', 10: 'KEYWORD_GENERATED'}
REDIRECT_TYPES = {1: 'CLIENT_REDIRECT', 2: 'SERVER_REDIRECT'}

_KEY = re.compile(rb'^(A-)?([a-z0-9_]+)-(dt|md)-(.*)$', re.S)
_GLOBAL = re.compile(rb'^(A-)?([a-z0-9_]+)-GlobalMetadata$')


class SyncStore:
    """The live records of one Sync Data/LevelDB folder.

    data      {(account storage, root tag): {storage key: value bytes}}
    globals   {(account storage, root tag): value bytes of its -GlobalMetadata}
    counts    records read, versions superseded by a newer one, keys whose
              newest version is a deletion
    """

    def __init__(self, folder):
        self.folder = folder
        self.data = {}
        self.globals = {}
        self.records = 0
        self.superseded = 0
        self.deleted = 0
        newest = {}
        database = ccl_leveldb.RawLevelDb(folder)
        try:
            for record in database.iterate_records_raw():
                self.records += 1
                key = bytes(record.user_key)
                held = newest.get(key)
                if held is None or record.seq > held[0]:
                    newest[key] = (record.seq, record.state, bytes(record.value or b''))
        finally:
            database.close()
        self.superseded = self.records - len(newest)
        for key, (_seq, state, value) in newest.items():
            if state == ccl_leveldb.KeyState.Deleted:
                self.deleted += 1
                continue
            match = _KEY.match(key)
            if match:
                if match.group(3) == b'dt':
                    group = (bool(match.group(1)), match.group(2).decode('ascii'))
                    storage_key = match.group(4).decode('utf-8', 'replace')
                    self.data.setdefault(group, {})[storage_key] = value
                continue
            match = _GLOBAL.match(key)
            if match:
                self.globals[(bool(match.group(1)), match.group(2).decode('ascii'))] = value

    def records_of(self, root_tag):
        """(account storage, storage key, value) for the live data records of one type."""
        out = []
        for (account, tag), records in sorted(self.data.items()):
            if tag != root_tag:
                continue
            for storage_key, value in sorted(records.items()):
                out.append((account, storage_key, value))
        return out

    def local_cache_guid(self, root_tag, account=False):
        """The cache GUID the type's DataTypeState records for this client, or ''.

        Raises ProtoError when the -GlobalMetadata value does not decode.
        """
        value = self.globals.get((account, root_tag))
        if not value:
            return ''
        return decode(value, 'DataTypeState').get('cache_guid', '')


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


def sync_folders(context, label=''):
    """The located Store of each Sync Data/LevelDB folder a browser profile holds.

    Grouped from the staged files the patterns matched, so a folder is read
    once however many of its files matched; directories in files_found are
    skipped. On a Mac logical extraction one profile can sit under Users/ and
    under System/Volumes/Data/Users/; a folder whose copy under the second path
    holds the same files with the same bytes is returned once, and copies that
    differ are both returned. Sorted by the folder's path inside the extraction.
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
        if name != 'Sync Data/LevelDB':
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
        logfunc(f'{label}: {skipped} byte-identical Sync Data folder copy(ies) under '
                f'System/Volumes/Data or System/Volumes/Update/mnt1 not read again')
    return sorted(kept, key=lambda store: store.relative)
