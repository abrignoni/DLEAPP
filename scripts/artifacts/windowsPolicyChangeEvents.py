"""Windows security policy change event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads four Microsoft-Windows-Security-Auditing events of the Security event log:
4719 (system audit policy was changed), 4717 and 4718 (system security access,
a logon right, was granted to or removed from an account) and 4739 (domain
policy was changed). The three artifacts share one read of the log. A 4719
stores its category, subcategory and changes as parameter references (%%n);
each is given the text of that message from the English (en-US) msobjs.dll.mui
on the log's own volume (_ParameterText), and is reported as stored when that
file is not there. Event IDs, field names and message text are sourced in the
notes.
"""

import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_LABEL = 'Security Policy Changes'
_LOG = 'security.evtx'
_SECURITY = 'Microsoft-Windows-Security-Auditing'
_EVENT_IDS = {'4717', '4718', '4719', '4739'}

_RIGHT_EVENTS = {
    '4717': ('Access granted', 'AccessGranted'),
    '4718': ('Access removed', 'AccessRemoved'),
}

# The 4739 fields the event's message lists under Changed Attributes, with the
# label the message gives each (see notes).
_ATTRIBUTES = (
    ('MinPasswordAge', 'Min. Password Age'),
    ('MaxPasswordAge', 'Max. Password Age'),
    ('ForceLogoff', 'Force Logoff'),
    ('LockoutThreshold', 'Lockout Threshold'),
    ('LockoutObservationWindow', 'Lockout Observation Window'),
    ('LockoutDuration', 'Lockout Duration'),
    ('PasswordProperties', 'Password Properties'),
    ('MinPasswordLength', 'Min. Password Length'),
    ('PasswordHistoryLength', 'Password History Length'),
    ('MachineAccountQuota', 'Machine Account Quota'),
    ('MixedDomainMode', 'Mixed Domain Mode'),
    ('DomainBehaviorVersion', 'Domain Behavior Version'),
    ('OemInformation', 'OEM Information'),
)

