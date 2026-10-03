"""Windows program compatibility event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Application-Experience Program-Telemetry log (500 and 505, a
compatibility fix applied to a process: the program path, its process ID and
start time, and the fix) and the Program Compatibility Assistant log (17, a PCA
resolver fired for a program). Event IDs, field names and message text are
sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records, utc_from_system_time

_TELEMETRY_LOG = 'Microsoft-Windows-Application-Experience%4Program-Telemetry.evtx'
_TELEMETRY_PROVIDER = 'Microsoft-Windows-Application-Experience'
_FIX_EVENTS = {'500', '505'}

_PCA_LOG = 'Microsoft-Windows-Application-Experience%4Program-Compatibility-Assistant.evtx'
_PCA_PROVIDER = 'Microsoft-Windows-Program-Compatibility-Assistant'
_RESOLVER_EVENT = '17'

__artifacts_v2__ = {
    "compatibilityFixEvents": {
        "name": "Compatibility Fix Events",
        "description": "Compatibility fixes Windows applied to a program's process, from the "
                       "Program-Telemetry event log: the program path, the process ID and "
                       "start time, the fix name and ID, and the account SID each record "
                       "stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Application-Experience%4Program-Telemetry.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-Application-Experience records with "
                 "Event ID 500 or 505 are read. The provider's manifest gives 500 and 505 the same fields "
                 "and the same message, 'Compatibility fix applied to %5. Fix information: %6, %3, %4.', "
                 "which prints the program path, the fix name, the fix ID and the flags, and nothing in it "
                 "tells the two apart, so Event ID is reported as stored (manifest as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Application-Experience.xml#L613-L631 "
                 "and #L709-L727; the same message and fields were read from aeevts.dll and its en-US .mui "
                 "on af_case2_win10, lonewolf_win10, pc_mus_001_win11 and szechuan_win10). Program Path is "
                 "ExePath, Process ID is ProcessId, and Fix Name, Fix ID and Flags are FixName, FixID and "
                 "Flags, all as stored; the manifest does not define the Flags bits. Every 505 row of the "
                 "tested images carried Flags 0x80010101, and every 500 row 0x00010101 except one "
                 "pc_mus_001_win11 row with 0x00010205 and two lonewolf_win10 rows with 0x00040102. Process "
                 "Start Time (UTC) is StartTime, a FILETIME "
                 "that python-evtx renders counted in UTC; on every row of the tested images it was "
                 "between 0.004 and 9.939 seconds before the record's own time, and under 3 seconds on every "
                 "row but one on pc_mus_001_win11. User SID is the SID the "
                 "record's Security element stores: an account SID (S-1-5-21-...) on every row of the "
                 "tested images except one pc_mus_001_win11 500 row that carried S-1-5-18 and two "
                 "lonewolf_win10 500 rows that carried S-1-5-20, and the other rows of lonewolf_win10 held "
                 "one account SID. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with "
                 "integer arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx "
                 "0.8.1's conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores: "
                 "it held one value on every row of af_case2_win10, lonewolf_win10 and pc_mus_001_win11, "
                 "and two on szechuan_win10. A row records that Windows applied the named fix to the "
                 "process started from the program path at the stored start time; it does not establish "
                 "why the program was run. Not read: 502, which the manifest gives the same message for a "
                 "Windows Installer package and which none of the tested images carried. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and "
                 "not reported; every record in this log rendered on the tested images. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-Application-Experience%4Program-Telemetry.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "tool",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1563 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 221 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 32 rows",
        },
    },
    "pcaResolverEvents": {
        "name": "Program Compatibility Assistant Events",
        "description": "Programs the Program Compatibility Assistant fired a resolver for, "
                       "from its event log: the program path and the resolver name as "
                       "stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from "
                 "Microsoft-Windows-Application-Experience%4Program-Compatibility-Assistant.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Program-Compatibility-Assistant "
                 "records with Event ID 17 are read. The provider's manifest message for 17 is 'Exe: %1 "
                 "ResolverName: %2', over the fields ExePath and ResolverName (manifest as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Program-Compatibility-Assistant.xml#L338-L353, "
                 "and the same message and fields were read from pcaevts.dll and its en-US .mui on the "
                 "tested images). The records store the two fields in an element named ResolverFiredEvent. "
                 "Program Path is ExePath and Resolver (as stored) is ResolverName; what each resolver "
                 "name means is not established here, so the names are reported as stored. The rows of "
                 "pc_mus_001_win11 carried three names: CrashOnLaunch, DetectorShim_KernelDriver and "
                 "WrpKeyMitigation. Every record carried S-1-5-18 in its Security element, so no SID is "
                 "reported. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer "
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx "
                 "0.8.1's conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores: "
                 "it held one value on every row of pc_mus_001_win11. The log held no records on "
                 "af_case2_win10, lonewolf_win10 and szechuan_win10. A row names the program the Program "
                 "Compatibility Assistant fired the resolver for; it does not establish who started the "
                 "program. Not read: the manifest's other events for this log (16, 30, 31, 32 and 200 to "
                 "206), none of which the tested images carried. A record python-evtx cannot render, or "
                 "whose XML does not parse, is counted in the run log and not reported; every record in "
                 "this log rendered on the tested images. Reading needs the python-evtx package (pip "
                 "install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-Application-Experience%4Program-Compatibility-Assistant.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the log holds no records)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the log holds no records)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the log holds no records)",
        },
    },
}


def fix_row(record):
    """One Program-Telemetry 500 or 505 record as a report row."""
    return (record.time, utc_from_system_time(record.get('StartTime')), record.event_id,
            record.get('ExePath'), record.get('ProcessId'), record.get('FixName'),
            record.get('FixID'), record.get('Flags'), record.user_sid, record.record_id,
            record.computer)


def resolver_row(record):
    """One Program Compatibility Assistant 17 record as a report row."""
    return (record.time, record.get('ExePath'), record.get('ResolverName'), record.record_id,
            record.computer)


@artifact_processor
def compatibilityFixEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Process Start Time (UTC)', 'datetime'),
                    'Event ID', 'Program Path', 'Process ID', 'Fix Name', 'Fix ID', 'Flags',
                    'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _TELEMETRY_LOG, 'Compatibility Fix Events', event_ids=_FIX_EVENTS,
        provider=_TELEMETRY_PROVIDER)
    return data_headers, [fix_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def pcaResolverEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Program Path', 'Resolver (as stored)',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _PCA_LOG, 'Program Compatibility Assistant Events',
        event_ids={_RESOLVER_EVENT}, provider=_PCA_PROVIDER)
    return data_headers, [resolver_row(record) for record in records], '\n'.join(sources)
