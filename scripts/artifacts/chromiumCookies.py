__artifacts_v2__ = {
    "chromiumCookies": {
        "name": "Chromium Cookies",
        "description": "Cookie metadata from the Cookies databases of Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles: host, name, path, flags and the "
                       "creation, expiry, last access and last update times. The value columns are not "
                       "queried.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the cookies table of each Cookies database in a Chromium-based browser profile, at "
                 "<profile>/Cookies (Chrome 65 on lonewolf_win10) or <profile>/Network/Cookies (Chrome and "
                 "Edge 108 on pc_mus_001_win11); one row per cookies row. The value and encrypted_value "
                 "columns are not queried. Chromium writes an empty value and the encrypted blob when it "
                 "has an encryptor "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/extras/sqlite/sqlite_persistent_cookie_store.cc#L1368-L1369), "
                 "and every cookie row of the tested images had an empty value and a non-empty "
                 "encrypted_value: 840 on pc_mus_001_win11 and 2953 on lonewolf_win10. Browser, Profile "
                 "and User come from the path: the browser from the user data folder, the profile from the "
                 "folder inside it, and the user from the home folder that holds it; Source File names the "
                 "file each row came from, so rows from two profiles or two users stay apart. A profile "
                 "under User Data/Snapshots/<version>/ is reported with that path as its Profile, so a "
                 "snapshot copy is not merged with the live profile; no registered image carries one, and "
                 "that branch was exercised on a constructed tree only. Created, Expires, Last Access Time "
                 "and Last Update Time are creation_utc, expires_utc, last_access_utc and last_update_utc, "
                 "microseconds since 1601-01-01 UTC. Current Chromium binds them with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/extras/sqlite/sqlite_persistent_cookie_store.cc#L1354-L1389), "
                 "which stores what Statement::TimeToSqlValue returns "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L300-L316), "
                 "ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for creation_utc, expires_utc "
                 "and last_access_utc "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/net/extras/sqlite/sqlite_persistent_cookie_store.cc#L1156-L1177), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "last_update_utc exists from cookie database version 18 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/extras/sqlite/sqlite_persistent_cookie_store.cc#L234-L236); "
                 "lonewolf_win10 holds version 9, so Last Update Time is blank on every row there, and it "
                 "was filled on every row of pc_mus_001_win11 (version 18). Expires is blank where "
                 "expires_utc is 0, which on the tested images were the rows whose Persistent is No (8 on "
                 "pc_mus_001_win11, 611 on lonewolf_win10), and on 3 lonewolf_win10 rows whose expires_utc "
                 "falls after 9999-12-31, beyond the range the report's datetime type holds. Secure, "
                 "HttpOnly and Persistent are is_secure, is_httponly and is_persistent, named secure, "
                 "httponly and persistent in older databases. has_expires is not reported: Chromium writes "
                 "has_expires and is_persistent from the same value "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/extras/sqlite/sqlite_persistent_cookie_store.cc#L1380-L1381), "
                 "and the two were equal on every tested row. A database left with a rollback journal that "
                 "SQLite treats as hot cannot be opened read only, because replaying the journal writes to "
                 "the database; such a database is read as found, with the journal ignored, and the run "
                 "log says so. No database read by this artifact on the tested images had one. Browser, "
                 "Profile and User each held one value on every row of lonewolf_win10, which carries one "
                 "Chrome profile in one home folder, and User held one value on every row of "
                 "pc_mus_001_win11, whose Chrome and Edge profiles sit in one home folder. Tested: Chrome "
                 "108.0.5359.125 (profiles Default and Profile 2 with rows; System Profile and Guest "
                 "Profile empty) and Microsoft Edge 108.0.1462.54 on pc_mus_001_win11, and Chrome "
                 "65.0.3325.181 on lonewolf_win10. No member of af_case2_win10 or dleapp_macos_bigsur "
                 "matched any of the declared paths. The user data folders read are those of Google "
                 "Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux, "
                 "and a store directly inside an Opera user data folder, or in the Network "
                 "folder of any of these user data folders, is reported with that folder as its "
                 "Profile. Only the Windows Google Chrome and Microsoft Edge folders were "
                 "exercised by a "
                 "registered image; a constructed tree exercised the Brave macOS, Vivaldi Linux and Opera "
                 "Windows folders, the last with its profile kept directly in the user data "
                 "folder, and the remaining folders were exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome channels (Beta, Dev, "
                 "Canary), extension storage partitions under a profile's Storage folder, and WebView2 or "
                 "Electron app profiles such as EBWebView folders, which share the layout but sit in other "
                 "applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Cookies*',
            '*/Library/Application Support/Google/Chrome/*/Cookies*',
            '*/.config/google-chrome/*/Cookies*',
            '*/AppData/Local/Chromium/User Data/*/Cookies*',
            '*/Library/Application Support/Chromium/*/Cookies*',
            '*/.config/chromium/*/Cookies*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Cookies*',
            '*/Library/Application Support/Microsoft Edge/*/Cookies*',
            '*/.config/microsoft-edge/*/Cookies*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Cookies*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Cookies*',
            '*/.config/BraveSoftware/Brave-Browser/*/Cookies*',
            '*/AppData/Local/Vivaldi/User Data/*/Cookies*',
            '*/Library/Application Support/Vivaldi/*/Cookies*',
            '*/.config/vivaldi/*/Cookies*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Cookies*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Cookies*',
            '*/.config/opera/*/Cookies*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Cookies*',
            '*/Library/Application Support/com.operasoftware.Opera/Cookies*',
            '*/.config/opera/Cookies*',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 840 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2953 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores,
                                               row_tail, table_columns, webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc


def _flag(value):
    if value is None or value == '':
        return ''
    return 'Yes' if int(value) else 'No'


@artifact_processor
def chromiumCookies(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Cookies', 'Network/Cookies'}, 'Chromium Cookies'):
        db = open_store(store, 'Chromium Cookies')
        if db is None:
            continue
        try:
            present = table_columns(db, 'cookies')
            if not present:
                continue
            # Older releases name the flag columns secure, httponly and persistent.
            secure = 'is_secure' if 'is_secure' in present else 'secure'
            httponly = 'is_httponly' if 'is_httponly' in present else 'httponly'
            persistent = 'is_persistent' if 'is_persistent' in present else 'persistent'
            last_update = 'last_update_utc' if 'last_update_utc' in present else 'NULL'
            rows = db.execute(f'''
                SELECT last_access_utc, creation_utc, expires_utc, {last_update}, host_key,
                       name, path, {secure}, {httponly}, {persistent}
                FROM cookies ORDER BY last_access_utc, host_key, name''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Cookies: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for (last_access, created, expires, updated, host, name, path, is_secure,
             is_httponly, is_persistent) in rows:
            data_list.append((webkit_time(last_access), webkit_time(created),
                              webkit_time(expires), webkit_time(updated), host, name, path,
                              _flag(is_secure), _flag(is_httponly), _flag(is_persistent))
                             + row_tail(store))
    data_headers = (('Last Access Time', 'datetime'), ('Created', 'datetime'),
                    ('Expires', 'datetime'), ('Last Update Time', 'datetime'), 'Host', 'Name',
                    'Path', 'Secure', 'HttpOnly', 'Persistent', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
