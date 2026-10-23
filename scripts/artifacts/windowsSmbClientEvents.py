"""Connections the Windows SMB client logged in its Connectivity event log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

import base64
import binascii
import ipaddress
import struct

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import hex_status, read_event_records

_LABEL = 'SMB Client Connection Events'
_LOG = 'microsoft-windows-smbclient%4connectivity.evtx'
_PROVIDER = 'Microsoft-Windows-SMBClient'

# Event ID: the first line of the provider's message for it, without its closing period or colon (see notes).
# 30833 is in neither manifest read.
_EVENTS = {
    '30800': 'The server name cannot be resolved',
    '30803': 'Failed to establish a network connection',
    '30804': 'A network connection was disconnected',
    '30805': 'The client lost its session to the server',
    '30806': 'The client re-established its session to the server',
    '30807': 'The connection to the share was lost',
    '30808': 'The connection to the share was re-established',
    '30828': 'The client established its session to the server',
    '30829': 'The client failed to establish its session to the server',
    '30830': 'The SMB redirector selected the connection initiated with the following parameters',
    '30833': '',
}

__artifacts_v2__ = {
    "smbClientConnectionEvents": {
        "name": "SMB Client Connection Events",
        "description": "Eleven Microsoft-Windows-SMBClient events of the SmbClient Connectivity event log that name a "
                       "server or share this computer's SMB client tried to reach: a name that could not be "
                       "resolved, a connection that failed, was selected or was lost, and a session or share "
                       "connection, with the server's address when the record holds one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-11",
        "last_update_date": "2026-10-11",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-SmbClient%4Connectivity.evtx the paths match with python-evtx and "
                 "reports, one row per record, the records whose provider is Microsoft-Windows-SMBClient and whose "
                 "Event ID is 30800, 30803 to 30808, 30828, 30829, 30830 or 30833. Event is the first line of the "
                 "message the provider's manifest gives the event, without its closing period or colon, as "
                 "registered on Windows 11 build 26100.1742 and published in nasbench's EVTX-ETW-Resources "
                 "repository "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-SMBClient.xml, "
                 "events starting at lines 2314, 2383, 2525, 2590, 2619, 2679, 2709, 3316, 3343 and 3372); the "
                 "manifest that repository publishes for Windows 10 build 16299.15 gives 30800 and 30803 to 30808 "
                 "the same first lines "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-SMBClient.xml). "
                 "Neither manifest has an event 30833: its rows have an empty Event and what it records is not "
                 "sourced here. Server or Share Name is the field ServerName, which the messages print as the server "
                 "name and, for 30807 and 30808, as the share name. Server Address is the field RemoteAddress, or "
                 "Address in the events that name it so, and Client Address is LocalAddress. The manifest types them "
                 "as binary socket addresses; python-evtx renders a binary field as base64 "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1359-L1360), "
                 "and the bytes are read in the member order Microsoft documents for the SOCKADDR_IN and "
                 "SOCKADDR_IN6 structures, family, port, then the IPv4 address, or flow information and the IPv6 "
                 "address; the scope ID that follows the IPv6 address is not shown "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/656e9656bfaef34dd29cd7ee9e1146aec17e924c/sdk-api-src/content/ws2def/ns-ws2def-sockaddr_in.md#L62-L70 "
                 "and "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/656e9656bfaef34dd29cd7ee9e1146aec17e924c/sdk-api-src/content/ws2ipdef/ns-ws2ipdef-sockaddr_in6_lh.md#L62-L74), "
                 "with the family numbers 2 and 23 "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/656e9656bfaef34dd29cd7ee9e1146aec17e924c/sdk-api-src/content/winsock2/nf-winsock2-socket.md#L87-L88 "
                 "and #L143-L144), and shown as address:port, or [address]:port for IPv6. Those pages say that all "
                 "the data but the family is in network byte order (lines 82 to 83 of the first structure page and "
                 "176 to 177 of the second); they do not give the members' sizes. The reading used, two bytes each "
                 "for the family and the port, is checked against the known data below for IPv4. The IPv6 reading, "
                 "four bytes of flow information before the address, was not exercised by a step: the 52 IPv6 rows "
                 "are earlier records that all decode to the loopback address on port 445. Bytes that are all zero "
                 "give an empty cell, and any other content is shown as the base64 text python-evtx renders. A port "
                 "is shown without its protocol. Status is the field Status: a number is shown in hexadecimal with "
                 "the decimal python-evtx renders in parentheses, and that of 30830, which the manifest types as a "
                 "hexadecimal number and python-evtx renders as 0x text, is shown as rendered. Connection Type, "
                 "Reason, Session ID and Tree ID are the fields ConnectionType, Reason, SessionId and TreeId as "
                 "python-evtx renders them; what the numbers of Connection Type and Reason stand for is not sourced "
                 "here. Signing Used and Encryption Used are the fields of those names; in the tested logs only "
                 "30833 carries them, and the Windows 11 manifest also gives them to version 3 of 30806 and 30808. "
                 "Instance Name is InstanceName. A column whose field the record does not carry is blank. Event Time "
                 "(UTC) is the record's TimeCreated SystemTime, Event Version the record's Version, and Record ID "
                 "and Computer its EventRecordID and Computer. windows11_arm_smb_known_20261011 is known data from a "
                 "Windows 11 build 26200 virtual machine: with net use, a share was tried on the made-up host name "
                 "dleapp-no-such-host, then on 10.211.55.250, an address where nothing answers, and then the "
                 "machine's own C$ share was connected over 127.0.0.1 and disconnected, and the log was exported. Of "
                 "its 854 rows 7 were written during the session: one 30800 naming the made-up host, 1.3 seconds "
                 "after that step began; two 30803 naming 10.211.55.250, whose Server Address is 10.211.55.250:443 "
                 "on the first, with Connection Type 4, and 10.211.55.250:445 on the second, with Connection Type 1; "
                 "UDP 443 and TCP 445 are the port numbers version 2 of the 30803 message names, and the two records "
                 "are versions 4 and 3, whose message names no number; one 30830 with Server Address 127.0.0.1:445, "
                 "inside the 0.07 seconds the connecting command took; two 30833 in the same second, naming the IPC$ "
                 "and C$ shares of 127.0.0.1 with the same Session ID; and one 30800 written 0.6 seconds before the "
                 "script's first log entry, naming the host of the shared folder the script was started from. The "
                 "second step also wrote one 30827, which this artifact does not report. No record was written "
                 "between the disconnect and the export 10 seconds later. The other 847 rows are that machine's "
                 "earlier use: 795 of 30800, 18 of 30830 and 34 of 30833, and on 52 of them Server Address is an "
                 "IPv6 address. Client Address is empty on all 854 rows: LocalAddress is 16 zero bytes in the 2 "
                 "records of 30803, empty in the 19 of 30830 and absent from the other 833. Computer held one value "
                 "on all 854. On lonewolf_win10 the 3 rows are 30803 records of version 2 written within two "
                 "seconds, each with a Server Address on port 445; Client Address, Session ID, Tree ID, Signing Used "
                 "and Encryption Used are empty on all 3, and Event ID, Event, Connection Type, Status, Reason, "
                 "Instance Name, Event Version and Computer each held one value on all 3. pc_mus_001_win11, "
                 "af_case2_win10 and szechuan_win10 have the log, with 406, 83 and 31 records, none of them one this "
                 "artifact reports. Not read: the provider's other events. Among them are 30810 to 30813, a TCP/IP "
                 "or TDI transport interface added or deleted, which together are most of the records in every "
                 "tested log (8,457 of 9,312 in the known data, 579 of 582 on lonewolf_win10 and every record of the "
                 "other three); 30812 and 30813 keep the interface name in a field named ServerName. Also not read "
                 "are other events that carry a server name, among them 30809, 30816, 30822 to 30825 and 30827. Not "
                 "exercised on real data: 30828 and 30829. 30804 to 30808 occur only on ou_ransomware_server2022 (version 2) "
                 "and version 0 of 30803 only on szechuan_dc01_server2012r2. A row shows that the "
                 "SMB client logged the event for that name, not that a share was opened or a file was read; 30800 "
                 "and 30803 are failures. For a log marked dirty, scripts/windows_evtx.py also reads the records of "
                 "intact chunks after the chunks its header counts, and the run log says how many records came from "
                 "there. Reading needs the python-evtx package (pip install python-evtx)."
                 " On evtx_baseline_nextron_085_win2022_ad Server Address was empty on its one row, a 30800 record, "
                 "which carries no RemoteAddress or Address field.",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-SmbClient%4Connectivity.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_smb_known_20261011": "Windows 11 build 26200 | 854 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 1 row",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 6 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 162 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1,913 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the matched logs hold no records)",
        },
    },
}

_AF_INET = 2
_AF_INET6 = 23


def socket_address(text):
    """A socket address python-evtx rendered as base64, as 'address:port' for IPv4 and '[address]:port' for IPv6.

    The structure starts with a 16-bit address family in the machine's byte order and a 16-bit port, high byte
    first; an IPv4 address follows in 4 bytes, and for IPv6 4 bytes of flow information and then the address in
    16 bytes. '' for no text and for bytes that are all zero; any other content, and text that is not base64, is
    shown as stored.
    """
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error):
        return text
    if not any(raw):
        return ''
    if len(raw) >= 8 and struct.unpack_from('<H', raw)[0] == _AF_INET:
        return f'{ipaddress.IPv4Address(raw[4:8])}:{struct.unpack_from(">H", raw, 2)[0]}'
    if len(raw) >= 24 and struct.unpack_from('<H', raw)[0] == _AF_INET6:
        return f'[{ipaddress.IPv6Address(raw[8:24])}]:{struct.unpack_from(">H", raw, 2)[0]}'
    return text


def smb_row(record):
    get = record.get
    return (record.time, record.event_id, _EVENTS[record.event_id], get('ServerName'),
            socket_address(get('RemoteAddress') or get('Address')), socket_address(get('LocalAddress')),
            get('ConnectionType'), hex_status(get('Status')), get('Reason'), get('SessionId'), get('TreeId'),
            get('SigningUsed'), get('EncryptionUsed'), get('InstanceName'), record.version, record.record_id,
            record.computer)


@artifact_processor
def smbClientConnectionEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Server or Share Name',
                    'Server Address', 'Client Address', 'Connection Type (as stored)', 'Status',
                    'Reason (as stored)', 'Session ID (as stored)', 'Tree ID (as stored)', 'Signing Used',
                    'Encryption Used', 'Instance Name', 'Event Version', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [smb_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
