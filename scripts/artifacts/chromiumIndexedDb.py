__artifacts_v2__ = {
    "chromiumIndexedDb": {
        "name": "Chromium IndexedDB Databases",
        "description": "Object stores of the IndexedDB databases that sites kept in Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles: the origin, the top-level site of a site "
                       "embedded in another site's page, database and object store names, and counts of each "
                       "store's record keys.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per object store of each IndexedDB database a site kept in a Chromium-based browser profile, read from the profile's IndexedDB/<origin>.indexeddb.leveldb folders and its WebStorage/<bucket id>/IndexedDB/indexeddb.leveldb folders with the vendored ccl_chromium_indexeddb reader (CCL Forensics). Origin (as stored) is the origin name the database metadata holds; on every tested row it had the shape <scheme>_<host>_<port>@<number>, a form this artifact does not decode. Database and Object Store are the database name and the object store name from the database and object store metadata (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L173-L184, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L215-L226). A database whose name record is no longer live is not listed, and an object store id with no name record is skipped. Live Records counts the store's keys under reserved index id 1, the object store data, whose newest record in the LevelDB files is a value, with every version of a key, in the .log file or an .ldb table file, taken as one key; Deletion Records counts those whose newest record is a deletion still in the files (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L277-L287). LevelDB compaction removes deletions (https://github.com/google/leveldb/blob/068d5ee1a3ac40dabd00d211d5013af44be55bea/doc/impl.md#L104), so 0 is not evidence that nothing was deleted. Live Records with Blobs or Files counts the live keys under reserved index id 3, the external object entries, which record a blob, a file or a File System Access handle kept outside the LevelDB files (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L106-L108, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L300-L309). The counts are read from the keys; no value is decoded, so a value the reader cannot deserialize is still counted. The records themselves are a site's own data and are left to the artifacts for the site. Chromium keeps a first-party default bucket's database in the IndexedDB/<origin> folder and every other bucket's, a site's storage while it is embedded in another site's page or a bucket a site named, in WebStorage/<bucket id>/IndexedDB/indexeddb.leveldb (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/file_path_util.cc#L40-L43, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/file_path_util.cc#L62-L79, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/storage/browser/quota/storage_directory_util.cc#L12-L27), whose folder name holds no origin. Its bucket is looked up by that id in the buckets table of the profile's WebStorage/QuotaManager SQLite database, opened read only (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/storage/browser/quota/quota_database.h#L67, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/storage/browser/quota/quota_database.cc#L163-L176); only its id, storage_key and name are read, which schema versions 10 and 11 both hold (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/storage/browser/quota/quota_database_migrations.cc#L63-L106), The two QuotaManager databases a bucket was looked up in, on hexordia_mvs2025_win11 and mvs2026_macbookpro_macos15, were schema version 10; the patterns also matched version 9 databases on pc_mus_001_win11 (three, which hold the same three columns) and two empty version 11 ones on ubuntu2604_arm64_chromium (snap and Flatpak), none beside a bucket IndexedDB folder, so none was read. Top-Level Site is the site after ^0 in the bucket's storage key, the site whose page the origin was embedded in; a key carrying any other attribute is shown whole in Top-Level Site, decoded as UTF-8 (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/third_party/blink/common/storage_key/storage_key.cc#L31-L100), and no tested key held one. Storage Bucket is the bucket id with its name in parentheses, or the id with (no QuotaManager database) or (no buckets row) when the bucket could not be looked up; no tested folder needed either. Top-Level Site and Storage Bucket are blank on the rows from IndexedDB/<origin> folders, and held no value on any row of cfreds_leakage_win7, lonewolf_win10, ou_ransomware_server2022, pc_mus_001_win11 and the known data, where the patterns matched no WebStorage bucket folder. On hexordia_mvs2025_win11 (6 bucket folders, Edge) and mvs2026_macbookpro_macos15 (3, Chrome) every bucket folder had a buckets row whose storage key was partitioned and whose name was _default, Chromium's name for the default bucket at the commit cited (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/public/cpp/buckets/constants.cc#L12); the version 9 databases on pc_mus_001_win11 name every bucket default instead. On those two images the origin in each bucket's key matched the origin of every database in its folder (10 and 6 databases); a named bucket was not exercised. Browser, Profile and User come from the path, as in the other Chromium artifacts; on a Mac logical extraction a folder whose copy under System/Volumes/Data holds the same files with the same bytes is read once. Browser, Profile and User each held one value on every row of hexordia_mvs2025_win11, lonewolf_win10 and mvs2026_macbookpro_macos15, and User on every row of pc_mus_001_win11, each of which holds IndexedDB folders under one home folder. Tested: windows11_arm_chromium_indexeddb_known_20261103, where Chrome 157.0.8103.39 and Edge 156.0.4314.58 each created database kd_known on https://www.example.com/, put 6 records in store notes and deleted 2, and put 3 Blob values in store files: each browser gave notes 4 live and 2 deletion records and files 3 live records, all 3 with blobs or files. The known data has only a .log file and no bucket folder; .ldb table files were read on hexordia_mvs2025_win11, lonewolf_win10, pc_mus_001_win11 and mvs2026_macbookpro_macos15, whose figures below are from the counting described here. On the corpus: cfreds_leakage_win7 1 row, hexordia_mvs2025_win11 79 (9 from bucket folders), lonewolf_win10 49, ou_ransomware_server2022 2, pc_mus_001_win11 119 and mvs2026_macbookpro_macos15 51 (6 from bucket folders); 149 of those 301 rows had no live record. Rows were seen only from Chrome and Edge profiles; the Brave, Vivaldi, Opera and Chromium paths are declared and were not exercised by any tested image, except that on ubuntu2604_arm64_chromium the Chromium QuotaManager patterns matched the snap and Flatpak profiles' QuotaManager files, with no bucket IndexedDB folder beside them, so no row. For an Opera user data folder with no profile folder, the path helper reads IndexedDB or WebStorage as the profile name, so those declared Opera patterns give no row. Live Records with Blobs or Files held 0 on all 79 rows of hexordia_mvs2025_win11. Not read: the database version and the other database and object store metadata, the index data, the blob files themselves, the other buckets table columns (host, use count, access, modification and expiration times, quota, persistence, durability), the SQLite IndexedDB back end that newer Chromium can keep beside these folders, under IndexedDB/<origin identifier> for a first-party default bucket and directly in WebStorage/<bucket id>/IndexedDB for the others (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/file_path_util.cc#L119-L131), WebStorage folders left behind for deletion under a -doomed- name (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/storage/browser/quota/storage_directory.cc#L16-L17), none seen in the tested images' staged files, Session Storage, File System and shared_proto_db folders, extension storage under a profile's Storage folder, and the profiles of apps that embed Chromium (WebView2, Electron and others), which sit outside the browser user data folders this artifact reads. On hexordia_mvs2025_win11 one such app, the Spotify packaged app (AppData/Local/Packages/SpotifyAB.SpotifyMusic_*/LocalCache/Spotify/Default), holds WebStorage/2 and WebStorage/3 IndexedDB folders and a QuotaManager database. AppData/Roaming/Code, AppData/Roaming/discord and a MicrosoftWindows.Client.WebExperience package each hold a QuotaManager database too; Code's bucket folders hold CacheStorage, not IndexedDB, and the other two hold no bucket folder. Spotify's two folders each held one database with no object store, which would give no row, and as an app's own profile it is left out like the others.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/IndexedDB/*',
            '*/Library/Application Support/Google/Chrome/*/IndexedDB/*',
            '*/.config/google-chrome/*/IndexedDB/*',
            '*/AppData/Local/Chromium/User Data/*/IndexedDB/*',
            '*/Library/Application Support/Chromium/*/IndexedDB/*',
            '*/.config/chromium/*/IndexedDB/*',
            '*/snap/chromium/common/chromium/*/IndexedDB/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/IndexedDB/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/IndexedDB/*',
            '*/Library/Application Support/Microsoft Edge/*/IndexedDB/*',
            '*/.config/microsoft-edge/*/IndexedDB/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/IndexedDB/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/IndexedDB/*',
            '*/.config/BraveSoftware/Brave-Browser/*/IndexedDB/*',
            '*/AppData/Local/Vivaldi/User Data/*/IndexedDB/*',
            '*/Library/Application Support/Vivaldi/*/IndexedDB/*',
            '*/.config/vivaldi/*/IndexedDB/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/IndexedDB/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/IndexedDB/*',
            '*/.config/opera/*/IndexedDB/*',
            '*/webbrowser/chrome/*/IndexedDB/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/IndexedDB/*',
            '*/Library/Application Support/com.operasoftware.Opera/IndexedDB/*',
            '*/.config/opera/IndexedDB/*',
            '*/AppData/Local/Google/Chrome/User Data/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/Google/Chrome/*/WebStorage/QuotaManager*',
            '*/.config/google-chrome/*/WebStorage/QuotaManager*',
            '*/AppData/Local/Chromium/User Data/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/Chromium/*/WebStorage/QuotaManager*',
            '*/.config/chromium/*/WebStorage/QuotaManager*',
            '*/snap/chromium/common/chromium/*/WebStorage/QuotaManager*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/WebStorage/QuotaManager*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/Microsoft Edge/*/WebStorage/QuotaManager*',
            '*/.config/microsoft-edge/*/WebStorage/QuotaManager*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/WebStorage/QuotaManager*',
            '*/.config/BraveSoftware/Brave-Browser/*/WebStorage/QuotaManager*',
            '*/AppData/Local/Vivaldi/User Data/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/Vivaldi/*/WebStorage/QuotaManager*',
            '*/.config/vivaldi/*/WebStorage/QuotaManager*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/WebStorage/QuotaManager*',
            '*/Library/Application Support/com.operasoftware.Opera/*/WebStorage/QuotaManager*',
            '*/.config/opera/*/WebStorage/QuotaManager*',
            '*/webbrowser/chrome/*/WebStorage/QuotaManager*',
            '*/AppData/Roaming/Opera Software/Opera Stable/WebStorage/QuotaManager*',
            '*/Library/Application Support/com.operasoftware.Opera/WebStorage/QuotaManager*',
            '*/.config/opera/WebStorage/QuotaManager*',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "windows11_arm_chromium_indexeddb_known_20261103": "Windows 11 build 26200 (ARM64), Chrome 157.0.8103.39 and Edge 156.0.4314.58 | 4 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 1 row",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 79 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 49 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 119 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 51 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (the QuotaManager patterns match the snap and Flatpak profiles; no IndexedDB folder)",
        },
    },
}