__artifacts_v2__ = {
    "auditPolicyChanges": {
        "name": "Audit Policy Changes",
        "description": "Changes to the system audit policy recorded in the Security event log, Event ID 4719, with "
                       "the category, subcategory and change each record stores and the account the record names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx, pefile",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line; only "
                 "Microsoft-Windows-Security-Auditing records with Event ID 4719 are read. Microsoft documents 4719 "
                 "as 'System audit policy was changed.', says it generates when the computer's audit policy changes "
                 "and that it is logged regardless of the Audit Policy Change subcategory setting (Microsoft Learn, "
                 "'4719(S): System audit policy was changed.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4719). "
                 "Category, Subcategory and Changes are CategoryId, SubcategoryId and AuditPolicyChanges, and "
                 "Subcategory GUID is SubcategoryGuid (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L3843-L3874). "
                 "The tested record stores the first three as parameter references such as %%8276, as the example "
                 "record on the page does, and each reference is given the text of that message from the English "
                 "msobjs.dll.mui in System32's en-US folder on the volume the log was read from, as in 'Detailed "
                 "Tracking (%%8276)'; the .mui is named in the located-at line when it gave a reference its text, "
                 "otherwise the reference is reported as stored, and the run log says how many were given text or "
                 "kept. msobjs.dll is the parameter file the publisher registration of "
                 "Microsoft-Windows-Security-Auditing names in the SOFTWARE hive of the four public images and of "
                 "windows11_arm_known_20261001. Account Name, Account Domain, Account SID and Logon ID are "
                 "SubjectUserName, SubjectDomainName, SubjectUserSid and SubjectLogonId, which the page describes as "
                 "the account that made the change. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. The one "
                 "tested 4719 is on windows11_arm_4688_known, known data made on a Windows 11 build 26200 ARM64 "
                 "virtual machine on 30 September 2026, where auditpol /set /subcategory:\"Process Creation\" "
                 "/success:enable was run as administrator. Its row reads Detailed Tracking (%%8276), Process "
                 "Creation (%%13312), {0cce922b-69ae-11d9-bed3-505054503030} and Success Added (%%8449), and "
                 "Microsoft's Group Policy audit configuration specification gives that GUID as the Process Creation "
                 "subcategory (Microsoft, '[MS-GPAC]: Subcategory and SubcategoryGUID', "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpac/77878370-0712-47cd-997d-b07053429f6d). "
                 "On each of the five tested copies of msobjs.dll.mui, those of the four public images and of that "
                 "capture, messages 8272 to 8280 are the nine categories the 4719 page lists and messages 8448 to "
                 "8451 are Success removed, Success Added, Failure removed and Failure added, the four changes it "
                 "lists. The page says Changes can combine several of those, and its example record stores '%%8448, "
                 "%%8450'; a value holding several references has each given its text, which no tested record "
                 "exercised. The Security logs of af_case2_win10, lonewolf_win10, pc_mus_001_win11 and "
                 "szechuan_win10 hold no 4719, and neither does that of windows11_arm_known_20261001, which was "
                 "cleared in its session, so those five give no rows. A row records that the audit policy changed "
                 "and the account the record names; it does not show who was using that account. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the six tested logs rendered. A log marked dirty is read past the chunks "
                 "its header counts, and the run log says how many records came from there. The log is read once for "
                 "Audit Policy Changes, Logon Right Changes and Domain Policy Changes. Reading needs the python-evtx "
                 "package (pip install python-evtx); giving the references their text needs the pefile package (pip "
                 "install pefile), and without it they are reported as stored.",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',
                  '*/Windows/System32/en-US/msobjs.dll.mui'),
        "output_types": ["standard"],
        "artifact_icon": "sliders",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 1 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
    "logonRightChanges": {
        "name": "Logon Right Changes",
        "description": "Logon rights granted to or removed from an account, from Security event log Event ID 4717 "
                       "and 4718, with the right, the SID it was granted to or removed from and the account the "
                       "record names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line; only "
                 "Microsoft-Windows-Security-Auditing records with Event ID 4717 or 4718 are read. Microsoft "
                 "documents 4717 as 'System security access was granted to an account.' and 4718 as 'System security "
                 "access was removed from an account.', generated every time the local logon user right policy is "
                 "changed and a logon right was granted to or removed from an account, and lists the ten logon "
                 "rights the events are generated for (Microsoft Learn, '4717(S): System security access was granted "
                 "to an account.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4717, "
                 "and '4718(S): System security access was removed from an account.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4718). "
                 "Event is 'Access granted' for 4717 and 'Access removed' for 4718. Access Right is AccessGranted on "
                 "4717 and AccessRemoved on 4718, as stored. Target SID is TargetSid, as stored and with no name "
                 "given to it; the event's message puts it under Account Modified. Account Name, Account Domain, "
                 "Account SID and Logon ID are SubjectUserName, SubjectDomainName, SubjectUserSid and "
                 "SubjectLogonId, the message's Subject (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L3783-L3812 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L3813-L3842). "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are "
                 "in the order the log holds them, which is the order of Record ID; on af_case2_win10 that is not "
                 "the order of Event Time (UTC). The tested logs give 19, 15, 1 and 19 rows on af_case2_win10, "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10, 30 granted and 24 removed, and none on "
                 "windows11_arm_4688_known and windows11_arm_known_20261001. The rows hold 7 of the ten rights the "
                 "pages list: SeBatchLogonRight, SeDenyInteractiveLogonRight, SeDenyNetworkLogonRight, "
                 "SeInteractiveLogonRight, SeNetworkLogonRight, SeRemoteInteractiveLogonRight and "
                 "SeServiceLogonRight. Account SID held one value, S-1-5-18, and Logon ID one value, "
                 "0x00000000000003e7, on every row of the tested images; the 4717 page says the event is typically "
                 "triggered by the SYSTEM account and recommends reporting it when the subject is not SYSTEM. On "
                 "af_case2_win10, lonewolf_win10 and szechuan_win10, 17, 15 and 19 rows name the account MINWINPC$ "
                 "with a blank Account Domain, and on each image those rows fall within 15 seconds of each other. "
                 "The other 3 rows are SeServiceLogonRight granted to and then removed from one S-1-5-111-... SID on "
                 "af_case2_win10, and SeServiceLogonRight granted to S-1-5-83-0 on pc_mus_001_win11. Account Name "
                 "held one value on every row of lonewolf_win10 and szechuan_win10, where Account Domain is blank on "
                 "every row, and Computer held one value on every row of lonewolf_win10 and szechuan_win10. A row "
                 "records a change of a logon right as this log recorded it and the account the record names; it "
                 "does not show who was using that account. A record python-evtx cannot render, or whose XML does "
                 "not parse, is counted in the run log and not reported; every record of the six tested logs "
                 "rendered. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. The log is read once for Audit Policy Changes, Logon Right Changes "
                 "and Domain Policy Changes. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 15 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 19 rows",
        },
    },
    "domainPolicyChanges": {
        "name": "Domain Policy Changes",
        "description": "Changes to the domain policy recorded in the Security event log, Event ID 4739, with the "
                       "policy changed, the attributes the record stores a value for and the account the record "
                       "names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line; only "
                 "Microsoft-Windows-Security-Auditing records with Event ID 4739 are read. Microsoft documents 4739 "
                 "as 'Domain Policy was changed.', generated when the computer's Account Lockout Policy or Password "
                 "Policy settings were modified, the 'Network security: Force logoff when logon hours expire' "
                 "setting was changed, or the domain functional level or some other attributes changed (Microsoft "
                 "Learn, '4739(S): Domain Policy was changed.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4739). "
                 "Policy Changed is DomainPolicyChanged, for which the page gives Lockout Policy, Password Policy, "
                 "Logoff Policy and '-' as some possible values. Domain Name and Domain SID are DomainName and "
                 "DomainSid. Changed Attributes lists the fields the event's message puts under Changed Attributes "
                 "whose stored value is neither empty nor '-', each as the message's label and the stored value, "
                 "joined by semicolons; the page says an attribute that was not changed holds '-'. Privileges is "
                 "PrivilegeList. Account Name, Account Domain, Account SID and Logon ID are SubjectUserName, "
                 "SubjectDomainName, SubjectUserSid and SubjectLogonId, the message's Subject (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L4650-L4712). "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. The "
                 "tested logs give 3, 1 and 2 rows on af_case2_win10, lonewolf_win10 and szechuan_win10 and none on "
                 "pc_mus_001_win11, windows11_arm_4688_known and windows11_arm_known_20261001. Policy Changed is "
                 "Password Policy on 5 of the 6 rows. Changed Attributes is 'OEM Information: 0' on the 4 rows of "
                 "af_case2_win10 and lonewolf_win10; the page says it has no information about that field. On one "
                 "szechuan_win10 row it lists Password Properties 1, Min. Password Length 7 and Password History "
                 "Length 24, and gives Min. Password Age and Max. Password Age as the same three characters, which "
                 "are not a number, where the page describes both as numeric: they are reported as python-evtx "
                 "renders them, and what the two values hold was not established. The other szechuan_win10 row comes "
                 "from a 4739 record with no event data, so every column from Policy Changed to Logon ID is blank on "
                 "it. On the 5 rows with event data Privileges held '-', Account SID S-1-5-18 and Logon ID "
                 "0x00000000000003e7; Policy Changed, Changed Attributes and Privileges therefore held one value on "
                 "every row of af_case2_win10, as did Domain SID, Account SID and Logon ID. Account Domain is blank "
                 "on the lonewolf_win10 row and on one af_case2_win10 row, both of which name the account MINWINPC$. "
                 "A row records a change of policy as this log recorded it and the account the record names; it does "
                 "not show who was using that account. A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported; every record of the six tested logs rendered. A "
                 "log marked dirty is read past the chunks its header counts, and the run log says how many records "
                 "came from there. The log is read once for Audit Policy Changes, Logon Right Changes and Domain "
                 "Policy Changes. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
        },
    },
}

