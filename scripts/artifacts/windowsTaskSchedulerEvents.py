"""Windows Task Scheduler Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-TaskScheduler/Operational: task registration, update
and deletion events (106, 140, 141) and task action start and finish events
(200, 201). Event IDs, field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-TaskScheduler%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-TaskScheduler'

# Message text from the TaskScheduler provider manifest (see notes).
_REGISTRATION_EVENTS = {
    '106': 'Task registered',
    '140': 'Task registration updated',
    '141': 'Task registration deleted',
}
_ACTION_EVENTS = {
    '200': 'Task action launched',
    '201': 'Task action finished',
}

__artifacts_v2__ = {
    "taskSchedulerRegistrations": {
        "name": "Task Scheduler Task Registrations",
        "description": "Scheduled task registration, update and deletion events "
                       "(106, 140, 141) from the Task Scheduler Operational log, "
                       "with the task name and the account each record names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-TaskScheduler%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-TaskScheduler records with "
                 "Event ID 106, 140 or 141 are read. Event is a short form of the provider "
                 "manifest's message for each, which names an account that registered, "
                 "updated or deleted the task (manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/"
                 "065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/"
                 "22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/"
                 "Microsoft-Windows-TaskScheduler.xml#L924-L938, #L1381-L1395 and "
                 "#L1396-L1410). Task Name is TaskName and Account is UserContext for 106 and "
                 "UserName for 140 and 141, as stored. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, "
                 "counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/"
                 "cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name it "
                 "stores. None of the three registered images carries this log file, so the "
                 "artifact reports nothing on them; it was exercised on one further public "
                 "test image, where it reported 144 rows (106: 11, 140: 127, 141: 6), Account "
                 "held a SID on 60 of them and a domain and account name on the rest, and "
                 "every record rendered. A record python-evtx cannot render, or whose XML "
                 "does not parse, is counted in the run log and not reported. The task "
                 "definitions themselves are reported by the Scheduled Tasks artifact, not "
                 "here. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-TaskScheduler%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Task Scheduler Operational log on the image)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Task Scheduler Operational log on the image)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Task Scheduler Operational log on the image)",
        },
    },
    "taskSchedulerActions": {
        "name": "Task Scheduler Task Actions",
        "description": "Scheduled task action launch and finish events (200, 201) "
                       "from the Task Scheduler Operational log, with the task, "
                       "action, task instance and return code each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-TaskScheduler%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-TaskScheduler records with "
                 "Event ID 200 or 201 are read. Event is a short form of the provider "
                 "manifest's message: 200 'Task Scheduler launched action' and 201 'Task "
                 "Scheduler successfully completed task' with the action and return code "
                 "(manifest as registered on Windows 11 build 22621.819, published in "
                 "nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/"
                 "065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/"
                 "22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/"
                 "Microsoft-Windows-TaskScheduler.xml#L1571-L1605 and #L1606-L1659). Task "
                 "Name, Action, Task Instance ID, Return Code and Engine Process ID are "
                 "TaskName, ActionName, TaskInstanceId, ResultCode and EnginePID as stored; "
                 "the manifest's version 0 of both events carries no EnginePID and version 0 "
                 "of 201 no ResultCode, and 200 never carries ResultCode, so Return Code is "
                 "blank on 200 rows. Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx "
                 "0.8.1, https://github.com/williballenthin/python-evtx/blob/"
                 "cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name it "
                 "stores. None of the three registered images carries this log file, so the "
                 "artifact reports nothing on them; it was exercised on one further public "
                 "test image, where it reported 201 rows (200: 109, 201: 92), Action was "
                 "blank on 6 of the 109 200 rows and 5 of the 92 201 rows as stored, and "
                 "every record rendered. A record python-evtx cannot render, or whose XML "
                 "does not parse, is counted in the run log and not reported. The log's "
                 "other events (for example 100, 102, 129) are not reported. Reading needs "
                 "the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-TaskScheduler%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Task Scheduler Operational log on the image)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Task Scheduler Operational log on the image)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Task Scheduler Operational log on the image)",
        },
    },
}


@artifact_processor
def taskSchedulerRegistrations(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Task Name',
                    'Account', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Task Scheduler Task Registrations',
        event_ids=set(_REGISTRATION_EVENTS), provider=_PROVIDER)
    data_list = []
    for record in records:
        account = record.get('UserContext') if record.event_id == '106' else record.get('UserName')
        data_list.append((
            record.time, record.event_id, _REGISTRATION_EVENTS[record.event_id],
            record.get('TaskName'), account, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def taskSchedulerActions(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Task Name',
                    'Action', 'Task Instance ID', 'Return Code', 'Engine Process ID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Task Scheduler Task Actions',
        event_ids=set(_ACTION_EVENTS), provider=_PROVIDER)
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _ACTION_EVENTS[record.event_id],
            record.get('TaskName'), record.get('ActionName'), record.get('TaskInstanceId'),
            record.get('ResultCode'), record.get('EnginePID'),
            record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
