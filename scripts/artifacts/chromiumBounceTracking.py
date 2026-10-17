__artifacts_v2__ = {
    "chromiumBounceTracking": {
        "name": "Chromium Bounce Tracking Sites (DIPS)",
        "description": "Sites in the DIPS database of Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera, "
                       "Chromium and webOS webbrowser profiles, the store of Chromium's bounce tracking "
                       "mitigation: per site, the first and last time recorded for a user activation, a bounce, "
                       "a WebAuthn assertion and, in older files, a stateful bounce and a site storage access.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the bounces table of each Chromium-based browser profile's DIPS database, one row "
                 "per site. The file keeps Chromium's earlier feature name; Chromium now calls the feature"
                 " Bounce Tracking Mitigations "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/README.md#L1-L53)."
                 " Browser, Profile and User come from the path, as in the other Chromium artifacts; "
                 "Source File names the file each row came from, since Browser, Profile and User do not "
                 "separate two copies of one profile, which a logical extraction can hold under Users/ and"
                 " System/Volumes/Data/Users/. Site is the site column as stored: Chromium records each "
                 "event under the registrable domain (private registries included) of the page's URL, or "
                 "its host when it has none "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_utils.cc#L146-L150,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_storage.cc#L35-L37)."
                 " Each pair of columns is the earliest and latest time of one kind of event, widened as "
                 "events arrive "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_utils.cc#L58-L75),"
                 " stored as microseconds since 1601-01-01 UTC through BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_database.cc#L80-L90,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L300-L316,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44);"
                 " a blank is NULL, and the artifact also shows blank for a value of zero or less or one "
                 "outside the datetime range, which no tested file holds. In the current source a user "
                 "activation is recorded when the top-level frame of an http or https page receives a user"
                 " activation, at most once a minute "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_bounce_detector.cc#L1101-L1120,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_utils.h#L213);"
                 " a bounce is recorded for a site a redirect chain passed through that was neither the "
                 "chain's first nor its last site and whose storage access was known, unless the site had "
                 "a third-party cookie exception under the chain's first or last site "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_service_impl.cc#L472-L481,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_service_impl.cc#L500-L547);"
                 " and a WebAuthn assertion is a successful one in the top-level frame "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_bounce_detector.cc#L1140-L1147)."
                 " Database Version is the meta table's version. Files of version 8 and earlier name the "
                 "user activation columns *_user_interaction_time, renamed in version 9, and carry "
                 "stateful bounce and site storage columns that version 10 dropped "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_database_migrator.cc#L324-L390);"
                 " the interaction columns are shown as User Activation. In Chromium 131 a stateful bounce"
                 " is a bounce whose storage access was more than a read "
                 "(https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_service_impl.cc#L568-L574,"
                 " "
                 "https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_storage.cc#L187-L196),"
                 " and a site storage time is recorded when a cookie or other storage is written, not "
                 "read, under the URL of the page or frame that wrote it, and when a worker is accessed "
                 "(https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_bounce_detector.cc#L752-L762,"
                 " "
                 "https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_bounce_detector.cc#L812-L826,"
                 " "
                 "https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_bounce_detector.cc#L859-L886,"
                 " "
                 "https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/dips/dips_bounce_detector.cc#L903-L978)."
                 " The source read is Chromium's; Microsoft Edge is built on Chromium, its files on the "
                 "tested images have the same tables and version numbers, and Edge's own code was not "
                 "read. In the current source Chromium deletes a site's row once the later of its last "
                 "user activation and last WebAuthn assertion is more than 45 days old by default (a row "
                 "with neither is not deleted by this rule), and the version 10 to 11 migration deleted "
                 "rows with neither of those nor a bounce "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_database.cc#L694-L712,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/public/common/content_features.cc#L342-L343,"
                 " "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/btm/btm_database_migrator.cc#L392-L414),"
                 " so a missing site is not evidence that no event was ever recorded for it. Chromium 120 "
                 "also filled rows when the service started with a database not yet marked prepopulated: "
                 "each http or https site with at least minimal site engagement and no interaction time "
                 "got a user interaction time equal to that moment, not to an interaction, and a site "
                 "storage time too if it had none "
                 "(https://github.com/chromium/chromium/blob/3419140ab665596f21b385ce136419fde0924272/chrome/browser/dips/dips_service.cc#L53-L72,"
                 " "
                 "https://github.com/chromium/chromium/blob/3419140ab665596f21b385ce136419fde0924272/chrome/browser/dips/dips_service.cc#L285-L307,"
                 " "
                 "https://github.com/chromium/chromium/blob/3419140ab665596f21b385ce136419fde0924272/chrome/browser/dips/dips_storage.cc#L314-L335);"
                 " such rows hold one and the same value in the four interaction and storage columns; no "
                 "row on the tested images does. Tested: Microsoft Edge 131.0.2903.51 on "
                 "hexordia_mvs2025_win11 (version 8, 29 rows), Edge 118.0.2088.76 and 120.0.2210.144 in "
                 "two home folders of ou_ransomware_server2022 (versions 4 and 5, 5 and 8 rows), and "
                 "Google Chrome 142.0.7444.176 on mvs2026_macbookpro_macos15 (version 11, 6 rows; the copy"
                 " under System/Volumes/Data/Users is byte-identical and read once). First Bounce, Last "
                 "Bounce, First Stateful Bounce, Last Stateful Bounce, First WebAuthn Assertion and Last "
                 "WebAuthn Assertion held no value on any row of any tested image, so those paths are "
                 "unexercised by data; First Site Storage and Last Site Storage held no value on the "
                 "version 11 rows, where the columns no longer exist, and a value on every row of versions"
                 " 4, 5 and 8. Last User Activation and First User Activation held a value on 22 of 29, 8 "
                 "of 13 and 6 of 6 rows. Browser, Profile, User and Database Version each held one value "
                 "on every row of hexordia_mvs2025_win11 and mvs2026_macbookpro_macos15, which each hold "
                 "one profile with a DIPS file. ubuntu2604_arm64_chromium holds two DIPS files (version "
                 "11) whose bounces tables are empty. Not read: the popups table, which Chromium's "
                 "third-party cookie heuristics fill with an opener site and a pop-up site when their "
                 "conditions are met "
                 "(https://github.com/chromium/chromium/blob/3d81e41b6f3ac8bcae63b32e8145c9eb0cd60a2d/chrome/browser/tpcd/heuristics/opener_heuristic_tab_helper.cc#L392-L413;"
                 " 1 row on hexordia_mvs2025_win11, 0 elsewhere), and the config table. DIPS files of "
                 "WebView2 and Electron apps, which sit in other applications' folders, are not read (on "
                 "hexordia_mvs2025_win11, EBWebView folders and Spotify hold DIPS files of version 7 with "
                 "the same bounces columns; mvs2026_macbookpro_macos15 holds a Signal DIPS write-ahead "
                 "log), as in the other Chromium artifacts. The user data folders read are those of Google"
                 " Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux,"
                 " and the webOS webbrowser folder; only the Windows Edge, macOS Chrome and Linux Chromium"
                 " snap and Flatpak folders held a DIPS file on the tested images.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/DIPS*',
            '*/Library/Application Support/Google/Chrome/*/DIPS*',
            '*/.config/google-chrome/*/DIPS*',
            '*/AppData/Local/Chromium/User Data/*/DIPS*',
            '*/Library/Application Support/Chromium/*/DIPS*',
            '*/.config/chromium/*/DIPS*',
            '*/snap/chromium/common/chromium/*/DIPS*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/DIPS*',
            '*/webbrowser/chrome/*/DIPS*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/DIPS*',
            '*/Library/Application Support/Microsoft Edge/*/DIPS*',
            '*/.config/microsoft-edge/*/DIPS*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/DIPS*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/DIPS*',
            '*/.config/BraveSoftware/Brave-Browser/*/DIPS*',
            '*/AppData/Local/Vivaldi/User Data/*/DIPS*',
            '*/Library/Application Support/Vivaldi/*/DIPS*',
            '*/.config/vivaldi/*/DIPS*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/DIPS*',
            '*/Library/Application Support/com.operasoftware.Opera/*/DIPS*',
            '*/.config/opera/*/DIPS*',
            '*/AppData/Roaming/Opera Software/Opera Stable/DIPS*',
            '*/Library/Application Support/com.operasoftware.Opera/DIPS*',
            '*/.config/opera/DIPS*',
        ),
        "output_types": "standard",
        "artifact_icon": "shuffle",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Microsoft Edge 131.0.2903.51 | 29 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348, Microsoft Edge 118.0.2088.76 and 120.0.2210.144 | 13 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4, Google Chrome 142.0.7444.176 | 6 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (bounces tables empty)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no DIPS file)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no DIPS file)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no DIPS file)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no DIPS file)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no DIPS file)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no DIPS file)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (no DIPS file)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no DIPS file)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no DIPS file)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no DIPS file)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no DIPS file)",
        },
    },
    "edgeWebAssistHistory": {
        "name": "Microsoft Edge WebAssist Navigation History",
        "description": "Pages in the navigation_history table of Microsoft Edge's WebAssistDatabase: "
                       "URL, title, the last_visited_time and num_visits values it stores, and its "
                       "metadata and locale text.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the navigation_history table of each Microsoft Edge profile's WebAssistDatabase, "
                 "one row per row. No Microsoft description of this store was found; the column headers "
                 "follow the stored column names, and what is said here was measured on the tested images "
                 "against the History database of the same profile. Source File names the file each row "
                 "came from, since Browser, Profile and User do not separate two copies of one profile, "
                 "which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. Last "
                 "Visit Time is last_visited_time read as seconds since 1970-01-01 UTC: on 184 of the 202 "
                 "rows it lies within 2 seconds of a visit time History holds for the same URL. URL "
                 "appeared in History's urls table on all 202 rows, Title equalled History's title on 182 "
                 "and Visits (as stored), num_visits, equalled History's visit_count on 118, so the two "
                 "stores do not agree on every row and neither is a copy of the other. Whether this table "
                 "outlives a History clear is not established. Metadata (as stored) is the metadata "
                 "column, a text value whose source is not established; it held a value on 86 of 191, 7 of"
                 " 8 and 1 of 3 rows. Locale is as stored, and NULL is shown blank in Metadata (as stored)"
                 " and Locale; Locale held one value on every row of pc_mus_001_win11. Database Version is"
                 " the meta table's version. Not shown: id (an integer that repeats across rows and is "
                 "blank on some; meaning not established), titledata and urldata (text columns whose "
                 "derivation is not established), product_entity_id and the product_entities table (2 rows"
                 " on hexordia_mvs2025_win11), which holds a category, an entity and search keywords per "
                 "row, source not established, page_profile (NULL on every row of the files that have it; "
                 "absent from the version 3 file) and semantic_encoding. Tested: Edge 131.0.2903.51 on "
                 "hexordia_mvs2025_win11 (version 5, 191 rows), Edge 118.0.2088.76 and 120.0.2210.144 in "
                 "two home folders of ou_ransomware_server2022 (version 4, 3 and 5 rows), and Edge "
                 "108.0.1462.54 on pc_mus_001_win11 (version 3, 3 rows). Browser, Profile and User each "
                 "held one value on every row of hexordia_mvs2025_win11 and pc_mus_001_win11, and Database"
                 " Version held one value on every row of each image. The Edge folders on macOS and Linux "
                 "are read too and were exercised by no registered image.",
        "paths": (
            '*/AppData/Local/Microsoft/Edge/User Data/*/WebAssistDatabase*',
            '*/Library/Application Support/Microsoft Edge/*/WebAssistDatabase*',
            '*/.config/microsoft-edge/*/WebAssistDatabase*',
        ),
        "output_types": "standard",
        "artifact_icon": "globe",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Microsoft Edge 131.0.2903.51 | 191 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348, Microsoft Edge 118.0.2088.76 and 120.0.2210.144 | 8 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Microsoft Edge 108.0.1462.54 | 3 rows",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no WebAssistDatabase)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no WebAssistDatabase)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no WebAssistDatabase)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no WebAssistDatabase)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores, row_tail,
                                               table_columns, unix_time, webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc

# The bounces columns of every DIPS schema version seen, as (column, header). Version 9
# renamed the *_user_interaction_time columns to *_user_activation_time and version 10
# dropped the site storage and stateful bounce columns (btm_database_migrator.cc).
_BOUNCE_TIMES = (
    (('last_user_activation_time', 'last_user_interaction_time'), 'Last User Activation'),
    (('first_user_activation_time', 'first_user_interaction_time'), 'First User Activation'),
    (('last_bounce_time',), 'Last Bounce'),
    (('first_bounce_time',), 'First Bounce'),
    (('last_stateful_bounce_time',), 'Last Stateful Bounce'),
    (('first_stateful_bounce_time',), 'First Stateful Bounce'),
    (('last_site_storage_time',), 'Last Site Storage'),
    (('first_site_storage_time',), 'First Site Storage'),
    (('last_web_authn_assertion_time',), 'Last WebAuthn Assertion'),
    (('first_web_authn_assertion_time',), 'First WebAuthn Assertion'),
)


def _meta_version(db):
    try:
        row = db.execute("SELECT value FROM meta WHERE key = 'version'").fetchone()
    except sqlite3.Error:
        return ''
    return row[0] if row else ''


@artifact_processor
def chromiumBounceTracking(context):
    label = 'Chromium Bounce Tracking Sites'
    data_list = []
    sources = []
    for store in profile_stores(context, {'DIPS'}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            present = table_columns(db, 'bounces')
            if not present:
                logfunc(f'{label}: {store.relative} has no bounces table')
                rows = []
            else:
                picks = []
                for names, _header in _BOUNCE_TIMES:
                    found = next((name for name in names if name in present), None)
                    picks.append(f'"{found}"' if found else 'NULL')
                rows = db.execute(f'SELECT site, {", ".join(picks)} FROM bounces '
                                  f'ORDER BY site').fetchall()
            version = _meta_version(db)
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for site, *times in rows:
            data_list.append(tuple(webkit_time(value) for value in times)
                             + (site, version) + row_tail(store))
    data_headers = tuple((header, 'datetime') for _names, header in _BOUNCE_TIMES) + (
        'Site', 'Database Version', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def edgeWebAssistHistory(context):
    label = 'Microsoft Edge WebAssist Navigation History'
    data_list = []
    sources = []
    for store in profile_stores(context, {'WebAssistDatabase'}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            present = table_columns(db, 'navigation_history')
            if not present:
                logfunc(f'{label}: {store.relative} has no navigation_history table')
                rows = []
            else:
                wanted = ('last_visited_time', 'url', 'title', 'num_visits', 'metadata', 'locale')
                picks = ', '.join(f'"{c}"' if c in present else 'NULL' for c in wanted)
                rows = db.execute(f'SELECT {picks} FROM navigation_history '
                                  f'ORDER BY last_visited_time, url').fetchall()
            version = _meta_version(db)
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for last_visited, url, title, visits, metadata, locale in rows:
            data_list.append((unix_time(last_visited), url, title or '',
                              visits if visits is not None else '', metadata or '',
                              locale or '', version) + row_tail(store))
    data_headers = (('Last Visit Time', 'datetime'), 'URL', 'Title', 'Visits (as stored)',
                    'Metadata (as stored)', 'Locale', 'Database Version', 'Browser', 'Profile',
                    'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
