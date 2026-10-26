__artifacts_v2__ = {
    "chromiumTopSites": {
        "name": "Chromium Top Sites",
        "description": "Ranked sites from the Top Sites databases of Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles, from the top_sites table or the "
                       "older thumbnails table, with the stored page thumbnail where the older table "
                       "holds one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads each Chromium-based browser profile's Top Sites database: the top_sites table of "
                 "current releases, or the thumbnails table the Chrome 65 release kept instead; one row "
                 "per table row. Browser, Profile and User come from the path: the browser from the user "
                 "data folder, the profile from the folder inside it, and the user from the home folder "
                 "that holds it; Source File names the file each row came from, since Browser, "
                 "Profile and User do not separate two copies of one profile, which a logical "
                 "extraction can hold under Users/ and System/Volumes/Data/Users/. A profile under"
                 " User Data/Snapshots/<version>/ is reported with "
                 "that path as its Profile, so a snapshot copy is not merged with the live profile; no "
                 "registered image carries one, and that branch was exercised on a constructed tree only. "
                 "Rank is url_rank as stored. The current source describes it as a 0-based index where the "
                 "site with the highest rank is the next one evicted "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/top_sites_database.cc#L34-L38), "
                 "and the Chrome 65 source gives forced thumbnails a rank of -1 "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/top_sites_database.cc#L29-L47). "
                 "Last Updated, Thumbnail and Last Forced come from the thumbnails table only, so they are "
                 "blank on every row read from a top_sites table, which holds url, url_rank and title "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/history/core/browser/top_sites_database.cc#L66-L69), "
                 "as on every row of pc_mus_001_win11. Last Updated is thumbnails.last_updated and Last "
                 "Forced is thumbnails.last_forced, both bound with since_origin().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/top_sites_database.cc#L523-L530), "
                 "which returns the internal value "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L368-L370), "
                 "microseconds since 1601-01-01 UTC (same file, lines 5 to 7); a zero value is shown "
                 "blank. Thumbnail renders the thumbnail blob as media where the row holds one: 5 of the "
                 "16 rows of lonewolf_win10, each a JPEG. On lonewolf_win10, 6 rows have rank -1 and those "
                 "6 carry Last Forced. A database left with a rollback journal that SQLite treats as hot "
                 "cannot be opened read only, because replaying the journal writes to the database; such a "
                 "database is read as found, with the journal ignored, and the run log says so. No "
                 "database read by this artifact on the tested images had one. Browser, Profile and User "
                 "each held one value on every row of lonewolf_win10, which carries one Chrome profile in "
                 "one home folder, and User held one value on every row of pc_mus_001_win11, whose Chrome "
                 "and Edge profiles sit in one home folder. Tested: Chrome 108.0.5359.125 and Microsoft "
                 "Edge 108.0.1462.54 on pc_mus_001_win11 (top_sites, 9 rows), and Chrome 65.0.3325.181 on "
                 "lonewolf_win10 (thumbnails, 16 rows). No member of af_case2_win10, szechuan_win10 or dleapp_macos_bigsur "
                 "matched any of the declared paths. The user data folders read are those of Google "
                 "Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, macOS and Linux, "
                 "and a store directly inside an Opera user data folder is reported with that "
                 "folder as its Profile. Only the Windows Google Chrome and Microsoft Edge "
                 "folders and the Linux Chromium snap and Flatpak folders were exercised by a registered image, "
                 "the last two by ubuntu2604_arm64_chromium; a constructed tree exercised the Brave macOS, Vivaldi "
                 "Linux and Opera "
                 "Windows folders, the last with its profile kept directly in the user data "
                 "folder, and the remaining folders were exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome channels (Beta, Dev, "
                 "Canary), extension storage partitions under a profile's Storage folder, and WebView2 or "
                 "Electron app profiles such as EBWebView folders, which share the layout but sit in other "
                 "applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag."
                 " Chromium installed as a snap keeps its user data folder in snap/chromium/common/chromium in the "
                 "home folder, because Chromium keeps it in a chromium folder inside CHROME_CONFIG_HOME, else "
                 "XDG_CONFIG_HOME, else .config "
                 "(Reference: Chromium, 'chrome_paths_linux.cc', "
                 "https://github.com/chromium/chromium/blob/73934a44f61e6b3878d1943064c141a5a820f5f7/chrome/common/chrome_paths_linux.cc#L62-L101) "
                 "and the snap's snap.yaml sets CHROME_CONFIG_HOME to the snap's common folder (measured on "
                 "revision 3535); installed as a Flatpak from Flathub it keeps it in "
                 ".var/app/org.chromium.Chromium/config/chromium, because Flatpak sets XDG_CONFIG_HOME to the "
                 "config folder in the app's folder (Reference: flatpak 1.16.6, 'flatpak-context.c', "
                 "https://github.com/flatpak/flatpak/blob/e761a8885453c217a931281092a641ebbdd0a0c6/common/flatpak-context.c#L3168-L3175). "
                 "Both are read as Chromium, measured on ubuntu2604_arm64_chromium, whose snap (Chromium "
                 "153.0.8010.47) and Flatpak (Chromium 154.0.8037.57) each kept a Default profile there. Other "
                 "browsers' Flatpaks are not read. A profile in a .config folder that is not directly in a home "
                 "folder, such as a snap's snap/<name>/<revision>/.config, is matched by the .config paths and "
                 "read with User blank. On ubuntu2604_arm64_chromium Browser, "
                 "Profile and User each held one value, Chromium, Default and parallels, on every row."
                 " The folder webbrowser/chrome, which an LG webOS TV keeps on the volume it mounts at"
                 " /mnt/lg/cmn_data, is read as the user data folder of a browser named webOS webbrowser (field"
                 " mapped from a private sample); which app writes it is not established, and User is blank for it,"
                 " since it sits in no home folder.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Top Sites*',
            '*/Library/Application Support/Google/Chrome/*/Top Sites*',
            '*/.config/google-chrome/*/Top Sites*',
            '*/AppData/Local/Chromium/User Data/*/Top Sites*',
            '*/Library/Application Support/Chromium/*/Top Sites*',
            '*/.config/chromium/*/Top Sites*',
            '*/snap/chromium/common/chromium/*/Top Sites*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Top Sites*',
            '*/webbrowser/chrome/*/Top Sites*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Top Sites*',
            '*/Library/Application Support/Microsoft Edge/*/Top Sites*',
            '*/.config/microsoft-edge/*/Top Sites*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Top Sites*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Top Sites*',
            '*/.config/BraveSoftware/Brave-Browser/*/Top Sites*',
            '*/AppData/Local/Vivaldi/User Data/*/Top Sites*',
            '*/Library/Application Support/Vivaldi/*/Top Sites*',
            '*/.config/vivaldi/*/Top Sites*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Top Sites*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Top Sites*',
            '*/.config/opera/*/Top Sites*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Top Sites*',
            '*/Library/Application Support/com.operasoftware.Opera/Top Sites*',
            '*/.config/opera/Top Sites*',
        ),
        "output_types": "standard",
        "artifact_icon": "star",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 16 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 4 rows",
        },
    },
    "chromiumShortcuts": {
        "name": "Chromium Omnibox Shortcuts",
        "description": "Rows of the omni_box_shortcuts table from the Shortcuts databases of Google "
                       "Chrome, Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles: the stored "
                       "input text, the URL and the fill_into_edit, contents and description text stored "
                       "with it, its hit count, match type, transition and keyword, and its last access "
                       "time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-10-26",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the omni_box_shortcuts table of each Chromium-based browser profile's Shortcuts "
                 "database; one row per table row. Browser, Profile and User come from the path: the "
                 "browser from the user data folder, the profile from the folder inside it, and the user "
                 "from the home folder that holds it; Source File names the file each row came "
                 "from, since Browser, Profile and User do not separate two copies of one profile,"
                 " which a logical extraction can hold under Users/ and "
                 "System/Volumes/Data/Users/. A profile under User "
                 "Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot copy "
                 "is not merged with the live profile; no registered image carries one, and that branch "
                 "was exercised on a constructed tree only. Last Access Time is last_access_time, "
                 "microseconds since 1601-01-01 UTC. Current Chromium binds it with Statement::BindTime "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.cc#L48), "
                 "which stores what Statement::TimeToSqlValue returns "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L300-L316), "
                 "ToDeltaSinceWindowsEpoch().InMicroseconds() "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L42-L44); "
                 "the Chrome 65 release wrote base::Time::ToInternalValue for it "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/omnibox/browser/shortcuts_database.cc#L46), "
                 "which base/time/time.h describes as microseconds since the Windows epoch, 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "The comment at the top of the current shortcuts_database.h says the time is stored in "
                 "seconds "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.h#L26-L39); "
                 "the writer binds it as above, and on both tested images the values decode to dates "
                 "within the range of that image's History visit times. Input Text is the text column, "
                 "which shortcuts_database.h calls the original input string, and Hits is number_of_hits, "
                 "which it describes as how many times the shortcut was selected "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.h#L86-L89). "
                 "The stored text need not match what was entered: current Chromium trims trailing "
                 "whitespace, and on reusing a shortcut replaces its text from the new input while adding "
                 "one to its hits "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_backend.cc#L322-L404). "
                 "Fill Into Edit, URL, Contents and Description are the fill_into_edit, url, contents and "
                 "description columns as stored. Match Type is the type column, an AutocompleteMatchType "
                 "value, shown as stored with the name the enum gives it; the header says these values "
                 "are stored in ShortcutsDatabase and cannot be renumbered "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/autocomplete_match_type.h#L16-L17). The names are those of "
                 "the current enum. The writer's version 1 migration rewrote stored types 9 to 12 as 13 "
                 "to 16 (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.cc#L390-L397), so in a "
                 "database with no meta table, or whose meta table carries no readable version, "
                 "neither of which has run it, values 9 to 12 are named by the "
                 "value they migrate to and marked as pre-migration numbering; no tested database was "
                 "at that version. The migration from the first table version filled transition with 1 "
                 "and type with 2 on every existing row "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.cc#L379-L383), so on a database "
                 "upgraded from it those two values can be the upgrade's default. Transition is the "
                 "transition column, a ui::PageTransition value: the name is that of its low byte, the "
                 "core value, and any higher qualifier bits are shown in hex as the unsigned 32-bit value; "
                 "no tested row carried one, so that branch is unexercised "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/ui/base/page_transition_types.h#L113). Keyword is the keyword column as stored. The "
                 "writer binds all three (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.cc#L45-L47). "
                 "On pc_mus_001_win11 the pairs were 7 (SEARCH_HISTORY) with 5 (GENERATED) on 51 rows, "
                 "1 (HISTORY_URL) with 1 (TYPED) on 4 and 1 (HISTORY_URL) with 0 (LINK) on 1; on "
                 "lonewolf_win10 7 (SEARCH_HISTORY) with 5 (GENERATED) on 89 and 1 (HISTORY_URL) with 1 "
                 "(TYPED) on 14; no qualifier bits were set. Keyword was blank on 5 rows of "
                 "pc_mus_001_win11 and 14 of lonewolf_win10. Chromium's first table version lacked these "
                 "columns (https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/omnibox/browser/shortcuts_database.cc#L312-L313); a database "
                 "whose table lacks one of them reports it blank. No tested database lacked one, so that "
                 "branch is unexercised. "
                 "Hits held one value, 1, on every row of pc_mus_001_win11 "
                 "and ran from 1 to 4 on lonewolf_win10. A database left with a rollback journal that "
                 "SQLite treats as hot cannot be opened read only, because replaying the journal writes to "
                 "the database; such a database is read as found, with the journal ignored, and the run "
                 "log says so. No database read by this artifact on the tested images had one. Browser, "
                 "Profile and User each held one value on every row of lonewolf_win10, which carries one "
                 "Chrome profile in one home folder, and User held one value on every row of "
                 "pc_mus_001_win11, whose Chrome and Edge profiles sit in one home folder. Tested: Chrome "
                 "108.0.5359.125 and Microsoft Edge 108.0.1462.54 on pc_mus_001_win11 (database version "
                 "2), and Chrome 65.0.3325.181 on lonewolf_win10 (version 1). No member of af_case2_win10, "
                 "szechuan_win10 or dleapp_macos_bigsur matched any of the declared paths. The user data "
                 "folders read are "
                 "those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, "
                 "macOS and Linux, and a store directly inside an Opera user data folder is "
                 "reported with that folder as its Profile. Only the Windows Google Chrome and "
                 "Microsoft Edge folders and the Linux Chromium snap and Flatpak folders were exercised by a "
                 "registered image, the last two by ubuntu2604_arm64_chromium; a constructed tree exercised the "
                 "Brave macOS, Vivaldi "
                 "Linux and Opera Windows folders, the last with its profile kept directly in the user "
                 "data folder, and the remaining folders were exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome "
                 "channels (Beta, Dev, Canary), extension storage partitions under a profile's Storage "
                 "folder, and WebView2 or Electron app profiles such as EBWebView folders, which share the "
                 "layout but sit in other applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag."
                 " Chromium installed as a snap keeps its user data folder in snap/chromium/common/chromium in the "
                 "home folder, because Chromium keeps it in a chromium folder inside CHROME_CONFIG_HOME, else "
                 "XDG_CONFIG_HOME, else .config "
                 "(Reference: Chromium, 'chrome_paths_linux.cc', "
                 "https://github.com/chromium/chromium/blob/73934a44f61e6b3878d1943064c141a5a820f5f7/chrome/common/chrome_paths_linux.cc#L62-L101) "
                 "and the snap's snap.yaml sets CHROME_CONFIG_HOME to the snap's common folder (measured on "
                 "revision 3535); installed as a Flatpak from Flathub it keeps it in "
                 ".var/app/org.chromium.Chromium/config/chromium, because Flatpak sets XDG_CONFIG_HOME to the "
                 "config folder in the app's folder (Reference: flatpak 1.16.6, 'flatpak-context.c', "
                 "https://github.com/flatpak/flatpak/blob/e761a8885453c217a931281092a641ebbdd0a0c6/common/flatpak-context.c#L3168-L3175). "
                 "Both are read as Chromium, measured on ubuntu2604_arm64_chromium, whose snap (Chromium "
                 "153.0.8010.47) and Flatpak (Chromium 154.0.8037.57) each kept a Default profile there. Other "
                 "browsers' Flatpaks are not read. A profile in a .config folder that is not directly in a home "
                 "folder, such as a snap's snap/<name>/<revision>/.config, is matched by the .config paths and "
                 "read with User blank."
                 " The folder webbrowser/chrome, which an LG webOS TV keeps on the volume it mounts at"
                 " /mnt/lg/cmn_data, is read as the user data folder of a browser named webOS webbrowser (field"
                 " mapped from a private sample); which app writes it is not established, and User is blank for it,"
                 " since it sits in no home folder.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Shortcuts*',
            '*/Library/Application Support/Google/Chrome/*/Shortcuts*',
            '*/.config/google-chrome/*/Shortcuts*',
            '*/AppData/Local/Chromium/User Data/*/Shortcuts*',
            '*/Library/Application Support/Chromium/*/Shortcuts*',
            '*/.config/chromium/*/Shortcuts*',
            '*/snap/chromium/common/chromium/*/Shortcuts*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Shortcuts*',
            '*/webbrowser/chrome/*/Shortcuts*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Shortcuts*',
            '*/Library/Application Support/Microsoft Edge/*/Shortcuts*',
            '*/.config/microsoft-edge/*/Shortcuts*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Shortcuts*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Shortcuts*',
            '*/.config/BraveSoftware/Brave-Browser/*/Shortcuts*',
            '*/AppData/Local/Vivaldi/User Data/*/Shortcuts*',
            '*/Library/Application Support/Vivaldi/*/Shortcuts*',
            '*/.config/vivaldi/*/Shortcuts*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Shortcuts*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Shortcuts*',
            '*/.config/opera/*/Shortcuts*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Shortcuts*',
            '*/Library/Application Support/com.operasoftware.Opera/Shortcuts*',
            '*/.config/opera/Shortcuts*',
        ),
        "output_types": "standard",
        "artifact_icon": "keyboard",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 56 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 103 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores, row_tail,
                                               select_list, table_columns, webkit_time)
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc


