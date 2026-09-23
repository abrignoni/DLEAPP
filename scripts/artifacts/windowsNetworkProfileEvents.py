"""Windows NetworkProfile Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-NetworkProfile/Operational events 10000 (Network
Connected), 10001 (Network Disconnected) and 10002 (Network Category Changed),
each naming the network profile. Event IDs, field names and message text are
sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-NetworkProfile%4Operational.evtx'

# Message text from the NetworkProfile provider manifest (see notes).
_EVENTS = {
    '10000': 'Network Connected',
    '10001': 'Network Disconnected',
    '10002': 'Network Category Changed',
}

__artifacts_v2__ = {
    "networkProfileEvents": {
        "name": "Network Profile Connection Events",
        "description": "Network connected, disconnected and category changed events "
                       "from the NetworkProfile Operational log, with the network "
                       "name, description and profile GUID each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-NetworkProfile%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-NetworkProfile "
                 "records with Event ID 10000, 10001 or 10002 are read. Event is the first "
                 "line of the provider manifest's message for each: 'Network Connected', "
                 "'Network Disconnected' and 'Network Category Changed' (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-NetworkProfile.xml#L225-L299). "
                 "Network Name, Description and Profile GUID are the Name, Description and "
                 "Guid fields. Type (as stored), State (as stored) and Category (as "
                 "stored) are the Type, State and Category numbers, for which the "
                 "published manifest dump carries no names. Description held the same text "
                 "as Network Name on every row of the three registered images (39, 173 and "
                 "22 rows); whether the two can differ was not established. Type held one "
                 "value on every row of each registered image, and Category held one value "
                 "on every row of pc_mus_001_win11 and lonewolf_win10. Event Time (UTC) is "
                 "the record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Not reported: the "
                 "log's other events (4001, 4002, 4003, 4004 and 20002 on the registered "
                 "images). A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported; every record in this "
                 "log rendered on the registered images. A row names the network profile "
                 "the event records; it does not by itself establish which account or "
                 "program used the connection. Reading needs the python-evtx package (pip "
                 "install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-NetworkProfile%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 39 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 173 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 22 rows",
                       },
    },
}


@artifact_processor
def networkProfileEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Network Name',
                    'Description', 'Profile GUID', 'Type (as stored)', 'State (as stored)',
                    'Category (as stored)', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Network Profile Connection Events', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-NetworkProfile')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], record.get('Name'),
            record.get('Description'), record.get('Guid'), record.get('Type'),
            record.get('State'), record.get('Category'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
