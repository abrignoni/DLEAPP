"""Chromium sync data for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Sync Data/LevelDB store of Chromium-based browser profiles with
scripts/chromium/sync_data.py: the devices the sync account lists, the session
headers and tabs synced for each device, and send-tab-to-self entries. Sources
are in the notes.
"""

__artifacts_v2__ = {
    "chromiumSyncDevices": {
        "name": "Chromium Sync Devices",
        "description": "Devices listed in the sync device information of Chromium-based browser profiles, with the name, operating system, model, browser version and last update time each device recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Sync Data/LevelDB folder of each Chromium-based browser profile, in the user data folders the other Chromium artifacts read (Google Chrome, Chromium including its snap and Flatpak, Microsoft Edge, Brave, Vivaldi, Opera and webOS webbrowser), including a folder directly in Opera's user data folder, with the vendored ccl_leveldb, through scripts/chromium/sync_data.py. Browser, Profile and User come from the path as in the other Chromium artifacts, and Source File names the folder a row came from. Chromium keeps each sync data type's records under the keys <type>-dt-<storage key>, with A- in front for account storage, and the type's sync state under <type>-GlobalMetadata (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L26-L63 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L172-L183 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L306-L311). Six of the 13 Sync Data folders read on the tested images held earlier versions of keys as well as the newest one; the other seven held one version of each key. LevelDB numbers each write and orders the versions of a key by decreasing sequence number, the newest first (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Only the newest version of each key is read, and a key whose newest version is a deletion is not reported; the earlier versions are not reported by any artifact, and the run log counts them for each folder. On the tested images that left 149 of hexordia_mvs2025_win11's 5,666 records, 172 of pc_mus_001_win11's 1,732 across five profile folders, 6 of lonewolf_win10's 255 and 77 of mvs2026_macbookpro_macos15's 6,291 as the newest version of a key, before deletions. Values are decoded with the field numbers and types of the messages Chromium publishes under components/sync/protocol at commit 5926523bcfedb77ba2533ace1dd93b477673f72a, transcribed into scripts/chromium/sync_data.py, not by guessing at field types; a record that does not decode is not reported, and the run log names its store and data type; none failed to decode on the tested images. On a Mac logical extraction a folder under System/Volumes/Data that holds the same files with the same bytes as the folder at the same path outside it is read once, as on mvs2026_macbookpro_macos15. Not read: Sync Data folders in the embedded browser profiles other apps keep, such as WebView2 EBWebView folders, ChromeOS profiles, the -md- metadata records, and the data types other than device_info, sessions and send_tab_to_self. Of those, the tested stores held preferences, priority_preferences, search_engines, web_apps, apps, extensions, themes and Edge's own edge_hub_app_usage data records; history_delete_directives, reading_list and the others held only their sync state. Stores with no device_info, sessions or send_tab_to_self data record: ou_ransomware_server2022's three Edge folders and pc_mus_001_win11's Guest Profile and System Profile, which held no data record at all, and ubuntu2604_arm64_chromium's two Chromium folders, which held one web_apps record each. The patterns matched no Sync Data folder in af_case2_win10, szechuan_win10, dleapp_macos_bigsur or evidencelocker_macos14. One row per live device_info record, a DeviceInfoSpecifics message (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L24-L110). Last Updated is last_updated_timestamp, which the proto describes as updated to the current time periodically and whenever another field changes (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L53-L57); the client sets it from its own clock (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync_device_info/device_info_sync_bridge.cc#L322-L325) in milliseconds since 1970-01-01 UTC (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/base/time.cc#L14-L20). Device Name is client_name, a non-unique human readable name (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L28-L29), and Cache GUID is cache_guid, which identifies a sync client (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L25-L26). This Device is Yes when the row's cache GUID equals the cache_guid in the type's sync state record, the GUID of the sync client that wrote the store (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/data_type_state.proto#L58-L64), No when it differs, and blank when the store records none. OS Type, Form Factor and Device Type are os_type and device_form_factor (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L96-L100) and the deprecated device_type (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L31-L34), named with sync_enums.proto (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/sync_enums.proto#L143-L177). Chrome Version is chrome_version_info.version_number (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L91-L92, https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L263-L266), or the deprecated chrome_version when that is absent (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L40-L42); both were present and equal on 6 of the 8 tested rows and only chrome_version on lonewolf_win10's 2. Manufacturer, Model, Sync User Agent and Signin Scoped Device ID are manufacturer, model, sync_user_agent and signin_scoped_device_id, decoded as UTF-8 (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L67-L71, https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L36-L38, https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/device_info_specifics.proto#L49-L51). A row records that a device was listed in the profile's sync data; it does not establish who used the device. Measured: pc_mus_001_win11 4 rows, one with This Device Yes in each of its Chrome Default, Chrome Profile 2 and Edge Default profiles and one No in Profile 2; hexordia_mvs2025_win11 and mvs2026_macbookpro_macos15 1 row each, This Device Yes; lonewolf_win10 2 rows. On lonewolf_win10 This Device, Manufacturer, Model, OS Type, Form Factor and Signin Scoped Device ID were blank on both rows, the store's sync state holding no cache_guid; on pc_mus_001_win11 OS Type and Form Factor were blank on all 4 rows and User held one value.",
        "paths": (
        '*/AppData/Local/Google/Chrome/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Google/Chrome/*/Sync Data/LevelDB/*',
        '*/.config/google-chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Chromium/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Chromium/*/Sync Data/LevelDB/*',
        '*/.config/chromium/*/Sync Data/LevelDB/*',
        '*/snap/chromium/common/chromium/*/Sync Data/LevelDB/*',
        '*/.var/app/org.chromium.Chromium/config/chromium/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Microsoft/Edge/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Microsoft Edge/*/Sync Data/LevelDB/*',
        '*/.config/microsoft-edge/*/Sync Data/LevelDB/*',
        '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/.config/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Vivaldi/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Vivaldi/*/Sync Data/LevelDB/*',
        '*/.config/vivaldi/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/*/Sync Data/LevelDB/*',
        '*/.config/opera/*/Sync Data/LevelDB/*',
        '*/webbrowser/chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/Sync Data/LevelDB/*',
        '*/.config/opera/Sync Data/LevelDB/*',
        ),
        "output_types": "standard",
        "artifact_icon": "smartphone",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Sync Data folder matched)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no Sync Data folder matched)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no Sync Data folder matched)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no matching data record in the Sync Data folders)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Sync Data folder matched)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no matching data record in the Sync Data folders)",
        },
    },
    "chromiumSyncedTabs": {
        "name": "Chromium Synced Tabs",
        "description": "Pages in the tabs Chromium-based browser profiles synced, from this profile and from other sync clients on the account, with the address, title, navigation time and the name of the device the tab belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Sync Data/LevelDB folder of each Chromium-based browser profile, in the user data folders the other Chromium artifacts read (Google Chrome, Chromium including its snap and Flatpak, Microsoft Edge, Brave, Vivaldi, Opera and webOS webbrowser), including a folder directly in Opera's user data folder, with the vendored ccl_leveldb, through scripts/chromium/sync_data.py. Browser, Profile and User come from the path as in the other Chromium artifacts, and Source File names the folder a row came from. Chromium keeps each sync data type's records under the keys <type>-dt-<storage key>, with A- in front for account storage, and the type's sync state under <type>-GlobalMetadata (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L26-L63 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L172-L183 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L306-L311). Six of the 13 Sync Data folders read on the tested images held earlier versions of keys as well as the newest one; the other seven held one version of each key. LevelDB numbers each write and orders the versions of a key by decreasing sequence number, the newest first (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Only the newest version of each key is read, and a key whose newest version is a deletion is not reported; the earlier versions are not reported by any artifact, and the run log counts them for each folder. On the tested images that left 149 of hexordia_mvs2025_win11's 5,666 records, 172 of pc_mus_001_win11's 1,732 across five profile folders, 6 of lonewolf_win10's 255 and 77 of mvs2026_macbookpro_macos15's 6,291 as the newest version of a key, before deletions. Values are decoded with the field numbers and types of the messages Chromium publishes under components/sync/protocol at commit 5926523bcfedb77ba2533ace1dd93b477673f72a, transcribed into scripts/chromium/sync_data.py, not by guessing at field types; a record that does not decode is not reported, and the run log names its store and data type; none failed to decode on the tested images. On a Mac logical extraction a folder under System/Volumes/Data that holds the same files with the same bytes as the folder at the same path outside it is read once, as on mvs2026_macbookpro_macos15. Not read: Sync Data folders in the embedded browser profiles other apps keep, such as WebView2 EBWebView folders, ChromeOS profiles, the -md- metadata records, and the data types other than device_info, sessions and send_tab_to_self. Of those, the tested stores held preferences, priority_preferences, search_engines, web_apps, apps, extensions, themes and Edge's own edge_hub_app_usage data records; history_delete_directives, reading_list and the others held only their sync state. Stores with no device_info, sessions or send_tab_to_self data record: ou_ransomware_server2022's three Edge folders and pc_mus_001_win11's Guest Profile and System Profile, which held no data record at all, and ubuntu2604_arm64_chromium's two Chromium folders, which held one web_apps record each. The patterns matched no Sync Data folder in af_case2_win10, szechuan_win10, dleapp_macos_bigsur or evidencelocker_macos14. One row per navigation entry in each live sessions record that holds a SessionTab (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L69-L91), whose entries are TabNavigation messages (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/tab_navigation.proto#L19-L51). URL is virtual_url, the URL as displayed to the user (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/tab_navigation.proto#L20-L24); Title, Referrer and HTTP Status are title, referrer and http_status_code as stored; Transition is page_transition, the core transition type, named with sync_enums.proto (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/sync_enums.proto#L63-L74); From Address Bar is navigation_from_address_bar (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/tab_navigation.proto#L40-L41). Navigation Time is timestamp_msec, described as when the navigation last occurred, in client time, and as able to refresh when the user goes back or forward (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/tab_navigation.proto#L35-L37), written with TimeToProtoTime (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync_sessions/synced_session.cc#L136), milliseconds since 1970-01-01 UTC. Of the 67 tested rows with This Device Yes, 46 were within 1 second of a visit to the same address in the same profile's History (Chromium Web Visits), 7 within 60 seconds and 3 further; the other 11 rows, three distinct addresses, had no visit to the same address in that History. Navigation Index is the entry's position in the tab and Current Entry is Yes on the entry at current_navigation_index (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L77-L79). Tab Last Active is last_active_time_unix_epoch_millis (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L89-L91); Pinned is pinned shown as Yes or No, blank when not stored; Tab ID and Window ID are tab_id and window_id as stored. Device Name is the client_name of the session header with the same session tag, or of the device with that Cache GUID when no header is stored; on the tested stores every tab's tag had a header and every tab id was listed in that header's windows. Session Tag is the record's session_tag. This Device is Yes when the session tag equals the cache_guid in the type's sync state record, the GUID of the sync client that wrote the store (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/data_type_state.proto#L58-L64), No when it differs, and blank when the store records none. A row whose This Device is No came from another sync client on the account, another device or another browser profile signed in to the same account; it is not a page opened in this profile. On pc_mus_001_win11 the No rows belong to a client whose header Device Type is TYPE_PHONE (6). Measured: pc_mus_001_win11 31 rows in Chrome Profile 2, 18 of them This Device No; hexordia_mvs2025_win11 22 rows and mvs2026_macbookpro_macos15 32, all This Device Yes. Pinned held No on every row of the three images. On hexordia_mvs2025_win11 and mvs2026_macbookpro_macos15, whose rows all came from the profile's own session, Device Name, This Device, Window ID and Session Tag each held one value, as did Browser, Profile and User on all three images; HTTP Status held 200 on every row of hexordia_mvs2025_win11; Tab Last Active was blank on every row of pc_mus_001_win11 and filled on every row of the other two.",
        "paths": (
        '*/AppData/Local/Google/Chrome/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Google/Chrome/*/Sync Data/LevelDB/*',
        '*/.config/google-chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Chromium/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Chromium/*/Sync Data/LevelDB/*',
        '*/.config/chromium/*/Sync Data/LevelDB/*',
        '*/snap/chromium/common/chromium/*/Sync Data/LevelDB/*',
        '*/.var/app/org.chromium.Chromium/config/chromium/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Microsoft/Edge/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Microsoft Edge/*/Sync Data/LevelDB/*',
        '*/.config/microsoft-edge/*/Sync Data/LevelDB/*',
        '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/.config/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Vivaldi/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Vivaldi/*/Sync Data/LevelDB/*',
        '*/.config/vivaldi/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/*/Sync Data/LevelDB/*',
        '*/.config/opera/*/Sync Data/LevelDB/*',
        '*/webbrowser/chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/Sync Data/LevelDB/*',
        '*/.config/opera/Sync Data/LevelDB/*',
        ),
        "output_types": "standard",
        "artifact_icon": "layers",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Sync Data folder matched)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no Sync Data folder matched)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no Sync Data folder matched)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 22 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no matching data record in the Sync Data folders)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 32 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no matching data record in the Sync Data folders)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 31 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Sync Data folder matched)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no matching data record in the Sync Data folders)",
        },
    },
    "chromiumSyncedSessions": {
        "name": "Chromium Synced Sessions",
        "description": "The session header each device synced to Chromium-based browser profiles: the device name and form factor and how many windows and tabs it listed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Sync Data/LevelDB folder of each Chromium-based browser profile, in the user data folders the other Chromium artifacts read (Google Chrome, Chromium including its snap and Flatpak, Microsoft Edge, Brave, Vivaldi, Opera and webOS webbrowser), including a folder directly in Opera's user data folder, with the vendored ccl_leveldb, through scripts/chromium/sync_data.py. Browser, Profile and User come from the path as in the other Chromium artifacts, and Source File names the folder a row came from. Chromium keeps each sync data type's records under the keys <type>-dt-<storage key>, with A- in front for account storage, and the type's sync state under <type>-GlobalMetadata (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L26-L63 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L172-L183 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L306-L311). Six of the 13 Sync Data folders read on the tested images held earlier versions of keys as well as the newest one; the other seven held one version of each key. LevelDB numbers each write and orders the versions of a key by decreasing sequence number, the newest first (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Only the newest version of each key is read, and a key whose newest version is a deletion is not reported; the earlier versions are not reported by any artifact, and the run log counts them for each folder. On the tested images that left 149 of hexordia_mvs2025_win11's 5,666 records, 172 of pc_mus_001_win11's 1,732 across five profile folders, 6 of lonewolf_win10's 255 and 77 of mvs2026_macbookpro_macos15's 6,291 as the newest version of a key, before deletions. Values are decoded with the field numbers and types of the messages Chromium publishes under components/sync/protocol at commit 5926523bcfedb77ba2533ace1dd93b477673f72a, transcribed into scripts/chromium/sync_data.py, not by guessing at field types; a record that does not decode is not reported, and the run log names its store and data type; none failed to decode on the tested images. On a Mac logical extraction a folder under System/Volumes/Data that holds the same files with the same bytes as the folder at the same path outside it is read once, as on mvs2026_macbookpro_macos15. Not read: Sync Data folders in the embedded browser profiles other apps keep, such as WebView2 EBWebView folders, ChromeOS profiles, the -md- metadata records, and the data types other than device_info, sessions and send_tab_to_self. Of those, the tested stores held preferences, priority_preferences, search_engines, web_apps, apps, extensions, themes and Edge's own edge_hub_app_usage data records; history_delete_directives, reading_list and the others held only their sync state. Stores with no device_info, sessions or send_tab_to_self data record: ou_ransomware_server2022's three Edge folders and pc_mus_001_win11's Guest Profile and System Profile, which held no data record at all, and ubuntu2604_arm64_chromium's two Chromium folders, which held one web_apps record each. The patterns matched no Sync Data folder in af_case2_win10, szechuan_win10, dleapp_macos_bigsur or evidencelocker_macos14. One row per live sessions record that holds a SessionHeader (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L21-L36 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L40-L56). Device Name is the header's client_name, Form Factor its device_form_factor and Device Type its deprecated device_type, named with sync_enums.proto (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/sync_enums.proto#L143-L177). Windows is the number of SessionWindow entries, Tabs Listed the number of tab ids they list, and Window Types the browser_type names of the windows (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L58-L66, https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/sync_enums.proto#L180-L186). Session Start is session_start_time_unix_epoch_millis, which the proto says was introduced in M130 and is not populated for sessions started before it (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L41-L44). Session Tag is session_tag, sync's cache GUID since M89 (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/session_specifics.proto#L21-L24); on the tested stores every header's tag matched the Cache GUID of a device in the Chromium Sync Devices artifact. This Device is Yes when the session tag equals the cache_guid in the type's sync state record, the GUID of the sync client that wrote the store (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/data_type_state.proto#L58-L64), No when it differs, and blank when the store records none. Measured: pc_mus_001_win11 2 rows, one Yes and one No, both in Chrome Profile 2; hexordia_mvs2025_win11 and mvs2026_macbookpro_macos15 1 row each, Yes. Window Types held TYPE_TABBED (1) on every row; Session Start was blank on the rows of hexordia_mvs2025_win11 and pc_mus_001_win11 and filled on mvs2026_macbookpro_macos15's; Form Factor was blank on pc_mus_001_win11's 2 rows.",
        "paths": (
        '*/AppData/Local/Google/Chrome/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Google/Chrome/*/Sync Data/LevelDB/*',
        '*/.config/google-chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Chromium/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Chromium/*/Sync Data/LevelDB/*',
        '*/.config/chromium/*/Sync Data/LevelDB/*',
        '*/snap/chromium/common/chromium/*/Sync Data/LevelDB/*',
        '*/.var/app/org.chromium.Chromium/config/chromium/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Microsoft/Edge/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Microsoft Edge/*/Sync Data/LevelDB/*',
        '*/.config/microsoft-edge/*/Sync Data/LevelDB/*',
        '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/.config/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Vivaldi/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Vivaldi/*/Sync Data/LevelDB/*',
        '*/.config/vivaldi/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/*/Sync Data/LevelDB/*',
        '*/.config/opera/*/Sync Data/LevelDB/*',
        '*/webbrowser/chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/Sync Data/LevelDB/*',
        '*/.config/opera/Sync Data/LevelDB/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Sync Data folder matched)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no Sync Data folder matched)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no Sync Data folder matched)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no matching data record in the Sync Data folders)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no matching data record in the Sync Data folders)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Sync Data folder matched)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no matching data record in the Sync Data folders)",
        },
    },
    "chromiumSendTabToSelf": {
        "name": "Chromium Send Tab To Self",
        "description": "Pages sent between devices with send tab to self, from the sync data of Chromium-based browser profiles: the title and address, when it was shared, the sending device's name and the target device.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Sync Data/LevelDB folder of each Chromium-based browser profile, in the user data folders the other Chromium artifacts read (Google Chrome, Chromium including its snap and Flatpak, Microsoft Edge, Brave, Vivaldi, Opera and webOS webbrowser), including a folder directly in Opera's user data folder, with the vendored ccl_leveldb, through scripts/chromium/sync_data.py. Browser, Profile and User come from the path as in the other Chromium artifacts, and Source File names the folder a row came from. Chromium keeps each sync data type's records under the keys <type>-dt-<storage key>, with A- in front for account storage, and the type's sync state under <type>-GlobalMetadata (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L26-L63 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L172-L183 and https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/model/blocking_data_type_store_impl.cc#L306-L311). Six of the 13 Sync Data folders read on the tested images held earlier versions of keys as well as the newest one; the other seven held one version of each key. LevelDB numbers each write and orders the versions of a key by decreasing sequence number, the newest first (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Only the newest version of each key is read, and a key whose newest version is a deletion is not reported; the earlier versions are not reported by any artifact, and the run log counts them for each folder. On the tested images that left 149 of hexordia_mvs2025_win11's 5,666 records, 172 of pc_mus_001_win11's 1,732 across five profile folders, 6 of lonewolf_win10's 255 and 77 of mvs2026_macbookpro_macos15's 6,291 as the newest version of a key, before deletions. Values are decoded with the field numbers and types of the messages Chromium publishes under components/sync/protocol at commit 5926523bcfedb77ba2533ace1dd93b477673f72a, transcribed into scripts/chromium/sync_data.py, not by guessing at field types; a record that does not decode is not reported, and the run log names its store and data type; none failed to decode on the tested images. On a Mac logical extraction a folder under System/Volumes/Data that holds the same files with the same bytes as the folder at the same path outside it is read once, as on mvs2026_macbookpro_macos15. Not read: Sync Data folders in the embedded browser profiles other apps keep, such as WebView2 EBWebView folders, ChromeOS profiles, the -md- metadata records, and the data types other than device_info, sessions and send_tab_to_self. Of those, the tested stores held preferences, priority_preferences, search_engines, web_apps, apps, extensions, themes and Edge's own edge_hub_app_usage data records; history_delete_directives, reading_list and the others held only their sync state. Stores with no device_info, sessions or send_tab_to_self data record: ou_ransomware_server2022's three Edge folders and pc_mus_001_win11's Guest Profile and System Profile, which held no data record at all, and ubuntu2604_arm64_chromium's two Chromium folders, which held one web_apps record each. The patterns matched no Sync Data folder in af_case2_win10, szechuan_win10, dleapp_macos_bigsur or evidencelocker_macos14. One row per live send_tab_to_self record, a SendTabToSelfLocal message whose field 1 is the SendTabToSelfSpecifics (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/send_tab_to_self/proto/send_tab_to_self.proto#L17-L19, https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/send_tab_to_self_specifics.proto#L23-L43), written by the bridge (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/send_tab_to_self/send_tab_to_self_bridge.cc#L707). Shared Time is shared_time_usec, the time the tab was shared as measured by the client, in microseconds since 1601-01-01 (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/send_tab_to_self_specifics.proto#L32-L34). Received Time, Opened Time and Activated Time are the received, opened and activated times in the same unit, which the proto says the receiving device sets; the first two are synced back to the sender and the third to the server (https://github.com/chromium/chromium/blob/5926523bcfedb77ba2533ace1dd93b477673f72a/components/sync/protocol/send_tab_to_self_specifics.proto#L70-L85). Title, URL, Sending Device Name (device_name) and Target Cache GUID (target_device_sync_cache_guid) are as stored; Opened and Notification Dismissed are opened and notification_dismissed shown as Yes or No, blank when not stored; and Target Device Name is the name of the device in the Chromium Sync Devices artifact with that Cache GUID, blank when the store lists none. No tested store held a send_tab_to_self data record: hexordia_mvs2025_win11's Edge profile, mvs2026_macbookpro_macos15's Chrome profile and pc_mus_001_win11's Chrome Default, Chrome Profile 2 and Edge Default profiles held only the type's sync state. The field layout comes from Chromium's published proto and is exercised only by synthetic test data; no tested image exercises it.",
        "paths": (
        '*/AppData/Local/Google/Chrome/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Google/Chrome/*/Sync Data/LevelDB/*',
        '*/.config/google-chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Chromium/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Chromium/*/Sync Data/LevelDB/*',
        '*/.config/chromium/*/Sync Data/LevelDB/*',
        '*/snap/chromium/common/chromium/*/Sync Data/LevelDB/*',
        '*/.var/app/org.chromium.Chromium/config/chromium/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Microsoft/Edge/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Microsoft Edge/*/Sync Data/LevelDB/*',
        '*/.config/microsoft-edge/*/Sync Data/LevelDB/*',
        '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/.config/BraveSoftware/Brave-Browser/*/Sync Data/LevelDB/*',
        '*/AppData/Local/Vivaldi/User Data/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/Vivaldi/*/Sync Data/LevelDB/*',
        '*/.config/vivaldi/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/*/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/*/Sync Data/LevelDB/*',
        '*/.config/opera/*/Sync Data/LevelDB/*',
        '*/webbrowser/chrome/*/Sync Data/LevelDB/*',
        '*/AppData/Roaming/Opera Software/Opera Stable/Sync Data/LevelDB/*',
        '*/Library/Application Support/com.operasoftware.Opera/Sync Data/LevelDB/*',
        '*/.config/opera/Sync Data/LevelDB/*',
        ),
        "output_types": "standard",
        "artifact_icon": "send",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Sync Data folder matched)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no Sync Data folder matched)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no Sync Data folder matched)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no matching data record in the Sync Data folders)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no matching data record in the Sync Data folders)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no matching data record in the Sync Data folders)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no matching data record in the Sync Data folders)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no matching data record in the Sync Data folders)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Sync Data folder matched)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (no matching data record in the Sync Data folders)",
        },
    },
}

