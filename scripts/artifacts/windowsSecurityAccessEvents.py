"""Windows special privilege, group enumeration and Credential Manager event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads four Microsoft-Windows-Security-Auditing events of the Security event log:
4672 (special privileges assigned to new logon), 4798 (a user's local group
membership was enumerated), 4799 (a security-enabled local group membership was
enumerated) and 5379 (Credential Manager credentials were read). The three
artifacts share one read of the log. A 5379 stores its read operation as a
parameter reference (%%n); it is given the text of that message from the English
(en-US) msobjs.dll.mui on the log's own volume (_ParameterText), and is reported
as stored when that file is not there. Event IDs, field names and message text
are sourced in the notes.
"""

import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records, utc_from_system_time

_LABEL = 'Security Access Events'
_LOG = 'security.evtx'
_SECURITY = 'Microsoft-Windows-Security-Auditing'
_PRIVILEGES = '4672'
_READS = '5379'

# The first sentence of each event's message in the provider manifest (see notes).
_ENUMERATIONS = {
    '4798': "A user's local group membership was enumerated",
    '4799': 'A security-enabled local group membership was enumerated',
}
_EVENT_IDS = {_PRIVILEGES, _READS, *_ENUMERATIONS}

__artifacts_v2__ = {
    "specialPrivilegeLogons": {
        "name": "Special Privilege Logons",
        "description": "Logons that were assigned special privileges, from Security event log Event ID 4672: the "
                       "account, its logon ID and the privileges the record lists.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 "Microsoft-Windows-Security-Auditing event 4672 is one row; the provider's message for it begins "
                 "'Special privileges assigned to new logon.' and lists the account, its logon ID and its privileges "
                 "(Microsoft-Windows-Security-Auditing manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L2453-L2477; "
                 "the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that repository give the "
                 "same message and fields). Only that provider and Event ID are read, because an Event ID means "
                 "different things for different providers. Account Name, Account Domain, Account SID and Logon ID "
                 "are the record's SubjectUserName, SubjectDomainName, SubjectUserSid and SubjectLogonId, as stored. "
                 "Privileges is the record's PrivilegeList: the names in stored order, joined here with a comma and "
                 "a space where the record separates them with line breaks and tabs. Microsoft documents the event "
                 "as generated for a new logon when any of 13 sensitive privileges is assigned to the logon session "
                 "(Microsoft, '4672(S) Special privileges assigned to new logon.', as updated 27 April 2026, "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4672). "
                 "The tested logs give 912, 789, 1,162 and 229 rows on af_case2_win10, lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10. Twelve privilege names appear on those 3,092 rows: 11 of the "
                 "13 that page lists (SeCreateTokenPrivilege and SeEnableDelegationPrivilege do not appear) and "
                 "SeDelegateSessionUserImpersonatePrivilege, which it does not list. Account SID is S-1-5-18 on "
                 "2,780 rows, which list 12 privileges except for 10 rows of szechuan_win10 that list 9, and the SID "
                 "of an account (S-1-5-21-...) on 148 rows, which list 9; the other 164 rows list 1 to 3. Microsoft "
                 "lists S-1-5-18 as System (or LocalSystem) (Microsoft, 'Security identifiers', "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/identity/ad-ds/manage/understand-security-identifiers.md#L193). "
                 "Each of the 3,092 rows has a logon record (Event ID 4624) with the same Logon ID and account SID "
                 "within two records of it in the log, before the row for 3,074 and after it for 18, and within 1.3 "
                 "seconds of it. That logon record's ElevatedToken is %%1842 on 3,057 of the rows and %%1843 on 35; "
                 "the msobjs.dll.mui of the same images gives those references the texts Yes and No. Its LogonType "
                 "is 5 on 2,852 of the rows. Logon ID does not pair a row with one logon record by itself: 2,770 "
                 "rows carry 0x00000000000003e7, all of them with Account SID S-1-5-18. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the record stores, "
                 "counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are "
                 "in the order the log file holds its records. That is the order of Record ID on every tested log "
                 "except pc_mus_001_win11's, whose file holds its lowest Record IDs last, and on the four public "
                 "images it is not the order of Event Time (UTC). Computer held one value on every row of "
                 "pc_mus_001_win11 and of the capture named next. On windows11_arm_4688_known, the Security log of a "
                 "Windows 11 build 26200 ARM64 virtual machine exported on 30 September 2026, the log gives 1,386 "
                 "rows: 1,353 with Account SID S-1-5-18, each listing 12 privileges, and 5 with the SID of an "
                 "account, each listing 9; 1,385 have the logon record within two records, within 18.3 seconds. The "
                 "Security log of windows11_arm_known_20261001, a later capture of the same machine, holds 2 "
                 "records, one of them a log cleared record (1102), and gives no row. A row records that Windows "
                 "assigned the listed privileges to a logon session; it does not show that a privilege was used. A "
                 "record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the six tested logs rendered. A log marked dirty is read past the chunks "
                 "its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 1386 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1162 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 912 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 789 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 229 rows",
        },
    },
    "localGroupEnumerations": {
        "name": "Local Group Membership Enumerations",
        "description": "Listings of a user's local groups and of a local group's members recorded in the Security "
                       "event log, Event IDs 4798 and 4799: the user or group listed, the calling process and the "
                       "subject account the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 "Microsoft-Windows-Security-Auditing events 4798 and 4799 is one row; the provider's messages for "
                 "them begin 'A user's local group membership was enumerated.' and 'A security-enabled local group "
                 "membership was enumerated.', the texts in Event (Microsoft-Windows-Security-Auditing manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L7051-L7086, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L7087-L7122; "
                 "the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that repository give the "
                 "same messages and fields). Microsoft documents 4798 as generated when a process enumerates a "
                 "user's security-enabled local groups, and 4799 when a process enumerates the members of a "
                 "security-enabled local group (Microsoft, '4798(S) A user's local group membership was enumerated.' "
                 "and '4799(S) A security-enabled local group membership was enumerated.', each as updated 27 April "
                 "2026, "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4798, "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4799). "
                 "Only that provider and those Event IDs are read. Target Name, Target Domain and Target SID are the "
                 "record's TargetUserName, TargetDomainName and TargetSid: the user whose groups were listed on a "
                 "4798 row, the group whose members were listed on a 4799 row. Process Name and Process ID (as "
                 "stored) are the record's CallerProcessName and CallerProcessId, the process ID in hexadecimal as "
                 "the record stores it. Account Name, Account Domain, Account SID and Logon ID are the record's "
                 "SubjectUserName, SubjectDomainName, SubjectUserSid and SubjectLogonId, as stored. The tested logs "
                 "give 350, 3,419, 3,959 and 227 rows on af_case2_win10, lonewolf_win10, pc_mus_001_win11 and "
                 "szechuan_win10: 6,438 of 4798 and 1,517 of 4799. Target SID is the SID of an account "
                 "(S-1-5-21-...) on all 6,438 rows of 4798 and a built-in group (S-1-5-32-...) on all 1,517 rows of "
                 "4799: S-1-5-32-544 on 1,000 and S-1-5-32-551 on 487, which Microsoft lists as Administrators and "
                 "Backup Operators (Microsoft, 'Security identifiers', "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/identity/ad-ds/manage/understand-security-identifiers.md#L213, "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/identity/ad-ds/manage/understand-security-identifiers.md#L220). "
                 "Account SID is S-1-5-18 on 7,524 of the 7,955 rows and S-1-5-20 on 61, and the file name in "
                 "Process Name is svchost.exe on 6,036. On the other 370 rows Account SID is the SID of an account; "
                 "explorer.exe is the file name in Process Name on 277 of them. Process Name is a path that begins "
                 "with a drive letter on 7,942 rows, 51 distinct paths counted per image, and a file exists at that "
                 "path on the image for 47 of the 51; the other 4, on pc_mus_001_win11, are named setup.exe and "
                 "tiworker.exe. Process ID (as stored) and Process Name equal the New Process ID and name of an "
                 "earlier process creation record (4688, see Windows Process Creation) of the same log on 3 rows; "
                 "those logs hold 210, 40, 88 and 78 such records. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are "
                 "in the order the log file holds its records. That is the order of Record ID on every tested log "
                 "except pc_mus_001_win11's, whose file holds its lowest Record IDs last, and on the four public "
                 "images it is not the order of Event Time (UTC). Computer held one value on every row of "
                 "pc_mus_001_win11 and of the capture named next. On windows11_arm_4688_known, the Security log of a "
                 "Windows 11 build 26200 ARM64 virtual machine exported on 30 September 2026, the log gives 502 "
                 "rows, 232 of 4798 and 270 of 4799; Account SID is the SID of an account on 208, and 5 rows match "
                 "an earlier 4688 record. The Security log of windows11_arm_known_20261001, a later capture of the "
                 "same machine, holds 2 records, one of them a log cleared record (1102), and gives no row. A row "
                 "records that the named process requested the listing, with the account the record names as its "
                 "subject; it does not show why, or what the process did with it. A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not reported; every record of "
                 "the six tested logs rendered. A log marked dirty is read past the chunks its header counts, and "
                 "the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 502 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3959 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 350 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 3419 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 227 rows",
        },
    },
    "credentialManagerReads": {
        "name": "Credential Manager Reads",
        "description": "Reads and listings of stored Credential Manager credentials recorded in the Security event "
                       "log, Event ID 5379: the operation, the target name, the count returned, the return code and "
                       "the client process the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx, pefile",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 "Microsoft-Windows-Security-Auditing event 5379 is one row; the provider's message for it begins "
                 "'Credential Manager credentials were read.', names the account and the read operation, and ends "
                 "'This event occurs when a user performs a read operation on stored credentials in Credential "
                 "Manager.' (Microsoft-Windows-Security-Auditing manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L13037-L13068). "
                 "The manifests of Windows 10 builds 17763.107 and 19041.208 in that repository give the same "
                 "message and fields; the manifest of build 16299.125 has no event 5379, and the log of "
                 "lonewolf_win10, build 16299, holds no such record. Only that provider and Event ID are read. The "
                 "message shows five of the record's eleven fields; the others are reported here as stored. Read "
                 "Operation is the record's ReadOperation, stored as a parameter reference: it is given the text the "
                 "English msobjs.dll.mui in System32's en-US folder on the volume the log was read from holds for "
                 "that reference, followed by the reference, as in 'Enumerate Credentials (%%8100)', and is reported "
                 "as stored when that file is not there or does not hold it; the .mui is named in the located-at "
                 "line when it gave a reference its text. Target Name is TargetName, Type (as stored) is Type, "
                 "Credentials Returned is CountOfCredentialsReturned, Return Code (as stored) is ReturnCode and "
                 "Client Process ID is ClientProcessId. Process Creation Time (UTC) is ProcessCreationTime, which "
                 "the manifest types as a FILETIME and python-evtx renders as it does the event's own time. Account "
                 "Name, Account Domain, Account SID and Logon ID are the record's SubjectUserName, "
                 "SubjectDomainName, SubjectUserSid and SubjectLogonId, as stored. No description of Type, "
                 "ReturnCode or the other fields the message does not show was found; the figures below are "
                 "measurements. The tested logs give 1,094, 21,492 and 594 rows on af_case2_win10, pc_mus_001_win11 "
                 "and szechuan_win10. Read Operation is Enumerate Credentials (%%8100) on 22,583 of those 23,180 "
                 "rows and Read Credential (%%8099) on 597, each reference given its text. Type (as stored) is 0 on "
                 "every Enumerate Credentials row; on the Read Credential rows it is 1 on 447, 2 on 100 and 6 on 50. "
                 "Credentials Returned is 0 on 4,278 rows and 1 on 18,902. Return Code (as stored) is 0 on 18,618 "
                 "rows, all with 1 credential returned; 3221226021 (0xC0000225 in hexadecimal) on 4,556, of which "
                 "4,272 returned 0 and 284 returned 1; and 3221225567 (0xC000005F) on 6, which returned 0. Target "
                 "Name was blank on 4 rows, and begins TERMSRV/ on 100 rows of pc_mus_001_win11. Account SID is the "
                 "SID of an account (S-1-5-21-...) on 20,819 rows, S-1-5-18 on 2,115, S-1-5-19 on 126 and S-1-5-20 "
                 "on 120. Client Process ID is a decimal number on every row, and the rows name 256 distinct pairs "
                 "of Client Process ID and Process Creation Time (UTC). On szechuan_win10 6 rows name a process for "
                 "which the log holds a process creation record (4688, see Windows Process Creation): the same "
                 "process ID, and an Event Time (UTC) within 1 second of Process Creation Time (UTC). Process "
                 "Creation Time (UTC) is later than Event Time (UTC) on 74 rows of af_case2_win10 and 76 of "
                 "szechuan_win10, by 28,710 to 28,789 and 2,872 to 2,908 seconds; Windows Security Time Changes "
                 "holds a clock change of 28,801 seconds backward on the first image and of 3,600 on the second. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are "
                 "in the order the log file holds its records. That is the order of Record ID on every tested log "
                 "except pc_mus_001_win11's, whose file holds its lowest Record IDs last, and on the three public "
                 "images with rows it is not the order of Event Time (UTC). Computer held one value on every row of "
                 "pc_mus_001_win11 and of the capture named next. On windows11_arm_4688_known, the Security log of a "
                 "Windows 11 build 26200 ARM64 virtual machine exported on 30 September 2026, the log gives 1,557 "
                 "rows: Enumerate Credentials (%%8100) on 1,554 and Read Credential (%%8099) on 3, Return Code (as "
                 "stored) 0 on 118, and 10 rows name a process with a 4688 record of the same process ID and time. "
                 "The Security log of windows11_arm_known_20261001, a later capture of the same machine, holds 2 "
                 "records, one of them a log cleared record (1102), and gives no row. A row records that a process "
                 "read or listed stored credentials under the named account; the record does not hold the "
                 "credential, and this artifact does not treat a row as proof of what the process did with it. A "
                 "record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the six tested logs rendered. A log marked dirty is read past the chunks "
                 "its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Giving the references their text also needs the "
                 "pefile package.",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',
                  '*/Windows/System32/en-US/msobjs.dll.mui'),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 1557 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21492 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1094 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 594 rows",
        },
    },
}

