"""Windows system time change events for DLEAPP.

Author: @AlexisBrignoni, Claude.

Two logs record a change to the system time: the System log, through the
Microsoft-Windows-Kernel-General provider's event 1, and the Security log, through
event 4616 ('The system time was changed'). Each is reported as its own artifact.

The Reason a Kernel-General event 1 stores is a number its provider's manifest maps
to a name. It is given that name from the value map in the provider's DLL and the
English (en-US) .mui on the log's own volume (_ReasonNames), and kept as stored
otherwise.
"""

import collections
import os
from datetime import datetime

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records, utc_from_system_time

_KERNEL_GENERAL = 'Microsoft-Windows-Kernel-General'
_SECURITY = 'Microsoft-Windows-Security-Auditing'
# The provider's DLL, as the publisher registration of Microsoft-Windows-Kernel-General
# names it on each of the four registered Windows disk images, and the provider's GUID.
_REASON_DLL = 'microsoft-windows-system-events.dll'
_KERNEL_GENERAL_GUID = 'a68ca8b7-004f-d7b6-a698-07e2de0f1f5d'

__artifacts_v2__ = {
    "systemTimeChanges": {
        "name": "Windows System Time Changes",
        "description": "Changes to the system time from the System event log (Kernel-General "
                       "event 1): the time before and after each change, the stored reason, the "
                       "process ID and, where the event stores them, the process name and the time "
                       "zone bias.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "python-evtx; pefile to give the stored reason its name",
        "category": "Windows",
        "notes": "Read from System.evtx, named in the report's located-at line; rows come only from "
                 "Microsoft-Windows-Kernel-General records with Event ID 1, and the same provider's Event ID "
                 "12 records are read for the build check described below. The provider's manifest gives "
                 "event 1 the message 'The system time has changed to %1 from %2.' with, from version 1, the "
                 "change reason, from version 2 the process and its PID, from version 3 the RTC time, the "
                 "current time zone bias, whether the RTC time is in UTC and whether the system time was "
                 "based on the RTC time, and in version 4 the time delta in milliseconds (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources "
                 "repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-General.xml#L126-L245). "
                 "The event 1 records on the four registered Windows disk images are version 1 "
                 "(lonewolf_win10, build 16299), version 2 (af_case2_win10, build 17763, and szechuan_win10, "
                 "build 19041) and version 4 (pc_mus_001_win11, build 22621). Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME "
                 "the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, "
                 "in place of python-evtx 0.8.1's conversion through a floating-point number, which can "
                 "differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113), "
                 "and on the four images it was within 0.015 seconds of New Time on every row. New Time (UTC) and "
                 "Previous Time "
                 "(UTC) are NewTime and OldTime, FILETIMEs that python-evtx also renders counted in UTC. "
                 "Change (seconds) is New Time minus Previous Time, computed here; the TimeDeltaInMs that "
                 "version 4 stores agreed with it to within 1 millisecond on all 86 rows of "
                 "pc_mus_001_win11. Reason is the stored number with the name the provider's value map gives "
                 "it, as in 'System time synchronized with the hardware clock (2)': the map is read from "
                 "microsoft-windows-system-events.dll in the System32 folder of the volume the log was read "
                 "from, the file the publisher registration for this provider names as its resource and "
                 "message file on each of the four images, with the text from its English .mui in the en-US "
                 "folder beside it, and both files are named in the located-at line when they named a "
                 "reason. A number is named only when the boot record (Kernel-General 12) before the event "
                 "names the same Windows build as the log's last boot record; otherwise it is reported as "
                 "stored, and the run log says how many were named or kept and why. On the four images the "
                 "map was the same for every version present: 0 'System time initialized during boot', 1 'An "
                 "application or system component changed the time', 2 'System time synchronized with the "
                 "hardware clock' and 3 'System time adjusted to the new time zone', and every row's reason "
                 "was named. On those images every Reason 3 row had the same Previous Time and New Time, "
                 "every Reason 2 row moved the clock forward, by up to 9.7 days (pc_mus_001_win11), Reason 1 "
                 "rows moved it both forward and back, and no row had Reason 0. Process Name is ProcessName, "
                 "which the event carries from version 2; on the version 2 and 4 rows it was blank on every "
                 "Reason 2 row and on one Reason 3 row of pc_mus_001_win11. Process ID is ProcessID where "
                 "the event stores it and otherwise, on version 1, the process ID in the record's Execution "
                 "element: the two were equal on all 108 rows of the four images that store ProcessID and on "
                 "every row of the two captures named below, it was 4 on every Reason "
                 "2 row and on every version 2 or 4 row with a blank Process Name, and it equalled the "
                 "paired record's process ID on all 48 rows paired with a Security 4616 record, 14 of them "
                 "version 1 rows on lonewolf_win10. Time Zone Bias (as stored) is TimeZoneBias, which only "
                 "versions 3 and 4 carry, so it is blank on af_case2_win10, lonewolf_win10 and "
                 "szechuan_win10; Time Zone Bias (as stored) held 300 on every row of pc_mus_001_win11, "
                 "where the RTC time (CmosTime) was exactly that many minutes before New Time on all 86 rows "
                 "and the fields for whether the RTC time is in UTC and whether the system time was based on "
                 "it (RealTimeIsUniversal and SystemInCmosMode) were False on every row. CmosTime, "
                 "RealTimeIsUniversal, SystemInCmosMode and TimeDeltaInMs are not reported. Computer is the "
                 "machine name the record stores: it held one value on every row of pc_mus_001_win11 and two "
                 "values on af_case2_win10, lonewolf_win10 and szechuan_win10. Every Security 4616 record on "
                 "the four images, 48 in all, had a Kernel-General 1 record with the same previous and new "
                 "times and Reason 1, and two Reason 1 rows on pc_mus_001_win11 had no 4616; no Reason 2 or "
                 "3 row had one. Those records are reported by Windows Security Time Changes. The System log "
                 "on lonewolf_win10, pc_mus_001_win11 and szechuan_win10 was marked dirty and held records "
                 "in chunks its header does not count; those chunks are read too, and they gave 37 of the 51 "
                 "lonewolf_win10 rows, 18 of the 86 pc_mus_001_win11 rows and 3 of the 12 szechuan_win10 "
                 "rows. A record python-evtx cannot render, or whose XML does not parse, is counted in the "
                 "run log and not reported; every record in this log rendered on the four images. "
                 "The two captures of a Windows 11 build 26200 machine, windows11_arm_4688_known and "
                 "windows11_arm_known_20261001, gave 266 and 267 rows, all version 4. Neither holds "
                 "microsoft-windows-system-events.dll, so Reason is reported as stored there (1 or 3) and the "
                 "run log says the reasons were kept as stored. On each, the Reason 1 rows named prl_tools.exe"
                 " (220 and 221 rows), svchost.exe (31) or rundll32.exe (1) and moved the clock both forward "
                 "and back; the 14 Reason 3 rows named prl_tools.exe, TiWorker.exe, rundll32.exe or msoobe.exe"
                 " and had the same Previous Time and New Time. Event Time was more than 0.015 seconds from "
                 "New Time on 8 and 9 rows, all of them Reason 1 rows naming prl_tools.exe, and less than 0.27"
                 " seconds from it on every row. Time Zone Bias (as stored) held 240 on 164 and 165 rows, 300 "
                 "on 98 and -600 on 4, Computer held two values, and every record in the log rendered. "
                 "A row "
                 "records a change to the system time as this provider logged it; it does not by itself "
                 "establish which person, if any, made the change. Reading needs the python-evtx package "
                 "(pip install python-evtx); naming the reason needs the pefile package (pip install "
                 "pefile), and without it the reason is reported as stored.",
        "paths": ("*/Windows/System32/winevt/Logs/System.evtx",
                  "*/Windows/System32/microsoft-windows-system-events.dll",
                  "*/Windows/System32/en-US/microsoft-windows-system-events.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 51 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 86 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 12 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 266 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 267 rows",
        },
    },
    "securityTimeChanges": {
        "name": "Windows Security Time Changes",
        "description": "Changes to the system time from the Security event log (event 4616): "
                       "the time before and after each change, the process that made it and the "
                       "account that requested it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line; only "
                 "Microsoft-Windows-Security-Auditing records with Event ID 4616 are read. Microsoft "
                 "documents 4616 as 'The system time was changed.' and says it is logged regardless of the "
                 "Audit Security State Change subcategory setting (Microsoft Learn, '4616(S): The system "
                 "time was changed.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4616); "
                 "every 4616 record on the four registered Windows disk images was version 1. Event Time "
                 "(UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from "
                 "the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, "
                 "which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113), "
                 "and on the four images it was within 0.01 seconds of New Time on every row. Previous Time "
                 "(UTC) and New Time "
                 "(UTC) are PreviousTime and NewTime, which that page describes as the previous time and the "
                 "new time in UTC, and Change (seconds) is New Time minus Previous Time, computed here. "
                 "Process Name is ProcessName, and Process ID is ProcessId, which the page describes as the "
                 "hexadecimal process ID of the process that changed the system time, shown here in decimal. "
                 "Account Name, Account Domain, Account SID and Logon ID are SubjectUserName, "
                 "SubjectDomainName, SubjectUserSid and SubjectLogonId as stored; the page describes the SID "
                 "as that of the account that requested the change and the Logon ID as a value that can "
                 "correlate the event with others that hold it, such as 4624. The page calls these events "
                 "with LOCAL SERVICE normal time correction actions, and says an account other than LOCAL "
                 "SERVICE, or a process other than svchost.exe, means the change was not made by the Windows "
                 "Time service. On lonewolf_win10, pc_mus_001_win11 and szechuan_win10 every row held LOCAL "
                 "SERVICE, NT AUTHORITY, S-1-5-19 and 0x00000000000003e5 in Account Name, Account Domain, "
                 "Account SID and Logon ID and a Process Name ending in svchost.exe; af_case2_win10 had "
                 "three such rows and one naming an account whose name ends in $, with no domain, S-1-5-18 "
                 "and rundll32.exe. Each of the 48 rows on the four images had a Kernel-General 1 record in "
                 "the System log with the same previous and new times and Reason 1, 'An application or "
                 "system component changed the time', and its process ID equalled that record's on all of "
                 "them; the System log also records changes this log does not, and those are reported by "
                 "Windows System Time Changes. Computer is the machine name the record stores: it held one "
                 "value on every row of pc_mus_001_win11 and two values on af_case2_win10, lonewolf_win10 "
                 "and szechuan_win10. The Security log was marked dirty on lonewolf_win10, pc_mus_001_win11 "
                 "and szechuan_win10; on lonewolf_win10 and szechuan_win10 it held records in chunks its "
                 "header does not count, and those chunks, which are read too, gave 11 of the 14 "
                 "lonewolf_win10 rows and 2 of the 9 szechuan_win10 rows. "
                 "On windows11_arm_4688_known, a capture of a Windows 11 build 26200 machine, the 19 rows are "
                 "version 1: 17 hold the SID S-1-5-18 with a Process Name ending in prl_tools.exe and 2 hold "
                 "LOCAL SERVICE with svchost.exe, so by the page's description the 17 were not made by the "
                 "Windows Time service; Event Time was less than 0.27 seconds from New Time on every row, and "
                 "each row had a Kernel-General 1 record with the same previous and new times. The Security "
                 "log of windows11_arm_known_20261001, a capture of the same machine, holds no 4616 record. "
                 "A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not reported; every "
                 "record in this log rendered on the four images. Reading needs the python-evtx package (pip "
                 "install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 14 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 9 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 19 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the Security log holds no 4616 record)",
        },
    },
}


