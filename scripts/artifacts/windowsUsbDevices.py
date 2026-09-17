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

__artifacts_v2__ = {
    "usbDevices": {
        "name": "USB Storage Devices",
        "description": "USB mass-storage devices recorded in the Windows "
                       "USBSTOR key: each device's friendly name, vendor, "
                       "product, revision and serial, with the times it was "
                       "first installed, last connected and last removed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the current control set's Enum\\USBSTOR key in the "
                 "SYSTEM hive, named in the report's located-at line, one row per device instance. "
                 "Vendor, Product and Revision are parsed from the model key name "
                 "(Disk&Ven_x&Prod_y&Rev_z), with underscores shown as spaces. "
                 "Serial is the instance sub-key name as stored; a device that "
                 "reports no unique serial is given one by Windows with an "
                 "ampersand as the second character, so a serial of that shape is "
                 "not the manufacturer's. Friendly Name is the device's "
                 "FriendlyName value. First Install (UTC), Last Connected (UTC) "
                 "and Last Removed (UTC) are Windows FILETIMEs read from the "
                 "instance's device properties under the property-key GUID "
                 "83da6326-97a6-4088-9453-a1923f573b29 at property ids 0065 "
                 "(DEVPKEY_Device_FirstInstallDate), 0066 "
                 "(DEVPKEY_Device_LastArrivalDate) and 0067 "
                 "(DEVPKEY_Device_LastRemovalDate); each is blank when the device "
                 "recorded none. USBSTOR covers USB mass storage; other device "
                 "classes under Enum are not read here. A record shows the device "
                 "was connected to the computer, not who connected it. Reading "
                 "the hive requires python-registry. Property ids: Microsoft "
                 "DEVPKEY_Device_FirstInstallDate and its sibling install-date "
                 "keys, https://learn.microsoft.com/en-us/windows-hardware/"
                 "drivers/install/devpkey-device-firstinstalldate",
        "paths": ('*/Windows/System32/config/SYSTEM',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no USBSTOR devices)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
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


def _property_filetime(instance, prop_id):
    """Read a device-property FILETIME. The value stores a device-property type
    that python-registry's value() cannot decode, so read the raw bytes."""
    try:
        node = instance.subkey('Properties').subkey(_PROP_SET).subkey(prop_id)
    except Registry.RegistryKeyNotFoundException:
        return ''
    for value in node.values():
        try:
            raw = value.raw_data()
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        if isinstance(raw, (bytes, bytearray)) and len(raw) >= 8:
            return _filetime_utc(struct.unpack('<Q', bytes(raw[:8]))[0])
    return ''


def _friendly_name(instance):
    try:
        return instance.value('FriendlyName').value() or ''
    except Registry.RegistryValueNotFoundException:
        return ''


@artifact_processor
def usbDevices(context):
    data_headers = ('Friendly Name', 'Vendor', 'Product', 'Revision', 'Serial',
                    ('First Install (UTC)', 'datetime'),
                    ('Last Connected (UTC)', 'datetime'),
                    ('Last Removed (UTC)', 'datetime'))
    data_list = []
    sources = []
    if Registry is None:
        logfunc('USB Storage Devices: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()]:
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
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
                    _friendly_name(instance), vendor, product, revision,
                    instance.name(),
                    _property_filetime(instance, _FIRST_INSTALL),
                    _property_filetime(instance, _LAST_ARRIVAL),
                    _property_filetime(instance, _LAST_REMOVAL)))
                rows_here += 1
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
