"""Windows Shell-Core Operational Run key event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Shell-Core/Operational events 9705 and 9706 (started
and finished enumeration of the commands for a registry key) and 9707 and 9708
(started and finished execution of a command). Event IDs, field names and
message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-Shell-Core%4Operational.evtx'

# Message text from the Shell-Core provider manifest (see notes).
_EVENTS = {
    '9705': 'Started enumeration of commands for registry key',
    '9706': 'Finished enumeration of commands for registry key',
    '9707': 'Started execution of command',
    '9708': 'Finished execution of command',
}

__artifacts_v2__ = {
    "shellCoreRunKeyEvents": {
        "name": "Shell-Core Run Key Command Events",
        "description": "Shell-Core Operational events 9705 to 9708: the start and finish "
                       "of the enumeration of commands for a registry key and of the "
                       "execution of each command, with the process ID the finish record "
                       "stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Shell-Core%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-Shell-Core records with "
                 "Event ID 9705, 9706, 9707 or 9708 are read. Event is the provider "
                 "manifest's message for each: 9705 and 9706 'Started' and 'Finished "
                 "enumeration of commands for registry key', 9707 'Started execution of "
                 "command' and 9708 'Finished execution of command' with its PID (manifest "
                 "as registered on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L15435-L15499). "
                 "Registry Key is the KeyName of 9705 and 9706, Command the Command of "
                 "9707 and 9708, and Command Process ID the PID of 9708, as stored. "
                 "Registry Key names a key path without its hive, so whether it was the "
                 "machine or a user key is not recorded; on the registered images it named "
                 "the CurrentVersion Run and RunOnce keys and, on lonewolf_win10, the "
                 "Policies Explorer Run key. User SID is the SID in the record's Security "
                 "element, which held one value on every row of each registered image, and "
                 "Logging Process ID is the process ID in its Execution element. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx "
                 "0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Command is the text "
                 "the record stores; on the registered images some commands began with a "
                 "file name and carried a closing quote with no opening quote and no "
                 "folder (3 of 24 distinct commands on af_case2_win10, 9 of 12 on "
                 "pc_mus_001_win11 and 5 of 11 on lonewolf_win10), so the stored text does "
                 "not always give a program's folder. Not reported: the log's other "
                 "events. A record python-evtx cannot render, or whose XML does not parse, "
                 "is counted in the run log and not reported; every record in this log "
                 "rendered on the registered images. The Run and RunOnce key contents are "
                 "reported by the Run and RunOnce Keys artifact. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Shell-Core%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 232 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 206 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 60 rows",
        },
    },
}


@artifact_processor
def shellCoreRunKeyEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Registry Key',
                    'Command', 'Command Process ID', 'User SID', 'Logging Process ID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Shell-Core Run Key Command Events', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-Shell-Core')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], record.get('KeyName'),
            record.get('Command'), record.get('PID'), record.user_sid, record.process_id,
            record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