import os
import re
import sqlite3

from scripts.vendor.ccl import ccl_chromium_indexeddb as idb
from scripts.vendor.ccl import ccl_leveldb
from scripts.chromium.browser_profiles import Store, open_store, table_columns
from scripts.chromium.web_storage import profile_folders, split_storage_key
from scripts.ilapfuncs import artifact_processor, logfunc

# Index ids that the IndexedDB LevelDB coding scheme reserves inside an object store
# prefix: 1 for the object store data, 3 for the external object (blob and file)
# entries (content/browser/indexed_db/docs/leveldb_coding_scheme.md lines 277-309,
# chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
_DATA_INDEX = 1
_EXTERNAL_INDEX = 3


def _is_origin_folder(name):
    return name.startswith('IndexedDB/') and name.count('/') == 1 and name.endswith('.indexeddb.leveldb')


# A storage bucket's IndexedDB folder: {profile}/WebStorage/{bucket id}/IndexedDB/indexeddb.leveldb,
# used for a bucket that is not a first-party default bucket
# (content/browser/indexed_db/file_path_util.cc lines 40-43 and 62-79,
# storage/browser/quota/storage_directory_util.cc lines 12-27, chromium
# 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
_BUCKET_FOLDER = re.compile(r'WebStorage/([0-9]+)/IndexedDB/indexeddb\.leveldb')


