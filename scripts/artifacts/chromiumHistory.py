__artifacts_v2__ = {
    "chromiumWebVisits": {
        "name": "Chromium Web Visits",
        "description": "Rows of the visits table from the History databases of Google Chrome, Microsoft "
                       "Edge, Brave, Vivaldi, Opera and Chromium profiles, with the URL, page title, "
                       "transition and visit source.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the visits table of each History database in a Chromium-based browser profile and "
                 "joins each visit to its urls row for the URL and title; one row per visits row. Every "
                 "visit on the tested images had a urls row. Browser, Profile and User come from the path: "
                 "the browser from the user data folder, the profile from the folder inside it, and the "
                 "user from the home folder that holds it; Source File names the file each row came from, "
                 "so rows from two profiles or two users stay apart. A profile under User "
                 "Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot copy "
                 "is not merged with the live profile; no registered image carries one, and that branch "
                 "was exercised on a constructed tree only. Visit Time is visits.visit_time, microseconds "
                 "since 1601-01-01 UTC. Current Chromium binds it with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/visit_database.cc#L394), "
                 "which stores ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for it "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/visit_database.cc#L157), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "Transition is the core type in the low byte of visits.transition and Transition "
                 "Qualifiers names the qualifier bits set above it, using the values in "
                 "page_transition_types.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/ui/base/page_transition_types.h#L30-L112 "
                 "and "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/ui/base/page_transition_types.h#L119-L155); "
                 "any other set bit is shown as other bits in hex, and none was set on the tested images. "
                 "Visit Source is read from the visit_source table: Chromium writes a row there only for a "
                 "visit whose source is not browsed "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/visit_database.cc#L420-L423) "
                 "and reads a missing row as browsed (same file, lines 612 and 613), so a visit with no "
                 "row is shown as BROWSED (no visit_source row); a stored value is shown with its name "
                 "from history_types.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/history_types.h#L50-L59). "
                 "Visit Source was SYNCED (0) on 4 of the 2293 rows of lonewolf_win10 and IE_IMPORTED (4) "
                 "on 12 of the 42 Microsoft Edge rows of pc_mus_001_win11. The names are Chromium's; "
                 "Microsoft Edge's source is not published, so their meaning in Edge was not confirmed. "
                 "Visit Duration (seconds) is visits.visit_duration, written in microseconds "
                 "(visit_database.cc line 399, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L331) "
                 "and divided by one million here; history_types.h describes it as the time from opening "
                 "to closing the visit including inactive time "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/history_types.h#L134-L138). "
                 "It was 0 on 827 of the 1099 rows of pc_mus_001_win11 and 2101 of the 2293 rows of "
                 "lonewolf_win10. Referring URL is the URL of the visit named in visits.from_visit, which "
                 "history_types.h describes as the redirecting or referring page's visit "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/history_types.h#L114-L117); "
                 "it is blank where from_visit is 0 or names no visits row, and it was blank on 597 of the "
                 "1099 rows of pc_mus_001_win11 and 1398 of the 2293 rows of lonewolf_win10. A database "
                 "left with a rollback journal that SQLite treats as hot cannot be opened read only, "
                 "because replaying the journal writes to the database; such a database is read as found, "
                 "with the journal ignored, and the run log says so. The lonewolf_win10 Chrome History is "
                 "one: read that way it passes SQLite's integrity_check, while rolling its journal back on "
                 "a scratch copy left the copy malformed. Browser, Profile and User each held one value on "
                 "every row of lonewolf_win10, which carries one Chrome profile in one home folder, and "
                 "User held one value on every row of pc_mus_001_win11, whose Chrome and Edge profiles sit "
                 "in one home folder. Tested: Chrome 108.0.5359.125 (profiles Default and Profile 2; the "
                 "System Profile and Guest Profile History databases held no visits, URLs, downloads or "
                 "search terms) and Microsoft Edge 108.0.1462.54 (profile Default) on pc_mus_001_win11, "
                 "and Chrome 65.0.3325.181 (profile Default) on lonewolf_win10. No member of "
                 "af_case2_win10 or dleapp_macos_bigsur matched any of the declared paths. The user data "
                 "folders read are those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and "
                 "Opera on Windows, macOS and Linux, and a store directly inside a user data folder is "
                 "reported with that folder as its Profile. Only the Windows Google Chrome and Microsoft "
                 "Edge folders were exercised by a registered image; a constructed tree exercised the "
                 "Brave macOS, Vivaldi Linux and Opera Windows folders, the last with its profile kept "
                 "directly in the user data folder, and the remaining folders were not exercised. Not "
                 "read: other Chrome channels (Beta, Dev, Canary), extension storage partitions under a "
                 "profile's Storage folder, and WebView2 or Electron app profiles such as EBWebView "
                 "folders, which share the layout but sit in other applications' folders. Also not read: "
                 "the Archived History database of older Chrome releases. Chromium source is cited at "
                 "commit 33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/History*',
            '*/Library/Application Support/Google/Chrome/*/History*',
            '*/.config/google-chrome/*/History*',
            '*/AppData/Local/Chromium/User Data/*/History*',
            '*/Library/Application Support/Chromium/*/History*',
            '*/.config/chromium/*/History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History*',
            '*/Library/Application Support/Microsoft Edge/*/History*',
            '*/.config/microsoft-edge/*/History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History*',
            '*/.config/BraveSoftware/Brave-Browser/*/History*',
            '*/AppData/Local/Vivaldi/User Data/*/History*',
            '*/Library/Application Support/Vivaldi/*/History*',
            '*/.config/vivaldi/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/History*',
            '*/.config/opera/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/History*',
            '*/Library/Application Support/com.operasoftware.Opera/History*',
            '*/.config/opera/History*',
        ),
        "output_types": "standard",
        "artifact_icon": "globe",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1099 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2293 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumUrls": {
        "name": "Chromium URLs",
        "description": "Rows of the urls table from the History databases of Google Chrome, Microsoft "
                       "Edge, Brave, Vivaldi, Opera and Chromium profiles, with each URL's last visit "
                       "time, visit count and typed count as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the urls table of each History database in a Chromium-based browser profile; one "
                 "row per urls row. On the tested images every urls row had at least one visits row, so "
                 "this artifact names no URL that Chromium Web Visits does not. Browser, Profile and User "
                 "come from the path: the browser from the user data folder, the profile from the folder "
                 "inside it, and the user from the home folder that holds it; Source File names the file "
                 "each row came from, so rows from two profiles or two users stay apart. A profile under "
                 "User Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot "
                 "copy is not merged with the live profile; no registered image carries one, and that "
                 "branch was exercised on a constructed tree only. Last Visit Time is "
                 "urls.last_visit_time, microseconds since 1601-01-01 UTC. Current Chromium binds it with "
                 "Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/url_database.cc#L217), "
                 "which stores ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for it "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/url_database.cc#L112), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "Visit Count and Typed Count are urls.visit_count and urls.typed_count as stored. "
                 "Chromium's url_row.h says the visit count will often, but not always, match the URL's "
                 "entries in the visits table because some transitions are not counted, and that the typed "
                 "count should match the number of TYPED transitions but can be out of sync with the "
                 "visits table "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/url_row.h#L70-L81). "
                 "Hidden is the urls.hidden flag as stored; url_row.h says the flag is usually for "
                 "subframes "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/url_row.h#L135-L137). "
                 "It was Yes on 3 of the 646 rows of pc_mus_001_win11 and 21 of the 737 rows of "
                 "lonewolf_win10. A database left with a rollback journal that SQLite treats as hot cannot "
                 "be opened read only, because replaying the journal writes to the database; such a "
                 "database is read as found, with the journal ignored, and the run log says so. The "
                 "lonewolf_win10 Chrome History is one: read that way it passes SQLite's integrity_check, "
                 "while rolling its journal back on a scratch copy left the copy malformed. Browser, "
                 "Profile and User each held one value on every row of lonewolf_win10, which carries one "
                 "Chrome profile in one home folder, and User held one value on every row of "
                 "pc_mus_001_win11, whose Chrome and Edge profiles sit in one home folder. Tested: Chrome "
                 "108.0.5359.125 (profiles Default and Profile 2; the System Profile and Guest Profile "
                 "History databases held no visits, URLs, downloads or search terms) and Microsoft Edge "
                 "108.0.1462.54 (profile Default) on pc_mus_001_win11, and Chrome 65.0.3325.181 (profile "
                 "Default) on lonewolf_win10. No member of af_case2_win10 or dleapp_macos_bigsur matched "
                 "any of the declared paths. The user data folders read are those of Google Chrome, "
                 "Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux, and a "
                 "store directly inside a user data folder is reported with that folder as its Profile. "
                 "Only the Windows Google Chrome and Microsoft Edge folders were exercised by a registered "
                 "image; a constructed tree exercised the Brave macOS, Vivaldi Linux and Opera Windows "
                 "folders, the last with its profile kept directly in the user data folder, and the "
                 "remaining folders were not exercised. Not read: other Chrome channels (Beta, Dev, "
                 "Canary), extension storage partitions under a profile's Storage folder, and WebView2 or "
                 "Electron app profiles such as EBWebView folders, which share the layout but sit in other "
                 "applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/History*',
            '*/Library/Application Support/Google/Chrome/*/History*',
            '*/.config/google-chrome/*/History*',
            '*/AppData/Local/Chromium/User Data/*/History*',
            '*/Library/Application Support/Chromium/*/History*',
            '*/.config/chromium/*/History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History*',
            '*/Library/Application Support/Microsoft Edge/*/History*',
            '*/.config/microsoft-edge/*/History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History*',
            '*/.config/BraveSoftware/Brave-Browser/*/History*',
            '*/AppData/Local/Vivaldi/User Data/*/History*',
            '*/Library/Application Support/Vivaldi/*/History*',
            '*/.config/vivaldi/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/History*',
            '*/.config/opera/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/History*',
            '*/Library/Application Support/com.operasoftware.Opera/History*',
            '*/.config/opera/History*',
        ),
        "output_types": "standard",
        "artifact_icon": "link",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 646 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 737 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumDownloads": {
        "name": "Chromium Downloads",
        "description": "Rows of the downloads table from the History databases of Google Chrome, "
                       "Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles, with the target "
                       "path, the URL chain, sizes and the stored state, danger type and interrupt "
                       "reason.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the downloads table of each History database in a Chromium-based browser profile, "
                 "with the URL chain from downloads_url_chains; one row per downloads row. Browser, "
                 "Profile and User come from the path: the browser from the user data folder, the profile "
                 "from the folder inside it, and the user from the home folder that holds it; Source File "
                 "names the file each row came from, so rows from two profiles or two users stay apart. A "
                 "profile under User Data/Snapshots/<version>/ is reported with that path as its Profile, "
                 "so a snapshot copy is not merged with the live profile; no registered image carries one, "
                 "and that branch was exercised on a constructed tree only. Start Time, End Time and Last "
                 "Access Time are downloads.start_time, end_time and last_access_time, microseconds since "
                 "1601-01-01 UTC. Current Chromium binds them with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/download_database.cc#L689-L700), "
                 "which stores ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for the same columns "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/download_database.cc#L636-L648), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "Chromium fills these columns from the download item's own fields "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/chrome/browser/download/download_history.cc#L144-L169), "
                 "and download_item.h describes the last access time as empty for a download never opened "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/download/public/common/download_item.h#L542-L544), "
                 "and on the tested images Last Access Time was filled on exactly the rows whose Opened is "
                 "Yes: 5 of 19 on pc_mus_001_win11 and 3 of 17 on lonewolf_win10. Final URL is the last "
                 "URL of the download's chain and Original URL the first, ordered by chain_index; "
                 "download_item.h names the tail of the chain as the URL the file is downloaded from and "
                 "the head as the URL first requested "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/download/public/common/download_item.h#L288-L306). "
                 "URL Chain Length is the number of chain rows. Tab URL is downloads.tab_url, described in "
                 "download_item.h as the top level frame's URL when the download was initiated (same file, "
                 "lines 316 and 317), and Referrer is downloads.referrer as stored. Target Path and "
                 "Current Path are target_path and current_path, which the schema comments call the final "
                 "and the current disk location "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/download_database.cc#L326-L327); "
                 "download_item.h describes the current file as possibly an intermediate one while the "
                 "download is in progress "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/download/public/common/download_item.h#L376-L393). "
                 "Target Path and Current Path were identical on every row, and Received Bytes and Total "
                 "Bytes were the same value on every row, of both pc_mus_001_win11 and lonewolf_win10, "
                 "where every download has State COMPLETE (1). State, Danger Type and Interrupt Reason "
                 "show the stored integer with its name from download_constants.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/download_constants.h#L15-L55) "
                 "and from download_interrupt_reasons.h line 17 and download_interrupt_reason_values.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/download/public/common/download_interrupt_reason_values.h#L16-L148). "
                 "State held one value, COMPLETE (1), and Interrupt Reason held one value, NONE (0), on "
                 "every row of the tested images; Danger Type was MAYBE_DANGEROUS_CONTENT (4) on 1 row of "
                 "pc_mus_001_win11 and 3 rows of lonewolf_win10 and NOT_DANGEROUS (0) on the rest. Not "
                 "reported: downloads.hash, which Chromium's schema comment calls the SHA-256 of the "
                 "contents "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/download_database.cc#L334), "
                 "was empty on every row of the tested images. A database left with a rollback journal "
                 "that SQLite treats as hot cannot be opened read only, because replaying the journal "
                 "writes to the database; such a database is read as found, with the journal ignored, and "
                 "the run log says so. The lonewolf_win10 Chrome History is one: read that way it passes "
                 "SQLite's integrity_check, while rolling its journal back on a scratch copy left the copy "
                 "malformed. Browser, Profile and User each held one value on every row of lonewolf_win10, "
                 "which carries one Chrome profile in one home folder, and User held one value on every "
                 "row of pc_mus_001_win11, whose Chrome and Edge profiles sit in one home folder. Tested: "
                 "Chrome 108.0.5359.125 (profiles Default and Profile 2; the System Profile and Guest "
                 "Profile History databases held no visits, URLs, downloads or search terms) and Microsoft "
                 "Edge 108.0.1462.54 (profile Default) on pc_mus_001_win11, and Chrome 65.0.3325.181 "
                 "(profile Default) on lonewolf_win10. No member of af_case2_win10 or dleapp_macos_bigsur "
                 "matched any of the declared paths. The user data folders read are those of Google "
                 "Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux, "
                 "and a store directly inside a user data folder is reported with that folder as its "
                 "Profile. Only the Windows Google Chrome and Microsoft Edge folders were exercised by a "
                 "registered image; a constructed tree exercised the Brave macOS, Vivaldi Linux and Opera "
                 "Windows folders, the last with its profile kept directly in the user data folder, and "
                 "the remaining folders were not exercised. Not read: other Chrome channels (Beta, Dev, "
                 "Canary), extension storage partitions under a profile's Storage folder, and WebView2 or "
                 "Electron app profiles such as EBWebView folders, which share the layout but sit in other "
                 "applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/History*',
            '*/Library/Application Support/Google/Chrome/*/History*',
            '*/.config/google-chrome/*/History*',
            '*/AppData/Local/Chromium/User Data/*/History*',
            '*/Library/Application Support/Chromium/*/History*',
            '*/.config/chromium/*/History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History*',
            '*/Library/Application Support/Microsoft Edge/*/History*',
            '*/.config/microsoft-edge/*/History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History*',
            '*/.config/BraveSoftware/Brave-Browser/*/History*',
            '*/AppData/Local/Vivaldi/User Data/*/History*',
            '*/Library/Application Support/Vivaldi/*/History*',
            '*/.config/vivaldi/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/History*',
            '*/.config/opera/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/History*',
            '*/Library/Application Support/com.operasoftware.Opera/History*',
            '*/.config/opera/History*',
        ),
        "output_types": "standard",
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 17 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumSearchTerms": {
        "name": "Chromium Search Terms",
        "description": "Rows of the keyword_search_terms table from the History databases of Google "
                       "Chrome, Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles, with the "
                       "search engine where the same profile's Web Data holds the stored keyword id.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the keyword_search_terms table of each History database in a Chromium-based "
                 "browser profile, joined to urls on url_id; one row per keyword_search_terms row. Search "
                 "Term is keyword_search_terms.term, described in keyword_search_term.h as the search term "
                 "that was used "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/keyword_search_term.h#L43-L45). "
                 "URL Last Visit Time is urls.last_visit_time of the search URL, microseconds since "
                 "1601-01-01 UTC, which current Chromium binds with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/url_database.cc#L217, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "it is the last visit to that URL, not a time stored for the term, and URL Visit Count is "
                 "that URL's urls.visit_count. Search Engine and Search Engine Keyword are "
                 "keywords.short_name and keywords.keyword from the Web Data database of the same profile, "
                 "matched on keyword_id: keyword_id is a search engine (TemplateURL) id "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/keyword_id.h#L16) "
                 "and keywords.id is the key of the keywords table "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/search_engines/keyword_table.cc#L256-L259). "
                 "Every row of the tested images matched a keywords row of its own profile: 62 of 62 on "
                 "pc_mus_001_win11 and 190 of 190 on lonewolf_win10. Both columns are blank where the "
                 "profile has no Web Data or no matching row; the located-at line lists the Web Data of "
                 "each profile whose History was read. Browser, Profile and User come from the path: the "
                 "browser from the user data folder, the profile from the folder inside it, and the user "
                 "from the home folder that holds it; Source File names the file each row came from, so "
                 "rows from two profiles or two users stay apart. A profile under User "
                 "Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot copy "
                 "is not merged with the live profile; no registered image carries one, and that branch "
                 "was exercised on a constructed tree only. A database left with a rollback journal that "
                 "SQLite treats as hot cannot be opened read only, because replaying the journal writes to "
                 "the database; such a database is read as found, with the journal ignored, and the run "
                 "log says so. The lonewolf_win10 Chrome History is one: read that way it passes SQLite's "
                 "integrity_check, while rolling its journal back on a scratch copy left the copy "
                 "malformed. Browser, Profile and User each held one value on every row of lonewolf_win10, "
                 "which carries one Chrome profile in one home folder, and User held one value on every "
                 "row of pc_mus_001_win11, whose Chrome and Edge profiles sit in one home folder. Tested: "
                 "Chrome 108.0.5359.125 (profiles Default and Profile 2; the System Profile and Guest "
                 "Profile History databases held no visits, URLs, downloads or search terms) and Microsoft "
                 "Edge 108.0.1462.54 (profile Default) on pc_mus_001_win11, and Chrome 65.0.3325.181 "
                 "(profile Default) on lonewolf_win10. No member of af_case2_win10 or dleapp_macos_bigsur "
                 "matched any of the declared paths. The user data folders read are those of Google "
                 "Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux, "
                 "and a store directly inside a user data folder is reported with that folder as its "
                 "Profile. Only the Windows Google Chrome and Microsoft Edge folders were exercised by a "
                 "registered image; a constructed tree exercised the Brave macOS, Vivaldi Linux and Opera "
                 "Windows folders, the last with its profile kept directly in the user data folder, and "
                 "the remaining folders were not exercised. Not read: other Chrome channels (Beta, Dev, "
                 "Canary), extension storage partitions under a profile's Storage folder, and WebView2 or "
                 "Electron app profiles such as EBWebView folders, which share the layout but sit in other "
                 "applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/History*',
            '*/Library/Application Support/Google/Chrome/*/History*',
            '*/.config/google-chrome/*/History*',
            '*/AppData/Local/Chromium/User Data/*/History*',
            '*/Library/Application Support/Chromium/*/History*',
            '*/.config/chromium/*/History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History*',
            '*/Library/Application Support/Microsoft Edge/*/History*',
            '*/.config/microsoft-edge/*/History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History*',
            '*/.config/BraveSoftware/Brave-Browser/*/History*',
            '*/AppData/Local/Vivaldi/User Data/*/History*',
            '*/Library/Application Support/Vivaldi/*/History*',
            '*/.config/vivaldi/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/History*',
            '*/.config/opera/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/History*',
            '*/Library/Application Support/com.operasoftware.Opera/History*',
            '*/.config/opera/History*',
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
        "artifact_icon": "search",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 62 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 190 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (enum_label, open_store,
                                               profile_stores, row_tail, select_list,
                                               table_columns, webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc

# ui/base/page_transition_types.h, lines 30 to 108 (core types) and 119 to 155
# (qualifiers), chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4.
_CORE_TRANSITIONS = {
    0: 'LINK', 1: 'TYPED', 2: 'AUTO_BOOKMARK', 3: 'AUTO_SUBFRAME', 4: 'MANUAL_SUBFRAME',
    5: 'GENERATED', 6: 'AUTO_TOPLEVEL', 7: 'FORM_SUBMIT', 8: 'RELOAD', 9: 'KEYWORD',
    10: 'KEYWORD_GENERATED',
}
_QUALIFIERS = (
    (0x00200000, 'FROM_API_3'),
    (0x00400000, 'FROM_API_2'),
    (0x00800000, 'BLOCKED'),
    (0x01000000, 'FORWARD_BACK'),
    (0x02000000, 'FROM_ADDRESS_BAR'),
    (0x04000000, 'HOME_PAGE'),
    (0x08000000, 'FROM_API'),
    (0x10000000, 'CHAIN_START'),
    (0x20000000, 'CHAIN_END'),
    (0x40000000, 'CLIENT_REDIRECT'),
    (0x80000000, 'SERVER_REDIRECT'),
)
_KNOWN_BITS = 0xFF | sum(mask for mask, _ in _QUALIFIERS)

# components/history/core/browser/history_types.h, lines 50 to 59.
_VISIT_SOURCES = {
    0: 'SYNCED', 1: 'BROWSED', 2: 'EXTENSION', 3: 'FIREFOX_IMPORTED', 4: 'IE_IMPORTED',
    5: 'SAFARI_IMPORTED', 6: 'ACTOR', 7: 'OS_MIGRATION_IMPORTED',
}

# components/history/core/browser/download_constants.h, lines 15 to 55.
_DOWNLOAD_STATES = {0: 'IN_PROGRESS', 1: 'COMPLETE', 2: 'CANCELLED', 3: 'BUG_140687', 4: 'INTERRUPTED'}
_DANGER_TYPES = {
    0: 'NOT_DANGEROUS', 1: 'DANGEROUS_FILE', 2: 'DANGEROUS_URL', 3: 'DANGEROUS_CONTENT',
    4: 'MAYBE_DANGEROUS_CONTENT', 5: 'UNCOMMON_CONTENT', 6: 'USER_VALIDATED',
    7: 'DANGEROUS_HOST', 8: 'POTENTIALLY_UNWANTED', 9: 'ALLOWLISTED_BY_POLICY',
    10: 'ASYNC_SCANNING', 11: 'BLOCKED_PASSWORD_PROTECTED', 12: 'BLOCKED_TOO_LARGE',
    13: 'SENSITIVE_CONTENT_WARNING', 14: 'SENSITIVE_CONTENT_BLOCK', 15: 'DEEP_SCANNED_SAFE',
    16: 'DEEP_SCANNED_OPENED_DANGEROUS', 17: 'PROMPT_FOR_SCANNING',
    18: 'BLOCKED_UNSUPPORTED_FILETYPE', 19: 'DANGEROUS_ACCOUNT_COMPROMISE',
    20: 'DEEP_SCANNED_FAILED', 21: 'PROMPT_FOR_LOCAL_PASSWORD_SCANNING',
    22: 'ASYNC_LOCAL_PASSWORD_SCANNING', 23: 'BLOCKED_SCAN_FAILED', 24: 'FORCED_SAVE_TO_GDRIVE',
    25: 'FORCED_SAVE_TO_ONEDRIVE',
}
# components/download/public/common/download_interrupt_reasons.h, line 17 (NONE), and
# download_interrupt_reason_values.h, lines 16 to 148.
_INTERRUPT_REASONS = {
    0: 'NONE', 1: 'FILE_FAILED', 2: 'FILE_ACCESS_DENIED', 3: 'FILE_NO_SPACE',
    5: 'FILE_NAME_TOO_LONG', 6: 'FILE_TOO_LARGE', 7: 'FILE_VIRUS_INFECTED',
    10: 'FILE_TRANSIENT_ERROR', 11: 'FILE_BLOCKED', 12: 'FILE_SECURITY_CHECK_FAILED',
    13: 'FILE_TOO_SHORT', 14: 'FILE_HASH_MISMATCH', 15: 'FILE_SAME_AS_SOURCE',
    20: 'NETWORK_FAILED', 21: 'NETWORK_TIMEOUT', 22: 'NETWORK_DISCONNECTED',
    23: 'NETWORK_SERVER_DOWN', 24: 'NETWORK_INVALID_REQUEST', 30: 'SERVER_FAILED',
    31: 'SERVER_NO_RANGE', 32: 'SERVER_PRECONDITION', 33: 'SERVER_BAD_CONTENT',
    34: 'SERVER_UNAUTHORIZED', 35: 'SERVER_CERT_PROBLEM', 36: 'SERVER_FORBIDDEN',
    37: 'SERVER_UNREACHABLE', 38: 'SERVER_CONTENT_LENGTH_MISMATCH',
    39: 'SERVER_CROSS_ORIGIN_REDIRECT', 40: 'USER_CANCELED', 41: 'USER_SHUTDOWN', 50: 'CRASH',
    51: 'LOCAL_DOWNLOAD_BLOCKED',
}


def _transition(value):
    """Core type and qualifier names of a stored visits.transition value."""
    if value is None:
        return '', ''
    bits = int(value) & 0xFFFFFFFF
    core = bits & 0xFF
    qualifiers = [name for mask, name in _QUALIFIERS if bits & mask]
    other = bits & ~_KNOWN_BITS & 0xFFFFFFFF
    if other:
        qualifiers.append(f'other bits 0x{other:08X}')
    return enum_label(_CORE_TRANSITIONS, core), ', '.join(qualifiers)


def _yes_no(value):
    if value is None or value == '':
        return ''
    return 'Yes' if int(value) else 'No'


def _seconds(microseconds):
    if microseconds is None or microseconds == '':
        return ''
    return int(microseconds) / 1_000_000


@artifact_processor
def chromiumWebVisits(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'History'}):
        db = open_store(store, 'Chromium Web Visits')
        if db is None:
            continue
        try:
            has_source = bool(table_columns(db, 'visit_source'))
            source_columns = 'visit_source.id, visit_source.source' if has_source else 'NULL, NULL'
            source_join = ('LEFT JOIN visit_source ON visit_source.id = visits.id'
                           if has_source else '')
            rows = db.execute(f'''
                SELECT visits.id, visits.visit_time, urls.url, urls.title, visits.transition,
                       {source_columns}, visits.visit_duration, referrer_urls.url
                FROM visits
                LEFT JOIN urls ON urls.id = visits.url
                {source_join}
                LEFT JOIN visits AS referrer
                       ON referrer.id = visits.from_visit AND visits.from_visit > 0
                LEFT JOIN urls AS referrer_urls ON referrer_urls.id = referrer.url
                ORDER BY visits.visit_time, visits.id''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Web Visits: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for (visit_id, visit_time, url, title, transition, source_row, source, duration,
             referrer_url) in rows:
            core, qualifiers = _transition(transition)
            if not has_source:
                visit_source = ''
            elif source_row is None:
                visit_source = 'BROWSED (no visit_source row)'
            else:
                visit_source = enum_label(_VISIT_SOURCES, source)
            data_list.append((webkit_time(visit_time), url, title, core, qualifiers,
                              visit_source, _seconds(duration), referrer_url or '',
                              visit_id) + row_tail(store))
    data_headers = (('Visit Time', 'datetime'), 'URL', 'Title', 'Transition',
                    'Transition Qualifiers', 'Visit Source', 'Visit Duration (seconds)',
                    'Referring URL', 'Visit ID', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumUrls(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'History'}):
        db = open_store(store, 'Chromium URLs')
        if db is None:
            continue
        try:
            rows = db.execute('''
                SELECT last_visit_time, url, title, visit_count, typed_count, hidden, id
                FROM urls ORDER BY last_visit_time, id''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium URLs: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for last_visit, url, title, visit_count, typed_count, hidden, url_id in rows:
            data_list.append((webkit_time(last_visit), url, title, visit_count, typed_count,
                              _yes_no(hidden), url_id) + row_tail(store))
    data_headers = (('Last Visit Time', 'datetime'), 'URL', 'Title', 'Visit Count',
                    'Typed Count', 'Hidden', 'URL ID', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)


_DOWNLOAD_COLUMNS = ('id', 'start_time', 'end_time', 'last_access_time', 'target_path',
                     'current_path', 'tab_url', 'referrer', 'mime_type', 'received_bytes',
                     'total_bytes', 'state', 'danger_type', 'interrupt_reason', 'opened')


@artifact_processor
def chromiumDownloads(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'History'}):
        db = open_store(store, 'Chromium Downloads')
        if db is None:
            continue
        try:
            present = table_columns(db, 'downloads')
            if not present:
                continue
            rows = db.execute(f'SELECT {select_list(present, _DOWNLOAD_COLUMNS)} '
                              f'FROM downloads ORDER BY start_time, id').fetchall()
            chains = {}
            if table_columns(db, 'downloads_url_chains'):
                for download_id, _, url in db.execute(
                        'SELECT id, chain_index, url FROM downloads_url_chains '
                        'ORDER BY id, chain_index'):
                    chains.setdefault(download_id, []).append(url)
        except sqlite3.Error as ex:
            logfunc(f'Chromium Downloads: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for (download_id, start, end, last_access, target_path, current_path, tab_url,
             referrer, mime_type, received, total, state, danger, interrupt,
             opened) in rows:
            chain = chains.get(download_id, [])
            data_list.append((webkit_time(start), webkit_time(end), webkit_time(last_access),
                              target_path, current_path, chain[-1] if chain else '',
                              chain[0] if chain else '', len(chain), tab_url or '',
                              referrer or '', mime_type or '', received, total,
                              enum_label(_DOWNLOAD_STATES, state),
                              enum_label(_DANGER_TYPES, danger),
                              enum_label(_INTERRUPT_REASONS, interrupt), _yes_no(opened),
                              download_id) + row_tail(store))
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    ('Last Access Time', 'datetime'), 'Target Path', 'Current Path',
                    'Final URL', 'Original URL', 'URL Chain Length', 'Tab URL', 'Referrer',
                    'MIME Type', 'Received Bytes', 'Total Bytes', 'State', 'Danger Type',
                    'Interrupt Reason', 'Opened', 'Download ID', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)


