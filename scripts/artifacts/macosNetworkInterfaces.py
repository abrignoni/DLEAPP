__artifacts_v2__ = {
    "macosNetworkInterfaces": {
        "name": "macOS Network Interfaces",
        "description": "Network interfaces recorded in NetworkInterfaces.plist on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": (
            'One row per entry of the Interfaces array of '
            'Library/Preferences/SystemConfiguration/NetworkInterfaces.plist, values as stored. BSD Name is the'
            ' BSD Name value, Interface Name is UserDefinedName inside SCNetworkInterfaceInfo, Interface Type '
            'is SCNetworkInterfaceType, MAC Address is the IOMACAddress bytes as colon-separated hex, Active, '
            'Built In and Hidden are Active, IOBuiltin and HiddenInterface, and IO Interface Type, IO Interface'
            ' Unit and IO Path Match are the keys of those names. Other Interface Info holds the other keys of '
            "SCNetworkInterfaceInfo and Other Values the other keys of the entry, as JSON. Model is the file's "
            "top-level Model value. The key names are the file's own and what each means is not sourced here. "
            'When an entry is written and whether it outlives a removed interface is not established. Model '
            'held one value on every row of each of the five tested images. IO Interface Type held one value on'
            ' every row of all five images (6). Other Values held one value on every row of four images, the '
            'IOInterfaceNamePrefix key alone. Active held one value on every row of three images, Interface '
            'Type held one value on every row of the Big Sur E01 image, and Hidden and Other Interface Info '
            'each held no value on any row of two images. A copy of the file under a Preboot volume folder is '
            'read as a separate file and reported with its own Source File. Four of the five tested images held'
            ' one. On each of the four it was byte-identical to the main copy, so every interface is listed '
            'twice there. The top-level __VERSION__ value is not reported. When a logical extraction holds the '
            'same file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy'
            ' is not read again and the run log counts it. When the views hold different bytes but give the '
            'same row, the row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Preferences/SystemConfiguration/NetworkInterfaces.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "share-2",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 16 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 4 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 6 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 12 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 14 rows",
        },
    },
}

import json
import os

from scripts.ilapfuncs import artifact_processor
from scripts.macos_plists import fold_view_rows, load_plist, unique_sources

_SHOWN = ('BSD Name', 'SCNetworkInterfaceInfo', 'SCNetworkInterfaceType', 'IOMACAddress', 'Active', 'IOBuiltin',
          'HiddenInterface', 'IOInterfaceType', 'IOInterfaceUnit', 'IOPathMatch')


def _flag(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return '' if value is None else str(value)


def _json(value):
    def default(item):
        if isinstance(item, (bytes, bytearray)):
            return bytes(item).hex()
        return str(item)
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True, default=default)


def _mac(value):
    if isinstance(value, (bytes, bytearray)):
        return ':'.join(f'{byte:02x}' for byte in value)
    return '' if value is None else str(value)


@artifact_processor
def macosNetworkInterfaces(context):
    data_headers = ('BSD Name', 'Interface Name', 'Interface Type', 'MAC Address', 'Active', 'Built In', 'Hidden',
                    'IO Interface Type', 'IO Interface Unit', 'IO Path Match', 'Other Interface Info',
                    'Other Values', 'Model', 'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'NetworkInterfaces.plist']
    paths, _skipped = unique_sources(context, found, label='macOS Network Interfaces')
    rows, read = [], []
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict) or not isinstance(plist.get('Interfaces'), list):
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        model = plist.get('Model')
        model = model if isinstance(model, str) else ''
        for entry in plist['Interfaces']:
            if not isinstance(entry, dict):
                continue
            info = entry.get('SCNetworkInterfaceInfo')
            info = info if isinstance(info, dict) else {}
            name = info.get('UserDefinedName')
            other_info = {key: value for key, value in info.items() if key != 'UserDefinedName'}
            other = {key: value for key, value in entry.items() if key not in _SHOWN}
            rows.append((
                _flag(entry.get('BSD Name')),
                name if isinstance(name, str) else '',
                _flag(entry.get('SCNetworkInterfaceType')),
                _mac(entry.get('IOMACAddress')),
                _flag(entry.get('Active')),
                _flag(entry.get('IOBuiltin')),
                _flag(entry.get('HiddenInterface')),
                _flag(entry.get('IOInterfaceType')),
                _flag(entry.get('IOInterfaceUnit')),
                _flag(entry.get('IOPathMatch')),
                _json(other_info) if other_info else '',
                _json(other) if other else '',
                model,
                relative,
            ))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
