"""Dropbox desktop client for Windows: account info, sync history, storage file list and the
sync engine (Nucleus) trees, for DLEAPP.

Author: @charpy4n6, Claude.
"""

__artifacts_v2__ = {
    "dropboxAccountInfo": {
        "name": "Dropbox Account Info",
        "description": "The accounts the Dropbox desktop client lists in info.json: the account kind, the local "
                       "Dropbox folder path, the host value, the team flag and the subscription type, as stored.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads info.json in the Dropbox folder of AppData/Local on Windows, one row per top-level key "
                 "(personal, business). Path, Host, Is Team and Subscription Type are path, host, is_team and "
                 "subscription_type as stored; no published definition of host was found and it is not "
                 "interpreted. On the tested sample the file held one personal account. The account email is "
                 "not in this file; it is believed to be in the DPAPI-encrypted .dbx files, which are not read.",
        "paths": ('*/Dropbox/info.json',),
        "output_types": ["standard"],
        "artifact_icon": "user",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 1 row",
        },
    },
    "dropboxSyncHistory": {
        "name": "Dropbox Sync History",
        "description": "Sync events the Dropbox desktop client kept in sync_history.db: the time, whether a file "
                       "or folder, the event type and direction, the local and server paths and the file ID.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads the sync_history table of sync_history.db, with its -wal when present, in each "
                 "instance folder of the Dropbox client, one row per table row. Time (UTC) is timestamp read as "
                 "Unix seconds; on the tested sample the 38 values fell between 22:49 and 23:37 UTC on the day the tester "
                 "used the client, and each upload row's time was within 2 seconds of the matching sync "
                 "engine node's remote_tree field 3.2. When the Dropbox folder itself is in the extraction at the "
                 "local path a row names (from after the drive letter, compared without regard to case), File "
                 "links to that file; the tested sample did not include the folder, so this linking is "
                 "code-present but not exercised against real data. Item Type, Event Type and Direction are event_type, file_event_type and "
                 "direction as stored (file or directory; add, move or delete; upload or download on the "
                 "tested sample). On the tested sample a renamed file appeared as an add under its new name. "
                 "File ID is file_id as stored: base64url of the 16-byte node key that nucleus.sqlite3 uses, "
                 "decoded in Node Key so rows can be matched to Dropbox Sync Engine Items; all 38 decoded on "
                 "the tested sample and 37 matched a node there, the exception being the deleted folder. Server Path is server_path as stored, a number, a colon and the path; "
                 "the number is not interpreted. Other User is other_user as stored (0 on every tested row). "
                 "The table appears to hold recent events only; a missing event is not evidence the action "
                 "did not happen.",
        "paths": ('*/Dropbox/instance*/sync_history.db*', '*/[Uu]sers/*/Dropbox/*'),
        "output_types": ["standard"],
        "artifact_icon": "refresh-cw",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 38 rows",
        },
    },
    "dropboxStorageFiles": {
        "name": "Dropbox Storage Files",
        "description": "Files and folders the Dropbox desktop client listed in sync_and_storage.db: the path, "
                       "size, modified time, folder flag, offline availability and online-only counters.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads the storage_files table of sync_and_storage.db, with its -wal when present, in each "
                 "instance folder of the Dropbox client, one row per table row. Modified (UTC) is last_modified "
                 "read as Unix milliseconds, and Online Files Modified (UTC) is online_files_modified_time read "
                 "the same way when not 0. Path, File Name, Size, Blocks, Is Folder, Available Offline, File "
                 "Type, Parent Path, Online Files Size, Has Online-Only Files and Has Offline Files are fq_path, "
                 "filename, size, blocks, is_dir, is_available_offline, file_type, parent_path, "
                 "online_files_size, has_online_only_files and has_offline_files as stored. On the tested "
                 "sample the table held 40 rows. When the Dropbox folder itself is in the extraction at the "
                 "path a row names (from after the drive letter, compared without regard to case), File links "
                 "to that file; the tested sample did not include the folder, so this linking is "
                 "code-present but not exercised against real data.",
        "paths": ('*/Dropbox/instance*/sync_and_storage.db*', '*/[Uu]sers/*/Dropbox/*'),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 40 rows",
        },
    },
    "dropboxNucleusItems": {
        "name": "Dropbox Sync Engine Items",
        "description": "Files and folders in the local, remote and synced trees of the Dropbox sync engine "
                       "database (nucleus.sqlite3), and its remote tombstones: the path, size, content hash, "
                       "local and remote times, and the NTFS file reference.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads local_tree, remote_tree, synced_tree and remote_tombstones in sync/nucleus.sqlite3, with "
                 "its -wal, in each instance folder of the Dropbox client, one row per node key, the three trees "
                 "joined on the key, and one row per tombstone. Each value is an undocumented protobuf; the "
                 "field numbers were worked out from the tested sample and are reported as such. Field 1 of a "
                 "local_tree or remote_tree value, and field 2 of a synced_tree value, holds the node: 1 the "
                 "node key, 2 the parent key, 3 the name and 5.1 the content hash (1) and size (2). Kind is "
                 "File when the node has field 5 and Folder when it has field 6; otherwise it is blank. On the "
                 "tested sample 31 nodes were File, 5 Folder and 5 blank, the 5 blank all named like files ("
                 "pic.PNG, Capture2.PNG, a .jpg and two screenshots) that were added from elsewhere and "
                 "synced down; why they lack both fields is not established. Path is built from the names up the parent keys of whichever tree holds "
                 "the node, preferring local; the root key is sixteen 0xFF bytes. Local Modified (UTC) is "
                 "local_tree field 2.1 read as a Windows FILETIME; on the tested sample it equalled, to the "
                 "second, remote_tree field 2 read as Unix seconds (Remote Modified (UTC)) on 36 of the 40 "
                 "nodes with both set; the other 4 were folders, whose local time was later. Remote Field 3.2 "
                 "(UTC) is remote_tree field 3.2 read as Unix seconds; on the tested sample it fell within 2 "
                 "seconds of the sync_history time of the same node key on every upload row, but its meaning is not established. Local "
                 "File Reference is local_tree field 3 as stored, which on the tested sample had the form of an "
                 "NTFS file reference (low 48 bits the MFT entry, high 16 the sequence), split into those two "
                 "parts; the MFT was not available to confirm it. Content Hash is shown as hex; its algorithm "
                 "is not established here. In Local, In Remote and In Synced say which tables held the key. A "
                 "tombstone row has only the key and Tombstone Time (UTC), field 2.2 read as Unix seconds; on "
                 "the tested sample the 3 tombstones shared one time, 24 seconds after the sync_history delete "
                 "of folder BFOR304, and their keys are in no tree; that they are BFOR304 and its contents is "
                 "not established. Not reported: remote_overlay, config, "
                 "periodic_jobs and file_block_upload_tokens.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*',),
        "output_types": ["standard"],
        "artifact_icon": "git-branch",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 44 rows (41 nodes, 3 tombstones)",
        },
    },
    "dropboxNucleusHistory": {
        "name": "Dropbox Sync Engine History",
        "description": "Changes to the Dropbox sync engine trees recovered from earlier versions of "
                       "nucleus.sqlite3 held in its -wal: items added, removed, renamed, moved or given new "
                       "content in the local or remote tree, and tombstones written or removed, in commit order.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads sync/nucleus.sqlite3 and its -wal. The -wal frames are read up to the first frame whose "
                 "salts differ from the header's, and the database is opened, in a temporary copy, as it stood "
                 "after each commit frame; local_tree, remote_tree and remote_tombstones are compared between "
                 "consecutive commits, decoded as Dropbox Sync Engine Items describes. One row per change. "
                 "Commit is the commit's number in -wal order; no wall-clock time is stored per commit, so "
                 "Item Time (UTC) is a time from the changed record itself: for a remote item remote_tree "
                 "field 3.2, for a local item local_tree field 2.1, for a tombstone field 2.2, each read as "
                 "Dropbox Sync Engine Items reads it. Change is Added, Removed, Renamed (field 3 differs), Moved "
                 "(parent key differs), Content Changed (content hash or size differs) or Tombstone Added/"
                 "Removed; a change of other fields only is not reported. On the tested sample the -wal held "
                 "723 frames and 436 commits, and the rows matched what the tester reports doing: three files "
                 "removed from both trees with tombstones written (deleted) and back under new node keys three "
                 "minutes later (restored from the trash), folder BFOR304 removed with a tombstone that was "
                 "itself removed later (permanently deleted online), 20191013_124817.jpg renamed to 'renamed "
                 "file.jpg', dzivdzan-zbori.png moved to 'Moved Files', and a folder and two screenshots "
                 "uploaded from the web appearing in remote_tree before local_tree. The web upload and the "
                 "rename's old name are recorded in no other Dropbox file read here. What this shows depends "
                 "on how much of the -wal remains: a checkpoint moves pages into the database and later "
                 "commits overwrite the -wal, so earlier changes may be gone; an absent change is not evidence "
                 "it did not happen.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*',),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 144 rows (436 commits)",
        },
    },
    "dropboxClientEvents": {
        "name": "Dropbox Client Events",
        "description": "Usage events the Dropbox desktop client queued in its events/store file before sending "
                       "them to Dropbox: the time, the event name, the component and surface, and the event's "
                       "other fields, among them shared link and share invite events naming a file ID.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads events/store in the Dropbox folder of AppData/Local. The file is undocumented; its "
                 "layout was worked out from the tested sample. Blocks begin with a header of Unix seconds (8 "
                 "bytes), nanoseconds (4 bytes) and 24 zero bytes; Batch Time (UTC) is the time of the last such "
                 "header before the record, which on the tested sample was not written before every record, so "
                 "several records share one Batch Time and it is not the record's own time: on the tested "
                 "sample a ClientEventData record's own time was from 1 second before to 32 minutes after its Batch Time. Each record has a "
                 "length-prefixed type name and a length-prefixed protobuf. Two types were seen: "
                 "DesktopGenericCloggerEvent, whose protobuf holds the stream name (field 1) and name/value pairs "
                 "(field 4, the 'extra' pair holding nested pairs), and ClientEventData, whose protobuf holds a "
                 "time (field 2: seconds and nanoseconds, given as Event Time (UTC)), action and object (field "
                 "4), name/value pairs (field 8) and a surface (field 10). Event Name is the event_name pair, or "
                 "action.object for ClientEventData. Content ID is a content_identifier or file_id pair as "
                 "stored; where it is id: and base64url of a 16-byte value, Node Key gives that value in hex for "
                 "matching to Dropbox Sync Engine Items. Details are the remaining non-empty pairs, name=value, "
                 "except event, trace and session IDs. The same event can appear once per stream (all-events "
                 "and user-events) and again as ClientEventData; all are reported, with Stream naming which. On "
                 "the tested sample: 2,526 DesktopGenericCloggerEvent and 488 ClientEventData records, among "
                 "them preferences views, a camera upload mode selection with value photos, the selective sync "
                 "button, a share invite to 1 recipient with view access, and create.shared_link naming the "
                 "node key of Horse.jpg. These are the client's own telemetry: a record says the client logged "
                 "an interface event, not what the person intended, and records already sent to Dropbox may "
                 "have been removed from the file.",
        "paths": ('*/Dropbox/events/store',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 3014 rows",
        },
    },
    "dropboxThumbnails": {
        "name": "Dropbox Thumbnails",
        "description": "Thumbnails the Dropbox desktop client cached in icon.db for files and folders in the "
                       "Dropbox folder, with the path they were made for and the time the row was written.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads path_icon_table in icon.db, with its -wal when present, in each instance folder of the "
                 "Dropbox client, one row per table row. Each image column holds a Python pickle of "
                 "_codecs.encode(<text>, 'latin1'); it is not unpickled, which would run code: the pickle "
                 "opcodes are checked to be exactly that call and the text is read and encoded to bytes, which "
                 "on every tested row were a PNG. Created (UTC) is created_time read as Unix seconds. Path is "
                 "file_path after its leading 'tpng' and before its trailing _<size>, as stored (lower case on "
                 "the tested sample); Size is that number. File Modified is file_mtime as stored (empty on "
                 "every tested row). On the tested sample the 24 rows included Horse.jpg and Horse "
                 "(edited).jpg, whose thumbnails show the same picture mirrored left to right, and files "
                 "since deleted from the folder keep their row until it is replaced. ext_icon_table (generic "
                 "icons per file extension) is not reported.",
        "paths": ('*/Dropbox/instance*/icon.db*',),
        "output_types": ["standard"],
        "artifact_icon": "image",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 24 rows",
        },
    },
    "dropboxUploadRecords": {
        "name": "Dropbox Upload Records",
        "description": "Records the Dropbox sync engine kept in file_block_upload_tokens of nucleus.sqlite3, one "
                       "per uploaded block: the time, the file's node key and path, the block hash, and the user "
                       "and namespace IDs stored with it.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads file_block_upload_tokens (fileid, block_hash, ts, token) in sync/nucleus.sqlite3, with "
                 "its -wal, one row per table row. Time (UTC) is ts read as Unix seconds. Node Key is fileid; "
                 "Path is built from the sync engine trees as Dropbox Sync Engine Items builds it. Block Hash "
                 "is block_hash in hex. The token is an undocumented protobuf; field 1.1 holds the block hash "
                 "(1, equal to block_hash on all 38 tested rows), a time (2, Token Time (UTC), read as Unix "
                 "seconds), a user ID (3), a namespace ID (4) and a value (5), reported as stored. Field 1.2, a "
                 "text token, is not reported. On the tested sample all 38 rows named a node in local_tree, ts "
                 "fell between 23:01:23 and 23:13:49 UTC, 35 rows were 1 to 9 seconds before the sync_history "
                 "upload of the same node and 3 rows 6 to 10 minutes before it, Token Time was 60 or 61 "
                 "seconds before ts on every row, and User ID (883835137) equalled the "
                 "user_id in the client's events/store and remote_tree field 3.1, and Namespace ID "
                 "(1858787921) the number at the start of every sync_history server_path. One file can have "
                 "more than one block; a row does not by itself establish that the whole file was uploaded.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*',),
        "output_types": ["standard"],
        "artifact_icon": "upload-cloud",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 38 rows",
        },
    },
    "dropboxClientInfo": {
        "name": "Dropbox Client Info",
        "description": "Values about the Dropbox desktop client and the computer: the last client start time "
                       "from boot_marker.dbx, the Windows build the sync engine recorded, and the user and "
                       "namespace IDs found in the sync engine and sync history.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "One row per value. Last Boot Time (UTC) is last_boot_time in boot_marker.dbx, a JSON file "
                 "despite its name, read as Unix seconds, and Boot Count its boot_count, as stored; on the "
                 "tested sample last_boot_time was 23:41:06 UTC, after every other time in the extraction but "
                 "the events/store records, and boot_count was 0, so boot_count is not a count of starts. OS "
                 "Version is field 1 of config row 28 in nucleus.sqlite3, as stored ('11 26200' on the tested "
                 "sample, a Windows 11 25H2 machine, build 26200). User ID lists the distinct remote_tree field "
                 "3.1 values and Namespace ID the distinct numbers before the colon in sync_history server_path; "
                 "the meaning of each was not documented by Dropbox that was found, and is named from the "
                 "events/store user_id they equalled (User ID) and from their place in the server path "
                 "(Namespace ID). The account email and name are not in these files; they are believed to be in "
                 "the DPAPI-encrypted .dbx files, which are not read.",
        "paths": ('*/Dropbox/boot_marker.dbx', '*/Dropbox/instance*/sync/nucleus.sqlite3*',
                  '*/Dropbox/instance*/sync_history.db*'),
        "output_types": ["standard"],
        "artifact_icon": "info",
        "sample_data": {
            "user_win11": "Windows 11 Home 25H2, Dropbox 274.4.4905 | 5 rows",
        },
    },
}

