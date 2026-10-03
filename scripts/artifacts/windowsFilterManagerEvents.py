"""Windows file system filter event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-FilterManager events 1 to 10 of the System event log:
a file system filter loaded, unloaded or failed, and Filter Manager attached or
failed to attach to a volume or file system. A filter record names the filter,
its version and a time value; a volume record names the volume. Event IDs, field
names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'File System Filter Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-FilterManager'

# Event ID: the provider's message for it without its parameters and what follows them (see notes).
_EVENTS = {
    '1': 'File System Filter unloaded successfully',
    '2': 'Name caching for File System Filters has been disabled on volume',
    '3': 'Filter Manager failed to attach to volume',
    '4': 'File System Filter failed to attach to volume',
    '5': 'File System Filter failed to register with Filter Manager',
    '6': 'File System Filter has successfully loaded and registered with Filter Manager',
    '7': 'File System Filter failed to start filtering',
    '8': 'Filter Manager successfully attached to volume',
    '9': 'Filter Manager failed to attach to file system control device object (CDO)',
    '10': 'Filter Manager successfully attached to file system',
}

__artifacts_v2__ = {
    "fileSystemFilterEvents": {
        "name": "File System Filter Events",
        "description": "Microsoft-Windows-FilterManager events 1 to 10 of the System event log: a file system filter "
                       "loaded, unloaded or failed to register, start or attach, and Filter Manager attached or "
                       "failed to attach to a volume or file system, with the filter's name, version and stored time "
                       "value or the volume's name, and the final status.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-FilterManager and whose Event ID is 1 to 10. Other "
                 "providers use those Event IDs in the same log (27, 92, 215 and 22 records on the four public "
                 "images named below), so both are checked. The provider's manifest sends the ten events to the "
                 "System channel with the messages \"File System Filter '%5' (Version %2.%3, %6) unloaded "
                 "successfully.\" (1), \"Name caching for File System Filters has been disabled on volume '%3'.\" (2), "
                 "\"Filter Manager failed to attach to volume '%3'. This volume will be unavailable for filtering "
                 "until a reboot. The final status was %1.\" (3), \"File System Filter '%5' (Version %2.%3, %6) failed "
                 "to attach to volume '%8'. The filter returned a non-standard final status of %1. This filter "
                 "and/or its supporting applications should handle this condition. If this condition persists, "
                 "contact the vendor.\" (4), \"File System Filter '%5' (Version %2.%3, %6) failed to register with "
                 "Filter Manager. The final status for this operation was %1.\" (5), \"File System Filter '%5' (%2.%3, "
                 "%6) has successfully loaded and registered with Filter Manager.\" (6), \"File System Filter '%5' "
                 "(Version %2.%3, %6) failed to start filtering. The final status for this operation was %1.\" (7), "
                 "\"Filter Manager successfully attached to volume '%3'.\" (8), \"Filter Manager failed to attach to "
                 "file system control device object (CDO) '%3'. All volumes associated with this file system will be "
                 "unavailable for filtering until a reboot. The final status was %1.\" (9) and \"Filter Manager "
                 "successfully attached to file system '%3'.\" (10) (Microsoft-Windows-FilterManager manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-FilterManager.xml#L45-L211; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold the same ten entries: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-FilterManager.xml#L45-L211, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-FilterManager.xml#L45-L211 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-FilterManager.xml#L45-L211). "
                 "Event is that message with the filter's quoted name and the version and time in brackets taken "
                 "out, cut before its next parameter or its first period. The manifest gives events 1, 5, 6 and 7 "
                 "the fields FinalStatus, DeviceVersionMajor, DeviceVersionMinor, DeviceNameLength, DeviceName and "
                 "DeviceTime, events 2, 3, 8, 9 and 10 the fields FinalStatus, ExtraStringLength and ExtraString, "
                 "and event 4 both sets. Filter Name is DeviceName, Volume or File System is ExtraString and Final "
                 "Status (as stored) is FinalStatus, each as python-evtx renders it with any white space at either "
                 "end removed (no tested value had any). Filter Version is DeviceVersionMajor and DeviceVersionMinor "
                 "joined with a period, as the messages show them, and blank when the record stores neither. A "
                 "column whose field the record does not carry is blank. The two length fields are not reported; on "
                 "every tested record each equals the number of characters of the name beside it. The manifest gives "
                 "the events no field for a file path or a vendor, and no tested Volume or File System value begins "
                 "with a drive letter. Filter Time (as stored) is DeviceTime, which the manifest types as a FILETIME "
                 "and python-evtx renders as a date and time ending +00:00 (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1413-L1414). "
                 "It is kept as text and is not offered as the time of anything: over the six tested logs it was "
                 "later than the row's Event Time (UTC) on 1,470 of the 2,974 rows that have one and more than 366 "
                 "days from it on 2,800. On the four public images, 386 of the 458 rows with a Filter Time carry the "
                 "TimeDateStamp of the PE header of a file the image holds in Windows\\System32\\drivers or its wd "
                 "folder, named as the Filter Name with .sys and ignoring case, moved back a whole number of hours: "
                 "7 or 8 on af_case2_win10, 4 or 7 on lonewolf_win10, 5 on pc_mus_001_win11 and 7 on szechuan_win10. "
                 "On af_case2_win10 and lonewolf_win10 the same file stamp appears moved back by both numbers (8 of "
                 "11 and 7 of 10 matched stamps). For 71 of the other rows those folders hold a file of that name "
                 "whose stamp is not 0 to 14 whole hours later, and for 1 they hold no file of that name. Microsoft "
                 "describes TimeDateStamp as the low 32 bits of the number of seconds since 00:00 January 1, 1970, "
                 "at offset 4 of the COFF file header that follows the 4-byte PE signature, whose file offset is at "
                 "location 0x3c (Microsoft, 'PE Format', "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L97, "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L101 "
                 "and "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L111). "
                 "Why the difference is a whole number of hours was not established, and the two captures hold no "
                 "driver files to compare. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of one Windows 11 "
                 "build 26200 ARM64 virtual machine (windows11_arm_4688_known and windows11_arm_known_20261001). The "
                 "four public images gave 253, 38, 147 and 72 rows in that order and each capture gave 1,622, the "
                 "same 1,622 records on both. Only events 1 (208 rows over the six logs), 3 (780) and 6 (2,766) "
                 "occurred, every record version 0; events 2, 4, 5 and 7 to 10 are read as the manifest describes "
                 "them and no tested record exercised them. Event 3 occurred on af_case2_win10 (52 rows) and on each "
                 "capture (364), so Volume or File System is blank on every row of lonewolf_win10, pc_mus_001_win11 "
                 "and szechuan_win10, and Final Status (as stored) held one value, 0x00000000, on every row of those "
                 "three logs. Final Status (as stored) was 0x00000000 on all 2,974 rows of events 1 and 6 and "
                 "0xc03a001c on all 780 rows of event 3; what a status value stands for is not looked up. Filter "
                 "Version held one value, 10.0, on every row that has one. Volume or File System was "
                 "\\Device\\HarddiskVolume followed by a number on 770 of the 780 rows of event 3. Each of the 208 "
                 "rows of event 1 is followed later in its log by a row of event 6 with the same Filter Name. On the "
                 "public images the unloaded filters were CldFlt (30 rows) and WdFilter (4). Rows are in the order "
                 "the log file holds its records, which was rising Record ID on every tested log. Event Time (UTC) "
                 "rises with it except for 1 row on af_case2_win10, 1 on lonewolf_win10 and 2 on each capture that "
                 "are earlier than the row before them. Computer held one value on every row of pc_mus_001_win11; "
                 "af_case2_win10, lonewolf_win10 and each capture hold two names and szechuan_win10 three. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. Every record of the tested logs rendered, among them the 72 TPM event 27 records of each "
                 "capture's log, which python-evtx renders only with the array value types scripts/windows_evtx.py "
                 "adds. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: events 11 and 12, which the build 22621 manifest adds "
                 "about bypass IO "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-FilterManager.xml#L212-L257). "
                 "No tested System log held one, or any other event of the provider.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "filter",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 1622 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 1622 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 147 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 253 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 38 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 72 rows",
        },
    },
}


def filter_version(record):
    """'major.minor' as the provider's messages show it, or '' when the record stores neither."""
    major, minor = record.get('DeviceVersionMajor'), record.get('DeviceVersionMinor')
    return f'{major}.{minor}' if major or minor else ''


def filter_row(record):
    return (record.time, record.event_id, _EVENTS[record.event_id], record.get('DeviceName'),
            filter_version(record), record.get('DeviceTime'), record.get('ExtraString'),
            record.get('FinalStatus'), record.record_id, record.computer)


@artifact_processor
def fileSystemFilterEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Filter Name',
                    'Filter Version', 'Filter Time (as stored)', 'Volume or File System',
                    'Final Status (as stored)', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [filter_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
