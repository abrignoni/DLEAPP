"""Windows Remote Desktop client (RDPClient) Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-TerminalServices-RDPClient/Operational, written by the
TerminalServices-ClientActiveXCore provider: connection attempts (1024, 1102),
connection and domain events (1025, 1027), disconnections (1026) and the user
name hash event (1029). Event IDs, field names and message text are sourced in
the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-TerminalServices-RDPClient%4Operational.evtx'

# Message text from the TerminalServices-ClientActiveXCore manifest (see notes).
_EVENTS = {
    '1024': 'RDP ClientActiveX is trying to connect to the server',
    '1025': 'RDP ClientActiveX has connected to the server',
    '1026': 'RDP ClientActiveX has been disconnected',
    '1027': 'Connected to domain with session',
    '1029': 'Base64(SHA256(UserName))',
    '1102': 'The client has initiated a multi-transport connection to the server',
}

__artifacts_v2__ = {
    "rdpClientConnections": {
        "name": "Remote Desktop Client Connections",
        "description": "Outbound Remote Desktop client events from the RDPClient "
                       "Operational log: the server each connection attempt names, "
                       "disconnect reason codes, domain and session, and the user "
                       "name hash the client records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from "
                 "Microsoft-Windows-TerminalServices-RDPClient%4Operational.evtx, named in "
                 "the report's located-at line; only records of the "
                 "Microsoft-Windows-TerminalServices-ClientActiveXCore provider with Event "
                 "ID 1024, 1025, 1026, 1027, 1029 or 1102 are read. Event is the provider "
                 "manifest's message for each (manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-TerminalServices-ClientActiveXCore.xml#L816-L877, "
                 "#L893-L907 and #L1024-L1040). Server is the Value field of 1024 ('RDP "
                 "ClientActiveX is trying to connect to the server') and 1102 ('The client "
                 "has initiated a multi-transport connection to the server'). Disconnect "
                 "Reason (as stored) is the Value field of 1026, a number for which the "
                 "published manifest dump carries no names. Domain and Session ID are the "
                 "DomainName and SessionId of 1027 ('Connected to domain (%1) with session "
                 "%2.'). User Name Hash is the TraceMessage of 1029, whose manifest "
                 "message is 'Base64(SHA256(UserName)) is = %1'; on pc_mus_001_win11 it "
                 "held one or two base64 strings joined by a hyphen, or a hyphen alone on "
                 "2 of 33 rows, and the user name that was hashed is not recorded. User "
                 "SID is the SID in the record's Security element and Process ID the "
                 "process ID in its Execution element; User SID held one value on all 108 "
                 "rows of pc_mus_001_win11. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores and held one value on every row of pc_mus_001_win11. "
                 "af_case2_win10 and lonewolf_win10 carry no RDPClient Operational log. "
                 "Not reported: the log's other events (226, 1028, 1105, 1401 and 1402 on "
                 "pc_mus_001_win11). A record python-evtx cannot render, or whose XML does "
                 "not parse, is counted in the run log and not reported; every record in "
                 "this log rendered on the registered images. A connection attempt does "
                 "not by itself establish that a session was established or who was at the "
                 "keyboard. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-TerminalServices-RDPClient%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 108 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no RDPClient Operational log on the image)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no RDPClient Operational log on the image)",
        },
    },
}


@artifact_processor
def rdpClientConnections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Server',
                    'Disconnect Reason (as stored)', 'Domain', 'Session ID',
                    'User Name Hash', 'User SID', 'Process ID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Remote Desktop Client Connections', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-TerminalServices-ClientActiveXCore')
    data_list = []
    for record in records:
        server = reason = ''
        if record.event_id in ('1024', '1102'):
            server = record.get('Value')
        elif record.event_id == '1026':
            reason = record.get('Value')
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], server, reason,
            record.get('DomainName'), record.get('SessionId'),
            record.get('TraceMessage') if record.event_id == '1029' else '',
            record.user_sid, record.process_id, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