import base64
import json
import os
import re
import shutil
import sqlite3
import struct
import tempfile
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media, check_in_media, logfunc,
                              open_sqlite_db_readonly)

_SIDECAR = re.compile(r'-(wal|shm|journal)$')
_ROOT_KEY = b'\xff' * 16
_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _databases(context, name):
    """The staged paths of a database file, without its sidecars, in path order."""
    found = []
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.isdir(path) or _SIDECAR.search(path):
            continue
        if os.path.basename(path) == name:
            found.append(path)
    return found


def _path_key(path):
    """A Windows or extraction path, lower case with forward slashes, from after any drive letter."""
    path = (path or '').replace('\\', '/').lower()
    return path.split(':', 1)[1] if re.match(r'^[a-z]:', path) else path


class _LocalFiles:
    """Files of the Dropbox folder present in the extraction, found by the path a row names."""

    def __init__(self, context):
        self._found = [(str(p), _path_key(str(p))) for p in sorted({str(p) for p in context.get_files_found()})
                       if os.path.isfile(str(p)) and '/dropbox/' in _path_key(str(p))]
        self._cache = {}

    def media(self, local_path):
        key = _path_key(local_path)
        if not key or '/' not in key:
            return ''
        if key not in self._cache:
            match = next((path for path, found in self._found if found.endswith(key)), None)
            self._cache[key] = (check_in_media(match, name=os.path.basename(match)) or '') if match else ''
        return self._cache[key]


