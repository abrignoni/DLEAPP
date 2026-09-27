"""Chromium session and tab restore files for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the SNSS files a Chromium-based browser keeps in each profile: the session
file (Sessions/Session_<time>, or Current Session and Last Session in releases
before the Sessions folder) and the tab restore file (Sessions/Tabs_<time>, or
Current Tabs and Last Tabs). scripts/snss_parser.py walks the records and decodes
the navigation entry, which both files write the same way; this module applies
each file's own command ids. Sources are in the notes.
"""

__artifacts_v2__ = {
    "chromiumSessionTabs": {
        "name": "Chromium Session Tabs",
        "description": "Navigation entries the session files of Chromium-based browser profiles "
                       "record for each tab, with the tab's window, current entry, last active "
                       "value and any tab or window close the file records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads each Chromium-based browser profile's session file: Sessions/Session_<number> in "
                 "current releases, and Current Session and Last Session in the profile folder of older "
                 "ones, as in lonewolf_win10's Chrome profile; Sessions_Encrypted/Session_<number> is "
                 "matched too. Browser, Profile and User come from the path: the browser from the user "
                 "data folder, the profile from the folder inside it, and the user from the home folder "
                 "that holds it; Source File names the file each row came from. Browser, Profile and User "
                 "each held one value on every row of lonewolf_win10, which carries one Chrome profile in "
                 "one home folder, and User held one value on every row of pc_mus_001_win11, whose Chrome "
                 "and Edge profiles sit in one home folder. Only the Windows Google Chrome and Microsoft "
                 "Edge folders were exercised by a registered image, and a private sample exercised the "
                 "macOS Google Chrome and Opera folders; the other browsers' folders are matched by the "
                 "same paths and were not exercised. A session file directly inside a user data folder's "
                 "Sessions folder is read with that folder as its profile; no registered image carries "
                 "one, and that branch was exercised on a constructed tree only. The file is the SNSS "
                 "signature, a version, then records of a 16-bit size and a command id followed by the "
                 "command's data, read with scripts/snss_parser.py. The files were version 1 on "
                 "lonewolf_win10 and version 3 on pc_mus_001_win11. Chromium's storage code says version 1 "
                 "was used before commit 223e5cd on 2021-05-25 and names version 5 "
                 "kFileVersionEncryptedWithOSCrypt "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/command_storage_backend.cc#L46-L54), "
                 "the version it gives a file it encrypts, kept in a Sessions_Encrypted folder "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/command_storage_backend.cc#L691-L698 "
                 "with "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/command_storage_backend.cc#L756-L759 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_constants.cc#L12-L13); "
                 "a version 5 file is named in the run log and not read, and none was on the tested "
                 "images. Rows come from command 6 (kCommandUpdateTabNavigation) and the other columns "
                 "from commands 0, 7, 16, 17 and 21, ids defined in "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L59-L112 "
                 "and the same in the Chrome 65 source "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/session_service_commands.cc#L23-L46). "
                 "A navigation record is the tab's session id followed by the navigation entry, written by "
                 "one function for session and tab restore files alike "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/base_session_service_commands.cc#L45-L58) "
                 "in the field order of SerializedNavigationEntry::WriteToPickle "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/serialized_navigation_entry.cc#L116-L171). "
                 "URL is the entry's virtual URL "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/serialized_navigation_entry.cc#L122-L123), "
                 "which Chromium's navigation entry describes as the URL shown to the user "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/content/public/browser/navigation_entry.h#L92-L100). "
                 "Original Request URL is the entry's original request URL "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/serialized_navigation_entry.cc#L143-L146), "
                 "described as the URL that caused the entry to be created "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/content/public/browser/navigation_entry.h#L201-L203). "
                 "Navigation Time is the entry's timestamp "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/serialized_navigation_entry.cc#L148), "
                 "described as the time the last known local navigation to the entry completed, a reload "
                 "completing it again "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/content/public/browser/navigation_entry.h#L209-L220), "
                 "in microseconds since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7). "
                 "Transition and Transition Qualifiers decode the stored page transition with "
                 "page_transition_types.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/ui/base/page_transition_types.h#L30-L112 "
                 "and "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/ui/base/page_transition_types.h#L119-L155), "
                 "as in Chromium Web Visits; Referrer URL is the entry's referrer as stored. Every "
                 "navigation record in the tested images' session and tab restore files, 1,282 of them, "
                 "decoded to the same tab id, index, URL, title, time, referrer, original request URL and "
                 "transition with CCL Group's separate reader, ccl_chromium_snss2 in ccl_chromium_reader "
                 "0.3.18. The same tab and index can be written more than once in a file, as in both "
                 "tested images, and Chromium's reader keeps the last record written for a tab and index "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L692-L709); "
                 "Latest Record is Yes on that record and No on earlier ones. A record that repeats an "
                 "earlier record of the same file in every reported column is reported once: "
                 "lonewolf_win10's 90 navigation records gave 39 rows and pc_mus_001_win11's 214 gave 101, "
                 "of which 7 and 33 have Latest Record No. Commands 5, 11 and 24 remove entries from a "
                 "tab's list "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L646-L690); "
                 "Latest Record does not take them into account, and no tested file held one. Current "
                 "Entry is Yes on the latest record at the index the tab's last command 7 selects, which "
                 "Chromium's reader takes as the tab's current entry "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L711-L720), "
                 "No on the tab's other rows, and blank for a tab with no command 7 (none on the tested "
                 "images). Tab ID and Window ID are Chromium's session ids as stored, the window being the "
                 "one the tab's last command 0 placed it in "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L1097-L1101). "
                 "Tab Closed (UTC) and Window Closed (UTC) are the times in commands 16 and 17, which "
                 "Chromium takes from the clock when it records the close "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L1126-L1139); "
                 "its reader drops a closed tab with its entries and discards a closed window "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L629-L644), "
                 "so a row with a Tab Closed time holds a page Chromium would not restore from the file. "
                 "Tab Closed (UTC) and Window Closed (UTC) were blank on every row of lonewolf_win10, "
                 "while 19 rows of pc_mus_001_win11 had a Tab Closed time and 1 a Window Closed time. Tab "
                 "Last Active comes from command 21. Chrome 65 wrote base::TimeTicks' internal value there "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/session_service_commands.cc#L739-L749), "
                 "which base/time/time.h describes as an abstract time that cannot be converted to a "
                 "human-readable time "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L16-L19); "
                 "release 119.0.6045.8 still wrote it that way "
                 "(https://github.com/chromium/chromium/blob/bcd9ac54ef80a74be0c76655a2fe27e94076bdb4/components/sessions/core/session_service_commands.cc#L1056-L1063), "
                 "and from 119.0.6045.9 the value is converted to microseconds since 1601 "
                 "(https://github.com/chromium/chromium/blob/c7ec5863fa5c563b4b9057148aa2ae3f09f7994e/components/sessions/core/session_service_commands.cc#L1056-L1070), "
                 "as current releases store it "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/session_service_commands.cc#L1248-L1257). "
                 "The file does not record which release wrote it, so Tab Last Active (UTC) is filled only "
                 "when the stored value reads as a time on or after 1970-01-01, and Tab Last Active (as "
                 "stored) keeps every value. Tab Last Active (as stored) was filled on 39 of "
                 "lonewolf_win10's 39 rows and 99 of pc_mus_001_win11's 101 rows, every value below that "
                 "point (the largest 830,543,246,219), so Tab Last Active (UTC) was blank on every row of "
                 "both images, while a private sample written by Chrome 153 stored dates. On the tested "
                 "images the addresses in these rows that were not in the same profile's History urls "
                 "table were chrome:// pages, 2 on each image. Not reported: the other commands, among "
                 "them window bounds, tab order, pinned state, tab groups and user agent overrides, and "
                 "ids outside Chromium's list, such as the 132 in the files of pc_mus_001_win11's "
                 "Microsoft Edge profile.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Sessions*/Session_*',
            '*/AppData/Local/Google/Chrome/User Data/*/Current Session',
            '*/AppData/Local/Google/Chrome/User Data/*/Last Session',
            '*/Library/Application Support/Google/Chrome/*/Sessions*/Session_*',
            '*/Library/Application Support/Google/Chrome/*/Current Session',
            '*/Library/Application Support/Google/Chrome/*/Last Session',
            '*/.config/google-chrome/*/Sessions*/Session_*',
            '*/.config/google-chrome/*/Current Session',
            '*/.config/google-chrome/*/Last Session',
            '*/AppData/Local/Chromium/User Data/*/Sessions*/Session_*',
            '*/AppData/Local/Chromium/User Data/*/Current Session',
            '*/AppData/Local/Chromium/User Data/*/Last Session',
            '*/Library/Application Support/Chromium/*/Sessions*/Session_*',
            '*/Library/Application Support/Chromium/*/Current Session',
            '*/Library/Application Support/Chromium/*/Last Session',
            '*/.config/chromium/*/Sessions*/Session_*',
            '*/.config/chromium/*/Current Session',
            '*/.config/chromium/*/Last Session',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Sessions*/Session_*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Current Session',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Last Session',
            '*/Library/Application Support/Microsoft Edge/*/Sessions*/Session_*',
            '*/Library/Application Support/Microsoft Edge/*/Current Session',
            '*/Library/Application Support/Microsoft Edge/*/Last Session',
            '*/.config/microsoft-edge/*/Sessions*/Session_*',
            '*/.config/microsoft-edge/*/Current Session',
            '*/.config/microsoft-edge/*/Last Session',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sessions*/Session_*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Current Session',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Last Session',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sessions*/Session_*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Current Session',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Last Session',
            '*/.config/BraveSoftware/Brave-Browser/*/Sessions*/Session_*',
            '*/.config/BraveSoftware/Brave-Browser/*/Current Session',
            '*/.config/BraveSoftware/Brave-Browser/*/Last Session',
            '*/AppData/Local/Vivaldi/User Data/*/Sessions*/Session_*',
            '*/AppData/Local/Vivaldi/User Data/*/Current Session',
            '*/AppData/Local/Vivaldi/User Data/*/Last Session',
            '*/Library/Application Support/Vivaldi/*/Sessions*/Session_*',
            '*/Library/Application Support/Vivaldi/*/Current Session',
            '*/Library/Application Support/Vivaldi/*/Last Session',
            '*/.config/vivaldi/*/Sessions*/Session_*',
            '*/.config/vivaldi/*/Current Session',
            '*/.config/vivaldi/*/Last Session',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Sessions*/Session_*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Current Session',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Last Session',
            '*/Library/Application Support/com.operasoftware.Opera/*/Sessions*/Session_*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Current Session',
            '*/Library/Application Support/com.operasoftware.Opera/*/Last Session',
            '*/.config/opera/*/Sessions*/Session_*',
            '*/.config/opera/*/Current Session',
            '*/.config/opera/*/Last Session',
            '*/AppData/Roaming/Opera Software/Opera Stable/Sessions*/Session_*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Current Session',
            '*/AppData/Roaming/Opera Software/Opera Stable/Last Session',
            '*/Library/Application Support/com.operasoftware.Opera/Sessions*/Session_*',
            '*/Library/Application Support/com.operasoftware.Opera/Current Session',
            '*/Library/Application Support/com.operasoftware.Opera/Last Session',
            '*/.config/opera/Sessions*/Session_*',
            '*/.config/opera/Current Session',
            '*/.config/opera/Last Session',
        ),
        "output_types": "standard",
        "artifact_icon": "layers",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 39 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 101 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumClosedTabs": {
        "name": "Chromium Closed Tabs",
        "description": "Navigation entries of the closed tabs and windows kept in the tab restore "
                       "files of Chromium-based browser profiles, with each tab's stored close "
                       "time and current entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads each Chromium-based browser profile's tab restore file: Sessions/Tabs_<number> in "
                 "current releases, and Current Tabs and Last Tabs in the profile folder of older ones, as "
                 "in lonewolf_win10's Chrome profile; Sessions_Encrypted/Tabs_<number> is matched too. "
                 "Browser, Profile and User come from the path: the browser from the user data folder, the "
                 "profile from the folder inside it, and the user from the home folder that holds it; "
                 "Source File names the file each row came from. Browser, Profile and User each held one "
                 "value on every row of lonewolf_win10, which carries one Chrome profile in one home "
                 "folder, and User held one value on every row of pc_mus_001_win11, whose Chrome and Edge "
                 "profiles sit in one home folder. The folders exercised are as in Chromium Session Tabs. "
                 "The file's framing and versions are as in Chromium Session Tabs: version 1 on "
                 "lonewolf_win10, version 3 on pc_mus_001_win11, and a version 5 file named in the run log "
                 "and not read (none on the tested images). Chromium's source describes the order: when "
                 "the user closes a tab, a command 4 record identifies the tab and its selected entry and "
                 "is followed, after any pinned state, app id or user agent records, by one command 1 "
                 "record per navigation entry "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L102-L132); "
                 "the ids are the same in the Chrome 65 source "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/persistent_tab_restore_service.cc#L97-L105). "
                 "A row is one command 1 record, attached to the tab record before it as Chromium's reader "
                 "attaches it "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1369-L1443); "
                 "a navigation record before any tab record is counted in the run log and not reported, "
                 "and none was on the tested images. Closed Time (UTC) is the time in the tab record, "
                 "which Chromium takes from the clock when it builds the closed entry from the live tab "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_helper.cc#L1467-L1483 "
                 "and in Chrome 65 "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/tab_restore_service_helper.cc#L428) "
                 "and sets to zero for the entries it builds from the previous session's windows "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1649-L1661 "
                 "with "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1727 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1739 "
                 "as in Chrome 65 "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/persistent_tab_restore_service.cc#L1022 "
                 "and "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/sessions/core/persistent_tab_restore_service.cc#L1031). "
                 "A zero is left blank: Closed Time (UTC) was blank on 467 of pc_mus_001_win11's 711 rows "
                 "and none of lonewolf_win10's 267. Current Entry is Yes on the entry at the position the "
                 "tab record selects, counted from zero among the navigation records that follow it, "
                 "because Chromium's reader renumbers each tab's entries by position and takes the tab "
                 "record's index as the current one "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1423 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1439-L1442); "
                 "every tab record on the tested images selected a position its entries covered, 64 on "
                 "lonewolf_win10 and 173 on pc_mus_001_win11. Navigation Index is the index the record "
                 "stores, the entry's place in the tab's list when it was written, which Chromium replaces "
                 "with that position when it reads the file. Window ID is the id in the closed window "
                 "record (command 9, or 3 in older files) whose tab count covers the tab "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1293-L1318), "
                 "blank for a tab closed on its own or as part of a group (command 13) or split (command "
                 "15); pc_mus_001_win11 held 42 window records and 517 of its rows have a Window ID, "
                 "lonewolf_win10 none. Restored-Entry Record is Yes when a later command 2 in the same "
                 "file carries the tab's id or its window's id. Chromium writes that command when the user "
                 "restores an entry "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L846-L858) "
                 "and for every entry when the list is cleared "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L816-L831), "
                 "and its reader drops the entry it names "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/components/sessions/core/tab_restore_service_impl.cc#L1273-L1290). "
                 "Restored-Entry Record was Yes on 1 row of lonewolf_win10 and No on every row of "
                 "pc_mus_001_win11. URL, Title, Navigation Time, Transition, Transition Qualifiers, "
                 "Referrer URL and Original Request URL are read from the navigation record as in Chromium "
                 "Session Tabs, whose notes give the sources and the cross-check with CCL Group's reader, "
                 "which covered these files too. A profile can hold an older and a newer tab restore file: "
                 "on pc_mus_001_win11, 317 of the 344 rows from the three older files had a row with the "
                 "same Closed Time, Navigation Time, URL and Title in the newer file of the same profile, "
                 "so one closed tab can appear twice with different Source File values. On the tested "
                 "images the addresses in these rows that were not in the same profile's History urls "
                 "table were chrome:// and edge:// pages, and one https address on pc_mus_001_win11. Not "
                 "reported: pinned state, tab group and split data, extension app ids, user agent "
                 "overrides and extra data.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Sessions*/Tabs_*',
            '*/AppData/Local/Google/Chrome/User Data/*/Current Tabs',
            '*/AppData/Local/Google/Chrome/User Data/*/Last Tabs',
            '*/Library/Application Support/Google/Chrome/*/Sessions*/Tabs_*',
            '*/Library/Application Support/Google/Chrome/*/Current Tabs',
            '*/Library/Application Support/Google/Chrome/*/Last Tabs',
            '*/.config/google-chrome/*/Sessions*/Tabs_*',
            '*/.config/google-chrome/*/Current Tabs',
            '*/.config/google-chrome/*/Last Tabs',
            '*/AppData/Local/Chromium/User Data/*/Sessions*/Tabs_*',
            '*/AppData/Local/Chromium/User Data/*/Current Tabs',
            '*/AppData/Local/Chromium/User Data/*/Last Tabs',
            '*/Library/Application Support/Chromium/*/Sessions*/Tabs_*',
            '*/Library/Application Support/Chromium/*/Current Tabs',
            '*/Library/Application Support/Chromium/*/Last Tabs',
            '*/.config/chromium/*/Sessions*/Tabs_*',
            '*/.config/chromium/*/Current Tabs',
            '*/.config/chromium/*/Last Tabs',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Sessions*/Tabs_*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Current Tabs',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Last Tabs',
            '*/Library/Application Support/Microsoft Edge/*/Sessions*/Tabs_*',
            '*/Library/Application Support/Microsoft Edge/*/Current Tabs',
            '*/Library/Application Support/Microsoft Edge/*/Last Tabs',
            '*/.config/microsoft-edge/*/Sessions*/Tabs_*',
            '*/.config/microsoft-edge/*/Current Tabs',
            '*/.config/microsoft-edge/*/Last Tabs',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sessions*/Tabs_*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Current Tabs',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Last Tabs',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sessions*/Tabs_*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Current Tabs',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Last Tabs',
            '*/.config/BraveSoftware/Brave-Browser/*/Sessions*/Tabs_*',
            '*/.config/BraveSoftware/Brave-Browser/*/Current Tabs',
            '*/.config/BraveSoftware/Brave-Browser/*/Last Tabs',
            '*/AppData/Local/Vivaldi/User Data/*/Sessions*/Tabs_*',
            '*/AppData/Local/Vivaldi/User Data/*/Current Tabs',
            '*/AppData/Local/Vivaldi/User Data/*/Last Tabs',
            '*/Library/Application Support/Vivaldi/*/Sessions*/Tabs_*',
            '*/Library/Application Support/Vivaldi/*/Current Tabs',
            '*/Library/Application Support/Vivaldi/*/Last Tabs',
            '*/.config/vivaldi/*/Sessions*/Tabs_*',
            '*/.config/vivaldi/*/Current Tabs',
            '*/.config/vivaldi/*/Last Tabs',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Sessions*/Tabs_*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Current Tabs',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Last Tabs',
            '*/Library/Application Support/com.operasoftware.Opera/*/Sessions*/Tabs_*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Current Tabs',
            '*/Library/Application Support/com.operasoftware.Opera/*/Last Tabs',
            '*/.config/opera/*/Sessions*/Tabs_*',
            '*/.config/opera/*/Current Tabs',
            '*/.config/opera/*/Last Tabs',
            '*/AppData/Roaming/Opera Software/Opera Stable/Sessions*/Tabs_*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Current Tabs',
            '*/AppData/Roaming/Opera Software/Opera Stable/Last Tabs',
            '*/Library/Application Support/com.operasoftware.Opera/Sessions*/Tabs_*',
            '*/Library/Application Support/com.operasoftware.Opera/Current Tabs',
            '*/Library/Application Support/com.operasoftware.Opera/Last Tabs',
            '*/.config/opera/Sessions*/Tabs_*',
            '*/.config/opera/Current Tabs',
            '*/.config/opera/Last Tabs',
        ),
        "output_types": "standard",
        "artifact_icon": "rotate-ccw",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 267 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 711 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
