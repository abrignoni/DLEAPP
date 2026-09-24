__artifacts_v2__ = {
    "chromiumAutofill": {
        "name": "Chromium Autofill Entries",
        "description": "Rows of the autofill table from the Web Data databases of Google Chrome, "
                       "Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles: form field name, "
                       "stored value, stored count and the created and last used times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the autofill table of each Web Data database in a Chromium-based browser profile: "
                 "one row per stored form field name and value, with its count and dates. An "
                 "autofill table missing either date_created or date_last_used is logged and not "
                 "read; none of the tested "
                 "databases lacked them. Browser, Profile and User come from the path: the browser from "
                 "the user data folder, the profile from the folder inside it, and the user from the home "
                 "folder that holds it; Source File names the file each row came from, so rows from two "
                 "profiles or two users stay apart. A profile under User Data/Snapshots/<version>/ is "
                 "reported with that path as its Profile, so a snapshot copy is not merged with the live "
                 "profile; no registered image carries one, and that branch was exercised on a constructed "
                 "tree only. Created and Last Used are date_created and date_last_used, seconds since "
                 "1970-01-01 UTC: Chromium writes them with base::Time::ToTimeT "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L441-L442), "
                 "as the Chrome 65 release did "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/autofill/core/browser/webdata/autofill_table.cc#L816-L817). "
                 "On the tested rows Last Used was never earlier than Created. Count is the stored count: "
                 "Chromium adds one to it and sets date_last_used each time it records the value for the "
                 "field again "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L411-L413), "
                 "and an entry written through its insert path gets 1 or 2 depending on whether its two "
                 "dates differ "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L443-L447). "
                 "It ran from 1 to 2 on pc_mus_001_win11 and from 1 to 66 on lonewolf_win10. Field Name "
                 "and Value are the autofill name and value columns as stored. Browser held one value, "
                 "Google Chrome, on every row of pc_mus_001_win11, whose Microsoft Edge Web Data held no "
                 "autofill rows. A database left with a rollback journal that SQLite treats as hot cannot "
                 "be opened read only, because replaying the journal writes to the database; such a "
                 "database is read as found, with the journal ignored, and the run log says so. No "
                 "database read by this artifact on the tested images had one. Browser, Profile and User "
                 "each held one value on every row of lonewolf_win10, which carries one Chrome profile in "
                 "one home folder, and User held one value on every row of pc_mus_001_win11, whose Chrome "
                 "and Edge profiles sit in one home folder. Tested: Chrome 108.0.5359.125 (21 rows from "
                 "profiles Default and Profile 2) and Microsoft Edge 108.0.1462.54 (0 rows) on "
                 "pc_mus_001_win11, and Chrome 65.0.3325.181 on lonewolf_win10. Not read: the autofill "
                 "address, credit card and IBAN tables of Web Data. No member of af_case2_win10 or "
                 "dleapp_macos_bigsur matched any of the declared paths. The user data folders read are "
                 "those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, "
                 "macOS and Linux, and a store directly inside an Opera user data folder is "
                 "reported with that folder as its Profile. Only the Windows Google Chrome and "
                 "Microsoft Edge folders were "
                 "exercised by a registered image; a constructed tree exercised the Brave macOS, Vivaldi "
                 "Linux and Opera Windows folders, the last with its profile kept directly in the user "
                 "data folder, and the remaining folders were exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome "
                 "channels (Beta, Dev, Canary), extension storage partitions under a profile's Storage "
                 "folder, and WebView2 or Electron app profiles such as EBWebView folders, which share the "
                 "layout but sit in other applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Web Data*',
            '*/Library/Application Support/Google/Chrome/*/Web Data*',
            '*/.config/google-chrome/*/Web Data*',
            '*/AppData/Local/Chromium/User Data/*/Web Data*',
            '*/Library/Application Support/Chromium/*/Web Data*',
            '*/.config/chromium/*/Web Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Web Data*',
            '*/Library/Application Support/Microsoft Edge/*/Web Data*',
            '*/.config/microsoft-edge/*/Web Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Web Data*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/.config/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/AppData/Local/Vivaldi/User Data/*/Web Data*',
            '*/Library/Application Support/Vivaldi/*/Web Data*',
            '*/.config/vivaldi/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Web Data*',
            '*/.config/opera/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/Web Data*',
            '*/.config/opera/Web Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "edit",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 401 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores,
                                               row_tail, table_columns, unix_time)
from scripts.ilapfuncs import artifact_processor, logfunc


@artifact_processor
def chromiumAutofill(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Web Data'}, 'Chromium Autofill Entries'):
        db = open_store(store, 'Chromium Autofill Entries')
        if db is None:
            continue
        try:
            present = table_columns(db, 'autofill')
            if not {'date_created', 'date_last_used'} <= present:
                if present:
                    logfunc(f'Chromium Autofill Entries: {store.relative} has an autofill '
                            f'table without date_created and date_last_used; not read')
                continue
            rows = db.execute('''
                SELECT date_created, date_last_used, name, value, count
                FROM autofill ORDER BY date_created, name, value''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Autofill Entries: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for created, last_used, field, value, count in rows:
            data_list.append((unix_time(created), unix_time(last_used), field, value, count)
                             + row_tail(store))
    data_headers = (('Created', 'datetime'), ('Last Used', 'datetime'), 'Field Name', 'Value',
                    'Count', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
