"""Site permission settings, permission prompt actions and prompt counts from the
Preferences file of Chromium-based browser profiles, for DLEAPP.

Ported from ALEAPP's chromiumSitePermissions.py, with the permission list sourced for
desktop builds and the browser, profile and user taken from scripts/chromium/browser_profiles.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "chromiumSitePermissions": {
        "name": "Chromium Site Permissions",
        "description": "Per-site permission settings (location, notifications, camera, microphone and the other "
                       "content settings Chromium's permission request types map to) stored in the Preferences file "
                       "of Chromium-based browser profiles, with each entry's last_modified time where the browser "
                       "stored one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Preferences file of each Chromium-based browser profile that scripts/chromium/browser_profiles "
                 "locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and "
                 "webOS webbrowser) on Windows, macOS and Linux. Secure Preferences, and files beside Preferences such as "
                 "Preferences.backup, are not read; none of the 16 Secure Preferences files on the 7 tested images held a "
                 "profile.content_settings key. Format and meanings come from Chromium at commit "
                 "77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784. The rows on the tested images carry times from March 2018 to "
                 "December 2025. The two Preferences files of cfreds_leakage_win7 hold an empty "
                 "profile.content_settings.pattern_pairs and no exceptions key; pattern_pairs is not read and its meaning "
                 "was not sourced. Times are stored as microseconds since 1601-01-01 UTC, written as a string "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L22-L23, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L44-L46, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L60-L62), "
                 "and are shown in UTC; a missing, non-numeric, zero, negative or out-of-range time is blank. Browser, "
                 "Profile and User come from the path, as in "
                 "the other Chromium artifacts, and Source File names the file each row came from. On a Mac logical "
                 "extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a byte-identical copy "
                 "under the second path is read once, as it was on mvs2026_macbookpro_macos15. A file that does not parse "
                 "as JSON is skipped and named in the run log. Ported from ALEAPP's Chromium Site Permissions. "
                 "Each row is one per-site exception in profile.content_settings.exceptions for a content setting "
                 "that Chromium's permission request types map to: the types RequestTypeToContentSettingsType returns in any build "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/request_type.cc#L392-L480), "
                 "under the names Chromium stores them with, each - of the registered name written as _ "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/website_settings_info.cc#L18-L27): "
                 "ar, camera_pan_tilt_zoom, captured_surface_control, clipboard, geolocation, geolocation_with_options, "
                 "hand_tracking, idle_detection, keyboard_lock, local_fonts, local_network, loopback_network, "
                 "media_stream_camera, media_stream_mic, midi_sysex, nfc_devices, notifications, pointer_lock, "
                 "protected_media_identifier, sensors, smart_card_data, storage_access, top_level_storage_access, vr, "
                 "web_app_installation, web_printing and window_placement; and automatic_downloads, which the "
                 "multiple-downloads limiter writes itself "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/chrome/browser/download/download_request_limiter.cc#L261-L263). "
                 "Geolocation is stored under geolocation, or under geolocation_with_options when Chromium's "
                 "approximate-location feature is on "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/common/content_settings_utils.cc#L108-L113). "
                 "Other exception types (site engagement, cookies, JavaScript and the like), the defaults in "
                 "profile.default_content_setting_values, and the partitioned_exceptions list "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/website_settings_info.cc#L18-L21) "
                 "are not read; no tested file held a partitioned_exceptions list. On desktop a site's notification "
                 "setting is an exception in this file: Chromium registers notifications for desktop and Android builds "
                 "alike (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_registry.cc#L158-L169) "
                 "and registers an Android notification channel provider for it only in Android builds "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/chrome/browser/content_settings/host_content_settings_map_factory.cc#L178-L190), "
                 "so the Android channel caveat in the ALEAPP notes does not apply here. Each exception is keyed by a "
                 "pattern pair "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_pref.cc#L507-L508). "
                 "Site is the first pattern and Embedding Site the second, both as stored; what the second pattern means "
                 "differs by permission type and was not sourced per type. "
                 "Setting is the stored ContentSetting number with its name: 0 Default, 1 Allow, 2 Block, 3 Ask, 4 Session "
                 "only (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/common/content_settings.h#L26-L33). "
                 "A setting that is not a number, such as the GeolocationSetting object geolocation_with_options stores "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/permission_settings_registry.cc#L79-L88, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/geolocation_setting_delegate.cc#L65-L72), "
                 "is shown as its stored JSON; no tested file held one. Last Modified, Expiration and Last Visit are the "
                 "exception's last_modified, expiration and last_visit values "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_pref.cc#L45-L51, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_pref.cc#L538-L559). "
                 "When the stored value is cleared the browser removes the entry's setting, last_modified, last_visit, "
                 "expiration, model, lifetime and decided_by_related_website_sets keys "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_pref.cc#L526-L536) "
                 "and then the entry itself if nothing is left in it "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_pref.cc#L576-L579). "
                 "A row records the stored setting and its last_modified time, not who or what set it. "
                 "On the tested images: 7 rows on 2 of 7 images, all from Google Chrome. lonewolf_win10 held 4 "
                 "geolocation rows with Setting Allow (1) and 2 notifications rows with Setting Block (2); "
                 "mvs2026_macbookpro_macos15 held 1 notifications row with Setting Allow (1). Embedding Site repeated Site "
                 "on all 4 geolocation rows and held * on all 3 notifications rows, which is consistent with "
                 "notifications being registered with requesting-origin-only scope "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/content_settings_registry.cc#L163). "
                 "Expiration and Last Visit held no value on any of the 7 rows. Browser, Profile and User held one value "
                 "on all 6 rows of lonewolf_win10, whose one Chrome profile held these entries. The Preferences files of "
                 "cfreds_leakage_win7, ou_ransomware_server2022, pc_mus_001_win11, ubuntu2604_arm64_chromium and "
                 "windows11_arm_operagx_360se_known_20261107 held none of these entries. Not exercised by the tested "
                 "files: every permission type other than geolocation and notifications, Setting values other than Allow "
                 "and Block, a setting that is not a number, and any Expiration or Last Visit value. No row came from a "
                 "browser other than Google Chrome: Microsoft Edge, Chromium, Opera GX and 360 Safe Browser files were "
                 "read and held none of these entries, and no Brave, Vivaldi, Opera or webOS webbrowser file was in the "
                 "tested images.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Preferences*',
            '*/.config/google-chrome/*/Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Preferences*',
            '*/Library/Application Support/Chromium/*/Preferences*',
            '*/.config/chromium/*/Preferences*',
            '*/snap/chromium/common/chromium/*/Preferences*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Preferences*',
            '*/webbrowser/chrome/*/Preferences*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Preferences*',
            '*/Library/Application Support/Microsoft Edge/*/Preferences*',
            '*/.config/microsoft-edge/*/Preferences*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Preferences*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/.config/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/AppData/Local/Vivaldi/User Data/*/Preferences*',
            '*/Library/Application Support/Vivaldi/*/Preferences*',
            '*/.config/vivaldi/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Preferences*',
            '*/AppData/Roaming/360se6/User Data/*/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Preferences*',
            '*/.config/opera/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Preferences*',
            '*/AppData/Roaming/360se6/User Data/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Preferences*',
            '*/.config/opera/Preferences*',
        ),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (its Preferences held no such entry)",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 6 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (its Preferences held no such entry)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (its Preferences held no such entry)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (its Preferences held no such entry)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (its Preferences held no such entry)",
        },
    },
    "chromiumPermissionActions": {
        "name": "Chromium Permission Prompt Actions",
        "description": "Entries of a Chromium-based browser's permission action history (action, how the prompt was "
                       "shown, permission and time) from the profile's Preferences file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Preferences file of each Chromium-based browser profile that scripts/chromium/browser_profiles "
                 "locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and "
                 "webOS webbrowser) on Windows, macOS and Linux. Secure Preferences, and files beside Preferences such as "
                 "Preferences.backup, are not read; none of the 16 Secure Preferences files on the 7 tested images held a "
                 "profile.content_settings key. Format and meanings come from Chromium at commit "
                 "77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784. The rows on the tested images carry times from March 2018 to "
                 "December 2025. The two Preferences files of cfreds_leakage_win7 hold an empty "
                 "profile.content_settings.pattern_pairs and no exceptions key; pattern_pairs is not read and its meaning "
                 "was not sourced. Times are stored as microseconds since 1601-01-01 UTC, written as a string "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L22-L23, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L44-L46, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L60-L62), "
                 "and are shown in UTC; a missing, non-numeric, zero, negative or out-of-range time is blank. Browser, "
                 "Profile and User come from the path, as in "
                 "the other Chromium artifacts, and Source File names the file each row came from. On a Mac logical "
                 "extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a byte-identical copy "
                 "under the second path is read once, as it was on mvs2026_macbookpro_macos15. A file that does not parse "
                 "as JSON is skipped and named in the run log. Ported from ALEAPP's Chromium Permission Prompt Actions. "
                 "Each row is one entry of profile.content_settings.permission_actions, which Chromium's source "
                 "describes as a history of past permission actions "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L30-L45). "
                 "An entry holds no site: it records the permission, the action, how the prompt was shown and the time "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L149-L178). "
                 "Permission is the list's key as stored. Action is the stored PermissionAction number with its name: "
                 "0 GRANTED, 1 DENIED, 2 DISMISSED, 3 IGNORED, 4 REVOKED, 5 GRANTED_ONCE "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_uma_constants.h#L13-L19). "
                 "Prompt Shown As is the stored PermissionPromptDisposition number with its name "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_uma_constants.h#L214-L277); "
                 "entries written before Chrome 96 have none "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L43-L45). "
                 "When the browser records an action it drops entries older than 90 days from that permission's list "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L59, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L158-L168); "
                 "the lists of other permissions are not pruned by that call. It also has a call that removes the entries "
                 "in a time range "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_actions_history.cc#L181-L200); "
                 "which clearing choices reach it was not traced. On the tested images: 7 rows on 2 of 7 images, all "
                 "from Google Chrome. pc_mus_001_win11 held 5 across its Default and Profile 2 profiles (notifications 3, "
                 "geolocation 1, idle_detection 1) and mvs2026_macbookpro_macos15 held 2 (geolocation). Action held one "
                 "value, DISMISSED (2), on all 5 rows of pc_mus_001_win11, and IGNORED (3) on both rows of "
                 "mvs2026_macbookpro_macos15. Prompt Shown As held one value, ANCHORED_BUBBLE (1), on all 7 rows. Browser "
                 "and User held one value on all 5 rows of pc_mus_001_win11. lonewolf_win10 held no prompt action entries "
                 "although its Preferences held a prompt count; why was not established. The other images held none. Not "
                 "exercised by the tested files: Action values other than DISMISSED and IGNORED, Prompt Shown As values "
                 "other than ANCHORED_BUBBLE, and an entry with no prompt_disposition. No row came from a browser other "
                 "than Google Chrome: Microsoft Edge, Chromium, Opera GX and 360 Safe Browser files were read and held no "
                 "such entry, and no Brave, Vivaldi, Opera or webOS webbrowser file was in the tested images.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Preferences*',
            '*/.config/google-chrome/*/Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Preferences*',
            '*/Library/Application Support/Chromium/*/Preferences*',
            '*/.config/chromium/*/Preferences*',
            '*/snap/chromium/common/chromium/*/Preferences*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Preferences*',
            '*/webbrowser/chrome/*/Preferences*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Preferences*',
            '*/Library/Application Support/Microsoft Edge/*/Preferences*',
            '*/.config/microsoft-edge/*/Preferences*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Preferences*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/.config/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/AppData/Local/Vivaldi/User Data/*/Preferences*',
            '*/Library/Application Support/Vivaldi/*/Preferences*',
            '*/.config/vivaldi/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Preferences*',
            '*/AppData/Roaming/360se6/User Data/*/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Preferences*',
            '*/.config/opera/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Preferences*',
            '*/AppData/Roaming/360se6/User Data/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Preferences*',
            '*/.config/opera/Preferences*',
        ),
        "output_types": "standard",
        "artifact_icon": "check-square",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (its Preferences held no such entry)",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 0 rows (its Preferences held no such entry)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (its Preferences held no such entry)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 5 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (its Preferences held no such entry)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (its Preferences held no such entry)",
        },
    },
    "chromiumPermissionPromptCounts": {
        "name": "Chromium Permission Prompt Counts",
        "description": "Per site and permission, the dismiss and ignore counts a Chromium-based browser stores for "
                       "its permission prompt, from the profile's Preferences file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Preferences file of each Chromium-based browser profile that scripts/chromium/browser_profiles "
                 "locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and "
                 "webOS webbrowser) on Windows, macOS and Linux. Secure Preferences, and files beside Preferences such as "
                 "Preferences.backup, are not read; none of the 16 Secure Preferences files on the 7 tested images held a "
                 "profile.content_settings key. Format and meanings come from Chromium at commit "
                 "77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784. The rows on the tested images carry times from March 2018 to "
                 "December 2025. The two Preferences files of cfreds_leakage_win7 hold an empty "
                 "profile.content_settings.pattern_pairs and no exceptions key; pattern_pairs is not read and its meaning "
                 "was not sourced. Times are stored as microseconds since 1601-01-01 UTC, written as a string "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L22-L23, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L44-L46, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/base/json/values_util.cc#L60-L62), "
                 "and are shown in UTC; a missing, non-numeric, zero, negative or out-of-range time is blank. Browser, "
                 "Profile and User come from the path, as in "
                 "the other Chromium artifacts, and Source File names the file each row came from. On a Mac logical "
                 "extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a byte-identical copy "
                 "under the second path is read once, as it was on mvs2026_macbookpro_macos15. A file that does not parse "
                 "as JSON is skipped and named in the run log. Ported from ALEAPP's Chromium Permission Prompt Counts. "
                 "Each row is one permission of one site in the permission_autoblocking_data exception, registered as "
                 "permission-autoblocking-data "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/website_settings_registry.cc#L164-L165) "
                 "and stored with - written as _ "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/content_settings/core/browser/website_settings_info.cc#L18-L27), "
                 "whose dismiss_count and ignore_count keys "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L217-L222) "
                 "are raised by one each time the browser records a dismissed or ignored prompt for that site and "
                 "permission (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L124-L142, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L388-L393, "
                 "https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L427-L432). "
                 "Chromium has a call that removes a permission's counts "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L481-L490), "
                 "so a count is the value stored now; which actions reach that call was not traced. "
                 "Site is the first pattern of the exception. Permission (as stored) is the stored key, for example "
                 "Notifications, Geolocation or IdleDetection. Dismiss Count and Ignore Count are the dismiss_count and "
                 "ignore_count values; Other Values (as stored) holds the entry's remaining keys, such as "
                 "dismiss_count_quiet_ui, ignore_count_quiet_ui and dismissal_embargo_days "
                 "(https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/components/permissions/permission_decision_auto_blocker.cc#L217-L234). Last Modified "
                 "is the exception's last_modified value and is shared by every permission of that site. On the tested "
                 "images: 7 rows on 3 of 7 images, all from Google Chrome. pc_mus_001_win11 held 5 (Notifications 3, "
                 "Geolocation 1, IdleDetection 1), mvs2026_macbookpro_macos15 held 1 (Geolocation) and lonewolf_win10 held "
                 "1 (Notifications). Dismiss Count held one value, 1, on all 5 rows of pc_mus_001_win11, and no value on "
                 "the rows of lonewolf_win10 and mvs2026_macbookpro_macos15, where Ignore Count held 1 and 2. Ignore Count "
                 "held no value on any of the 5 rows of pc_mus_001_win11. Other Values (as stored) held no value on any of "
                 "the 7 rows. Browser and User held one value on all 5 rows of pc_mus_001_win11. On the 6 rows of "
                 "pc_mus_001_win11 and mvs2026_macbookpro_macos15, Last Modified fell within 0.03 ms of a Chromium "
                 "Permission Prompt Actions row for the same profile and permission; lonewolf_win10 held no prompt action "
                 "entries to compare. Not exercised by the tested files: any key in Other Values (as stored). No row came "
                 "from a browser other than Google Chrome: Microsoft Edge, Chromium, Opera GX and 360 Safe Browser files "
                 "were read and held no such entry, and no Brave, Vivaldi, Opera or webOS webbrowser file was in the "
                 "tested images.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Preferences*',
            '*/.config/google-chrome/*/Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Preferences*',
            '*/Library/Application Support/Chromium/*/Preferences*',
            '*/.config/chromium/*/Preferences*',
            '*/snap/chromium/common/chromium/*/Preferences*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Preferences*',
            '*/webbrowser/chrome/*/Preferences*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Preferences*',
            '*/Library/Application Support/Microsoft Edge/*/Preferences*',
            '*/.config/microsoft-edge/*/Preferences*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Preferences*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/.config/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/AppData/Local/Vivaldi/User Data/*/Preferences*',
            '*/Library/Application Support/Vivaldi/*/Preferences*',
            '*/.config/vivaldi/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Preferences*',
            '*/AppData/Roaming/360se6/User Data/*/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Preferences*',
            '*/.config/opera/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Preferences*',
            '*/AppData/Roaming/360se6/User Data/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Preferences*',
            '*/.config/opera/Preferences*',
        ),
        "output_types": "standard",
        "artifact_icon": "x-square",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (its Preferences held no such entry)",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 1 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (its Preferences held no such entry)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 5 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (its Preferences held no such entry)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (its Preferences held no such entry)",
        },
    },
}

import json

from scripts.chromium.browser_profiles import enum_label, profile_stores, row_tail, webkit_time
from scripts.ilapfuncs import artifact_processor, logfunc

# The content settings a permission prompt can set: the types
# RequestTypeToContentSettingsType returns (components/permissions/request_type.cc), as
# stored, with '-' in the registered name replaced by '_'; plus automatic_downloads,
# which the multiple-downloads limiter writes itself, and geolocation_with_options.
_PERMISSION_TYPES = (
    'ar', 'automatic_downloads', 'camera_pan_tilt_zoom', 'captured_surface_control', 'clipboard',
    'geolocation', 'geolocation_with_options', 'hand_tracking', 'idle_detection', 'keyboard_lock',
    'local_fonts', 'local_network', 'loopback_network', 'media_stream_camera', 'media_stream_mic',
    'midi_sysex', 'nfc_devices', 'notifications', 'pointer_lock', 'protected_media_identifier',
    'sensors', 'smart_card_data', 'storage_access', 'top_level_storage_access', 'vr',
    'web_app_installation', 'web_printing', 'window_placement',
)
_SETTINGS = {0: 'Default', 1: 'Allow', 2: 'Block', 3: 'Ask', 4: 'Session only'}
_ACTIONS = {0: 'GRANTED', 1: 'DENIED', 2: 'DISMISSED', 3: 'IGNORED', 4: 'REVOKED', 5: 'GRANTED_ONCE'}
_DISPOSITIONS = {
    0: 'NOT_APPLICABLE', 1: 'ANCHORED_BUBBLE', 2: 'LOCATION_BAR_RIGHT_STATIC_ICON',
    3: 'LOCATION_BAR_RIGHT_ANIMATED_ICON', 4: 'MODAL_DIALOG', 5: 'MINI_INFOBAR', 6: 'LOCATION_BAR_LEFT_CHIP',
    7: 'NONE_VISIBLE', 8: 'CUSTOM_MODAL_DIALOG', 9: 'LOCATION_BAR_LEFT_QUIET_CHIP', 10: 'MESSAGE_UI',
    11: 'LOCATION_BAR_LEFT_QUIET_ABUSIVE_CHIP', 12: 'LOCATION_BAR_LEFT_CHIP_AUTO_BUBBLE',
    13: 'ELEMENT_ANCHORED_BUBBLE', 15: 'MESSAGE_UI_LOUD', 16: 'LOCATION_BAR_LEFT_QUIET_ICON',
}


def _content_settings(context, label):
    """[(store, content_settings dict)] for each Preferences file of a browser profile."""
    found = []
    for store in profile_stores(context, {'Preferences'}, label):
        try:
            with open(store.path, 'r', encoding='utf-8') as handle:
                document = json.load(handle)
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        profile = document.get('profile') if isinstance(document, dict) else None
        settings = profile.get('content_settings') if isinstance(profile, dict) else None
        found.append((store, settings if isinstance(settings, dict) else {}))
    return found


def _exceptions(settings, kind):
    exceptions = settings.get('exceptions')
    sites = exceptions.get(kind) if isinstance(exceptions, dict) else None
    return sites.items() if isinstance(sites, dict) else ()


def _patterns(key):
    """The primary and secondary site pattern of a stored pattern pair key."""
    primary, _, secondary = str(key).partition(',')
    return primary, secondary


def _setting(value):
    """A stored setting: 'NAME (n)' for a ContentSetting number, else the stored value as JSON."""
    if isinstance(value, bool) or value is None:
        return '' if value is None else json.dumps(value)
    if isinstance(value, int):
        return enum_label(_SETTINGS, value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@artifact_processor
def chromiumSitePermissions(context):
    data_headers = (('Last Modified', 'datetime'), ('Expiration', 'datetime'), ('Last Visit', 'datetime'),
                    'Site', 'Embedding Site', 'Permission', 'Setting', 'Browser', 'Profile', 'User',
                    'Source File')
    data_list, sources = [], []
    for store, settings in _content_settings(context, 'Chromium Site Permissions'):
        sources.append(store.path)
        for kind in _PERMISSION_TYPES:
            for key, value in _exceptions(settings, kind):
                if not isinstance(value, dict):
                    continue
                site, embedding = _patterns(key)
                data_list.append((webkit_time(value.get('last_modified')), webkit_time(value.get('expiration')),
                                  webkit_time(value.get('last_visit')), site, embedding, kind,
                                  _setting(value.get('setting'))) + row_tail(store))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumPermissionActions(context):
    data_headers = (('Time', 'datetime'), 'Permission', 'Action', 'Prompt Shown As', 'Browser', 'Profile',
                    'User', 'Source File')
    data_list, sources = [], []
    for store, settings in _content_settings(context, 'Chromium Permission Prompt Actions'):
        sources.append(store.path)
        actions = settings.get('permission_actions')
        for kind, entries in (actions.items() if isinstance(actions, dict) else ()):
            for entry in (entries if isinstance(entries, list) else ()):
                if not isinstance(entry, dict):
                    continue
                data_list.append((webkit_time(entry.get('time')), kind,
                                  enum_label(_ACTIONS, entry.get('action')),
                                  enum_label(_DISPOSITIONS, entry.get('prompt_disposition'))) + row_tail(store))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumPermissionPromptCounts(context):
    data_headers = (('Last Modified', 'datetime'), 'Site', 'Permission (as stored)', 'Dismiss Count',
                    'Ignore Count', 'Other Values (as stored)', 'Browser', 'Profile', 'User', 'Source File')
    data_list, sources = [], []
    for store, settings in _content_settings(context, 'Chromium Permission Prompt Counts'):
        sources.append(store.path)
        for key, value in _exceptions(settings, 'permission_autoblocking_data'):
            counts = value.get('setting') if isinstance(value, dict) else None
            if not isinstance(counts, dict):
                continue
            site, _ = _patterns(key)
            for kind, entry in counts.items():
                if not isinstance(entry, dict):
                    continue
                other = ', '.join(f'{name}={entry[name]}' for name in sorted(entry)
                                  if name not in ('dismiss_count', 'ignore_count'))
                data_list.append((webkit_time(value.get('last_modified')), site, kind,
                                  entry.get('dismiss_count', ''), entry.get('ignore_count', ''), other)
                                 + row_tail(store))
    return data_headers, data_list, '\n'.join(sources)