def _change(previous, new):
    """New minus previous in seconds, to the microsecond, or '' when either time is missing."""
    if not isinstance(previous, datetime) or not isinstance(new, datetime):
        return ''
    return f'{(new - previous).total_seconds():.6f}'


def _record_number(record):
    try:
        return int(record.record_id)
    except (TypeError, ValueError):
        return None


def _written_under_last_build(record_id, boots):
    """Whether the boot record before this one names the same build as the log's last.

    `boots` holds (record id, BuildVersion) for every Kernel-General 12 record in the
    log. A record before the first of them, or in a log without one, returns False.
    """
    if record_id is None or not boots:
        return False
    ordered = sorted(boots)
    before = [build for boot_id, build in ordered if boot_id < record_id]
    return bool(before) and before[-1] == ordered[-1][1]


class _ReasonNames:
    """Names for the Reason a Kernel-General event 1 stores, from the value map on its volume.

    The number is shown as 'name (number)' when three things hold: the provider's DLL in
    the System32 folder beside the log carries an event manifest that binds a value map
    to Reason for the event's version, the English (en-US) .mui beside that DLL gives the
    map entry's text, and the boot record (Kernel-General 12) before the event names the
    same Windows build as the last boot record in the log, so the event was written under
    the build that was running when the volume was acquired. Otherwise the number is kept
    as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _SYSTEM32 = '/windows/system32/'
    _LABEL = 'Windows System Time Changes'

    def __init__(self, context):
        self.context = context
        self.files = {}      # (volume root, file name) -> staged path
        self.loaded = {}     # volume root -> (value maps, messages, DLL, .mui)
        self.named = collections.Counter()   # staged path -> numbers it named
        self.kept = collections.Counter()    # why a number was kept as stored
        for path in sorted(str(f) for f in context.get_files_found()):
            if os.path.isdir(path):
                continue
            relative = self._relative(path)
            for name, suffix in ((_REASON_DLL, self._SYSTEM32 + _REASON_DLL),
                                 (_REASON_DLL + '.mui', f'{self._SYSTEM32}en-us/{_REASON_DLL}.mui')):
                if relative.endswith(suffix):
                    self.files.setdefault((relative[:-len(suffix)], name), path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _load(self, root):
        if root not in self.loaded:
            dll_path = self.files.get((root, _REASON_DLL))
            mui_path = self.files.get((root, _REASON_DLL + '.mui'))
            maps, messages = {}, {}
            if dll_path and mui_path:
                maps = windows_messages.read_event_value_maps(dll_path, _KERNEL_GENERAL_GUID)
                if maps:
                    messages = windows_messages.read_message_table(mui_path)
            self.loaded[root] = (maps, messages, dll_path, mui_path)
        return self.loaded[root]

    def text(self, record, boots):
        """The record's stored Reason, as 'name (number)' when it can be."""
        value = record.get('Reason')
        if not value.isdigit():
            return value
        relative = self._relative(record.source)
        at = relative.find(self._LOG_DIR)
        maps, messages, dll_path, mui_path = self._load(relative[:at]) if at >= 0 else ({}, {}, None, None)
        if not maps or not messages:
            self.kept['no value map'] += 1
            return value
        if not _written_under_last_build(_record_number(record), boots):
            self.kept['build'] += 1
            return value
        try:
            version = int(record.version)
        except ValueError:
            version = None
        message_id = maps.get((1, version), {}).get('Reason', {}).get(int(value))
        name = messages.get(message_id, '').strip() if message_id is not None else ''
        if not name:
            self.kept['not in the map'] += 1
            return value
        self.named[dll_path] += 1
        self.named[mui_path] += 1
        return f'{name} ({value})'

    def files_used(self):
        """The DLL and .mui files that named at least one number, for the source path."""
        return sorted(self.named)

    def log(self):
        for path, count in sorted(self.named.items()):
            logfunc(f'{self._LABEL}: {count} stored reason(s) named with '
                    f'{self.context.get_relative_path(path)}')
        reasons = {
            'no value map': 'no DLL with an English .mui beside the log gave a value map'
                            + ('' if windows_messages.pefile else ' (pefile is not installed)'),
            'build': 'the boot record before the event did not name the build of the '
                     "log's last boot record, or no boot record came before it",
            'not in the map': 'the value map has no entry for the number',
        }
        for reason, count in sorted(self.kept.items()):
            logfunc(f'{self._LABEL}: {count} stored reason(s) kept as stored: {reasons[reason]}')