# Chromium at 33f34ef179f55596f6c2fc8a55878b7ccf6276e4.
# ui/base/page_transition_types.h: the core transition is the low byte of the stored value.
_TRANSITIONS = {
    0: 'LINK', 1: 'TYPED', 2: 'AUTO_BOOKMARK', 3: 'AUTO_SUBFRAME', 4: 'MANUAL_SUBFRAME',
    5: 'GENERATED', 6: 'AUTO_TOPLEVEL', 7: 'FORM_SUBMIT', 8: 'RELOAD', 9: 'KEYWORD',
    10: 'KEYWORD_GENERATED',
}
# components/omnibox/browser/autocomplete_match_type.h
_MATCH_TYPES = {
    0: 'URL_WHAT_YOU_TYPED', 1: 'HISTORY_URL', 2: 'HISTORY_TITLE', 3: 'HISTORY_BODY',
    4: 'HISTORY_KEYWORD', 5: 'NAVSUGGEST', 6: 'SEARCH_WHAT_YOU_TYPED', 7: 'SEARCH_HISTORY',
    8: 'SEARCH_SUGGEST', 9: 'SEARCH_SUGGEST_ENTITY', 10: 'SEARCH_SUGGEST_TAIL',
    11: 'SEARCH_SUGGEST_PERSONALIZED', 12: 'SEARCH_SUGGEST_PROFILE', 13: 'SEARCH_OTHER_ENGINE',
    14: 'EXTENSION_APP_DEPRECATED', 15: 'CONTACT_DEPRECATED', 16: 'BOOKMARK_TITLE',
    17: 'NAVSUGGEST_PERSONALIZED', 18: 'CALCULATOR', 19: 'CLIPBOARD_URL', 20: 'VOICE_SUGGEST',
    21: 'PHYSICAL_WEB_DEPRECATED', 22: 'PHYSICAL_WEB_OVERFLOW_DEPRECATED',
    23: 'TAB_SEARCH_DEPRECATED', 24: 'DOCUMENT_SUGGESTION', 25: 'PEDAL', 26: 'CLIPBOARD_TEXT',
    27: 'CLIPBOARD_IMAGE', 28: 'TILE_SUGGESTION', 29: 'TILE_NAVSUGGEST', 30: 'OPEN_TAB',
    31: 'HISTORY_CLUSTER', 32: 'NULL_RESULT_MESSAGE', 33: 'STARTER_PACK',
    34: 'TILE_MOST_VISITED_SITE', 35: 'TILE_REPEATABLE_QUERY', 36: 'HISTORY_EMBEDDINGS',
    37: 'FEATURED_ENTERPRISE_SEARCH', 38: 'HISTORY_EMBEDDINGS_ANSWER', 39: 'TAB_GROUP',
    40: 'CROSS_DEVICE_TAB',
}


