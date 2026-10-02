"""Windows DNS client name resolution timeout parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-DNS-Client event 1014 of the System event log: name
resolution for a name timed out after none of the configured DNS servers
responded. Each record stores the name, a socket address and, from version 1,
the process ID of the client. The socket address layout, the Event ID and the
message text are sourced in the notes.
"""

import base64
import binascii
import ipaddress

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'DNS Name Resolution Timeouts'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-DNS-Client'
_EVENT_ID = '1014'
# Address family numbers and where each socket address structure keeps its address (see notes).
_AF_INET = 2
_AF_INET6 = 23

__artifacts_v2__ = {
    "dnsNameResolutionTimeouts": {
        "name": "DNS Name Resolution Timeouts",
        "description": "Microsoft-Windows-DNS-Client event 1014 of the System event log, name resolution for a name "
                       "timed out after none of the configured DNS servers responded: the name, the socket address "
                       "the record stores and, where the record has it, the client process ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-DNS-Client and whose Event ID is 1014. The provider's "
                 "manifest sends 1014 to the System channel as a warning with the message 'Name resolution for the "
                 "name %1 timed out after none of the configured DNS servers responded.' and the fields QueryName, "
                 "AddressLength and Address, and version 1 of the event adds 'Client PID %4.' to the message and a "
                 "ClientPID field (Microsoft-Windows-DNS-Client manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-DNS-Client.xml#L639-L655 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-DNS-Client.xml#L656-L673; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold version 0 only: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-DNS-Client.xml#L600-L616, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-DNS-Client.xml#L600-L616 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-DNS-Client.xml#L600-L616). "
                 "Query Name and Client Process ID are QueryName and ClientPID as python-evtx renders them, with any "
                 "white space at either end removed (no tested value had any); Client Process ID is blank on a "
                 "version 0 record, which has no such field. The manifest types Address as binary data shown as a "
                 "socket address and does not say whose address it is. python-evtx renders binary data as base64 "
                 "text (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1359-L1360), "
                 "and the three columns Address Family (as stored), Address and Scope ID are read from the bytes "
                 "that text decodes to. Address Family (as stored) is the number in the first two bytes, least "
                 "significant byte first. Microsoft gives 2 for AF_INET and 23 for AF_INET6 (Microsoft, 'socket "
                 "function (winsock2.h)', "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/winsock2/nf-winsock2-socket.md#L87-L88 "
                 "and "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/winsock2/nf-winsock2-socket.md#L143-L144) "
                 "and lists the members of the two socket address structures in order: family, port, address and "
                 "reserved bytes for AF_INET, and family, port, flow information, address and scope identifier for "
                 "AF_INET6 (Microsoft, 'SOCKADDR_IN (ws2def.h)', "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/ws2def/ns-ws2def-sockaddr_in.md#L62-L78, "
                 "and 'SOCKADDR_IN6_LH (ws2ipdef.h)', "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/ws2ipdef/ns-ws2ipdef-sockaddr_in6_lh.md#L62-L83). "
                 "Those pages do not give the size of each member; the positions read here are bytes 4 to 7 for an "
                 "IPv4 address when the family is 2, and bytes 8 to 23 for an IPv6 address and bytes 24 to 27 for "
                 "Scope ID, least significant byte first, when the family is 23. An IPv6 address is written in its "
                 "shortened text form. For any other family, or for data too short to hold the address, Address and "
                 "Scope ID are blank and the family number is still shown; Scope ID is also blank for an IPv4 "
                 "address and for IPv6 data that ends before byte 27. All three columns are blank when the record "
                 "has no Address field or its text does not decode to at least two bytes, which no tested record "
                 "showed. The AddressLength field is not used. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of one Windows 11 "
                 "build 26200 ARM64 virtual machine (windows11_arm_4688_known and windows11_arm_known_20261001). The "
                 "four public images gave 23, 13, 0 and 4 rows in that order and each capture gave 551, the same 551 "
                 "records on both. The 40 records of the public images are version 0 and the captures' are version "
                 "1, so Client Process ID is blank on every row of af_case2_win10, lonewolf_win10 and szechuan_win10 "
                 "and filled, with a whole number, on every row of the captures. Every tested record stores 128 "
                 "bytes of address data and an AddressLength of 128. Address Family (as stored) was 2 on 33 rows "
                 "over the six logs, 23 on 1,108 and 0 on 1, a row of lonewolf_win10 whose 128 bytes are all zero "
                 "and whose Address is therefore blank. On single logs, Address held one value and Address Family "
                 "(as stored) held one value, 2, on every row of af_case2_win10, and Address Family (as stored) held "
                 "one value, 2, on every row of szechuan_win10; Scope ID is blank on every row of those two logs, "
                 "whose addresses are all IPv4. The port bytes were zero on every row with family 2 or 23, and the "
                 "flow information bytes zero on every row with family 23. Scope ID was 0 on the 12 IPv6 rows of "
                 "lonewolf_win10 and one other number on the 548 IPv6 rows of each capture, every one of which has "
                 "an Address beginning fe80:; no row with Scope ID 0 has such an address. Scope ID was not checked "
                 "against another record of the machine. Read at those positions, the Address of 37 of the 39 "
                 "public-image rows that have one equals a name server the image's SYSTEM hive records in a "
                 "NameServer, DhcpNameServer or Dhcpv6DNSServers value under the Tcpip or Tcpip6 service's "
                 "Parameters key, in any control set (23 of 23 on af_case2_win10, 12 of 12 on lonewolf_win10 and 2 "
                 "of 4 on szechuan_win10). That measurement is what supports the byte positions, and it is the only "
                 "support here for reading Address as a DNS server's address. Query Name had no dot on 392 rows over "
                 "the six logs, and on every one of them it was wpad, ignoring case. The manifest's message is the "
                 "only statement here of what a record means. A version 0 record names no process, and on a version "
                 "1 record Client Process ID is a process ID and not a program name. It was not matched to a process "
                 "here: the Security logs of the two captures hold their first process creation record (4688, which "
                 "Windows Process Creation reports) after all but 2 and after all 551 of their rows, and neither of "
                 "those 2 rows' process IDs has an earlier process creation record. Rows are in the order the log "
                 "file holds its records, which was rising Record ID on every tested log. Event Time (UTC) rises "
                 "with it except for 1 row on each capture that is earlier than the row before it. Computer held one "
                 "value on every row of each tested log that gave rows except szechuan_win10, where its 4 rows hold "
                 "three names. A record python-evtx cannot render, or whose XML does not parse, is counted in the "
                 "run log and not reported. Every record of the four public images' logs rendered; 72 records of "
                 "each capture's log did not, and each of those stores 27 at index 3 of its substitution values, the "
                 "place that holds the Event ID on the records that rendered. A log marked dirty is read past the "
                 "chunks its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read: the provider's other events. Of those, "
                 "the tested System logs held only 8014 (7 records) and 8015 (2 records), both on szechuan_win10.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 551 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 551 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 23 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 13 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
        },
    },
}