_read = {}


def _security_logs(context):
    return sorted(path for path in (str(f) for f in context.get_files_found())
                  if path.lower().endswith(_LOG) and not os.path.isdir(path))


def policy_records(context):
    """The 4717, 4718, 4719 and 4739 records of every Security log found, and the logs read.

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
    """Text for the parameter references (%%n) a 4719 record stores.

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
        """The value with each reference the volume's msobjs.dll.mui resolves written 'text (%%n)'."""
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
        """The message files that gave text to at least one reference, for the source path."""
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


def audit_row(record, parameters):
    return (record.time, parameters.text(record, record.get('CategoryId')),
            parameters.text(record, record.get('SubcategoryId')), record.get('SubcategoryGuid'),
            parameters.text(record, record.get('AuditPolicyChanges')), *_subject(record),
            record.record_id, record.computer)


def right_row(record):
    event, field = _RIGHT_EVENTS[record.event_id]
    return (record.time, record.event_id, event, record.get(field), record.get('TargetSid'),
            *_subject(record), record.record_id, record.computer)


def changed_attributes(record):
    """The Changed Attributes fields a 4739 stores a value for, as 'label: value' joined by '; '."""
    return '; '.join(f'{label}: {record.get(field)}' for field, label in _ATTRIBUTES
                     if record.get(field) not in ('', '-'))


def domain_row(record):
    return (record.time, record.get('DomainPolicyChanged'), record.get('DomainName'),
            record.get('DomainSid'), changed_attributes(record), record.get('PrivilegeList'),
            *_subject(record), record.record_id, record.computer)


@artifact_processor
def auditPolicyChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Category', 'Subcategory', 'Subcategory GUID',
                    'Changes', 'Account Name', 'Account Domain', 'Account SID', 'Logon ID',
                    'Record ID', 'Computer')
    records, sources = policy_records(context)
    parameters = _ParameterText(context, 'Audit Policy Changes')
    data_list = [audit_row(record, parameters) for record in records if record.event_id == '4719']
    parameters.log()
    return data_headers, data_list, '\n'.join(list(sources) + parameters.files_used())


@artifact_processor
def logonRightChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Access Right',
                    'Target SID', 'Account Name', 'Account Domain', 'Account SID', 'Logon ID',
                    'Record ID', 'Computer')
    records, sources = policy_records(context)
    data_list = [right_row(record) for record in records if record.event_id in _RIGHT_EVENTS]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def domainPolicyChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Policy Changed', 'Domain Name', 'Domain SID',
                    'Changed Attributes', 'Privileges', 'Account Name', 'Account Domain',
                    'Account SID', 'Logon ID', 'Record ID', 'Computer')
    records, sources = policy_records(context)
    data_list = [domain_row(record) for record in records if record.event_id == '4739']
    return data_headers, data_list, '\n'.join(sources)
