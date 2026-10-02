"""Windows device driver and service install event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads four Microsoft-Windows-UserPnp events of the System event log. Events
20001 and 20002 record that Driver Management concluded the process to install
a driver for a device instance, or to remove one; events 20003 and 20004 record
the same for adding or removing a service for a device instance. Each pair
stores the same fields and is one artifact. The two artifacts share one read of
the log. Event IDs, field names and message text are sourced in the notes.
"""

import os

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Driver Install Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-UserPnp'

# Event ID: the words of the provider's message that say what the process was to do
# ('Driver Management concluded the process to <these words> %1 ...', see notes).
_DRIVER_EVENTS = {'20001': 'install driver', '20002': 'remove driver'}
_SERVICE_EVENTS = {'20003': 'add Service', '20004': 'remove Service'}
_EVENT_IDS = set(_DRIVER_EVENTS) | set(_SERVICE_EVENTS)

__artifacts_v2__ = {
    "deviceDriverInstalls": {
        "name": "Device Driver Installs",
        "description": "Microsoft-Windows-UserPnp events 20001 and 20002 of the System event log, in which Driver "
                       "Management records that it concluded the process to install a driver for a device instance "
                       "or to remove one: the device, the driver's name, description, provider and version, and the "
                       "status stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-UserPnp and whose Event ID is 20001 or 20002. The "
                 "provider's manifest gives 20001 the message 'Driver Management concluded the process to install "
                 "driver %1 for Device Instance ID %4 with the following status: %9.' and 20002 the message 'Driver "
                 "Management concluded the process to remove driver %1 from Device Instance ID %4 with the following "
                 "status: %9.', sends both to the System channel and gives both the same ten fields "
                 "(Microsoft-Windows-UserPnp manifest as registered on Windows 11 build 22621.819, published in "
                 "nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1160-L1182 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1183-L1205; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold the same two entries: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1072-L1117, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1072-L1117 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1072-L1117). "
                 "Event is the words of that message that name the process: 'install driver' for 20001 and 'remove "
                 "driver' for 20002. Driver Name, Driver Version, Driver Provider, Device Instance ID, Setup Class "
                 "GUID, Reboot Option (as stored), Upgrade Device (as stored), OEM Driver (as stored), Install "
                 "Status (as stored) and Driver Description are the record's DriverName, DriverVersion, "
                 "DriverProvider, DeviceInstanceID, SetupClass, RebootOption, UpgradeDevice, IsDriverOEM, "
                 "InstallStatus and DriverDescription fields as python-evtx renders them. The manifest types "
                 "SetupClass as a GUID, the three flags as booleans and InstallStatus as a 32-bit number shown in "
                 "hexadecimal, and says nothing more about what any field means. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the record stores, counted in "
                 "UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Microsoft "
                 "describes a device instance ID as 'a system-supplied device identification string that uniquely "
                 "identifies a device in the system' "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/device-instance-ids.md#L10). "
                 "Tested on the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, "
                 "build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of "
                 "one Windows 11 build 26200 ARM64 virtual machine (windows11_arm_4688_known and "
                 "windows11_arm_known_20261001). af_case2_win10 gave 12 rows and lonewolf_win10 gave 35, all 47 from "
                 "Event ID 20001. No tested log held a 20002 record, so the 'remove driver' row is written from the "
                 "manifest and no tested record exercised it. The other four logs held no 20001 record although each "
                 "held 20003 records (reported by Device Service Installs) and the manifests of builds 19041.208 and "
                 "22621.819 define 20001; why they hold none is not established. Event ID held one value, 20001, and "
                 "Event held one value, 'install driver', on all 47 rows. Install Status (as stored) held one value, "
                 "0x00000000, on all 47 rows. Reboot Option (as stored) was False on 46 rows and True on 1; on "
                 "af_case2_win10 Reboot Option (as stored) held one value, False, on all 12 rows. OEM Driver (as "
                 "stored) was True on 29 rows and False on 18, and Upgrade Device (as stored) was True on 11 rows "
                 "and False on 36. Driver Name was an INF file name, an underscore, the architecture, an underscore "
                 "and sixteen hexadecimal digits (of the shape name.inf_amd64_0123456789abcdef) on the 12 rows of "
                 "af_case2_win10, and that text followed by a backslash and the INF file name on the 35 rows of "
                 "lonewolf_win10. Driver Version was four numbers joined by dots on all 47 rows. In each image's "
                 "SYSTEM hive (the control set its Select key names as current), every row's Device Instance ID is a "
                 "key under Enum whose ClassGUID value equals Setup Class GUID ignoring case (47 of 47 rows). Taking "
                 "the last row of each of the 38 devices, the key under Control\\Class that the Enum key's Driver "
                 "value names held a DriverVersion equal to Driver Version on 36, a DriverDesc equal to Driver "
                 "Description on 37 and a ProviderName equal to Driver Provider on 38. Its InfPath was a name of the "
                 "form oemN.inf on all 23 whose OEM Driver (as stored) is True, and on all 15 whose value is False "
                 "it was the INF file name that Driver Name begins with. The "
                 "Microsoft-Windows-Kernel-PnP/Configuration log of the same image, which Plug and Play Device "
                 "Configuration Events reports, holds an event 400 (labelled 'Device was configured' there) for the "
                 "row's device within 30 seconds of 22 of the 47 rows, each 0.002 to 26.606 seconds before the row, "
                 "to the millisecond. On all 22 that record's DriverVersion, DriverProvider and ClassGuid equal the "
                 "row's Driver Version, Driver Provider and Setup Class GUID (the GUID ignoring case), and its "
                 "DriverInbox is false on the 12 whose OEM Driver (as stored) is True and true on the 10 whose value "
                 "is False. A device with no row is not shown to have had no driver installed: the Configuration "
                 "logs of the four public images hold 103, 134, 200 and 205 event 400 records, and 10, 12, 0 and 0 "
                 "of them have a row for the same device within 30 seconds. Moved back by a whole number of hours "
                 "(4, 7 or 8), the Event Time (UTC) of 36 of the 47 rows falls between the start and one second "
                 "after the end of a section of the image's Windows\\INF\\setupapi.dev.log whose title begins 'Device "
                 "Install' and whose text names the row's Device Instance ID, ignoring case; each of those sections "
                 "ends 'Exit status: SUCCESS'. Microsoft documents the section times as local time "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/format-of-a-text-log-section-header.md#L45). "
                 "SetupAPI Sections reports that log. Of the 8 and 23 distinct driver names in the rows of the two "
                 "images (the part before any backslash), 3 and 9 are the Driver Package of an Amcache Driver "
                 "Packages row of the same image, and those are all 3 and 9 rows of that table. Rows are in the "
                 "order the log file holds its records, which was rising Record ID on both images. It is not the "
                 "order of Event Time (UTC): on each image one row is earlier than the row before it, and Computer "
                 "held two names. A record python-evtx cannot render, or whose XML does not parse, is counted in the "
                 "run log and not reported. Every record of the four public images' logs rendered; 72 records of "
                 "each capture's log did not, and each of those stores 27 at index 3 of its substitution values, the "
                 "place that held the rendered Event ID on all 43,858 records that rendered. A log marked dirty is "
                 "read past the chunks its header counts, and the run log says how many records came from there. "
                 "Reading needs the python-evtx package (pip install python-evtx). Not read: the provider's events "
                 "20005 to 20009, which the manifest sends to the System channel and whose messages concern device "
                 "installation restricted by policy "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1244-L1313; "
                 "no tested log held one), and the Microsoft-Windows-UserPnp/DeviceInstall log.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "plug",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 12 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 35 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
    "deviceServiceInstalls": {
        "name": "Device Service Installs",
        "description": "Microsoft-Windows-UserPnp events 20003 and 20004 of the System event log, in which Driver "
                       "Management records that it concluded the process to add a service for a device instance or "
                       "to remove one: the device, the service name, the file name and the status stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-UserPnp and whose Event ID is 20003 or 20004. The "
                 "provider's manifest gives 20003 the message 'Driver Management has concluded the process to add "
                 "Service %1 for Device Instance ID %3 with the following status: %6.' and 20004 the message 'Driver "
                 "Management has concluded the process to remove Service %1 for Device Instance ID %3 with the "
                 "following status: %6.', sends both to the System channel and gives both the same six fields "
                 "(Microsoft-Windows-UserPnp manifest as registered on Windows 11 build 22621.819, published in "
                 "nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1206-L1224 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1225-L1243; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold the same two entries: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1118-L1155, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1118-L1155 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1118-L1155). "
                 "Event is the words of that message that name the process: 'add Service' for 20003 and 'remove "
                 "Service' for 20004. Service Name, Driver File Name, Device Instance ID, Primary Service (as "
                 "stored), Update Service (as stored) and Status (as stored) are the record's ServiceName, "
                 "DriverFileName, DeviceInstanceID, PrimaryService, UpdateService and AddServiceStatus fields as "
                 "python-evtx renders them. The manifest types the two flags as booleans and AddServiceStatus as an "
                 "unsigned 32-bit number, and says nothing more about what any field means. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the record stores, "
                 "counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Microsoft "
                 "describes a device instance ID as 'a system-supplied device identification string that uniquely "
                 "identifies a device in the system' "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/device-instance-ids.md#L10). "
                 "Tested on the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, "
                 "build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of "
                 "one Windows 11 build 26200 ARM64 virtual machine (windows11_arm_4688_known and "
                 "windows11_arm_known_20261001). The four public images gave 9, 35, 7 and 5 rows in that order and "
                 "each capture gave 8, the same eight records on both: 72 rows, all from Event ID 20003. No tested "
                 "log held a 20004 record, so the 'remove Service' row is written from the manifest and no tested "
                 "record exercised it. Event ID held one value, 20003, Event held one value, 'add Service', and "
                 "Status (as stored) held one value, 0, on all 72 rows. Primary Service (as stored) was True on 48 "
                 "rows and False on 24, and Update Service (as stored) was True on 36 rows and False on 36. On "
                 "single logs, Device Instance ID held one value and Computer held one value on the 9 rows of "
                 "af_case2_win10; Computer held one value on the 7 rows of pc_mus_001_win11; Update Service (as "
                 "stored) held one value, False, on the 5 rows of szechuan_win10; and Primary Service (as stored) "
                 "held one value, True, and Computer held one value on the 8 rows of each capture. Ignoring case, "
                 "Driver File Name began \\SystemRoot\\ on 58 rows, %SystemRoot%\\ on 6, system32\\ on 1 and a quotation "
                 "mark on 1, and it named a file ending .sys on 65 rows and .exe on 7, so it is not always a driver "
                 "file. The other 6 are 3 rows on each capture, the same three records: a Driver File Name of 38 "
                 "characters that begins 'Sys', then two characters that differ on each of the three, then 'mRoot\\'. "
                 "Where the other rows' values begin with a backslash, the record stores a character between U+000E "
                 "and U+001F before 'Sys', and python-evtx removes the characters of that range from a value it "
                 "renders "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Views.py#L34 "
                 "and "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Views.py#L55-L72). "
                 "The rest of each value, from 'mRoot' on, equals the same part of the ImagePath of the service's "
                 "key in the SYSTEM hive of windows11_arm_known_20261001, ignoring case. The value is reported as "
                 "rendered; how the records came to hold it is not established. In the SYSTEM hive of each public "
                 "image (the control set its Select key names as current), every row's Service Name is a key under "
                 "Services whose ImagePath equals Driver File Name ignoring case (56 of 56 rows; 47 with the same "
                 "letter case), and every row's Device Instance ID is a key under Enum (56 of 56). That Enum key's "
                 "Service value equals Service Name, ignoring case, on all 32 rows whose Primary Service (as stored) "
                 "is True and differs on all 24 whose value is False. Microsoft's AddService documentation describes "
                 "a flag, SPSVCINST_ASSOCSERVICE, with the words 'Assign the named service as the PnP function "
                 "driver (or legacy driver) for the device being installed by this INF file' "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-addservice-directive.md#L42-L43); "
                 "whether Primary Service (as stored) records that flag is not established. In the hive of "
                 "windows11_arm_known_20261001 all 8 rows' services are keys, 5 with an ImagePath equal ignoring "
                 "case, and 4 of the 8 devices are Enum keys, each with a Service value equal to Service Name. "
                 "windows11_arm_4688_known holds no SYSTEM hive. On af_case2_win10 and lonewolf_win10 every row is "
                 "followed by a Device Driver Installs row for the same device: within 0.4 seconds on all 9 rows of "
                 "the first, and within 30 seconds on 33 of the 35 rows of the second, 64.1 seconds at most. The "
                 "other four logs hold no Device Driver Installs row. Moved back by a whole number of hours (4, 5, 7 "
                 "or 8), the Event Time (UTC) of 47 of the 56 rows of the public images falls between the start and "
                 "one second after the end of a section of the image's Windows\\INF\\setupapi.dev.log whose title "
                 "begins 'Device Install' and whose text names the row's Device Instance ID, ignoring case; each of "
                 "those sections ends 'Exit status: SUCCESS'. Microsoft documents the section times as local time "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/format-of-a-text-log-section-header.md#L45). "
                 "SetupAPI Sections reports that log. Rows are in the order the log file holds its records, which "
                 "was rising Record ID on every tested log. It is not always the order of Event Time (UTC): one row "
                 "of lonewolf_win10 is earlier than the row before it. Computer held two names on lonewolf_win10 and "
                 "on szechuan_win10. A record python-evtx cannot render, or whose XML does not parse, is counted in "
                 "the run log and not reported. Every record of the four public images' logs rendered; 72 records of "
                 "each capture's log did not, and each of those stores 27 at index 3 of its substitution values, the "
                 "place that held the rendered Event ID on all 43,858 records that rendered. A log marked dirty is "
                 "read past the chunks its header counts, and the run log says how many records came from there. "
                 "Reading needs the python-evtx package (pip install python-evtx). Not read: the provider's events "
                 "20005 to 20009, which the manifest sends to the System channel and whose messages concern device "
                 "installation restricted by policy "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-UserPnp.xml#L1244-L1313; "
                 "no tested log held one), and the Microsoft-Windows-UserPnp/DeviceInstall log.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "plug",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 8 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 8 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 7 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 9 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 35 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 5 rows",
        },
    },
}

