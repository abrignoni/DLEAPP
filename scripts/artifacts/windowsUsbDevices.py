"""Windows USB storage device history parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange and RegRipper artifacts that read the same
USBSTOR keys; the implementation reads the SYSTEM hive keys directly and is not
ported from those artifacts.
"""

import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import is_transaction_log, open_hive

# Windows records each USB mass-storage device it has seen under
# CurrentControlSet\Enum\USBSTOR in the SYSTEM hive: a model key
# (Disk&Ven_x&Prod_y&Rev_z) with an instance (serial) sub-key per device. Each
# instance's Properties hold the device property FILETIMEs for when it was first
# installed, last connected (arrived) and last removed.
_PROP_SET = "{83da6326-97a6-4088-9453-a1923f573b29}"
# DEVPKEY_Device_* property ids under that property-key GUID.
_FIRST_INSTALL = "0065"   # DEVPKEY_Device_FirstInstallDate
_LAST_ARRIVAL = "0066"    # DEVPKEY_Device_LastArrivalDate
_LAST_REMOVAL = "0067"    # DEVPKEY_Device_LastRemovalDate
_TYPE_FILETIME = 0x10     # DEVPROP_TYPE_FILETIME

__artifacts_v2__ = {
    "usbDevices": {
        "name": "USB Storage Devices",
        "description": "USB mass-storage devices recorded in the Windows "
                       "USBSTOR key: each device's friendly name, vendor, "
                       "product, revision and serial, with the times it was "
                       "first installed, last connected and last removed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-10-19",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from Enum\\USBSTOR in the SYSTEM hive, in the control set named by the "
                 "hive's Select\\Current value (ControlSet001 when that value cannot be read), "
                 "named in the report's located-at line, one row per device instance. Vendor, "
                 "Product and Revision are parsed from the Ven_, Prod_ and Rev_ segments of the "
                 "model key name (for example Disk&Ven_x&Prod_y&Rev_z; the first segment was "
                 "Disk, CdRom or Other in the tested hives), with underscores shown as spaces. "
                 "Serial is the instance sub-key name as stored; when a device reports no "
                 "system-unique serial, Windows modifies the instance name to make it unique "
                 "(Microsoft, Instance IDs, "
                 "https://learn.microsoft.com/en-us/windows-hardware/drivers/install/instance-ids), "
                 "so such a name is not the manufacturer's serial. Friendly Name is the device's "
                 "FriendlyName value, blank when the instance holds none. First Install (UTC), "
                 "Last Connected (UTC) and Last Removed (UTC) are Windows FILETIMEs read from "
                 "the instance's device properties under the property-key GUID "
                 "83da6326-97a6-4088-9453-a1923f573b29 at property ids 0065 "
                 "(DEVPKEY_Device_FirstInstallDate), 0066 (DEVPKEY_Device_LastArrivalDate) and "
                 "0067 (DEVPKEY_Device_LastRemovalDate), read only when stored with the FILETIME "
                 "property type. On the Windows 7 hive (cfreds_leakage_win7) these property "
                 "sub-keys have eight hex digits (00000065) and keep the data in a further "
                 "sub-key 00000000 with Type and Data values; on the Windows 10 and 11 hives "
                 "they have four digits (0065) and keep it in the sub-key's default value; both "
                 "layouts are read. The Windows 8.1 hive, read without its transaction log, "
                 "holds no USBSTOR key, so its layout was not exercised here. The Windows 7 "
                 "instances held First Install but no Last Connected or Last Removed property, "
                 "so those two columns are blank there. Each time is blank when the instance "
                 "holds no such property, holds it empty or with another type, or holds a zero "
                 "FILETIME. USBSTOR covers USB mass storage (Microsoft, USB device class drivers "
                 "included in Windows, "
                 "https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/supported-usb-classes); "
                 "other USB devices are reported by USB Device Instances and HID Input Devices. "
                 "A record shows the device was connected to the computer, not who connected it. "
                 "Reading the hive requires python-registry. A dirty hive, one whose base "
                 "block's two sequence numbers differ, is read after the entries in its .LOG1 "
                 "and .LOG2 transaction logs that continue its sequence are applied, following "
                 "Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither "
                 "is a replay that would give a key an earlier last-written time than the hive "
                 "already holds, a check added here beyond the specification; the run log names "
                 "each hive replayed, with the sequence numbers applied, and each dirty hive "
                 "read as it is, with the reason. Property names and type: Microsoft "
                 "DEVPKEY_Device_FirstInstallDate, "
                 "https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-firstinstalldate. "
                 "Numeric ids and GUID as declared in Wine's devpkey.h, "
                 "https://github.com/wine-mirror/wine/blob/7298a818b79446bae153b8d5aa27235ab3703bf9/include/devpkey.h#L106-L108; "
                 "FILETIME type 0x10 as declared in Wine's devpropdef.h, "
                 "https://github.com/wine-mirror/wine/blob/7298a818b79446bae153b8d5aa27235ab3703bf9/include/devpropdef.h#L44.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no USBSTOR key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 4 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no USBSTOR key in the hive as read; its dirty-hive log was not applied, see the run log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 | 5 rows",
        },
    },
}