def _search_engines(stores):
    """Keyword id to (short name, keyword) from each profile's Web Data, keyed by profile."""
    engines = {}
    read = {}
    for store in stores:
        db = open_store(store, 'Chromium Search Terms')
        if db is None:
            continue
        try:
            if table_columns(db, 'keywords'):
                engines[store.container] = {
                    row[0]: (row[1], row[2]) for row in
                    db.execute('SELECT id, short_name, keyword FROM keywords')}
                read[store.container] = store.path
        except sqlite3.Error as ex:
            logfunc(f'Chromium Search Terms: could not read {store.relative}: {ex}')
        finally:
            db.close()
    return engines, read


@artifact_processor
def chromiumSearchTerms(context):
    data_list = []
    sources = []
    engines, web_data = _search_engines(profile_stores(context, {'Web Data'}))
    for store in profile_stores(context, {'History'}):
        db = open_store(store, 'Chromium Search Terms')
        if db is None:
            continue
        try:
            if not table_columns(db, 'keyword_search_terms'):
                continue
            rows = db.execute('''
                SELECT urls.last_visit_time, keyword_search_terms.term,
                       keyword_search_terms.keyword_id, urls.url, urls.visit_count
                FROM keyword_search_terms
                LEFT JOIN urls ON urls.id = keyword_search_terms.url_id
                ORDER BY urls.last_visit_time, keyword_search_terms.url_id''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Search Terms: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        profile_engines = engines.get(store.container, {})
        if store.container in web_data:
            sources.append(web_data[store.container])
        for last_visit, term, keyword_id, url, visit_count in rows:
            short_name, keyword = profile_engines.get(keyword_id, ('', ''))
            data_list.append((webkit_time(last_visit), term, short_name, keyword, url or '',
                              visit_count, keyword_id) + row_tail(store))
    data_headers = (('URL Last Visit Time', 'datetime'), 'Search Term', 'Search Engine',
                    'Search Engine Keyword', 'Search URL', 'URL Visit Count', 'Keyword ID',
                    'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
