"""AppModel Runtime event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-AppModel-Runtime record of the provider's Admin event log: a process created for an
application of a package, a process added to a package's Desktop AppX container, containers created and destroyed,
AppContainers created, updated and deleted, package status changes, and the provider's other events of that log.
The Event IDs, the message text and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'AppModel Runtime Events'
_LOG = 'Microsoft-Windows-AppModel-Runtime%4Admin.evtx'
_PROVIDER = 'Microsoft-Windows-AppModel-Runtime'

# The fields that name a package (no manifest entry holds two of them) and the two fields with a column of their
# own; every other field goes to Other Fields.
_PACKAGE = ('PackageFullName', 'PackageName', 'PackageFamilyName')
_IMAGE = 'ImageName'
_PROCESS = 'ProcessID'

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '2': '%2: Cannot create the process for package %1 because an error was encountered.',
    '3': '%2: Cannot create the process for package %1 because an error was encountered while querying the '
         'fast cache.',
    '4': '%2: Cannot create the process for package %1 because an error was encountered while preparing the '
         'App credentials.',
    '5': '%2: Cannot create the process for package %1 because an error was encountered while checking the '
         'user-level package status.',
    '6': '%2: Cannot create the process for package %1 because an error was encountered while checking the '
         'machine-level package status.',
    '7': '%2: Cannot create the process for package %1 because an error was encountered while verifying the '
         'App credentials.',
    '8': 'App %1 was terminated with error %2 because of an issue with application binary %3.',
    '11': 'App %1 prevented the load of generated binary %3 due to error %2.',
    '12': 'An app prevented the load of a binary due to error %1.',
    '14': '%2: Package runtime information %1 is corrupted (address=%5, size=%3, offset=%4, section=%6, '
          'processid=%7).',
    '15': '%2: Package runtime information %1 is missing expected data (address=%4, size=%3, section=%5, '
          'processid=%6).',
    '16': '%2: Package runtime information %1 contains conflicting data (address=%5, size=%3, offset=%4, '
          'section=%6, processid=%7).',
    '17': '%2: Package runtime information %1 contains unexpected data (address=%5, size=%3, offset=%4, '
          'section=%6, processid=%7).',
    '18': '%2: Package runtime information %1 failed to load (processid=%3).',
    '19': 'Package runtime information %1 failed to load because exception %2 occurred.',
    '20': '%2: Cannot create the process for package %1 because an error was encountered while loading the '
          'runtime information.',
    '21': 'CreateAppContainerProfile failed for AppContainer %2 with error %1.',
    '22': 'DeleteAppContainerProfile failed for AppContainer %2 with error %1.',
    '23': 'UpdateAppContainerProfile failed for AppContainer %2 with error %1.',
    '24': 'CreateAppContainerProfile failed with error %1 because it was unable to create registry key %2.',
    '25': 'CreateAppContainerProfile failed with error %1 because it was unable to set security on registry key %2.',
    '26': 'AppContainer profile failed with error %1 because it was unable to delete registry key %2.',
    '27': 'CreateAppContainerProfile failed with error %1 because it was unable to create folder %2.',
    '28': 'CreateAppContainerProfile failed with error %1 because it was unable to set attributes on folder %2.',
    '29': 'CreateAppContainerProfile failed with error %1 because it was unable to verify the existence of '
          'registry key %2.',
    '30': 'CreateAppContainerProfile failed with error %1 because it was unable to verify the existence of '
          'folder %2.',
    '31': 'CreateAppContainerProfile failed with error %1 because it was unable to find the users local app '
          'data folder.',
    '32': 'AppContainer profile failed with error %1 because it was unable to delete folder %2 or its contents.',
    '33': 'AppContainer profile failed with error %1 because it was unable to look up the AppContainer name.',
    '34': 'AppContainer profile failed with error %1 because it was unable to look up the AppContainer display name.',
    '35': 'CreateAppContainerProfile failed with error %1 because it was unable to register with the firewall.',
    '36': 'DeleteAppContainerProfile failed with error %1 because it was unable to unregister with the firewall.',
    '37': 'App Container profile failed with error %1 because it was unable to register the AppContainer SID.',
    '38': 'DeleteAppContainerProfile failed with error %1 because it was unable to unregister the AppContainer SID.',
    '39': 'Successfully created AppContainer %1.',
    '40': 'AppContainer %1 was not created because it already exists.',
    '41': 'Successfully deleted AppContainer %1.',
    '42': 'Successfully updated AppContainer %1.',
    '43': '%2: Package runtime information %1 is missing expected data (address=%4, size=%3, section=%5, '
          'processid=%6).',
    '44': '%2: Application identity not accessible while loading package runtime information %1 (address=%4, '
          'size=%3, processid=%5).',
    '45': 'Failed with %1 while retrieving AppContainer %2 information during interaction with Restricted '
          'AppContainer.',
    '46': 'Failed with %1 while retrieving AppContainer information during interaction with Restricted AppContainer.',
    '47': 'Failed with %1 while retrieving AppContainer information.',
    '48': 'Failed to create shared context object for Restricted AppContainer %2 with %1.',
    '49': 'Failed to activate Restricted AppContainer %2 with %1.',
    '50': 'Creation of Restricted AppContainer %2 failed with %1 because an invalid capability was specified.',
    '51': 'Opening existing Restricted AppContainer %2 failed with %1 because the capabilities storage value '
          'could not be read.',
    '52': 'Failed to create the capabilities storage value for Restricted AppContainer %2 with %1.',
    '53': 'The package %1 requires validation.',
    '54': 'Modification was detected in package %1.',
    '55': 'Failed to terminate app with package %1.',
    '56': 'Validation of app with package %1 was successful.',
    '57': 'Failed with %1 to retrieve the trust state of the package %2 folder.',
    '58': 'App Integrity check failed with %1 while checking %2.',
    '59': 'App Integrity terminated an application.',
    '60': 'App Integrity check for %1 timed out.',
    '61': '%2: Cannot create the process for package %1 because an error was encountered while performing '
          'the integrity check.',
    '62': 'Deployment server integrity check of package %1 failed with %2.',
    '63': 'Failed with %1 retrieving AppModel Runtime group policy values.',
    '64': 'Failed with %1 validating AppModel Runtime group policy values.',
    '65': 'Failed with %1 retrieving AppModel Runtime status for package %2.',
    '66': 'Failed with %1 retrieving AppModel Runtime status for package %2 for user %3.',
    '67': 'Failed with %1 modifying AppModel Runtime status for package %2 (current status = %4, desired '
          'status = %3).',
    '68': 'AppModel Runtime status for package %1 successfully updated to %2 (previous status = %3).',
    '69': 'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (clear=%4, set=%5).',
    '70': 'Successfully updated AppModel Runtime status for package %1 for user %2 (clear=%3, set=%4).',
    '71': 'Failed with %1 modifying AppModel Runtime status version (context = %2).',
    '73': '%2: Cannot create the process for package %1 because an error was encountered while performing '
          'the app data creation.',
    '74': 'Package runtime information %1 failed to refresh because the following error %2 occurred in '
          'operation type %3.',
    '75': 'error %2: Cannot register the %1 package because the following error was encountered while '
          'opening the HKEY_USERS registry key',
    '76': 'error %4: Cannot register the %1 package because the following error was encountered while '
          'enumerating to remove the %2\\%3 package family registry key',
    '77': 'error %4 : Cannot register the %1 package because the following error was encountered while '
          'creating the %2\\%3 package family registry key',
    '78': 'error %4: Cannot register the %1 package because the following error was encountered while '
          'removing the %2\\%3 package family registry key',
    '79': '%2: Package family %1 runtime information is corrupted.',
    '80': '%2: Package family %1 runtime information is corrupted but we cannot repair it at this time.',
    '81': 'Failed with %1 to get IsPackageStageInPlace info from State Repository cache for package %2.',
    '201': 'Created process %1 for application %4 in package %2.',
    '202': '%4: Cannot create the process for package %1 because an error was encountered.',
    '203': '%4: Cannot create the process for package %1 because an error was encountered while preparing '
           'for activation.',
    '204': '%4: Cannot create the process for package %1 because an error was encountered while elevating the token.',
    '205': '%4: Cannot create the process for package %1 because UI Access is not supported for Desktop AppX '
           'processes.',
    '206': '%4: Cannot create the process for package %1 because an error was encountered while adjusting the token.',
    '207': '%4: Cannot create the process for package %1 because an error was encountered while launching.',
    '208': '%4: Cannot create the process for package %1 because an error was encountered while configuring runtime.',
    '209': '%4: Cannot create the process for package %1 because an error was encountered while resuming the thread.',
    '210': 'Created Desktop AppX container %3 for package %1.',
    '211': 'Added process %1 to Desktop AppX container %3 for package %2.',
    '212': '%1: Cannot add process %2 to Desktop AppX container %4 for package %3 because an error was encountered.',
    '213': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
           'creating the job.',
    '214': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
           'creating the description.',
    '215': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
           'converting the job.',
    '216': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
           'configuring the runtime.',
    '217': 'Destroyed Desktop AppX container %2 for package %1.',
    '218': 'Cannot destroy Desktop AppX container %2 for package %1.',
    '219': 'PSMFlags for Desktop AppX process %1 with applicationID %2 is %3.',
}

# The build 26100 manifest rewords 69 and 70 and gives them other fields; a record that carries the earlier
# manifests' DesiredStatus field is given the earlier text (see notes).
_EARLIER_FIELD = 'DesiredStatus'
_EARLIER = {
    '69': 'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (current status = %5, '
          'desired status = %4).',
    '70': 'AppModel Runtime status for package %1 for user %2 successfully updated to %3 (previous status = %4).',
}


__artifacts_v2__ = {
    "appModelRuntimeEvents": {
        "name": "AppModel Runtime Events",
        "description": "Microsoft-Windows-AppModel-Runtime records of the provider's Admin event log, such as a "
                       "process created for an application of a package with its image name and process ID, Desktop "
                       "AppX containers created and destroyed and AppContainers created, with each record's other "
                       "fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-AppModel-Runtime%4Admin.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-AppModel-Runtime, "
                 "whatever its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 95 events to "
                 "this log's channel, each version 0; they sit among lines 239 to 2275 of the file, with entries of "
                 "the provider's other channels between them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-AppModel-Runtime.xml#L239-L2275). "
                 "The manifest of Windows 11 build 22621.819 holds the same 95, that of Windows 10 build 19041.208 "
                 "holds 94 of them (not 219) and those of builds 16299.15 and 17763.107 hold 93 (not 81 and not 219) "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppModel-Runtime.xml#L239-L2275, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-AppModel-Runtime.xml#L239-L2259, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-AppModel-Runtime.xml#L229-L2234 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-AppModel-Runtime.xml#L229-L2234), "
                 "with the same messages and fields except 69 and 70. These are the manifests nasbench's "
                 "EVTX-ETW-Resources repository publishes. Event is, for the record's Event ID, the first sentence "
                 "of the first line of the build 26100 message: the first line that holds more than white space, "
                 "with each run of white space made one space, cut after the first period that a space or the end of "
                 "the line follows (whole when it has none), with its placeholders (such as %1) as the manifest "
                 "writes them. A placeholder is an insertion string for a data item of the event's template by its "
                 "position (Microsoft's Defining Events page: 'to include the third data item in the template, "
                 "include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. The four earlier manifests word 69 and 70 differently, 'Failed with %1 "
                 "modifying AppModel Runtime status for package %2 for user %3 (current status = %5, desired status "
                 "= %4).' and 'AppModel Runtime status for package %1 for user %2 successfully updated to %3 "
                 "(previous status = %4).', and give them the fields DesiredStatus and CurrentStatus where build "
                 "26100 gives StatusToClear and StatusToSet. A 69 or 70 record that carries a DesiredStatus field is "
                 "given that earlier text, as each of the 2,265 tested records of the two was; the build 26100 text "
                 "of the two is unexercised. Event is blank for an Event ID outside the 95, which no tested record "
                 "had. Package is the PackageFullName, PackageName or PackageFamilyName field, whichever the record "
                 "carries: the manifests give PackageFullName to 32 Event IDs, PackageName to 18 (201 to 218) and "
                 "PackageFamilyName to 2 (79 and 80), and no entry holds two of them. If a record did, the first in "
                 "that order would be shown and the other listed in Other Fields. 3,009 of the 4,086 tested rows "
                 "have a Package. Image Name is the ImageName field and Process ID the ProcessID field. On the 72 "
                 "tested rows of 201, whose message begins 'Created process %1 for application %4 in package %2.', "
                 "Image Name is a file name ending .exe (7 distinct names, Notepad.exe on 24 rows) and the Message "
                 "field begins [LaunchProcess] on 51 and [FinishPackageActivation] on 21. Process ID is on those 72 "
                 "rows and on the 306 rows of 211 ('Added process %1 to Desktop AppX container %3 for package %2.'), "
                 "a decimal number on each and on none the process ID of the record's own Execution element. 58 of "
                 "the 72 rows of 201 have a 211 row with the same Process ID and Package. Image Name and Process ID "
                 "are blank on every row of af_case2_win10 and lonewolf_win10, whose logs hold no 201 or 211 record. "
                 "210, 211 and 217 name a Desktop AppX container by a ContainerId, written in braces and capitals on "
                 "442 tested records and in lower case without braces on 166. Compared without braces or case, each "
                 "of the 152 tested containers has one 210 row, and each of the 306 rows of 211 and the 150 rows of "
                 "217 follows the 210 row of its container and has the same Package. The 1,004 tested rows of 39, "
                 "40, 41 and 42 (an AppContainer created, already there, deleted and updated) carry one field, "
                 "AppContainerName, listed in Other Fields. 69 and 70 carry a User field, a SID on each of the 2,265 "
                 "tested records, and status numbers, reported as stored; what the numbers stand for is not "
                 "established here. ErrorCode is a decimal number on the tested 5, 21, 36 and 69 records and 0x with "
                 "hexadecimal digits on 79 and 80, as stored. The 71 records of 219 on pc_mus_001_win11, the only "
                 "tested records of that event, store a ProcessingErrorData element in place of event data, with the "
                 "children ErrorCode, DataItemName and EventPayload. That element is not read, so those rows have "
                 "the record's own columns and no field. Other Fields lists every other named field that holds more "
                 "than white space as 'name: value', in the record's order, joined with ' | '. Each value is as "
                 "python-evtx renders it with any white space at either end removed (1 tested value had some, the "
                 "ErrorMessage of the 5 record). A data item that has no name is not shown, and no tested record had "
                 "one. If a record named a field twice the last would be read. Apart from those 71, the tested "
                 "records carried the field names their image's build manifest gives the event. Tested on the logs "
                 "of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, "
                 "build 22621; szechuan_win10, build 19041), which gave 604, 688, 942 and 1,852 rows in that order; "
                 "the two captures of a Windows 11 build 26200 machine hold no such log. 17 of the 95 Event IDs "
                 "occur: 39, 40, 41 and 42 on all four images, 69 and 70 on the three other than pc_mus_001_win11, "
                 "201, 210, 211 and 217 on pc_mus_001_win11 and szechuan_win10, and 5, 21, 36, 68, 79, 80 and 219 on "
                 "one image each. The other 78 Event IDs are unexercised. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the record stores, counted in "
                 "UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on 3,075 tested rows, S-1-5-19 "
                 "on 70 and an S-1-5-21 account on 941. Record ID is the record's EventRecordID and Computer the "
                 "machine name the record stores, which held one value on pc_mus_001_win11 and two on each of the "
                 "other three. Rows are in the order the file holds them, which was rising Record ID on three tested "
                 "logs. On szechuan_win10 the file begins with records 1866 to 1966 and goes on with 115 to 1865, so "
                 "its 101 latest rows come first. In time order 3 rows are earlier than the row before them (1 each "
                 "on af_case2_win10, lonewolf_win10 and szechuan_win10, the last where its Record ID falls). Every "
                 "record of the tested logs rendered and is the provider's. A record python-evtx cannot render, or "
                 "whose XML does not parse, is counted in the run log and not reported. A log marked dirty is read "
                 "past the chunks its header counts, and the run log says how many records came from there. Reading "
                 "needs the python-evtx package (pip install python-evtx). Not read: the events these manifests send "
                 "to the provider's Analytic, Debug and Diagnostics channels and to the Application log.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-AppModel-Runtime%4Admin.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 604 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 688 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 942 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1852 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def event_text(record):
    if record.event_id in _EARLIER and _EARLIER_FIELD in record.fields:
        return _EARLIER[record.event_id]
    return _EVENTS.get(record.event_id, '')


def app_model_row(record):
    package = next((name for name in _PACKAGE if name in record.fields), '')
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in (package, _IMAGE, _PROCESS) and record.get(name))
    return (record.time, record.event_id, event_text(record), record.get(package), record.get(_IMAGE),
            record.get(_PROCESS), other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def appModelRuntimeEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Package', 'Image Name', 'Process ID',
                    'Other Fields', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [app_model_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
