"""Software installs recorded in /Library/Receipts/InstallHistory.plist, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosInstallHistory": {
        "name": "Install History",
        "description": "Entries in /Library/Receipts/InstallHistory.plist, with the date, "
                       "display name and version, installing process and package identifiers "
                       "as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Installed Software (macOS)",
        "notes": "Reads the array in /Library/Receipts/InstallHistory.plist, one row per entry; Date "
                 "is the entry's date value. On dleapp_macos_bigsur the 16 entries run from 2020-12-02"
                 " to 2021-02-15: 15 name softwareupdated as the process and one Installer, 13 carry "
                 "package identifiers and 12 a content type. On the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) the 21 entries run from "
                 "2025-11-20 to 2025-12-24, 10 of them from appstoreagent. When a logical extraction "
                 "holds the file under Library/Receipts/ and again under "
                 "System/Volumes/Data/Library/Receipts/, a second copy byte-identical to the "
                 "first is not read again, and is counted in the run log.",
        "paths": ('*/Library/Receipts/InstallHistory.plist',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "package",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 16 rows",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources


def _text(value):
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    return '' if value is None else str(value)


@artifact_processor
def macosInstallHistory(context):
    data_headers = (('Date (UTC)', 'datetime'), 'Display Name', 'Display Version',
                    'Process Name', 'Content Type', 'Package Identifiers', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Install History')
    for path in paths:
        history = load_plist(path)
        if not isinstance(history, list):
            logfunc(f'Install History: could not read {context.get_relative_path(path)}')
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        for entry in history:
            if isinstance(entry, dict):
                data_list.append((as_utc(entry.get('date')), _text(entry.get('displayName')),
                                  _text(entry.get('displayVersion')), _text(entry.get('processName')),
                                  _text(entry.get('contentType')),
                                  _text(entry.get('packageIdentifiers')), relative))
    return data_headers, data_list, '\n'.join(read)
