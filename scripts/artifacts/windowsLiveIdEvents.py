"""Microsoft account (LiveId) event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-LiveId record of the LiveId Operational event log: service tokens acquired for a
resource, SOAP requests and responses of the Microsoft account service, errors it reported, and its service starting
and stopping. The Event IDs, the message text and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Microsoft Account (LiveId) Events'
_LOG = 'Microsoft-Windows-LiveId%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-LiveId'

# The fields with a column of their own, in column order; every other field goes to Other Fields.
_SHOWN = ('ResourceURI', 'Created', 'Expires', 'TokenType', 'RequestStatus', 'cid', 'FunctionName', 'ErrorCode',
          'Value')

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '1021': 'SignOutUser_RegistryOpenOrReadFailure.',
    '1022': 'SignOutUser_RegistryWriteFailure.',
    '2023': 'Operation: %1',
    '2024': 'Operation: %1',
    '2025': 'WLIDSvc service failed to start.',
    '2028': 'ErrorVerifier in function %1 encountered unexpected error code (%2).',
    '6113': 'RPC call to function %1 returned the following error code: %2.',
    '6114': "SOAP Request of type %1 for user CID '%2' in %4 environment received the following error code "
            'from the Microsoft Account server: %3.',
    '6115': '## SOAP Request: %1',
    '6116': '## SOAP Response: %1',
    '6117': 'Acquired Service token.',
}


__artifacts_v2__ = {
    "liveIdEvents": {
        "name": "Microsoft Account (LiveId) Events",
        "description": "Microsoft-Windows-LiveId records of the LiveId Operational event log, such as service tokens "
                       "acquired for a resource, with their resource, times and type as stored, SOAP requests and "
                       "responses as stored, errors with the function name, error code and account CID where a "
                       "record carries them, and the service starting and stopping.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-LiveId%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-LiveId, whatever its "
                 "Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 11 entries to this log's "
                 "channel, every one version 0: 1021, 1022, 2023, 2024, 2025, 2028, 6113, 6114, 6115, 6116 and 6117. "
                 "They sit among lines 434 to 1989 of the file, with 92 entries of other channels between them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-LiveId.xml#L434-L1989). "
                 "The build 22621.819 manifest sends the same 11 with the same first sentences "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-LiveId.xml#L434-L1989). "
                 "The manifests of Windows 10 builds 19041.208, 17763.107 and 16299.15 send it only 1021, 1022, "
                 "2023, 2024, 2025 and 2028 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-LiveId.xml#L434-L800, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-LiveId.xml#L419-L785 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-LiveId.xml#L419-L785), "
                 "yet the logs of szechuan_win10 (build 19041), af_case2_win10 (build 17763) and lonewolf_win10 "
                 "(build 16299) hold records of 6113, 6115, 6116 and 6117, and lonewolf_win10 of 6114, with the "
                 "field names of the build 26100 entries. These are the manifests nasbench's EVTX-ETW-Resources "
                 "repository publishes. Event is the first sentence of the first line of the build 26100 message for "
                 "the record's Event ID: the first line that holds more than white space, with each run of white "
                 "space made one space, cut after the first period that a space or the end of the line follows "
                 "(whole when it has none), with its placeholders (such as %1) as the manifest writes them. A "
                 "placeholder is an insertion string for a data item of the event's template by its position "
                 "(Microsoft's Defining Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in; 7 of the 11 texts hold one. Event is blank for an Event ID outside the "
                 "table, which no tested record had. The build 26100 entry for 6117 ('Acquired Service token.') "
                 "declares no template; its message names nine values, ResourceURI, Created, Expires, TokenType, "
                 "AuthRequired, RequestStatus, HasFlowUrl, HasAuthUrl and HasEndAuthUrl, and every tested 6117 "
                 "record carries fields of those names in that order. Resource URI, Token Created (as stored), Token "
                 "Expires (as stored), Token Type and Request Status (as stored) are the ResourceURI, Created, "
                 "Expires, TokenType and RequestStatus fields. Account CID is the cid field of 6114 ('SOAP Request "
                 "of type %1 for user CID '%2' in %4 environment received the following error code from the "
                 "Microsoft Account server: %3.'). Function Name and Error Code (as stored) are the FunctionName and "
                 "ErrorCode fields, which the manifest gives 2028 and 6113, and 6114 for ErrorCode. SOAP Body (as "
                 "stored) is the Value field of 6115 ('## SOAP Request: %1') and 6116 ('## SOAP Response: %1'). "
                 "Token Created and Token Expires are text with no time zone and are not converted. On every tested "
                 "6117 row except the 19 below, Event Time (UTC) is later than Token Created by a whole number of "
                 "hours, within 6 seconds: 7 hours on af_case2_win10, 4 on lonewolf_win10, 5 on pc_mus_001_win11 and "
                 "7 or 8 on szechuan_win10. That is the Time Zone Bias Windows System Information reports for the "
                 "image (480 minutes on af_case2_win10 and szechuan_win10, 300 on lonewolf_win10 and "
                 "pc_mus_001_win11), or that bias less 60 minutes. On pc_mus_001_win11, 19 of the 170 rows of 6117 "
                 "hold 1969-12-31 19:00:00 as both Token Created and Token Expires, a negative Request Status and no "
                 "Token Type; 1969-12-31 19:00:00 is 1970-01-01 00:00:00 less that image's 300-minute bias. Token "
                 "Expires is later than Token Created on every other 6117 row except 2 on pc_mus_001_win11, where "
                 "the two are equal. What the Request Status values stand for is not established here. The 6117 rows "
                 "name 2, 30, 80 and 12 distinct Resource URIs on af_case2_win10, lonewolf_win10, pc_mus_001_win11 "
                 "and szechuan_win10; http://Passport.NET/tb is the Resource URI of 47, 77 and 8 of them on "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10. Token Type held urn:passport:compact, "
                 "urn:passport:legacy, urn:passport:delegationcompact and urn:passport:loginprooftoken on the tested "
                 "rows, as stored, and was blank on the 19 rows above. Account CID is filled on the 36 rows of 6114 "
                 "on lonewolf_win10, with one value of 16 hexadecimal digits, and is blank on every row of "
                 "af_case2_win10, pc_mus_001_win11 and szechuan_win10, which hold no 6114 record. The tested logs "
                 "store the SOAP bodies with element values replaced by *, in part or in full: every element text is "
                 "* in 793 of the 795 bodies of 6115 on af_case2_win10 and in 71 of the 116 on szechuan_win10, while "
                 "every body on lonewolf_win10 and pc_mus_001_win11 keeps text in some elements, among them "
                 "wsa:Address (a service address) and wsu:Created (a timestamp); ps:HostingApp (the requesting "
                 "application) keeps text in bodies on pc_mus_001_win11 and szechuan_win10 and in none on "
                 "lonewolf_win10. 84 bodies of 6115, 78 on pc_mus_001_win11 and 6 on szechuan_win10, keep text in a "
                 "wsse:BinarySecurityToken element, so the column can hold security token values. The bodies are "
                 "reported as stored. Other Fields lists every other named field that holds more than white space as "
                 "'name: value', in the record's order, joined with ' | '; for 2024 ('Operation: %1') that is "
                 "Operation (Service started or Service stopped), Details and Status, which held 0x00000000 on every "
                 "tested 2024 row. Each value, here and in the named columns, is as python-evtx renders it with any "
                 "white space at either end removed; no tested value had any. A data item that has no name is not "
                 "shown, and no tested record had one. If a record named a field twice the last would be read. "
                 "Tested on the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build "
                 "16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 1544, 499, 449 and "
                 "298 rows in that order; the two captures of a Windows 11 build 26200 machine hold no such log. "
                 "2024, 6113, 6115, 6116 and 6117 occur on all four images, 2028 on af_case2_win10 and "
                 "szechuan_win10, and 6114 on lonewolf_win10 alone; 1021, 1022, 2023 and 2025 are unexercised. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element, which every tested record carries: "
                 "S-1-5-18, S-1-5-19, S-1-5-20 and S-1-5-21 SIDs on all four images. Record ID is the record's "
                 "EventRecordID and Computer the machine name the record stores, which held one value on "
                 "af_case2_win10, lonewolf_win10 and pc_mus_001_win11 and three on szechuan_win10. Rows are in the "
                 "order the file holds them; Record ID drops once on af_case2_win10, lonewolf_win10 and "
                 "pc_mus_001_win11, and in time order 4 rows are earlier than the row before them (1 on each image). "
                 "Every record of the tested logs rendered and is the provider's. A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not reported. A log marked "
                 "dirty is read past the chunks its header counts, and the run log says how many records came from "
                 "there. Reading needs the python-evtx package (pip install python-evtx). Not read: the events these "
                 "manifests send to the provider's Analytic channel, and the 184 build 26100 entries that name no "
                 "channel. What the function names and error codes stand for is not established here.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-LiveId%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "user-check",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1544 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 499 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 449 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 298 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def live_id_row(record):
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in _SHOWN and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''),
            *(record.get(name) for name in _SHOWN), other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def liveIdEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Resource URI', 'Token Created (as stored)',
                    'Token Expires (as stored)', 'Token Type', 'Request Status (as stored)', 'Account CID',
                    'Function Name', 'Error Code (as stored)', 'SOAP Body (as stored)', 'Other Fields', 'User SID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [live_id_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
