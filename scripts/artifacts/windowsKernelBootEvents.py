"""Kernel boot event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-Kernel-Boot record of the System event log: what the boot environment reported when
Windows started or resumed, such as the boot type, the load options and whether the last shutdown and boot succeeded.
The Event IDs, the message text and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Kernel Boot Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-Kernel-Boot'

# The fields that have a column of their own, in column order; any other field goes to Other Fields.
_SHOWN = ('BootType', 'LoadOptions', 'LastShutdownGood', 'LastBootGood')

# Event ID: the first sentence of the provider's message for it, placeholders as written (see notes).
_EVENTS = {
    '10': 'The system firmware has allocated a memory region previously determined to be unreliable.',
    '16': 'Windows failed to resume from hibernate with error status %1.',
    '17': 'The boot manager multi OS selection screen was displayed.',
    '18': 'There are %1 boot options on this system.',
    '19': 'There are %1 boot tool options on this system.',
    '20': "The last shutdown's success status was %1.",
    '21': 'The OS loader advanced options menu was displayed and the user selected option %1.',
    '22': 'The OS loader edit options menu was displayed.',
    '23': 'The Windows key was pressed during boot.',
    '24': 'The F8 key was pressed during boot.',
    '25': 'The boot menu policy was %1.',
    '26': 'A one-time boot sequence was used during this boot.',
    '27': 'The boot type was %1.',
    '29': 'Windows failed fast startup with error status %1.',
    '30': 'The firmware reported boot metrics.',
    '32': 'The bootmgr spent %1 ms waiting for user input.',
    '115': 'Soft reboot cancellation started: %1',
    '116': 'Soft reboot cancellation finished: %1.',
    '124': 'The virtualization-based security enablement policy check at phase %1 failed with status: %2',
    '153': 'Virtualization-based security (policies: %3) is %2.',
    '156': 'Virtualization-based security (policies: %3) is %2 with status: %1',
    '214': 'Soft reboot prepare started (complete requested: %1).',
    '215': 'Soft reboot prepare finished: %1.',
    '216': 'Soft reboot complete prepare started.',
    '217': 'Soft reboot complete prepare finished: %1.',
    '218': 'Soft reboot call to %1 failed: %2 (checkpoint: %3).',
    '221': 'System drivers need update to support VBS launch.',
    '222': 'SMM configuration failed validation.',
    '238': 'EFI time zone bias: %1.',
    '242': 'SMM isolation detected.',
    '247': 'Unable to load Pluton-Windows firmware.',
    '256': 'AMD DRTM Firmware Anti-Rollback Disabled.',
    '272': 'PPAM Manifest Info: %1',
    '274': 'Bootmgr Security Version Number check failed.',
}


__artifacts_v2__ = {
    "kernelBootEvents": {
        "name": "Kernel Boot Events",
        "description": "Microsoft-Windows-Kernel-Boot records of the System event log: the boot type, the load "
                       "options, the success status of the last shutdown and the last boot and the provider's other "
                       "System log values, as the records store them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, every "
                 "record whose provider is Microsoft-Windows-Kernel-Boot, whatever its Event ID. The provider's "
                 "manifest sends 34 Event IDs to the System channel "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L12-L18), "
                 "among them 'There are %1 boot options on this system.' (18, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1346-L1359), "
                 "'The last shutdown's success status was %1. The last boot's success status was %2.' (20, in "
                 "versions 0 and 1, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1373-L1404), "
                 "'The boot menu policy was %1.' (25, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1454-L1467), "
                 "'A one-time boot sequence was used during this boot.' (26, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1468-L1479), "
                 "'The boot type was %1.' (27, in versions 0 and 1, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1480-L1508), "
                 "'The firmware reported boot metrics.' (30, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1555-L1572), "
                 "'The bootmgr spent %1 ms waiting for user input.' (32, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L1586-L1599), "
                 "'The virtualization-based security enablement policy check at phase %1 failed with status: %2' "
                 "(124, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L2757-L2771), "
                 "'Virtualization-based security (policies: %3) is %2.' (153, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L3311-L3326), "
                 "'EFI time zone bias: %1. Daylight flags: %2.' (238, to which version 1 adds 'Firmware time: %3.', "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L4398-L4428) "
                 "and 'Unable to load Pluton-Windows firmware. StatusCode: %1, Reason: %2' (247, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml#L4558-L4573). "
                 "These are entries of the provider's manifest as registered on Windows 11 build 26100.1742, "
                 "published in nasbench's EVTX-ETW-Resources repository. Event is, for each of those 34 Event IDs, "
                 "the message's first sentence: the message with each run of white space made one space, cut after "
                 "the first period that a space or the end of the message follows, with its placeholders (such as "
                 "%1) as the manifest writes them; the versions of an Event ID have the same first sentence. A "
                 "placeholder is an insertion string for a data item of the event's template by its position "
                 "(Microsoft's Defining Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID outside the 34, which no tested record had. "
                 "The manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "and Windows 11 build 22621.819 send 19, 26, 29 and 32 of the 34 Event IDs to the System channel "
                 "with the same first sentence, but for 247 on build 22621.819, whose message is 'Windows boot "
                 "environment failed load the HSP firmware. StatusCode: %1, Reason: %2' at the level Error where "
                 "build 26100.1742 gives the level Information "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-Boot.xml). "
                 "No manifest of build 26200, the captures' build, was read; the captures' records carried Event IDs "
                 "and field names of the build 26100.1742 manifest, and their 247 records store level 4 "
                 "(Information). Boot Type (as stored) and Load Options are the fields BootType and LoadOptions, "
                 "which only 27 carries among those events, and Last Shutdown Good and Last Boot Good are "
                 "LastShutdownGood and LastBootGood, which only 20 carries; they are read by name. Each value is as "
                 "python-evtx renders it with any white space at either end removed, and a column whose field the "
                 "record does not carry is blank. Other Fields lists every other named field that holds more than "
                 "white space as 'name: value', in the record's order, joined with ' | '; a data item that has no "
                 "name is not shown, and no tested record had one. If a record named a field twice the last would be "
                 "read; no entry of the build 26100 manifest names a field twice. Every stored LoadOptions value "
                 "that is not empty had white space at an end (41 rows of the four images and the 77 of each "
                 "capture) and is shown without it. EfiTime of 238 version 1 is a FILETIME, which python-evtx "
                 "renders as text counted in UTC "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1413-L1414). "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element, blank when the record stores none. Record "
                 "ID is the record's EventRecordID and Computer the machine name the record stores. Tested on the "
                 "System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of a Windows 11 "
                 "build 26200 machine, which gave 113, 72, 146, 48, 603 and 603 rows in that order; every row of the "
                 "first capture is a row of the second. The rows are of eleven Event IDs: 18, 20, 25, 27, 32 and 153 "
                 "on every tested log, 30 on lonewolf_win10 and pc_mus_001_win11, 238 on pc_mus_001_win11, "
                 "szechuan_win10 and the captures, 26 on pc_mus_001_win11 (1 row) and the captures (2 rows each), "
                 "124 on pc_mus_001_win11 (4 rows) and 247 on the captures (64 rows each). Every 20 and 27 record is "
                 "version 1, and the 238 records are version 0 on szechuan_win10 and version 1 on the others; each "
                 "tested record's field names were the names the manifest lists for its event and version, in the "
                 "manifest's order. The other 23 Event IDs, and version 0 of 20 and of 27, are unexercised: they are "
                 "read by the field names the manifest lists, which no tested record confirms for them. What a Boot "
                 "Type (as stored) number stands for is not sourced here. It is 0 on 19, 4, 11, 7, 77 and 77 rows of "
                 "27 in the order of the logs above and 2 on the other 9 rows of lonewolf_win10. Load Options is "
                 "filled on every 27 row whose Boot Type (as stored) is 0 and blank on the 9 whose Boot Type (as "
                 "stored) is 2. Last Boot Good is True on every row of 20; Last Shutdown Good is True on all of them "
                 "but 1 row of pc_mus_001_win11 and 1 of each capture, where it is False. The rows come in groups: "
                 "rows less than five seconds apart, which were never more than 0.001 seconds apart, make 19, 13, "
                 "29, 7, 77 and 77 groups. 19, 4, 11, 7, 77 and 77 of them are within five seconds of a "
                 "Kernel-General 12 record (The operating system started, which the Windows System Power Events "
                 "artifact reports); every one of those groups holds a 27 row with Boot Type (as stored) 0, and User "
                 "SID is S-1-5-18 on every row of them. The other 9 groups of lonewolf_win10 and 18 of "
                 "pc_mus_001_win11 have no such record near: each of those 27 groups is within five seconds of the "
                 "WakeTime of a Power-Troubleshooter 1 record (the Wake Time (UTC) of that artifact), the last "
                 "Kernel-Power 42 record before it stores EffectiveState 5, and User SID is blank on all 99 of their "
                 "rows. On lonewolf_win10 each of the 9 holds a 27 row with Boot Type (as stored) 2; on "
                 "pc_mus_001_win11 the 18 hold only 18, 30 and 32 rows and no 27 row. In the other direction, each "
                 "of the 27 Kernel-Power 42 records that store EffectiveState 5 is followed by such a group before "
                 "the next 42 record, and none of the 69 that store EffectiveState 4 or 2 is. What the "
                 "EffectiveState numbers stand for is not sourced here. Last Shutdown Good and Last Boot Good are "
                 "the same, True, on every 20 row of af_case2_win10, lonewolf_win10 and szechuan_win10, and both are "
                 "blank on every other row. Computer held one value on pc_mus_001_win11, two on af_case2_win10, "
                 "lonewolf_win10 and each capture and three on szechuan_win10. Rows are in the order the log file "
                 "holds its records, which was rising Record ID on every tested log; in time order 1 row each of "
                 "af_case2_win10, lonewolf_win10 and the captures is earlier than the row before it. Every record of "
                 "the tested logs rendered, among them the 72 TPM event 27 records of each capture's log, which "
                 "python-evtx renders only with the array value types scripts/windows_evtx.py adds. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted "
                 "in the run log and not reported. A log marked dirty is read past the chunks its header counts, and "
                 "the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx). Not read: the provider's events in its other channels, "
                 "Microsoft-Windows-Kernel-Boot/Operational and Microsoft-Windows-Kernel-Boot/Analytic.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 603 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 603 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 113 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 72 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 146 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 48 rows",
        },
    },
}


def other_fields(record):
    """Every named field without a column that holds a value, as 'name: value' joined with ' | '."""
    return ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                      if name not in _SHOWN and record.get(name))


def boot_row(record):
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''),
            *(record.get(name) for name in _SHOWN), other_fields(record), record.user_sid, record.record_id,
            record.computer)


@artifact_processor
def kernelBootEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Boot Type (as stored)', 'Load Options',
                    'Last Shutdown Good', 'Last Boot Good', 'Other Fields', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [boot_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
