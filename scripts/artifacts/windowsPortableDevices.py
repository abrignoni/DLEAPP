"""Windows Portable Devices entries from the SOFTWARE and SYSTEM hives, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "portableDevices": {
        "name": "Portable Devices",
        "description": "Subkeys of Windows Portable Devices\\Devices in the SOFTWARE hive and "
                       "Enum\\SWD\\WPDBUSENUM in the SYSTEM hive, with each device's "
                       "FriendlyName and DeviceDesc values and key last-written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the subkeys of Microsoft\\Windows Portable Devices\\Devices in the SOFTWARE hive"
                 " and of Enum\\SWD\\WPDBUSENUM in the SYSTEM hive's control set named by the Select "
                 "key's Current value (ControlSet001 when there is none), with each subkey's "
                 "FriendlyName and DeviceDesc values as stored. Device Key is the subkey name as "
                 "stored and is not parsed. Registry Location names the key a row came from. Key Last "
                 "Written is when the subkey was last written, which is not established as when a "
                 "device was connected.",
        "paths": (
            '*/Windows/System32/config/SOFTWARE',
            '*/Windows/System32/config/SYSTEM',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (Devices key has no subkeys and there is no WPDBUSENUM key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, current_control_set, found_hives,
                                      key_written_utc, open_key, value_of)

_DEVICES = r'Microsoft\Windows Portable Devices\Devices'


def _text(value):
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if v)
    return str(value) if value else ''


@artifact_processor
def portableDevices(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Friendly Name', 'Device Key',
                    'Device Description', 'Registry Location', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Portable Devices: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'SOFTWARE', 'SYSTEM'):
        relative = context.get_relative_path(path)
        try:
            reg = Registry.Registry(path)
            if os.path.basename(path).upper() == 'SOFTWARE':
                where = 'SOFTWARE\\' + _DEVICES
                root = open_key(reg, _DEVICES)
            else:
                cs = current_control_set(reg)
                where = f'SYSTEM\\{cs}\\Enum\\SWD\\WPDBUSENUM'
                root = open_key(reg, cs + r'\Enum\SWD\WPDBUSENUM')
            for device in (root.subkeys() if root else []):
                data_list.append((key_written_utc(device),
                                  _text(value_of(device, 'FriendlyName')),
                                  device.name(),
                                  _text(value_of(device, 'DeviceDesc')),
                                  where, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Portable Devices: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
