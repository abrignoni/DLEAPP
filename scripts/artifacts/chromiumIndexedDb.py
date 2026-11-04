__artifacts_v2__ = {
    "chromiumIndexedDb": {
        "name": "Chromium IndexedDB Databases",
        "description": "Object stores of the IndexedDB databases that sites kept in Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles: the origin, database and object store names, "
                       "and counts of each store's record keys.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per object store of each IndexedDB database a site kept in a Chromium-based browser "
                 "profile, read from the profile's IndexedDB/<origin>.indexeddb.leveldb folders with the "
                 "vendored ccl_chromium_indexeddb reader (CCL Forensics). Origin (as stored) is the origin "
                 "name the database metadata holds; on every tested row it had the shape "
                 "<scheme>_<host>_<port>@<number>, a form this artifact does not decode. Database and Object "
                 "Store are the database name and the object store name from the database and object store "
                 "metadata "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L173-L184, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L215-L226). "
                 "A database whose name record is no longer live is not listed, and an object store id with no "
                 "name record is skipped. Live Records counts the store's keys under reserved index id 1, the "
                 "object store data, whose newest record in the LevelDB files is a value, with every version "
                 "of a key, in the .log file or an .ldb table file, taken as one key; Deletion Records counts "
                 "those whose newest record is a deletion still in the files "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L277-L287). "
                 "LevelDB compaction removes deletions "
                 "(https://github.com/google/leveldb/blob/068d5ee1a3ac40dabd00d211d5013af44be55bea/doc/impl.md#L104), "
                 "so 0 is not evidence that nothing was deleted. Live Records with Blobs or Files counts the "
                 "live keys under reserved index id 3, the external object entries, which record a blob, a "
                 "file or a File System Access handle kept outside the LevelDB files "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L106-L108, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/indexed_db/docs/leveldb_coding_scheme.md#L300-L309). "
                 "The counts are read from the keys; no value is decoded, so a value the reader cannot "
                 "deserialize is still counted. The records themselves are a site's own data and are left to "
                 "the artifacts for the site. Browser, Profile and User come from the path, as in the other "
                 "Chromium artifacts; on a Mac logical extraction a folder whose copy under "
                 "System/Volumes/Data holds the same files with the same bytes is read once. Tested: "
                 "windows11_arm_chromium_indexeddb_known_20261103, where Chrome 157.0.8103.39 and Edge "
                 "156.0.4314.58 each created database kd_known on https://www.example.com/, put 6 records in "
                 "store notes and deleted 2, and put 3 Blob values in store files: each browser gave notes 4 "
                 "live and 2 deletion records and files 3 live records, all 3 with blobs or files. The known "
                 "data has only a .log file; .ldb table files were read on hexordia_mvs2025_win11 (14 files), "
                 "lonewolf_win10 (1), pc_mus_001_win11 (11) and mvs2026_macbookpro_macos15 (12, after the 12 "
                 "in byte-identical System/Volumes copies were not read again), whose figures below are from "
                 "the counting described here. On the corpus: cfreds_leakage_win7 1 row, "
                 "hexordia_mvs2025_win11 70, lonewolf_win10 49, ou_ransomware_server2022 2, pc_mus_001_win11 "
                 "119 and mvs2026_macbookpro_macos15 45; 142 of those 286 rows had no live record. Rows were "
                 "seen only from Chrome and Edge profiles; the Brave, Vivaldi, Opera and Chromium paths are "
                 "declared and were not exercised by any tested image. Live Records with Blobs or Files held 0 "
                 "on all 70 rows of hexordia_mvs2025_win11. Not read: the database version and the other "
                 "database and object store metadata, the index data, the blob files themselves, Session "
                 "Storage, File System and shared_proto_db folders, extension storage under a profile's "
                 "Storage folder, the IndexedDB folders under a profile's WebStorage/<number> folders (2 on "
                 "hexordia_mvs2025_win11), whose layout has no origin in the folder name, and WebView2 or "
                 "Electron app profiles.",
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
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "windows11_arm_chromium_indexeddb_known_20261103": "Windows 11 build 26200 (ARM64), Chrome 157.0.8103.39 and Edge 156.0.4314.58 | 4 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 1 row",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 70 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 49 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 119 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 45 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no member matches the declared paths)",
        },
    },
}

from scripts.vendor.ccl import ccl_chromium_indexeddb as idb
from scripts.vendor.ccl import ccl_leveldb
from scripts.chromium.web_storage import profile_folders
from scripts.ilapfuncs import artifact_processor, logfunc

# Index ids that the IndexedDB LevelDB coding scheme reserves inside an object store
# prefix: 1 for the object store data, 3 for the external object (blob and file)
# entries (content/browser/indexed_db/docs/leveldb_coding_scheme.md lines 277-309,
# chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
_DATA_INDEX = 1
_EXTERNAL_INDEX = 3


def _is_origin_folder(name):
    return name.startswith('IndexedDB/') and name.count('/') == 1 and name.endswith('.indexeddb.leveldb')


_is_origin_folder.folder_label = 'IndexedDB'


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
    for store in profile_folders(context, _is_origin_folder, label):
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
                    rows.append((database.origin, database.name, name, live, deleted, with_external,
                                 store.browser, store.profile, store.user))
        finally:
            db.close()
        sources.append(store.path)
        data_list.extend(rows)
    data_headers = ('Origin (as stored)', 'Database', 'Object Store', 'Live Records', 'Deletion Records',
                    'Live Records with Blobs or Files', 'Browser', 'Profile', 'User')
    return data_headers, data_list, '\n'.join(sources)
