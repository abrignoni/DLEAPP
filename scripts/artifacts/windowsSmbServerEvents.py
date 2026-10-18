"""Events the Windows SMB server logged whose manifest template names a client, a user or a file on a share, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

from scripts.artifacts.windowsSmbClientEvents import socket_address
from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import hex_status, read_event_records

_LABEL = 'SMB Server Client Events'
_PROVIDER = 'Microsoft-Windows-SMBServer'
_LOGS = ('microsoft-windows-smbserver%4operational.evtx', 'microsoft-windows-smbserver%4security.evtx',
         'microsoft-windows-smbserver%4audit.evtx', 'microsoft-windows-smbserver%4connectivity.evtx')

# (Event ID, Version): the first line of the provider's message for that version, without its closing period
# (see notes). A version the table does not hold, and 4000, which no manifest read has, get an empty Event.
_EVENTS = {
    ('551', '1'): 'SMB Session Authentication Failure',
    ('551', '2'): 'SMB Session Authentication Failure',
    ('551', '3'): 'SMB Session Authentication Failure',
    ('658', '0'): 'File handle for file "%8\\%2" was invalidated by user %4 from computer %6',
    ('1000', '0'): 'S4U2Self authentication failure - The client could not be reauthenticated with S4U2Self to '
                   'obtain claims.  This may be expected if the account is not a domain account',
    ('1001', '0'): 'SRV Disabled - The SMB1 negotiate request fails due to SMB1 is disabled',
    ('1001', '1'): 'A client attempted to access the server using SMB1 and was rejected because SMB1 file sharing '
                   'support is disabled or has been uninstalled',
    ('1003', '0'): 'The server received an unencrypted message. Message was rejected',
    ('1003', '1'): 'The server received an unencrypted message from client when encryption was required. Message '
                   'was rejected',
    ('1004', '0'): 'The server received an incorrectly signed message. Message was rejected',
    ('1004', '1'): 'The server rejected an incorrectly signed message',
    ('1005', '0'): 'The server failed to validate negotiation from client %2. Connection was terminated',
    ('1005', '1'): 'The server rejected an invalid negotiation request. Connection was terminated',
    ('1005', '2'): 'Negotiate integrity check failed',
    ('1006', '0'): 'The share denied access to the client',
    ('1007', '0'): 'The share denied anonymous access to the client',
    ('1009', '0'): 'The server denied anonymous access to the client',
    ('1015', '0'): 'Decrypt call failed',
    ('1016', '0'): 'Reopen failed',
    ('1017', '0'): 'Handle scavenged',
    ('1020', '0'): 'File system operation has taken longer than expected',
    ('1020', '1'): 'File system operation has taken longer than expected',
    ('1046', '0'): 'The server received a request and the server requires encryption, but the server and client did '
                   'not negotiate an encryption cipher, nor does server allow unencrypted access',
    ('1054', '0'): 'Network operation has taken longer than expected',
    ('1061', '0'): 'SMB2 Request Negotiate Dialect Failure',
    ('1906', '0'): 'Session key for connection is weaker than required. Connection will be closed as a result',
    ('3000', '0'): 'SMB1 access',
    ('3002', '1'): 'A remote device attempted SMB1 connection to this computer',
    ('3021', '0'): "The SMB server observed that the client doesn't support signing",
    ('3022', '0'): "The SMB server observed that the client doesn't support encryption",
    ('3023', '0'): 'The SMB client was logged on as Guest account',
}
_EVENT_IDS = {event_id for event_id, _ in _EVENTS} | {'4000'}

__artifacts_v2__ = {
    "smbServerClientEvents": {
        "name": "SMB Server Client Events",
        "description": "Microsoft-Windows-SMBServer events of the SMB server's Operational, Security, Audit and "
                       "Connectivity event logs whose manifest template names the client, its address or a user, such "
                       "as a failed session authentication, a share that denied access or an SMB1 connection that "
                       "was rejected, with the share and file name when the record holds them. A record of a version "
                       "with no fields, such as the SMB1 rejection (1001 version 1), shows only that the event was "
                       "logged.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-SMBServer%4Operational.evtx, %4Security.evtx, %4Audit.evtx and "
                 "%4Connectivity.evtx the paths match with python-evtx and reports, one row per record, the records "
                 "whose provider is Microsoft-Windows-SMBServer and whose Event ID is 551, 658, 1000, 1001, 1003 to "
                 "1007, 1009, 1015, 1016, 1017, 1020, 1046, 1054, 1061, 1906, 3000, 3002, 3021, 3022, 3023 or 4000. "
                 "Those are the events of the provider's manifest, as registered on Windows 11 build 26100.1742 and "
                 "published in nasbench's EVTX-ETW-Resources repository "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-SMBServer.xml), "
                 "logged to those four channels whose template has a field ClientName, ClientAddress, UserName or "
                 "ComputerName, less 1012, plus 1017 and 4000. 1012 is left out because its message prints its "
                 "ClientAddress as the IP Address of a network name change, and the manifest's guidance for it names "
                 "failover, startup and network configuration (lines 3818 to 3851). 1017 has no client field and is "
                 "kept for its share and file name: its message says the server closed a handle previously reserved "
                 "for a client after 60 seconds (lines 3986 to 4019). 4000 is in none of the manifests read (that "
                 "one, and those the repository publishes at the same commit for Windows 7 SP1, Windows 8.1, Windows "
                 "10 1709, 1809 and 2004, Windows 11 22H2 and Windows Server 2012 R2, 2019 and 2022): its rows have "
                 "an empty Event and what it records is not sourced here; its fields are read by the names its "
                 "records carry. Not reported, though their templates name a share or a file: 604, 605, 1002, 1030, "
                 "1800, 1801 and 1912, which name no client or user. Event is the first line of the manifest's "
                 "message for the record's Event ID and version, without its closing period, with insertion markers "
                 "such as %2 kept as the manifest has them; a version that manifest does not list gives an empty "
                 "Event. In that manifest 551 versions 1 to 3 start at lines 2813, 2852 and 2895, 1001 versions 0 "
                 "and 1 at 3383 and 3400, 1016 at 3933 and 1020 versions 0 and 1 at 4075 and 4119. Of the other "
                 "manifests, that of Windows 7 SP1 gives version 0 of 1001 another first line, and those of Windows "
                 "8.1, Windows 10 and Windows Server 2012 R2 and 2019 give version 0 of 1003 and 1004 first lines "
                 "that add 'from client' and an insertion marker. Every field is read by the name the "
                 "record's event data carries, never by position, and a column whose field the record does not "
                 "carry is blank. Client Name is ClientName, or for 658 ComputerName, which its message prints as "
                 "the computer the user was from; the messages of 3000 and 3002 print their ClientName as the Client "
                 "Address. Client Address is ClientAddress, which the manifest types as a binary socket address; it "
                 "is decoded as the SMB Client Connection Events artifact decodes one, as address:port or "
                 "[address]:port, with an all-zero value blank and any other content shown as python-evtx renders "
                 "it. On all 64 rows of the "
                 "tested logs that have a Client Address, its address equals the Client Name without its leading "
                 "backslashes. What the port is, is not sourced here. User Name, Domain Name, Share Name, Share Path "
                 "and File Name are UserName, DomainName, ShareName, SharePath and FileName. Session ID is SessionId "
                 "or SessionID as python-evtx renders it. Status and Translated Status are Status and "
                 "TranslatedStatus: a number is shown in hexadecimal with the decimal python-evtx renders in "
                 "parentheses, and hexadecimal text is shown as rendered; the 551 message prints them as 'Status: "
                 "TranslatedStatus (Status)'. Status and Translated Status were identical on every tested row, and "
                 "empty on the rows of 1001, 1017, 1020 and 4000. Not shown: GUIDs, lengths, SPN, handle flags, "
                 "durations and the other fields of the reported events. Channel is the record's Channel, Event Time "
                 "(UTC) its TimeCreated SystemTime, and Event Version, Record ID and Computer its Version, "
                 "EventRecordID and Computer; Computer held one value on all rows of ou_ransomware_server2022, "
                 "evtx_baseline_nextron_085_win2022_ad and hexordia_mvs2025_win11, and the 2 rows of "
                 "evtx_baseline_nextron_085_win2022_0_20348_azure hold two values. Channel held "
                 "one value on all rows of ou_ransomware_server2022, evtx_baseline_nextron_085_win2022_ad and "
                 "hexordia_mvs2025_win11. Event ID, Event and Event Version held one value on all 10 rows of "
                 "evtx_baseline_nextron_085_win2022_ad, and Status and Translated Status held one value on all 10; "
                 "Event ID and Event Version held one value on all 12 rows of hexordia_mvs2025_win11. Rows in the "
                 "tested logs: on ou_ransomware_server2022 171, all from the Operational log: 124 of 1001 version 1, "
                 "which has no fields, so those rows show only that the record was written; 2 of 1016 and 39 of 1020 "
                 "version 1, each with a Client Name, Client Address, User Name, Share Name, File Name and Session "
                 "ID; and 6 of 1017 with a Share Name and File Name only. On evtx_baseline_nextron_085_win2022_ad 10 "
                 "rows of 551 version 3 from the Security log, and on evtx_baseline_nextron_085_win2022_0_20348_azure "
                 "1 such row and 1 of 1001 version 1; on those 11 rows of 551 User Name, Share Name and File Name "
                 "are empty, and on the first key Client Name held one value on all 10. On hexordia_mvs2025_win11 12 "
                 "rows of 4000 from the Connectivity log, each with a Client Name, an IPv6 Client Address that is the "
                 "loopback address, a Share Name and a Session ID, and with User Name, File Name, Status and "
                 "Translated Status empty; Client Name held one value on all 12. Domain Name and Share Path were "
                 "empty on every tested row: no 1000, 1006 or 1007 record was found. The Security log held records "
                 "on the two baseline keys above only, and the Audit log held none on any key. For every key whose logs were "
                 "matched (15 of the 16 in sample_data; the Windows 7 key has none) the record count per Event ID "
                 "was also taken with a second reader, the evtx crate's Python binding (pyevtx-rs, PyPI package "
                 "evtx 0.13.1), and the rows match it record for record by channel, Event ID, "
                 "EventRecordID and time to the second. Not exercised on real data: 658, 1000, 1003 to 1007, 1009, 1015, 1046, "
                 "1054, 1061, 1906, 3000, 3002, 3021, 3022, 3023, the versions not named above, and the IPv4 reading "
                 "of 4000. Not read: the provider's other events, which are most of the records of every tested Operational log "
                 "that holds records "
                 "(among them 1010 and 1011, endpoints added and removed, 1025 and 1027, configuration notices, and "
                 "1033, 1034, 1038 and 1040, RDMA endpoint notifications, whose messages name an interface or a "
                 "device and no client). A row shows that the SMB server logged the event, not that a file was read or "
                 "written; 551, 1006, 1007 and 1009 are refusals. For a log marked dirty, scripts/windows_evtx.py "
                 "also reads the records of intact chunks after the chunks its header counts, and the run log says "
                 "how many records came from there. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-SMBServer%4Operational.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-SMBServer%4Security.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-SMBServer%4Audit.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-SMBServer%4Connectivity.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "server",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the logs hold no records)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 2 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 10 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 12 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 171 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def smb_server_row(record):
    get = record.get
    return (record.time, record.event_id, _EVENTS.get((record.event_id, record.version), ''),
            get('ClientName') or get('ComputerName'), socket_address(get('ClientAddress')), get('UserName'),
            get('DomainName'), get('ShareName'), get('SharePath'), get('FileName'),
            get('SessionId') or get('SessionID'), hex_status(get('Status')), hex_status(get('TranslatedStatus')),
            record.channel, record.version, record.record_id, record.computer)


@artifact_processor
def smbServerClientEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Client Name', 'Client Address',
                    'User Name', 'Domain Name', 'Share Name', 'Share Path', 'File Name', 'Session ID (as stored)',
                    'Status', 'Translated Status', 'Channel', 'Event Version', 'Record ID', 'Computer')
    data_list = []
    sources = []
    for log in _LOGS:
        records, read = read_event_records(context, log, _LABEL, event_ids=_EVENT_IDS, provider=_PROVIDER)
        data_list.extend(smb_server_row(record) for record in records)
        sources.extend(read)
    return data_headers, data_list, '\n'.join(sources)
