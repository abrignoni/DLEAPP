"""Login items and background items managed by BackgroundTaskManagement, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosBackgroundItems": {
        "name": "Login and Background Items (BTM)",
        "description": "Items in /private/var/db/com.apple.backgroundtaskmanagement/"
                       "BackgroundItems-v*.btm, per user identifier, with name, developer, URL, "
                       "executable, arguments, bundle and team identifiers, and the stored type "
                       "and disposition values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "notes": "Reads BackgroundItems-v*.btm in /private/var/db/com.apple.backgroundtaskmanagement, "
                 "an NSKeyedArchiver archive whose store object lists items per user identifier; each "
                 "item is one row, and User Identifier is the key it is listed under, as stored. Type "
                 "and Disposition decode the stored bit fields as Objective-See's DumpBTM does: type "
                 "0x2 app, 0x4 login item, 0x8 agent, 0x10 daemon, 0x20 developer, 0x10000 legacy and "
                 "0x80000 curated; disposition 0x1 enabled, 0x2 allowed, 0x4 hidden and 0x8 notified, "
                 "with the opposite word when a bit is clear. Other bits are shown as not decoded, and"
                 " the raw values are kept in the as stored columns. Those meanings are DumpBTM's and "
                 "were not tested here. Modification Date and Executable Modification Date are "
                 "modificationDate and executableModificationDate read as seconds since 00:00:00 UTC "
                 "on 1 January 2001, and a value of 0 or less is left empty. On the public "
                 "MacBook Pro logical"
                 " extraction (macOS 15.4, not a registered corpus key) the file holds 7 items under 3"
                 " user identifiers; read from 2001 their modification dates fall between 2025-05-23 "
                 "and 2025-12-10, before the 20251225 date in the extraction's file name, while read "
                 "from 1970 they would fall in 1994. One item has type 0x800, a bit DumpBTM does not "
                 "name, and 5 have an executableModificationDate of 0. dleapp_macos_bigsur has no "
                 "BackgroundItems file. When a logical extraction holds the file under "
                 "private/var/db/ and again under System/Volumes/Data/private/var/db/, a second "
                 "copy byte-identical to the first is not read again, and is counted in the run "
                 "log. Reference: Patrick Wardle (Objective-See), DumpBTM, "
                 "dumpBTM.m, "
                 "https://github.com/objective-see/DumpBTM/blob/19ba38005242afe07ba6e66c29f65663fa9b9917/library/code/dumpBTM.m#L388-L428"
                 " and "
                 "https://github.com/objective-see/DumpBTM/blob/19ba38005242afe07ba6e66c29f65663fa9b9917/library/code/dumpBTM.m#L476-L518.",
        "paths": ('*/private/var/db/com.apple.backgroundtaskmanagement/BackgroundItems-v*.btm',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "rocket",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no BackgroundItems file)",
        },
    },
}

import json

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import load_plist, mac_absolute_utc, resolve_keyed_archive, unique_sources

_TYPE_BITS = ((0x2, 'app'), (0x4, 'login item'), (0x8, 'agent'), (0x10, 'daemon'),
              (0x20, 'developer'), (0x10000, 'legacy'), (0x80000, 'curated'))
_DISPOSITION_BITS = ((0x1, 'enabled', 'disabled'), (0x2, 'allowed', 'disallowed'),
                     (0x4, 'hidden', 'visible'), (0x8, 'notified', 'not notified'))


def _text(value):
    if value is None:
        return ''
    if isinstance(value, list):
        return json.dumps(value)
    return str(value)


def _type_text(value):
    if not isinstance(value, int):
        return ''
    names = [name for bit, name in _TYPE_BITS if value & bit]
    rest = value & ~sum(bit for bit, _name in _TYPE_BITS)
    if rest:
        names.append(f'{rest:#x} not decoded')
    return ', '.join(names)


def _disposition_text(value):
    if not isinstance(value, int):
        return ''
    names = [on if value & bit else off for bit, on, off in _DISPOSITION_BITS]
    rest = value & ~0xF
    if rest:
        names.append(f'{rest:#x} not decoded')
    return ', '.join(names)


def _when(seconds):
    return mac_absolute_utc(seconds) if isinstance(seconds, (int, float)) and seconds > 0 else ''


@artifact_processor
def macosBackgroundItems(context):
    data_headers = (('Modification Date (UTC)', 'datetime'),
                    ('Executable Modification Date (UTC)', 'datetime'), 'Name', 'Developer Name',
                    'Type', 'Type (as stored)', 'Disposition', 'Disposition (as stored)', 'URL',
                    'Executable Path', 'Program Arguments', 'Bundle ID', 'Team ID', 'Identifier',
                    'Container', 'Associated Bundle IDs', 'User Identifier', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Login and Background Items')
    for path in paths:
        relative = context.get_relative_path(path)
        store = resolve_keyed_archive(load_plist(path), 'store')
        if not isinstance(store, dict):
            logfunc(f'Login and Background Items: could not read {relative}')
            continue
        read.append(path)
        for user, items in sorted((store.get('itemsByUserIdentifier') or {}).items()):
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                kind, disposition = item.get('type'), item.get('disposition')
                data_list.append((
                    _when(item.get('modificationDate')), _when(item.get('executableModificationDate')),
                    _text(item.get('name')), _text(item.get('developerName')), _type_text(kind),
                    f'{kind:#x}' if isinstance(kind, int) else _text(kind),
                    _disposition_text(disposition),
                    f'{disposition:#x}' if isinstance(disposition, int) else _text(disposition),
                    _text(item.get('url')), _text(item.get('executablePath')),
                    _text(item.get('programArguments')), _text(item.get('bundleIdentifier')),
                    _text(item.get('teamIdentifier')), _text(item.get('identifier')),
                    _text(item.get('container')), _text(item.get('associatedBundleIdentifiers')),
                    _text(user), relative))
    return data_headers, data_list, '\n'.join(read)