def system_time_row(record, reason):
    """The report row for one Kernel-General event 1; reason is the Reason text to show."""
    previous = utc_from_system_time(record.get('OldTime'))
    new = utc_from_system_time(record.get('NewTime'))
    # Version 1 stores no ProcessID; the record's Execution element holds the process ID then.
    return (record.time, previous, new, _change(previous, new), reason,
            record.get('ProcessName'), record.get('ProcessID') or record.process_id,
            record.get('TimeZoneBias'), record.computer)


def _decimal(value):
    """A stored hexadecimal number ('0x...') in decimal; anything else as stored."""
    text = (value or '').strip()
    if text.lower().startswith('0x'):
        try:
            return str(int(text, 16))
        except ValueError:
            return text
    return text


def security_time_row(record):
    """The report row for one Security event 4616."""
    previous = utc_from_system_time(record.get('PreviousTime'))
    new = utc_from_system_time(record.get('NewTime'))
    return (record.time, previous, new, _change(previous, new), record.get('ProcessName'),
            _decimal(record.get('ProcessId')), record.get('SubjectUserName'),
            record.get('SubjectDomainName'), record.get('SubjectUserSid'),
            record.get('SubjectLogonId'), record.computer)


@artifact_processor
def systemTimeChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Previous Time (UTC)', 'datetime'),
                    ('New Time (UTC)', 'datetime'), 'Change (seconds)', 'Reason', 'Process Name',
                    'Process ID', 'Time Zone Bias (as stored)', 'Computer')
    records, _sources = read_event_records(context, 'system.evtx', 'Windows System Time Changes',
                                           event_ids={'1', '12'}, provider=_KERNEL_GENERAL)
    boots = collections.defaultdict(list)
    for record in records:
        number = _record_number(record)
        build = record.get('BuildVersion')
        if record.event_id == '12' and build and number is not None:
            boots[record.source].append((number, build))
    names = _ReasonNames(context)
    data_list = []
    sources = []
    for record in records:
        if record.event_id != '1':
            continue
        data_list.append(system_time_row(record, names.text(record, boots[record.source])))
        if record.source not in sources:
            sources.append(record.source)
    names.log()
    sources.extend(names.files_used())
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def securityTimeChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Previous Time (UTC)', 'datetime'),
                    ('New Time (UTC)', 'datetime'), 'Change (seconds)', 'Process Name',
                    'Process ID', 'Account Name', 'Account Domain', 'Account SID', 'Logon ID',
                    'Computer')
    records, _sources = read_event_records(context, 'security.evtx', 'Windows Security Time Changes',
                                           event_ids={'4616'}, provider=_SECURITY)
    data_list = [security_time_row(record) for record in records]
    sources = []
    for record in records:
        if record.source not in sources:
            sources.append(record.source)
    return data_headers, data_list, '\n'.join(sources)