def _named(value, names):
    """The stored integer with the enum name the cited source gives it."""
    if not isinstance(value, int):
        return value if value is not None else ''
    name = names.get(value)
    return f'{value} ({name})' if name else str(value)


def _transition(value):
    if not isinstance(value, int):
        return value if value is not None else ''
    value &= 0xFFFFFFFF  # stored as a signed 32-bit int; a qualifier can set the sign bit
    core = value & 0xFF
    text = _named(core, _TRANSITIONS)
    if value != core:
        text += f', qualifiers 0x{value & 0xFFFFFF00:08X}'
    return text


def _match_type(value, version):
    """A database with no meta table (version 0) predates the version 1 migration, which
    rewrote stored types 9 to 12 as 13 to 16; name those by the value they migrate to."""
    if version == 0 and isinstance(value, int) and 9 <= value <= 12:
        name = _MATCH_TYPES[value + 4]
        return f'{value} ({name}, pre-migration numbering)'
    return _named(value, _MATCH_TYPES)


def _shortcuts_version(db):
    """The meta table's version, or 0 when the database has no meta table."""
    try:
        row = db.execute("SELECT value FROM meta WHERE key = 'version'").fetchone()
    except sqlite3.Error:
        return 0
    try:
        return int(row[0]) if row else 0
    except (TypeError, ValueError):
        return 0


