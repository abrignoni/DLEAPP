"""Dropbox desktop client for Windows: account info, the linked account from the encrypted
config.dbx, sync history, storage file list, the sync engine (Nucleus) trees and their -wal
history, upload records, client events and the thumbnail cache, for DLEAPP.

Author: @charpy4n6, @AlexisBrignoni, Claude.
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
        "notes": "Reads info.json in the Dropbox folder of AppData/Local on Windows, one row per top-level key (only personal on the private sample). Path, Host, Is Team and Subscription Type are path, host, is_team and subscription_type as stored; no published definition of host was found and it is not interpreted. On the private sample the file held one personal account. The account email is not in this file; it is in the encrypted config.dbx, which Dropbox Linked Account reads. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/AppData/Local/Dropbox/info.json',),
        "output_types": ["standard"],
        "artifact_icon": "user",
    },
    "dropboxLinkedAccount": {
        "name": "Dropbox Linked Account",
        "description": "The account each Dropbox desktop instance is linked to, read from the instance's "
                       "encrypted config.dbx and the encrypted instance.dbx, decrypted with the key file "
                       "Dropbox keeps beside them.",
        "author": "@AlexisBrignoni, @charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "PyCryptodome",
        "category": "Dropbox",
        "notes": "Reads config.dbx in each Dropbox instance folder (instance1 and so on) and instance.dbx in instance_db. Both are encrypted SQLite databases. The key comes from the ks_Client file in the same folder (ks_Client1 beside instance1, ks_Client beside instance_db). That file is a version (0), a payload length (16), the payload, and an HMAC-MD5 of the bytes before it; the HMAC verifies under the Dropbox HMAC key published in decwindbx, and the database key is PBKDF2-HMAC-SHA1 of the payload with the published salt and 1066 iterations (Reference: decwindbx, https://github.com/dfirfpi/decwindbx/blob/db2e0f19ae03424b299d791178f33f4d0222ab0f/dbx-key-win-live.py#L62-L79 and #L89-L103). In decwindbx the payload is DPAPI-protected and read from the registry; here it is used as stored, as a 2021 comment on that project describes for the registry value Client-p (Reference: https://github.com/dfirfpi/decwindbx/issues/1#issuecomment-808895040). No DPAPI master key or Windows password is needed. Each page is AES-128-OFB over all but its 12 reserved bytes, which hold the page's nonce, with the page number (4 bytes, little-endian) and that nonce as the IV; bytes 16 to 23 of the first page are stored in the clear. That layout was established on the private sample, not from a published source: config.dbx, instance.dbx and photo.dbx decrypt with it and pass SQLite's integrity_check, and AES-128-CTR with the same IV does not give a database. A unit test round-trips a database through an encryptor written in the test as the inverse of the reader. The decrypted copy is written to a temporary file and deleted after the query; the evidence files are read only. One row is reported per decrypted config.dbx. First Linked (UTC) and Last Successful Startup (UTC) are first_link_ts and SUCCESSFUL_STARTUP_TS read as Unix seconds. Client Version is SUCCESSFUL_STARTUP; the label rests on the key's name and the shape of its value; the same string appears in events/store as the desktop app version pair of several Dropbox Client Events rows. Email, User Display Name, Account ID, Display Name, Dropbox Folder, Host ID and Root Namespace ID are the email, userdisplayname, account_id, displayname, dropbox_path, host_id and root_ns keys as stored, and User ID is sync_root_account_uid. On the private sample Account ID equals, ignoring case, the percent-encoded dbid that names a folder under AppData/Roaming/Dropbox/Partitions, User ID equals the uid instance.dbx records for the instance, the User ID of Dropbox Upload Records and Dropbox Client Info, and Root Namespace ID equals their Namespace ID. Business Name is business_name from instance.dbx and Team ID is team_id; on the private sample, a personal account, Business Name held no value and Team ID held no value. The oauth_refresh_token_v2 and client_key_pair keys are not reported, because they are credentials; the run log names each credential key it leaves out. The other config keys, the shared_config table of instance.dbx (2 rows on the sample) and photo.dbx (a config table of 3 rows; its photo import tables empty on the sample) are not reported. A config.dbx with no ks_Client file beside it, as older clients kept the key in the registry, is logged and not decrypted (not exercised on the sample). The macOS client is not covered. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/config.dbx', '*/Dropbox/instance*/ks_Client*',
                  '*/Dropbox/instance_db/instance.dbx', '*/Dropbox/instance_db/ks_Client*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user-check",
    },
    "dropboxSyncHistory": {
        "name": "Dropbox Sync History",
        "description": "Sync events the Dropbox desktop client kept in sync_history.db: the time, whether a file "
                       "or folder, the event type and direction, the local and server paths and the file ID.",
        "author": "@charpy4n6, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads the sync_history table of sync_history.db, with its -wal when present, in each instance folder of the Dropbox client, one row per table row. Time (UTC) is timestamp read as Unix seconds; on the private sample each upload row's time fell 0 to 2 seconds after the sync engine's remote_tree field 3.2 for the same node key on 31 of 33 upload rows, and 396 and 564 seconds after it on the other two, the 564 second row being the one move. Item Type, Event Type and Direction are event_type, file_event_type and direction as stored (file or directory; add, move or delete; upload or download on the private sample); their meaning is not established from a published source. On the private sample a file the tester renamed appeared as an add under its new name. File ID is file_id as stored: base64url of the 16-byte node key that nucleus.sqlite3 uses, decoded in Node Key so rows can be matched to Dropbox Sync Engine Items; all 38 decoded on the private sample, 34 match a node in the trees, 3 a remote tombstone, and one, a deleted folder, neither. Server Path is server_path as stored, a number, a colon and the path, and is empty on the one directory delete row; the number equals Root Namespace ID in Dropbox Linked Account. Other User (as stored) is other_user, and Other User (as stored) held 0 on all 38 rows. Thumbnail is the image icon.db, in the same instance folder, holds for the row's local path, matched on that path lowercased as icon.db stores it (see Dropbox Thumbnails); it shows the file as the thumbnail was made, which need not be its content at the row's time. 21 of 38 rows have one on the private sample. The table appears to hold recent events only; a missing event is not evidence the action did not happen. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/sync_history.db*', '*/Dropbox/instance*/icon.db*'),
        "output_types": ["standard"],
        "artifact_icon": "refresh-cw",
    },
    "dropboxStorageFiles": {
        "name": "Dropbox Storage Files",
        "description": "Files and folders the Dropbox desktop client listed in sync_and_storage.db: the path, "
                       "size, modified time, folder flag, offline availability and online-only counters.",
        "author": "@charpy4n6, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads the storage_files table of sync_and_storage.db, with its -wal when present, in each instance folder of the Dropbox client, one row per table row. Modified (UTC) is last_modified read as Unix milliseconds, and Online Files Modified (UTC) is online_files_modified_time read the same way when not 0; on the private sample 3 rows held the text null there and are shown empty. Path, File Name, Size, Blocks, Is Folder, Available Offline, File Type, Parent Path, Online Files Size, Has Online-Only Files and Has Offline Files are fq_path, filename, size, blocks, is_dir, is_available_offline, file_type, parent_path, online_files_size, has_online_only_files and has_offline_files as stored. On the private sample the table held 40 rows, is_available_offline was 0 on 5 files and 1 on the rest, and Modified equalled, to the second, Remote Modified (UTC) in Dropbox Sync Engine Items for all 36 files. Thumbnail is the image icon.db, in the same instance folder, holds for the row's local path, matched on that path lowercased as icon.db stores it (see Dropbox Thumbnails); it shows the file as the thumbnail was made, which need not be its content at the row's time. 24 of 40 rows have one on the private sample. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/sync_and_storage.db*', '*/Dropbox/instance*/icon.db*'),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
    },
    "dropboxNucleusItems": {
        "name": "Dropbox Sync Engine Items",
        "description": "Files and folders in the local, remote and synced trees of the Dropbox sync engine "
                       "database (nucleus.sqlite3), and its remote tombstones: the path, size, content hash, "
                       "local and remote times, and the local file reference value.",
        "author": "@charpy4n6, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads local_tree, remote_tree, synced_tree and remote_tombstones in sync/nucleus.sqlite3, with its -wal, in each instance folder of the Dropbox client, one row per node key, the three trees joined on the key, and one row per tombstone. Each value is an undocumented protobuf; the field numbers were worked out from the private sample and are reported as such. Dropbox describes the engine as keeping a Remote Tree, the latest state of the account's Dropbox in the cloud, a Local Tree, the last observed state on disk, and a Synced Tree (Reference: https://dropbox.tech/infrastructure/-testing-our-new-sync-engine). Field 1 of a local_tree or remote_tree value, and field 2 of a synced_tree value, holds the node: 1 the node key, 2 the parent key, 3 the name and 5.1 the content hash (1) and size (2). Kind is File when the node has field 5 and Folder when it has field 6; otherwise it is blank. On the private sample 32 nodes were File, 5 Folder (the root among them) and 4 blank; the 4 blank nodes carry a field 11 in place of field 5 in the local tree, and each is a file storage_files lists with is_available_offline 0. Path is built from the names up the parent keys of whichever tree holds the node, preferring local; the root key is sixteen 0xFF bytes. Local Modified (UTC) is local_tree field 2.1 read as a Windows FILETIME; on the private sample it equalled, to the second, remote_tree field 2 read as Unix seconds (Remote Modified (UTC)) on 36 of the 40 nodes with both set; the other 4 were folders, whose local time was later. Remote Field 3.2 (UTC) is remote_tree field 3.2 read as Unix seconds; see Dropbox Sync History for how it compares with the upload times; its meaning is not established. Local File Reference is local_tree field 3 as stored, which on the private sample had the form of an NTFS file reference (low 48 bits the MFT entry, high 16 the sequence), split into those two parts; the MFT was not available to confirm it. Content Hash is shown as hex; on the private sample it equals the one block_hash file_block_upload_tokens holds for each of the 20 files under 4 MiB that have an upload record, and one of the two it holds for each of the 9 larger files, and 3 files have no upload record; its algorithm is not established. In Local, In Remote and In Synced say which tables held the key; on the private sample In Local, In Remote and In Synced were identical on all 44 rows, Yes on the 41 tree rows and No on the 3 tombstones. A tombstone row has only the key and Tombstone Time (UTC), field 2.2 read as Unix seconds; on the private sample the 3 tombstones shared one time, 24 seconds after the sync_history delete of a folder, their keys are in no tree, each key is the File ID of a sync_history file add download row, and the 3 local paths those rows name are in the trees under other keys (see Dropbox Sync Engine History). Thumbnail is the icon.db image for the local path, the path info.json gives for the Dropbox folder joined with Path; 24 of the 41 tree rows have one on the private sample. Not reported: remote_overlay, config and periodic_jobs, file_block_upload_tokens (see Dropbox Upload Records), and deleted_files, commit_intents, reconstruct_intents and the three migration tables, which held no rows on the private sample; deleted_files has identifier, prune_after, dirtied_on, original_data and last_observed_stat columns and is a candidate for a later artifact once a sample holds rows in it. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*', '*/Dropbox/instance*/icon.db*',
                  '*/AppData/Local/Dropbox/info.json'),
        "output_types": ["standard"],
        "artifact_icon": "git-branch",
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
        "notes": "Reads sync/nucleus.sqlite3 and its -wal. The -wal frames are read up to the first frame whose salts differ from the header's, and the database is opened, in a temporary copy, as it stood after each commit frame; local_tree, remote_tree and remote_tombstones are compared between consecutive commits, decoded as Dropbox Sync Engine Items describes. One row per change. Commit is the commit's number in -wal order; no wall-clock time is stored per commit, so Item Time (UTC) is a time from the changed record itself: for a remote item remote_tree field 3.2, for a local item local_tree field 2.1, for a tombstone field 2.2, each read as Dropbox Sync Engine Items reads it. Change is Added, Removed, Renamed (field 3 differs), Moved (parent key differs), Content Changed (content hash or size differs) or Tombstone Added/Removed; a change of other fields only is not reported. On the private sample the -wal held 1,929 frames and 1,634 commits, 103 of which changed a reported field, giving 149 rows, and the rows matched what the tester records doing: three files removed from both trees with tombstones written and present again under new node keys (deleted, then restored from the trash), a folder removed with a tombstone that was itself removed later (permanently deleted online), one file renamed, one file moved into another folder, and a folder and three files appearing in remote_tree before local_tree, which the tester records as uploaded from the web; one of the three also has a sync_history download row. The rename's old name was not found in the other files this module reads. That those items reached the remote tree first is recorded only here; the items themselves are listed in Dropbox Storage Files and Dropbox Sync Engine Items. What this shows depends on how much of the -wal remains: a checkpoint moves pages into the database and later commits overwrite the -wal, so earlier changes may be gone; an absent change is not evidence it did not happen. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*',),
        "output_types": ["standard"],
        "artifact_icon": "clock",
    },
    "dropboxClientEvents": {
        "name": "Dropbox Client Events",
        "description": "Usage events the Dropbox desktop client wrote to its events/store file: the time, the event name, the component and surface, and the event's other fields, among them shared link events naming a file ID.",
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads events/store in the Dropbox folder of AppData/Local. The file is undocumented; its layout was worked out from the private sample. Blocks begin with a header of Unix seconds (8 bytes), nanoseconds (4 bytes) and 24 zero bytes; Batch Time (UTC) is the time of the last such header before the record, which on the private sample was not written before every record, so several records share one Batch Time and it is not the record's own time. Each record has a length-prefixed type name and a length-prefixed protobuf. Two type names were found: DesktopGenericCloggerEvent, whose protobuf holds the stream name (field 1) and name/value pairs (field 4, the 'extra' pair holding nested pairs), and ClientEventData, whose protobuf holds a time (field 2: seconds and nanoseconds, given as Event Time (UTC)), action and object (field 4), name/value pairs (field 8) and a surface (field 10). Event Name is the event_name pair, or action.object for ClientEventData. Content ID is a content_identifier or file_id pair as stored; where it is id: and base64url of a 16-byte value, Node Key gives that value in hex for matching to Dropbox Sync Engine Items. Details are the remaining non-empty pairs, name=value, except event, trace and session IDs. The same event can appear once per stream (all-events and user-events) and again as ClientEventData; all are reported, with Stream naming which. On the private sample: 3,384 DesktopGenericCloggerEvent and 678 ClientEventData records, so Event Time (UTC) leads the table and is filled on the 678 ClientEventData rows only, with Batch Time filled on the others; 45 of them with a Node Key. The 45 rows with a Node Key are share modal, manage access, shared link and sharing entry point events, all naming one file in the trees. Other events seen include preferences tab views, selective sync window events and share invite events. These are the client's own telemetry: a record says the client logged an interface event, not what the person intended, and records already sent to Dropbox may have been removed from the file. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/AppData/Local/Dropbox/events/store',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
    },
    "dropboxThumbnails": {
        "name": "Dropbox Thumbnails",
        "description": "Thumbnails the Dropbox desktop client cached in icon.db for files in the Dropbox folder, with the path they were made for and the row's created_time.",
        "author": "@charpy4n6, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "Reads path_icon_table in icon.db, with its -wal when present, in each instance folder of the Dropbox client, one row per table row. Each image column holds a Python pickle of _codecs.encode(<text>, 'latin1'); it is not unpickled, which would run code: the pickle opcodes are checked to be exactly that call and the text is read and encoded to bytes, which on every row of the private sample were a PNG. Created (UTC) is created_time read as Unix seconds. Path is file_path after its leading 'tpng' and before its trailing _<size>, as stored (lower case on the private sample); Size is that number, and Size held 256 on all 24 rows, the longest side of every image. File Modified is file_mtime as stored (empty on every row of the private sample). On the private sample the 24 rows included a picture and the copy the tester edited, whose thumbnails show the same picture mirrored left to right, two rows hold the same image, and every path is in the sync engine trees; whether a row outlives its file was not tested. The same images are shown inline in Dropbox Sync History, Dropbox Storage Files and Dropbox Sync Engine Items. ext_icon_table (generic icons per file extension, 2 rows on the sample) is not reported. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/icon.db*',),
        "output_types": ["standard"],
        "artifact_icon": "image",
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
        "notes": "Reads file_block_upload_tokens (fileid, block_hash, ts, token) in sync/nucleus.sqlite3, with its -wal, one row per table row. Time (UTC) is ts read as Unix seconds. Node Key is fileid; Path is built from the sync engine trees as Dropbox Sync Engine Items builds it. Block Hash is block_hash in hex. The token is an undocumented protobuf; field 1.1 holds the block hash (1, equal to block_hash on all 38 rows of the private sample), a time (2, Token Time (UTC), read as Unix seconds), a user ID (3), a namespace ID (4) and a value (5), reported as stored; Token Field 5 held 2 on every row of the private sample. Field 1.2, a text token, is not reported. On the private sample all 38 rows named a node in local_tree, 35 rows were 1 to 9 seconds before the sync_history upload of the same node and 3 rows 396 to 565 seconds before it, Token Time was 60 or 61 seconds before Time on every row, User ID equalled the User ID in Dropbox Linked Account and remote_tree field 3.1, and Namespace ID equalled its Root Namespace ID, the number at the start of every sync_history server_path. One file can have more than one block; a row does not by itself establish that the whole file was uploaded. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/Dropbox/instance*/sync/nucleus.sqlite3*',),
        "output_types": ["standard"],
        "artifact_icon": "upload-cloud",
    },
    "dropboxClientInfo": {
        "name": "Dropbox Client Info",
        "description": 'Values about the Dropbox desktop client and the computer: the last_boot_time value from boot_marker.dbx, a value of config row 28 in nucleus.sqlite3 shaped like a Windows version and build, and the user and namespace IDs found in the sync engine and sync history.',
        "author": "@charpy4n6, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "Dropbox",
        "notes": "One row per value; Time (UTC) leads the table and is filled on the Last Boot Time row only. Last Boot Time (UTC) is last_boot_time in boot_marker.dbx, a JSON file despite its name, read as Unix seconds, and Boot Count its boot_count, as stored; on the private sample last_boot_time was later than every Sync History, Thumbnails and Upload Records time, and boot_count was 0 although the client had started, so on this sample it did not count starts. OS Version is field 1 of config row 28 in nucleus.sqlite3, as stored; on the private sample it held a value shaped like a Windows major version and build number, and the label rests on that shape. User ID lists the distinct remote_tree field 3.1 values and Namespace ID the distinct numbers before the colon in sync_history server_path; on the private sample they equal User ID and Root Namespace ID in Dropbox Linked Account, which reads them from config.dbx. The account email and name are in config.dbx; see Dropbox Linked Account. Fields were mapped from a private sample, the tester's own Windows install of the client with one personal account, which has no corpus key; the counts here are from a capture of it in which the client had last started in October 2026.",
        "paths": ('*/AppData/Local/Dropbox/boot_marker.dbx', '*/Dropbox/instance*/sync/nucleus.sqlite3*',
                  '*/Dropbox/instance*/sync_history.db*'),
        "output_types": ["standard"],
        "artifact_icon": "info",
    },
}

import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import sqlite3
import struct
import tempfile
from datetime import datetime, timedelta, timezone

from pathlib import Path

from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media, logfunc,
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


class _Thumbnails:
    """The icon.db thumbnails of one instance folder, found by the local path a row names.

    icon.db keys a thumbnail on 'tpng', the lowercased local path and '_<size>'; the largest size
    is used. The match is on that recorded path, never on a file name alone.
    """

    def __init__(self, icon_db, images):
        self._icon_db = icon_db
        self._images = images
        self._cache = {}

    def media(self, local_path):
        key = (local_path or '').lower()
        if not self._icon_db or key not in self._images:
            return ''
        if key not in self._cache:
            self._cache[key] = check_in_embedded_media(self._icon_db, self._images[key]) or ''
        return self._cache[key]


def _thumbnails(context, instance):
    """The thumbnails of the icon.db in an instance folder, or an empty index."""
    icon_db = next((p for p in _databases(context, 'icon.db') if os.path.dirname(p) == instance), None)
    best = {}
    if icon_db:
        db = open_sqlite_db_readonly(icon_db)
        if db is not None:
            try:
                rows = _rows(db, 'SELECT file_path, image FROM path_icon_table', 'Thumbnails')
            finally:
                db.close()
            for file_path, image in rows:
                match = _THUMB_PATH.match(file_path or '')
                png = thumbnail_bytes(image) if match else None
                if png and (match.group(1) not in best or int(match.group(2)) > best[match.group(1)][0]):
                    best[match.group(1)] = (int(match.group(2)), png)
    return _Thumbnails(icon_db, {path: png for path, (_, png) in best.items()})


def _dropbox_folders(context, instance):
    """The local Dropbox folder paths info.json lists, for the instance folder's parent."""
    folders = []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.basename(path) == 'info.json' and os.path.dirname(path) == os.path.dirname(instance):
            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    info = json.load(handle)
            except (OSError, ValueError):
                continue
            folders.extend(d['path'] for d in (info.values() if isinstance(info, dict) else [])
                           if isinstance(d, dict) and isinstance(d.get('path'), str))
    return folders


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
                    'Name', 'Kind', 'Size', ('Thumbnail', 'media'), 'Content Hash', 'In Local', 'In Remote',
                    'In Synced',
                    'Tombstone', 'Local File Reference (as stored)', 'MFT Entry (if NTFS reference)',
                    'MFT Sequence (if NTFS reference)', 'Node Key',
                    'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'nucleus.sqlite3'):
        sources.append(path)
        instance = os.path.dirname(os.path.dirname(path))
        icons = _thumbnails(context, instance)
        folders = _dropbox_folders(context, instance)
        for row in nucleus_rows(path, context.get_relative_path(path)):
            media = next((m for m in (icons.media(f + row[4].replace('/', '\\')) for f in folders) if m), '') \
                if row[4] else ''
            data_list.append(row[:8] + (media,) + row[8:])
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxSyncHistory(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Item Type', 'Event Type', 'Direction', 'Local Path',
                    ('Thumbnail', 'media'), 'Server Path', 'Other User (as stored)', 'File ID', 'Node Key',
                    'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'sync_history.db'):
        icons = _thumbnails(context, os.path.dirname(path))
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
                              icons.media(local_path), server_path or '',
                              other if other is not None else '', file_id or '',
                              file_id_key(file_id), relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def dropboxStorageFiles(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Online Files Modified (UTC)', 'datetime'), 'Path',
                    ('Thumbnail', 'media'), 'File Name', 'Size', 'Blocks', 'Is Folder', 'Available Offline',
                    'File Type', 'Parent Path',
                    'Online Files Size', 'Has Online-Only Files', 'Has Offline Files', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'sync_and_storage.db'):
        icons = _thumbnails(context, os.path.dirname(path))
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
            media = icons.media(row[2])
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
    data_headers = (('Time (UTC)', 'datetime'), 'Key', 'Value', 'Source File')
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
            data_list.append((unix_time(marker['last_boot_time']), 'Last Boot Time', marker['last_boot_time'],
                              relative))
        if 'boot_count' in marker:
            data_list.append(('', 'Boot Count (as stored)', marker['boot_count'], relative))
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
                data_list.append(('', 'OS Version', version.decode('utf-8', 'replace'), relative))
        users = set()
        for (value,) in remote:
            try:
                user = _sub(pb_fields(bytes(value)), 3, 1)
            except ValueError:
                continue
            if isinstance(user, int):
                users.add(user)
        for user in sorted(users):
            data_list.append(('', 'User ID', user, relative))
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
            data_list.append(('', 'Namespace ID', space, relative))
    return data_headers, data_list, '\n'.join(sources)


# Constants of the Dropbox keystore, as published in dfirfpi/decwindbx (see dropboxLinkedAccount notes).
_KS_HMAC_KEY = bytes.fromhex('d114a55212655f74bd772e37e64aee9b')
_KS_APP_KEY = bytes.fromhex('0d638c092e8b82fc452883f95f355b8e')
_KS_ITERATIONS = 1066
# Config keys holding credentials, never reported.
_SECRET_CONFIG_KEYS = ('oauth', 'token', 'secret', 'key_pair', 'password')


def database_key(ks_path):
    """The 16-byte database key from a ks_Client file, or None.

    The file is a version (u32), a payload length (u32), the payload, and an HMAC-MD5 of everything
    before it under the published Dropbox HMAC key. The payload is the user key in the clear, and
    the database key is PBKDF2-HMAC-SHA1 of it.
    """
    try:
        with open(ks_path, 'rb') as handle:
            blob = handle.read()
    except OSError as exc:
        logfunc(f'Dropbox Linked Account: key file not read ({exc.__class__.__name__})')
        return None
    if len(blob) < 8:
        return None
    version, length = struct.unpack_from('<II', blob)
    if version != 0 or len(blob) != 8 + length + 16:
        logfunc(f'Dropbox Linked Account: {os.path.basename(ks_path)} has version {version} and '
                f'{len(blob)} bytes, a layout this module does not read')
        return None
    if not hmac.compare_digest(hmac.new(_KS_HMAC_KEY, blob[:-16], hashlib.md5).digest(), blob[-16:]):
        logfunc(f'Dropbox Linked Account: the HMAC of {os.path.basename(ks_path)} does not verify')
        return None
    return hashlib.pbkdf2_hmac('sha1', blob[8:8 + length], _KS_APP_KEY, _KS_ITERATIONS, 16)


def decrypt_dbx(path, key):
    """The plaintext of an encrypted .dbx SQLite database, or None.

    Each page is AES-128-OFB over everything but the reserved bytes at its end, which hold the
    page's nonce; the IV is the page number (u32 little-endian) followed by that nonce. Bytes 16
    to 23 of the first page are stored in the clear.
    """
    try:
        from Crypto.Cipher import AES  # pylint: disable=import-outside-toplevel
    except ImportError:
        logfunc('Dropbox Linked Account: PyCryptodome is not installed, so .dbx files are not decrypted')
        return None
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
    except OSError as exc:
        logfunc(f'Dropbox Linked Account: {os.path.basename(path)} not read ({exc.__class__.__name__})')
        return None
    if data[:16] == b'SQLite format 3\x00':
        return data
    if len(data) < 100:
        return None
    page_size = struct.unpack('>H', data[16:18])[0]
    page_size = 65536 if page_size == 1 else page_size
    reserved = data[20]
    if page_size < 512 or page_size & (page_size - 1) or reserved < 12 or len(data) % page_size:
        logfunc(f'Dropbox Linked Account: {os.path.basename(path)} does not have the page layout of an '
                f'encrypted .dbx (page size {page_size}, {reserved} reserved bytes, {len(data)} bytes)')
        return None
    out = bytearray()
    for number in range(len(data) // page_size):
        page = data[number * page_size:(number + 1) * page_size]
        iv = struct.pack('<I', number + 1) + page[page_size - 12:]
        plain = bytearray(AES.new(key, AES.MODE_OFB, iv=iv).decrypt(page[:page_size - reserved]))
        plain += page[page_size - reserved:]
        if number == 0:
            plain[16:24] = page[16:24]
        out += plain
    if out[:16] != b'SQLite format 3\x00':
        logfunc(f'Dropbox Linked Account: {os.path.basename(path)} did not decrypt to a SQLite database '
                'with the key beside it')
        return None
    return bytes(out)


def read_decrypted(data, query):
    """Run a query over a decrypted database; the temporary copy is removed afterwards."""
    folder = tempfile.mkdtemp(prefix='dleapp_dropbox_')
    try:
        path = os.path.join(folder, 'decrypted.sqlite')
        with open(path, 'wb') as handle:
            handle.write(data)
        db = sqlite3.connect(Path(path).as_uri() + '?mode=ro', uri=True)
        try:
            return db.execute(query).fetchall()
        finally:
            db.close()
    except sqlite3.Error as exc:
        logfunc(f'Dropbox Linked Account: a decrypted database was not read ({exc})')
        return []
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def _key_beside(context, folder):
    return next((p for p in sorted(str(f) for f in context.get_files_found())
                 if os.path.dirname(p) == folder and os.path.basename(p).startswith('ks_Client')
                 and os.path.isfile(p)), None)


def _decrypted(context, path):
    """(rows of key/value or instance query input, key file) for a .dbx, or (None, key file)."""
    ks_path = _key_beside(context, os.path.dirname(path))
    if not ks_path:
        logfunc(f'Dropbox Linked Account: no ks_Client key file beside {context.get_relative_path(path)}; '
                'older clients keep the key in the registry')
        return None, None
    key = database_key(ks_path)
    return (decrypt_dbx(path, key) if key else None), ks_path


def _instance_label(folder):
    parts = Path(folder).parts
    users = [i for i, part in enumerate(parts) if part.lower() == 'users']
    user = parts[users[-1] + 1] if users and users[-1] + 1 < len(parts) else ''
    return f'{user}\\{parts[-1]}' if user else parts[-1]


@artifact_processor
def dropboxLinkedAccount(context):
    data_headers = (('First Linked (UTC)', 'datetime'), ('Last Successful Startup (UTC)', 'datetime'),
                    'Email', 'User Display Name', 'Account ID', 'User ID', 'Display Name', 'Dropbox Folder',
                    'Client Version', 'Host ID', 'Root Namespace ID', 'Business Name', 'Team ID',
                    'Instance')
    data_list, sources = [], []
    businesses = {}
    for path in _databases(context, 'instance.dbx'):
        data, ks_path = _decrypted(context, path)
        if data is None:
            continue
        sources.extend([path, ks_path])
        for appdata_path, business_name in read_decrypted(
                data, 'SELECT appdata_path, business_name FROM instance'):
            if appdata_path:
                name = str(appdata_path).replace('/', '\\').rstrip('\\').rsplit('\\', 1)[-1]
                businesses[(os.path.dirname(os.path.dirname(path)), name)] = business_name or ''
    for path in _databases(context, 'config.dbx'):
        data, ks_path = _decrypted(context, path)
        if data is None:
            continue
        config = dict(read_decrypted(data, 'SELECT key, value FROM config'))
        if not config:
            continue
        sources.extend([path, ks_path])
        folder = os.path.dirname(path)
        data_list.append((
            unix_time(config.get('first_link_ts')), unix_time(config.get('SUCCESSFUL_STARTUP_TS')),
            config.get('email') or '', config.get('userdisplayname') or '', config.get('account_id') or '',
            config.get('sync_root_account_uid') or '', config.get('displayname') or '',
            config.get('dropbox_path') or '', config.get('SUCCESSFUL_STARTUP') or '',
            config.get('host_id') or '', config.get('root_ns') or '',
            businesses.get((os.path.dirname(folder), os.path.basename(folder)), ''),
            config.get('team_id') or '', _instance_label(folder)))
        secrets = sorted(k for k in config if any(word in k.lower() for word in _SECRET_CONFIG_KEYS))
        if secrets:
            logfunc(f'Dropbox Linked Account: {len(secrets)} credential entries of '
                    f'{_instance_label(folder)}/config.dbx are not reported: {", ".join(secrets)}')
    return data_headers, data_list, '\n'.join(dict.fromkeys(p for p in sources if p))
