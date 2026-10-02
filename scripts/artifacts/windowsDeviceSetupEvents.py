"""Windows Device Setup Manager event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-DeviceSetupManager Admin log events whose data names
a device by name or instance ID: a device serviced (112) or removed (150, 151,
with its name and container ID), driver installs and updates for a device (121,
123, 124, 125, 126, 234), a failed device node removal (152), and software
installed (160) or a Store link requested (166) for a device. Event IDs, field
names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import hex_status, read_event_records

_LOG = 'Microsoft-Windows-DeviceSetupManager%4Admin.evtx'
_PROVIDER = 'Microsoft-Windows-DeviceSetupManager'

# The provider's message for each event with its inserted values removed (see notes).
_EVENTS = {
    '112': 'Device has been serviced',
    '121': 'Driver install failed for devnode',
    '123': 'The DSM service was delayed for a driver query/download/install on device',
    '124': 'Driver was installed on device',
    '125': 'Installation of a driver on device was blocked by PnP restriction policy',
    '126': 'Device matched driver update',
    '150': 'The device has been removed',
    '151': 'The device failed to respond to a device remove request',
    '152': 'Removal of device node failed',
    '160': 'Software was installed for device',
    '166': 'Device is requesting the following link from the Store',
    '234': 'Device has had a driver update installed',
}

# Report column -> the event data field each event stores it in (see notes).
_FIELDS = {
    'Device Name': {'112': 'Prop_DeviceName', '150': 'Prop_DeviceName',
                    '151': 'Prop_DeviceName', '152': 'Prop_DeviceName'},
    'Container ID': {'112': 'Prop_ContainerId', '150': 'Prop_ContainerId',
                     '151': 'Prop_ContainerId', '152': 'Prop_ContainerId'},
    'Device Instance ID': {'121': 'Prop_DevnodeId', '123': 'Prop_DeviceId',
                           '124': 'Prop_DeviceInstanceId', '125': 'Prop_DevnodeId',
                           '126': 'Prop_DeviceInstanceId', '152': 'Prop_DevnodeId',
                           '160': 'Prop_DeviceInstanceId', '166': 'Prop_DeviceInstanceId',
                           '234': 'Prop_DevnodeId'},
    'Driver Package ID': {'124': 'Prop_PackageId', '126': 'Prop_PackageId'},
    'Software': {'160': 'Prop_SoftwareName'},
    'Store Link': {'166': 'Prop_SoftwareLinks'},
}
_RESULT_EVENTS = {'121', '152'}

__artifacts_v2__ = {
    "deviceSetupManagerEvents": {
        "name": "Device Setup Manager Events",
        "description": "Devices named in the Device Setup Manager Admin event log: devices "
                       "it serviced, device removals, and driver and software install events "
                       "for a device, with the device name and container ID or instance ID "
                       "each record stores and the driver package, software and Store link "
                       "it names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-DeviceSetupManager%4Admin.evtx, named in the report's "
                 "located-at line; only Microsoft-Windows-DeviceSetupManager records with Event ID 112, "
                 "121, 123, 124, 125, 126, 150, 151, 152, 160, 166 or 234 are read, the Admin events whose "
                 "data names a device by name, instance ID, devnode ID or device ID. Event is the "
                 "provider's message for the event with its inserted values, and the clauses that hold "
                 "them, removed: 112 'Device has been serviced' (the message is 'Device '%1' (%2) has been "
                 "serviced, processed %3 tasks, wrote %4 properties, active worktime was %5 "
                 "milliseconds.'), 121 'Driver install failed for devnode', 123 'The DSM service was "
                 "delayed for a driver query/download/install on device', 124 'Driver was installed on "
                 "device', 125 'Installation of a driver on device was blocked by PnP restriction policy', "
                 "126 'Device matched driver update', 150 'The device has been removed', 151 'The device "
                 "failed to respond to a device remove request', 152 'Removal of device node failed', 160 "
                 "'Software was installed for device', 166 'Device is requesting the following link from "
                 "the Store' and 234 'Device has had a driver update installed' (manifest as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-DeviceSetupManager.xml#L285-L301, "
                 "#L316-L329, #L340-L353, #L354-L368, #L369-L381, #L382-L395, #L425-L438, #L439-L452, "
                 "#L453-L466, #L467-L481, #L560-L573 and #L824-L837; the same messages and fields were "
                 "read from DeviceSetupManager.dll and its en-US .mui on the tested images, where build "
                 "16299 on lonewolf_win10 defines neither 160 nor 166). Device Name and Container ID are "
                 "Prop_DeviceName and Prop_ContainerId on 112, 150 and 151, and on 152 when the record "
                 "carries them: the manifest of Windows 11 build 26100.1742 gives 152 the fields "
                 "Prop_DeviceName, Prop_ContainerId and HRESULT and the message 'Device '%1' (%2) "
                 "removal failed with error %3.' "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-DeviceSetupManager.xml#L732-L746), "
                 "where the older manifest gives it Prop_DevnodeId and HRESULT, and it words the other "
                 "eleven messages differently too (112 is 'Device container '%1' (%2) has been serviced, "
                 "processed %3 tasks, and wrote %4 properties in %5 ms.', "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-DeviceSetupManager.xml#L435-L451). "
                 "No tested record is of that build, and Event keeps the labels made from the older "
                 "messages. Device Instance ID is "
                 "Prop_DevnodeId on 121, 125, 152 and 234, Prop_DeviceId on 123, and Prop_DeviceInstanceId "
                 "on 124, 126, 160 and 166. Driver Package ID is Prop_PackageId on 124 and 126, which "
                 "their messages call the driver and the driver update. Software is Prop_SoftwareName on "
                 "160, Store Link is Prop_SoftwareLinks on 166, and Result is the HRESULT on 121 and 152, "
                 "in hexadecimal with the stored decimal in parentheses. Every other value is reported as "
                 "stored. A container ID is 'a system-supplied device identification string that uniquely "
                 "groups the functional devices associated with a single-function or multifunction device "
                 "installed in the computer' (Microsoft Learn, 'Container IDs', "
                 "https://learn.microsoft.com/en-us/windows-hardware/drivers/install/container-ids), so a "
                 "Container ID can be matched to the same device in other records that store one. On the "
                 "tested images 112 and 123 rows were present on all four, 126 and 234 on lonewolf_win10 "
                 "and pc_mus_001_win11, 166 on pc_mus_001_win11 and 121 on szechuan_win10; no tested image "
                 "carried 124, 125, 150, 151, 152 or 160, and those were checked with constructed records "
                 "only. So Driver Package ID was empty on every row of af_case2_win10 and szechuan_win10, "
                 "Software on every row of all four, Store Link on every row except those of "
                 "pc_mus_001_win11, and Result on every row except those of szechuan_win10. Every record "
                 "carried S-1-5-18 in its Security element, so no SID is reported. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores: "
                 "it held one value on every row of af_case2_win10 and pc_mus_001_win11, and two on "
                 "lonewolf_win10 and szechuan_win10. A 112 row records that the service processed the "
                 "device at that time; it does not by itself establish when the device was connected or "
                 "removed. Not reported: the log's events that name no device by name or instance ID (on "
                 "the tested images 100, 101, 105, 106, 109, 130, 167, 169, 171, 200, 201 and 202), the "
                 "task, property and time counts, and the DeviceSetupManager Operational log. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and "
                 "not reported; every record in this log rendered on the tested images. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-DeviceSetupManager%4Admin.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "plug",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 134 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 41 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 43 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 71 rows",
        },
    },
}


def device_row(record):
    """One Device Setup Manager record as a report row."""
    event_id = record.event_id
    values = tuple(record.get(fields[event_id]) if event_id in fields else ''
                   for fields in _FIELDS.values())
    result = hex_status(record.get('HRESULT')) if event_id in _RESULT_EVENTS else ''
    return (record.time, event_id, _EVENTS[event_id], *values, result, record.record_id,
            record.computer)


@artifact_processor
def deviceSetupManagerEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', *_FIELDS, 'Result',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Device Setup Manager Events', event_ids=set(_EVENTS), provider=_PROVIDER)
    return data_headers, [device_row(record) for record in records], '\n'.join(sources)
