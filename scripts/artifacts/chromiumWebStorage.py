__artifacts_v2__ = {
    "chromiumLocalStorageSites": {
        "name": "Chromium Local Storage Sites",
        "description": "Sites that kept data in the Local Storage of Google Chrome, Microsoft Edge, Brave, "
                       "Vivaldi, Opera, Chromium and webOS webbrowser profiles, one row per site and profile: "
                       "the last time the browser wrote the site's storage, the last access time Chromium "
                       "records, the recorded size and the number of stored keys.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Local Storage/leveldb folder of each Chromium-based browser profile with the LevelDB reader in scripts/ccl, one row per storage key, which is the site that stored the data and, when the key is partitioned, the top-level site it was stored under. Chromium keeps a META:<storage key> record holding last_modified and size_bytes and, in newer builds, a METAACCESS:<storage key> record holding last_accessed, both times written by base::Time::ToInternalValue, microseconds since 1601-01-01 UTC (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/leveldb/local_storage_database.proto#L13-L24, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/leveldb/local_storage_leveldb.cc#L103-L131, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/base/time/time.h#L537). Last Modified is the time Chromium committed a change to the site's storage: it is stamped when a commit is made, and commits wait at least 5 seconds after a change and are limited to 60 an hour per storage area (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/local_storage_impl.cc#L133-L153, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/local_storage_impl.cc#L46-L59). Last Accessed is written once each time the storage area is loaded, at its first commit or, if nothing was committed, when the area is closed, which includes browser shutdown (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/local_storage_impl.cc#L85-L120); it is the time of that write, not of a page view. Last Accessed held no value on any row of the files from 2018 to 2023 (lonewolf_win10, pc_mus_001_win11, ou_ransomware_server2022), whose files hold no METAACCESS record, and a value on every Live row of the 2024 and 2025 files (hexordia_mvs2025_win11, mvs2026_macbookpro_macos15). The source read is Chromium's at the commit cited; the files read, from 2018 to 2025, decode the same way. Site is the origin part of the storage key and Top-Level Site the site after ^0 in a partitioned key; a key carrying any other attribute (a nonce, the ancestor chain bit, an opaque top-level site) is shown whole in Site, as stored (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/third_party/blink/common/storage_key/storage_key.cc#L31-L100); no tested file held one. A site in this table can be a frame embedded in another page rather than a page loaded on its own, and a key that is not partitioned does not record which page embedded it. Of the Live rows, 25 of 79 on hexordia_mvs2025_win11, 38 of 109 on lonewolf_win10, 9 of 52 on pc_mus_001_win11, 10 of 27 on mvs2026_macbookpro_macos15 and 4 of 10 on ou_ransomware_server2022 name a site whose last two domain labels appear in no URL of that profile's History. State is Live when the newest META record is a value, and Emptied when it is a deletion. Chromium deletes the META and METAACCESS records when a commit finds the storage area empty (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/local_storage_impl.cc#L136-L140), and also when it clears an area not accessed or modified for 400 days (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/local_storage_impl.cc#L740-L765); clearing browsing data was not traced, and which cause applies is not recorded. On every Emptied row of the tested files no earlier META value survived, so Last Modified and Recorded Size are blank there, and Stored Keys was 0. A row with no META record would show State No metadata record; no tested file held one. Recorded Size (bytes) is size_bytes as stored. Stored Keys counts the site's keys whose newest record is a value. Deletion Records counts the site's keys whose newest record is a deletion still in the files; LevelDB compaction removes deletions, so 0 is not evidence that nothing was deleted. The keys and values a site stored are not reported here: they are a site's own data, read by the site-specific artifacts (Discord, Slack, Wire and WhatsApp Web) and left in the folder for an examiner who needs one site. Browser, Profile and User come from the path, as in the other Chromium artifacts; Source File names the folder each row came from, since Browser, Profile and User do not separate two copies of one profile, which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. A copy under the second path with the same files and bytes is read once; on mvs2026_macbookpro_macos15 the two copies were identical. On ou_ransomware_server2022 Source File and User separate the same two folders. Browser and Profile held one value on every row of lonewolf_win10 and mvs2026_macbookpro_macos15, which each hold one profile with Local Storage. User held one value on every row of hexordia_mvs2025_win11, lonewolf_win10, mvs2026_macbookpro_macos15 and pc_mus_001_win11, which each hold one home folder with Local Storage. Top-Level Site held no value on any row of lonewolf_win10 and pc_mus_001_win11, whose files hold no partitioned key. State held Live on all 10 rows of ou_ransomware_server2022. Not read: IndexedDB, Session Storage, File System and shared_proto_db, which hold no time per site; storage of Chromium extensions (Storage/ext); and the Local Storage of WebView2 and Electron apps, which sit in other applications' folders (on pc_mus_001_win11 the LevelDB reader stopped with an error in two of them, the Microsoft Teams package and a MicrosoftWindows.Client package), as in the other Chromium artifacts. Newer Chromium has a SQLite back end for this storage (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/dom_storage/sqlite/local_storage_sqlite.cc#L1); no tested profile used it, and it is not read.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Local Storage/leveldb/*',
            '*/Library/Application Support/Google/Chrome/*/Local Storage/leveldb/*',
            '*/.config/google-chrome/*/Local Storage/leveldb/*',
            '*/AppData/Local/Chromium/User Data/*/Local Storage/leveldb/*',
            '*/Library/Application Support/Chromium/*/Local Storage/leveldb/*',
            '*/.config/chromium/*/Local Storage/leveldb/*',
            '*/snap/chromium/common/chromium/*/Local Storage/leveldb/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Local Storage/leveldb/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Local Storage/leveldb/*',
            '*/Library/Application Support/Microsoft Edge/*/Local Storage/leveldb/*',
            '*/.config/microsoft-edge/*/Local Storage/leveldb/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Local Storage/leveldb/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Local Storage/leveldb/*',
            '*/.config/BraveSoftware/Brave-Browser/*/Local Storage/leveldb/*',
            '*/AppData/Local/Vivaldi/User Data/*/Local Storage/leveldb/*',
            '*/Library/Application Support/Vivaldi/*/Local Storage/leveldb/*',
            '*/.config/vivaldi/*/Local Storage/leveldb/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Local Storage/leveldb/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Local Storage/leveldb/*',
            '*/.config/opera/*/Local Storage/leveldb/*',
            '*/webbrowser/chrome/*/Local Storage/leveldb/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Local Storage/leveldb/*',
            '*/Library/Application Support/com.operasoftware.Opera/Local Storage/leveldb/*',
            '*/.config/opera/Local Storage/leveldb/*',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Microsoft Edge 131.0.2903.51 | 83 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, Google Chrome | 125 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Google Chrome and Microsoft Edge 108.0.1462.54 | 59 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4, Google Chrome 142.0.7444.176 | 28 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348, Microsoft Edge 118.0.2088.76 and 120.0.2210.144 | 10 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (both Local Storage logs hold only the VERSION record)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no Local Storage folder in a browser profile)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumServiceWorkers": {
        "name": "Chromium Service Worker Registrations",
        "description": "Service workers registered in Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera, "
                       "Chromium and webOS webbrowser profiles: the scope and script of each registration, "
                       "when the browser last checked the script for an update and when it received it, "
                       "including registrations whose record was deleted and is still readable.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Service Worker/Database folder of each Chromium-based browser profile with the LevelDB reader in scripts/ccl, one row per REG:<storage key> record, a ServiceWorkerRegistrationData message (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/service_worker/service_worker_database.cc#L76-L77, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/service_worker/service_worker_database.proto#L239-L279). Scope and Script URL are scope_url and script_url as stored. Last Update Check is last_update_check_time and Script Response Time is script_response_time, the time the browser received the worker's main script, both microseconds since 1601-01-01 UTC (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/service_worker/service_worker_database.proto#L253-L254, https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/services/storage/service_worker/service_worker_database.proto#L276-L279). Chromium sets the update check time when a registration or update fetched the script from the network or bypassed the cache, or when none was set (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/service_worker/service_worker_register_job.cc#L1035-L1042). What starts an update was not traced, so Last Update Check is not evidence of a visit to the site. Script Response Time held no value on the 11 rows of lonewolf_win10 (Google Chrome, 2018), whose records lack the field, and a value on 17 of 19 rows of hexordia_mvs2025_win11 and 19 of 23 of mvs2026_macbookpro_macos15. State is Live when the newest version of the record is a value; Deleted, value kept when it is a deletion and an earlier version of the record is still readable, whose fields the row shows; and Deleted, key only when no earlier version survives (no tested file held one). Why a registration was deleted is not recorded. Site is the origin part of the storage key and Top-Level Site the site after ^0 in a partitioned key; a key with any other attribute is shown whole in Site, as stored (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/third_party/blink/common/storage_key/storage_key.cc#L31-L100). Top-Level Site held no value on any row of lonewolf_win10, pc_mus_001_win11 and ou_ransomware_server2022. State held Live on every row of lonewolf_win10 and pc_mus_001_win11. Browser and Profile held one value on every row of hexordia_mvs2025_win11, lonewolf_win10, mvs2026_macbookpro_macos15 and ou_ransomware_server2022. Not read: is_active, has_fetch_handler and the other registration fields, the cached script resources (RES, URES, PRES records) and the Service Worker CacheStorage folder, and the service workers of WebView2 and Electron apps. Browser, Profile and User come from the path; Source File names the folder each row came from, for the reason given in Chromium Local Storage Sites. On ou_ransomware_server2022 the 4 rows are one live and one deleted registration in each of two home folders, all four with the same scope, so Scope and Site held one value on all 4 rows there, and Source File and User separate the two folders.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Service Worker/Database/*',
            '*/Library/Application Support/Google/Chrome/*/Service Worker/Database/*',
            '*/.config/google-chrome/*/Service Worker/Database/*',
            '*/AppData/Local/Chromium/User Data/*/Service Worker/Database/*',
            '*/Library/Application Support/Chromium/*/Service Worker/Database/*',
            '*/.config/chromium/*/Service Worker/Database/*',
            '*/snap/chromium/common/chromium/*/Service Worker/Database/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Service Worker/Database/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Service Worker/Database/*',
            '*/Library/Application Support/Microsoft Edge/*/Service Worker/Database/*',
            '*/.config/microsoft-edge/*/Service Worker/Database/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Service Worker/Database/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Service Worker/Database/*',
            '*/.config/BraveSoftware/Brave-Browser/*/Service Worker/Database/*',
            '*/AppData/Local/Vivaldi/User Data/*/Service Worker/Database/*',
            '*/Library/Application Support/Vivaldi/*/Service Worker/Database/*',
            '*/.config/vivaldi/*/Service Worker/Database/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Service Worker/Database/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Service Worker/Database/*',
            '*/.config/opera/*/Service Worker/Database/*',
            '*/webbrowser/chrome/*/Service Worker/Database/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Service Worker/Database/*',
            '*/Library/Application Support/com.operasoftware.Opera/Service Worker/Database/*',
            '*/.config/opera/Service Worker/Database/*',
        ),
        "output_types": "standard",
        "artifact_icon": "cpu",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Microsoft Edge 131.0.2903.51 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, Google Chrome | 11 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Google Chrome and Microsoft Edge 108.0.1462.54 | 23 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4, Google Chrome 142.0.7444.176 | 23 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348, Microsoft Edge 118.0.2088.76 and 120.0.2210.144 | 4 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

