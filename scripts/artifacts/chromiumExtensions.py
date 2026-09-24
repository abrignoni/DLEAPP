__artifacts_v2__ = {
    "chromiumExtensions": {
        "name": "Chromium Extensions",
        "description": "Extension entries that record an install location, other than the browser's own "
                       "components, from the extensions.settings dictionary in the Preferences and "
                       "Secure Preferences files of Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera "
                       "and Chromium profiles, with the stored manifest name and version, install "
                       "location, install times, state and disable reasons.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the extensions.settings dictionary "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/browser/pref_names.h#L70-L72) "
                 "of each Chromium-based browser profile's Preferences and Secure Preferences files; one "
                 "row per file and extension id, so an extension listed in both files has two rows, and "
                 "Preferences File names the file. An entry with no location is not reported. An entry "
                 "whose location is COMPONENT (5) or EXTERNAL_COMPONENT (10) is not reported either: the "
                 "source describes those as parts of the browser itself "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/common/mojom/manifest.mojom#L30-L32 "
                 "and "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/common/mojom/manifest.mojom#L42-L45), "
                 "and the run log counts them per file. That left out 26 component entries on "
                 "pc_mus_001_win11 and 10 on lonewolf_win10, and 20 entries with no location in the "
                 "Microsoft Edge Secure Preferences of pc_mus_001_win11. Browser, Profile and User come "
                 "from the path: the browser from the user data folder, the profile from the folder inside "
                 "it, and the user from the home folder that holds it; Source File names the file each row "
                 "came from, so rows from two profiles or two users stay apart. A profile under User "
                 "Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot copy "
                 "is not merged with the live profile; no registered image carries one, and that branch "
                 "was exercised on a constructed tree only. Name and Version are the name and version of "
                 "the manifest stored in the entry, which Chromium stores for every location other than "
                 "UNPACKED (4) and COMMAND_LINE (8) "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/browser/extension_prefs.cc#L2402-L2408, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/common/manifest.h#L66-L69); "
                 "they are blank where the entry has no manifest. Location shows the stored integer with "
                 "its name from manifest.mojom "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/common/mojom/manifest.mojom#L18-L46). "
                 "Install Time is install_time, which the Chrome 65 release wrote with "
                 "base::Time::ToInternalValue each time it populated the entry "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/extensions/browser/extension_prefs.cc#L1813-L1824). "
                 "First Install Time and Last Update Time are first_install_time, kept from the first "
                 "write, and last_update_time, rewritten each time, as current Chromium writes them "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/browser/extension_prefs.cc#L2354-L2361); "
                 "all three are microseconds since 1601-01-01 UTC. The tested images carry install_time "
                 "only, so First Install Time and Last Update Time are blank on every row of "
                 "pc_mus_001_win11 and lonewolf_win10. State (as stored) is the state key with its name "
                 "from the Chrome 65 extension.h "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/extensions/common/extension.h#L50-L56). "
                 "Current Chromium lists state among the obsolete keys "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/browser/extension_prefs.cc#L2700) "
                 "and removes those keys from every entry (same file, lines 2715 to 2724), so State is "
                 "blank where an entry no longer carries the key. Disable Reasons names each bit of the "
                 "stored disable_reasons, a number in older releases and a list in newer ones, from "
                 "disable_reason.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/extensions/browser/disable_reason.h#L26-L72). "
                 "Disable Reasons was blank on every row of pc_mus_001_win11; on lonewolf_win10 it was "
                 "EXTERNAL_EXTENSION (8192) on the one row whose State is DISABLED (0). From Web Store and "
                 "Installed By Default are from_webstore and was_installed_by_default as stored. From Web "
                 "Store held one value, Yes, on every row of lonewolf_win10, and Preferences File held one "
                 "value, Secure Preferences, on every row of both images: their Preferences files held no "
                 "extensions.settings entries. Browser, Profile and User each held one value on every row "
                 "of lonewolf_win10, which carries one Chrome profile in one home folder, and User held "
                 "one value on every row of pc_mus_001_win11, whose Chrome and Edge profiles sit in one "
                 "home folder. Tested: Chrome 108.0.5359.125 and Microsoft Edge 108.0.1462.54 on "
                 "pc_mus_001_win11, and Chrome 65.0.3325.181 on lonewolf_win10. The extension files under "
                 "a profile's Extensions folder are not read. No member of af_case2_win10 or "
                 "dleapp_macos_bigsur matched any of the declared paths. The user data folders read are "
                 "those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, "
                 "macOS and Linux, and a store directly inside a user data folder is reported with that "
                 "folder as its Profile. Only the Windows Google Chrome and Microsoft Edge folders were "
                 "exercised by a registered image; a constructed tree exercised the Brave macOS, Vivaldi "
                 "Linux and Opera Windows folders, the last with its profile kept directly in the user "
                 "data folder, and the remaining folders were not exercised. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical "
                 "is read once and counted in the run log, and copies that differ are both "
                 "read. The macOS Google Chrome folder was also exercised, on the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus "
                 "key), where each store was byte-identical under the two paths. "
                 "Not read: other Chrome "
                 "channels (Beta, Dev, Canary), extension storage partitions under a profile's Storage "
                 "folder, and WebView2 or Electron app profiles such as EBWebView folders, which share the "
                 "layout but sit in other applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Preferences*',
            '*/.config/google-chrome/*/Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Preferences*',
            '*/Library/Application Support/Chromium/*/Preferences*',
            '*/.config/chromium/*/Preferences*',
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
            '*/Library/Application Support/com.operasoftware.Opera/*/Preferences*',
            '*/.config/opera/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Preferences*',
            '*/.config/opera/Preferences*',
            '*/AppData/Local/Google/Chrome/User Data/*/Secure Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Secure Preferences*',
            '*/.config/google-chrome/*/Secure Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Secure Preferences*',
            '*/Library/Application Support/Chromium/*/Secure Preferences*',
            '*/.config/chromium/*/Secure Preferences*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Secure Preferences*',
            '*/Library/Application Support/Microsoft Edge/*/Secure Preferences*',
            '*/.config/microsoft-edge/*/Secure Preferences*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Secure Preferences*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Secure Preferences*',
            '*/.config/BraveSoftware/Brave-Browser/*/Secure Preferences*',
            '*/AppData/Local/Vivaldi/User Data/*/Secure Preferences*',
            '*/Library/Application Support/Vivaldi/*/Secure Preferences*',
            '*/.config/vivaldi/*/Secure Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Secure Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Secure Preferences*',
            '*/.config/opera/*/Secure Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Secure Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Secure Preferences*',
            '*/.config/opera/Secure Preferences*',
        ),
        "output_types": "standard",
        "artifact_icon": "puzzle",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 8 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json

from scripts.chromium.browser_profiles import (enum_label, profile_stores,
                                               row_tail, webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc

# extensions/common/mojom/manifest.mojom, lines 18 to 46,
# chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4.
_LOCATIONS = {
    0: 'INVALID_LOCATION', 1: 'INTERNAL', 2: 'EXTERNAL_PREF', 3: 'EXTERNAL_REGISTRY',
    4: 'UNPACKED', 5: 'COMPONENT', 6: 'EXTERNAL_PREF_DOWNLOAD', 7: 'EXTERNAL_POLICY_DOWNLOAD',
    8: 'COMMAND_LINE', 9: 'EXTERNAL_POLICY', 10: 'EXTERNAL_COMPONENT',
}
# Parts of the browser itself, which the browser does not list as extensions.
_COMPONENT_LOCATIONS = (5, 10)

# extensions/common/extension.h, lines 50 to 56, chromium 65.0.3325.181.
_STATES = {0: 'DISABLED', 1: 'ENABLED', 2: 'EXTERNAL_EXTENSION_UNINSTALLED'}

# extensions/browser/disable_reason.h, lines 26 to 72,
# chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4.
_DISABLE_REASONS = {
    1 << 0: 'USER_ACTION', 1 << 1: 'PERMISSIONS_INCREASE', 1 << 2: 'RELOAD',
    1 << 3: 'UNSUPPORTED_REQUIREMENT', 1 << 4: 'SIDELOAD_WIPEOUT',
    1 << 5: 'DEPRECATED_UNKNOWN_FROM_SYNC', 1 << 8: 'NOT_VERIFIED', 1 << 9: 'GREYLIST',
    1 << 10: 'CORRUPTED', 1 << 11: 'REMOTE_INSTALL', 1 << 13: 'EXTERNAL_EXTENSION',
    1 << 14: 'UPDATE_REQUIRED_BY_POLICY', 1 << 15: 'CUSTODIAN_APPROVAL_REQUIRED',
    1 << 16: 'BLOCKED_BY_POLICY', 1 << 19: 'REINSTALL', 1 << 20: 'NOT_ALLOWLISTED',
    1 << 21: 'DEPRECATED_NOT_ASH_KEEPLISTED', 1 << 22: 'PUBLISHED_IN_STORE_REQUIRED_BY_POLICY',
    1 << 23: 'UNSUPPORTED_MANIFEST_VERSION', 1 << 24: 'UNSUPPORTED_DEVELOPER_EXTENSION',
    1 << 25: 'UNKNOWN', 1 << 26: 'BLOCKED_BY_CLOUD_POLICY_CHECK',
    1 << 27: 'BY_ANOTHER_EXTENSION',
}


def _disable_reasons(value):
    """Name each disable reason in a stored bitmask (older releases) or list (newer)."""
    if value is None:
        return ''
    values = value if isinstance(value, list) else [value]
    names = []
    for item in values:
        try:
            bits = int(item)
        except (TypeError, ValueError):
            names.append(str(item))
            continue
        for bit in range(64):
            flag = 1 << bit
            if bits & flag:
                names.append(f'{_DISABLE_REASONS.get(flag, "unknown")} ({flag})')
    return ', '.join(names)


def _yes_no(value):
    if value is None:
        return ''
    return 'Yes' if value else 'No'


@artifact_processor
def chromiumExtensions(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Preferences', 'Secure Preferences'},
                                'Chromium Extensions'):
        try:
            with open(store.path, 'r', encoding='utf-8') as handle:
                document = json.load(handle)
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            logfunc(f'Chromium Extensions: could not read {store.relative}: {ex}')
            continue
        extensions = document.get('extensions') if isinstance(document, dict) else None
        settings = extensions.get('settings') if isinstance(extensions, dict) else None
        sources.append(store.path)
        if not isinstance(settings, dict):
            continue
        components = 0
        for extension_id in sorted(settings):
            entry = settings[extension_id]
            if not isinstance(entry, dict) or entry.get('location') is None:
                continue
            if entry.get('location') in _COMPONENT_LOCATIONS:
                components += 1
                continue
            manifest = entry.get('manifest') if isinstance(entry.get('manifest'), dict) else {}
            data_list.append((webkit_time(entry.get('install_time')),
                              webkit_time(entry.get('first_install_time')),
                              webkit_time(entry.get('last_update_time')), extension_id,
                              manifest.get('name', ''), manifest.get('version', ''),
                              enum_label(_LOCATIONS, entry.get('location')),
                              _yes_no(entry.get('from_webstore')),
                              _yes_no(entry.get('was_installed_by_default')),
                              enum_label(_STATES, entry.get('state')),
                              _disable_reasons(entry.get('disable_reasons')), store.name)
                             + row_tail(store))
        if components:
            logfunc(f'Chromium Extensions: {components} component entries in '
                    f'{store.relative} not reported')
    data_headers = (('Install Time', 'datetime'), ('First Install Time', 'datetime'),
                    ('Last Update Time', 'datetime'), 'Extension ID', 'Name', 'Version',
                    'Location', 'From Web Store', 'Installed By Default', 'State (as stored)',
                    'Disable Reasons', 'Preferences File', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)
