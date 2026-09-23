"""Windows VHDMP Operational (virtual disk) event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-VHDMP-Operational: virtual disks surfaced and
unsurfaced (1, 2, 17, 18, 25), handles to virtual disk files opened and closed
(12, 22, 23, 24, 27, 28), and virtual disk file operations (50, 51), each naming
the virtual disk file. Event IDs, field names and message text are sourced in
the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import hex_status, read_event_records

_LOG = 'Microsoft-Windows-VHDMP-Operational.evtx'

# Message text from the VHDMP provider manifest (see notes).
_EVENTS = {
    '1': 'The VHD has come online (surfaced) as disk number',
    '2': 'The VHD has been removed (unsurfaced) as disk number',
    '12': 'Handle for virtual disk created successfully',
    '17': 'Virtual disk (no host access) has been surfaced',
    '18': 'Virtual disk (no host access) has been unsurfaced',
    '22': 'Starting to create the handle for the file backing virtual disk',
    '23': 'Handle for the file backing virtual disk created successfully',
    '24': 'Failed to create handle for the file backing virtual disk',
    '25': 'Beginning to bring the VHD online (surface)',
    '27': 'Starting to close the handle for the file backing virtual disk',
    '28': 'Handle for the file backing virtual disk closed successfully',
    '50': 'Performing VHD operation',
    '51': 'Successfully performed VHD operation',
}

__artifacts_v2__ = {
    "virtualDiskEvents": {
        "name": "Virtual Disk (VHDMP) Events",
        "description": "Virtual disk events from the VHDMP Operational log: the "
                       "virtual disk file each record names, surfacing as a disk "
                       "number, handle creation and closing, and file operations, "
                       "with the account SID each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-VHDMP-Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-VHDMP records with "
                 "Event ID 1, 2, 12, 17, 18, 22, 23, 24, 25, 27, 28, 50 or 51 are read. "
                 "Event is the first sentence of the provider manifest's message with its "
                 "inserted values removed; for 50 and 51 the word operation stands in for "
                 "the VhdMetaOps value, which Operation carries (manifest as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources "
                 "repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-VHDMP.xml#L155-L190, "
                 "#L328-L355, #L426-L461, #L512-L579, #L596-L629 and #L760-L789). Virtual "
                 "Disk File is VhdFileName, or VhdFile on 12, whose message prints it as "
                 "the virtual disk; Disk Number is VhdDiskNumber on 1, 2, 17 and 18; "
                 "Operation and Target File are VhdMetaOps and TargetVhdFileName, which 50 "
                 "carries (51 carries the first); Read Only and VHD Type (as stored) are "
                 "ReadOnly and VhdType on 12, VhdType a number for which the published "
                 "manifest dump carries no names; Status is the Status number on 12, 23, "
                 "24, 28 and 51, shown in hexadecimal with the stored decimal in "
                 "parentheses. Every other value is reported as stored. User SID and "
                 "Process ID are the SID in the record's Security element and the process "
                 "ID in its Execution element. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11. On af_case2_win10 Target File was blank on its one 50 "
                 "row, and Read Only and VHD Type are empty because it carries no 12 "
                 "records; on pc_mus_001_win11 Operation and Target File are empty because "
                 "it carries no 50 or 51 records. lonewolf_win10 carries no VHDMP "
                 "Operational log. Not reported: the manifest's pointer fields "
                 "(VirtualDisk, HandleContext, FileObject), the VmId, Version, Flags, "
                 "AccessMask, WriteDepth and GetInfoOnly fields of 12, the DesiredAccess "
                 "field of 22 and 27, and the log's other events (14, 15, 16, 21, 26, 30, "
                 "300 and 301 on pc_mus_001_win11). A record python-evtx cannot render, or "
                 "whose XML does not parse, is counted in the run log and not reported; "
                 "every record in this log rendered on the registered images. A row names "
                 "the virtual disk file the provider recorded; it does not by itself "
                 "establish which person or program asked for the disk. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-VHDMP-Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 14 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 245 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no VHDMP Operational log on the image)",
                       },
    },
}


@artifact_processor
def virtualDiskEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Virtual Disk File',
                    'Disk Number', 'Operation', 'Target File', 'Read Only', 'VHD Type (as stored)',
                    'Status', 'User SID', 'Process ID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Virtual Disk (VHDMP) Events', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-VHDMP')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id],
            record.get('VhdFileName') or record.get('VhdFile'), record.get('VhdDiskNumber'),
            record.get('VhdMetaOps'), record.get('TargetVhdFileName'), record.get('ReadOnly'),
            record.get('VhdType'), hex_status(record.get('Status')), record.user_sid,
            record.process_id, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