_read = {}


def _system_logs(context):
    return sorted(str(f) for f in context.get_files_found()
                  if str(f).lower().endswith(_LOG) and not os.path.isdir(str(f)))


def install_records(context):
    """The 20001 to 20004 records of every System log found, and the logs read.

    The module's two artifacts are given the same staged logs one after the other, so
    the logs are read once and the result is kept while their paths, sizes and
    modification times stay the same.
    """
    key = tuple((path, os.path.getsize(path), os.path.getmtime(path))
                for path in _system_logs(context))
    if _read.get('key') != key:
        records, sources = read_event_records(context, _LOG, _LABEL, event_ids=_EVENT_IDS,
                                              provider=_PROVIDER)
        _read.update(key=key, records=records, sources=sources)
    return _read['records'], _read['sources']


def driver_row(record):
    return (record.time, record.event_id, _DRIVER_EVENTS[record.event_id],
            record.get('DeviceInstanceID'), record.get('DriverName'),
            record.get('DriverDescription'), record.get('DriverProvider'),
            record.get('DriverVersion'), record.get('SetupClass'), record.get('IsDriverOEM'),
            record.get('UpgradeDevice'), record.get('RebootOption'), record.get('InstallStatus'),
            record.record_id, record.computer)


def service_row(record):
    return (record.time, record.event_id, _SERVICE_EVENTS[record.event_id],
            record.get('DeviceInstanceID'), record.get('ServiceName'),
            record.get('DriverFileName'), record.get('PrimaryService'),
            record.get('UpdateService'), record.get('AddServiceStatus'), record.record_id,
            record.computer)


@artifact_processor
def deviceDriverInstalls(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Instance ID',
                    'Driver Name', 'Driver Description', 'Driver Provider', 'Driver Version',
                    'Setup Class GUID', 'OEM Driver (as stored)', 'Upgrade Device (as stored)',
                    'Reboot Option (as stored)', 'Install Status (as stored)', 'Record ID',
                    'Computer')
    records, sources = install_records(context)
    data_list = [driver_row(record) for record in records if record.event_id in _DRIVER_EVENTS]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def deviceServiceInstalls(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Instance ID',
                    'Service Name', 'Driver File Name', 'Primary Service (as stored)',
                    'Update Service (as stored)', 'Status (as stored)', 'Record ID', 'Computer')
    records, sources = install_records(context)
    data_list = [service_row(record) for record in records if record.event_id in _SERVICE_EVENTS]
    return data_headers, data_list, '\n'.join(sources)
