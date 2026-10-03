"""Windows Update client event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads six Microsoft-Windows-WindowsUpdateClient events of the System event log:
an update started downloading (44), its installation started (43), succeeded
(19) or failed (20), and its uninstallation succeeded (23) or failed (24). Each
record names one update by title, identifier and revision number. Event IDs,
field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Windows Update Client Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-WindowsUpdateClient'

# Event ID: the words that open the provider's message for it (see notes).
_EVENTS = {
    '19': 'Installation Successful',
    '20': 'Installation Failure',
    '23': 'Uninstallation Successful',
    '24': 'Uninstallation Failure',
    '43': 'Installation Started',
    '44': 'Windows Update started downloading an update',
}
# The manifest names the title field of event 24 updatelist, and of the others updateTitle.
_TITLE_FIELD = {'24': 'updatelist'}

__artifacts_v2__ = {
    "windowsUpdateClientEvents": {
        "name": "Windows Update Client Events",
        "description": "Microsoft-Windows-WindowsUpdateClient events of the System event log that name one update: "
                       "download started (44), installation started (43), installation successful (19) or failed "
                       "(20), and uninstallation successful (23) or failed (24), with the update's title, identifier "
                       "and revision number.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-WindowsUpdateClient and whose Event ID is 19, 20, 23, "
                 "24, 43 or 44. Other providers use those Event IDs in the same log (37, 3, 58 and 31 records on the "
                 "four public images named below), so both are checked. The provider's manifest sends the six events "
                 "to the System channel with the messages 'Installation Successful: Windows successfully installed "
                 "the following update: %1' (19), 'Installation Failure: Windows failed to install the following "
                 "update with error %1: %2.' (20), 'Uninstallation Successful: Windows successfully uninstalled the "
                 "following update: %1' (23), 'Uninstallation Failure: Windows failed to uninstall the following "
                 "update with error %1: %2' (24), 'Installation Started: Windows has started installing the "
                 "following update: %1' (43) and 'Windows Update started downloading an update.' (44) (versions 0 "
                 "and 1 of each in the Microsoft-Windows-WindowsUpdateClient manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L290-L326, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L327-L365, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L399-L435, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L436-L474, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L842-L877 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L878-L912; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold the same entries: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L274-L458 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L826-L896, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L279-L463 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L831-L901, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L290-L474 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-WindowsUpdateClient.xml#L842-L912). "
                 "Event is the words of that message before its colon; the message of 44 has no colon, and Event is "
                 "that message without its period. Update Title, Update ID, Revision Number, Service ID and Error "
                 "Code (as stored) are the record's updateTitle, updateGuid, updateRevisionNumber, serviceGuid and "
                 "errorCode fields as python-evtx renders them, with any white space at either end removed (no "
                 "tested value had any). In the manifest version 1 of 19, 20, 23 and 24 carries serviceGuid and "
                 "version 0 does not, 43 and 44 carry it in neither version, only 20 and 24 carry errorCode, and "
                 "version 0 of 44 carries no updateTitle. A field a record does not carry is left blank, so Service "
                 "ID is blank on 43 and 44 rows and Error Code (as stored) is blank on rows of every event but 20 "
                 "and 24. The manifest names the title field of 24 updatelist, and that field is read into Update "
                 "Title on 24 rows. It types updateGuid and serviceGuid as GUIDs, updateRevisionNumber as an "
                 "unsigned 32-bit number and errorCode as a 32-bit number shown in hexadecimal, and does not say "
                 "what a service GUID or an error code stands for; both are reported as stored. Event Time (UTC) is "
                 "the record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of one Windows 11 "
                 "build 26200 ARM64 virtual machine (windows11_arm_4688_known and windows11_arm_known_20261001). The "
                 "four public images gave 41, 243, 281 and 210 rows in that order and the captures 1,574 and 1,583, "
                 "every row of the first capture being a row of the second. By Event ID the six logs hold 1,709 rows "
                 "of 44, 1,097 of 43, 1,049 of 19 and 77 of 20, every record version 1. No tested log held a 23 or "
                 "24 record, so the two uninstallation rows are written from the manifest and no tested record "
                 "exercised them. Error Code (as stored) is blank on every row of af_case2_win10 and of "
                 "szechuan_win10, whose logs hold no 20 record. On the 77 rows of 20 it was 0x80073d02 on 74, "
                 "0xc1800109 on 2 and 0x80246007 on 1. Update ID was a GUID in braces and lower case and Revision "
                 "Number a whole number on all 3,932 rows. Update Title began with twelve characters from 0 to 9 and "
                 "A to Z and a hyphen on 3,142 rows. Every one of those rows that has a Service ID has "
                 "{855e8a7c-ecb4-4ca3-b045-1dfa50104289}, and all 869 rows with that Service ID have a title of that "
                 "shape. Service ID held four values over the six logs. Counting rows with the same Update ID and "
                 "Revision Number as one update, and taking order from Record ID: every 43 row comes after a 44 row "
                 "of its update (1,097 of 1,097) and every 20 row after a 43 row (77 of 77); every 19 row comes "
                 "after a 43 row on the public images (180 of 180) and all but 1 on each capture. A 44 row alone "
                 "does not show an installation: 0, 2, 1 and 37 updates on the four public images and 26 on each "
                 "capture have only 44 rows. A 20 row is not always the last row of its update: 2 of the 4 updates "
                 "with a 20 row on lonewolf_win10, 1 of 9 on pc_mus_001_win11 and 2 of 26 on each capture have a "
                 "later 19 row. On the four public images every row has a line for the same update in the image's "
                 "ReportingEvents.log, which Windows Update Reporting Events reports: a line whose Identifier (as "
                 "stored) equals Update ID ignoring case and whose Event ID is 167 for a 44 row, 181 for a 43 row, "
                 "183 or 184 for a 19 row and 182 for a 20 row, within 60 seconds of the row (775 of 775 rows; "
                 "within 5 seconds on 721 and 31.8 seconds at most). That line's Update Title equals the row's on "
                 "all 188 rows of 43 and all 180 of 19, is blank on all 394 of 44 and is the row's title with one "
                 "more period on all 13 of 20, where its Result Code (as stored) equals Error Code (as stored) "
                 "without its 0x, ignoring case. In the other direction, every such line since the oldest System "
                 "record has a row within 60 seconds (41, 243, 281 and 210 lines); on pc_mus_001_win11 another 328 "
                 "such lines are older than the oldest System record, so that log reaches further back there. On "
                 "lonewolf_win10 the 4 rows of 19 whose title ends with a four-part version each have a Device "
                 "Driver Installs row within 60 seconds whose Driver Version is that version. Rows are in the order "
                 "the log file holds its records, which was rising Record ID on every tested log. Event Time (UTC) "
                 "rises with it except for 1 row on each capture that is earlier than the row before it. Computer "
                 "held one value on every row of each tested log except lonewolf_win10, where it held two. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. Every record of the tested logs rendered, among them the 72 TPM event 27 records of each "
                 "capture's log, which python-evtx renders only with the array value types scripts/windows_evtx.py "
                 "adds. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: the provider's other events; no tested System log "
                 "held one.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 1574 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 1583 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 281 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 41 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 243 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 210 rows",
        },
    },
}


def update_row(record):
    return (record.time, record.event_id, _EVENTS[record.event_id],
            record.get(_TITLE_FIELD.get(record.event_id, 'updateTitle')),
            record.get('updateGuid'), record.get('updateRevisionNumber'),
            record.get('serviceGuid'), record.get('errorCode'), record.record_id, record.computer)


@artifact_processor
def windowsUpdateClientEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Update Title',
                    'Update ID', 'Revision Number', 'Service ID', 'Error Code (as stored)',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [update_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
