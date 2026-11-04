"""Windows USB device and HID input device history from the SYSTEM hive, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every device instance under Enum\\USB and Enum\\HID, where windowsUsbDevices.py
reads only Enum\\USBSTOR. Keyboards, mice, cameras and other non-storage devices appear
here and not in USBSTOR.
"""

__artifacts_v2__ = {
    "usbAllDevices": {
        "name": "USB Device Instances",
        "description": "USB device instances recorded under Enum\\USB in the SYSTEM hive, of any device "
                       "class: vendor and product ids, instance id, the name the bus driver reported "
                       "for it, the driver service, the HID input functions linked to it by its "
                       "ParentIdPrefix, and its first install, last connected and last removed times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-19",
        "last_update_date": "2026-10-19",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per instance sub-key under the VID_ keys of Enum\\USB in the control "
                 "set the Select key's Current value names (ControlSet001 when there is none). "
                 "Keys not named VID_ are not reported; on the tested hives those were ROOT_HUB, "
                 "ROOT_HUB20 and ROOT_HUB30, whose DeviceDesc begins \"USB Root Hub\" on every "
                 "tested hive, and the run log names each key left out. VID, PID and Interface "
                 "are parsed from the key name (VID_xxxx&PID_yyyy, with &MI_zz on interface "
                 "keys; on the tested hives every MI_ row shared its Container ID with a usbccgp "
                 "instance). Instance ID is the instance sub-key name as stored and is not "
                 "parsed. Bus-Reported Name is the device property "
                 "DEVPKEY_Device_BusReportedDeviceDesc, which Microsoft documents as the string "
                 "the bus driver reported for the device instance "
                 "(https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-busreporteddevicedesc), "
                 "property id 4 of GUID 540b947e-8b40-45bc-a8a2-6a0b894cbda2 as declared in "
                 "Wine's devpkey.h "
                 "(https://github.com/wine-mirror/wine/blob/7298a818b79446bae153b8d5aa27235ab3703bf9/include/devpkey.h#L84). "
                 "On the tested hives it differed from Device Description on every row that held "
                 "it (68 of 73) and was blank on 5. Device Description was a class name such as "
                 "USB Mass Storage Device or USB Composite Device on 70 rows and a vendor's "
                 "description on the 3 Bluetooth adapter rows. On the Parallels virtual machine "
                 "hives (windows11_arm_known_*) the camera instances carried vendor id 203A, the "
                 "id the virtual keyboard and mouse also carry, Device Description read USB "
                 "Video Device on those rows, and only Bus-Reported Name held a device-specific "
                 "string. Device Description and Manufacturer are the DeviceDesc and Mfg values; "
                 "a value of the form @file.inf,%key%;text is shown as the text after the first "
                 "semicolon; the prefix names an INF file and a string key in it, and the text "
                 "is not the bus-reported string. Friendly Name is the FriendlyName value. "
                 "Driver Service is the Service value as stored; observed values, each paired on "
                 "every tested row with one Device Description, are USBSTOR (USB Mass Storage "
                 "Device), UASPStor (USB Attached SCSI (UAS) Mass Storage Device), HidUsb (USB "
                 "Input Device), usbccgp (USB Composite Device), usbvideo (USB Video Device), "
                 "usbhub (Generic USB Hub) and BTHUSB (Bluetooth adapter descriptions). Parent "
                 "Device and Input Functions follow the ParentIdPrefix value Windows records on "
                 "an instance: on the tested hives a child instance's name begins with that "
                 "prefix followed by an ampersand. Parent Device names, as Enum key\\instance, "
                 "the Enum\\USB instance whose ParentIdPrefix begins this row's instance name, "
                 "root hubs included; it is blank when none does, as for instances named with a "
                 "serial and for 4 of the 20 ampersand-style names on the virtual machine hives. "
                 "Input Functions lists the Enum\\HID instances whose names begin with this row's "
                 "ParentIdPrefix, each as its driver service, or (no service) when the HID "
                 "instance recorded none, and description; on the tested hives every kbdhid "
                 "instance had the description HID Keyboard Device and every mouhid instance a "
                 "mouse or pointing-device description. A second read with python-registry "
                 "alone, without log replay, returned 114 instances across the nine tested hives "
                 "and agreed with this artifact on every date, bus-reported name and parent link "
                 "for each; the two USB instances present only after log replay (one each on "
                 "lonewolf_win10 and szechuan_win10) have no second read. Each of the 25 "
                 "Enum\\HID instances named with a VID matched exactly one Enum\\USB "
                 "ParentIdPrefix, with the same ContainerID as that parent. Container ID is the "
                 "ContainerID value as stored; the interfaces of one composite device shared it "
                 "on the tested hives, and 12 of the 73 tested rows held "
                 "{00000000-0000-0000-ffff-ffffffffffff}, among them every BTHUSB row and every "
                 "usbvideo row on the hives that are not virtual machines. First Install (UTC), "
                 "Last Connected (UTC) and Last Removed (UTC) are Windows FILETIMEs from the "
                 "instance's device properties under the property-key GUID "
                 "83da6326-97a6-4088-9453-a1923f573b29 at property ids 101, 102 and 103, "
                 "DEVPKEY_Device_FirstInstallDate, DEVPKEY_Device_LastArrivalDate and "
                 "DEVPKEY_Device_LastRemovalDate as declared in Wine's devpkey.h "
                 "(https://github.com/wine-mirror/wine/blob/7298a818b79446bae153b8d5aa27235ab3703bf9/include/devpkey.h#L106-L108). "
                 "A property is read only when it is stored with the FILETIME or string property "
                 "type its column expects. On the Windows 7 hive the property sub-keys have "
                 "eight hex digits (00000065) and keep the data in a further sub-key 00000000 "
                 "with Type and Data values; on the Windows 8.1, 10 and 11 hives they have four "
                 "digits (0065) and keep it in the sub-key's default value; both layouts are "
                 "read. Friendly Name held no value on any row of cfreds_leakage_win7, and Input "
                 "Functions none on pc_mus_001_win11 or hexordia_mvs2025_win11, whose USB "
                 "devices recorded no HID children. On the Windows 7 image (cfreds_leakage_win7) "
                 "the instances held First Install but no Last Connected or Last Removed "
                 "property, so those two columns are blank there. Each time is blank when the "
                 "instance holds no such property, holds it empty or with another type, or holds "
                 "a zero FILETIME. A row shows a device was attached to the computer, not who "
                 "attached it. Vendor and product ids are what the device presented and can be "
                 "changed to imitate another device "
                 "(https://blog.nviso.eu/2026/10/16/keystrokes-in-disguise-forensic-analysis-of-a-digispark-hid-device/). "
                 "Source File names the hive a row came from, because the declared paths also "
                 "match a SYSTEM hive under Windows.old. A dirty hive, one whose base block's "
                 "two sequence numbers differ, is read after the entries in its .LOG1 and .LOG2 "
                 "transaction logs that continue its sequence are applied, following Maxim "
                 "Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "When no log in the format Windows 8.1 and later write applies, a log in the older format used before Windows 8.1 is applied instead: the first of .LOG1 and .LOG2 whose base block is valid and holds the hive's last-written time has the pages its dirty vector marks written where the vector places them (https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L620-L677, https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L742). On the 16 hives of cfreds_leakage_win7 that carry such a log as .LOG1, each copied, made dirty and given overwritten bytes in every page its log marks for the test, this rebuilt each hive byte for byte, as rla 2026.10.1 did; none of the 54 dirty hives in the 17 corpus images surveyed carries one. A lone .LOG beside a hive is not read. A replay that would give a key an earlier last-written time than the hive already holds is not applied; the run log names each hive replayed and each dirty hive read "
                 "as it is. Mass-storage devices also appear in USB Storage Devices, which "
                 "reports their USBSTOR vendor, product and revision strings. Bluetooth-paired "
                 "devices (BTHPORT) are not read here.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "usb",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 6 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Enum\\USB key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 8 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 6 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 6 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 | 21 rows",
        },
    },
    "hidDevices": {
        "name": "HID Input Devices",
        "description": "Human interface device instances recorded under Enum\\HID in the SYSTEM hive "
                       "(keyboards, mice, touch pads and other input functions), with the driver "
                       "service, the USB device each belongs to where Windows recorded the link, and "
                       "first install, last connected and last removed times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-19",
        "last_update_date": "2026-10-19",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per instance sub-key under Enum\\HID in the control set the Select "
                 "key's Current value names (ControlSet001 when there is none). Device Key and "
                 "Instance ID are the key and sub-key names as stored and are not parsed. Driver "
                 "Service is the Service value as stored, blank for a function that recorded "
                 "none; on the tested hives every kbdhid instance had the description HID "
                 "Keyboard Device and every mouhid instance a mouse or pointing-device "
                 "description. A device that presents itself to Windows as a keyboard, as "
                 "keystroke-injection boards do "
                 "(https://blog.nviso.eu/2026/10/16/keystrokes-in-disguise-forensic-analysis-of-a-digispark-hid-device/), "
                 "would be recorded by what it presents, a keyboard function, whatever it is; no "
                 "such device is in the tested hives, and the keyboard rows were exercised with "
                 "a Parallels virtual USB keyboard (windows11_arm_known_20261010) and a keyboard "
                 "not linked to any USB instance (hexordia_mvs2025_win11, device key "
                 "ConvertedDevice). A row does not show what was typed. Device Description and "
                 "Manufacturer are the DeviceDesc and Mfg values, a value of the form "
                 "@file.inf,%key%;text shown as the text after the first semicolon. USB Parent "
                 "names, as Enum key\\instance, the Enum\\USB instance whose ParentIdPrefix value "
                 "begins this row's instance name followed by an ampersand; see USB Device "
                 "Instances for that device's ids, bus-reported name and times. It was blank on "
                 "18 of 43 tested rows, all with device keys not named with a VID, with device "
                 "keys such as ELAN2514, VEN_27C6 and ConvertedDevice and descriptions such as "
                 "HID-compliant touch pad, HID-compliant touch screen and HID Keyboard Device. "
                 "USB Parent held no value on any row of pc_mus_001_win11 or "
                 "hexordia_mvs2025_win11, whose Enum\\HID held only keys not named with a VID, "
                 "and Container ID held {00000000-0000-0000-ffff-ffffffffffff} on every row of "
                 "those two hives. No Enum\\HID instance on the tested hives is named with a "
                 "Bluetooth bus shape; devices enumerated under Enum\\BTH, present on three of "
                 "the hives, are not read here. Across the nine tested hives each of the 25 "
                 "instances named with a VID matched exactly one Enum\\USB ParentIdPrefix, with "
                 "the same ContainerID as that parent, and a second read with python-registry "
                 "alone, without log replay, agreed with this artifact on every date and parent "
                 "link of all 43 rows. Container ID is the ContainerID value as stored. First "
                 "Install (UTC), Last Connected (UTC) and Last Removed (UTC) are read exactly as "
                 "in USB Device Instances, from DEVPKEY_Device_FirstInstallDate, "
                 "DEVPKEY_Device_LastArrivalDate and DEVPKEY_Device_LastRemovalDate "
                 "(property-key GUID 83da6326-97a6-4088-9453-a1923f573b29, ids 101 to 103 as "
                 "declared in Wine's devpkey.h, "
                 "https://github.com/wine-mirror/wine/blob/7298a818b79446bae153b8d5aa27235ab3703bf9/include/devpkey.h#L106-L108), "
                 "in both the Windows 7 and the later layout; each is blank when the instance "
                 "holds no such property, holds it empty or with another type, or holds a zero "
                 "FILETIME, and Last Connected and Last Removed are blank on the Windows 7 "
                 "image. A row shows the input function was installed on the computer, not who "
                 "used it. Source File names the hive a row came from. Dirty hives are read "
                 "after their transaction logs are replayed, as described for USB Device "
                 "Instances.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "keyboard",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 8 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Enum\\HID key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 9 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 | 10 rows",
        },
    },
}

