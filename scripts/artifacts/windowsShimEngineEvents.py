"""Windows kernel shim engine event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-Kernel-ShimEngine/Operational log: event 4 (flags
applied to a device) and event 3
(shims applied to a driver). Event IDs, field names and message text are
sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Kernel-ShimEngine'
_DEVICE_FLAGS_EVENT = '4'
_DRIVER_SHIM_EVENT = '3'

__artifacts_v2__ = {
    "shimEngineDeviceFlags": {
        "name": "Kernel Shim Engine Device Flags",
        "description": "Devices the kernel shim engine applied flags to, from the "
                       "Kernel-ShimEngine Operational event log (event 4): the device name "
                       "as stored, the device class, and the "
                       "flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx, named in the report's "
                 "located-at line; only Microsoft-Windows-Kernel-ShimEngine records with Event ID 4 are read. "
                 "The provider's manifest gives event 4 the message 'Flags [%4] were applied to device [%1] - "
                 "class [%2]. Flags source: %3.' over the fields DeviceName, DeviceClass, FlagSource (UInt32) "
                 "and Flags (UInt64), in that order (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-ShimEngine.xml#L149-L166). Every "
                 "event 4 record on the tested images carried exactly those four fields. Event 4 names a "
                 "device and a device class, not a program. Device Name is DeviceName as stored: on the tested images it began with one of "
                 "five prefixes and a colon (USBXHCI:, BthRadioHci:, USB:, USBSTOR:, NDIS:), and what the prefix "
                 "denotes is not established here. On 820 of the 936 rows it went on with a string in the form of "
                 "a Plug and Play hardware ID, such as USB\\VID_xxxx&PID_xxxx, and the other 116 rows carried a "
                 "single word instead. Device Class "
                 "is DeviceClass as stored; the tested images carried USBXHCI, USBXHCI2, BthRadioHci, USB, "
                 "USBSTOR and NdisMp. Device Name and Device Class held one value on every row of af_case2_win10 "
                 "and alihadi_challenge3_win81, where one NDIS device is the only device named. Flags and Flags Source are Flags and FlagSource as stored; the manifest "
                 "defines no meaning for either value, so none is given here. Flags Source held 1 on every "
                 "row of every tested image. On the tested images every USBSTOR row (eight rows on four "
                 "images) named the device by vendor and product ID only, with no serial number, and such a value "
                 "on its own does not single out one physical device. One device name can have many rows: on "
                 "ou_ransomware_server2022 the 396 rows carry five distinct device names, two of them on 132 rows "
                 "each, and when the engine writes the event is not established here. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with "
                 "integer arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx "
                 "0.8.1's conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/"
                 "Evtx/BinaryParser.py#L105-L113). Record ID is the record's EventRecordID. Computer is the "
                 "machine name the record stores. Computer held one value on every pc_mus_001_win11 row and two "
                 "or three values on each other image with more than one row, so it is read per row. The records' Security element carried S-1-5-18 or no SID, so no SID is reported. Event 3, "
                 "shims applied to a driver, is reported by Kernel Shim Engine Driver Shims; events 5 and 6, "
                 "which the manifest places in this log at the Verbose level, appeared on none of the tested "
                 "images and are not read. A log marked dirty is read with the chunks its header does not "
                 "count, as scripts/windows_evtx.py describes; six of the eight logs with records were marked "
                 "dirty, and no record came from such a chunk on any of them. A record python-evtx cannot render, or whose XML does not parse, is counted in the run "
                 "log and not reported; every record in this log rendered on the tested images. The log was "
                 "present with no records on alihadi_threatsim_server2019 and no file matched the "
                 "declared path on cfreds_leakage_win7 (Windows 7). Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 7 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the log holds no records)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the "
                                   "declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 157 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 70 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 396 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 271 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 15 rows",
        },
    },
    "shimEngineDriverShims": {
        "name": "Kernel Shim Engine Driver Shims",
        "description": "Drivers the kernel shim engine applied shims to, from the Kernel-ShimEngine "
                       "Operational event log (event 3): the driver name, the shim count and GUIDs, "
                       "and the shim source as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx, named in the report's "
                 "located-at line; only Microsoft-Windows-Kernel-ShimEngine records with Event ID 3 are read. "
                 "The provider's manifest gives event 3 the message '%3 shim(s) were applied to driver [%1]. "
                 "Shim(s) source: %2. Shim GUID(s): %4.' over the fields DriverName, ShimSource (UInt32), "
                 "ShimCount (UInt32) and AppliedGuids, in that order (manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository: https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-ShimEngine.xml#L129-L148"
                 "). Every event 3 record on the tested images carried exactly those four fields. "
                 "Driver Name is DriverName, Shim Count is ShimCount and Shim GUIDs is AppliedGuids, all as "
                 "stored. Shim Source is ShimSource as stored; the manifest defines no meaning for its values, "
                 "so none is given here. On the tested images Shim Count held 1 on every row, and Shim Source "
                 "held 0 on every row except the eight pc_mus_001_win11 rows naming a second driver, which "
                 "held 1. The tested images carried two driver names, one on every image with records and a "
                 "second on pc_mus_001_win11 only, each with one GUID, and the GUIDs are not resolved to shim "
                 "names here. Driver Name and Shim GUIDs therefore held one value on every row of each tested "
                 "image except pc_mus_001_win11. A row records that the engine applied the shims to the named driver; it does "
                 "not say who installed the driver or when. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with "
                 "integer arithmetic, counted in UTC and cut to whole microseconds. Record ID is the record's "
                 "EventRecordID. Computer is the machine name the record stores. Computer held one value on every "
                 "pc_mus_001_win11 row and one to four values on each other image, so it is read per row. The records' Security element carried S-1-5-18, so no SID is reported. Event 4, flags applied to a device, is reported by Kernel Shim Engine Device "
                 "Flags. A record python-evtx cannot render, or whose XML does not parse, is counted in the run"
                 " log and not reported; every record in this log rendered on the tested images. The log was "
                 "present with no records on alihadi_threatsim_server2019 and no file matched the "
                 "declared path on cfreds_leakage_win7 (Windows 7). Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 3 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 7 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the log holds no records)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the "
                                   "declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 33 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 11 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
        },
    },
}


def device_flags_row(record):
    """One event 4 record as a report row."""
    return (record.time, record.get('DeviceName'), record.get('DeviceClass'), record.get('Flags'),
            record.get('FlagSource'), record.record_id, record.computer)


def driver_shim_row(record):
    """One event 3 record as a report row."""
    return (record.time, record.get('DriverName'), record.get('ShimCount'), record.get('AppliedGuids'),
            record.get('ShimSource'), record.record_id, record.computer)


@artifact_processor
def shimEngineDeviceFlags(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Device Name', 'Device Class', 'Flags',
                    'Flags Source', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Kernel Shim Engine Device Flags', event_ids={_DEVICE_FLAGS_EVENT},
        provider=_PROVIDER)
    return data_headers, [device_flags_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def shimEngineDriverShims(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Driver Name', 'Shim Count', 'Shim GUIDs',
                    'Shim Source', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Kernel Shim Engine Driver Shims', event_ids={_DRIVER_SHIM_EVENT},
        provider=_PROVIDER)
    return data_headers, [driver_shim_row(record) for record in records], '\n'.join(sources)