import datetime

from scripts.chromium.browser_profiles import enum_label, row_tail, webkit_time
from scripts.chromium.sync_data import (BROWSER_TYPES, DEVICE_TYPES, FORM_FACTORS, OS_TYPES,
                                        PAGE_TRANSITIONS, ProtoError, SyncStore, decode,
                                        sync_folders)
from scripts.ilapfuncs import artifact_processor, logfunc


def _ms_time(value):
    """Milliseconds since 1970-01-01 UTC as a datetime; '' for missing, zero or out of range."""
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        return ''
    if milliseconds <= 0:
        return ''
    try:
        return datetime.datetime.fromtimestamp(milliseconds / 1000, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _yes_no(value):
    if value is None:
        return ''
    return 'Yes' if value else 'No'


def _stores(context, label):
    """(Store, SyncStore) for each Sync Data/LevelDB folder that could be read."""
    out = []
    for store in sync_folders(context, label):
        try:
            sync = SyncStore(store.path)
        except (OSError, ValueError, EOFError) as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        logfunc(f'{label}: {store.relative}: {sync.records} records, {sync.superseded} older '
                f'versions of a key not read, {sync.deleted} keys whose newest version is a '
                f'deletion')
        out.append((store, sync))
    return out


def _decoded(sync, root_tag, message, label, store):
    """(storage key, decoded message) for each live data record of one type that decodes."""
    out = []
    for _account, storage_key, value in sync.records_of(root_tag):
        try:
            out.append((storage_key, decode(value, message)))
        except ProtoError as ex:
            logfunc(f'{label}: {store.relative}: a {root_tag} record did not decode as '
                    f'{message} and is not reported: {ex}')
    return out


def _devices(sync, label, store):
    """{cache GUID: DeviceInfoSpecifics} from the live device_info records."""
    devices = {}
    for _key, device in _decoded(sync, 'device_info', 'DeviceInfoSpecifics', label, store):
        devices.setdefault(device.get('cache_guid', ''), device)
    return devices


def _local_guid(sync, root_tag, label, store):
    try:
        return sync.local_cache_guid(root_tag)
    except ProtoError as ex:
        logfunc(f'{label}: {store.relative}: the {root_tag} sync state did not decode, so '
                f'This Device is blank: {ex}')
        return ''


def _this_device(guid, local_guid):
    if not local_guid:
        return ''
    return 'Yes' if guid == local_guid else 'No'


@artifact_processor
def chromiumSyncDevices(context):
    label = 'Chromium Sync Devices'
    data_list = []
    sources = []
    for store, sync in _stores(context, label):
        local_guid = _local_guid(sync, 'device_info', label, store)
        rows = 0
        for _key, device in _decoded(sync, 'device_info', 'DeviceInfoSpecifics', label, store):
            guid = device.get('cache_guid', '')
            version = (device.get('chrome_version_info') or {}).get('version_number')
            if version is None:
                version = device.get('chrome_version', '')
            data_list.append((
                _ms_time(device.get('last_updated_timestamp')),
                device.get('client_name', ''),
                _this_device(guid, local_guid),
                device.get('manufacturer', ''),
                device.get('model', ''),
                enum_label(OS_TYPES, device.get('os_type')),
                enum_label(FORM_FACTORS, device.get('device_form_factor')),
                enum_label(DEVICE_TYPES, device.get('device_type')),
                version,
                device.get('sync_user_agent', ''),
                guid,
                device.get('signin_scoped_device_id', ''),
            ) + row_tail(store))
            rows += 1
        if rows:
            sources.append(store.path)
    data_headers = (('Last Updated', 'datetime'), 'Device Name', 'This Device', 'Manufacturer',
                    'Model', 'OS Type', 'Form Factor', 'Device Type', 'Chrome Version',
                    'Sync User Agent', 'Cache GUID', 'Signin Scoped Device ID', 'Browser',
                    'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


def _sessions(sync, label, store):
    """(headers {session tag: SessionHeader}, tabs [(session tag, SessionTab)])."""
    headers, tabs = {}, []
    for _key, session in _decoded(sync, 'sessions', 'SessionSpecifics', label, store):
        tag = session.get('session_tag', '')
        if 'header' in session:
            headers[tag] = session['header']
        elif 'tab' in session:
            tabs.append((tag, session['tab']))
    return headers, tabs


def _device_name(tag, headers, devices):
    name = headers.get(tag, {}).get('client_name')
    if name is None:
        name = devices.get(tag, {}).get('client_name', '')
    return name


@artifact_processor
def chromiumSyncedTabs(context):
    label = 'Chromium Synced Tabs'
    data_list = []
    sources = []
    for store, sync in _stores(context, label):
        local_guid = _local_guid(sync, 'sessions', label, store)
        devices = _devices(sync, label, store)
        headers, tabs = _sessions(sync, label, store)
        rows = 0
        for tag, tab in sorted(tabs, key=lambda item: (item[0], item[1].get('window_id', 0),
                                                        item[1].get('tab_id', 0))):
            current = tab.get('current_navigation_index')
            for index, navigation in enumerate(tab.get('navigation', [])):
                data_list.append((
                    _ms_time(navigation.get('timestamp_msec')),
                    _ms_time(tab.get('last_active_time_unix_epoch_millis')),
                    _device_name(tag, headers, devices),
                    _this_device(tag, local_guid),
                    navigation.get('virtual_url', ''),
                    navigation.get('title', ''),
                    navigation.get('referrer', ''),
                    navigation.get('http_status_code', ''),
                    enum_label(PAGE_TRANSITIONS, navigation.get('page_transition')),
                    _yes_no(navigation.get('navigation_from_address_bar')),
                    index,
                    '' if current is None else ('Yes' if index == current else 'No'),
                    _yes_no(tab.get('pinned')),
                    tab.get('tab_id', ''),
                    tab.get('window_id', ''),
                    tag,
                ) + row_tail(store))
                rows += 1
        if rows:
            sources.append(store.path)
    data_headers = (('Navigation Time', 'datetime'), ('Tab Last Active', 'datetime'),
                    'Device Name', 'This Device', 'URL', 'Title', 'Referrer', 'HTTP Status',
                    'Transition', 'From Address Bar', 'Navigation Index', 'Current Entry',
                    'Pinned', 'Tab ID', 'Window ID', 'Session Tag', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumSyncedSessions(context):
    label = 'Chromium Synced Sessions'
    data_list = []
    sources = []
    for store, sync in _stores(context, label):
        local_guid = _local_guid(sync, 'sessions', label, store)
        headers, _tabs = _sessions(sync, label, store)
        rows = 0
        for tag, header in sorted(headers.items()):
            windows = header.get('window', [])
            browser_types = sorted({enum_label(BROWSER_TYPES, window.get('browser_type'))
                                    for window in windows if 'browser_type' in window})
            data_list.append((
                header.get('client_name', ''),
                _this_device(tag, local_guid),
                enum_label(FORM_FACTORS, header.get('device_form_factor')),
                enum_label(DEVICE_TYPES, header.get('device_type')),
                len(windows),
                sum(len(window.get('tab', [])) for window in windows),
                ', '.join(browser_types),
                _ms_time(header.get('session_start_time_unix_epoch_millis')),
                tag,
            ) + row_tail(store))
            rows += 1
        if rows:
            sources.append(store.path)
    data_headers = ('Device Name', 'This Device', 'Form Factor', 'Device Type', 'Windows',
                    'Tabs Listed', 'Window Types', ('Session Start', 'datetime'), 'Session Tag',
                    'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumSendTabToSelf(context):
    label = 'Chromium Send Tab To Self'
    data_list = []
    sources = []
    for store, sync in _stores(context, label):
        devices = _devices(sync, label, store)
        rows = 0
        for _key, local in _decoded(sync, 'send_tab_to_self', 'SendTabToSelfLocal', label, store):
            entry = local.get('specifics', {})
            target = entry.get('target_device_sync_cache_guid', '')
            data_list.append((
                webkit_time(entry.get('shared_time_usec')),
                webkit_time(entry.get('received_time_windows_epoch_micros')),
                webkit_time(entry.get('opened_time_windows_epoch_micros')),
                webkit_time(entry.get('activated_time_windows_epoch_micros')),
                entry.get('title', ''),
                entry.get('url', ''),
                entry.get('device_name', ''),
                devices.get(target, {}).get('client_name', '') if target else '',
                target,
                _yes_no(entry.get('opened')),
                _yes_no(entry.get('notification_dismissed')),
                entry.get('guid', ''),
            ) + row_tail(store))
            rows += 1
        if rows:
            sources.append(store.path)
    data_headers = (('Shared Time', 'datetime'), ('Received Time', 'datetime'),
                    ('Opened Time', 'datetime'), ('Activated Time', 'datetime'), 'Title', 'URL',
                    'Sending Device Name', 'Target Device Name', 'Target Cache GUID', 'Opened',
                    'Notification Dismissed', 'GUID', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
