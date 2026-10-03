"""Network Connectivity Status Indicator event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-NCSI record of the provider's Operational event log: the changes of an interface's
connectivity (none, local or internet, for IPv4 or IPv6) with the reason the record stores, and the provider's other
events of that log. The Event IDs, the message text, the field names and the numbers' names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Network Connectivity Status Events'
_LOG = 'Microsoft-Windows-NCSI%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-NCSI'

# The fields that have a column of their own, in column order; any other field goes to Other Fields.
_SHOWN = ('InterfaceGuid', 'IfLuid', 'Family', 'Capability', 'PreviousCapability', 'CapabilityChangeReason')

# Event ID: the first sentence of the provider's message for it, placeholders as written (see notes).
_EVENTS = {
    '4009': 'Inside/Outside detection started for interface %3.',
    '4010': 'Inside/Outside detection finished for interface %3 (%4).',
    '4011': 'Windows Firewall Group Policy settings have been updated.',
    '4012': 'Inside/Outside probe failed for interface %1.',
    '4028': 'Inside/Outside detection is suspect',
    '4038': 'Hotspot detected on interface %1 (Family: %2)',
    '4042': 'Capability change on %1 (%2 Family: %3 Capability: %4 ChangeReason: %5)',
}


__artifacts_v2__ = {
    "networkConnectivityEvents": {
        "name": "Network Connectivity Status Events",
        "description": "Microsoft-Windows-NCSI records of the provider's Operational event log, such as each change "
                       "of an interface's connectivity capability with its address family, previous capability and "
                       "change reason as the numbers the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-NCSI%4Operational.evtx the paths match with python-evtx and reports, "
                 "one row per record, every record whose provider is Microsoft-Windows-NCSI, whatever its Event ID. "
                 "Microsoft's overview calls the Network Connectivity Status Indicator (NCSI) 'a feature that helps "
                 "to provide a visual display of the current network connection status' and says it 'sends separate "
                 "IPv4 and IPv6 active probes in parallel' "
                 "(https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/networking/ncsi/ncsi-overview.md?plain=1#L16 "
                 "and "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/networking/ncsi/ncsi-overview.md?plain=1#L51). "
                 "The provider's manifest of Windows 11 build 26100.1742 sends six events to this log's channel: "
                 "4009, 4010, 4011 and 4012 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-NCSI.xml#L376-L447), "
                 "4038 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-NCSI.xml#L832-L846) "
                 "and 4042 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-NCSI.xml#L892-L910). "
                 "The manifests of Windows 10 builds 16299.15, 17763.107 and 19041.208 and Windows 11 build "
                 "22621.819 hold the same six with the same message and fields and a seventh, 4028 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-NCSI.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-NCSI.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-NCSI.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-NCSI.xml, "
                 "in the last at lines 702 to 715). These are the manifests nasbench's EVTX-ETW-Resources repository "
                 "publishes, and every one of these entries is version 0. Event is, for the record's Event ID, the "
                 "message's first sentence: the message with each run of white space made one space, cut after the "
                 "first period that a space or the end of the message follows, with its placeholders (such as %1) as "
                 "the manifest writes them. A placeholder is an insertion string for a data item of the event's "
                 "template by its position (Microsoft's Defining Events page: 'to include the third data item in the "
                 "template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID outside the seven, which no tested record "
                 "had. Every tested record is a 4042, 'Capability change on %1 (%2 Family: %3 Capability: %4 "
                 "ChangeReason: %5)'. It stores six fields, and the tested records carried exactly these names in "
                 "this order: InterfaceGuid (Interface GUID), IfLuid (Interface LUID), Family, Capability, "
                 "CapabilityChangeReason (Change Reason) and PreviousCapability (Previous Capability). Family, "
                 "Capability, Previous Capability and Change Reason are the numbers the record stores. The numbers' "
                 "names were read from ncsi.dll of each public image, the file each image's SOFTWARE hive registers "
                 "as the provider's resource file. Its 4042 template ties Family to the value map FamilyMap, "
                 "Capability and PreviousCapability to CapabilityMap and CapabilityChangeReason to "
                 "CapabilityChangeReasonMap, and the three maps read the same on the four images (builds 16299, "
                 "17763, 19041 and 22621). Family: 0 V4, 1 V6. Capability and Previous Capability: 0 None, 1 Local, "
                 "2 Internet. Change Reason: 0 Unknown, 1 NoAddress, 2 NoGlobalAddress, 3 NoRoute, 4 "
                 "ActiveHttpProbeSucceeded, 5 ActiveHttpProbeFailed, 6 ActiveHttpProbeFailedButDnsSucceeded, 7 "
                 "ActiveHttpProbeFailedHotspotDetected, 8 ActiveDnsProbeSucceeded, 9 ActiveDnsProbeFailed, 10 "
                 "SuspectDnsProbeFailed, 11 SuspectDnsProbeFailedAndNoGateway, 12 SuspectArpProbeFailed, 13 "
                 "PassivePacketHops, 14 CapabilityReset, 15 ActiveHttpProbeSucceededViaProxy, 16 "
                 "SuspectArpProbeFailedExitingCS. The tie between a field and its map was read from bytes 8 to 11 of "
                 "the field's template item descriptor, which on the four images hold the offset of that map inside "
                 "the file's event template resource; libfwevt's description of that resource gives the layout of "
                 "the event, template and map structures and marks those bytes unknown "
                 "(https://github.com/libyal/libfwevt/blob/7bfd3403b1bd1476aefbaf2e94b5562cbf724997/documentation/Windows%20Event%20manifest%20binary%20format.asciidoc?plain=1#L391-L418, "
                 "https://github.com/libyal/libfwevt/blob/7bfd3403b1bd1476aefbaf2e94b5562cbf724997/documentation/Windows%20Event%20manifest%20binary%20format.asciidoc?plain=1#L603-L621 "
                 "and "
                 "https://github.com/libyal/libfwevt/blob/7bfd3403b1bd1476aefbaf2e94b5562cbf724997/documentation/Windows%20Event%20manifest%20binary%20format.asciidoc?plain=1#L276-L292). "
                 "A published dump of the provider on build 18990 shows the same map on Capability "
                 "(https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-18990/Microsoft-Windows-NCSI.xml#L228-L235). "
                 "No ncsi.dll of a later build was read, so the names are not established for records of a later "
                 "build; the artifact reports the numbers and adds no name. Interface GUID is the GUID as "
                 "python-evtx renders it, lower case in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376). "
                 "Interface LUID is the stored number. Microsoft names the parts of an interface LUID Reserved, "
                 "NetLuidIndex and IfType and lists IfType 6 as 'An Ethernet network interface' and 71 as 'An IEEE "
                 "802.11 wireless network interface' "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/ifdef/ns-ifdef-net_luid_lh.md?plain=1#L71-L87, "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/ifdef/ns-ifdef-net_luid_lh.md?plain=1#L108-L114 "
                 "and "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/ifdef/ns-ifdef-net_luid_lh.md?plain=1#L163-L169). "
                 "On the tested images the number's top 16 bits were 6 or 71 and its low 24 bits 0, and for 4 of the "
                 "5 interfaces the rows name, the SYSTEM hive's network adapter key whose NetCfgInstanceId is the "
                 "row's GUID stores an *IfType equal to the top 16 bits and a NetLuidIndex equal to the next 24 "
                 "bits; the fifth (1 row of pc_mus_001_win11) has no such key in the hive as it was read. All 5 "
                 "GUIDs are Interface GUID values of the Windows Network Interfaces artifact on the same image. "
                 "Tested on the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build "
                 "16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 13, 112, 107 and 18 "
                 "rows in that order; the two captures of a Windows 11 build 26200 machine hold no such log. Family "
                 "is 0 on 189 rows and 1 on 61. Capability is 0 on 97, 1 on 37 and 2 on 116; Previous Capability is "
                 "0 on 124, 1 on 30 and 2 on 96. Change Reason is 4 on 96 rows, 14 on 62, 5 on 21, 1 on 18, 13 on "
                 "18, 2 on 15, 8 on 14 and 3, 6 and 10 on 2 each. The six other events and Change Reason 0, 7, 9, "
                 "11, 12, 15 and 16 are unexercised. Capability equals Previous Capability on 25 of the 250 rows (1, "
                 "21, 1 and 2). Previous Capability equals the Capability of the row before it for the same "
                 "interface and family on 110 of 110 rows that have one on lonewolf_win10 and 103 of 104 on "
                 "pc_mus_001_win11, and on 2 of 12 on af_case2_win10 and 7 of 16 on szechuan_win10. So a row's "
                 "Previous Capability is not always the last Capability the log shows for that interface and family; "
                 "why is not established. Of the Network Connected (10000) and Network Disconnected (10001) rows of "
                 "the Network Profile Connection Events artifact that fall inside the period the rows of the same "
                 "image span, 9 of 9, 19 of 21, 156 of 173 and 14 of 19 are within five seconds of a row. Event Time "
                 "(UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the "
                 "FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, "
                 "in place of python-evtx 0.8.1's conversion through a floating-point number, which can differ by "
                 "microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element and held one value, S-1-5-20, on every "
                 "row. Record ID is the record's EventRecordID and Computer the machine name the record stores, "
                 "which held one value on pc_mus_001_win11, two on af_case2_win10 and lonewolf_win10 and three on "
                 "szechuan_win10. Event ID and Event held one value on every tested image. Other Fields lists any "
                 "named field that has no column and holds more than white space as 'name: value', in the record's "
                 "order, joined with ' | '; it is blank on every row, since a 4042 record has no such field. Family "
                 "held one value, 0, on af_case2_win10. Interface GUID and Interface LUID held one value on "
                 "af_case2_win10, lonewolf_win10 and szechuan_win10. Each value is as python-evtx renders it with "
                 "any white space at either end removed, and no tested value had any. A data item that has no name "
                 "is not shown, and no tested record had one. If a record named a field twice the last would be "
                 "read. Rows are in the order the file holds them, which was rising Record ID on every tested log; "
                 "in time order 1 row each of af_case2_win10 and szechuan_win10 is earlier than the row before it. "
                 "Every record of the tested logs rendered and is the provider's. A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not reported. A log marked "
                 "dirty is read past the chunks its header counts, and the run log says how many records came from "
                 "there. Reading needs the python-evtx package (pip install python-evtx). Not read: the 51 events "
                 "each of these manifests sends to the provider's Analytic channel.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 13 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 112 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 107 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 18 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-NCSI%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
    },
}


def connectivity_row(record):
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields if name not in _SHOWN and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), *(record.get(name) for name in _SHOWN), other,
            record.user_sid, record.record_id, record.computer)


@artifact_processor
def networkConnectivityEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Interface GUID', 'Interface LUID', 'Family',
                    'Capability', 'Previous Capability', 'Change Reason', 'Other Fields', 'User SID', 'Record ID',
                    'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [connectivity_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
