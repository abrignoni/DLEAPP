"""LG webOS TV records from DB8, webOS's object database, for DLEAPP.

The reader is scripts/webos_db8.py, which cites the db8 source for every layout it reads.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "lgWebosDb8AppUsage": {
        "name": "LG webOS App Events (DB8)",
        "description": "Objects of the DB8 kind com.webos.service.usercontextmanager.app:1: an app ID with the "
                       "start and end times stored for it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per object of the kind com.webos.service.usercontextmanager.app:1, including older "
                 "versions still in the store's files. Start Time (UTC) and End Time (UTC) read startTimeStamp "
                 "and endTimeStamp as seconds since 1970, Duration (seconds) is End minus Start, and App ID is "
                 "eventId as stored; field mapped from a private sample. What starts or ends a record, whether "
                 "the app was in the foreground, and whether anyone was watching are not established, and "
                 "overlapping rows are reported as stored, not merged. The times are as stored: a TV whose clock "
                 "was not yet set when a record was written can store a wrong time, so corroborate with "
                 "another source. A value that is not a whole number is left out of the "
                 "time columns and counted in the run log. Store, record and header handling are described in "
                 "the notes of LG webOS DB8 Kinds; Record Status, DB8 Deleted, Revision and Store are "
                 "described there too. Validated only against a private sample; sample_data is left empty "
                 "for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "activity",
        "sample_data": {},
    },
    "lgWebosDb8ChannelUsage": {
        "name": "LG webOS Channel Events (DB8)",
        "description": "Objects of the DB8 kind com.webos.service.usercontextmanager.channel:1: a channel ID "
                       "with the start and end times stored for it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per object of the kind com.webos.service.usercontextmanager.channel:1, including "
                 "older versions still in the store's files. Start Time (UTC) and End Time (UTC) read startTimeStamp "
                 "and endTimeStamp as seconds since 1970, Duration (seconds) is End minus Start, and Channel ID "
                 "is eventId as stored; field mapped from a private sample. The Channel ID is not joined to a "
                 "channel name. What starts or ends a record and whether anyone was watching are not "
                 "established, and overlapping rows are reported as stored, not merged. The times are as stored: a TV "
                 "whose clock was not yet set when a record was written can store a wrong time, so corroborate "
                 "with another source. A value that is not a whole number is "
                 "left out of the time columns and counted in the run log. Store, record and header handling "
                 "and the Record Status, DB8 Deleted, Revision and Store columns are described in the notes of "
                 "LG webOS DB8 Kinds. Validated only against a private sample; sample_data is left empty for "
                 "that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "monitor",
        "sample_data": {},
    },
    "lgWebosDb8RecentItems": {
        "name": "LG webOS Recent Items (DB8)",
        "description": "Objects of the DB8 kind com.webos.launcher.recentsitems:1 (title, subtitle, app ID, card "
                       "snapshot path), including records whose key LevelDB has since deleted.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per object of the kind com.webos.launcher.recentsitems:1, including older versions and records whose key has a LevelDB "
                 "deletion as its newest record, which the Record Status column marks as Removed. Title, "
                 "Subtitle, App ID, Card Snapshot Path and Fullscreen are the title, subtitle, appId, "
                 "cardSnapShotFilePath and fullscreen fields as stored; field mapped from a private sample. No "
                 "time field is read, so rows are ordered by Store and then Revision, which orders writes "
                 "within one store; Revision does not give a date. The snapshot path is reported as text and the file it names is "
                 "not looked up. Store, record and header handling and the Record Status, DB8 Deleted, Revision "
                 "and Store columns are described in the notes of LG webOS DB8 Kinds. Validated only against a "
                 "private sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "clock",
        "sample_data": {},
    },
    "lgWebosDb8IotClient": {
        "name": "LG webOS IoT Client Record (DB8)",
        "description": "Objects of the DB8 kind com.webos.service.iotclient.req:1: account entries (user ID, "
                       "user number, alias, requester), device ID, endpoint, topics, and whether a certificate "
                       "and private key are stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per entry of accountInfoList in each object of the kind "
                 "com.webos.service.iotclient.req:1, or one row with the account columns blank when the list is "
                 "empty or missing. User ID, User No, Alias Name and Requester are the entry's userId, userNo, "
                 "aliasName and requester fields; Device ID, Enabled, Endpoint URL, Publish Topic, Subscribe "
                 "Topic and Shadow Topic are the object's deviceId, isEnabled, endPointUrl, pubTopic, subTopic "
                 "and shadowTopic fields, all as stored; field mapped from a private sample. Certificate Stored "
                 "and Private Key Stored say whether the cert and privKey fields hold text, with its length; the "
                 "text itself is not put in the report, and is in the store for an examiner who needs it. Which "
                 "service these identifiers belong to, and whether the record is current, are not "
                 "established. Store, record and header handling and the Record Status, DB8 Deleted, Revision "
                 "and Store columns are described in the notes of LG webOS DB8 Kinds. Validated only against a "
                 "private sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "cloud",
        "sample_data": {},
    },
    "lgWebosDb8Membership": {
        "name": "LG webOS Membership Values (DB8)",
        "description": "Objects of the DB8 kind com.webos.membership.db:1: a key, a value and the regtime each "
                       "carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per object of the kind com.webos.membership.db:1, including older versions and records whose key has a "
                 "LevelDB deletion as its newest record. Key and Value are the key and value fields as stored. "
                 "Reg Time (UTC) reads regtime as milliseconds since 1970, whether stored as text or as a "
                 "number, and Reg Time (as stored) keeps the value; field mapped from a private sample. What each key "
                 "means is not established. Store, record and header handling and the Record Status, DB8 "
                 "Deleted, Revision and Store columns are described in the notes of LG webOS DB8 Kinds. "
                 "Validated only against a private sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "user",
        "sample_data": {},
    },
    "lgWebosDb8ChannelFlags": {
        "name": "LG webOS Channel Favorites and Locks (DB8)",
        "description": "Channels in the webOS channel list kinds that carry a favorite group, a favorite "
                       "position, a lock or a skip.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads the kinds com.webos.service.pbs.stb.ch:1 and com.webos.service.tv.channel.dblist:1, "
                 "including older versions, and reports a channel only when favoriteGroup is not empty, one "
                 "of favoriteIdxA to favoriteIdxH holds a value, or locked or skipped is true; every other channel is counted in the run log and not reported. Channel "
                 "Number, "
                 "Channel Name, Favorite Groups, Locked, Skipped and Channel ID are the channelNumber, "
                 "channelName, favoriteGroup, locked, skipped and channelId fields as stored, and Favorite "
                 "Positions lists each favoriteIdx field that holds a value as name=value; field mapped from a "
                 "private sample. Who set a flag, and when, are not established. Objects of "
                 "the kind com.webos.service.favorites.channels:1 are reported by LG webOS DB8 Records (Other "
                 "Kinds). Store, record and header handling and the Record "
                 "Status, DB8 Deleted, Revision and Store columns are described in the notes of LG webOS DB8 "
                 "Kinds. Validated only against a private sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "star",
        "sample_data": {},
    },
    "lgWebosDb8Settings": {
        "name": "LG webOS Settings Service Values (DB8)",
        "description": "Setting values in the DB8 kind com.webos.settings.system:1, one row per key, leaving "
                       "out categories named for picture, sound and 3D.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "Reads the kind com.webos.settings.system:1, including older versions, so a value that changed can show both readings. "
                 "One row is reported per key of an object's value field when it is an object, and one row "
                 "with Key blank when it is not; Category, App ID, Key and Value are the category, app_id, key "
                 "and value as stored, Volatile is the object's volatile field, and a value that is not text is "
                 "shown as JSON. Objects whose category begins "
                 "with picture, sound or 3d are counted in the run log and not reported, to keep the report to "
                 "the other settings. The kinds com.webos.settings.default:1 and com.webos.settings.desc* are "
                 "not read. What "
                 "each key means is not established; field mapped from a private sample. Store, record and "
                 "header handling and the Record Status, DB8 Deleted, Revision and Store columns are described "
                 "in the notes of LG webOS DB8 Kinds. Validated only against a private sample; sample_data is "
                 "left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {},
    },
    "lgWebosDb8OtherKinds": {
        "name": "LG webOS DB8 Records (Other Kinds)",
        "description": "Objects of webOS DB8 kinds for notification history, second screen, favorites, TV "
                       "reservations, the credentials manager, ACR, music recent play and play lists, cbox "
                       "recording and my channels, with their fields as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per object, including older versions, of these kinds: "
                 "com.webos.notificationhistory:1, com.webos.secondscreen.gateway.clientprofile:1, "
                 "com.webos.secondscreen.user:1, com.webos.secondscreen.userdata:1, "
                 "com.webos.secondscreen.userinfo:1, com.webos.secondscreen.webapp:1, "
                 "com.webos.service.favorites.channels:1, com.webos.service.favorites.shows:1, "
                 "com.webos.service.favorites.shows.details:1, com.webos.service.tv.reservation.event:1, "
                 "com.webos.service.tv.reservation.info:1, com.webos.service.credentialsmanager:1, "
                 "com.webos.service.acr:1, com.webos.app.music.recentplay:1, com.webos.app.music.myplaylist:1, "
                 "com.webos.service.cbox.recording:1 and mychannels.db:1. Fields (as stored) is the object's "
                 "fields as JSON, with decimals as text, and nothing in it is interpreted: which fields a kind "
                 "holds, and what they mean, were not established from a populated sample, so no column is "
                 "given a meaning and no time is converted. These kinds were chosen by their names, which were "
                 "mapped from a private sample. A credentials kind can hold secrets, which are reported as "
                 "stored. Store, record and header handling and the Record Status, DB8 Deleted, Revision and "
                 "Store columns are described in the notes of LG webOS DB8 Kinds. Validated only against a "
                 "private sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {},
    },
    "lgWebosDb8Kinds": {
        "name": "LG webOS DB8 Kinds",
        "description": "The kinds of each webOS DB8 store, with the owner their kind records name and counts of "
                       "objects, older versions, removed records and deleted-flagged objects.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "LG webOS TV",
        "notes": "One row per kind per store: every kind the store's indexIds.db part gives a kind token, and "
                 "any kind named by a record in objects.db. Owner is the owner field of the kind's own record "
                 "(kind Kind:1) when there is one. Live Objects counts the objects whose key is live, and DB8 "
                 "Deleted counts those among them carrying DB8's deleted flag; Older Versions and Removed "
                 "Records count the other records in the files, as defined below. A record that could not be "
                 "decoded is counted in the run log and in no column. This lists what a store holds "
                 "so that kinds no other artifact reports can be found. "
                 "The store: db8's configuration places its stores at /var/db/main, /var/db/temp and "
                 "/media/cryptofs/data/db8/mediadb/media (Reference: webOS OSE db8, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/files/conf/maindb.conf.in#L11, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/files/conf/tempdb.conf.in#L11, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/files/conf/mediadb.conf.in#L11), "
                 "and db8 writes a _version file in the folder it opens its storage engine on (Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDb.cpp#L184-L200, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDb.cpp#L1444-L1499). "
                 "The declared paths match folders ending in db/main, db/temp or db8/mediadb/media, and a "
                 "folder is reported only when it holds CURRENT and _version and its LevelDB meta part names "
                 "objects.db, so a LevelDB without that meta part yields no rows. With the sandwich engine every db8 "
                 "database is a part of one LevelDB whose keys start with a two-byte prefix; part 0 maps each "
                 "database name to its prefix (Reference: leveldb-tl, 'sandwich_db.hpp', "
                 "https://github.com/ony/leveldb-tl/blob/fc5850f31e2668893a2398fdd6725521fa7bb8bf/include/leveldb/sandwich_db.hpp#L10-L19, "
                 "https://github.com/ony/leveldb-tl/blob/fc5850f31e2668893a2398fdd6725521fa7bb8bf/include/leveldb/sandwich_db.hpp#L59-L84; "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/engine/sandwich/MojDbSandwichEngine.cpp#L297-L316), "
                 "and a key within objects.db is the object ID serialized (Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/engine/sandwich/MojDbSandwichDatabase.cpp#L188-L202). "
                 "The object: a header of version, kind token, revision and an optional deleted flag "
                 "(Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDbObjectHeader.cpp#L82-L126), "
                 "then the fields in db8's binary encoding, where a property name can be a one-byte token from "
                 "the kind's token list in kinds.db, and kind tokens come from indexIds.db (Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/inc/core/MojObjectSerialization.h#L32-L54, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/core/MojObjectSerialization.cpp#L230-L384, "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDbKindState.cpp#L24-L26). "
                 "Between the webOS OSE db8 tags submissions/1 (2018) and submissions/32 (2024) the encoding "
                 "and data serialization files are unchanged, and the other files cited changed only in ways "
                 "that do not touch the layouts cited (copyright lines, casts, const references and error "
                 "handling); the encoding and header code also match Open webOS db8 4.0.0 (2013) apart from "
                 "two changes that do not change the bytes read or written. The reader follows that published source and was checked "
                 "against a private sample; a store written by a db8 build that differs from it may not read "
                 "the same way. The columns the LG webOS DB8 artifacts share: Record Status is Live "
                 "for the newest record of a key, Superseded for an older record of a key that is still live, "
                 "and Removed when the key's newest LevelDB record is a deletion; older records are read from "
                 "the log and table files still in the folder, and one whose bytes equal the next record's is "
                 "not repeated. A store keeps older records only until LevelDB compacts them away, so their "
                 "absence says nothing. DB8 Deleted is the object's own deleted flag: db8 either purges a "
                 "deleted object from objects.db or writes it again with _del set (Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDb.cpp#L976-L1021). "
                 "Revision is _rev, which db8 takes from the store-wide id sequence on every write, so within "
                 "one store a higher revision was written later (Reference: "
                 "https://github.com/webosose/db8/blob/7b551709f5bbd932e7119752e4929014f4bf8837/src/db/MojDb.cpp#L889-L897). "
                 "Object ID is the object's _id and Store is the folder read. Validated only against a private "
                 "sample; sample_data is left empty for that reason.",
        "paths": ("*db/main/*", "*db/temp/*", "*/db8/mediadb/media/*"),
        "output_types": "standard",
        "artifact_icon": "list",
        "sample_data": {},
    },
}

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.webos_db8 import STATUS_LIVE, STATUS_REMOVED, STATUS_SUPERSEDED, Db8Store

APP_KIND = 'com.webos.service.usercontextmanager.app:1'
CHANNEL_KIND = 'com.webos.service.usercontextmanager.channel:1'
RECENTS_KIND = 'com.webos.launcher.recentsitems:1'
IOT_KIND = 'com.webos.service.iotclient.req:1'
MEMBERSHIP_KIND = 'com.webos.membership.db:1'
CHANNEL_LIST_KINDS = ('com.webos.service.pbs.stb.ch:1', 'com.webos.service.tv.channel.dblist:1')
SETTINGS_KIND = 'com.webos.settings.system:1'
SETTINGS_LEFT_OUT = ('picture', 'sound', '3d')
OTHER_KINDS = (
    'com.webos.notificationhistory:1',
    'com.webos.secondscreen.gateway.clientprofile:1',
    'com.webos.secondscreen.user:1',
    'com.webos.secondscreen.userdata:1',
    'com.webos.secondscreen.userinfo:1',
    'com.webos.secondscreen.webapp:1',
    'com.webos.service.favorites.channels:1',
    'com.webos.service.favorites.shows:1',
    'com.webos.service.favorites.shows.details:1',
    'com.webos.service.tv.reservation.event:1',
    'com.webos.service.tv.reservation.info:1',
    'com.webos.service.credentialsmanager:1',
    'com.webos.service.acr:1',
    'com.webos.app.music.recentplay:1',
    'com.webos.app.music.myplaylist:1',
    'com.webos.service.cbox.recording:1',
    'mychannels.db:1',
)
FAVORITE_POSITIONS = tuple(f'favoriteIdx{letter}' for letter in 'ABCDEFGH')
LEVELDB_FILE = re.compile(r'(\d{6}\.(ldb|log|sst)|MANIFEST-\d+)')

_STORES = {}


def _stores(context):
    """[(store folder relative path, Db8Store, files read)] for the matched folders that are DB8 stores.

    A folder counts only when it holds CURRENT and _version and its LevelDB meta part names
    objects.db."""
    folders = {}
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        folders.setdefault(os.path.dirname(path), []).append(path)
    found = []
    for folder in sorted(folders, key=context.get_relative_path):
        names = {os.path.basename(p) for p in folders[folder]}
        if 'CURRENT' not in names or '_version' not in names:
            continue
        store = _STORES.get(folder)
        if store is None:
            try:
                store = Db8Store(folder)
            except (OSError, ValueError) as exc:
                logfunc(f'LG webOS DB8: {context.get_relative_path(folder)} could not be read: {exc}')
                continue
            _STORES[folder] = store
        if not store.is_db8():
            continue
        read = sorted(p for p in folders[folder] if LEVELDB_FILE.fullmatch(os.path.basename(p)))
        found.append((context.get_relative_path(folder), store, read))
    return found


def _versions(stores, kinds):
    """(store relative path, Db8Object) for every version of an object of the given kinds."""
    out = []
    for relative, store, _read in stores:
        for obj in store.object_versions():
            if obj.kind in kinds:
                out.append((relative, obj))
    return out


def _tail(relative, obj):
    return (obj.status, 'Yes' if obj.deleted else 'No', obj.rev, str(obj.id), relative)


def _text(value):
    """A stored value as report text: strings as they are, anything else as JSON."""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, Decimal)):
        return str(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _seconds(value, counts):
    """A whole number of seconds since 1970 as a UTC time; '' (and a count) for anything else."""
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            pass
    if value is not None:
        counts['time values that are not a whole number of seconds, left out'] += 1
    return ''


def _read_paths(stores):
    return '\n'.join(p for _relative, _store, read in stores for p in read)


def _log(name, stores, counts):
    for relative, store, _read in stores:
        if store.errors:
            logfunc(f'{name}: {len(store.errors)} records in {relative} could not be decoded')
    if counts:
        logfunc(f'{name}: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))


def _usage(context, kind, name):
    """(rows, files read) for one of the user-context-manager kinds."""
    stores = _stores(context)
    counts = Counter()
    rows = []
    for relative, obj in _versions(stores, {kind}):
        start = obj.body.get('startTimeStamp')
        end = obj.body.get('endTimeStamp')
        duration = ''
        if all(isinstance(v, int) and not isinstance(v, bool) for v in (start, end)):
            duration = end - start
        rows.append((_seconds(start, counts), _seconds(end, counts), duration,
                     _text(obj.body.get('eventId'))) + _tail(relative, obj))
    rows.sort(key=lambda r: (r[0] == '', r[0] or datetime.min.replace(tzinfo=timezone.utc), r[6]))
    _log(name, stores, counts)
    return rows, _read_paths(stores)


@artifact_processor
def lgWebosDb8AppUsage(context):
    data_headers = (('Start Time (UTC)', 'datetime'), ('End Time (UTC)', 'datetime'), 'Duration (seconds)',
                    'App ID', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    rows, read = _usage(context, APP_KIND, 'LG webOS App Events (DB8)')
    return data_headers, rows, read


@artifact_processor
def lgWebosDb8ChannelUsage(context):
    data_headers = (('Start Time (UTC)', 'datetime'), ('End Time (UTC)', 'datetime'), 'Duration (seconds)',
                    'Channel ID', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    rows, read = _usage(context, CHANNEL_KIND, 'LG webOS Channel Events (DB8)')
    return data_headers, rows, read


@artifact_processor
def lgWebosDb8RecentItems(context):
    data_headers = ('Revision', 'Title', 'Subtitle', 'App ID', 'Card Snapshot Path', 'Fullscreen',
                    'Record Status', 'DB8 Deleted', 'Object ID', 'Store')
    stores = _stores(context)
    rows = []
    for relative, obj in _versions(stores, {RECENTS_KIND}):
        body = obj.body
        status, deleted, rev, obj_id, store = _tail(relative, obj)
        rows.append((rev, _text(body.get('title')), _text(body.get('subtitle')), _text(body.get('appId')),
                     _text(body.get('cardSnapShotFilePath')), _text(body.get('fullscreen')),
                     status, deleted, obj_id, store))
    rows.sort(key=lambda r: (r[9], r[0]))
    _log('LG webOS Recent Items (DB8)', stores, Counter())
    return data_headers, rows, _read_paths(stores)


def _stored(value):
    if isinstance(value, str) and value:
        return f'Yes ({len(value)} characters)'
    if value is None:
        return 'No'
    return 'No' if value == '' else f'Yes ({type(value).__name__})'


@artifact_processor
def lgWebosDb8IotClient(context):
    data_headers = ('User ID', 'User No', 'Alias Name', 'Requester', 'Device ID', 'Enabled', 'Endpoint URL',
                    'Publish Topic', 'Subscribe Topic', 'Shadow Topic', 'Certificate Stored',
                    'Private Key Stored', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    stores = _stores(context)
    rows = []
    for relative, obj in _versions(stores, {IOT_KIND}):
        body = obj.body
        shared = (_text(body.get('deviceId')), _text(body.get('isEnabled')), _text(body.get('endPointUrl')),
                  _text(body.get('pubTopic')), _text(body.get('subTopic')), _text(body.get('shadowTopic')),
                  _stored(body.get('cert')), _stored(body.get('privKey')))
        accounts = body.get('accountInfoList')
        entries = [a for a in accounts if isinstance(a, dict)] if isinstance(accounts, list) else []
        if not entries:
            rows.append(('', '', '', '') + shared + _tail(relative, obj))
        for entry in entries:
            rows.append((_text(entry.get('userId')), _text(entry.get('userNo')), _text(entry.get('aliasName')),
                         _text(entry.get('requester'))) + shared + _tail(relative, obj))
    _log('LG webOS IoT Client Record (DB8)', stores, Counter())
    return data_headers, rows, _read_paths(stores)


def _milliseconds(value, counts):
    """regtime (milliseconds since 1970, stored as text or a number) as a UTC time, or ''."""
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value / 1000, timezone.utc)
        except (OverflowError, OSError, ValueError):
            pass
    if value not in (None, ''):
        counts['regtime values that are not a whole number of milliseconds, left out'] += 1
    return ''


@artifact_processor
def lgWebosDb8Membership(context):
    data_headers = (('Reg Time (UTC)', 'datetime'), 'Reg Time (as stored)', 'Key', 'Value', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    stores = _stores(context)
    counts = Counter()
    rows = []
    for relative, obj in _versions(stores, {MEMBERSHIP_KIND}):
        body = obj.body
        rows.append((_milliseconds(body.get('regtime'), counts), _text(body.get('regtime')),
                     _text(body.get('key')), _text(body.get('value'))) + _tail(relative, obj))
    rows.sort(key=lambda r: (r[8], r[2], r[6]))
    _log('LG webOS Membership Values (DB8)', stores, counts)
    return data_headers, rows, _read_paths(stores)


def _flagged(body):
    group = body.get('favoriteGroup')
    has_group = bool(group) if isinstance(group, (list, dict, str)) else group not in (None, False)
    positions = [f for f in FAVORITE_POSITIONS if body.get(f) is not None]
    return has_group or positions or body.get('locked') is True or body.get('skipped') is True, positions


@artifact_processor
def lgWebosDb8ChannelFlags(context):
    data_headers = ('Channel Number', 'Channel Name', 'Favorite Groups', 'Favorite Positions', 'Locked',
                    'Skipped', 'Channel ID', 'Kind', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    stores = _stores(context)
    counts = Counter()
    rows = []
    for relative, obj in _versions(stores, set(CHANNEL_LIST_KINDS)):
        body = obj.body
        flagged, positions = _flagged(body)
        if not flagged:
            counts['channel records with no favorite, lock or skip, not reported'] += 1
            continue
        rows.append((_text(body.get('channelNumber')), _text(body.get('channelName')),
                     _text(body.get('favoriteGroup')),
                     '\n'.join(f'{f}={_text(body.get(f))}' for f in positions),
                     _text(body.get('locked')), _text(body.get('skipped')), _text(body.get('channelId')),
                     obj.kind) + _tail(relative, obj))
    _log('LG webOS Channel Favorites and Locks (DB8)', stores, counts)
    return data_headers, rows, _read_paths(stores)


@artifact_processor
def lgWebosDb8Settings(context):
    data_headers = ('Category', 'Key', 'Value', 'App ID', 'Volatile', 'Record Status', 'DB8 Deleted', 'Revision', 'Object ID', 'Store')
    stores = _stores(context)
    counts = Counter()
    rows = []
    for relative, obj in _versions(stores, {SETTINGS_KIND}):
        body = obj.body
        category = _text(body.get('category'))
        if category.lower().startswith(SETTINGS_LEFT_OUT):
            counts['picture, sound and 3d setting objects, not reported'] += 1
            continue
        value = body.get('value')
        pairs = sorted(value.items()) if isinstance(value, dict) else [('', value)]
        for key, item in pairs:
            rows.append((category, key, _text(item), _text(body.get('app_id')),
                         _text(body.get('volatile'))) + _tail(relative, obj))
    rows.sort(key=lambda r: (r[9], r[0], r[1], r[7]))
    _log('LG webOS Settings Service Values (DB8)', stores, counts)
    return data_headers, rows, _read_paths(stores)


@artifact_processor
def lgWebosDb8OtherKinds(context):
    data_headers = ('Kind', 'Revision', 'Fields (as stored)', 'Record Status', 'DB8 Deleted', 'Object ID',
                    'Store')
    stores = _stores(context)
    rows = []
    for relative, obj in _versions(stores, set(OTHER_KINDS)):
        status, deleted, rev, obj_id, store = _tail(relative, obj)
        rows.append((obj.kind, rev, _text(obj.body), status, deleted, obj_id, store))
    rows.sort(key=lambda r: (r[6], r[0], r[1]))
    _log('LG webOS DB8 Records (Other Kinds)', stores, Counter())
    return data_headers, rows, _read_paths(stores)


@artifact_processor
def lgWebosDb8Kinds(context):
    data_headers = ('Kind', 'Owner', 'Live Objects', 'DB8 Deleted', 'Older Versions', 'Removed Records',
                    'Store')
    stores = _stores(context)
    rows = []
    for relative, store, _read in stores:
        live, flagged, older, removed = Counter(), Counter(), Counter(), Counter()
        owners = {}
        for obj in store.object_versions():
            if obj.status == STATUS_LIVE:
                live[obj.kind] += 1
                if obj.deleted:
                    flagged[obj.kind] += 1
                if obj.kind == 'Kind:1' and isinstance(obj.body.get('id'), str):
                    owners[obj.body['id']] = _text(obj.body.get('owner'))
            elif obj.status == STATUS_SUPERSEDED:
                older[obj.kind] += 1
            elif obj.status == STATUS_REMOVED:
                removed[obj.kind] += 1
        kinds = set(store.kinds.values()) | set(live) | set(older) | set(removed)
        for kind in sorted(kinds):
            rows.append((kind, owners.get(kind, ''), live[kind], flagged[kind], older[kind], removed[kind],
                         relative))
    _log('LG webOS DB8 Kinds', stores, Counter())
    return data_headers, rows, _read_paths(stores)