_read = {}


def _security_logs(context):
    return sorted(path for path in (str(f) for f in context.get_files_found())
                  if path.lower().endswith(_LOG) and not os.path.isdir(path))


def access_records(context):
    """The 4672, 4798, 4799 and 5379 records of every Security log found, and the logs read.

    The module's three artifacts are given the same staged logs one after the other, so
    the logs are read once and the result is kept while their paths, sizes and
    modification times stay the same.
    """
    key = tuple((path, os.path.getsize(path), os.path.getmtime(path))
                for path in _security_logs(context))
    if _read.get('key') != key:
        records, sources = read_event_records(context, _LOG, _LABEL, event_ids=_EVENT_IDS,
                                              provider=_SECURITY)
        _read.clear()
        _read.update(key=key, records=records, sources=sources)
    return _read['records'], _read['sources']


class _ParameterText:
    """Text for the parameter reference (%%n) a 5379 record stores as its read operation.

    The text comes from the English (en-US) msobjs.dll.mui in the System32 folder of
    the volume the record's log was read from. A resolved reference reads
    'text (%%n)'; a reference that file does not resolve is kept as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _MESSAGE_FILE = '/windows/system32/en-us/msobjs.dll.mui'

    def __init__(self, context, label):
        self.context = context
        self.label = label
        self.files = {}        # volume root -> staged path
        self.tables = {}       # staged path -> {message id: text}
        self.resolved = collections.Counter()
        self.kept = 0
        for path in sorted(str(f) for f in context.get_files_found()):
            if os.path.isdir(path):
                continue
            relative = self._relative(path)
            if relative.endswith(self._MESSAGE_FILE):
                self.files.setdefault(relative[:-len(self._MESSAGE_FILE)], path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _message_file(self, record):
        relative = self._relative(record.source) if record.source else ''
        at = relative.find(self._LOG_DIR)
        return self.files.get(relative[:at]) if at >= 0 else None

    def text(self, record, value):
        if not windows_messages.REFERENCE.search(value or ''):
            return value
        path = self._message_file(record)
        if path and path not in self.tables:
            self.tables[path] = windows_messages.read_message_table(path)
        table = self.tables.get(path, {})

        def shown(match):
            message = (table.get(int(match.group(1))) or '').strip()
            if not message:
                self.kept += 1
                return match.group(0)
            self.resolved[path] += 1
            return f'{message} ({match.group(0)})'

        return windows_messages.REFERENCE.sub(shown, value)

    def files_used(self):
        return sorted(self.resolved)

    def log(self):
        for path, count in sorted(self.resolved.items()):
            logfunc(f'{self.label}: {count} parameter reference(s) given their text from '
                    f'{self.context.get_relative_path(path)}')
        if self.kept:
            missing = '' if windows_messages.pefile else ' (pefile is not installed)'
            logfunc(f'{self.label}: {self.kept} parameter reference(s) reported as stored; '
                    f'no English msobjs.dll.mui on the same volume gave their text{missing}')


def _subject(record):
    return (record.get('SubjectUserName'), record.get('SubjectDomainName'),
            record.get('SubjectUserSid'), record.get('SubjectLogonId'))


def privileges(record):
    """The privilege names a 4672 stores, in stored order, joined by ', '."""
    return ', '.join(record.get('PrivilegeList').split())


def privilege_row(record):
    return (record.time, *_subject(record), privileges(record), record.record_id, record.computer)


def enumeration_row(record):
    return (record.time, record.event_id, _ENUMERATIONS[record.event_id],
            record.get('TargetUserName'), record.get('TargetDomainName'), record.get('TargetSid'),
            record.get('CallerProcessName'), record.get('CallerProcessId'), *_subject(record),
            record.record_id, record.computer)


def read_row(record, parameters):
    return (record.time, utc_from_system_time(record.get('ProcessCreationTime')),
            parameters.text(record, record.get('ReadOperation')), record.get('TargetName'),
            record.get('Type'), record.get('CountOfCredentialsReturned'), record.get('ReturnCode'),
            record.get('ClientProcessId'), *_subject(record), record.record_id, record.computer)


@artifact_processor
def specialPrivilegeLogons(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Account Name', 'Account Domain',
                    'Account SID', 'Logon ID', 'Privileges', 'Record ID', 'Computer')
    records, sources = access_records(context)
    data_list = [privilege_row(record) for record in records if record.event_id == _PRIVILEGES]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def localGroupEnumerations(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Target Name',
                    'Target Domain', 'Target SID', 'Process Name', 'Process ID (as stored)',
                    'Account Name', 'Account Domain', 'Account SID', 'Logon ID', 'Record ID',
                    'Computer')
    records, sources = access_records(context)
    data_list = [enumeration_row(record) for record in records if record.event_id in _ENUMERATIONS]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def credentialManagerReads(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Process Creation Time (UTC)', 'datetime'),
                    'Read Operation', 'Target Name', 'Type (as stored)', 'Credentials Returned',
                    'Return Code (as stored)', 'Client Process ID', 'Account Name',
                    'Account Domain', 'Account SID', 'Logon ID', 'Record ID', 'Computer')
    records, sources = access_records(context)
    parameters = _ParameterText(context, 'Credential Manager Reads')
    data_list = []
    unread = 0
    for record in records:
        if record.event_id != _READS:
            continue
        row = read_row(record, parameters)
        if record.get('ProcessCreationTime') and row[1] == '':
            unread += 1
        data_list.append(row)
    parameters.log()
    if unread:
        logfunc(f'Credential Manager Reads: {unread} record(s) store a process creation time that '
                'could not be read as a time; the column is blank on those rows')
    return data_headers, data_list, '\n'.join(list(sources) + parameters.files_used())