import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, current_control_set, filetime_bytes_utc,
                                      is_transaction_log, open_hive, open_key, value_of)

# DEVPKEY_Device_* property-key GUIDs and ids (Wine include/devpkey.h, pinned above).
_DATES_GUID = '{83da6326-97a6-4088-9453-a1923f573b29}'
_FIRST_INSTALL = 101
_LAST_ARRIVAL = 102
_LAST_REMOVAL = 103
_BUS_GUID = '{540b947e-8b40-45bc-a8a2-6a0b894cbda2}'
_BUS_REPORTED_DESC = 4

# DEVPROP_TYPE_FILETIME and DEVPROP_TYPE_STRING (Wine include/devpropdef.h).
_TYPE_FILETIME = 0x10
_TYPE_STRING = 0x12


def _text(value):
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if v)
    return str(value) if value else ''


def _display(value):
    """DeviceDesc and Mfg are stored as '@file.inf,%key%;text'; the text after the first
    semicolon is the name Windows shows. Anything else is returned as stored."""
    text = _text(value)
    if text.startswith('@') and ';' in text:
        return text.split(';', 1)[1]
    return text


def _stored_property(node):
    """(property type, raw bytes) from one property sub-key, in either layout seen:
    Windows 8 and later keep the data in the sub-key's default value, whose registry
    type carries the property type in its low 16 bits (python-registry reports only
    those bits); Windows 7 keeps a sub-key 00000000 holding a Type value and a Data
    value. (None, None) when neither is there."""
    for value in node.values():
        try:
            return value.value_type() & 0xFFFF, bytes(value.raw_data())
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    inner = _child(node, '00000000')
    if inner is not None:
        try:
            kind = struct.unpack('<I', bytes(inner.value('Type').raw_data())[:4])[0]
            return kind, bytes(inner.value('Data').raw_data())
        except (Registry.RegistryValueNotFoundException, struct.error):
            pass
    return None, None


