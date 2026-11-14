"""Rocket.Chat Desktop (Electron) data, for DLEAPP: rooms and subscriptions cached in IndexedDB, and the configured servers.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "rocketChatRooms": {
        "name": "Rocket.Chat Rooms",
        "description": (
            'Rooms and subscriptions saved in the Rocket.Chat Desktop IndexedDB: room type and '
            'names, user and message counts, the last message of the room with its time and '
            'sender, and the read state.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Rocket.Chat (Desktop)",
        "notes": (
            "Reads the IndexedDB database the Rocket.Chat web client keeps in the desktop app's "
            'partition for a server '
            '(Rocket.Chat/Partitions/<server>/IndexedDB/<origin>.indexeddb.leveldb); the '
            'Rocket.Chat/IndexedDB path is also searched, is not in the sample and is not '
            'sourced. The client writes each collection with localforage as a dictionary with '
            'updatedAt, version, token and records '
            '(apps/meteor/client/lib/cachedStores/CachedStore.ts at the same commit: lines 195 '
            'to 199, version 19 at line 57, the database named from the server address at line '
            '38), under the keys rooms and subscriptions of the object store keyvaluepairs; '
            'every value in the sample has those four keys, and records is a list of room or '
            'subscription records. Each write of a collection is a new LevelDB record, so '
            'earlier states can remain in the .log and .ldb files until LevelDB compacts them; '
            'this reads all of them and keeps one row per distinct (store, record _id, record '
            '_updatedAt, record content), because a subscription record can change without its '
            '_updatedAt changing (on the sample 4 subscription records were saved twice with '
            'the same _updatedAt and different content, and both are shown). Where states tie '
            'on updatedAt, the first one read supplies Store Updated At. A collection stored as '
            'an external blob is read when the .indexeddb.blob folder is in the extraction, and '
            'an error while reading records is logged with the rows read so far kept. The V8 '
            'deserializer returns each JavaScript Date as a naive datetime '
            '(ccl_v8_value_deserializer.py lines 368 to 372), read here as UTC.Field names '
            'follow the typings of RocketChat/Rocket.Chat at 8.9.0 (commit '
            '057a927d903c83b5d61cf236d650c4500ebb4b66), the server version config.json records '
            'for the sample: IRoom, ISubscription, RoomType and IRocketChatRecord in '
            'packages/core-typings/src, and IMessage in its IMessage folder.Store says which '
            'collection the row is from: rooms or subscriptions. Record Updated (UTC) is the '
            "record's _updatedAt (IRocketChatRecord.ts line 8). ts (UTC) is ts, declared by "
            'ISubscription (ISubscription.ts line 16) and IRoom (IRoom.ts line 65); neither '
            'file says what it marks, so it is not called a creation time. Last Message (UTC) '
            'is lm (IRoom.ts line 39), blank when the record has none (2 room rows in the '
            'sample). The subscription records of the sample also carry lm, lastMessage, '
            'usersCount and usernames, which ISubscription does not declare. Last Seen (UTC) is '
            'ls (ISubscription.ts line 23) and in the sample is only on subscription rows (17 '
            'of 21). Store Updated At (UTC) is the updatedAt of the saved collection state, '
            'which the client keeps as the position up to which it has synced (CachedStore.ts '
            'lines 116 to 124, 163 to 173 and 264 to 289); it is not shown to be the time the '
            "state was written, and the sample's 40 rows hold 3 distinct values of it. Server "
            'is the origin the IndexedDB folder is named for, shown without a port when the '
            "folder name ends _0, which Chromium writes for a scheme's default port. Server "
            'held one value on all 40 rows. Type is t as stored; RoomType allows c, d, p and l '
            '(RoomType.ts), which the room type guards in IRoom.ts name as public (line 155), '
            'private (156), direct message (167) and omnichannel (347). Name and Display Name '
            'are name and fname; a room record of a direct conversation has no name (the 10 '
            'room rows of type d) while its subscription does. Users is usersCount, Messages is '
            'msgs and Usernames is the usernames list; in the sample only room rows hold msgs '
            'and only type d rows hold usernames. Last Message, Last Message Type and Last '
            "Message Sender are the msg, t and u.username of the record's lastMessage as "
            'stored. A message typed e2e is an end-to-end encrypted one (IE2EEMessage, '
            'IMessage.ts lines 376 to 380). In the sample Last Message Type is e2e on 17 rows; '
            'every such lastMessage carries its ciphertext in content, which is not reported, '
            'and not in msg; Last Message is empty on 11 of the 17 rows and holds a short text '
            'on 6 (5 distinct texts of 2 to 24 characters), and those texts come from '
            'lastMessage records that carry e2e = done (IMessage.ts line 179 declares the '
            'field; what sets it was not read). Whether that text is the decrypted message was '
            'not tested, and a record written by another version could hold ciphertext in msg. '
            'Last Message is empty on 19 rows in all, the other 8 being rows that are not typed '
            'e2e (4 with no lastMessage and 4 with one whose msg is empty). Unread, Alert and '
            'Open are unread (ISubscription.ts line 21), alert (line 20) and open (line 15); '
            'Alert and Open show yes for a stored true and are blank for a stored false or an '
            'absent value. They are blank on the room rows of the sample; IRoom also declares '
            'the three (lines 52, 56 and 57). Room ID is rid for a subscription and _id for a '
            "room; Record ID is the record's own _id. In the sample: 2 rooms (1 of type d, 1 of "
            'type p) and 40 rows, 19 from rooms (10 type d, 9 type p) and 21 from subscriptions '
            '(11 and 10); Users held 2 on all 40 rows. Not reported: the end-to-end key fields '
            'of a subscription (E2EKey) and of a room (e2eKeyId), the encrypted content of an '
            'e2e last message, the sync token of a collection, and the other record fields. '
            'Among the stores of the Rocket.Chat Desktop folder that these artifacts do not '
            'report: the permissions and public-settings collections of the same IndexedDB '
            "(1,186 and 424 records in each saved state in the sample), Meteor's "
            'MeteorDynamicImportCache database, Local Storage and Session Storage, Service '
            'Worker, Network/Cookies (values not read), logs/main.log and errors.jsonl, the '
            "root Cache folder, the blockfile cache of the server's partition (its index "
            'records 0 entries), the .copyN copies of config.json, supportedVersions.json, '
            'Preferences, Local State and the other settings of config.json. A macOS or Linux '
            'folder is matched only if it is also named Rocket.Chat; that was not sourced or '
            'tested. Windows is the only layout exercised. Sample: the public lab folder of '
            'Rocket.Chat Desktop 4.18.5 from 0ri0ri/selfhosted-chat-forensics (MIT, commit '
            '0bbb8b1; corpus keys rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1 and the '
            'same name ending _users_layout, README beside them), whose config.json records '
            'server 8.9.0. It is the only Rocket.Chat client sample run. No record of what was '
            'typed or sent accompanies it, so the rows were not compared with known data.'
        ),
        "paths": ('*/Rocket.Chat/Partitions/*/IndexedDB/*.indexeddb.leveldb/*', '*/Rocket.Chat/Partitions/*/IndexedDB/*.indexeddb.blob/*',
                  '*/Rocket.Chat/IndexedDB/*.indexeddb.leveldb/*', '*/Rocket.Chat/IndexedDB/*.indexeddb.blob/*',),
        "output_types": "standard",
        "artifact_icon": "message-circle",
        "sample_data": {
            'rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Rocket.Chat Desktop 4.18.5, Windows | 40 rows',
            'rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1': 'Rocket.Chat Desktop 4.18.5, Windows | 40 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
    "rocketChatServers": {
        "name": "Rocket.Chat Servers",
        "description": (
            "The servers listed in Rocket.Chat Desktop's config.json: title, address, server "
            'version, login state, roles and last path as the desktop app recorded them.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Rocket.Chat (Desktop)",
        "notes": (
            'Reads the servers list of Rocket.Chat/config.json. The fields reported are eight '
            "of those of the desktop app's Server type (src/servers/common.ts lines 14 to 53 of "
            'RocketChat/Rocket.Chat.Electron at 4.18.5, commit '
            "d52c2044a503a0ef80d50dc11b00792e7da4abef, the desktop version the sample's logs "
            'record): title, url, version, userLoggedIn, userRoles, lastPath, '
            'isSupportedVersion and supportedVersionsValidatedAt. Server Version is the version '
            'the app recorded for the server (8.9.0 on the sample). User Logged In is yes for a '
            'stored true, no for a stored false and blank when absent; Supported Version is the '
            'same for isSupportedVersion. Version Validated (UTC) is '
            'supportedVersionsValidatedAt, an ISO 8601 string ending in Z on the sample (the '
            'type declares a Date, common.ts line 41); a string without an offset would be read '
            'as local time. A row says the app listed that server, not that anyone signed in '
            'there beyond what userLoggedIn records. Rows: 1 on the sample. Not reported: the '
            'rest of config.json (window state, trusted certificates, theme and update '
            'settings, downloads, the last selected server and the per-server support '
            'messages). Among the stores of the Rocket.Chat Desktop folder that these artifacts '
            'do not report: the permissions and public-settings collections of the same '
            "IndexedDB (1,186 and 424 records in each saved state in the sample), Meteor's "
            'MeteorDynamicImportCache database, Local Storage and Session Storage, Service '
            'Worker, Network/Cookies (values not read), logs/main.log and errors.jsonl, the '
            "root Cache folder, the blockfile cache of the server's partition (its index "
            'records 0 entries), the .copyN copies of config.json, supportedVersions.json, '
            'Preferences, Local State and the other settings of config.json. A macOS or Linux '
            'folder is matched only if it is also named Rocket.Chat; that was not sourced or '
            'tested. Windows is the only layout exercised. Sample: the public lab folder of '
            'Rocket.Chat Desktop 4.18.5 from 0ri0ri/selfhosted-chat-forensics (MIT, commit '
            '0bbb8b1; corpus keys rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1 and the '
            'same name ending _users_layout, README beside them), whose config.json records '
            'server 8.9.0. It is the only Rocket.Chat client sample run. No record of what was '
            'typed or sent accompanies it, so the rows were not compared with known data.'
        ),
        "paths": ('*/Rocket.Chat/config.json',),
        "output_types": "standard",
        "artifact_icon": "message-circle",
        "sample_data": {
            'rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Rocket.Chat Desktop 4.18.5, Windows | 1 rows',
            'rocketchat_desktop_selfhosted_chat_forensics_0bbb8b1': 'Rocket.Chat Desktop 4.18.5, Windows | 1 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
}

import hashlib
import json
import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor.ccl import ccl_chromium_indexeddb as indexeddb

_LABEL = 'Rocket.Chat'
# The keys of the localforage store the Rocket.Chat web client keeps its cached collections in.
_COLLECTIONS = ('rooms', 'subscriptions')


def _utc(value):
    """A date the V8 deserializer returned (naive, a JavaScript Date is a UTC instant) as an aware UTC datetime, '' otherwise."""
    if hasattr(value, 'tzinfo') and hasattr(value, 'replace'):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return ''


def _text(value):
    return value if isinstance(value, str) else ''


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else ''


def _origin(folder_name):
    """The origin an IndexedDB folder is named for: scheme_host_port.indexeddb.leveldb. Chromium writes the default
    port of a scheme as 0 (database_identifier.cc), so port 0 is shown as no port."""
    stem = folder_name.split('.indexeddb')[0]
    scheme, _, rest = stem.partition('_')
    host, _, port = rest.rpartition('_')
    if port.isdigit():
        return f'{scheme}://{host}' if int(port) == 0 else f'{scheme}://{host}:{port}'
    return f'{scheme}://{rest}'


def _content_key(item):
    return hashlib.sha1(json.dumps(item, sort_keys=True, default=str).encode('utf-8', 'replace')).hexdigest()


@artifact_processor
def rocketChatRooms(context):
    data_headers = (('Record Updated (UTC)', 'datetime'), ('ts (UTC)', 'datetime'), ('Last Message (UTC)', 'datetime'),
                    ('Last Seen (UTC)', 'datetime'), ('Store Updated At (UTC)', 'datetime'), 'Server', 'Store', 'Type',
                    'Name', 'Display Name', 'Users', 'Messages', 'Usernames', 'Last Message', 'Last Message Type',
                    'Last Message Sender', 'Unread', 'Alert', 'Open', 'Room ID', 'Record ID')
    found = sorted(str(p) for p in context.get_files_found() if os.path.isfile(str(p)))
    folders = sorted({os.path.dirname(p) for p in found if p.endswith(('.log', '.ldb'))
                      and os.path.dirname(p).endswith('.indexeddb.leveldb')})
    if not folders:
        return data_headers, [], ''
    versions, sources = {}, []
    for folder in folders:
        sources.extend(p for p in found if os.path.dirname(p) == folder and p.endswith(('.log', '.ldb')))
        blob = folder[:-len('.leveldb')] + '.blob'
        try:
            wrapped = indexeddb.WrappedIndexDB(folder, blob if os.path.isdir(blob) else None)
            databases = list(wrapped.database_ids)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: {context.get_relative_path(folder)} could not be opened as IndexedDB: {exc}')
            continue
        for database in databases:
            store = wrapped[database.dbid_no]
            if 'keyvaluepairs' not in store.object_store_names:
                continue
            try:
                for record in store['keyvaluepairs'].iterate_records():
                    name = str(record.key.value)
                    value = record.value
                    if name not in _COLLECTIONS or not isinstance(value, dict) or not isinstance(value.get('records'), list):
                        continue
                    saved = _utc(value.get('updatedAt'))
                    for item in value['records']:
                        if not isinstance(item, dict):
                            continue
                        key = (folder, name, str(item.get('_id')), str(item.get('_updatedAt')), _content_key(item))
                        best = versions.get(key)
                        if best is None or (saved and (not best[1] or saved > best[1])):
                            versions[key] = (item, saved)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logfunc(f'{_LABEL}: {context.get_relative_path(folder)}: reading the {database.name} database stopped: {exc}')
    rows = []
    for (folder, name, _ident, _upd, _content), (item, saved) in versions.items():
        last = item.get('lastMessage') if isinstance(item.get('lastMessage'), dict) else {}
        sender = last.get('u') if isinstance(last.get('u'), dict) else {}
        names = item.get('usernames') if isinstance(item.get('usernames'), list) else []
        rows.append((_utc(item.get('_updatedAt')), _utc(item.get('ts')), _utc(item.get('lm')), _utc(item.get('ls')), saved,
                     _origin(os.path.basename(folder)), name, _text(item.get('t')), _text(item.get('name')),
                     _text(item.get('fname')), _count(item.get('usersCount')), _count(item.get('msgs')),
                     '\n'.join(str(n) for n in names), _text(last.get('msg')), _text(last.get('t')),
                     _text(sender.get('username')), _count(item.get('unread')), 'yes' if item.get('alert') else '',
                     'yes' if item.get('open') else '', _text(item.get('rid')) or _text(item.get('_id')),
                     _text(item.get('_id'))))
    rows.sort(key=lambda r: (str(r[0]), r[6], r[20], str(r[4])))
    return data_headers, rows, '\n'.join(sources)


@artifact_processor
def rocketChatServers(context):
    data_headers = ('Title', 'URL', 'Server Version', 'User Logged In', 'User Roles', 'Last Path', 'Supported Version',
                    ('Version Validated (UTC)', 'datetime'))
    found = sorted(str(p) for p in context.get_files_found() if os.path.isfile(str(p)))
    rows, sources = [], []
    for path in (p for p in found if os.path.basename(p) == 'config.json'):
        sources.append(path)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                config = json.load(handle)
        except (OSError, ValueError) as exc:
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} did not read as JSON: {exc}')
            continue
        servers = config.get('servers') if isinstance(config, dict) else None
        if not isinstance(servers, list):
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} holds no servers list')
            continue
        for server in servers:
            if not isinstance(server, dict):
                continue
            rows.append((_text(server.get('title')), _text(server.get('url')), _text(server.get('version')),
                         _yes_no(server.get('userLoggedIn')),
                         ', '.join(str(r) for r in server.get('userRoles') or []), _text(server.get('lastPath')),
                         _yes_no(server.get('isSupportedVersion')), _iso(server.get('supportedVersionsValidatedAt'))))
    return data_headers, rows, '\n'.join(sources)


def _yes_no(value):
    """yes for a stored true, no for a stored false, blank for anything else."""
    return 'yes' if value is True else ('no' if value is False else '')


def _iso(value):
    if not isinstance(value, str):
        return ''
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except ValueError:
        return ''
