"""Windows process creation events for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Security event 4688 ('A new process has been created'). The token elevation
type is stored as a parameter reference (%%n). It is given the text of that message
from the English (en-US) msobjs.dll.mui on the log's own volume (_ParameterText),
and kept as stored otherwise.
"""

import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_SECURITY = 'Microsoft-Windows-Security-Auditing'

__artifacts_v2__ = {
    "processCreation": {
        "name": "Windows Process Creation",
        "description": "Processes the Security event log records as created (event 4688): the time, the "
                       "new process and its ID, the parent process ID, the account that requested it and "
                       "the token elevation type, and, where the event stores them, the command line, the "
                       "parent process name, the target account and the integrity label.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "python-evtx; pefile to give the token elevation type its text",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line; only "
                 "Microsoft-Windows-Security-Auditing records with Event ID 4688 are read. Microsoft "
                 "documents 4688 as 'A new process has been created.' in the Audit Process Creation "
                 "subcategory and says it is generated every time a new process starts (Microsoft Learn, "
                 "'4688(S): A new process has been created.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4688); "
                 "every 4688 record on the four registered Windows disk images was version 2. On those "
                 "images every record's Event Time fell between 1.0 and 48.9 seconds after the latest system "
                 "start time before it that the System log gives: the StartTime of a "
                 "Microsoft-Windows-Kernel-General record with Event ID 12, whose message is 'The operating "
                 "system started at system time %7.' (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-General.xml#L330-L350). "
                 "The Process Name values ended in Registry, smss.exe, autochk.exe, csrss.exe, wininit.exe, "
                 "winlogon.exe, services.exe, lsass.exe and setupcl.exe, and on pc_mus_001_win11 also in "
                 "LsaIso.exe. Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx "
                 "renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Process Name is NewProcessName, which the page describes as the full path and the name of "
                 "the executable for the new process, and Process ID is NewProcessId, which the page "
                 "describes as the hexadecimal process ID of the new process, shown here in decimal; Process "
                 "Name was blank on 4 rows of pc_mus_001_win11. Command Line is CommandLine, which the event "
                 "carries from version 1 and which the page says holds the name of the executable and the "
                 "arguments passed to it and is empty by default, unless the group policy 'Include command "
                 "line in process creation events' is enabled, and it was empty on every row of the four "
                 "images. Parent Process ID is ProcessId, which the page describes as the hexadecimal "
                 "process ID of the process which ran the new process, shown here in decimal, and Parent "
                 "Process Name is ParentProcessName, which the event carries from version 2; Parent Process "
                 "Name was blank on 76 rows, and Parent Process ID was 4 on every one of them. Account Name, "
                 "Account Domain, Account SID and Logon ID are SubjectUserName, SubjectDomainName, "
                 "SubjectUserSid and SubjectLogonId as stored, which the page lists under Creator Subject, "
                 "the account that requested the 'create process' operation, and on every row of the four "
                 "images they held '-', '-', S-1-5-18 and 0x00000000000003e7. Target Account Name, Target "
                 "Account Domain, Target Account SID and Target Logon ID are TargetUserName, "
                 "TargetDomainName, TargetUserSid and TargetLogonId, which the event carries from version 2 "
                 "and which the page says name the target principal when the creator and target do not share "
                 "the same logon, and on every row of the four images they held '-', '-', S-1-0-0 and "
                 "0x0000000000000000. Token Elevation Type is TokenElevationType, stored as a parameter "
                 "reference such as %%1936, and it is given the text of that message from the English "
                 "msobjs.dll.mui in System32's en-US folder on the volume the log was read from, as in "
                 "'TokenElevationTypeDefault (1) (%%1936)': msobjs.dll is the parameter file the publisher "
                 "registration for Microsoft-Windows-Security-Auditing names on each of the four images, and "
                 "the .mui is named in the located-at line when it gave a reference its text; otherwise the "
                 "reference is reported as stored, and the run log says how many were given text or kept. "
                 "The page describes %%1936 as a full token with no privileges removed or groups disabled, "
                 "%%1937 as an elevated token with no privileges removed or groups disabled and %%1938 as a "
                 "limited token with administrative privileges removed and administrative groups disabled; "
                 "each image's copy gives them as TokenElevationTypeDefault (1), TokenElevationTypeFull (2) "
                 "and TokenElevationTypeLimited (3), and Token Elevation Type held the reference %%1936 on "
                 "every row of the four images. Mandatory Label is MandatoryLabel, which the event carries "
                 "from version 2 and the page describes as the SID of the integrity label assigned to the "
                 "new process, and it held S-1-16-16384 on every row of the four images, which the page's "
                 "table gives as System integrity. Computer is the machine name the record stores: it held "
                 "one value on every row of pc_mus_001_win11, two values on af_case2_win10 and "
                 "lonewolf_win10 and three on szechuan_win10. The Security log was marked dirty on "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10; on lonewolf_win10 and szechuan_win10 "
                 "it held records in chunks its header does not count, and those chunks, which are read too, "
                 "held no 4688 record. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record in this log rendered on the four "
                 "images. A row records a process creation as this log recorded it; it does not by itself "
                 "establish which person, if any, started the process. Reading needs the python-evtx package "
                 "(pip install python-evtx); giving the token elevation type its text needs the pefile "
                 "package (pip install pefile), and without it the reference is reported as stored.",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",
                  "*/Windows/System32/en-US/msobjs.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 210 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 40 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 88 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 78 rows",
        },
    },
}


