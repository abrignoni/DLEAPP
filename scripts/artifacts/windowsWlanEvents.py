"""Windows WLAN AutoConfig Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-WLAN-AutoConfig/Operational: wireless connection
succeeded and disconnected (8001, 8003) and association started and succeeded
(11000, 11001), with the SSID, profile, authentication and encryption each
record stores. Event IDs, field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-WLAN-AutoConfig%4Operational.evtx'

# Message text from the WLAN-AutoConfig provider manifest (see notes).
_EVENTS = {
    '8001': 'WLAN AutoConfig service has successfully connected to a wireless network',
    '8003': 'WLAN AutoConfig service has successfully disconnected from a wireless network',
    '11000': 'Wireless network association started',
    '11001': 'Wireless network association succeeded',
}

__artifacts_v2__ = {
    "wlanConnections": {
        "name": "WLAN Connection Events",
        "description": "Wireless connection, disconnection and association events "
                       "from the WLAN-AutoConfig Operational log, with the SSID, "
                       "profile, authentication and encryption each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-WLAN-AutoConfig%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-WLAN-AutoConfig "
                 "records with Event ID 8001, 8003, 11000 or 11001 are read. Event is the "
                 "first sentence of the provider manifest's message for each (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WLAN-AutoConfig.xml#L568-L607, "
                 "#L643-L675 and #L970-L1034). SSID, BSS Type and Connection ID are SSID, "
                 "BSSType and ConnectionId; Profile Name, Connection Mode and PHY Type are "
                 "ProfileName, ConnectionMode and PHYType, which 8001 carries (8003 "
                 "carries the first two); Authentication and Encryption are "
                 "AuthenticationAlgorithm and CipherAlgorithm on 8001 and Auth and Cipher "
                 "on 11000; Disconnect Reason is the Reason text of 8003; Local MAC "
                 "Address is LocalMac on 11000 and 11001, which the manifest's messages "
                 "label 'Local MAC Address'; Adapter and Interface GUID are "
                 "InterfaceDescription and InterfaceGuid on 8001 and 8003 and Adapter and "
                 "DeviceGuid on 11000 and 11001. Every value is reported as stored. None "
                 "of these events carries a BSSID field in the manifest, so no access "
                 "point hardware address is reported. SSID, BSS Type, Adapter and "
                 "Interface GUID each held one value on every row of pc_mus_001_win11 and "
                 "lonewolf_win10. Disconnect Reason is empty on lonewolf_win10, which "
                 "carries no 8003 records. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of pc_mus_001_win11 "
                 "and two values on lonewolf_win10. af_case2_win10 carries no "
                 "WLAN-AutoConfig Operational log. Not reported: the log's other events "
                 "(8000, 11004, 11005 and 11010 on the registered images). A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in "
                 "the run log and not reported; every record in this log rendered on the "
                 "registered images. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-WLAN-AutoConfig%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 45 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 9 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no WLAN-AutoConfig Operational log on the image)",
        },
    },
}


@artifact_processor
def wlanConnections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'SSID',
                    'Profile Name', 'Authentication', 'Encryption', 'BSS Type', 'PHY Type',
                    'Connection Mode', 'Disconnect Reason', 'Local MAC Address', 'Adapter',
                    'Interface GUID', 'Connection ID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'WLAN Connection Events', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-WLAN-AutoConfig')
    data_list = []
    for record in records:
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], record.get('SSID'),
            record.get('ProfileName'),
            record.get('AuthenticationAlgorithm') or record.get('Auth'),
            record.get('CipherAlgorithm') or record.get('Cipher'), record.get('BSSType'),
            record.get('PHYType'), record.get('ConnectionMode'), record.get('Reason'),
            record.get('LocalMac'),
            record.get('InterfaceDescription') or record.get('Adapter'),
            record.get('InterfaceGuid') or record.get('DeviceGuid'),
            record.get('ConnectionId'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
