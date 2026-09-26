"""Incoming Remote Desktop connection events from the TerminalServices-RemoteConnectionManager
log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "rdpConnections": {
        "name": "Windows Remote Desktop Connections",
        "description": "Incoming Remote Desktop events from the "
                       "TerminalServices-RemoteConnectionManager log: a listener receiving a "
                       "connection, user authentication succeeding with the user, domain and "
                       "source address, and connections accepted from an address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads "
                 "Microsoft-Windows-TerminalServices-RemoteConnectionManager%4Operational.evtx and "
                 "reports the records of the provider of that name with Event ID 261, 1149, 1150 "
                 "or 1158, one row per record; a record python-evtx cannot render, or whose XML "
                 "does not parse, is counted in the run log and skipped. Event is the message the "
                 "provider's manifest in termsrv.dll gives the ID, read from its English .mui, "
                 "without its fields; the messages were the same in the DLLs of the Szechuan Sauce "
                 "desktop image (build 19041) and pc_mus_001_win11 (build 22621): 261 'Listener %1 "
                 "received a connection', 1149 'Remote Desktop Services: User authentication "
                 "succeeded:' and 1150 'Remote Desktop Services: User config data have been "
                 "merged:', each followed by User, Domain and Source Network Address, and 1158 "
                 "'Remote Desktop Services accepted a connection from IP address %1.' User, Domain "
                 "and Source Network Address are the Param1, Param2 and Param3 fields of 1149 and "
                 "1150, which those messages print under those labels. For 1158 Source Network "
                 "Address is Param1, and Listener is the listenerName field of 261. Event Time "
                 "(UTC) is the record's TimeCreated, and Computer and Record ID are the record's "
                 "own. None of af_case2_win10, lonewolf_win10 and pc_mus_001_win11 holds the log "
                 "file. On the Szechuan Sauce desktop image (not a registered corpus key) it held "
                 "39 records and 2 are reported: a 261 for the RDP-Tcp listener and, 28 seconds "
                 "later, a 1149 for Administrator in domain C137 from 10.42.85.10. The "
                 "TerminalServices-LocalSessionManager log on that image, which the Windows "
                 "Terminal Services Sessions artifact reads, recorded a session logon for "
                 "C137\\Administrator from the same address 2.6 seconds after the 1149. 1150 and "
                 "1158 records are unexercised.",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-TerminalServices-RemoteConnectionManager%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "screen-share",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
        },
    },
}

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-TerminalServices-RemoteConnectionManager%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-TerminalServices-RemoteConnectionManager'

# Event ID -> the provider's message for it without its fields (notes).
_EVENTS = {
    '261': 'Listener received a connection',
    '1149': 'Remote Desktop Services: User authentication succeeded',
    '1150': 'Remote Desktop Services: User config data have been merged',
    '1158': 'Remote Desktop Services accepted a connection from IP address',
}


def connection_row(record):
    """The report row for one record."""
    user = domain = address = listener = ''
    if record.event_id in ('1149', '1150'):
        user, domain, address = record.get('Param1'), record.get('Param2'), record.get('Param3')
    elif record.event_id == '1158':
        address = record.get('Param1')
    elif record.event_id == '261':
        listener = record.get('listenerName')
    return (record.time, record.event_id, _EVENTS[record.event_id], user, domain, address,
            listener, record.computer, record.record_id)


@artifact_processor
def rdpConnections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User', 'Domain',
                    'Source Network Address', 'Listener', 'Computer', 'Record ID')
    records, sources = read_event_records(context, _LOG, 'Windows Remote Desktop Connections',
                                          event_ids=set(_EVENTS), provider=_PROVIDER)
    return data_headers, [connection_row(record) for record in records], '\n'.join(sources)