def _property(instance, guid, prop_id, kind):
    """The raw bytes of one device property of the given type, matching the property
    sub-key by its number so that Windows 7's eight-digit names (00000065) and the later
    four-digit ones (0065) both resolve. None when the instance recorded no such property
    or recorded it with another type."""
    props = _child(instance, 'Properties')
    if props is None:
        return None
    for group in props.subkeys():
        if group.name().lower() != guid:
            continue
        for node in group.subkeys():
            try:
                if int(node.name(), 16) != prop_id:
                    continue
            except ValueError:
                continue
            stored_kind, raw = _stored_property(node)
            if stored_kind == kind:
                return raw
    return None


def _child(key, name):
    try:
        return key.subkey(name)
    except Registry.RegistryKeyNotFoundException:
        return None


def _date(instance, prop_id):
    return filetime_bytes_utc(_property(instance, _DATES_GUID, prop_id, _TYPE_FILETIME))


def _string_property(instance, guid, prop_id):
    raw = _property(instance, guid, prop_id, _TYPE_STRING)
    if not raw:
        return ''
    return raw.decode('utf-16-le', errors='replace').split('\x00', 1)[0]


def _ids(model_name):
    vid = pid = interface = ''
    for part in model_name.split('&'):
        upper = part.upper()
        if upper.startswith('VID_'):
            vid = part[4:]
        elif upper.startswith('PID_'):
            pid = part[4:]
        elif upper.startswith('MI_'):
            interface = part[3:]
    return vid, pid, interface


