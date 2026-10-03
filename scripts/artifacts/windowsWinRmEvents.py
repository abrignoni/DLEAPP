"""WinRM event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-WinRM record of the provider's Operational event log: WS-Management sessions, shells and
operations as the Windows Remote Management client and service log them, with each record's fields, activity ID and
process ID. The Event IDs, the message text and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'WinRM Events'
_LOG = 'Microsoft-Windows-WinRM%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-WinRM'

# Event ID: the first sentence of the provider's message for it, placeholders as written (see notes).
_EVENTS = {
    '2': 'Initializing WSMan API',
    '3': 'Initialization of WSMan API failed, error code %1',
    '4': 'Deinitializing WSMan API',
    '5': 'Deinitialization of WSMan API failed, error code %1',
    '6': 'Creating WSMan Session.',
    '7': 'WSMan Create Session operation failed, error code %1',
    '8': 'Closing WSMan Session',
    '9': 'Closing WSMan Session failed, error code %1',
    '10': 'Setting WSMan Session Option (%1) - %2 with value (%3) completed successfully.',
    '11': 'Creating WSMan shell with the ResourceUri: %1 and ShellId: %2',
    '12': 'WSMan shell creation failed, error code %1',
    '13': 'Running WSMan command with CommandId: %1',
    '14': 'Running WSMan command failed, error code %1',
    '15': 'Closing WSMan command',
    '16': 'Closing WSMan shell',
    '28': 'Access Denied error: the %1 API caller does not match the creator of the application object',
    '29': 'Initialization of WSMan API completed successfuly',
    '30': 'Deinitialization of WSMan API completed successfuly',
    '31': 'WSMan Create Session operation completed successfuly',
    '32': 'Setting WSMan Session Option (%1) - %2 failed, error code %3.',
    '33': 'Closing WSMan Session completed successfuly',
    '37': 'Closing WSMan shell failed, error code %1',
    '38': 'Closing WSMan command failed, error code %1',
    '40': 'Closing WSMan %1 operation failed, error code %2',
    '41': 'The WinRM protocol handler has began loading for application %1.',
    '42': 'The WinRM protocol handler completed unloading.',
    '43': 'The WinRM protocol handler unloaded prematurely due to the following error: %2.',
    '44': 'The WinRM protocol handler started to create a session at the following destination: %1.',
    '45': 'The WinRM protocol handler closed the session.',
    '46': 'The WinRM protocol session closed prematurely due to the following error: %2.',
    '47': 'The WinRM protocol session began an operation of type %1 to the server.',
    '48': 'The WinRM protocol session successfully completed the operation.',
    '49': 'The WinRM protocol operation failed due to the following error: %2.',
    '84': 'The maximum number of users (%1) executing shell operations has been exceeded.',
    '85': 'The %1 user is allowed a maximum number of %2 concurrent shells, which has been exceeded.',
    '86': 'The WSMan service could not launch a host process to process the given request.',
    '87': 'The WSMan host process was unexpectedly terminated.',
    '90': 'RunAs was disabled by Group Policy; WSMan service has erased all RunAs credentials.',
    '91': 'Creating WSMan shell on server with ResourceUri: %1',
    '131': 'Received redirect status code from Network layer; status: 302 (HTTP_STATUS_REDIRECT); location: %1',
    '132': 'WSMan operation %1 completed successfully',
    '135': 'Re-sending the request as a result of ERROR_WINHTTP_CANNOT_CONNECT, using next proxy',
    '136': 'Re-sending the request as a result of ERROR_WINHTTP_NAME_NOT_RESOLVED, using next proxy',
    '137': 'Network layer returned ERROR_WINHTTP_NAME_NOT_RESOLVED - The server name cannot be resolved.',
    '138': 'The client got a timeout from the network layer (ERROR_WINHTTP_TIMEOUT)',
    '139': 'The client got a login failure from the network layer (ERROR_WINHTTP_LOGIN_FAILURE)',
    '142': 'WSMan operation %1 failed, error code %2',
    '145': 'WSMan operation %1 started with resourceUri %2',
    '161': '%1',
    '162': 'Authenticating the user failed.',
    '163': 'The authentication mechanism (%1) requested by the client is not supported by the server.',
    '164': "The destination computer (%1) returned an 'access denied' error.",
    '165': 'The authentication mechanism requested by the proxy is not supported by the client.',
    '171': 'Authenticating the user with the proxy failed.',
    '172': 'The server certificate on the destination computer (%1:%2) has the following errors: %3 %4 %5 %6 '
           '%7 %8 %9 %10.',
    '173': 'The WinRM service has terminated %1 unauthenticated connections over the past %2 minutes to '
           'maintain healthy system state.',
    '192': 'The authorization of the user failed with error %1',
    '193': 'Request for user %1 (%2) will be executed using WinRM virtual account %3 (%4)',
    '208': 'The Winrm service is starting',
    '209': 'The Winrm service started successfully',
    '210': 'The WinRM service is unable to start because of a failure during initialization.',
    '211': 'The Winrm service is stopping',
    '212': 'The Winrm service was stopped successfully',
    '213': 'The WSMan service could not load current configuration settings as the settings are corrupted.',
    '214': 'The WSMan client could not load current configuration settings as the settings are corrupted.',
    '215': 'The WSMan service failed to read configuration of the following plugin: %1.',
    '216': 'The WSMan service failed to restart the plugins marked for AutoRestart.',
    '217': 'The WSMan service failed to restart the %1 plugin on service startup.',
    '218': 'The WSMan service successfully restarted the following plugin on service startup: %1.',
    '219': 'The WSMan shell instance %1 will no longer support disconnect reconnect functionality because a '
           'non-supported request was sent by the client.',
    '224': '%1',
    '229': 'The WinRM %1 failed to register for group policy change notifications.',
    '230': 'Deletion of registry key %1 resulted in access denied.',
    '254': 'Activity Transfer',
}


__artifacts_v2__ = {
    "winRmEvents": {
        "name": "WinRM Events",
        "description": "Microsoft-Windows-WinRM records of the provider's Operational event log, such as a "
                       "WS-Management operation started or failed and the WinRM service starting or stopping, with "
                       "each record's named fields, activity ID, related activity ID and process ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-03",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-WinRM%4Operational.evtx the paths match with python-evtx and reports, one row per record, every record whose provider is Microsoft-Windows-WinRM, whatever its Event ID. Microsoft's "
                 "Windows Remote Management page describes WinRM as its implementation of the WS-Management Protocol, 'a standard Simple Object Access Protocol (SOAP)-based, firewall-friendly protocol that allows hardware and "
                 "operating systems, from different vendors, to interoperate' (https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WinRM/portal.md?plain=1#L22). The provider's manifest of "
                 "Windows 11 build 26100.1742 sends 74 events to this log's channel, each version 0 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-WinRM.xml#L196-L1378), "
                 "and the manifests of Windows 10 builds 16299.15, 17763.107 and 19041.208 and Windows 11 build 22621.819 hold the same 74 with the same message, fields and level "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-WinRM.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-WinRM.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-WinRM.xml and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WinRM.xml). These are "
                 "the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the record's Event ID, the message's first sentence: the message with each run of white space made one space, cut after the first period"
                 " that a space or the end of the message follows, with its placeholders (such as %1) as the manifest writes them. A placeholder is an insertion string for a data item of the event's template by its position "
                 "(Microsoft's Defining Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) and is not filled in; the record's own values are in Fields. The whole message of "
                 "161 and of 224 is the placeholder %1. Event is blank for an Event ID outside the 74, which no tested record had. Fields lists every named field that holds more than white space as 'name: value', by the names the "
                 "record carries, in the record's order, joined with ' | '. Each value is as python-evtx renders it with any white space at either end removed; 6 tested values had some, the message field of the 6 rows of 224. A data "
                 "item that has no name is not shown, and no tested record had one. If a record named a field twice the last would be read. The tested records carried the field names and the level the manifest gives their event. "
                 "Activity ID is the ActivityID of the record's Correlation element, a GUID python-evtx renders lower case in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376); it is blank on the 9 rows of 208, which store none. On the tested logs each of the 72 rows of "
                 "142 and of the 14 rows of 132 shares its Activity ID with a row of 145, and each of the 72 rows of 161 shares its Activity ID with a row of 254. Related Activity ID is the RelatedActivityID of the record's "
                 "Correlation element, in the same form, which Microsoft's event schema describes as 'A globally unique identifier that identifies the activity to which control was transferred to' "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/eventschema-correlation-systempropertiestype-element.md?plain=1#L46); it is filled on the 72 rows of 254 and blank"
                 " on every other tested row, and on each of the 72 it equals the Activity ID of the 145 row before it. Process ID is the ProcessID of the record's Execution element; the record does not name the process. Tested on the"
                 " logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 122, 36, 168 and 32 rows in that order; the two captures "
                 "of a Windows 11 build 26200 machine hold no such log. Every image has rows of 145, 'WSMan operation %1 started with resourceUri %2' (27, 9, 42 and 8), 142, 'WSMan operation %1 failed, error code %2', 161 and 254, "
                 "'Activity Transfer' (13, 9, 42 and 8 of each). af_case2_win10 also has 14 rows of 132, 'WSMan operation %1 completed successfully', 9 each of 208, 'The Winrm service is starting', 209, 'The Winrm service started "
                 "successfully', 211, 'The Winrm service is stopping', and 212, 'The Winrm service was stopped successfully', and 6 of 224. The other 64 events are unexercised, among them 6, 'Creating WSMan Session.', and 91, "
                 "'Creating WSMan shell on server with ResourceUri: %1'. Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which can differ by microseconds "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). User SID is the UserID of the record's Security element. User SID held one value, "
                 "S-1-5-18, on lonewolf_win10, pc_mus_001_win11 and szechuan_win10; on af_case2_win10 it is S-1-5-18 on 56 rows, S-1-5-20 on the 36 rows of 208, 209, 211 and 212 and one S-1-5-21 account on 30 (12 of 145, 12 of 132 and"
                 " the 6 of 224). Record ID is the record's EventRecordID and Computer the machine name the record stores, which held one value on af_case2_win10 and pc_mus_001_win11, two on lonewolf_win10 and three on szechuan_win10."
                 " Rows are in the order the file holds them, which was rising Record ID on every tested log; in time order 1 row each of af_case2_win10 and lonewolf_win10 is earlier than the row before it. Every record of the tested "
                 "logs rendered and is the provider's. A record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not reported. A log marked dirty is read past the chunks its header counts, and the "
                 "run log says how many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not read: the events these manifests send to the provider's Analytic and Debug channels.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 122 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 36 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 168 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 32 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-WinRM%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
    },
}


def winrm_row(record):
    fields = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields if record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), fields, record.activity_id,
            record.related_activity_id, record.process_id, record.user_sid, record.record_id, record.computer)


@artifact_processor
def winRmEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Fields', 'Activity ID', 'Related Activity ID',
                    'Process ID', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [winrm_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
