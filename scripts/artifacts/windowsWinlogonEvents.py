"""Windows Winlogon event parsers for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-Winlogon records of the System event log with
Event ID 7001 and 7002, the user logon and logoff notifications Winlogon logs
for the Customer Experience Improvement Program, and the records of Winlogon's
own Operational log with Event ID 1, 2, 811 and 812: authentication started
and stopped, and a notification subscriber beginning and finishing a
notification event. Each record is one row. Event IDs, field names and message
text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Winlogon Logon and Logoff Notifications'
_LOG = 'System.evtx'
_PROVIDER = 'Microsoft-Windows-Winlogon'

# The provider's message for each event, shortened (see notes).
_EVENTS = {
    '7001': 'User logon notification',
    '7002': 'User logoff notification',
}

_OPERATIONAL_LABEL = 'Winlogon Operational Events'
_OPERATIONAL_LOG = 'Microsoft-Windows-Winlogon%4Operational.evtx'

# The provider's message for each Operational event, shortened (see notes).
_OPERATIONAL_EVENTS = {
    '1': 'Authentication started',
    '2': 'Authentication stopped',
    '811': 'A notification subscriber began handling a notification event',
    '812': 'A notification subscriber finished handling a notification event',
}

__artifacts_v2__ = {
    "winlogonNotifications": {
        "name": "Winlogon Logon and Logoff Notifications",
        "description": "User logon and logoff notifications Winlogon writes to the System event log, Event ID 7001 "
                       "and 7002, with the user SID and the session each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from System.evtx, named in the report's located-at line; only Microsoft-Windows-Winlogon "
                 "records with Event ID 7001 or 7002 are read. Event is the provider's message, shortened: the "
                 "message of 7001 is 'User Logon Notification for Customer Experience Improvement Program' and that "
                 "of 7002 'User Logoff Notification for Customer Experience Improvement Program' (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L1815-L1829 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L1830-L1844; "
                 "that repository's manifests for Windows 10 builds 16299.125, 17763.107 and 19041.208 and Windows "
                 "11 build 26100.1742 define the two events the same way, and it holds none for build 26200). User "
                 "SID and Session are the record's UserSid and TSId fields, as stored. The record's own Security "
                 "element, which held S-1-5-18 on every row of the tested images, is not reported. Event Time (UTC) "
                 "is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME "
                 "the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, in place "
                 "of python-evtx 0.8.1's conversion through a floating-point number, which can differ by "
                 "microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores: it held "
                 "one value on every row of af_case2_win10, pc_mus_001_win11 and windows11_arm_known_20261001, and "
                 "two on lonewolf_win10 and szechuan_win10. Rows are in the order the log holds them, which is the "
                 "order of Record ID; on lonewolf_win10, szechuan_win10 and windows11_arm_known_20261001 that is not "
                 "the order of Event Time (UTC). The tested logs give 36, 7, 21 and 21 rows on af_case2_win10, "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10 and 126 on windows11_arm_known_20261001, the "
                 "System log of a Windows 11 build 26200 ARM64 virtual machine exported with wevtutil on 1 October "
                 "2026: 108 logon and 103 logoff notifications. Every row holds an account SID (S-1-5-21-...) and a "
                 "session number, which is 1 on 193 of the 211 rows. User SID held one value on every row of "
                 "pc_mus_001_win11, two on af_case2_win10, lonewolf_win10 and the capture, and five on "
                 "szechuan_win10. On the four public images every logon notification has a User Profile Service "
                 "Event ID 1 with the same SID and session 1.7 to 750.7 ms after it, and every logoff notification "
                 "an Event ID 3 with the same SID and session 7.8 to 245.7 ms before it (see User Profile Service "
                 "Events): 44 and 41 pairs, with no notification of either log left over. For the 7 account profiles "
                 "whose ProfileList key stores times (see User Profile List), Profile Load Time is 10.7 to 397.7 ms "
                 "after the SID's last logon notification and Profile Unload Time within 22.0 ms of its last logoff "
                 "notification. On af_case2_win10, lonewolf_win10, szechuan_win10 and the capture one SID in the "
                 "rows has no ProfileList subkey, with 2 rows on each. On pc_mus_001_win11 5 rows are earlier than "
                 "the earliest row of Windows Security Logons, and the capture, whose Security log was cleared in "
                 "the session, gives no Windows Security Logons row. A row records a notification Winlogon logged "
                 "for the session; it does not record how the user logged on, and a logon notification is not always "
                 "followed by a logoff notification: logon rows outnumber logoff rows by 1 on lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10 and by 2 on the capture. Not reported: records of other "
                 "providers with the same Event IDs, of which the tested logs held Netwtw06 7002 (12 on "
                 "pc_mus_001_win11) and Service Control Manager 7001 (1 on szechuan_win10, 3 on the capture). No "
                 "Microsoft-Windows-Winlogon record with another Event ID was in the tested System logs; Winlogon's "
                 "own Operational log is read by Winlogon Operational Events. A record python-evtx cannot render, or "
                 "whose XML does not parse, "
                 "is counted in the run log and not reported; every record of the tested logs rendered, among them "
                 "the 72 TPM event 27 records of the capture's log, which python-evtx renders only with the array "
                 "value types scripts/windows_evtx.py adds. A log marked dirty is read past the chunks its "
                 "header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "log-in",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 126 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 36 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 7 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 21 rows",
        },
    },
    "winlogonOperational": {
        "name": "Winlogon Operational Events",
        "description": "Records of Winlogon's Operational event log: authentication started and stopped, and each "
                       "notification subscriber beginning and finishing a notification event, with the event number "
                       "and subscriber name the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Winlogon%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, the Microsoft-Windows-Winlogon records with Event ID 1, 2, 811 or 812."
                 " Event is the provider's message, shortened: 'Authentication started.' for 1, 'Authentication "
                 "stopped. Result %1' for 2, 'The winlogon notification subscriber <%2> began handling the "
                 "notification event (%1).' for 811 and 'The winlogon notification subscriber <%2> finished handling "
                 "the notification event (%1).' for 812 (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L409-L421,"
                 " "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L422-L437,"
                 " "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L1157-L1173"
                 " and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Winlogon.xml#L1174-L1190;"
                 " that repository's manifests for Windows 10 builds 16299.125, 17763.107 and 19041.208 and Windows "
                 "11 build 26100.1742 define the four the same way). Notification Event (as stored) and Subscriber "
                 "are the Event and SubscriberName fields of 811 and 812 (%1 and %2 of the message), and the manifest"
                 " gives the event number no names; Result (as stored) is the Win32Status field of 2. A column whose "
                 "field the record does not carry is blank. User SID is the UserID of the record's Security element "
                 "and Process ID the ProcessID of its Execution element; on the tested logs User SID was S-1-5-18 on "
                 "every row of 1 and 2, and S-1-5-18 or an account SID (S-1-5-21-...) on the rows of 811 and 812. "
                 "windows11_arm_winlogon_known_20261004 is this log from a Windows 11 build 26200 ARM64 virtual "
                 "machine, exported with wevtutil after a known session locked the workstation three times with "
                 "rundll32 user32.dll,LockWorkStation and unlocked it each time with the account password, noting the"
                 " times in UTC. Each lock request was followed within 0.25 seconds by rows of 811 and 812 with "
                 "Notification Event 4 for the subscribers Sens and TermSrv, and each unlock, taken as the moment the"
                 " lock screen process LogonUI.exe exited, was preceded within 0.6 seconds by rows of 811 and 812 "
                 "with Notification Event 5 for the same two subscribers; those 24 rows are the only records of the "
                 "log inside the session. On that build, then, 4 was written at each lock and 5 at each unlock. "
                 "Outside the session that log holds one more Sens row of 811 with 4 and none with 5. On "
                 "af_case2_win10, lonewolf_win10, pc_mus_001_win11 and szechuan_win10, 4 and 5 were likewise written "
                 "only for Sens and TermSrv, and on every tested log each row with 4 or 5 holds an account SID in "
                 "User SID; what the two numbers mark on those builds was not tested, and no tested Security log "
                 "holds a 4800 or 4801 record to compare with. The event numbers seen were 0, 1, 2, 3, 4, 5, 12 and "
                 "13 and, on the capture only, 14; what the numbers other than 4 and 5 mark is not established here. "
                 "The subscribers seen were GPClient, Profiles, Sens, SessionEnv, TermSrv, TrustedInstaller and "
                 "Wlansvc. Result (as stored) was 0 on 103 of the 104 rows of 2 and 1326 on one row of "
                 "af_case2_win10, which Microsoft's system error codes give as ERROR_LOGON_FAILURE, 'The user name or"
                 " password is incorrect.' "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/Debug/system-error-codes--1300-1699-.md?plain=1#L356-L364)."
                 " The tested logs gave 698, 312, 785 and 400 rows on af_case2_win10, lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10 and 2,482 on the capture. Every row of 811 is followed at once "
                 "by a row of 812 with the same event number and subscriber, except one on pc_mus_001_win11, and "
                 "every row of 1 by a row of 2. The two earlier captures of the same machine, "
                 "windows11_arm_4688_known and windows11_arm_known_20261001, hold no such log. Event Time (UTC) is "
                 "the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME the "
                 "record stores with integer arithmetic, counted in UTC and cut to whole microseconds, in place of "
                 "python-evtx 0.8.1's conversion through a floating-point number, which can differ by microseconds "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113)."
                 " Record ID is the record's EventRecordID. Computer is the machine name the record stores: it held "
                 "one value on af_case2_win10, pc_mus_001_win11 and the capture, and two on lonewolf_win10 and "
                 "szechuan_win10. Rows are in the order the file holds them, which was rising Record ID on every "
                 "tested log; 1, 1 and 3 rows on lonewolf_win10, szechuan_win10 and the capture are earlier than the "
                 "row before them. Every record of the tested logs is a Microsoft-Windows-Winlogon record with one of"
                 " the four Event IDs, and every one rendered. The manifest also defines 505, 1001, 1101, 1102, 1103 "
                 "and 1104 for this log; they are not read. A record python-evtx cannot render, or whose XML does not"
                 " parse, is counted in the run log and not reported. A log marked dirty is read past the chunks its "
                 "header counts, and the run log says how many records came from there. A row records that Winlogon "
                 "notified a subscriber or ran an authentication; it does not by itself establish which person locked"
                 " or unlocked the workstation, and locks started another way (a key press or a timeout) were not "
                 "compared. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Winlogon%4Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 698 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 312 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 785 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 400 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 2482 rows",
        },
    },
}


def notification_row(record):
    return (record.time, record.event_id, _EVENTS[record.event_id], record.get('UserSid'),
            record.get('TSId'), record.record_id, record.computer)


@artifact_processor
def winlogonNotifications(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User SID', 'Session',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, _LABEL, event_ids=set(_EVENTS), provider=_PROVIDER)
    return data_headers, [notification_row(record) for record in records], '\n'.join(sources)


def operational_row(record):
    get = record.get
    return (record.time, record.event_id, _OPERATIONAL_EVENTS[record.event_id], get('Event'), get('SubscriberName'),
            get('Win32Status'), record.user_sid, record.process_id, record.record_id, record.computer)


@artifact_processor
def winlogonOperational(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Notification Event (as stored)',
                    'Subscriber', 'Result (as stored)', 'User SID', 'Process ID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _OPERATIONAL_LOG, _OPERATIONAL_LABEL, event_ids=set(_OPERATIONAL_EVENTS), provider=_PROVIDER)
    return data_headers, [operational_row(record) for record in records], '\n'.join(sources)
