"""Windows DHCP client event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads six Microsoft-Windows-Dhcp-Client events of the Dhcp-Client Admin event
log: DHCP received a wireless network name (SSID) for a network card (50067),
found a match for it in its cache (50065) or plumbed an address using it
(50066), the computer was not assigned an address (1001) or could not renew
one (1003), and a DHCP server denied a lease (1002). The Event IDs, field names
and message text are sourced in the notes.
"""

import base64
import binascii

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'DHCP Client Events'
_LOG = 'microsoft-windows-dhcp-client%4admin.evtx'
_PROVIDER = 'Microsoft-Windows-Dhcp-Client'

# Event ID: a short label made of words of the provider's message for it (see notes).
_EVENTS = {
    '1001': 'Your computer was not assigned an address from the network',
    '1002': 'The IP address lease has been denied by the DHCP server',
    '1003': 'Your computer was not able to renew its address from the network',
    '50065': 'DHCP has found a match in the cache for Service Set Identifier(SSID)',
    '50066': 'DHCP has plumbed an address using Service Set Identifier(SSID)',
    '50067': 'DHCP has received a Service Set Identifier(SSID)',
}

__artifacts_v2__ = {
    "dhcpClientEvents": {
        "name": "DHCP Client Events",
        "description": "Microsoft-Windows-Dhcp-Client events of the Dhcp-Client Admin event log: DHCP received a "
                       "wireless network name (SSID) for a network card (50067), found a match for it in its cache "
                       "(50065) or plumbed an address using it (50066), the computer was not assigned an address "
                       "(1001) or could not renew one (1003), or a DHCP server denied a lease (1002), with the "
                       "network card's address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Dhcp-Client%4Admin.evtx the paths match with python-evtx and "
                 "reports, one row per record, the records whose provider is Microsoft-Windows-Dhcp-Client and whose "
                 "Event ID is 1001, 1002, 1003, 50065, 50066 or 50067. The provider's manifest gives the six events "
                 "the messages 'DHCP has received a Service Set Identifier(SSID) %1(Hexadecimal value of SSID: %2) "
                 "for the Network Card with the network address %4' (50067, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L2268-L2285), "
                 "'DHCP has found a match in the cache for Service Set Identifier(SSID) %1(Hexadecimal value of "
                 "SSID: %2) for the Network Card with the network address %4' (50065, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L2232-L2249), "
                 "'DHCP has plumbed an address using Service Set Identifier(SSID) %1(Hexadecimal value of SSID: %2) "
                 "for the Network Card with the network address %4' (50066, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L2250-L2267), "
                 "'Your computer was not assigned an address from the network (by the DHCP Server) for the Network "
                 "Card with network address %2. The following error occurred: %3. Your computer will continue to try "
                 "and obtain an address on its own from the network address (DHCP) server.' (1001, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L835-L852), "
                 "'Your computer was not able to renew its address from the network (from the DHCP Server) for the "
                 "Network Card with network address %2. The following error occurred: %3. Your computer will "
                 "continue to try and obtain an address on its own from the network address (DHCP) server.' (1003, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L872-L889) "
                 "and 'The IP address lease %1 for the Network Card with network address %3 has been denied by the "
                 "DHCP server %4 (The DHCP Server sent a DHCPNACK message).' (1002, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml#L853-L871). "
                 "These are the entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository; the manifests that repository publishes for "
                 "Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same six messages with the same "
                 "fields "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Dhcp-Client.xml). "
                 "Those manifests name the channel Microsoft-Windows-DHCP Client Events/Admin; every tested record "
                 "names it Microsoft-Windows-Dhcp-Client/Admin. Event is a short label made of words of that "
                 "message, in the message's order. SSID is the field NetworkHintString and SSID Hexadecimal (as "
                 "stored) is NetworkHint (50065, 50066 and 50067), which those messages print as the Service Set "
                 "Identifier and as the 'Hexadecimal value of SSID'. On all 216 tested rows that have them, SSID "
                 "Hexadecimal (as stored) is the bytes of SSID written in hexadecimal with the two digits of each "
                 "byte exchanged (the letter N, 4E, is stored as E4), and on none is it the plain hexadecimal; the "
                 "two tested network names hold ASCII characters only. Network Card Address is the field HWAddress "
                 "(all six events), which the messages print as the network address of the Network Card. It is a "
                 "binary field, which python-evtx renders as base64 "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1359-L1360), "
                 "and is shown as its bytes in two-digit upper-case hexadecimal joined by colons; text that is not "
                 "base64 would be shown as stored, and no tested record had any. The number of bytes equals the "
                 "record's HWLength field, 6, on all 224 tested rows, and HWLength is not otherwise used. Status "
                 "Code (as stored) is StatusCode (1001 and 1003), which those messages print as the error that "
                 "occurred. Lease Address (as stored) and DHCP Server (as stored) are Address1 and Address2 of 1002, "
                 "which its message prints as the lease and the DHCP server; the manifest types both as 32-bit "
                 "unsigned numbers and they are reported as the numbers python-evtx renders. The 1 tested 1002 row "
                 "stores lease 2157357248, which is 192.168.150.128 read least significant byte first and "
                 "128.150.168.192 read most significant byte first, and server 0; which reading the provider means "
                 "is not sourced here. Each field is as python-evtx renders it with any white space at either end "
                 "removed (no tested value had any), and a column whose field the record does not carry is blank. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 1, 73, 150 and 0 rows in "
                 "that order: 109 of 50067, 107 of 50065, 7 of 1003 (pc_mus_001_win11) and 1 of 1002 "
                 "(af_case2_win10), each reported record version 0. No tested log held a 1001 or a 50066 record, so "
                 "those two events are unexercised and read as the manifest describes them. Status Code (as stored) "
                 "was 121 on all 7 rows of 1003 and is blank on every row of lonewolf_win10, as are Lease Address "
                 "(as stored) and DHCP Server (as stored) on every row of lonewolf_win10 and pc_mus_001_win11; what "
                 "a status code stands for is not looked up. SSID and SSID Hexadecimal (as stored) are blank on "
                 "every row of af_case2_win10, whose 1 row is the 1002. On lonewolf_win10 and on pc_mus_001_win11 "
                 "Network Card Address held one value on every row, and SSID and SSID Hexadecimal (as stored) each "
                 "held one value on every row that has them. On both of those images the SSID is one the WLAN "
                 "Connection Events artifact reports, and the Network Card Address equals the Local MAC Address on "
                 "that artifact's rows, in the same form. Each of the 107 rows of 50065 comes right after a 50067 "
                 "row stamped less than a millisecond earlier with the same SSID and Network Card Address; 2 rows of "
                 "50067 have no 50065 row after them. Rows are in the order the log file holds its records, which "
                 "was rising Record ID on every tested log. On lonewolf_win10 the second row is 8,374 seconds "
                 "earlier than the first, and Computer changes between them; no other tested row is earlier than the "
                 "one before it. Computer held one value on pc_mus_001_win11 and two on lonewolf_win10. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the four tested logs rendered. A log marked dirty is read past the "
                 "chunks its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read: the provider's other events. The four "
                 "tested logs hold 5 records of 1 other Event ID.",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Dhcp-Client%4Admin.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 73 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 150 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def hardware_address(text):
    """The bytes of a binary field python-evtx rendered as base64, as two-digit hexadecimal numbers joined by colons.

    '' for no text; the text itself when it is not base64.
    """
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error):
        return text
    return ':'.join(f'{byte:02X}' for byte in raw)


def dhcp_row(record):
    return (record.time, record.event_id, _EVENTS[record.event_id], record.get('NetworkHintString'),
            record.get('NetworkHint'), hardware_address(record.get('HWAddress')),
            record.get('StatusCode'), record.get('Address1'), record.get('Address2'), record.record_id,
            record.computer)


@artifact_processor
def dhcpClientEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'SSID', 'SSID Hexadecimal (as stored)',
                    'Network Card Address', 'Status Code (as stored)', 'Lease Address (as stored)',
                    'DHCP Server (as stored)', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [dhcp_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