import struct

from scripts.chromium.browser_profiles import (locate, page_transition, profile_stores,
                                               row_tail, webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative
from scripts.snss_parser import SNSSError, decode_navigation_entry, read_commands

# Session file commands: components/sessions/core/session_service_commands.cc (see notes).
_SET_TAB_WINDOW = 0
_UPDATE_TAB_NAVIGATION = 6
_SET_SELECTED_NAVIGATION_INDEX = 7
_TAB_CLOSED = 16
_WINDOW_CLOSED = 17
_LAST_ACTIVE_TIME = 21

# Tab restore file commands: components/sessions/core/tab_restore_service_impl.cc.
_TR_UPDATE_TAB_NAVIGATION = 1
_TR_RESTORED_ENTRY = 2
_TR_WINDOW_DEPRECATED = 3
_TR_SELECTED_NAVIGATION_IN_TAB = 4
_TR_WINDOW = 9
_TR_CREATE_GROUP = 13
_TR_CREATE_SPLIT = 15

# components/sessions/core/command_storage_backend.cc: version 5 is encrypted with the
# browser's own key.
_ENCRYPTED_VERSION = 5

# 1970-01-01 as microseconds since 1601-01-01. A last active value below it is not a date:
# releases up to 119.0.6045.8 stored a base::TimeTicks reading there (see notes).
_UNIX_EPOCH_IN_WINDOWS_MICROSECONDS = 11644473600 * 1_000_000

_SESSION_NAME = re.compile(r'^(?:Sessions(?:_Encrypted)?/Session_\d+|Current Session|Last Session)$')
_TABS_NAME = re.compile(r'^(?:Sessions(?:_Encrypted)?/Tabs_\d+|Current Tabs|Last Tabs)$')

def _stores(context, pattern, label):
    """The session files the name pattern selects, one Store each (see profile_stores)."""
    names = set()
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        located = locate(canonical_relative(context.get_relative_path(path)))
        if located and pattern.match(located[4]):
            names.add(located[4])
    return profile_stores(context, names, label) if names else []


def _commands(store, label):
    """The file's (command id, payload) records, or None when it cannot be read."""
    try:
        with open(store.path, 'rb') as handle:
            header = handle.read(8)
    except OSError as exc:
        logfunc(f'{label}: could not read {store.relative}: {type(exc).__name__}')
        return None
    if len(header) == 8 and header[:4] == b'SNSS' and \
            struct.unpack_from('<i', header, 4)[0] == _ENCRYPTED_VERSION:
        logfunc(f'{label}: {store.relative} is SNSS version 5, which the browser encrypts; '
                f'not read')
        return None
    try:
        return list(read_commands(store.path))
    except (SNSSError, OSError) as exc:
        logfunc(f'{label}: could not read {store.relative}: {exc}')
        return None


def _entry_columns(entry):
    core, qualifiers = page_transition(entry['transition_type'])
    return (entry['url'], entry['title'], core, qualifiers, entry['referrer_url'],
            entry['original_request_url'])


def _decode(payload):
    try:
        return decode_navigation_entry(payload)
    except (SNSSError, struct.error, UnicodeDecodeError):
        return None


def session_rows(commands):
    """Rows for one session file, and the count of navigation records not decoded."""
    entries = []
    tab_window, selected, last_active, tab_closed, window_closed = {}, {}, {}, {}, {}
    undecoded = 0
    for order, (command, payload) in enumerate(commands):
        if command == _UPDATE_TAB_NAVIGATION:
            entry = _decode(payload)
            if entry is None:
                undecoded += 1
            else:
                entries.append((order, entry))
        elif command == _SET_TAB_WINDOW and len(payload) == 8:
            window_id, tab_id = struct.unpack('<ii', payload)
            tab_window[tab_id] = window_id
        elif command == _SET_SELECTED_NAVIGATION_INDEX and len(payload) == 8:
            tab_id, index = struct.unpack('<ii', payload)
            selected[tab_id] = index
        elif command == _LAST_ACTIVE_TIME and len(payload) == 16:
            tab_id, when = struct.unpack('<i4xq', payload)
            last_active[tab_id] = when
        elif command in (_TAB_CLOSED, _WINDOW_CLOSED) and len(payload) == 16:
            item_id, when = struct.unpack('<i4xq', payload)
            (tab_closed if command == _TAB_CLOSED else window_closed)[item_id] = when
    # A record identical to an earlier one in every reported value is reported once.
    rows, last_seen, latest = {}, {}, {}
    for order, entry in entries:
        slot = (entry['tab_id'], entry['index'])
        key = slot + (entry['timestamp'],) + _entry_columns(entry)
        if key not in rows:
            rows[key] = entry
        last_seen[key] = order
        latest[slot] = order
    out = []
    for key, entry in rows.items():
        tab_id, index = key[0], key[1]
        is_latest = last_seen[key] == latest[(tab_id, index)]
        if tab_id not in selected:
            current = ''
        else:
            current = 'Yes' if is_latest and selected[tab_id] == index else 'No'
        window_id = tab_window.get(tab_id, '')
        active = last_active.get(tab_id, '')
        active_utc = (webkit_time(active)
                      if active != '' and active >= _UNIX_EPOCH_IN_WINDOWS_MICROSECONDS else '')
        out.append((webkit_time(entry['timestamp']), active_utc,
                    webkit_time(tab_closed.get(tab_id)),
                    webkit_time(window_closed.get(window_id)) if window_id != '' else '')
                   + _entry_columns(entry)
                   + (tab_id, index, current, 'Yes' if is_latest else 'No', window_id, active))
    return out, undecoded


def _window(command, payload):
    """(window id, number of tabs) of a closed window record, or None."""
    if command == _TR_WINDOW and len(payload) >= 24:
        window_id, _selected, num_tabs = struct.unpack_from('<iii', payload, 4)
        return window_id, num_tabs
    if command == _TR_WINDOW_DEPRECATED and len(payload) in (12, 24):
        window_id, _selected, num_tabs = struct.unpack_from('<iii', payload, 0)
        return window_id, num_tabs
    return None


def closed_tab_rows(commands):
    """Rows for one tab restore file, and the count of navigation records not reported."""
    entries = []
    # The tab record the next navigation records belong to, empty when none. As in Chromium's
    # reader, only a restored-entry record ends it; a window, group or split record does not.
    tab = {}
    window = None
    restored = {}
    unreported = 0
    for order, (command, payload) in enumerate(commands):
        if command == _TR_SELECTED_NAVIGATION_IN_TAB and len(payload) in (8, 16):
            tab_id, selected = struct.unpack_from('<ii', payload)
            closed = struct.unpack_from('<q', payload, 8)[0] if len(payload) == 16 else 0
            window_id = window_order = ''
            if window:
                window_id, window_order = window[0], window[2]
                window[1] -= 1
                if window[1] <= 0:
                    window = None
            tab = {'id': tab_id, 'selected': selected, 'closed': closed, 'order': order,
                   'window': window_id, 'window_order': window_order, 'count': 0}
        elif command == _TR_UPDATE_TAB_NAVIGATION:
            entry = _decode(payload)
            if not tab or entry is None:
                unreported += 1
                continue
            entries.append((tab, tab['count'], entry))
            tab['count'] += 1
        elif command in (_TR_WINDOW, _TR_WINDOW_DEPRECATED):
            parsed = _window(command, payload)
            window = [parsed[0], parsed[1], order] if parsed and parsed[1] > 0 else None
        elif command in (_TR_CREATE_GROUP, _TR_CREATE_SPLIT):
            window = None
        elif command == _TR_RESTORED_ENTRY:
            if len(payload) == 4:
                restored.setdefault(struct.unpack('<i', payload)[0], []).append(order)
            window, tab = None, {}
    out = []
    for tab, position, entry in entries:
        later = any(o > tab['order'] for o in restored.get(tab['id'], ())) or (
            tab['window'] != '' and
            any(o > tab['window_order'] for o in restored.get(tab['window'], ())))
        out.append((webkit_time(entry['timestamp']), webkit_time(tab['closed']))
                   + _entry_columns(entry)
                   + (tab['id'], entry['index'], 'Yes' if position == tab['selected'] else 'No',
                      tab['window'], 'Yes' if later else 'No'))
    return out, unreported


@artifact_processor
def chromiumSessionTabs(context):
    label = 'Chromium Session Tabs'
    data_list, sources = [], []
    for store in _stores(context, _SESSION_NAME, label):
        commands = _commands(store, label)
        if commands is None:
            continue
        rows, undecoded = session_rows(commands)
        if undecoded:
            logfunc(f'{label}: {undecoded} navigation record(s) in {store.relative} '
                    f'could not be decoded')
        sources.append(store.path)
        data_list.extend(row + row_tail(store) for row in rows)
    data_headers = (('Navigation Time (UTC)', 'datetime'), ('Tab Last Active (UTC)', 'datetime'),
                    ('Tab Closed (UTC)', 'datetime'), ('Window Closed (UTC)', 'datetime'),
                    'URL', 'Title', 'Transition', 'Transition Qualifiers', 'Referrer URL',
                    'Original Request URL', 'Tab ID', 'Navigation Index', 'Current Entry',
                    'Latest Record', 'Window ID', 'Tab Last Active (as stored)', 'Browser',
                    'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumClosedTabs(context):
    label = 'Chromium Closed Tabs'
    data_list, sources = [], []
    for store in _stores(context, _TABS_NAME, label):
        commands = _commands(store, label)
        if commands is None:
            continue
        rows, unreported = closed_tab_rows(commands)
        if unreported:
            logfunc(f'{label}: {unreported} navigation record(s) in {store.relative} '
                    f'were not reported (not decoded, or not after a tab record)')
        sources.append(store.path)
        data_list.extend(row + row_tail(store) for row in rows)
    data_headers = (('Navigation Time (UTC)', 'datetime'), ('Closed Time (UTC)', 'datetime'),
                    'URL', 'Title', 'Transition', 'Transition Qualifiers', 'Referrer URL',
                    'Original Request URL', 'Tab ID', 'Navigation Index', 'Current Entry',
                    'Window ID', 'Restored-Entry Record', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
