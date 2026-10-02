"""Storage ClassPnP event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-StorDiag record of the Storage-ClassPnP Operational event log: requests to a storage
device that the class driver completed as failed, with the device number, vendor, model, serial number and firmware
version the record stores, and the provider's other events of that log. The Event IDs, the message text and the
field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Storage ClassPnP Events'
_LOG = 'Microsoft-Windows-Storage-ClassPnP%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-StorDiag'

# The fields with a column of their own, in column order; every other field goes to Other Fields.
_SHOWN = ('DeviceNumber', 'Vendor', 'Model', 'SerialNumber', 'FirmwareVersion')

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '500': 'Completing a failed upper level read request.',
    '501': 'Completing a failed upper level write request.',
    '502': 'Completing a failed upper level paging read request.',
    '503': 'Completing a failed upper level paging write request.',
    '504': 'Completing a failed IOCTL request.',
    '505': 'Completing a failed Read SCSI SRB request',
    '506': 'Completing a failed Write SCSI SRB request',
    '507': 'Completing a failed non-ReadWrite SCSI SRB request',
    '508': 'Completing a failed Non-SCSI SRB request',
    '509': 'Completing a failed PNP request.',
    '510': 'Completing a failed Power request.',
    '511': 'Completing a failed WMI request',
    '512': 'Get Storage Firmware Information',
    '513': 'Download Storage Firmware',
    '514': 'Activate New Storage Firmware',
    '515': 'Query Device Telemetry',
    '516': 'Failed to process zone command asynchronously',
    '517': 'Read capacity failed with SMR device',
    '518': 'Zone count mismatch',
    '519': 'Retrieve zone information failed',
    '520': 'Query Command Duration Limit support and its Mode Page',
    '521': 'Query Command Duration Limit Mode Page failed',
    '522': 'Set Command Duration Limit Mode Page failed',
    '523': 'Read capacity failed',
}


__artifacts_v2__ = {
    "storageClassPnpEvents": {
        "name": "Storage ClassPnP Events",
        "description": "Microsoft-Windows-StorDiag records of the Storage-ClassPnP Operational event log, such as a "
                       "failed read, write, IOCTL or SCSI request to a storage device, with the device's number, "
                       "vendor, model, serial number and firmware version and each record's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Storage-ClassPnP%4Operational.evtx the paths match with python-evtx "
                 "and reports, one row per record, every record whose provider is Microsoft-Windows-StorDiag, "
                 "whatever its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 24 events to "
                 "this log's channel, 500 to 523, one after another in the file, each version 1 except 517, which is "
                 "version 2 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-StorDiag.xml#L1113-L1741). "
                 "The manifest of Windows 11 build 22621.819 holds 500 to 522, its 517 a version 1 without the "
                 "BytesPerSector and SectorShift fields "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-StorDiag.xml#L1113-L1714), "
                 "and those of Windows 10 builds 16299.15, 17763.107 and 19041.208 hold 500 to 514 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-StorDiag.xml#L1032-L1438, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-StorDiag.xml#L1080-L1486 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-StorDiag.xml#L1103-L1509); "
                 "apart from 517, the entries they share have the same message and fields. These are the manifests "
                 "nasbench's EVTX-ETW-Resources repository publishes. Event is, for the record's Event ID, the first "
                 "sentence of the first line of the build 26100 message: the first line that holds more than white "
                 "space, with each run of white space made one space, cut after the first period that a space or the "
                 "end of the line follows (whole when it has none). None of the 24 messages holds a placeholder. "
                 "Event is blank for an Event ID outside the 24, which no tested record had. Device Number, Vendor, "
                 "Model, Serial Number and Firmware Version are the DeviceNumber, Vendor, Model, SerialNumber and "
                 "FirmwareVersion fields. The manifests give DeviceNumber to each of the 24 events and the other "
                 "four to 20 of them (not 512, 513, 514 and 515), so the 11 tested rows of 512 have a Device Number "
                 "and none of the four. Each value, here and in Other Fields, is as python-evtx renders it with any "
                 "white space at either end removed, which 2,049 tested values had, each in one of the four (Vendor "
                 "on 958 records, FirmwareVersion on 935, Model on 133 and SerialNumber on 23). Vendor is the text "
                 "NULL on 11 tested rows and Serial Number the text NULL on the 933 rows of af_case2_win10, as "
                 "stored. On af_case2_win10 Serial Number held one value, NULL, and Firmware Version held one value, "
                 "1.0, on all 933 rows; on pc_mus_001_win11 Device Number held one value, 1, on all 610 rows. The "
                 "tested rows name 10 devices by Vendor, Model and Serial Number (2, 4, 2 and 2 on the four images), "
                 "among them a SanDisk Extreme and a Samsung Portable SSD T5 on lonewolf_win10 and a SanDisk Cruzer "
                 "Dial on pc_mus_001_win11. Each of the 10 has a row in Partition Diagnostic Disk Events with the "
                 "same manufacturer, model and serial number. Other Fields lists every other named field that holds "
                 "more than white space as 'name: value', in the record's order, joined with ' | '. DeviceGUID is a "
                 "GUID in braces on each of the 1,591 tested records. IrpStatus, DownLevelIrpStatus, Status, "
                 "IoctlControlCode and LBA are 0x followed by hexadecimal digits on every tested record that has "
                 "them, as stored; what the status and control codes stand for is not established here. CdbBytes is "
                 "a win:Binary field in the manifests, which python-evtx renders as Base64 text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1339-L1360); "
                 "decoded, its length equals the record's CdbByteCount on each of the 243 tested records of 505 and "
                 "507. A data item that has no name is not shown, and no tested record had one. If a record named a "
                 "field twice the last would be read. The tested records carried the field names their image's build "
                 "manifest gives the event. Tested on the logs of four public images (af_case2_win10, build 17763; "
                 "lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which "
                 "gave 933, 46, 610 and 2 rows in that order; the two captures of a Windows 11 build 26200 machine "
                 "hold no such log. 8 of the 24 Event IDs occur: 502 and 507 on three images, 504 and 505 on two, "
                 "and 500, 501, 509 and 512 on lonewolf_win10 alone. The other 16 Event IDs are unexercised. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on 711 tested rows, an S-1-5-21 "
                 "account on 168 and blank, the record carrying none, on 712. Record ID is the record's "
                 "EventRecordID and Computer the machine name the record stores, which held one value on "
                 "pc_mus_001_win11 and szechuan_win10 and two on af_case2_win10 and lonewolf_win10. Rows are in the "
                 "order the file holds them, which was rising Record ID on every tested log; in time order 2 rows "
                 "are earlier than the row before them (1 each on af_case2_win10 and lonewolf_win10). Every record "
                 "of the tested logs rendered and is the provider's. A record python-evtx cannot render, or whose "
                 "XML does not parse, is counted in the run log and not reported. A log marked dirty is read past "
                 "the chunks its header counts, and the run log says how many records came from there. Reading needs "
                 "the python-evtx package (pip install python-evtx). Not read: the events these manifests send to "
                 "the Storage-ClassPnP Analytic and Diagnose channels and to the StorDiag Operational channel.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Storage-ClassPnP%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 933 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 46 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 610 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def class_pnp_row(record):
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in _SHOWN and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), *(record.get(name) for name in _SHOWN),
            other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def storageClassPnpEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Number', 'Vendor', 'Model',
                    'Serial Number', 'Firmware Version', 'Other Fields', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [class_pnp_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
