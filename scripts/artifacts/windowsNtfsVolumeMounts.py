"""Windows NTFS volume mount and dismount event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Ntfs events 4, 300, 303 and 305 of the Ntfs Operational
event log: a volume mounted, a dismount started, a volume dismounted and a mount
that failed, with the device the volume is on as the record stores it. The
Event IDs, field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'NTFS Volume Mounts'
_LOG = 'Microsoft-Windows-Ntfs%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Ntfs'
_EVENTS = {
    '4': 'The NTFS volume has been successfully mounted.',
    '300': 'NTFS volume dismount has started.',
    '303': 'The NTFS volume has successfully dismounted.',
    '305': 'NTFS failed to mount the volume.',
}

__artifacts_v2__ = {
    "ntfsVolumeMounts": {
        "name": "NTFS Volume Mounts",
        "description": "Microsoft-Windows-Ntfs records of the Ntfs Operational event log for a volume mounted, a "
                       "dismount started, a volume dismounted or a mount that failed, with the device the volume is "
                       "on as the record stores it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Ntfs%4Operational.evtx the paths match with python-evtx and reports, "
                 "one row per record, the records whose provider is Microsoft-Windows-Ntfs and whose Event ID is 4, "
                 "300, 303 or 305. Event is the first line of the event's message in the provider's manifest: 4 'The "
                 "NTFS volume has been successfully mounted.', 300 'NTFS volume dismount has started.', 303 'The NTFS"
                 " volume has successfully dismounted.' and 305 'NTFS failed to mount the volume.' "
                 "(Microsoft-Windows-Ntfs manifest as registered on Windows 11 build 22621.819, published in "
                 "nasbench's EVTX-ETW-Resources repository, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L342-L415,"
                 " "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L3917-L3974,"
                 " "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L4029-L4086"
                 " and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L4183-L4235)."
                 " In version 1 of those events, which every tested record of Windows 11 build 22621 is, the message "
                 "labels the fields the columns read: Volume Name is VolumeId ('Volume name'), Volume Label "
                 "VolumeLabel, Device Manufacturer VendorId ('Device manufacturer'), Device Model ProductId ('Device "
                 "model'), Device Revision ProductRevision, Device Serial Number DeviceSerialNumber, Bus Type (as "
                 "stored) BusType ('Bus type'), Adapter Serial Number AdapterSerialNumber, Device Name DeviceName, "
                 "Volume Correlation ID VolumeCorrelationId and Device GUID DeviceGuid; on 300 and 303, Process ID, "
                 "Process Name and Reason are ProcessId, ProcessName and DismountReason ('Process Id', 'Process name'"
                 " and 'Reason'), and on 4 Mount Duration is MountDuration ('Total mount duration'), text as stored "
                 "such as '62 ms'. Version 0 of 305, which every tested record of Windows 10 build 17763 is, carries "
                 "only Error, VolumeGuid and VolumeName ('Error', 'Volume GUID' and 'Volume Name', "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Ntfs.xml#L1170-L1195),"
                 " read into Error, Volume GUID and Volume Name, so the device columns are blank on those rows. Each "
                 "value is as python-evtx renders it with any white space at either end removed; no tested value had "
                 "any. Tested on the Ntfs Operational logs of four public images: af_case2_win10 (build 17763) gave "
                 "68 rows, all of 305, and pc_mus_001_win11 (build 22621) gave 79, 47 of 4, 16 of 300 and 16 of 303. "
                 "The logs of lonewolf_win10 (build 16299) and szechuan_win10 (build 19041) hold no record of these "
                 "events, and the two captures of a Windows 11 build 26200 machine hold no such log. Every "
                 "af_case2_win10 row names the volume E: and one Volume GUID, and Error is the NTSTATUS the record "
                 "stores: 0xc0210000 on 52 rows and 0xc000000e on 16, which Microsoft's [MS-ERREF] gives as "
                 "STATUS_FVE_LOCKED_VOLUME, 'The volume must be unlocked before it can be used.', and "
                 "STATUS_NO_SUCH_DEVICE, 'A device that does not exist was specified.' "
                 "(https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)."
                 " On af_case2_win10 Event ID, Event, Volume Name and Volume GUID each held one value on all 68 rows,"
                 " and Volume Label, Device Manufacturer, Device Model, Device Revision, Device Serial Number, Bus "
                 "Type, Adapter Serial Number, Process ID, Process Name, Reason, Mount Duration, Device Name, Volume "
                 "Correlation ID and Device GUID were blank on every row. Bus Type is a number for which the manifest"
                 " gives no names. On pc_mus_001_win11 it was 7 on the 4 rows of a NORELSYS 106X volume, D: with the "
                 "label New Volume, 17 on the 23 rows of a LITEON CA1-8D256-HP and 0 on the rest. The same image's "
                 "Partition Diagnostic log, which the Partition Diagnostic Disk Events artifact reads, records a disk"
                 " with that manufacturer and model, bus type 7, a Parent ID beginning USB\\ and the same serial "
                 "number. The two mounts of D: are 3.37 and 2.29 seconds after a record of that disk there with a "
                 "capacity, and its dismount started 0.07 seconds after a record of the disk with capacity 0. Volume "
                 "Name is a drive letter, a \\\\?\\Volume{GUID} path or blank; it is blank on the 24 rows of 4 and the "
                 "14 each of 300 and 303 whose Device Name begins \\Device\\HarddiskVolumeShadowCopy, which leave "
                 "Volume Label and every Device column but Device Name blank, with a Bus Type of 0 and a Device GUID "
                 "of zeros. On every tested dismount the process and reason were System and 'Surprise removal' (3 "
                 "pairs: the NORELSYS volume, the LITEON volume and one shadow copy) or svchost.exe and 'User "
                 "request' (13 pairs, all shadow copies); which service in svchost.exe asked is not recorded. Each of"
                 " the 16 rows of 300 is followed by a row of 303 with the same Volume Correlation ID. Mount Duration"
                 " was '0 µs' on 5 mounts of the LITEON volumes; what that marks is not established here. Event Time "
                 "(UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the "
                 "FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, "
                 "in place of python-evtx 0.8.1's conversion through a floating-point number, which can differ by "
                 "microseconds "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113)."
                 " Record ID is the record's EventRecordID and Computer the machine name the record stores, which "
                 "held one value on each image. Rows are in the order the file holds them, which was rising Record ID"
                 " and time on both images. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record of the tested logs rendered. A log marked "
                 "dirty is read past the chunks its header counts, and the run log says how many records came from "
                 "there. Reading needs the python-evtx package (pip install python-evtx). Not read: the log's other "
                 "events, such as disk space summaries (142), deletions from known folders (151) and a USN journal "
                 "created or deleted (500, 501).",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 68 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the log holds no record of these events)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 79 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the log holds no record of these events)",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
    },
}


def mount_row(record):
    get = record.get
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''),
            get('VolumeId') or get('VolumeName'), get('VolumeLabel'), get('VendorId'), get('ProductId'),
            get('ProductRevision'), get('DeviceSerialNumber'), get('BusType'), get('AdapterSerialNumber'),
            get('ProcessId'), get('ProcessName'), get('DismountReason'), get('MountDuration'), get('Error'),
            get('DeviceName'), get('VolumeCorrelationId'), get('VolumeGuid'), get('DeviceGuid'),
            record.record_id, record.computer)


@artifact_processor
def ntfsVolumeMounts(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Volume Name', 'Volume Label',
                    'Device Manufacturer', 'Device Model', 'Device Revision', 'Device Serial Number',
                    'Bus Type (as stored)', 'Adapter Serial Number', 'Process ID', 'Process Name', 'Reason',
                    'Mount Duration', 'Error', 'Device Name', 'Volume Correlation ID', 'Volume GUID', 'Device GUID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS), provider=_PROVIDER)
    data_list = [mount_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
