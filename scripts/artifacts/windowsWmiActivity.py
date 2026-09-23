"""Windows WMI-Activity Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-WMI-Activity/Operational: the notification query events
5859 and 5860 and the event filter and consumer binding event 5861, and the
provider start (5857) and Error level client operation (5858) events. The
records keep their fields under UserData, and three of those element names
differ from the published manifest dump's names (Processid, Provider and
ClientMachine against processid, providerName and MachineName), so both
spellings are read. Event IDs, field names and message text are sourced in the
notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-WMI-Activity%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-WMI-Activity'

_SUBSCRIPTION_EVENTS = ('5859', '5860', '5861')
_PROVIDER_EVENTS = ('5857', '5858')

__artifacts_v2__ = {
    "wmiEventSubscriptions": {
        "name": "WMI Event Subscription Events",
        "description": "WMI-Activity Operational events 5859, 5860 and 5861: the "
                       "notification queries 5859 and 5860 record and the event filter and "
                       "consumer pairs 5861 records, with the namespace, account and "
                       "process ID each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-WMI-Activity%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-WMI-Activity records "
                 "with Event ID 5859, 5860 or 5861 are read. The provider manifest's "
                 "messages for these events are lists of labelled fields: 5859 labels them "
                 "Namespace, NotificationQuery, OwnerName, HostProcessID, Provider, "
                 "queryID and PossibleCause, 5860 Namespace, NotificationQuery, UserName, "
                 "ClientProcessID, ClientMachine and PossibleCause, and 5861 Namespace, "
                 "Eventfilter (with 'refer to its activate eventid:5859'), Consumer and "
                 "PossibleCause (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WMI-Activity.xml#L418-L467). "
                 "The records keep their fields under a UserData element, and Event "
                 "Element (as stored) is that element's name, one name per Event ID on the "
                 "registered images. Namespace is NamespaceName on 5859 and 5860 and "
                 "Namespace on 5861; Query is Query on 5859 and 5860, which their messages "
                 "label NotificationQuery; Event Filter and Consumer are ESS and CONSUMER "
                 "on 5861; Account is User, labelled OwnerName on 5859 and UserName on "
                 "5860; Process ID, Client Machine and Provider are Processid on 5859 and "
                 "5860, ClientMachine on 5860 and Provider on 5859, the names the records "
                 "on the registered images carry where the published manifest dump names "
                 "them processid, MachineName and providerName, and both spellings are "
                 "read; Possible Cause is PossibleCause. Every value is reported as "
                 "stored. Client Machine held one value on every 5860 row of each "
                 "registered image (12, 16 and 3 rows), the same text as Computer on 12 of "
                 "12, 16 of 16 and 2 of 3 of those rows. On each registered image the 5861 "
                 "rows named one Event Filter and Consumer pair (12 rows on "
                 "af_case2_win10, 10 on pc_mus_001_win11 and 3 on lonewolf_win10). Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx "
                 "0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Not reported: the "
                 "queryid field of 5859. A record python-evtx cannot render, or whose XML "
                 "does not parse, is counted in the run log and not reported; every record "
                 "in this log rendered on the registered images. A row records what the "
                 "WMI-Activity provider logged about a query, filter or consumer; it does "
                 "not by itself establish who registered it or what it ran. Reading needs "
                 "the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-WMI-Activity%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "zap",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 36 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 36 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 9 rows",
                       },
    },
    "wmiProviderActivity": {
        "name": "WMI Provider and Operation Failure Events",
        "description": "WMI-Activity Operational events 5857 (provider started, with its "
                       "result code, host process and provider path) and 5858 (Error "
                       "level, with the client operation, account, client process ID and "
                       "result code).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-WMI-Activity%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-WMI-Activity records "
                 "with Event ID 5857 or 5858 are read. The provider manifest's message for "
                 "5857 is '%1 provider started with result code %2. HostProcess = %3; "
                 "ProcessID = %4; ProviderPath = %5', and 5858, at Error level, labels its "
                 "fields Id, ClientMachine, User, ClientProcessId, Component, Operation, "
                 "ResultCode and PossibleCause (manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WMI-Activity.xml#L382-L417). "
                 "Event Element (as stored) is the name of the UserData element the record "
                 "keeps its fields under, one name per Event ID on the registered images. "
                 "On 5857, Provider Name, Result Code, Host Process, Process ID and "
                 "Provider Path are ProviderName, Code, HostProcess, ProcessID and "
                 "ProviderPath; on 5858, Client Machine, Account, Process ID, Component, "
                 "Operation, Result Code and Possible Cause are ClientMachine, User, "
                 "ClientProcessId, Component, Operation, ResultCode and PossibleCause. "
                 "Every value is reported as stored; the manifest formats both result "
                 "codes as hexadecimal. Result Code held one value on every 5857 row of "
                 "each registered image. Component and Possible Cause held the same text "
                 "as each other on every 5858 row of lonewolf_win10 (156 rows), on 173 of "
                 "174 rows on af_case2_win10 and on 235 of 246 on pc_mus_001_win11. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx "
                 "0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Not reported: the Id "
                 "field of 5858. A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported; every record in this "
                 "log rendered on the registered images. A 5858 row records an operation "
                 "the provider logged at Error level; it does not by itself establish who "
                 "requested it. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-WMI-Activity%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 287 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 506 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 225 rows",
                       },
    },
}


@artifact_processor
def wmiEventSubscriptions(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event Element (as stored)',
                    'Namespace', 'Query', 'Event Filter', 'Consumer', 'Account', 'Process ID',
                    'Client Machine', 'Provider', 'Possible Cause', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'WMI Event Subscription Events', event_ids=set(_SUBSCRIPTION_EVENTS),
        provider=_PROVIDER)
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, record.user_data_name,
            record.get('NamespaceName') or record.get('Namespace'), record.get('Query'),
            record.get('ESS'), record.get('CONSUMER'), record.get('User'),
            record.get('Processid') or record.get('processid'),
            record.get('ClientMachine') or record.get('MachineName'),
            record.get('Provider') or record.get('providerName'),
            record.get('PossibleCause'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def wmiProviderActivity(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event Element (as stored)',
                    'Provider Name', 'Provider Path', 'Host Process', 'Operation', 'Account',
                    'Process ID', 'Client Machine', 'Component', 'Result Code',
                    'Possible Cause', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'WMI Provider and Operation Failure Events',
        event_ids=set(_PROVIDER_EVENTS), provider=_PROVIDER)
    data_list = []
    for record in records:
        if record.event_id == '5857':
            process_id, result = record.get('ProcessID'), record.get('Code')
        else:
            process_id, result = record.get('ClientProcessId'), record.get('ResultCode')
        data_list.append((
            record.time, record.event_id, record.user_data_name,
            record.get('ProviderName'), record.get('ProviderPath'), record.get('HostProcess'),
            record.get('Operation'), record.get('User'), process_id,
            record.get('ClientMachine'), record.get('Component'), result,
            record.get('PossibleCause'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
