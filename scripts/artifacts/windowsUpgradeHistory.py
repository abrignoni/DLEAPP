"""Earlier Windows installations recorded in the SYSTEM hive's Setup key (Source OS), and the devices in its
DeviceMigration keys, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsUpgradeHistory": {
        "name": "Upgrade History (Source OS)",
        "description": "Earlier Windows installations a system was upgraded from, one row per Source OS key of the "
                       "SYSTEM hive: the product, build and install time of the earlier installation and the "
                       "time in the key's name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each subkey of the SYSTEM hive's Setup key whose name has the form Source OS "
                 "(Updated on <date and time>). No Microsoft description of these keys was found, so nothing "
                 "here rests on one: the artifact reports what the key stores, and what follows was measured on "
                 "pc_mus_001_win11, the only tested extraction that has such a key. The key holds values with "
                 "the names Windows uses for the installed system under Microsoft\\Windows NT\\CurrentVersion of "
                 "the SOFTWARE hive, and on that image they describe another installation than the current one: "
                 "Product Name Windows 10 Home, Display Version 22H2, Release ID 2009, Build 19045 and UBR 2006, "
                 "where the SOFTWARE hive of the same image holds build 22621. Install Date (UTC) is the key's "
                 "InstallDate value read as seconds since 1970 and Install Time (UTC) its InstallTime value read "
                 "as a FILETIME, as the Windows System Information artifact reads the values of the same names; "
                 "on the image the two are the same second, 2022-11-11 16:10:44 UTC. Updated On (Key Name) is "
                 "the date and time in the key's name, as written there and not converted: it holds no time "
                 "zone. On the image it is 11/22/2022 19:09:57, and read with the hive's time zone bias of 300 "
                 "minutes it is 33 minutes 32 seconds before the InstallDate of the current installation in the "
                 "SOFTWARE hive and 19 minutes 10 seconds before the key's last-written time, which is "
                 "consistent with a local time written when the upgrade to the current installation ran; the "
                 "order of day and month in the name on systems with other regional settings was not tested. Key "
                 "Last Written (UTC) is the last-written time of the key. The same image's Setup\\Upgrade key "
                 "holds a DownlevelBuildNumber of 10.0.19045, the Build of the row; that key is not read. "
                 "Edition ID, Registered Owner, Registered Organization, Product ID and System Root are the "
                 "values of those names as stored, and a value that is absent or binary gives an empty cell. "
                 "Registered Organization was empty on the one row. A system that was never upgraded in place "
                 "has no such key: af_case2_win10, lonewolf_win10, szechuan_win10 and the two Windows 11 build "
                 "26200 captures have none and give no row, so absence of a row is not evidence about how "
                 "Windows was installed beyond that. More than one key in a hive, a key without the install "
                 "values and a hive that cannot be read were tested with constructed input only. Source File is "
                 "the hive. Reading the hive requires the python-registry package; a dirty hive is read after "
                 "its transaction logs are applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "arrow-up-circle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Source OS key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Source OS key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Source OS key)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no Source OS key)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no Source OS key)",
        },
    },
    "windowsDeviceMigration": {
        "name": "Device Migration",
        "description": "Device instances under the DeviceMigration\\Devices keys of the SYSTEM hive, the one under "
                       "Setup\\Upgrade\\PnP and the one in each control set: one row per instance, with its "
                       "stored Present and LastPresentDate values and whether an instance with the same ID is a "
                       "key under Enum in the current control set.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each key three levels below a DeviceMigration\\Devices key (enumerator, device, "
                 "instance, the levels of the Enum key), read from Setup\\Upgrade\\PnP\\CurrentControlSet\\Control"
                 "\\DeviceMigration\\Devices and from Control\\DeviceMigration\\Devices in every ControlSet key; "
                 "Key names which. The subkeys below an instance (Interfaces, Properties, Driver, Device, "
                 "Instance) and the Classes and Locations keys beside Devices are not read. No Microsoft "
                 "description of these keys or their values was found, so nothing here rests on one. Published "
                 "research describes the Setup\\Upgrade copy as written by Windows Setup during a feature update, "
                 "with LastPresentDate dating when a device was last connected: Ilya Kobzar "
                 "(https://www.ilyakobzar.com/p/windows-updates-and-anti-forensics), Alexandru Stamate "
                 "(https://alexsta-cybersecurity.com/field-notes/windows-feature-update-evidence/) and Sujay "
                 "Adkesar (https://thelocalh0st.com/posts/windows-feature-update-evidence/). What follows was "
                 "measured on pc_mus_001_win11, the only tested extraction with these keys, which was upgraded "
                 "in place from Windows 10 (see the Upgrade History (Source OS) artifact). The Setup\\Upgrade "
                 "copy held 143 instances: Present was 1 on 130 and 0 on 13. Every row with Present 0 had a "
                 "LastPresentDate and no row with Present 1 had one. Last Present Date (UTC) is that value, eight "
                 "bytes of REG_BINARY data, read as a FILETIME; on the image the 13 values fall between "
                 "2022-11-11 and 2022-11-22, every one earlier than the time in the Source OS key's name read "
                 "with the hive's time zone bias (2022-11-23 00:09:57 UTC). A value that is not eight bytes "
                 "gives an empty cell and is counted in the run log. The ControlSet001 copy held 7 instances, "
                 "all with Present 0 and all also in the Setup\\Upgrade copy, six of them with the same values; "
                 "both copies are reported, 150 rows in all, and Last Present Date (UTC) was filled on 20 of "
                 "them, the rows with Present 0.Present (as stored) is the DWORD as stored. In Current Enum is yes "
                 "when Enum in the control set the Select key names as Current has a key with the same "
                 "enumerator, device and instance names, compared without case, and no otherwise. On the image "
                 "7 of the 13 Present 0 instances in the Setup\\Upgrade copy, of the DISPLAY, HDAUDIO and SWD "
                 "enumerators, were not under Enum, and the 6 others were; 2 instances with Present 1 were not "
                 "under Enum either. A no says only that the hive's Enum key holds no such instance, not when or "
                 "why. Key Last Written (UTC) is the instance key's last-written time; on the image every "
                 "instance in the Setup\\Upgrade copy was written within 20 seconds on 2022-11-23, between 00:28:15 "
                 "and 00:28:35 UTC, and these are times of the key, not of the device. Bus Device Description, "
                 "Matching Device ID, Class GUID, Driver INF and Location Info are the values BusDeviceDesc, "
                 "MatchingDeviceId, ClassGuid, DriverInfName and LocationInfo as stored, and an absent value gives "
                 "an empty cell: BusDeviceDesc was on 42 of the 143 instances. The Capabilities, HardwareIds, "
                 "CompatibleIds, LocationPaths and Duplicate values are not shown. Not tested: USB storage "
                 "devices (the image has none in these keys, though the research above reports them), a system "
                 "upgraded more than once, the hive in Windows.old and a hive that cannot be read; more than one "
                 "control set and a value of another type were tested with constructed input only. A system "
                 "with no feature update has no such key: af_case2_win10, lonewolf_win10, szechuan_win10 and the "
                 "two Windows 11 build 26200 captures have none and give no row. Source File is the hive. "
                 "Reading the hive requires the python-registry package; a dirty hive is read after its "
                 "transaction logs are applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cpu",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no DeviceMigration key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no DeviceMigration key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 150 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no DeviceMigration key)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no DeviceMigration key)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no DeviceMigration key)",
        },
    },
}

import re
from collections import Counter

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (current_control_set, filetime_bytes_utc, filetime_utc, found_hives,
                                      key_written_utc, open_hive, open_key, unix_utc)

_NAME = re.compile(r'Source OS \(Updated on (.*)\)\Z', re.IGNORECASE)
# the values shown as text columns, in column order
_TEXT = ('ProductName', 'DisplayVersion', 'ReleaseId', 'CurrentBuild', 'UBR', 'EditionID', 'RegisteredOwner',
         'RegisteredOrganization', 'ProductId', 'SystemRoot')


def _text(data):
    """A value's data for a text column: a string or a number as stored, '' for a missing value or binary data."""
    return '' if data is None or isinstance(data, (bytes, list)) else data