@artifact_processor
def chromiumTopSites(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Top Sites'}, 'Chromium Top Sites'):
        db = open_store(store, 'Chromium Top Sites')
        if db is None:
            continue
        try:
            if table_columns(db, 'top_sites'):
                rows = db.execute('SELECT NULL, url_rank, url, title, NULL, NULL '
                                  'FROM top_sites ORDER BY url_rank, url').fetchall()
            elif table_columns(db, 'thumbnails'):
                rows = db.execute('SELECT last_updated, url_rank, url, title, thumbnail, '
                                  'last_forced FROM thumbnails '
                                  'ORDER BY url_rank, url').fetchall()
            else:
                rows = []
        except sqlite3.Error as ex:
            logfunc(f'Chromium Top Sites: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for last_updated, rank, url, title, thumbnail, last_forced in rows:
            media = check_in_embedded_media(store.path, thumbnail) if thumbnail else ''
            data_list.append((webkit_time(last_updated), rank, url, title, media or '',
                              webkit_time(last_forced)) + row_tail(store))
    data_headers = (('Last Updated', 'datetime'), 'Rank', 'URL', 'Title',
                    ('Thumbnail', 'media'), ('Last Forced', 'datetime'), 'Browser', 'Profile',
                    'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumShortcuts(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Shortcuts'}, 'Chromium Omnibox Shortcuts'):
        db = open_store(store, 'Chromium Omnibox Shortcuts')
        if db is None:
            continue
        try:
            present = table_columns(db, 'omni_box_shortcuts')
            if not present:
                continue
            version = _shortcuts_version(db)
            columns = select_list(present, ('last_access_time', 'text', 'fill_into_edit', 'url',
                                            'contents', 'description', 'number_of_hits', 'type',
                                            'transition', 'keyword'))
            rows = db.execute(f'''
                SELECT {columns}
                FROM omni_box_shortcuts ORDER BY last_access_time, id''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Omnibox Shortcuts: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for (last_access, text, fill_into_edit, url, contents, description, hits, match_type,
             transition, keyword) in rows:
            data_list.append((webkit_time(last_access), text, fill_into_edit, url, contents,
                              description, hits, _match_type(match_type, version),
                              _transition(transition), keyword) + row_tail(store))
    data_headers = (('Last Access Time', 'datetime'), 'Input Text', 'Fill Into Edit', 'URL',
                    'Contents', 'Description', 'Hits', 'Match Type', 'Transition', 'Keyword',
                    'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
