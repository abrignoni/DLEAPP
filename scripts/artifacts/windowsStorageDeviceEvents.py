"""Windows storage device event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Partition/Diagnostic event 1006, which carries a disk's
manufacturer, model, serial number, capacity and bus type, and
Microsoft-Windows-Kernel-PnP/Configuration events 400, 410 and 420, which name
a device instance that was configured, started or deleted. Event IDs, field
names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_PARTITION_LOG = 'Microsoft-Windows-Partition%4Diagnostic.evtx'
_PNP_LOG = 'Microsoft-Windows-Kernel-PnP%4Configuration.evtx'

# Message text from the Kernel-PnP provider manifest (see notes).
_PNP_EVENTS = {
    '400': 'Device was configured',
    '410': 'Device was started',
    '420': 'Device was deleted',
}

__artifacts_v2__ = {
    "partitionDiagnosticEvents": {
        "name": "Partition Diagnostic Disk Events",
        "description": "Disk records from event 1006 in the "
                       "Microsoft-Windows-Partition/Diagnostic log: manufacturer, "
                       "model, serial number, capacity, bus type and parent device "
                       "as each record stores them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Partition%4Diagnostic.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-Partition records with "
                 "Event ID 1006 are read, one row each. The provider's manifest, as "
                 "registered on Windows 11 build 22621.819 and published in nasbench's "
                 "EVTX-ETW-Resources repository, defines 1006 with the field names used "
                 "here and gives it the message 'For internal use only.' "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Partition.xml#L123-L215), "
                 "so the manifest gives the event no description beyond its field names, "
                 "and every column reports the field as stored. Disk Number, Manufacturer, "
                 "Model, Revision, Serial Number, Capacity (bytes), Parent ID, Location, "
                 "Disk ID, Registry ID, Partition Count and User Removal Policy are "
                 "DiskNumber, Manufacturer, Model, Revision, SerialNumber, Capacity, "
                 "ParentId, Location, DiskId, RegistryId, PartitionCount and "
                 "UserRemovalPolicy; Manufacturer and Serial Number can hold the text "
                 "NULL, as Serial Number did on all 33 rows of af_case2_win10. Bus Type "
                 "(as stored) and Partition Style (as stored) are BusType and "
                 "PartitionStyle, numbers for which the published manifest dump carries no "
                 "names; the rows storing Bus Type 7 were exactly the rows whose Parent ID "
                 "begins USB\\ (8 on pc_mus_001_win11 and 7 on lonewolf_win10). Capacity "
                 "was 0 on 6, 4 and 1 rows on af_case2_win10, pc_mus_001_win11 and "
                 "lonewolf_win10, and those rows still stored a Model and Serial Number; "
                 "what a zero capacity marks is not established here. Event Version is the "
                 "record's event version, which held one value on every row of each "
                 "registered image: 0 on af_case2_win10 and lonewolf_win10 and 4 on "
                 "pc_mus_001_win11. Revision, Serial Number, Partition Style and User "
                 "Removal Policy each held one value on all 33 rows of af_case2_win10; "
                 "Partition Count held one value on all 11 rows of lonewolf_win10. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx "
                 "0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of pc_mus_001_win11 "
                 "and two values on af_case2_win10 and lonewolf_win10. Not reported: the "
                 "event's other fields, including the partition table, MBR and volume boot "
                 "record bytes, which are not decoded. A record python-evtx cannot render, "
                 "or whose XML does not parse, is counted in the run log and not reported; "
                 "every record in this log rendered on the registered images. A row "
                 "records that Windows logged this disk; it does not by itself establish "
                 "who connected it. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Partition%4Diagnostic.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 33 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 11 rows",
        },
    },
    "pnpDeviceConfiguration": {
        "name": "Plug and Play Device Configuration Events",
        "description": "Device configured, started and deleted events (400, 410, "
                       "420) from the Microsoft-Windows-Kernel-PnP/Configuration "
                       "log, with the device instance ID, class and driver each "
                       "record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Kernel-PnP%4Configuration.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-Kernel-PnP records with "
                 "Event ID 400, 410 or 420 are read. Event is the provider manifest's "
                 "message for each, 'Device %1 was configured.', 'Device %1 was started.' "
                 "and 'Device %1 was deleted.' (manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-PnP.xml#L1615-L1652, "
                 "#L1770-L1795 and #L1852-L1869). Device Instance ID, Parent Device "
                 "Instance ID, Class GUID, Driver Name, Driver Provider, Driver Version, "
                 "Driver Date, Matching Device ID and Service are DeviceInstanceId, "
                 "ParentDeviceInstanceId, ClassGuid, DriverName, DriverProvider, "
                 "DriverVersion, DriverDate, MatchingDeviceId and ServiceName as stored; "
                 "the manifest gives only 400 the parent, driver provider, version, date "
                 "and matching device fields, only 410 the service, and 420 no driver "
                 "name, so those columns are blank on the other rows. Status (as stored) "
                 "and Problem (as stored) are Status and Problem, numbers for which the "
                 "published manifest dump carries no names; Status held 0x00000000 on "
                 "every row on the registered images. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of pc_mus_001_win11 "
                 "and two values on af_case2_win10 and lonewolf_win10. Rows cover every "
                 "device class the log names, not only storage. Not reported: the log's "
                 "other events (403, 411, 430, 440, 442 on the registered images). A "
                 "record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record in this log "
                 "rendered on the registered images. Reading needs the python-evtx package "
                 "(pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Kernel-PnP%4Configuration.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "plug",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 345 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 205 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 250 rows",
        },
    },
}


@artifact_processor
def partitionDiagnosticEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Disk Number', 'Manufacturer', 'Model',
                    'Revision', 'Serial Number', 'Capacity (bytes)', 'Bus Type (as stored)',
                    'Parent ID', 'Location', 'Disk ID', 'Registry ID',
                    'Partition Style (as stored)', 'Partition Count', 'User Removal Policy',
                    'Event Version', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _PARTITION_LOG, 'Partition Diagnostic Disk Events', event_ids={'1006'},
        provider='Microsoft-Windows-Partition')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.get('DiskNumber'), record.get('Manufacturer'),
            record.get('Model'), record.get('Revision'), record.get('SerialNumber'),
            record.get('Capacity'), record.get('BusType'), record.get('ParentId'),
            record.get('Location'), record.get('DiskId'), record.get('RegistryId'),
            record.get('PartitionStyle'), record.get('PartitionCount'),
            record.get('UserRemovalPolicy'), record.version, record.record_id,
            record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pnpDeviceConfiguration(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Instance ID',
                    'Parent Device Instance ID', 'Class GUID', 'Driver Name',
                    'Driver Provider', 'Driver Version', 'Driver Date',
                    'Matching Device ID', 'Service', 'Status (as stored)',
                    'Problem (as stored)', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _PNP_LOG, 'Plug and Play Device Configuration Events',
        event_ids=set(_PNP_EVENTS), provider='Microsoft-Windows-Kernel-PnP')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _PNP_EVENTS[record.event_id],
            record.get('DeviceInstanceId'), record.get('ParentDeviceInstanceId'),
            record.get('ClassGuid'), record.get('DriverName'), record.get('DriverProvider'),
            record.get('DriverVersion'), record.get('DriverDate'),
            record.get('MatchingDeviceId'), record.get('ServiceName'), record.get('Status'),
            record.get('Problem'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