from scripts.chromium.browser_profiles import row_tail, webkit_time
from scripts.chromium.web_storage import (LOCAL_STORAGE, SERVICE_WORKER, ProtoError, is_deleted,
                                          newest_versions, profile_folders, proto_fields, signed64,
                                          split_storage_key)
from scripts.ilapfuncs import artifact_processor, logfunc

_META = b'META:'
_ACCESS = b'METAACCESS:'
_REG = b'REG:'


def _key_text(raw):
    return raw.decode('utf-8', 'replace')


def _site(storage_key):
    """(site, top-level site) of a serialized storage key; a key with any other attribute is the site as stored."""
    origin, top_level_site, other = split_storage_key(storage_key)
    if other:
        return storage_key, ''
    return origin, top_level_site


def _time_field(value, number, label, where):
    """The int64 time in field `number` of an encoded message, as a datetime, or ''."""
    if not value:
        return ''
    try:
        fields = proto_fields(value)
    except ProtoError as ex:
        logfunc(f'{label}: {where}: value does not decode ({ex})')
        return ''
    stored = fields.get(number)
    return webkit_time(signed64(stored)) if isinstance(stored, int) else ''


@artifact_processor
def chromiumLocalStorageSites(context):
    label = 'Chromium Local Storage Sites'
    data_list = []
    sources = []
    for store in profile_folders(context, LOCAL_STORAGE, label):
        try:
            newest, _puts, _records = newest_versions(store.path)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {store.relative}: {type(ex).__name__}: {ex}')
            continue
        sources.append(store.path)
        meta, access = {}, {}
        keys = {}
        for raw, (_seq, state, value) in newest.items():
            if raw.startswith(_ACCESS):
                access[_key_text(raw[len(_ACCESS):])] = (state, value)
            elif raw.startswith(_META):
                meta[_key_text(raw[len(_META):])] = (state, value)
            elif raw.startswith(b'_'):
                storage_key, separator, _name = raw[1:].partition(b'\x00')
                if not separator:
                    continue
                counts = keys.setdefault(_key_text(storage_key), [0, 0])
                counts[1 if is_deleted(state) else 0] += 1
        for storage_key in sorted(set(meta) | set(access) | set(keys)):
            meta_state, meta_value = meta.get(storage_key, (None, b''))
            access_state, access_value = access.get(storage_key, (None, b''))
            if meta_state is None:
                state = 'No metadata record'
            elif is_deleted(meta_state):
                state = 'Emptied'
            else:
                state = 'Live'
            last_modified, size = '', ''
            if meta_state is not None and not is_deleted(meta_state):
                where = f'{store.relative}: META:{storage_key}'
                last_modified = _time_field(meta_value, 1, label, where)
                try:
                    stored_size = proto_fields(meta_value).get(2)
                except ProtoError:
                    stored_size = None
                size = stored_size if isinstance(stored_size, int) else ''
            last_accessed = ''
            if access_state is not None and not is_deleted(access_state):
                last_accessed = _time_field(access_value, 1, label,
                                            f'{store.relative}: METAACCESS:{storage_key}')
            site, top_level_site = _site(storage_key)
            live, deleted = keys.get(storage_key, (0, 0))
            data_list.append((last_modified, last_accessed, site, top_level_site, state,
                              size, live, deleted) + row_tail(store))
    data_headers = (('Last Modified', 'datetime'), ('Last Accessed', 'datetime'), 'Site',
                    'Top-Level Site', 'State', 'Recorded Size (bytes)', 'Stored Keys',
                    'Deletion Records', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


def _registration(value, label, where):
    """(scope, script URL, last update check, script response time) of a ServiceWorkerRegistrationData."""
    try:
        fields = proto_fields(value)
    except ProtoError as ex:
        logfunc(f'{label}: {where}: value does not decode ({ex})')
        return None

    def text(number):
        stored = fields.get(number)
        return stored.decode('utf-8', 'replace') if isinstance(stored, bytes) else ''

    def when(number):
        stored = fields.get(number)
        return webkit_time(signed64(stored)) if isinstance(stored, int) else ''

    return text(2), text(3), when(7), when(16)


@artifact_processor
def chromiumServiceWorkers(context):
    label = 'Chromium Service Worker Registrations'
    data_list = []
    sources = []
    for store in profile_folders(context, SERVICE_WORKER, label):
        try:
            newest, puts, _records = newest_versions(store.path)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {store.relative}: {type(ex).__name__}: {ex}')
            continue
        sources.append(store.path)
        for raw in sorted(key for key in newest if key.startswith(_REG)):
            _seq, state, value = newest[raw]
            storage_key, separator, _registration_id = raw[len(_REG):].partition(b'\x00')
            if not separator:
                continue
            if not is_deleted(state):
                kept, row_state = value, 'Live'
            elif puts.get(raw):
                kept, row_state = max(puts[raw])[1], 'Deleted, value kept'
            else:
                kept, row_state = b'', 'Deleted, key only'
            fields = ('', '', '', '')
            if kept:
                decoded = _registration(kept, label, f'{store.relative}: {_key_text(raw[:80])}')
                if decoded is not None:
                    fields = decoded
            scope, script, last_check, response_time = fields
            site, top_level_site = _site(_key_text(storage_key))
            data_list.append((last_check, response_time, scope, script, site, top_level_site,
                              row_state) + row_tail(store))
    data_headers = (('Last Update Check', 'datetime'), ('Script Response Time', 'datetime'), 'Scope',
                    'Script URL', 'Site', 'Top-Level Site', 'State', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
