"""Windows NTFS file deletion summary event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Ntfs event 151 of the Ntfs Operational event log: the
number of file deletions the record counts on a volume over a period, with the
names of the processes that made them, as the record stores them. The Event ID, field
names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'NTFS File Deletion Summaries'
_LOG = 'Microsoft-Windows-Ntfs%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Ntfs'
_EVENT_ID = '151'

__artifacts_v2__ = {
    "ntfsDeletionSummaries": {
        "name": "NTFS File Deletion Summaries",
        "description": "Microsoft-Windows-Ntfs event 151 of the Ntfs Operational event log: the number of file deletions "
                       "the record counts on a volume over a period, with the names of the processes that made them and, on "
                       "Windows 11 build 22621, the counts per known folder, as the record stores them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Ntfs%4Operational.evtx the paths match with python-evtx and reports, "
                 "one row per record, the records whose provider is Microsoft-Windows-Ntfs and whose Event ID is 151."
                 " The event is version 0 on Windows 10 build 19041 and Windows 11 build 22621 with different fields "
                 "and messages: on 22621 'In the past %5 seconds %6 files were deleted from the user's popular known "
                 "folders (i.e. Desktop, Documents, Downloads, Music, Pictures, Videos, etc.).' and '%7 of the "
                 "deletions recorded their process names.' (Microsoft-Windows-Ntfs manifest as registered on Windows "
                 "11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L2054-L2097),"
                 " and on 19041 'In the past %5 seconds %6 files were deleted.' and '%7 of the deletions record their"
                 " process name.' "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Ntfs.xml#L1044-L1072)."
                 " Whether the 19041 counts are limited to known folders is not established here. Period (seconds), "
                 "Files Deleted and Deletions With A Process Name are SecondsElapsed, TotalCountDeleteFile and "
                 "TotalCountDeleteFileLogged (%5, %6 and %7). On 22621 Process Names is ProcessNamesArray ('Process "
                 "names') and Desktop, Documents, Downloads, Music, Pictures, Videos and Other are "
                 "CountDeletesInDesktopArray to CountDeletesInOtherArray ('Delete counts'), all text in the manifest "
                 "and reported as stored; every tested record named one process, so how a record writes several is "
                 "not established here. On 19041 a record names one process, Process Names is ProcessName ('Process "
                 "name') and Deleted By The Process is CountDeleteFile ('Delete file count'). Volume Name, Is Boot "
                 "Volume and Volume ID are VolumeName, IsBootVolume and VolumeCorrelationId ('Volume Id'). Each value"
                 " is as python-evtx renders it with any white space at either end removed; no tested value had any. "
                 "Tested on the Ntfs Operational logs of four public images: pc_mus_001_win11 (build 22621) gave 4 "
                 "rows and szechuan_win10 (build 19041) gave 42. The logs of af_case2_win10 and lonewolf_win10 hold "
                 "no record of this event, and two earlier captures of a Windows 11 build 26200 machine hold no such log. A later capture of that machine, windows11_arm_ntfs_known_20261004, holds the log as wevtutil exported it at "
                 "the end of a known session; its 6,194 records, from 2025-08-06 to 2026-10-04, include none of 151. In the session 5 files on the Desktop and 3 in Documents were created and then deleted with PowerShell's "
                 "Remove-Item, and the log was exported 65.1 minutes later, after 3 records of the disk space summary (142) had been written; no 151 followed. Whether build 26200 writes this event, and for which deletions, is not "
                 "established here."
                 " On szechuan_win10 the 42 records form 4 summaries, each a run of records with the same time to the"
                 " second, Period and Files Deleted, and in each the Deleted By The Process counts add up to Files "
                 "Deleted, which equalled Deletions With A Process Name. The largest, at 2020-09-19 04:13:28 UTC, "
                 "counts 8,247 deletions over 3,604 seconds by 19 processes. On pc_mus_001_win11 each of the 4 rows "
                 "names explorer.exe or qemu-system-x8, and its Desktop count equals Files Deleted and Deletions With"
                 " A Process Name. No stored process name was longer than 14 characters, and names such as "
                 "'qemu-system-x8' and 'MicrosoftEdge.' end mid-name. Period ran from 3,600 to 3,629 seconds, and was"
                 " 6,556 on one szechuan_win10 summary. The record does not say when the period began. Volume Name "
                 "was C:, Is Boot Volume True and Volume ID held one value on each image. On pc_mus_001_win11 "
                 "Documents, Downloads, Music, Pictures, Videos and Other held 0 on every row and Deleted By The "
                 "Process was blank, and on szechuan_win10 Desktop, Documents, Downloads, Music, Pictures, Videos and"
                 " Other were blank on every row. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113)."
                 " Record ID is the record's EventRecordID and Computer the machine name the record stores, which "
                 "held one value on each image. Rows are in the order the file holds them, which was rising Record ID"
                 " and time on both images. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: the files deleted, which the record does not name, and"
                 " the log's other events.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the log holds no record of this event)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the log holds no record of this event)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 42 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 | 0 rows (the log holds no record of this event)",
        },
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
    },
}


def deletion_row(record):
    get = record.get
    return (record.time, get('SecondsElapsed'), get('TotalCountDeleteFile'), get('TotalCountDeleteFileLogged'),
            get('ProcessName') or get('ProcessNamesArray'), get('CountDeleteFile'), get('CountDeletesInDesktopArray'),
            get('CountDeletesInDocumentsArray'), get('CountDeletesInDownloadsArray'), get('CountDeletesInMusicArray'),
            get('CountDeletesInPicturesArray'), get('CountDeletesInVideosArray'), get('CountDeletesInOtherArray'),
            get('VolumeName'), get('IsBootVolume'), get('VolumeCorrelationId'), record.record_id, record.computer)


@artifact_processor
def ntfsDeletionSummaries(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Period (seconds)', 'Files Deleted', 'Deletions With A Process Name',
                    'Process Names', 'Deleted By The Process', 'Desktop', 'Documents', 'Downloads', 'Music', 'Pictures',
                    'Videos', 'Other', 'Volume Name', 'Is Boot Volume', 'Volume ID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids={_EVENT_ID}, provider=_PROVIDER)
    data_list = [deletion_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