def _decimal(value):
    """A stored hexadecimal number ('0x...') in decimal; anything else as stored."""
    text = (value or '').strip()
    if text.lower().startswith('0x'):
        try:
            return str(int(text, 16))
        except ValueError:
            return text
    return text


class _ParameterText:
    """Text for the parameter references (%%n) a 4688 record stores.

    The text comes from the English (en-US) msobjs.dll.mui in the System32 folder of
    the volume the record's log was read from. A resolved field reads 'text (%%n)';
    a reference that file does not resolve is kept as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _MESSAGE_FILE = '/windows/system32/en-us/msobjs.dll.mui'
    _LABEL = 'Windows Process Creation'

    def __init__(self, context):
        self.context = context
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

    def text(self, record, value):
        """The value, or 'text (%%n)' when it is a reference the volume's msobjs.dll.mui resolves."""
        match = windows_messages.REFERENCE.fullmatch(value or '')
        if not match:
            return value
        relative = self._relative(record.source) if record.source else ''
        at = relative.find(self._LOG_DIR)
        path = self.files.get(relative[:at]) if at >= 0 else None
        if path:
            if path not in self.tables:
                self.tables[path] = windows_messages.read_message_table(path)
            message = (self.tables[path].get(int(match.group(1))) or '').strip()
            if message:
                self.resolved[path] += 1
                return f'{message} ({value})'
        self.kept += 1
        return value

    def files_used(self):
        """The message files that gave text to at least one field, for the source path."""
        return sorted(self.resolved)

    def log(self):
        for path, count in sorted(self.resolved.items()):
            logfunc(f'{self._LABEL}: {count} parameter reference(s) given their text from '
                    f'{self.context.get_relative_path(path)}')
        if self.kept:
            missing = '' if windows_messages.pefile else ' (pefile is not installed)'
            logfunc(f'{self._LABEL}: {self.kept} parameter reference(s) reported as stored; '
                    f'no English msobjs.dll.mui on the same volume gave their text{missing}')


def process_row(record, elevation):
    """The report row for one 4688; elevation is the Token Elevation Type text to show."""
    return (record.time, record.get('NewProcessName'), _decimal(record.get('NewProcessId')),
            record.get('CommandLine'), record.get('ParentProcessName'),
            _decimal(record.get('ProcessId')), record.get('SubjectUserName'),
            record.get('SubjectDomainName'), record.get('SubjectUserSid'),
            record.get('SubjectLogonId'), record.get('TargetUserName'),
            record.get('TargetDomainName'), record.get('TargetUserSid'),
            record.get('TargetLogonId'), elevation, record.get('MandatoryLabel'), record.computer)


@artifact_processor
def processCreation(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Process Name', 'Process ID', 'Command Line',
                    'Parent Process Name', 'Parent Process ID', 'Account Name', 'Account Domain',
                    'Account SID', 'Logon ID', 'Target Account Name', 'Target Account Domain',
                    'Target Account SID', 'Target Logon ID', 'Token Elevation Type',
                    'Mandatory Label', 'Computer')
    records, _sources = read_event_records(context, 'security.evtx', 'Windows Process Creation',
                                           event_ids={'4688'}, provider=_SECURITY)
    parameters = _ParameterText(context)
    data_list = []
    sources = []
    for record in records:
        data_list.append(process_row(record, parameters.text(record, record.get('TokenElevationType'))))
        if record.source not in sources:
            sources.append(record.source)
    parameters.log()
    sources.extend(parameters.files_used())
    return data_headers, data_list, '\n'.join(sources)
