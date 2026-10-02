"""Windows Remote Desktop core connection event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads eight Microsoft-Windows-RemoteDesktopServices-RdpCoreTS events of the
RdpCoreTS Operational event log: the server accepted a connection from a client
address (131), a connection was created (65) and assigned to a session (66),
the client's timezone (104), the disconnect reason (103), the server ended the
main connection (102), and the two events that name a client address after a
protocol error (139) or a wrong user name or password (140). The Event IDs,
field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Remote Desktop Core Connection Events'
_LOG = 'microsoft-windows-remotedesktopservices-rdpcorets%4operational.evtx'
_PROVIDER = 'Microsoft-Windows-RemoteDesktopServices-RdpCoreTS'

# Event ID: a short label made of words of the provider's message for it (see notes).
_EVENTS = {
    '65': 'Connection created',
    '66': 'The connection was assigned to session',
    '102': 'The server has terminated main RDP connection with the client',
    '103': 'The disconnect reason is',
    '104': 'Client timezone hour from UTC',
    '131': 'The server accepted a new connection from client',
    '139': 'The server security layer detected an error in the protocol stream and the client has been '
           'disconnected',
    '140': 'A connection from the client computer failed because the user name or password is not '
           'correct',
}
# The field that holds the client address, by Event ID.
_ADDRESS_FIELD = {'131': 'ClientIP', '139': 'IPString', '140': 'IPString'}

__artifacts_v2__ = {
    "rdpCoreConnectionEvents": {
        "name": "Remote Desktop Core Connection Events",
        "description": "Microsoft-Windows-RemoteDesktopServices-RdpCoreTS events of the RdpCoreTS Operational event "
                       "log: the Remote Desktop server accepted a connection from a client address (131), created a "
                       "connection (65) and assigned it to a session (66), recorded the client's timezone (104) and "
                       "the disconnect reason (103), ended the main connection (102), disconnected a client address "
                       "after a protocol error (139) or failed a connection from one over the user name or password "
                       "(140), each with the Activity ID the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-RemoteDesktopServices-RdpCoreTS%4Operational.evtx the paths match "
                 "with python-evtx and reports, one row per record, the records whose provider is "
                 "Microsoft-Windows-RemoteDesktopServices-RdpCoreTS and whose Event ID is 65, 66, 102, 103, 104, "
                 "131, 139 or 140. The provider's manifest sends the eight events to the "
                 "Microsoft-Windows-RemoteDesktopServices-RdpCoreTS/Operational channel with the messages 'The "
                 "server accepted a new %1 connection from client %2.' (131, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L673-L688), "
                 "'Connection %1 created' (65, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L352-L366), "
                 "'The connection %1 was assigned to session %2' (66, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L367-L382), "
                 "'Client timezone is %1 hour from UTC;' (104, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L591-L605), "
                 "'The disconnect reason is %1' (103, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L576-L590), "
                 "'The server has terminated main RDP connection with the client.' (102, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L564-L575), "
                 "'The server security layer detected an error (%1) in the protocol stream and the client (Client "
                 "IP:%2) has been disconnected.' (139, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L800-L815) "
                 "and 'A connection from the client computer with an IP address of %1 failed because the user name "
                 "or password is not correct.' (140, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml#L816-L830). "
                 "These are the entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository; the manifests that repository publishes for "
                 "Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same eight entries at the same lines "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-RemoteDesktopServices-RdpCoreTS.xml). "
                 "Event is a short label made of words of that message, in the message's order. Client Address (as "
                 "stored) is the field ClientIP of 131 and IPString of 139 and 140, Connection Type is ConnType "
                 "(131), Connection Name is ConnectionName (65 and 66), Session ID is SessionID (66), Reason Code "
                 "(as stored) is ReasonCode (103), Client Timezone (as stored) is TimezoneBiasHour (104) and Result "
                 "Code (as stored) is ResultCode (139). Each is as python-evtx renders it with any white space at "
                 "either end removed (no tested value had any), and a column whose field the record does not carry "
                 "is blank. Activity ID is the ActivityID of the record's Correlation element, a GUID that "
                 "python-evtx renders in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376), "
                 "and is blank when the record has none. Event Time (UTC) is the record's TimeCreated SystemTime, "
                 "which python-evtx renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "szechuan_win10, the public DFIR Madness Szechuan Sauce desktop image (Windows 10 build 19041). "
                 "None of af_case2_win10, lonewolf_win10 and pc_mus_001_win11 holds the log file. The tested log "
                 "held 131 records, all of this provider, and 7 are reported: 2 of 131 and 1 each of 65, 66, 102, "
                 "103 and 104, each reported record version 0. The log held no 139 and no 140 record, so those two "
                 "events are unexercised and read as the manifest describes them, and Result Code (as stored) is "
                 "blank on every row. The first 131 row is a TCP connection from 10.42.85.10:62514 and the second, "
                 "28 seconds later, a UDP connection from [10.42.85.10]:63121: the address is reported in the form "
                 "the record stores, with its port and, on the UDP row, its square brackets. 6 of the 7 rows carry "
                 "the Activity ID of the TCP 131 row (131, 65, 104, 66, 103 and 102, in that order); the UDP 131 row "
                 "carries another. Connection Name was RDP-Tcp#0 on both rows that have one, Session ID 3, Reason "
                 "Code (as stored) 12 and Client Timezone (as stored) [-8], square brackets included. What a reason "
                 "code stands for is not looked up, and whether the timezone number counts hours ahead of UTC or "
                 "behind it is not established here. Two other artifacts' rows from the same image line up with "
                 "these. Windows Remote Desktop Connections reports a 261 (listener received a connection) 4 "
                 "milliseconds after the TCP 131 row and a 1149 (user authentication succeeded) from 10.42.85.10 "
                 "less than 1 millisecond after the 104 row. Windows Terminal Services Sessions reports a session "
                 "logon (21) for session 3 from 10.42.85.10 2.6 seconds after the 66 row, its only 21 row from that "
                 "address, and a disconnect (24) of session 3 6 milliseconds after the 102 row. Rows are in the "
                 "order the log file holds its records, which was rising Record ID and time on the tested log. "
                 "Computer held one value. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record of the tested log rendered. A log marked "
                 "dirty is read past the chunks its header counts, and the run log says how many records came from "
                 "there; the tested log is marked dirty and 1 of the 7 rows, Record ID 119, came from there. Reading "
                 "needs the python-evtx package (pip install python-evtx). Not read: the provider's other events. "
                 "The tested log holds 124 records of 24 other Event IDs.",
        "paths": ('*/Windows/System32/winevt/Logs/'
                  'Microsoft-Windows-RemoteDesktopServices-RdpCoreTS%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
        },
    },
}


def connection_row(record):
    event_id = record.event_id
    address = record.get(_ADDRESS_FIELD[event_id]) if event_id in _ADDRESS_FIELD else ''
    return (record.time, event_id, _EVENTS[event_id], address, record.get('ConnType'),
            record.get('ConnectionName'), record.get('SessionID'), record.get('ReasonCode'),
            record.get('TimezoneBiasHour'), record.get('ResultCode'), record.activity_id,
            record.record_id, record.computer)


@artifact_processor
def rdpCoreConnectionEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Client Address (as stored)',
                    'Connection Type', 'Connection Name', 'Session ID', 'Reason Code (as stored)',
                    'Client Timezone (as stored)', 'Result Code (as stored)', 'Activity ID', 'Record ID',
                    'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [connection_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
