"""Application Firewall settings from com.apple.alf.plist on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosApplicationFirewall": {
        "name": "Application Firewall",
        "description": "Values stored in the macOS Application Firewall's settings file, "
                       "com.apple.alf.plist, one row per value with the path of keys that leads to "
                       "it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads the Application Firewall settings file "
                 "/Library/Preferences/com.apple.alf.plist, and a file of the same name in any "
                 "other Library/Preferences folder of the extraction, and reports one row per "
                 "value in the order the file stores them. The NIST macOS Security Compliance "
                 "Project's rules for macOS 15, 26 and 27 enable the macOS Application Firewall by "
                 "writing globalstate as the integer 1 to this file, and stealth mode by writing "
                 "stealthenabled as the integer 1 "
                 "(https://github.com/usnistgov/macos_security/blob/ab0ad0ef17fcbdffda1e0e00a11e5c40d51cc401/src/mscp/data/rules/system_settings/system_settings_firewall_enable.yaml#L69-L101, "
                 "https://github.com/usnistgov/macos_security/blob/ab0ad0ef17fcbdffda1e0e00a11e5c40d51cc401/src/mscp/data/rules/system_settings/system_settings_firewall_stealth_mode_enable.yaml#L58-L84). "
                 "The corresponding rules on the project's big_sur branch check and set those two "
                 "settings with socketfilterfw rather than this file "
                 "(https://github.com/usnistgov/macos_security/blob/1323b76a7a82b1a88c8ead359fbf02af8e967eba/rules/sysprefs/sysprefs_firewall_enable.yaml#L7-L15, "
                 "https://github.com/usnistgov/macos_security/blob/1323b76a7a82b1a88c8ead359fbf02af8e967eba/rules/sysprefs/sysprefs_firewall_stealth_mode_enable.yaml#L12-L20). "
                 "The meaning of the other keys and of other values is not established here, so "
                 "values are reported as stored and none is interpreted. Velociraptor's exchange "
                 "artifact MacOS.Network.ApplicationLayerFirewall, by Wes Lambert, reads the same "
                 "file "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Network.ApplicationLayerFirewall.yaml#L13-L15). "
                 "Setting is the path of keys down to a value, with a 1-based position after an "
                 "array's name, as in exceptions[2]/path; Value is the value as text, with a "
                 "boolean as Yes or No, binary data as hex and a date in UTC; and Settings File "
                 "names the file a row came from. An empty array or dictionary is reported as one "
                 "row with a blank Value. Two copies whose paths differ only by a leading "
                 "System/Volumes/Data and whose bytes are identical are read once, and a file that "
                 "cannot be read as a plist, or whose top level is not a dictionary, is logged and "
                 "skipped. dleapp_macos_bigsur held one such file, under Macintosh HD - Data, so "
                 "Settings File named that file on every row. The file gave 54 rows, the same as "
                 "an independent count of its 53 values and one empty array (applications), and "
                 "held integers and text only, so no boolean, data or date value was tested. The "
                 "public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) "
                 "does not include the /Library/Preferences folder, so no file from a later macOS "
                 "version was tested.",
        "paths": ('*/Library/Preferences/com.apple.alf.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield-lock",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 54 rows",
        },
    },
}

from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources


def stored_text(value):
    """A plist scalar as report text: Yes or No for a boolean, hex for data, a date in UTC."""
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, datetime):
        return str(as_utc(value))
    return '' if value is None else str(value)


def flatten(value, path=''):
    """(setting path, value) for every scalar in a plist value.

    Dictionary keys join the path with '/', and an array member carries its 1-based position,
    as in exceptions[2]/path. An empty dictionary or array gives one row with a blank value.
    """
    if isinstance(value, dict):
        if not value:
            yield path, ''
        for key, item in value.items():
            yield from flatten(item, f'{path}/{key}' if path else str(key))
    elif isinstance(value, list):
        if not value:
            yield path, ''
        for index, item in enumerate(value, 1):
            yield from flatten(item, f'{path}[{index}]')
    else:
        yield path, stored_text(value)


@artifact_processor
def macosApplicationFirewall(context):
    data_headers = ('Setting', 'Value', 'Settings File')
    data_list, sources = [], []
    kept, _skipped = unique_sources(context, context.get_files_found(), label='Application Firewall')
    for path in kept:
        relative = context.get_relative_path(path)
        settings = load_plist(path)
        if not isinstance(settings, dict):
            logfunc(f'Application Firewall: {relative} is not a plist dictionary')
            continue
        data_list.extend(row + (relative,) for row in flatten(settings))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