def source_os_rows(reg):
    """The rows for one SYSTEM hive, one per Setup subkey named Source OS (Updated on ...): (install date, install
    time, updated on, key last written, the _TEXT values, key path)."""
    rows = []
    setup = open_key(reg, 'Setup')
    for key in (setup.subkeys() if setup is not None else []):
        match = _NAME.match(key.name())
        if not match:
            continue
        stored = {value.name().lower(): value.value() for value in key.values()}
        text = tuple(_text(stored.get(name.lower())) for name in _TEXT)
        rows.append((unix_utc(stored.get('installdate')), filetime_utc(stored.get('installtime')), match.group(1),
                     key_written_utc(key)) + text + ('Setup\\' + key.name(),))
    return rows


@artifact_processor
def windowsUpgradeHistory(context):
    data_headers = (('Install Date (UTC)', 'datetime'), ('Install Time (UTC)', 'datetime'), 'Updated On (Key Name)',
                    ('Key Last Written (UTC)', 'datetime'), 'Product Name', 'Display Version', 'Release ID',
                    'Build', 'UBR', 'Edition ID', 'Registered Owner', 'Registered Organization', 'Product ID',
                    'System Root', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Upgrade History (Source OS): the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SYSTEM')):
        relative = context.get_relative_path(source)
        try:
            rows = source_os_rows(open_hive(source, context))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Upgrade History (Source OS): could not read {relative}: {exc}')
            continue
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


_MIGRATION = 'Control\\DeviceMigration\\Devices'
_SETUP_MIGRATION = 'Setup\\Upgrade\\PnP\\CurrentControlSet\\' + _MIGRATION
# the values shown as text columns after Present, in column order
_DEVICE_TEXT = ('BusDeviceDesc', 'MatchingDeviceId', 'ClassGuid', 'DriverInfName', 'LocationInfo')


def _instances(key):
    """(enumerator, device, instance) names and key for every key three levels below key."""
    for enumerator in key.subkeys():
        for device in enumerator.subkeys():
            for instance in device.subkeys():
                yield (enumerator.name(), device.name(), instance.name()), instance


def _migration_keys(reg):
    """(path, key) for the DeviceMigration\\Devices key under Setup\\Upgrade and in each control set present."""
    found = [(_SETUP_MIGRATION, open_key(reg, _SETUP_MIGRATION))]
    root = reg.root()
    for control_set in sorted(key.name() for key in root.subkeys() if key.name().lower().startswith('controlset')):
        path = control_set + '\\' + _MIGRATION
        found.append((path, open_key(reg, path)))
    return [(path, key) for path, key in found if key is not None]


def _enum_ids(reg):
    """The enumerator\\device\\instance names under Enum in the current control set, folded to lower case."""
    enum = open_key(reg, current_control_set(reg) + '\\Enum')
    return {'\\'.join(names).lower() for names, _ in _instances(enum)} if enum is not None else set()


def device_migration_rows(reg, problems):
    """The rows for one SYSTEM hive, one per device instance in each DeviceMigration\\Devices key: (last present
    date, key last written, present, instance ID, in current Enum, the _DEVICE_TEXT values, key path)."""
    rows = []
    live = _enum_ids(reg)
    for path, key in _migration_keys(reg):
        for names, instance in _instances(key):
            stored = {value.name().lower(): value.value() for value in instance.values()}
            last_present = stored.get('lastpresentdate')
            if last_present is not None and not (isinstance(last_present, bytes) and len(last_present) == 8):
                problems['LastPresentDate values that are not eight bytes, left blank'] += 1
                last_present = None
            instance_id = '\\'.join(names)
            rows.append((filetime_bytes_utc(last_present), key_written_utc(instance),
                         _text(stored.get('present')), instance_id,
                         'yes' if instance_id.lower() in live else 'no')
                        + tuple(_text(stored.get(name.lower())) for name in _DEVICE_TEXT)
                        + (path + '\\' + instance_id,))
    return rows


@artifact_processor
def windowsDeviceMigration(context):
    data_headers = (('Last Present Date (UTC)', 'datetime'), ('Key Last Written (UTC)', 'datetime'),
                    'Present (as stored)', 'Device Instance ID', 'In Current Enum', 'Bus Device Description',
                    'Matching Device ID', 'Class GUID', 'Driver INF', 'Location Info', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Device Migration: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SYSTEM')):
        relative = context.get_relative_path(source)
        problems = Counter()
        try:
            rows = device_migration_rows(open_hive(source, context), problems)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Device Migration: could not read {relative}: {exc}')
            continue
        for problem, count in sorted(problems.items()):
            logfunc(f'Device Migration: {relative}: {count} {problem}')
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
