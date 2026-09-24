__artifacts_v2__ = {
    "chromiumLoginData": {
        "name": "Chromium Saved Logins",
        "description": "Rows of the logins table, including never-save entries, from the Login Data "
                       "and Login Data For Account databases of "
                       "Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles: "
                       "site, username, dates and use count. The password column is not queried.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the logins table of the Login Data and Login Data For Account databases of each "
                 "Chromium-based browser profile, the two file names in password_manager_constants.cc "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/password_manager/core/browser/password_manager_constants.cc#L12-L15); "
                 "one row per logins row, and Store names the file. The password_value column is not "
                 "queried. Browser, Profile and User come from the path: the browser from the user data "
                 "folder, the profile from the folder inside it, and the user from the home folder that "
                 "holds it; Source File names the file each row came from, so rows from two profiles or "
                 "two users stay apart. A profile under User Data/Snapshots/<version>/ is reported with "
                 "that path as its Profile, so a snapshot copy is not merged with the live profile; no "
                 "registered image carries one, and that branch was exercised on a constructed tree only. "
                 "Created, Last Used and Password Modified are date_created, date_last_used and "
                 "date_password_modified, microseconds since 1601-01-01 UTC. Current Chromium binds them "
                 "with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/password_manager/core/browser/password_store/login_database.cc#L240-L265), "
                 "which stores what Statement::TimeToSqlValue returns "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L300-L316), "
                 "ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for date_created "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/password_manager/core/browser/login_database.cc#L138), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "date_last_used was added in database version 25 and date_password_modified in version 30 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/password_manager/core/browser/password_store/login_database.cc#L486-L488 "
                 "and "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/password_manager/core/browser/password_store/login_database.cc#L516-L517); "
                 "lonewolf_win10 holds version 19, so Last Used and Password Modified are blank on every "
                 "row there, and both were filled on every row of pc_mus_001_win11 (version 33). "
                 "Chromium's password_form.h describes date_last_used as updated after a successful form "
                 "submission that used the login, date_password_modified as the last change of the "
                 "password value, date_created as the time the login was saved, and "
                 "times_used_in_html_form, stored as times_used, as the number of times the saved "
                 "credential was used to authenticate in an HTML form "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/password_manager/core/browser/password_form.h#L349-L391). "
                 "Blocklisted is blacklisted_by_user, the never-save marker for the form (same file, lines "
                 "376 to 380), and Signon Realm is signon_realm as stored (lines 224 to 230). "
                 "The Microsoft Edge Login Data of pc_mus_001_win11 has the same logins columns "
                 "as the Chrome Login Data on that image; Edge's own source was not examined, so "
                 "these descriptions were not confirmed for Edge. Times Used held one value, 0, "
                 "on every row of "
                 "pc_mus_001_win11 and was 0, 2 or 3 on lonewolf_win10. Blocklisted held one value, No, on "
                 "every row of pc_mus_001_win11 and was Yes on 1 of the 6 rows of lonewolf_win10, the one "
                 "row with no Username. Store held one value, Login Data, on every row of both images: the "
                 "four Login Data For Account databases of pc_mus_001_win11 held no rows. Browser held one "
                 "value, Google Chrome, on every row of pc_mus_001_win11, whose Microsoft Edge Login Data "
                 "held no rows. A database left with a rollback journal that SQLite treats as hot cannot "
                 "be opened read only, because replaying the journal writes to the database; such a "
                 "database is read as found, with the journal ignored, and the run log says so. No "
                 "database read by this artifact on the tested images had one. Browser, Profile and User "
                 "each held one value on every row of lonewolf_win10, which carries one Chrome profile in "
                 "one home folder, and User held one value on every row of pc_mus_001_win11, whose Chrome "
                 "and Edge profiles sit in one home folder. Tested: Chrome 108.0.5359.125 and Microsoft "
                 "Edge 108.0.1462.54 on pc_mus_001_win11, and Chrome 65.0.3325.181 on lonewolf_win10. No "
                 "member of af_case2_win10 or dleapp_macos_bigsur matched any of the declared paths. The "
                 "user data folders read are those of Google Chrome, Chromium, Microsoft Edge, Brave, "
                 "Vivaldi and Opera on Windows, macOS and Linux, and a store directly inside an "
                 "Opera user data folder is reported with that folder as its Profile. Only the "
                 "Windows Google Chrome and "
                 "Microsoft Edge folders were exercised by a registered image; a constructed tree "
                 "exercised the Brave macOS, Vivaldi Linux and Opera Windows folders, the last with its "
                 "profile kept directly in the user data folder, and the remaining folders were "
                 "exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome channels (Beta, Dev, Canary), extension storage "
                 "partitions under a profile's Storage folder, and WebView2 or Electron app profiles such "
                 "as EBWebView folders, which share the layout but sit in other applications' folders. "
                 "Chromium source is cited at commit 33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the "
                 "Chrome 65 release, at abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Login Data*',
            '*/Library/Application Support/Google/Chrome/*/Login Data*',
            '*/.config/google-chrome/*/Login Data*',
            '*/AppData/Local/Chromium/User Data/*/Login Data*',
            '*/Library/Application Support/Chromium/*/Login Data*',
            '*/.config/chromium/*/Login Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Login Data*',
            '*/Library/Application Support/Microsoft Edge/*/Login Data*',
            '*/.config/microsoft-edge/*/Login Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Login Data*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Login Data*',
            '*/.config/BraveSoftware/Brave-Browser/*/Login Data*',
            '*/AppData/Local/Vivaldi/User Data/*/Login Data*',
            '*/Library/Application Support/Vivaldi/*/Login Data*',
            '*/.config/vivaldi/*/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Login Data*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Login Data*',
            '*/.config/opera/*/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Login Data*',
            '*/Library/Application Support/com.operasoftware.Opera/Login Data*',
            '*/.config/opera/Login Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores,
                                               row_tail, select_list, table_columns,
                                               webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc

# The password_value column is never selected.
_COLUMNS = ('date_created', 'date_last_used', 'date_password_modified', 'origin_url',
            'signon_realm', 'username_value', 'times_used', 'blacklisted_by_user')


def _yes_no(value):
    if value is None or value == '':
        return ''
    return 'Yes' if int(value) else 'No'


@artifact_processor
def chromiumLoginData(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Login Data', 'Login Data For Account'},
                                'Chromium Saved Logins'):
        db = open_store(store, 'Chromium Saved Logins')
        if db is None:
            continue
        try:
            present = table_columns(db, 'logins')
            if not present:
                continue
            rows = db.execute(f'SELECT {select_list(present, _COLUMNS)} FROM logins '
                              f'ORDER BY date_created, signon_realm').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Saved Logins: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for (created, last_used, modified, origin, realm, username, times_used,
             blocklisted) in rows:
            data_list.append((webkit_time(created), webkit_time(last_used),
                              webkit_time(modified), origin, realm, username, times_used,
                              _yes_no(blocklisted), store.name) + row_tail(store))
    data_headers = (('Created', 'datetime'), ('Last Used', 'datetime'),
                    ('Password Modified', 'datetime'), 'Origin URL', 'Signon Realm', 'Username',
                    'Times Used', 'Blocklisted', 'Store', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
