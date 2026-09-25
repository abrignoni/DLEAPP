"""iOS devices paired with or connected to a Mac, and Bluetooth devices, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosLockdownPairings": {
        "name": "Paired iOS Devices (lockdown)",
        "description": "Pairing records in /private/var/db/lockdown, one per device identifier, "
                       "with the Wi-Fi MAC address, host ID and system BUID they store.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "Reads each plist in /private/var/db/lockdown and reports those that hold a HostID or"
                 " DeviceCertificate value, one row per file; Device Identifier is the file name "
                 "without .plist. libimobiledevice's usbmuxd, which reads the same folder, stores a "
                 "device's pairing record there as the device identifier followed by .plist and the "
                 "host's SystemBUID in SystemConfiguration.plist "
                 "(https://github.com/libimobiledevice/usbmuxd/blob/3ded00c9985a5108cfc7591a309f9a23d57a8cba/src/conf.c#L56-L67,"
                 " "
                 "https://github.com/libimobiledevice/usbmuxd/blob/3ded00c9985a5108cfc7591a309f9a23d57a8cba/src/conf.c#L128-L129"
                 " and "
                 "https://github.com/libimobiledevice/usbmuxd/blob/3ded00c9985a5108cfc7591a309f9a23d57a8cba/src/conf.c#L414-L456)."
                 " SystemConfiguration.plist, which on dleapp_macos_bigsur holds only a SystemBUID, is"
                 " not reported. A record's certificates, private keys and escrow bag are not "
                 "reported; Keys and Certificates Present names which of them it holds. On "
                 "dleapp_macos_bigsur the one record's file name ends with the key the same Mac's "
                 "com.apple.iPod.plist uses for its one device, compared without letter case.",
        "paths": ('*/private/var/db/lockdown/*.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 1 row",
        },
    },
    "macosIpodDevices": {
        "name": "iOS Devices (com.apple.iPod.plist)",
        "description": "Devices listed in each user's com.apple.iPod.plist, with the Connected "
                       "time, product type, serial number, IMEI, firmware and use count as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "Reads the Devices dictionary of each user's "
                 "~/Library/Preferences/com.apple.iPod.plist, one row per device. Connected is the "
                 "device's Connected date as stored; whether it records the first or the latest "
                 "connection is not established. Device ID is the device's ID value, or its key "
                 "in Devices when ID is missing or empty, and User is taken from the file's "
                 "path; the other columns except Source File are the stored values of the same "
                 "names. The conn:128:Last Connect value at the top level of the file is not "
                 "reported. "
                 "On dleapp_macos_bigsur the one device's ID equals its key in Devices and "
                 "matches the end of the pairing record's file name in /private/var/db/lockdown "
                 "when letter case is ignored. When a logical "
                 "extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a second copy byte-identical to the first is not "
                 "read again, and is counted in the run log."
                 " User is the folder after Users in the source path, or root under private/var/root,"
                 " and is blank when the input is one user's home folder whose path names no user, as"
                 " in an acquisition of a single user folder.",
        "paths": ('*/Library/Preferences/com.apple.iPod.plist',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 1 row",
        },
    },
    "macosBluetoothDevices": {
        "name": "Bluetooth Devices",
        "description": "Devices in the DeviceCache of /Library/Preferences/com.apple.Bluetooth.plist "
                       "and the addresses in its paired device lists, with names and IDs as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "Reads /Library/Preferences/com.apple.Bluetooth.plist: one row per address found in "
                 "DeviceCache or in the PairedDevices, BRPairedDevices, MagicCloudPairedDevices and "
                 "IDSPairedDevices lists, with Listed In naming the lists that hold it. Name, Display "
                 "Name, Vendor ID and Product ID are the DeviceCache values Name, displayName, "
                 "VendorID and ProductID as stored, and First Pairing is the FirstPairing value as "
                 "stored; its meaning is not established. On dleapp_macos_bigsur both cached devices "
                 "appear in PairedDevices, BRPairedDevices and MagicCloudPairedDevices, and Name and "
                 "Display Name are identical on both rows.",
        "paths": ('*/Library/Preferences/com.apple.Bluetooth.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "bluetooth",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 2 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources, user_from_path


def _text(value):
    return '' if value is None else str(value)


@artifact_processor
def macosLockdownPairings(context):
    data_headers = ('Device Identifier', 'Wi-Fi MAC Address', 'Host ID', 'System BUID',
                    'Keys and Certificates Present', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Paired iOS Devices')
    for path in paths:
        record = load_plist(path)
        if not isinstance(record, dict):
            logfunc(f'Paired iOS Devices: could not read {context.get_relative_path(path)}')
            continue
        read.append(path)
        if 'HostID' not in record and 'DeviceCertificate' not in record:
            continue
        secrets = sorted(key for key in ('DeviceCertificate', 'HostCertificate', 'HostPrivateKey',
                                         'RootCertificate', 'RootPrivateKey', 'EscrowBag')
                         if key in record)
        data_list.append((os.path.splitext(os.path.basename(path))[0],
                          _text(record.get('WiFiMACAddress')), _text(record.get('HostID')),
                          _text(record.get('SystemBUID')), ', '.join(secrets),
                          context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosIpodDevices(context):
    data_headers = (('Connected (UTC)', 'datetime'), 'Device Class', 'Product Type',
                    'Serial Number', 'IMEI', 'MEID', 'Firmware Version String', 'Build Version',
                    'Use Count', 'Device ID', 'Region Info', 'Family ID', 'User', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='iOS Devices')
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'iOS Devices: could not read {context.get_relative_path(path)}')
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        for key, device in (plist.get('Devices') or {}).items():
            if not isinstance(device, dict):
                continue
            data_list.append((as_utc(device.get('Connected')), _text(device.get('Device Class')),
                              _text(device.get('Product Type')), _text(device.get('Serial Number')),
                              _text(device.get('IMEI')), _text(device.get('MEID')),
                              _text(device.get('Firmware Version String')),
                              _text(device.get('Build Version')), _text(device.get('Use Count')),
                              _text(device.get('ID') or key), _text(device.get('Region Info')),
                              _text(device.get('Family ID')), user_from_path(relative), relative))
    return data_headers, data_list, '\n'.join(read)


_PAIRED_LISTS = ('PairedDevices', 'BRPairedDevices', 'MagicCloudPairedDevices', 'IDSPairedDevices')


@artifact_processor
def macosBluetoothDevices(context):
    data_headers = ('Address', 'Name', 'Display Name', 'Vendor ID', 'Product ID',
                    'Listed In', 'First Pairing (as stored)', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Bluetooth Devices')
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'Bluetooth Devices: could not read {context.get_relative_path(path)}')
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        cache = plist.get('DeviceCache') or {}
        listed = {}
        for list_name in _PAIRED_LISTS:
            for address in plist.get(list_name) or []:
                listed.setdefault(str(address), []).append(list_name)
        for address in sorted(set(cache) | set(listed)):
            device = cache.get(address) if isinstance(cache.get(address), dict) else {}
            first = device.get('FirstPairing')
            data_list.append((address, _text(device.get('Name')), _text(device.get('displayName')),
                              _text(device.get('VendorID')), _text(device.get('ProductID')),
                              ', '.join(listed.get(address, [])),
                              {True: 'Yes', False: 'No'}.get(first, _text(first)), relative))
    return data_headers, data_list, '\n'.join(read)