def _instances(branch_key):
    """(model key, instance key) for every instance under an Enum branch."""
    for model in (branch_key.subkeys() if branch_key else []):
        for instance in model.subkeys():
            yield model, instance


def _children_of(prefixes, instance_name):
    """The USB parents whose ParentIdPrefix, followed by an ampersand, begins
    instance_name."""
    lowered = instance_name.lower()
    return [label for prefix, label in prefixes if lowered.startswith(prefix + '&')]


def _read_system(path, context):
    """(control set, Enum\\USB key, Enum\\HID key) for one SYSTEM hive."""
    reg = open_hive(path, context)
    cs = current_control_set(reg)
    return cs, open_key(reg, cs + r'\Enum\USB'), open_key(reg, cs + r'\Enum\HID')


def _usb_prefixes(usb):
    """(lowercased ParentIdPrefix, 'model\\instance') for each Enum\\USB instance that
    records one, root hubs included, since they are parents of devices without serials."""
    prefixes = []
    for model, instance in _instances(usb):
        prefix = _text(value_of(instance, 'ParentIdPrefix'))
        if prefix:
            prefixes.append((prefix.lower(), f'{model.name()}\\{instance.name()}'))
    return prefixes


def _hives(context):
    return [str(f) for f in context.get_files_found() if not is_transaction_log(f)]