def _bucket_id(name):
    """The bucket id of a bucket's IndexedDB folder, or None for any other folder."""
    match = _BUCKET_FOLDER.fullmatch(name)
    return int(match.group(1)) if match else None


def _is_store_folder(name):
    return _is_origin_folder(name) or _bucket_id(name) is not None


_is_store_folder.folder_label = 'IndexedDB'


def _read_buckets(quota_store, label):
    """{bucket id: (storage key, bucket name)} from the buckets table of a QuotaManager database.

    Only id, storage_key and name are read; the table has them in schema version 10 and 11
    (storage/browser/quota/quota_database.cc lines 163-176 and quota_database_migrations.cc
    lines 63-106, chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4). Returns None when the
    database cannot be read or has no such table.
    """
    db = open_store(quota_store, label)
    if db is None:
        return None
    try:
        if not {'id', 'storage_key', 'name'} <= table_columns(db, 'buckets'):
            logfunc(f'{label}: {quota_store.relative} has no buckets table with id, storage_key and name')
            return None
        return {row[0]: (row[1], row[2]) for row in db.execute('SELECT id, storage_key, name FROM buckets')}
    except sqlite3.DatabaseError as ex:
        logfunc(f'{label}: could not read the buckets table of {quota_store.relative}: {ex}')
        return None
    finally:
        db.close()