def _filetime_utc(value):
    if not value:
        return ''
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError):
        return ''


def _current_set(reg):
    try:
        current = reg.open('Select').value('Current').value()
        return f"ControlSet{current:03d}"
    except Exception:  # pylint: disable=broad-exception-caught
        return "ControlSet001"


def _model_parts(name):
    vendor = product = revision = ''
    for part in name.split('&'):
        if part.startswith('Ven_'):
            vendor = part[4:].replace('_', ' ')
        elif part.startswith('Prod_'):
            product = part[5:].replace('_', ' ')
        elif part.startswith('Rev_'):
            revision = part[4:].replace('_', ' ')
    return vendor, product, revision


def _property_node(instance, prop_id):
    """The sub-key of one device property under _PROP_SET, matched by its number so
    that Windows 7's eight-digit names (00000065) and the later four-digit ones (0065)
    both resolve."""
    try:
        group = instance.subkey('Properties').subkey(_PROP_SET)
    except Registry.RegistryKeyNotFoundException:
        return None
    for node in group.subkeys():
        try:
            if int(node.name(), 16) == int(prop_id, 16):
                return node
        except ValueError:
            continue
    return None


def _stored_filetime(node):
    """The raw bytes of a device property stored with the FILETIME property type, in
    either layout: Windows 8 and later keep it in the sub-key's default value, whose
    type python-registry reports as the property type (0x10); Windows 7 keeps a sub-key
    00000000 holding a Type value and a Data value. None for anything else."""
    for value in node.values():
        try:
            if value.value_type() & 0xFFFF == _TYPE_FILETIME:
                return bytes(value.raw_data())
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    try:
        inner = node.subkey('00000000')
        kind = struct.unpack('<I', bytes(inner.value('Type').raw_data())[:4])[0]
        if kind == _TYPE_FILETIME:
            return bytes(inner.value('Data').raw_data())
    except (Registry.RegistryKeyNotFoundException, Registry.RegistryValueNotFoundException,
            struct.error):
        pass
    return None


def _property_filetime(instance, prop_id):
    """Read a device-property FILETIME. The value stores a device-property type
    that python-registry's value() cannot decode, so read the raw bytes."""
    node = _property_node(instance, prop_id)
    raw = _stored_filetime(node) if node is not None else None
    if raw and len(raw) >= 8:
        return _filetime_utc(struct.unpack('<Q', raw[:8])[0])
    return ''


def _friendly_name(instance):
    try:
        return instance.value('FriendlyName').value() or ''
    except Registry.RegistryValueNotFoundException:
        return ''


@artifact_processor
def usbDevices(context):
    data_headers = (('Last Connected (UTC)', 'datetime'),
                    ('First Install (UTC)', 'datetime'),
                    ('Last Removed (UTC)', 'datetime'),
                    'Friendly Name', 'Vendor', 'Product', 'Revision', 'Serial')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('USB Storage Devices: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found() if not is_transaction_log(f)]:
        relative_source = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            usbstor = reg.open(_current_set(reg) + r"\Enum\USBSTOR")
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'USB Storage Devices: could not read {relative_source}: {exc}')
            continue
        rows_here = 0
        for model in usbstor.subkeys():
            vendor, product, revision = _model_parts(model.name())
            for instance in model.subkeys():
                data_list.append((
                    _property_filetime(instance, _LAST_ARRIVAL),
                    _property_filetime(instance, _FIRST_INSTALL),
                    _property_filetime(instance, _LAST_REMOVAL),
                    _friendly_name(instance), vendor, product, revision,
                    instance.name()))
                rows_here += 1
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
