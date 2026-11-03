__artifacts_v2__ = {
    "chromiumIndexedDb": {
        "name": "Chromium IndexedDB Databases",
        "description": "Object stores of the IndexedDB databases that sites kept in Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles: the origin, database and object store names, "
                       "and how many records each store holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "NOTES_IDB",
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
        "sample_data": {},
    },
}

from scripts.ccl import ccl_chromium_indexeddb as idb
from scripts.ccl import ccl_leveldb
from scripts.chromium.web_storage import profile_folders
from scripts.ilapfuncs import artifact_processor, logfunc

# Index ids that the IndexedDB LevelDB coding scheme reserves inside an object store
# prefix: 1 for the object store data, 3 for the external object (blob and file)
# entries (content/browser/indexed_db/docs/leveldb_coding_scheme.md lines 277-310,
# chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
_DATA_INDEX = 1
_EXTERNAL_INDEX = 3


def _is_origin_folder(name):
    return name.startswith('IndexedDB/') and name.count('/') == 1 and name.endswith('.indexeddb.leveldb')


_is_origin_folder.folder_label = 'IndexedDB'


def _newest_states(db):
    """{key: live?} for the newest LevelDB record of every key the database holds."""
    newest = {}
    for record in db._fetched_records:  # pylint: disable=protected-access
        current = newest.get(record.key)
        if current is None or record.seq > current[0]:
            newest[record.key] = (record.seq, record.state == ccl_leveldb.KeyState.Live)
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