def socket_address(text):
    """(address family, address, scope ID) of a socket address python-evtx rendered as base64 text.

    The family is the number in the first two bytes, least significant first. The
    address is given for an IPv4 or IPv6 socket address long enough to hold one, and
    the scope ID for an IPv6 one long enough to hold it; each is '' otherwise. All
    three are '' when the text is not base64 or holds under two bytes.
    """
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error):
        return '', '', ''
    if len(raw) < 2:
        return '', '', ''
    family = int.from_bytes(raw[:2], 'little')
    if family == _AF_INET and len(raw) >= 8:
        return str(family), str(ipaddress.IPv4Address(raw[4:8])), ''
    if family == _AF_INET6 and len(raw) >= 24:
        scope = str(int.from_bytes(raw[24:28], 'little')) if len(raw) >= 28 else ''
        return str(family), str(ipaddress.IPv6Address(raw[8:24])), scope
    return str(family), '', ''


def timeout_row(record):
    family, address, scope = socket_address(record.get('Address'))
    return (record.time, record.get('QueryName'), address, scope, family, record.get('ClientPID'),
            record.record_id, record.computer)


@artifact_processor
def dnsNameResolutionTimeouts(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Query Name', 'Address', 'Scope ID',
                    'Address Family (as stored)', 'Client Process ID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids={_EVENT_ID},
                                          provider=_PROVIDER)
    data_list = [timeout_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
