"""Windows servicing (package and optional feature) event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-Servicing events 1 to 16 of the Setup event log:
changes to a package (1 to 6) and an update of a package, such as an optional
Windows feature, being turned on or off (7 to 16). The Event IDs, the message
text and the element names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Windows Servicing Events'
_LOG = 'setup.evtx'
_PROVIDER = 'Microsoft-Windows-Servicing'

# Event ID: a short label made of words of the provider's message for it (see notes).
_EVENTS = {
    '1': 'Initiating changes for package',
    '2': 'Package was successfully changed to the state',
    '3': 'Package failed to be changed to the state',
    '4': 'A reboot is necessary before package can be changed to the state',
    '5': 'The servicing request received for package cannot be satisfied since the package is not applicable',
    '6': 'Package failed to be changed to the state and is now partially installed',
    '7': 'Initiating changes to turn on update of package',
    '8': 'Initiating changes to turn off update of package',
    '9': 'Selectable update of package was successfully turned on',
    '10': 'Selectable update of package was successfully turned off',
    '11': 'Update of package failed to be turned on',
    '12': 'Update of package failed to be turned off',
    '13': 'A reboot is necessary before the selectable update of package can be turned on',
    '14': 'A reboot is necessary before the selectable update of package can be turned off',
    '15': 'Selectable update of package was successfully turned off with its payload removed',
    '16': 'Update of package failed to be turned off. Payload removal was requested',
}

__artifacts_v2__ = {
    "windowsServicingEvents": {
        "name": "Windows Servicing Events",
        "description": "Microsoft-Windows-Servicing events 1 to 16 of the Setup event log: changes to a package such "
                       "as an update (initiated, changed to a state, failed, or waiting for a reboot) and an update "
                       "of a package, such as an optional Windows feature, being turned on or off, with the package, "
                       "the states, the error code and the client the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Setup.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-Servicing and whose Event ID is 1 to 16. The "
                 "provider's manifest sends those sixteen events to the Setup channel with the messages 'Initiating "
                 "changes for package %1. Current state is %2. Target state is %4. Client id: %6.' (1), 'Package %1 "
                 "was successfully changed to the %2 state.' (2), 'Package %1 failed to be changed to the %2 state. "
                 "Status: %4.' (3), 'A reboot is necessary before package %1 can be changed to the %2 state.' (4), "
                 "'The servicing request received for package %1 cannot be satisfied since the package is not "
                 "applicable.' (5), 'Package %1 failed to be changed to the %2 state and is now partially installed. "
                 "Status: %4.' (6), 'Initiating changes to turn on update %1 of package %2. Client id: %4.' (7), "
                 "'Initiating changes to turn off update %1 of package %2. Client id: %4.' (8), 'Selectable update "
                 "%1 of package %2 was successfully turned on.' (9), 'Selectable update %1 of package %2 was "
                 "successfully turned off.' (10), 'Update %1 of package %2 failed to be turned on. Status: %3.' "
                 "(11), 'Update %1 of package %2 failed to be turned off. Status: %3.' (12), 'A reboot is necessary "
                 "before the selectable update %1 of package %2 can be turned on.' (13), 'A reboot is necessary "
                 "before the selectable update %1 of package %2 can be turned off.' (14), 'Selectable update %1 of "
                 "package %2 was successfully turned off with its payload removed.' (15) and 'Update %1 of package "
                 "%2 failed to be turned off. Payload removal was requested. Status: %3.' (16) "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Servicing.xml#L70-L332). "
                 "These are the entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository; the manifests that repository publishes for "
                 "Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same sixteen entries at the same "
                 "lines "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Servicing.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Servicing.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Servicing.xml). "
                 "Event is a short label made of words of that message, in the message's order. Each tested record "
                 "carries its values in a UserData element (CbsPackageInitiateChanges on 1, CbsPackageChangeState on "
                 "2 and 4, CbsUpdateChangeState on 7, 8, 9, 10 and 13), and the columns are read from its child "
                 "elements by name; those names are not the data names the manifest lists. Package is "
                 "PackageIdentifier, Update is UpdateName (7, 8, 9, 10 and 13 on the tested rows), Initial State is "
                 "InitialPackageStateTextized (1), Intended State is IntendedPackageStateTextized (1, 2 and 4), "
                 "Error Code (as stored) is ErrorCode (every tested event but 1) and Client is Client. Each is as "
                 "python-evtx renders it with any white space at either end removed (no tested value had any), and a "
                 "column whose element the record does not carry is blank. The records also store each state as a "
                 "number (InitialPackageState, IntendedPackageState), which is not reported; on the tested rows 5000 "
                 "came with Absent, 5112 with Installed and 5080 with Superseded. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the record stores, counted in "
                 "UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 24, 10, 26 and 0 rows in "
                 "that order: 20 of 1, 16 of 2, 13 of 4, 3 each of 7, 9 and 13 (pc_mus_001_win11) and 1 each of 8 "
                 "and 10 (af_case2_win10), each reported record version 0. No tested log held a 3, 5, 6, 11, 12, 14, "
                 "15 or 16 record, so those eight events are unexercised: they are read by the element names the "
                 "tested events use, which is not confirmed for them. On the 20 rows of 1 the Initial State and "
                 "Intended State were Absent and Installed on 15, Installed and Absent on 2, Superseded and Absent "
                 "on 2 and Installed and Installed on 1; Intended State was Installed on all 29 rows of 2 and 4. "
                 "Each of those 29 rows has an earlier 1 row with the same Package. Error Code (as stored) was 0x0 "
                 "on every row of 2, 4, 9, 10 and 13 and blank on every row of 1, 7 and 8. Client was "
                 "WindowsUpdateAgent on 24 rows, UpdateAgentLCU on 18, Windows Optional Component Manager on 9, "
                 "CbsTask on 4, LCUReservicing on 3 and DISM Package Manager Provider on 2. The 9 rows of 7, 13 and "
                 "9 on pc_mus_001_win11 are three updates being turned on, HypervisorPlatform, "
                 "VirtualMachinePlatform and Microsoft-Windows-Subsystem-Linux, each with a 7 row, then a 13 row, "
                 "then a 9 row; the 8 and 10 rows on af_case2_win10 are Windows-Defender-Default-Definitions being "
                 "turned off. Update is blank on every row of lonewolf_win10, which holds no row of 7 to 16. The "
                 "Package of all 16 rows of 2 is KB and digits. For 12 of them the Windows Update Client Events "
                 "artifact reports an installation successful (19) row whose title holds that KB number in brackets "
                 "within 7 minutes of the row; for 3 it reports no such row at all. Rows are in the order the log "
                 "file holds its records, which was rising Record ID and time on every tested log. Computer held one "
                 "value on af_case2_win10 and on pc_mus_001_win11 and two on lonewolf_win10. A record python-evtx "
                 "cannot render, or whose XML does not parse, is counted in the run log and not reported; every "
                 "record of the tested logs rendered. A log marked dirty is read past the chunks its header counts, "
                 "and the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx). Not read: the provider's other events. No tested Setup log held a record of "
                 "another Event ID or of another provider.",
        "paths": ('*/Windows/System32/winevt/Logs/Setup.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 24 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 26 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def servicing_row(record):
    return (record.time, record.event_id, _EVENTS[record.event_id], record.get('PackageIdentifier'),
            record.get('UpdateName'), record.get('InitialPackageStateTextized'),
            record.get('IntendedPackageStateTextized'), record.get('ErrorCode'), record.get('Client'),
            record.record_id, record.computer)


@artifact_processor
def windowsServicingEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Package', 'Update', 'Initial State',
                    'Intended State', 'Error Code (as stored)', 'Client', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [servicing_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
