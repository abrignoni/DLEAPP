"""Windows boot and shutdown performance event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-Diagnostics-Performance events of the
Diagnostics-Performance Operational event log that describe a start up (100),
a shutdown (200) and the items the provider says slowed one (101 to 110 and
201 to 203). The Event IDs, field names and message text are sourced in the
notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records, utc_from_system_time

_LOG = 'microsoft-windows-diagnostics-performance%4operational.evtx'
_PROVIDER = 'Microsoft-Windows-Diagnostics-Performance'

# Event ID: the opening words of the provider's message for it (see notes).
_PERFORMANCE = {
    '100': 'Windows has started up',
    '200': 'Windows has shutdown',
}
_DELAYS = {
    '101': 'This application took longer than usual to start up',
    '102': 'This driver took longer to initialize',
    '103': 'This startup service took longer than expected to startup',
    '104': 'Core system took longer to initialize',
    '105': 'Foreground optimizations (prefetching) took longer to complete',
    '106': 'Background optimizations (prefetching) took longer to complete',
    '107': 'Application of machine policy caused a slow down in the system start up process',
    '108': 'Application of user policy caused a slow down in the system start up process',
    '109': 'This device took longer to initialize',
    '110': 'Session manager initialization caused a slow down in the startup process',
    '201': 'This application caused a delay in the system shutdown process',
    '202': 'This device caused a delay in the system shutdown process',
    '203': 'This service caused a delay in the system shutdown process',
}
# The fields a 100 record and a 200 record name the same things by.
_START = {'100': 'BootStartTime', '200': 'ShutdownStartTime'}
_END = {'100': 'BootEndTime', '200': 'ShutdownEndTime'}
_DURATION = {'100': 'BootTime', '200': 'ShutdownTime'}
_DEGRADATION = {'100': 'BootIsDegradation', '200': 'ShutdownIsDegradation'}

__artifacts_v2__ = {
    "bootShutdownPerformance": {
        "name": "Boot and Shutdown Performance",
        "description": "Microsoft-Windows-Diagnostics-Performance events 100 (Windows has started up) and 200 "
                       "(Windows has shutdown) of the Diagnostics-Performance Operational event log, with the start "
                       "and end times and the duration the record stores for the start up or the shutdown.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Diagnostics-Performance%4Operational.evtx the paths match with "
                 "python-evtx and reports, one row per record, the records whose provider is "
                 "Microsoft-Windows-Diagnostics-Performance and whose Event ID is 100 or 200. The provider's "
                 "manifest sends them to the Microsoft-Windows-Diagnostics-Performance/Operational channel with the "
                 "messages 'Windows has started up: Boot Duration : %6ms IsDegradation : %26 Incident Time (UTC) : "
                 "%2' (100, in versions 1 and 2, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml#L512-L622) "
                 "and 'Windows has shutdown: Shutdown Duration : %4ms IsDegradation : %16 Incident Time (UTC) : %2' "
                 "(200, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml#L911-L945). "
                 "These are the entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository; the manifests that repository publishes for "
                 "Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same entries "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml). "
                 "Event is that message up to its colon. Start Time (UTC) is the field BootStartTime of 100 and "
                 "ShutdownStartTime of 200, which the message prints as Incident Time (UTC). End Time (UTC) is "
                 "BootEndTime or ShutdownEndTime, which the message does not print. Duration (ms) is BootTime or "
                 "ShutdownTime, which the message prints as the duration in milliseconds, and Degradation is "
                 "BootIsDegradation or ShutdownIsDegradation. Main Path Boot Time (ms), Post Boot Time (ms), Startup "
                 "Apps and Reboot After Install are MainPathBootTime, BootPostBootTime, BootNumStartupApps and "
                 "BootIsRebootAfterInstall of 100, and are blank on a 200 row. Start Time (UTC) and End Time (UTC) "
                 "are FILETIME fields, which python-evtx renders as text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1413-L1414) "
                 "counted in UTC, and are blank when that text does not read as a time, which no tested record "
                 "showed. The other fields are as python-evtx renders them with any white space at either end "
                 "removed (no tested value had any), and a column whose field the record does not carry is blank. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 19, 5, 15 and 8 rows in "
                 "that order: 27 of 100, each version 2, and 20 of 200, each version 1. On all 27 rows of 100 "
                 "Duration (ms) equals Main Path Boot Time (ms) plus Post Boot Time (ms), and the Windows System "
                 "Power Events artifact reports a Kernel-General 12 row (The operating system started) no more than "
                 "0.2 seconds after Start Time (UTC). End Time (UTC) is later than Start Time (UTC) plus Duration "
                 "(ms) on all 27, by 0.9 to 6,736.8 seconds, and Event Time (UTC) is 1.1 to 20.1 seconds after End "
                 "Time (UTC). On all 20 rows of 200 End Time (UTC) minus Start Time (UTC) equals Duration (ms) to "
                 "the millisecond. A 200 record is not stamped at the shutdown it describes: Event Time (UTC) is "
                 "more than a minute after End Time (UTC) on 17 of the 20 rows, by 97 to 515,230 seconds, and before "
                 "End Time (UTC) on the other 3. Start Time (UTC) and End Time (UTC), not Event Time (UTC), are the "
                 "times of the shutdown. For 12 of the 20 rows Windows System Power Events reports a 1074 row (A "
                 "process initiated a shutdown or restart) within 3 seconds of Start Time (UTC). Degradation was "
                 "True on 10 rows of 100 and 10 rows of 200 and False on the other 27; what the provider counts as a "
                 "degradation is not sourced here. Reboot After Install held one value, False, on every row of 100. "
                 "Rows are in the order the log file holds its records, which was rising Record ID on every tested "
                 "log; 1 row of lonewolf_win10 is earlier in Event Time (UTC) than the row before it. Computer held "
                 "one value on af_case2_win10 and pc_mus_001_win11 and two on lonewolf_win10 and szechuan_win10. A "
                 "record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the four tested logs rendered. A log marked dirty is read past the "
                 "chunks its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read here: the provider's other events. The "
                 "Boot and Shutdown Delays artifact reads 101 to 110 and 201 to 203, and the four tested logs hold "
                 "no record of any other Event ID.",
        "paths": ('*/Windows/System32/winevt/Logs/'
                  'Microsoft-Windows-Diagnostics-Performance%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 15 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 8 rows",
        },
    },
    "bootShutdownDelays": {
        "name": "Boot and Shutdown Delays",
        "description": "Microsoft-Windows-Diagnostics-Performance events 101 to 110 and 201 to 203 of the "
                       "Diagnostics-Performance Operational event log: the application, driver, service, device or "
                       "system step the provider reports as having slowed a start up or a shutdown, with its file "
                       "details and the times the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Diagnostics-Performance%4Operational.evtx the paths match with "
                 "python-evtx and reports, one row per record, the records whose provider is "
                 "Microsoft-Windows-Diagnostics-Performance and whose Event ID is 101 to 110 or 201 to 203. The "
                 "provider's manifest sends the thirteen events to the "
                 "Microsoft-Windows-Diagnostics-Performance/Operational channel, each in version 1, and Event is its "
                 "message for the Event ID up to the first comma or colon (101 to 110, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml#L623-L910; "
                 "201 to 203, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml#L946-L1053). "
                 "These are the entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository; the manifests that repository publishes for "
                 "Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same entries "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Diagnostics-Performance.xml). "
                 "Incident Time (UTC) is the field StartTime, which every one of those messages prints as Incident "
                 "Time (UTC); it is a FILETIME field, which python-evtx renders as text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1413-L1414) "
                 "counted in UTC, and is blank when that text does not read as a time, which no tested record "
                 "showed. Name is Name, which the messages of 101, 102, 103, 109, 201, 202 and 203 print as File "
                 "Name and the others as Name. Friendly Name and Version are FriendlyName and Version, Total Time "
                 "(ms) and Degradation Time (ms) are TotalTime and DegradationTime, and Path, Product Name and "
                 "Company Name are Path, ProductName and CompanyName, which no message prints. The manifest gives "
                 "104, 105, 106, 107, 108 and 110 only StartTime, Name, TotalTime and DegradationTime, so the other "
                 "columns are blank on their rows. Each field is as python-evtx renders it with any white space at "
                 "either end removed, which changed 1 tested value, a Friendly Name on pc_mus_001_win11 that ends in "
                 "a space; a column whose field the record does not carry is blank. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores "
                 "with integer arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx "
                 "0.8.1's conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 10, 2, 33 and 6 rows in "
                 "that order: 42 of 101, 5 of 203, 2 of 110 and 1 each of 103 and 107, each version 1. No tested log "
                 "held a 102, 104, 105, 106, 108, 109, 201 or 202 record, so those eight events are unexercised and "
                 "read as the manifest describes them. Incident Time (UTC) equals the Start Time (UTC) of a Boot and "
                 "Shutdown Performance row on every tested row: a 100 row for all 46 rows of 101, 103, 107 and 110 "
                 "and a 200 row for all 5 rows of 203. Total Time (ms) is not below Degradation Time (ms) on any of "
                 "the 51 rows. Of the 51 rows, Path is filled on 48, Version, Product Name and Company Name on 34 "
                 "and Friendly Name on 29. Name and Path are as stored: 6 rows of 101 (5 on af_case2_win10 and 1 on "
                 "lonewolf_win10) store a Name of Devic, Dev or De and a Path of C:\\ followed by that name, and what "
                 "file they stand for is not established. Rows are in the order the log file holds its records, "
                 "which was rising Record ID and time on every tested log. Computer held one value on af_case2_win10 "
                 "and pc_mus_001_win11 and two on lonewolf_win10 and szechuan_win10. A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not reported; every record of "
                 "the four tested logs rendered. A log marked dirty is read past the chunks its header counts, and "
                 "the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx). Not read here: the provider's other events. The Boot and Shutdown "
                 "Performance artifact reads 100 and 200, and the four tested logs hold no record of any other Event "
                 "ID.",
        "paths": ('*/Windows/System32/winevt/Logs/'
                  'Microsoft-Windows-Diagnostics-Performance%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 33 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 6 rows",
        },
    },
}


def performance_row(record):
    event_id = record.event_id
    return (record.time, utc_from_system_time(record.get(_START[event_id])),
            utc_from_system_time(record.get(_END[event_id])), event_id, _PERFORMANCE[event_id],
            record.get(_DURATION[event_id]), record.get('MainPathBootTime'), record.get('BootPostBootTime'),
            record.get(_DEGRADATION[event_id]), record.get('BootNumStartupApps'),
            record.get('BootIsRebootAfterInstall'), record.record_id, record.computer)


def delay_row(record):
    return (record.time, utc_from_system_time(record.get('StartTime')), record.event_id,
            _DELAYS[record.event_id], record.get('Name'), record.get('FriendlyName'), record.get('Version'),
            record.get('TotalTime'), record.get('DegradationTime'), record.get('Path'),
            record.get('ProductName'), record.get('CompanyName'), record.record_id, record.computer)


@artifact_processor
def bootShutdownPerformance(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Start Time (UTC)', 'datetime'),
                    ('End Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Duration (ms)',
                    'Main Path Boot Time (ms)', 'Post Boot Time (ms)', 'Degradation', 'Startup Apps',
                    'Reboot After Install', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, 'Boot and Shutdown Performance',
                                          event_ids=set(_PERFORMANCE), provider=_PROVIDER)
    data_list = [performance_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def bootShutdownDelays(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Incident Time (UTC)', 'datetime'), 'Event ID', 'Event',
                    'Name', 'Friendly Name', 'Version', 'Total Time (ms)', 'Degradation Time (ms)', 'Path',
                    'Product Name', 'Company Name', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, 'Boot and Shutdown Delays',
                                          event_ids=set(_DELAYS), provider=_PROVIDER)
    data_list = [delay_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