def _rows(db, query, label):
    try:
        return db.execute(query).fetchall()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logfunc(f'Dropbox {label}: query failed ({exc})')
        return []


def unix_time(value, scale=1):
    """A Unix time (seconds, or milliseconds with scale=1000) as an aware UTC datetime, or ''."""
    if value in (None, '', 0):
        return ''
    try:
        return datetime.fromtimestamp(int(value) / scale, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ''


def filetime(value):
    """A Windows FILETIME (100 ns since 1601) as an aware UTC datetime, or ''."""
    if not value:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=int(value) // 10)
    except (TypeError, ValueError, OverflowError):
        return ''


def file_id_key(file_id):
    """The 16-byte node key a sync_history file_id (base64url, unpadded) encodes, as hex, or ''."""
    if not file_id:
        return ''
    try:
        raw = base64.urlsafe_b64decode(file_id + '=' * (-len(file_id) % 4))
    except (ValueError, TypeError):
        return ''
    return raw.hex() if len(raw) == 16 else ''


def _varint(data, pos):
    result = shift = 0
    while True:
        if pos >= len(data):
            raise ValueError('truncated varint')
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, pos


def pb_fields(data):
    """A protobuf message as {field number: [values]}: ints for varints, bytes otherwise."""
    fields = {}
    pos = 0
    while pos < len(data):
        key, pos = _varint(data, pos)
        number, wire = key >> 3, key & 7
        if wire == 0:
            value, pos = _varint(data, pos)
        elif wire == 1:
            value, pos = data[pos:pos + 8], pos + 8
        elif wire == 5:
            value, pos = data[pos:pos + 4], pos + 4
        elif wire == 2:
            length, pos = _varint(data, pos)
            value, pos = data[pos:pos + length], pos + length
        else:
            raise ValueError(f'unsupported wire type {wire}')
        fields.setdefault(number, []).append(value)
    return fields


def _first(fields, number, default=None):
    values = fields.get(number)
    return values[0] if values else default


def _sub(fields, *path):
    """The value at a path of nested field numbers, or None."""
    current = fields
    for depth, number in enumerate(path):
        value = _first(current, number)
        if value is None:
            return None
        if depth == len(path) - 1:
            return value
        if not isinstance(value, bytes):
            return None
        try:
            current = pb_fields(value)
        except ValueError:
            return None
    return current


def _node_fields(inner_raw, outer):
    """The node fields of a tree value: key, parent, name, kind, hash, size, and the outer fields."""
    inner = pb_fields(inner_raw) if isinstance(inner_raw, bytes) else {}
    name = _first(inner, 3, b'')
    if 6 in inner:
        kind = 'Folder'
    elif 5 in inner:
        kind = 'File'
    else:
        kind = ''
    return {
        'key': _first(inner, 1, b''),
        'parent': _first(inner, 2, b''),
        'name': name.decode('utf-8', 'replace') if isinstance(name, bytes) else '',
        'kind': kind,
        'hash': _sub(inner, 5, 1, 1),
        'size': _sub(inner, 5, 1, 2),
        'outer': outer,
    }


def _tree(db, table):
    """local_tree and remote_tree keep the node in field 1, synced_tree in field 2."""
    node_field = 2 if table == 'synced_tree' else 1
    nodes = {}
    for key, value in _rows(db, f'SELECT key, value FROM {table}', 'Sync Engine Items'):
        try:
            outer = pb_fields(bytes(value))
            nodes[bytes(key)] = _node_fields(_first(outer, node_field), outer)
        except ValueError as exc:
            logfunc(f'Dropbox Sync Engine Items: {table} value not decoded ({exc})')
    return nodes


def _path(key, trees):
    parts, seen = [], set()
    current = key
    while current and current != _ROOT_KEY and current not in seen:
        seen.add(current)
        node = next((t[current] for t in trees if current in t), None)
        if node is None:
            parts.append(f'<{current.hex()}>')
            break
        parts.append(node['name'])
        current = node['parent']
    return '/' + '/'.join(reversed(parts))


def nucleus_rows(path, relative):
    db = open_sqlite_db_readonly(path)
    if db is None:
        return []
    try:
        local, remote, synced = (_tree(db, t) for t in ('local_tree', 'remote_tree', 'synced_tree'))
        tombstones = _rows(db, 'SELECT key, value FROM remote_tombstones', 'Sync Engine Items')
    finally:
        db.close()

    rows = []
    trees = (local, remote, synced)
    for key in sorted(set(local) | set(remote) | set(synced)):
        node = local.get(key) or remote.get(key) or synced.get(key)
        loc, rem = local.get(key), remote.get(key)
        local_mod = filetime(_sub(loc['outer'], 2, 1)) if loc else ''
        remote_mod = unix_time(_first(rem['outer'], 2)) if rem else ''
        remote_f32 = unix_time(_sub(rem['outer'], 3, 2)) if rem else ''
        file_ref = _first(loc['outer'], 3) if loc else None
        mft = seq = ''
        if isinstance(file_ref, int):
            mft, seq = file_ref & 0xFFFFFFFFFFFF, file_ref >> 48
        content_hash = node['hash']
        rows.append((local_mod, remote_mod, remote_f32, '', _path(key, trees), node['name'], node['kind'],
                     node['size'] if node['size'] is not None else '',
                     content_hash.hex() if isinstance(content_hash, bytes) else '',
                     'Yes' if key in local else 'No', 'Yes' if key in remote else 'No',
                     'Yes' if key in synced else 'No', 'No',
                     file_ref if file_ref is not None else '', mft, seq, key.hex(), relative))
    for key, value in tombstones:
        try:
            when = unix_time(_sub(pb_fields(bytes(value)), 2, 2))
        except ValueError:
            when = ''
        rows.append(('', '', '', when, '', '', '', '', '', 'No', 'No', 'No', 'Yes', '', '', '',
                     bytes(key).hex(), relative))
    return rows


@artifact_processor
def dropboxNucleusItems(context):
    data_headers = (('Local Modified (UTC)', 'datetime'), ('Remote Modified (UTC)', 'datetime'),
                    ('Remote Field 3.2 (UTC)', 'datetime'), ('Tombstone Time (UTC)', 'datetime'), 'Path',
                    'Name', 'Kind', 'Size', 'Content Hash', 'In Local', 'In Remote', 'In Synced',
                    'Tombstone', 'Local File Reference (as stored)', 'MFT Entry', 'MFT Sequence', 'Node Key',
                    'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'nucleus.sqlite3'):
        sources.append(path)
        data_list.extend(nucleus_rows(path, context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxSyncHistory(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Item Type', 'Event Type', 'Direction', 'Local Path',
                    ('File', 'media'), 'Server Path', 'Other User (as stored)', 'File ID', 'Node Key', 'Source File')
    data_list, sources = [], []
    local = _LocalFiles(context)
    for path in _databases(context, 'sync_history.db'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            rows = _rows(db, 'SELECT timestamp, event_type, file_event_type, direction, local_path, '
                             'server_path, other_user, file_id FROM sync_history ORDER BY timestamp',
                         'Sync History')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        for ts, item, event, direction, local_path, server_path, other, file_id in rows:
            data_list.append((unix_time(ts), item or '', event or '', direction or '', local_path or '',
                              local.media(local_path) if item == 'file' else '', server_path or '', other if other is not None else '', file_id or '',
                              file_id_key(file_id), relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxStorageFiles(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Online Files Modified (UTC)', 'datetime'), 'Path',
                    ('File', 'media'), 'File Name', 'Size', 'Blocks', 'Is Folder', 'Available Offline', 'File Type', 'Parent Path',
                    'Online Files Size', 'Has Online-Only Files', 'Has Offline Files', 'Source File')
    data_list, sources = [], []
    local = _LocalFiles(context)
    for path in _databases(context, 'sync_and_storage.db'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            rows = _rows(db, 'SELECT last_modified, online_files_modified_time, fq_path, filename, size, '
                             'blocks, is_dir, is_available_offline, file_type, parent_path, online_files_size, '
                             'has_online_only_files, has_offline_files FROM storage_files ORDER BY fq_path',
                         'Storage Files')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        for row in rows:
            values = tuple('' if v is None else v for v in row[2:])
            media = '' if row[6] else local.media(row[2])
            data_list.append((unix_time(row[0], 1000), unix_time(row[1], 1000), values[0], media)
                             + values[1:] + (relative,))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxAccountInfo(context):
    data_headers = ('Account', 'Path', 'Host (as stored)', 'Is Team', 'Subscription Type', 'Source File')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.basename(path) != 'info.json' or os.path.isdir(path):
            continue
        sources.append(path)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                info = json.load(handle)
        except (OSError, ValueError) as exc:
            logfunc(f'Dropbox Account Info: {path} not read ({exc})')
            continue
        relative = context.get_relative_path(path)
        for account, details in (info.items() if isinstance(info, dict) else []):
            if not isinstance(details, dict):
                continue
            data_list.append((account, details.get('path', ''), details.get('host', ''),
                              details.get('is_team', ''), details.get('subscription_type', ''), relative))
    return data_headers, data_list, '\n'.join(sources)


def wal_commit_offsets(wal):
    """The byte length of the -wal up to and including each commit frame, in order."""
    if len(wal) < 32:
        return []
    page_size = struct.unpack('>I', wal[8:12])[0]
    salts = wal[16:24]
    frame = 24 + page_size
    offsets = []
    for index in range((len(wal) - 32) // frame):
        start = 32 + index * frame
        header = wal[start:start + 24]
        if header[8:16] != salts:
            break
        if struct.unpack('>I', header[4:8])[0]:
            offsets.append(start + frame)
    return offsets


def _tree_states(path):
    """(commit number, {table: {key: value}}) as the database stood after each -wal commit.

    Works on a temporary copy; the evidence files are only read.
    """
    tables = ('local_tree', 'remote_tree', 'remote_tombstones')
    try:
        with open(path + '-wal', 'rb') as handle:
            wal = handle.read()
    except OSError:
        return []
    states = []
    work = tempfile.mkdtemp(prefix='dleapp_dropbox_')
    try:
        copy = os.path.join(work, 'nucleus.sqlite3')
        for number, length in enumerate(wal_commit_offsets(wal), 1):
            shutil.copyfile(path, copy)
            with open(copy + '-wal', 'wb') as handle:
                handle.write(wal[:length])
            db = sqlite3.connect(copy)
            try:
                state = {}
                for table in tables:
                    try:
                        state[table] = {bytes(k): bytes(v) for k, v in
                                        db.execute(f'SELECT key, value FROM {table}')}
                    except sqlite3.Error:
                        state[table] = {}
            finally:
                db.close()
            for suffix in ('-wal', '-shm'):
                if os.path.exists(copy + suffix):
                    os.remove(copy + suffix)
            states.append((number, state))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return states


def _decode_tree(raw):
    try:
        outer = pb_fields(raw)
        return _node_fields(_first(outer, 1), outer)
    except ValueError:
        return None


def _item_time(table, node):
    if node is None:
        return ''
    if table == 'remote_tree':
        return unix_time(_sub(node['outer'], 3, 2))
    return filetime(_sub(node['outer'], 2, 1))


def nucleus_history_rows(path, relative):
    states = _tree_states(path)
    if not states:
        return []
    names, parents = {}, {}
    for _, state in states:
        for table in ('local_tree', 'remote_tree'):
            for key, raw in state[table].items():
                node = _decode_tree(raw)
                if node:
                    names.setdefault(key, node['name'])
                    parents.setdefault(key, node['parent'])

    def label(key):
        if key == _ROOT_KEY:
            return '/'
        return names.get(key, key.hex() if key else '')

    rows = []
    previous = states[0][1]
    for number, state in states[1:]:
        for table in ('local_tree', 'remote_tree'):
            before, after = previous[table], state[table]
            for key in sorted(after.keys() | before.keys()):
                old = _decode_tree(before[key]) if key in before else None
                new = _decode_tree(after[key]) if key in after else None
                if old is None and new is None:
                    continue
                changes = []
                if old is None:
                    changes.append('Added')
                elif new is None:
                    changes.append('Removed')
                else:
                    if old['name'] != new['name']:
                        changes.append('Renamed')
                    if old['parent'] != new['parent']:
                        changes.append('Moved')
                    if (old['hash'], old['size']) != (new['hash'], new['size']):
                        changes.append('Content Changed')
                if not changes:
                    continue
                node = new or old
                tree = 'Local' if table == 'local_tree' else 'Remote'
                rows.append((_item_time(table, node), number, ', '.join(changes), tree, node['name'],
                             label(node['parent']),
                             old['name'] if old and new and old['name'] != new['name'] else '',
                             label(old['parent']) if old and new and old['parent'] != new['parent'] else '',
                             node['size'] if node['size'] is not None else '', key.hex(), relative))
        before, after = previous['remote_tombstones'], state['remote_tombstones']
        for key in sorted(after.keys() ^ before.keys()):
            raw = after.get(key) or before.get(key)
            try:
                when = unix_time(_sub(pb_fields(raw), 2, 2))
            except ValueError:
                when = ''
            change = 'Tombstone Added' if key in after else 'Tombstone Removed'
            rows.append((when, number, change, 'Remote', label(key), label(parents.get(key, b'')), '', '', '',
                         key.hex(), relative))
        previous = state
    logfunc(f'Dropbox Sync Engine History: {relative}: {len(states)} commits, {len(rows)} changes')
    return rows


@artifact_processor
def dropboxNucleusHistory(context):
    data_headers = (('Item Time (UTC)', 'datetime'), 'Commit', 'Change', 'Tree', 'Name', 'Parent',
                    'Previous Name', 'Previous Parent', 'Size', 'Node Key', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'nucleus.sqlite3'):
        sources.append(path)
        data_list.extend(nucleus_history_rows(path, context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(sources)


_EVENT_TYPES = (b'DesktopGenericCloggerEvent', b'ClientEventData')
_EVENT_SKIP = {'event_id', 'validation_trace_id', 'feature_session_id', 'udcl_measure_id', 'udclMeasureId',
               'validationTraceId', 'event_name', 'component', 'action_surface', 'extra'}
_CONTENT_KEYS = ('content_identifier', 'contentIdentifier', 'file_id', 'fileId')


def _pairs(data, plain=False):
    """Name/value pairs from a repeated {1: name, 2: value} message list.

    plain: the value is text (ClientEventData); otherwise it is a message holding the text in
    field 2, or nested pairs in field 7 (DesktopGenericCloggerEvent).
    """
    out = []
    for raw in data:
        if not isinstance(raw, bytes):
            continue
        try:
            pair = pb_fields(raw)
        except ValueError:
            continue
        name = _first(pair, 1, b'')
        value = _first(pair, 2, b'')
        name = name.decode('utf-8', 'replace') if isinstance(name, bytes) else str(name)
        if plain:
            out.append((name, value.decode('utf-8', 'replace') if isinstance(value, bytes) else str(value)))
            continue
        try:
            inner = pb_fields(value) if isinstance(value, bytes) else {}
        except ValueError:
            inner = {}
        if 7 in inner:
            for nested in inner[7]:
                if not isinstance(nested, bytes):
                    continue
                try:
                    out.extend(_pairs(pb_fields(nested).get(1, [])))
                except ValueError:
                    continue
        elif 2 in inner and isinstance(inner[2][0], bytes):
            out.append((name, inner[2][0].decode('utf-8', 'replace')))
        elif inner:
            out.append((name, str(next(iter(inner.values()))[0])))
        else:
            out.append((name, value.decode('utf-8', 'replace') if isinstance(value, bytes) else str(value)))
    return out


_HEADER = re.compile(rb'(?=([\x00-\xff]{4}\x00\x00\x00\x00[\x00-\xff]{4}\x00{24}))', re.S)


def batch_times(data):
    """(offset, UTC datetime) of every block header: Unix seconds (8 bytes), nanoseconds (4) and 24 zeros."""
    found = []
    for match in _HEADER.finditer(data):
        seconds, nanos = struct.unpack('<QI', match.group(1)[:12])
        if 1_000_000_000 < seconds < 4_000_000_000 and nanos < 1_000_000_000:
            found.append((match.start(), datetime.fromtimestamp(seconds, tz=timezone.utc)
                          + timedelta(microseconds=nanos // 1000)))
    return found


def _batch_time(headers, offset):
    """The time of the last header before offset, or ''."""
    low, high = 0, len(headers)
    while low < high:
        mid = (low + high) // 2
        if headers[mid][0] < offset:
            low = mid + 1
        else:
            high = mid
    return headers[low - 1][1] if low else ''


def client_event_rows(path, relative):
    with open(path, 'rb') as handle:
        data = handle.read()
    headers = batch_times(data)
    rows = []
    for type_name in _EVENT_TYPES:
        for match in re.finditer(re.escape(type_name), data):
            start = match.start()
            if data[start - 8:start] != struct.pack('<Q', len(type_name)):
                continue
            length_at = match.end()
            length = struct.unpack('<Q', data[length_at:length_at + 8])[0]
            payload = data[length_at + 8:length_at + 8 + length]
            if length == 0 or len(payload) != length:
                continue
            try:
                fields = pb_fields(payload)
            except ValueError:
                continue
            if type_name == b'DesktopGenericCloggerEvent':
                stream = _first(fields, 1, b'').decode('utf-8', 'replace')
                pairs = _pairs(fields.get(4, []))
                event = dict(pairs).get('event_name', '')
                surface = dict(pairs).get('action_surface', '')
                own_time = ''
            else:
                stream = 'ClientEventData'
                action = _sub(fields, 4, 1)
                obj = _sub(fields, 4, 2)
                event = '.'.join(x.decode('utf-8', 'replace') for x in (action, obj) if isinstance(x, bytes))
                pairs = _pairs(fields.get(8, []), plain=True)
                surface = _first(fields, 10, b'')
                surface = surface.decode('utf-8', 'replace') if isinstance(surface, bytes) else ''
                own_time = unix_time(_sub(fields, 2, 1))
            values = dict(pairs)
            component = values.get('component', '')
            content = next((values[k] for k in _CONTENT_KEYS if values.get(k)), '')
            node_key = file_id_key(content[3:]) if content.startswith('id:') else ''
            details = '; '.join(f'{k}={v}' for k, v in pairs if v and k not in _EVENT_SKIP
                                and k not in _CONTENT_KEYS)
            rows.append((own_time, _batch_time(headers, start), event, component, surface, content, node_key, details,
                         type_name.decode(), stream, relative))
    rows.sort(key=lambda r: str(r[0] or r[1]))
    return rows


@artifact_processor
def dropboxClientEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Batch Time (UTC)', 'datetime'), 'Event Name', 'Component', 'Surface', 'Content ID', 'Node Key',
                    'Details', 'Record Type', 'Stream', 'Source File')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) != 'store':
            continue
        sources.append(path)
        try:
            data_list.extend(client_event_rows(path, context.get_relative_path(path)))
        except OSError as exc:
            logfunc(f'Dropbox Client Events: {path} not read ({exc})')
    return data_headers, data_list, '\n'.join(sources)


_PICKLE_HEAD = b'\x80\x02c_codecs\nencode\nq\x00X'
_PICKLE_TAIL = b'q\x01X\x06\x00\x00\x00latin1q\x02\x86q\x03Rq\x04.'
_THUMB_PATH = re.compile(r'^tpng(.*)_(\d+)$', re.S)


def thumbnail_bytes(blob):
    """The bytes a pickled _codecs.encode(text, 'latin1') call holds, without unpickling, or None."""
    if not isinstance(blob, bytes) or not blob.startswith(_PICKLE_HEAD):
        return None
    start = len(_PICKLE_HEAD) + 4
    length = struct.unpack('<I', blob[len(_PICKLE_HEAD):start])[0]
    if blob[start + length:] != _PICKLE_TAIL:
        return None
    try:
        return blob[start:start + length].decode('utf-8').encode('latin-1')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None


@artifact_processor
def dropboxThumbnails(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Thumbnail', 'media'), 'Path', 'Size',
                    'File Modified (as stored)', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'icon.db'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            rows = _rows(db, 'SELECT created_time, file_path, file_mtime, image FROM path_icon_table '
                             'ORDER BY created_time', 'Thumbnails')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        for created, file_path, mtime, image in rows:
            match = _THUMB_PATH.match(file_path or '')
            shown, size = (match.group(1), match.group(2)) if match else (file_path or '', '')
            png = thumbnail_bytes(image)
            media = check_in_embedded_media(path, png, name=os.path.basename(shown.replace('\\', '/'))) \
                if png else ''
            data_list.append((unix_time(created), media, shown, size, mtime if mtime is not None else '',
                              relative))
    return data_headers, data_list, '\n'.join(sources)


def _all_trees(db):
    return tuple(_tree(db, t) for t in ('local_tree', 'remote_tree', 'synced_tree'))


@artifact_processor
def dropboxUploadRecords(context):
    data_headers = (('Time (UTC)', 'datetime'), ('Token Time (UTC)', 'datetime'), 'Path', 'Block Hash',
                    'User ID', 'Namespace ID', 'Token Field 5 (as stored)', 'Node Key', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'nucleus.sqlite3'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            trees = _all_trees(db)
            rows = _rows(db, 'SELECT fileid, block_hash, ts, token FROM file_block_upload_tokens ORDER BY ts',
                         'Upload Records')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        for fileid, block_hash, ts, token in rows:
            key = bytes(fileid) if fileid is not None else b''
            inner = {}
            try:
                outer = pb_fields(bytes(token)) if token is not None else {}
                inner = pb_fields(_sub(outer, 1, 1) or b'')
            except ValueError:
                pass
            data_list.append((unix_time(ts), unix_time(_first(inner, 2)),
                              _path(key, trees) if key else '',
                              bytes(block_hash).hex() if block_hash is not None else '',
                              _first(inner, 3, ''), _first(inner, 4, ''), _first(inner, 5, ''), key.hex(),
                              relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxClientInfo(context):
    data_headers = ('Key', 'Value', ('Time (UTC)', 'datetime'), 'Source File')
    data_list, sources = [], []
    found = sorted({str(p) for p in context.get_files_found()})
    for path in found:
        if os.path.basename(path) != 'boot_marker.dbx' or os.path.isdir(path):
            continue
        sources.append(path)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                marker = json.load(handle)
        except (OSError, ValueError) as exc:
            logfunc(f'Dropbox Client Info: {path} not read ({exc})')
            continue
        relative = context.get_relative_path(path)
        if 'last_boot_time' in marker:
            data_list.append(('Last Boot Time', marker['last_boot_time'], unix_time(marker['last_boot_time']),
                              relative))
        if 'boot_count' in marker:
            data_list.append(('Boot Count (as stored)', marker['boot_count'], '', relative))
    for path in _databases(context, 'nucleus.sqlite3'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            config = _rows(db, 'SELECT value FROM config WHERE key = 28', 'Client Info')
            remote = _rows(db, 'SELECT value FROM remote_tree', 'Client Info')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        for (value,) in config:
            try:
                version = _first(pb_fields(bytes(value)), 1, b'')
            except ValueError:
                continue
            if isinstance(version, bytes):
                data_list.append(('OS Version', version.decode('utf-8', 'replace'), '', relative))
        users = set()
        for (value,) in remote:
            try:
                user = _sub(pb_fields(bytes(value)), 3, 1)
            except ValueError:
                continue
            if isinstance(user, int):
                users.add(user)
        for user in sorted(users):
            data_list.append(('User ID', user, '', relative))
    for path in _databases(context, 'sync_history.db'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            rows = _rows(db, 'SELECT DISTINCT server_path FROM sync_history', 'Client Info')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        spaces = {sp.split(':', 1)[0] for (sp,) in rows if sp and ':' in sp}
        for space in sorted(spaces):
            data_list.append(('Namespace ID', space, '', relative))
    return data_headers, data_list, '\n'.join(sources)
