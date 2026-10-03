"""Windows app package deployment event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads five Microsoft-Windows-AppXDeployment-Server events of the
AppXDeploymentServer Operational event log: a deployment operation started
(603), was de-queued and is running for a user (607), finished successfully
(400) or failed (401, 404). The Event IDs, field names, message text and the
operation names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'App Package Deployment Events'
_LOG = 'microsoft-windows-appxdeploymentserver%4operational.evtx'
_PROVIDER = 'Microsoft-Windows-AppXDeployment-Server'

# Event ID: a short label made of words of the provider's message for it (see notes).
_EVENTS = {
    '400': 'Deployment operation finished successfully',
    '401': 'Deployment operation failed',
    '404': 'AppX Deployment operation failed for package',
    '603': 'Started deployment operation',
    '607': 'Deployment operation de-queued and running for user',
}
# DeploymentOperation values the provider's value map names the same way on every build checked
# (see notes); from 34 on the builds disagree, so those are left as the number.
_OPERATIONS = {
    '0': 'Invalid',
    '1': 'Add',
    '2': 'Remove',
    '3': 'Update',
    '4': 'Stage',
    '5': 'DeStage',
    '6': 'Register',
    '7': 'Get list of registered packages',
    '8': 'Fix staged packages',
    '9': 'Delete all files of the package',
    '10': 'RegisterByPackageFullName',
    '11': 'StageUserData',
    '12': 'PreRegisterPackage',
    '13': 'MovePackageOperation',
    '14': 'AddVolumeOperation',
    '15': 'DeleteVolumeOperation',
    '16': 'SetVolumeOfflineOperation',
    '17': 'SetVolumeOnlineOperation',
    '18': 'GetDefaultVolumeOperation',
    '19': 'SetDefaultVolumeOperation',
    '20': 'RegisterByPackageFamilyName',
    '22': 'GeneratePreviewTilesOperation',
    '23': 'ResetApplicationDataOperation',
    '24': 'ResetAllApplicationDataForUserOperation',
    '25': 'ResumeOperation',
    '26': 'ResetSingleApplicationDataOperation',
    '27': 'OnDemandRegisterOperation',
    '28': 'AddByPackageFamilyNameOperation',
    '29': 'ProvisionPackageOperation',
    '30': 'AddFromAppInstallerOperation',
    '31': 'UpdateUsingAppInstallerOperation',
    '32': 'RegisterPackageOnLogonForUserOperation',
    '33': 'DeprovisionPackageOperation',
}

__artifacts_v2__ = {
    "appPackageDeploymentEvents": {
        "name": "App Package Deployment Events",
        "description": "Microsoft-Windows-AppXDeployment-Server events of the AppXDeploymentServer Operational event "
                       "log: a deployment operation on an app package started (603), was de-queued and is running "
                       "for a user (607), finished successfully (400) or failed (401, 404), with the operation, the "
                       "package, the path, the calling process and the error the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-AppXDeploymentServer%4Operational.evtx the paths match with "
                 "python-evtx and reports, one row per record, the records whose provider is "
                 "Microsoft-Windows-AppXDeployment-Server and whose Event ID is 400, 401, 404, 603 or 607. The "
                 "provider's manifest sends the five events to the "
                 "Microsoft-Windows-AppXDeploymentServer/Operational channel with the messages 'Started deployment "
                 "%1 operation on a package with main parameter %2 and Options %3 and %4. See "
                 "http://go.microsoft.com/fwlink/?LinkId=235160 "
                 "for help diagnosing app deployment issues.' (603, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml#L3525-L3544), "
                 "'Deployment %1 operation on package %2 has been de-queued and is running for user SID %3.' (607, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml#L3583-L3599), "
                 "'Deployment %1 operation with target volume %4 on Package %2 from: %3 finished successfully.' "
                 "(400, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml#L1228-L1266), "
                 "'Deployment %1 operation with target volume %5 on Package %2 from: %3 failed with error %4. See "
                 "http://go.microsoft.com/fwlink/?LinkId=235160 "
                 "for help diagnosing app deployment issues.' (401, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml#L1267-L1310) "
                 "and 'AppX Deployment operation failed for package %2 with error %3. The specific error text for "
                 "this failure is: %1' (404, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml#L1344-L1364). "
                 "These are the entries of the Microsoft-Windows-AppXDeployment-Server manifest as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository; the manifests "
                 "that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same "
                 "five messages, except that the 16299.15 one has a colon after 'main parameter' and after 'Options' "
                 "in 603 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-AppXDeployment-Server.xml). "
                 "Event is a short label made of words of that message, in the message's order. Operation (as "
                 "stored) is the field DeploymentOperation (400, 401, 603 and 607), Package is PackageFullName (400, "
                 "401, 404 and 607), Path is Path (400, 401 and 603; the 'main parameter' of 603 and the 'from' of "
                 "400 and 401), Running for User SID is UserSid (607), Calling Process is CallingProcess (all five), "
                 "Error Code (as stored) is ErrorCode (401 and 404) and Error is SummaryError (404). Each is as "
                 "python-evtx renders it with any white space at either end removed, and a column whose field the "
                 "record does not carry is blank. That removal changed every tested Path of 400 and 401 and no other "
                 "tested value: the record stores a space, or a space, text in brackets and a space (795 values of "
                 "400 and 19 of 401), and the row shows it without the two spaces. User SID is the SID the record's "
                 "Security element stores. Operation Name is the name the provider's value map "
                 "DeploymentOperationEnumMap gives the number, and is filled for 0 to 20 and 22 to 33 only. Every "
                 "source read that holds one of those values gives it the same name: the provider manifests of "
                 "Windows 10 builds 10240, 17134 and 18990 published in repnz's etw-providers-docs repository "
                 "(https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-10240/Microsoft-Windows-AppXDeployment-Server.xml#L113-L137, "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-17134/Microsoft-Windows-AppXDeployment-Server.xml#L164-L197 "
                 "and "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-18990/Microsoft-Windows-AppXDeployment-Server.xml#L120-L157), "
                 "and the map in the AppXDeploymentServer.dll of the four tested images (builds 16299, 17763, 19041 "
                 "and 22621), read from the file's WEVT_TEMPLATE resource with the text taken from the message table "
                 "of its en-US .mui file. The map of build 10240 ends at 23, of build 16299 at 31 and of build 17134 "
                 "at 32. From 34 on the builds disagree (34 is StageInContainerOperation on builds 18990 and 19041 "
                 "and SetMutablePackagesOnlineOperation on build 22621), so Operation Name is blank for 34 and "
                 "above, and no map read holds 21. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 577, 695, 604 and 548 rows "
                 "in that order: 836 of 607, 795 of 400, 745 of 603, 19 of 401 (3 on lonewolf_win10 and 16 on "
                 "pc_mus_001_win11) and 29 of 404 (6 on lonewolf_win10, 18 on pc_mus_001_win11 and 5 on "
                 "szechuan_win10), every record version 0. Error Code (as stored) and Error are therefore blank on "
                 "every row of af_case2_win10. The operations on the 2,395 rows that have one were 6 Register (713 "
                 "rows), 4 Stage (704), 20 RegisterByPackageFamilyName (211), 12 PreRegisterPackage (196), 11 "
                 "StageUserData (177), 2 Remove (131), 5 DeStage (122), 1 Add (45), 27 OnDemandRegisterOperation "
                 "(24), 10 RegisterByPackageFullName (19), 19 SetDefaultVolumeOperation (18), 29 "
                 "ProvisionPackageOperation (16), 22 GeneratePreviewTilesOperation (12) and 34 (7 rows of 603 on "
                 "pc_mus_001_win11, whose Operation Name is blank). Running for User SID equals User SID on 829 of "
                 "the 836 rows of 607 and differs on 7 (3 on af_case2_win10 and 4 on lonewolf_win10). User SID was "
                 "S-1-5-18 on 1,175 of the 2,424 rows. Calling Process is the text NULL on 98 rows of 607 and blank "
                 "on 98 rows of 400; on pc_mus_001_win11 it is powershell.exe on 10 rows each of 603, 607, 401 and "
                 "404. A 603 row carries no package name. Package is blank on 9 of the 29 rows of 404. All 19 rows "
                 "of 401 and 708 of the 795 rows of 400 have an earlier 607 row with the same Package and Operation "
                 "(as stored); the other 87 rows of 400 have none in the log. Each of the 19 rows of 401 is followed "
                 "within three rows by a 404 row with the same Package and Error Code (as stored). Error Code (as "
                 "stored) is 0x and eight hexadecimal digits on all 48 rows that have one; what a code stands for is "
                 "not looked up. Rows are in the order the log file holds its records. That was rising Record ID on "
                 "af_case2_win10; on each of the other three logs Record ID falls once from one row to the next and "
                 "Event Time (UTC) falls at the same row, and sorting a log's rows by Record ID leaves no row "
                 "earlier than the one before it except 1 on af_case2_win10. Computer held one value on every row of "
                 "pc_mus_001_win11 and szechuan_win10; af_case2_win10 and lonewolf_win10 hold two names. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the four tested logs rendered. A log marked dirty is read past the "
                 "chunks its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read: the provider's other events. The four "
                 "tested logs hold 14,592 records of 108 other Event IDs.",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-AppXDeploymentServer%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 577 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 695 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 604 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 548 rows",
        },
    },
}


def deployment_row(record):
    operation = record.get('DeploymentOperation')
    return (record.time, record.event_id, _EVENTS[record.event_id], operation,
            _OPERATIONS.get(operation, ''), record.get('PackageFullName'), record.get('Path'),
            record.get('UserSid'), record.get('CallingProcess'), record.get('ErrorCode'),
            record.get('SummaryError'), record.user_sid, record.record_id, record.computer)


@artifact_processor
def appPackageDeploymentEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Operation (as stored)',
                    'Operation Name', 'Package', 'Path', 'Running for User SID', 'Calling Process',
                    'Error Code (as stored)', 'Error', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [deployment_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