def _top_level_site(storage_key):
    """The top-level site of a serialized storage key; a key with any other attribute, whole as stored."""
    _origin, top_level_site, other = split_storage_key(storage_key)
    return storage_key if other else top_level_site


def _bucket_columns(store, bucket_id, quota_cache, label):
    """(Top-Level Site, Storage Bucket) of one bucket's IndexedDB folder."""
    quota_path = os.path.normpath(os.path.join(store.path, '..', '..', '..', 'QuotaManager'))
    if quota_path not in quota_cache:
        buckets = None
        if os.path.isfile(quota_path):
            quota_relative = os.path.normpath(os.path.join(store.relative, '..', '..', '..', 'QuotaManager'))
            buckets = _read_buckets(Store(quota_path, quota_relative, store.browser, store.profile, store.user,
                                          store.container, 'WebStorage/QuotaManager'), label)
        quota_cache[quota_path] = buckets
    buckets = quota_cache[quota_path]
    if buckets is None:
        logfunc(f'{label}: no readable WebStorage/QuotaManager beside {store.relative}; its bucket is not resolved')
        return '', f'{bucket_id} (no QuotaManager database)'
    if bucket_id not in buckets:
        logfunc(f'{label}: the QuotaManager buckets table has no row for {store.relative}')
        return '', f'{bucket_id} (no buckets row)'
    storage_key, name = buckets[bucket_id]
    return _top_level_site(storage_key), f'{bucket_id} ({name})'


def _newest_states(db):
    """{user key: live?} for the newest LevelDB record of every key the database holds.

    Keyed on the user key: a record read from an .ldb table file carries an 8-byte
    sequence and type trailer on its raw key, so the raw keys of two versions of one
    key differ (ccl_leveldb.Record.user_key).
    """
    newest = {}
    for record in db._fetched_records:  # pylint: disable=protected-access
        key = record.user_key
        current = newest.get(key)
        if current is None or record.seq > current[0]:
            newest[key] = (record.seq, record.state == ccl_leveldb.KeyState.Live)
    return {key: live for key, (_seq, live) in newest.items()}


def _store_counts(states, db_id, store_id):
    """(live records, deleted records, live records with an external object entry)."""
    data = idb.IndexedDb.make_prefix(db_id, store_id, _DATA_INDEX)
    external = idb.IndexedDb.make_prefix(db_id, store_id, _EXTERNAL_INDEX)
    live = deleted = with_external = 0
    for key, is_live in states.items():
        if key.startswith(data):
            if is_live:
                live += 1
            else:
                deleted += 1
        elif is_live and key.startswith(external):
            with_external += 1
    return live, deleted, with_external


@artifact_processor
def chromiumIndexedDb(context):
    label = 'Chromium IndexedDB Databases'
    data_list = []
    sources = []
    quota_cache = {}
    for store in profile_folders(context, _is_store_folder, label):
        bucket_id = _bucket_id(store.name)
        if bucket_id is None:
            top_level_site, bucket = '', ''
        else:
            top_level_site, bucket = _bucket_columns(store, bucket_id, quota_cache, label)
        try:
            db = idb.IndexedDb(store.path)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {store.relative}: {type(ex).__name__}: {ex}')
            continue
        try:
            states = _newest_states(db)
            rows = []
            for database in sorted(db.global_metadata.db_ids, key=lambda d: (d.origin, d.name, d.dbid_no)):
                top = db.get_database_metadata(database.dbid_no, idb.DatabaseMetadataType.MaximumObjectStoreId) or 0
                for store_id in range(1, top + 1):
                    name = db.get_object_store_metadata(database.dbid_no, store_id,
                                                        idb.ObjectStoreMetadataType.StoreName)
                    if name is None:
                        continue
                    live, deleted, with_external = _store_counts(states, database.dbid_no, store_id)
                    rows.append((database.origin, top_level_site, database.name, name, live, deleted,
                                 with_external, bucket, store.browser, store.profile, store.user))
        finally:
            db.close()
        sources.append(store.path)
        if bucket_id is not None:
            quota_path = os.path.normpath(os.path.join(store.path, '..', '..', '..', 'QuotaManager'))
            if quota_cache.get(quota_path) is not None and quota_path not in sources:
                sources.append(quota_path)
        data_list.extend(rows)
    data_headers = ('Origin (as stored)', 'Top-Level Site', 'Database', 'Object Store', 'Live Records',
                    'Deletion Records', 'Live Records with Blobs or Files', 'Storage Bucket', 'Browser',
                    'Profile', 'User')
    return data_headers, data_list, '\n'.join(sources)
