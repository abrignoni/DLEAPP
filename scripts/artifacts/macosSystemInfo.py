"""macOS system information from SystemVersion.plist, the SystemConfiguration preferences and
the system-wide global and login window preferences, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSystemInfo": {
        "name": "macOS System Information",
        "description": "Operating system name, version and build, computer and host names, the "
                       "system locale, languages and country, the last selected time zone city, "
                       "and the login window's last user and guest settings, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "System Information (macOS)",
        "notes": "Reads SystemVersion.plist, the SystemConfiguration preferences.plist, and the "
                 ".GlobalPreferences.plist and com.apple.loginwindow.plist in a volume's own "
                 "Library/Preferences folder. Copies in a user's, the root account's, a service's or a "
                 "template's Library/Preferences are left out, as is any value a file does not hold. Each "
                 "row names its Plist Key and the file it came from, so a copy on another volume gives "
                 "rows of its own: on dleapp_macos_bigsur the Preboot volume held copies of "
                 "SystemVersion.plist, preferences.plist and com.apple.loginwindow.plist that gave 8 of "
                 "the 20 rows, each with the same value as the System or Data volume's copy. A logical "
                 "extraction's byte-identical copy under System/Volumes/Data is read once. Product Name, "
                 "Product Version, Product User Visible Version and Product Build Version are the "
                 "ProductName, ProductVersion, ProductUserVisibleVersion and ProductBuildVersion values, "
                 "the keys CoreFoundation defines for the file it reads at "
                 "/System/Library/CoreServices/SystemVersion.plist "
                 "(https://github.com/apple-oss-distributions/CF/blob/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3/CFUtilities.c#L310-L315 "
                 "and "
                 "https://github.com/apple-oss-distributions/CF/blob/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3/CFUtilities.c#L324-L329). "
                 "Computer Name and Host Name are the ComputerName and HostName values under "
                 "System/System, and Local Host Name the LocalHostName value under "
                 "System/Network/HostNames, where Apple's configd reads and writes them in its default "
                 "preferences file, Library/Preferences/SystemConfiguration/preferences.plist "
                 "(https://github.com/apple-oss-distributions/configd/blob/585b7f2fca293f4642d21d15c5daf187f63c4796/SystemConfiguration.fproj/SCPreferencesInternal.h#L47-L54, "
                 "with "
                 "https://github.com/apple-oss-distributions/configd/blob/585b7f2fca293f4642d21d15c5daf187f63c4796/SystemConfiguration.fproj/SCDHostName.c#L283-L300, "
                 "https://github.com/apple-oss-distributions/configd/blob/585b7f2fca293f4642d21d15c5daf187f63c4796/SystemConfiguration.fproj/SCDHostName.c#L345-L364 "
                 "and "
                 "https://github.com/apple-oss-distributions/configd/blob/585b7f2fca293f4642d21d15c5daf187f63c4796/SystemConfiguration.fproj/SCDHostName.c#L584-L602). "
                 "Locale, Languages and Country are the AppleLocale, AppleLanguages and Country values of "
                 "the system-wide .GlobalPreferences.plist, as stored, with Languages in its stored order. "
                 "Last Selected City (as stored) is the com.apple.TimeZonePref.Last_Selected_City array "
                 "joined in its stored order. A GitHub code search of the apple and "
                 "apple-oss-distributions organizations found no mention of that key; on "
                 "dleapp_macos_bigsur its fourth item was the time zone name America/New_York and its last "
                 "item the text DEPRECATED IN 10.6, so it is not presented as the time zone in force. Last "
                 "User Name, Automatic Login User and Guest Enabled are the lastUserName, autoLoginUser "
                 "and GuestEnabled values of the system-wide com.apple.loginwindow.plist, as stored. "
                 "Apple's login window payload documentation does not list these keys "
                 "(https://github.com/apple/device-management/blob/09f249a06e7e3289930bf6d05f38fb562f748ebf/mdm/profiles/com.apple.loginwindow.yaml), "
                 "so what sets each one is not established here. Booleans are shown as true or false, and "
                 "a file that cannot be read as a plist is logged and gives no rows.",
        "paths": (
            '*/System/Library/CoreServices/SystemVersion.plist',
            '*/Library/Preferences/SystemConfiguration/preferences.plist',
            '*/Library/Preferences/.GlobalPreferences.plist',
            '*/Library/Preferences/com.apple.loginwindow.plist',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 20 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import load_plist, unique_sources

_VERSION_KEYS = (
    ('ProductName', 'Product Name'),
    ('ProductVersion', 'Product Version'),
    ('ProductUserVisibleVersion', 'Product User Visible Version'),
    ('ProductBuildVersion', 'Product Build Version'),
)
_GLOBAL_KEYS = (
    ('AppleLocale', 'Locale'),
    ('AppleLanguages', 'Languages'),
    ('Country', 'Country'),
)
_LOGIN_KEYS = (
    ('lastUserName', 'Last User Name'),
    ('autoLoginUser', 'Automatic Login User'),
    ('GuestEnabled', 'Guest Enabled'),
)
_LAST_CITY = 'com.apple.TimeZonePref.Last_Selected_City'


def _text(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, list):
        return ', '.join(_text(item) for item in value)
    return '' if value is None else str(value)


def _system_scope(relative):
    """True for a volume's own Library/Preferences, not a user, service or template copy.

    Above a system-wide preferences folder there is only the volume, so any Users, var,
    Library or Containers folder there marks a copy kept for an account or a template
    (such as /Library/User Template/<language>.lproj/Library/Preferences).
    """
    head = relative.replace('\\', '/').split('Library/Preferences/', 1)[0].lower()
    parts = [part for part in head.split('/') if part]
    return not any(part in ('users', 'var', 'library', 'containers') for part in parts)


def _rows(path, relative):
    """(property, value, key) rows the file holds, by its name."""
    data = load_plist(path)
    if not isinstance(data, dict):
        return None
    name = os.path.basename(path)
    rows = []
    if name == 'SystemVersion.plist':
        for key, label in _VERSION_KEYS:
            rows.append((label, data.get(key), key))
    elif name == 'preferences.plist':
        system = data.get('System') if isinstance(data.get('System'), dict) else {}
        names = system.get('System') if isinstance(system.get('System'), dict) else {}
        network = system.get('Network') if isinstance(system.get('Network'), dict) else {}
        hosts = network.get('HostNames') if isinstance(network.get('HostNames'), dict) else {}
        rows.append(('Computer Name', names.get('ComputerName'), 'System/System/ComputerName'))
        rows.append(('Host Name', names.get('HostName'), 'System/System/HostName'))
        rows.append(('Local Host Name', hosts.get('LocalHostName'),
                     'System/Network/HostNames/LocalHostName'))
    elif name == '.GlobalPreferences.plist':
        if not _system_scope(relative):
            return []
        for key, label in _GLOBAL_KEYS:
            rows.append((label, data.get(key), key))
        city = data.get(_LAST_CITY)
        if isinstance(city, list):
            rows.append(('Last Selected City (as stored)', city, _LAST_CITY))
    elif name == 'com.apple.loginwindow.plist':
        if not _system_scope(relative):
            return []
        for key, label in _LOGIN_KEYS:
            rows.append((label, data.get(key), key))
    return [(label, _text(value), key) for label, value, key in rows
            if value not in (None, '', [], {})]


@artifact_processor
def macosSystemInfo(context):
    data_headers = ('Property', 'Value', 'Plist Key', 'Source File')
    data_list = []
    sources = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='macOS System Information')
    for path in paths:
        relative = context.get_relative_path(path)
        rows = _rows(path, relative)
        if rows is None:
            logfunc(f'macOS System Information: could not read {relative}')
            continue
        if rows:
            sources.append(path)
        for label, value, key in rows:
            data_list.append((label, value, key, relative))
    logfunc(f'macOS System Information: {len(data_list)} value(s) from {len(sources)} file(s).')
    return data_headers, data_list, '\n'.join(sources)
