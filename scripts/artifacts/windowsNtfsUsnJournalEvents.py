"""Windows NTFS USN journal event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Ntfs events 500 and 501 of the Ntfs Operational event
log: a process created or deleted a USN journal on a volume. The Event IDs,
field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'NTFS USN Journal Events'
_LOG = 'Microsoft-Windows-Ntfs%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Ntfs'
_EVENTS = {
    '500': 'A process has created a USN journal on a volume.',
    '501': 'A process has deleted a USN journal on a volume.',
}

__artifacts_v2__ = {
    "ntfsUsnJournalEvents": {
        "name": "NTFS USN Journal Events",
        "description": "Microsoft-Windows-Ntfs records of the Ntfs Operational event log for a process creating or "
                       "deleting a USN journal on a volume, with the process name and volume the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Ntfs%4Operational.evtx the paths match with python-evtx and reports, "
                 "one row per record, the records whose provider is Microsoft-Windows-Ntfs and whose Event ID is 500,"
                 " 'A process has created a USN journal on a volume.', or 501, 'A process has deleted a USN journal "
                 "on a volume.' (Microsoft-Windows-Ntfs manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L4374-L4401"
                 " and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L4402-L4427)."
                 " Both are version 0 on Windows 10 build 19041 and Windows 11 build 22621, with different fields: on"
                 " 19041, 500 carries ProcessName, VolumeCorrelationId, VolumeName, MaximumSize and AllocationDelta "
                 "and 501 the first three "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Ntfs.xml#L2068-L2093"
                 " and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Ntfs.xml#L2094-L2115),"
                 " and on 22621 both also carry JournalId and 501 CurrentUsn. The message labels them 'Process', "
                 "'Volume Id', 'Volume Name', 'Journal Id', 'Maximum Size', 'Allocation Delta' and 'Current USN', "
                 "read into Process Name, Volume ID, Volume Name, Journal ID, Maximum Size, Allocation Delta and "
                 "Current USN, each as python-evtx renders it with any white space at either end removed (no tested "
                 "value had any); a column whose field the record does not carry is blank. Tested on the Ntfs "
                 "Operational logs of four public images: pc_mus_001_win11 (build 22621) gave 9 rows, all of 501, and"
                 " szechuan_win10 (build 19041) gave 13, 7 of 500 and 6 of 501. The logs of af_case2_win10 and "
                 "lonewolf_win10 hold no record of these events, and two earlier captures of a Windows 11 build 26200 machine hold no such log. A later capture of that machine, windows11_arm_ntfs_known_20261004, holds the log as "
                 "wevtutil exported it at the end of a known session, and gave 70 rows, 5 of 500 and 65 of 501, both version 0 with the fields of build 22621. In the session fsutil created a USN journal on a newly formatted volume "
                 "Q: with a maximum size of 1,048,576 and an allocation delta of 262,144, and 5 seconds later deleted it. One row of 500 is timed inside the first step, with Process Name fsutil.exe, Volume Name Q:, Maximum Size "
                 "0x0000000000100000 and Allocation Delta 0x0000000000040000, and its Journal ID read as a FILETIME is 4.002 ms before the row. One row of 501 with the same Journal ID, fsutil.exe and Q: is timed 0.2 ms after the "
                 "recorded end of the second step. On that build, then, a journal deleted with fsutil left a row of 501. The capture's other 64 rows of 501 name 'SearchIndexer.' and C: with one Journal ID, and none is followed by a"
                 " row of 500; its other 4 rows of 500 name powershell.exe and W:. On pc_mus_001_win11 Event ID and Event held one value, 501, on every row."
                 " On the two images Process Name was 'SearchIndexer.' on every row but the first 500 of szechuan_win10, which names System; no stored name was longer than 14 characters, and 'SearchIndexer.' is the first 14 of "
                 "SearchIndexer.exe. Volume Name was C: and Volume ID held one value on each image. Each of the 6 "
                 "rows of 501 on szechuan_win10 is followed by a row of 500 from the same process, at most 85.632 ms "
                 "later, and every 500 row there stores Maximum Size 0x0000000000400000 and Allocation Delta "
                 "0x0000000000100000; on pc_mus_001_win11 Maximum Size and Allocation Delta are blank, and Journal ID"
                 " held one value and Current USN held 0x0000000000000000 on all 9 rows. Microsoft says of a "
                 "journal's identifier 'A journal is assigned a new identifier on creation' "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/winioctl/ns-winioctl-usn_journal_data_v0.md?plain=1#L65)."
                 " Read with The Sleuth Kit 4.15.0, the $Max stream of each image's $Extend\\$UsnJrnl holds a journal "
                 "identifier that, read as a FILETIME, equals the journal file's created time to the microsecond. On "
                 "pc_mus_001_win11 it is the Journal ID all 9 rows of 501 name, so the journal those rows name was on"
                 " the volume when the image was made. On szechuan_win10 it is 3.242 ms before the first 500 row, and"
                 " the $Max stream holds the Maximum Size and Allocation Delta the rows store. On these images, then,"
                 " a row of 501 does not show that the journal was removed and replaced; what the process did to the "
                 "journal is not established here. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113)."
                 " Record ID is the record's EventRecordID and Computer the machine name the record stores, which held one value on pc_mus_001_win11 and on the capture and three on szechuan_win10. Rows are in the order the file "
                 "holds them, which was rising Record ID and time on both images and on the capture. A record python-evtx cannot render,"
                 " or whose XML does not parse, is counted in the run log and not reported. A log marked dirty is "
                 "read past the chunks its header counts, and the run log says how many records came from there. "
                 "Reading needs the python-evtx package (pip install python-evtx). Not read: the $UsnJrnl itself and "
                 "the log's other events.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the log holds no record of these events)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the log holds no record of these events)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 13 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 | 70 rows",
        },
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
    },
}


def journal_row(record):
    get = record.get
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), get('ProcessName'), get('VolumeName'),
            get('JournalId'), get('MaximumSize'), get('AllocationDelta'), get('CurrentUsn'), get('VolumeCorrelationId'),
            record.record_id, record.computer)


@artifact_processor
def ntfsUsnJournalEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Process Name', 'Volume Name', 'Journal ID',
                    'Maximum Size', 'Allocation Delta', 'Current USN', 'Volume ID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS), provider=_PROVIDER)
    data_list = [journal_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