@artifact_processor
def usbAllDevices(context):
    data_headers = (('Last Connected (UTC)', 'datetime'), ('First Install (UTC)', 'datetime'),
                    ('Last Removed (UTC)', 'datetime'), 'VID', 'PID', 'Interface',
                    'Instance ID', 'Bus-Reported Name', 'Device Description', 'Manufacturer',
                    'Friendly Name', 'Driver Service', 'Input Functions', 'Parent Device',
                    'Container ID', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('USB Device Instances: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in _hives(context):
        relative = context.get_relative_path(path)
        try:
            _cs, usb, hid = _read_system(path, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'USB Device Instances: could not read {relative}: {exc}')
            continue
        prefixes = _usb_prefixes(usb)
        hid_children = [(instance.name().lower(),
                         f"{_text(value_of(instance, 'Service')) or '(no service)'} "
                         f"({_display(value_of(instance, 'DeviceDesc'))})")
                        for _model, instance in _instances(hid)]
        skipped = {}
        rows_here = 0
        for model, instance in _instances(usb):
            if not model.name().upper().startswith('VID_'):
                skipped[model.name()] = skipped.get(model.name(), 0) + 1
                continue
            vid, pid, interface = _ids(model.name())
            own_prefix = _text(value_of(instance, 'ParentIdPrefix')).lower()
            functions = ([label for name, label in hid_children
                          if own_prefix and name.startswith(own_prefix + '&')])
            parents = _children_of(prefixes, instance.name())
            data_list.append((
                _date(instance, _LAST_ARRIVAL), _date(instance, _FIRST_INSTALL),
                _date(instance, _LAST_REMOVAL), vid, pid, interface, instance.name(),
                _string_property(instance, _BUS_GUID, _BUS_REPORTED_DESC),
                _display(value_of(instance, 'DeviceDesc')),
                _display(value_of(instance, 'Mfg')),
                _text(value_of(instance, 'FriendlyName')),
                _text(value_of(instance, 'Service')),
                '; '.join(functions), '; '.join(parents),
                _text(value_of(instance, 'ContainerID')), relative))
            rows_here += 1
        if skipped:
            logfunc(f'USB Device Instances: {relative}: not reported, keys without a VID: '
                    + ', '.join(f'{name} ({count})' for name, count in sorted(skipped.items())))
        if usb is not None:
            sources.append(path)
        logfunc(f'USB Device Instances: {relative}: {rows_here} instances')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def hidDevices(context):
    data_headers = (('Last Connected (UTC)', 'datetime'), ('First Install (UTC)', 'datetime'),
                    ('Last Removed (UTC)', 'datetime'), 'Device Key', 'Instance ID',
                    'Driver Service', 'Device Description', 'Manufacturer', 'USB Parent',
                    'Container ID', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('HID Input Devices: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in _hives(context):
        relative = context.get_relative_path(path)
        try:
            _cs, usb, hid = _read_system(path, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'HID Input Devices: could not read {relative}: {exc}')
            continue
        prefixes = _usb_prefixes(usb)
        rows_here = 0
        for model, instance in _instances(hid):
            data_list.append((
                _date(instance, _LAST_ARRIVAL), _date(instance, _FIRST_INSTALL),
                _date(instance, _LAST_REMOVAL), model.name(), instance.name(),
                _text(value_of(instance, 'Service')),
                _display(value_of(instance, 'DeviceDesc')),
                _display(value_of(instance, 'Mfg')),
                '; '.join(_children_of(prefixes, instance.name())),
                _text(value_of(instance, 'ContainerID')), relative))
            rows_here += 1
        if hid is not None:
            sources.append(path)
        logfunc(f'HID Input Devices: {relative}: {rows_here} instances')
    return data_headers, data_list, '\n'.join(sources)
