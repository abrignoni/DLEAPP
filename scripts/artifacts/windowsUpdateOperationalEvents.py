"""Windows Update Operational event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-WindowsUpdateClient record of the WindowsUpdateClient Operational event log: update
scans and the number of updates found, updates detected, downloaded or failing to download, connectivity, service
stop and shutdown requests, client self-updates and health changes. The Event IDs, the message text and the field
names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Windows Update Operational Events'
_LOG = 'Microsoft-Windows-WindowsUpdateClient%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-WindowsUpdateClient'

# The fields with a column of their own, in column order; every other field goes to Other Fields.
_SHOWN = ('updateTitle', 'updateGuid', 'updateRevisionNumber', 'serviceGuid', 'updateCount', 'errorCode')

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '25': 'Windows Update failed to check for updates with error %1.',
    '26': 'Windows Update successfully found %1 updates.',
    '29': 'Windows Update lost connectivity.',
    '30': 'Windows Update established connectivity.',
    '31': 'Windows Update failed to download an update.',
    '34': 'The Windows Update Client Core component failed to install a self-update with error %1.',
    '35': 'The Windows Update Client Auxillary component failed to install a self-update with error %1.',
    '36': 'The Windows Update Client Core component was successfully updated from version %1 to version %2.',
    '37': 'The Windows Update Client Auxillary was successfully updated from version %1 to version %2.',
    '38': 'Windows Update received a service stop request.',
    '39': 'Windows Update received a service shutdown request.',
    '40': 'An update was detected.',
    '41': 'An update was downloaded.',
    '42': 'There has been a change in the health of Windows Update.',
}


__artifacts_v2__ = {
    "windowsUpdateOperationalEvents": {
        "name": "Windows Update Operational Events",
        "description": "Microsoft-Windows-WindowsUpdateClient records of the WindowsUpdateClient Operational event "
                       "log, such as a scan that found a number of updates and an update downloaded, with the "
                       "update's title, ID and revision, the service ID, the update count and the error code where a "
                       "record carries them, and each record's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-WindowsUpdateClient%4Operational.evtx the paths match with "
                 "python-evtx and reports, one row per record, every record whose provider is "
                 "Microsoft-Windows-WindowsUpdateClient, whatever its Event ID. The provider's records in the System "
                 "log are reported by Windows Update Client Events. The provider's manifest of Windows 11 build "
                 "26100.1742 sends 19 events to this log's channel: 14 Event IDs (25, 26, 29, 30, 31 and 34 to 42), "
                 "each version 0, and a version 1 of 25, 26, 31, 40 and 41. They sit among lines 475 to 841 of the "
                 "file, with 4 entries of other channels between them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L475-L841). "
                 "The manifests of Windows 11 build 22621.819 and Windows 10 builds 19041.208, 17763.107 and "
                 "16299.15 hold the same 19 entries with the same level, message and fields "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L475-L841, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L475-L841, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L464-L830 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L459-L825). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the "
                 "record's Event ID, the first sentence of the first line of the build 26100 message, which the "
                 "versions of an Event ID share: the first line that holds more than white space, with each run of "
                 "white space made one space, cut after the first period that a space or the end of the line follows "
                 "(whole when it has none), with its placeholders (such as %1) as the manifest writes them. A "
                 "placeholder is an insertion string for a data item of the event's template by its position "
                 "(Microsoft's Defining Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in; 6 of the 14 texts hold one. Event is blank for an Event ID outside the 14, "
                 "which no tested record had. Update Title, Update ID, Revision Number, Service ID, Update Count and "
                 "Error Code (as stored) are the updateTitle, updateGuid, updateRevisionNumber, serviceGuid, "
                 "updateCount and errorCode fields, which the manifests type as win:UnicodeString, win:GUID, "
                 "win:UInt32, win:GUID, win:UInt32 and win:HexInt32. Version 1 of 31 and 41 carries updateTitle, "
                 "which version 0 does not, and version 1 of 25, 26 and 40 carries serviceGuid. A field a record "
                 "does not carry is left blank. Only 26 and 41 occur on the tested logs, every record of them "
                 "version 1: 221 rows of 26 ('Windows Update successfully found %1 updates.'), with an Update Count "
                 "from 0 to 48 and a Service ID on each, and 254 rows of 41 ('An update was downloaded.'), each with "
                 "an Update Title, an Update ID in braces and a decimal Revision Number. Error Code (as stored) and "
                 "Other Fields were blank on every tested row. The other 12 Event IDs are unexercised. 181 of the "
                 "254 titles are 12 capital letters and digits, a hyphen and a package name (such as "
                 "9WZDNCRFJBMP-Microsoft.WindowsStore), and 21 hold a KB number in parentheses. Service ID held four "
                 "values over the 221 rows of 26: {8b24b027-1dee-babb-9a95-3517dfb9c552} on 83, "
                 "{9482f4b4-e343-43b6-b170-9a65bc822c77} on 74, {855e8a7c-ecb4-4ca3-b045-1dfa50104289} on 54 and "
                 "{7971f918-a847-4430-9279-4a52d1efe18d} on 10; which update service each names is not established "
                 "here. Each of the 201 Update IDs of the tested 41 rows also appears in Windows Update Client "
                 "Events from the same image's System log, and on every 41 row the Update Title equals that "
                 "artifact's title for the same Update ID. Other Fields lists every other named field that holds "
                 "more than white space as 'name: value', in the record's order, joined with ' | '. Each value, here "
                 "and in the six columns before it, is as python-evtx renders it with any white space at either end "
                 "removed; no tested value had any. A data item that has no name is not shown, and no tested record "
                 "had one. If a record named a field twice the last would be read. The tested records carried the "
                 "field names their image's build manifest gives the event. Tested on the logs of four public images "
                 "(af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; "
                 "szechuan_win10, build 19041), which gave 35, 155, 198 and 87 rows in that order; the two captures "
                 "of a Windows 11 build 26200 machine hold no such log. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with integer "
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's "
                 "conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element, which held one value, S-1-5-18, on every "
                 "tested row. Record ID is the record's EventRecordID and Computer the machine name the record "
                 "stores, which held one value on af_case2_win10 and pc_mus_001_win11 and two on lonewolf_win10 and "
                 "szechuan_win10. Rows are in the order the file holds them, which was rising Record ID and rising "
                 "time on every tested log. Every record of the tested logs rendered and is the provider's. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not "
                 "read: the events these manifests send to the provider's Analytic channel.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-WindowsUpdateClient%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 35 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 155 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 198 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 87 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def update_row(record):
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in _SHOWN and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), *(record.get(name) for name in _SHOWN),
            other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def windowsUpdateOperationalEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Update Title', 'Update ID',
                    'Revision Number', 'Service ID', 'Update Count', 'Error Code (as stored)', 'Other Fields',
                    'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [update_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
