"""Windows Service Control Manager event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads two sets of Service Control Manager events of the System event log. Event
7040 records a change of a service's start type. Eleven other events record a
service that failed to start, timed out, hung or terminated; each is reported
with the provider's message filled in from the record. An error such a record
stores as a parameter reference (%%n) is given the text of that message from
the English (en-US) kernel32.dll.mui on the log's own volume (_ParameterText),
and is reported as stored when that file does not give it. Service installs
(7045) are read by windowsServiceInstalls.py. The two artifacts share one read
of the log. Event IDs, field names and message text are sourced in the notes.
"""

import collections
import os
import re

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_LABEL = 'Service Control Manager Events'
_LOG = 'system.evtx'
_PROVIDER = 'Service Control Manager'
_START_TYPE = '7040'

# Event ID: (the provider's message with its line breaks as spaces, the number of the
# parameter that names the service, the number of the parameter that holds an error or 0).
_FAILURES = {
    '7000': ('The %1 service failed to start due to the following error: %2', 1, 2),
    '7001': ('The %1 service depends on the %2 service which failed to start because of the following '
             'error: %3', 1, 3),
    '7009': ('A timeout was reached (%1 milliseconds) while waiting for the %2 service to connect.', 2, 0),
    '7011': ('A timeout (%1 milliseconds) was reached while waiting for a transaction response from the '
             '%2 service.', 2, 0),
    '7022': ('The %1 service hung on starting.', 1, 0),
    '7023': ('The %1 service terminated with the following error: %2', 1, 2),
    '7024': ('The %1 service terminated with the following service-specific error: %2', 1, 2),
    '7031': ('The %1 service terminated unexpectedly. It has done this %2 time(s). The following '
             'corrective action will be taken in %3 milliseconds: %5.', 1, 0),
    '7032': ('The Service Control Manager tried to take a corrective action (%2) after the unexpected '
             'termination of the %3 service, but this action failed with the following error: %4', 3, 4),
    '7034': ('The %1 service terminated unexpectedly. It has done this %2 time(s).', 1, 0),
    '7043': ('The %1 service did not shut down properly after receiving a preshutdown control.', 1, 0),
}
_EVENT_IDS = {_START_TYPE} | set(_FAILURES)
_INSERT = re.compile(r'%(\d)')

__artifacts_v2__ = {
    "serviceStartTypeChanges": {
        "name": "Service Start Type Changes",
        "description": "Changes of a service's start type recorded by Service Control Manager event 7040 in the "
                       "System event log: the service, its previous and new start type and the SID the record "
                       "carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the System event log, named in the report's located-at line. Each record of Service "
                 "Control Manager event 7040 is one row; the provider's message for it is 'The start type of the %1 "
                 "service was changed from %2 to %3.' (Service Control Manager manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L495-L508; "
                 "the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that repository give the "
                 "same message and parameters). Only that provider and Event ID are read, because an Event ID means "
                 "different things for different providers. Service, Previous Start Type and New Start Type are the "
                 "record's first three parameters, the three the message inserts, as stored. Service Name is the "
                 "fourth parameter, which the message does not insert: on all 547 tested rows it is the name of a "
                 "key under Services in the SYSTEM hive of the same input (see Windows Services). The start types "
                 "the tested records store are auto start, demand start, disabled and system start; no source "
                 "listing these texts was found. User SID is the UserID of the record's Security element, which "
                 "Microsoft's event schema describes as identifying the user that logged the event, the SID of the "
                 "user in string form (Microsoft, 'Security (SystemPropertiesType) Element', "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/WES/eventschema-security-systempropertiestype-element.md#L20, "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/WES/eventschema-security-systempropertiestype-element.md#L41). "
                 "It is S-1-5-18 on 540 of the 547 rows, S-1-5-20 on 5, one on each input, and the SID of an account "
                 "on 2, one on af_case2_win10 and one on pc_mus_001_win11; each of those two SIDs has a profile in "
                 "User Profile List on its image. Microsoft lists S-1-5-18 as System (or LocalSystem) and S-1-5-20 "
                 "as NetworkService (Microsoft, 'Security identifiers', "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/identity/ad-ds/manage/understand-security-identifiers.md#L193-L195). "
                 "The tested logs give 30, 27, 122 and 17 rows on af_case2_win10, lonewolf_win10, pc_mus_001_win11 "
                 "and szechuan_win10 and 351 on windows11_arm_known_20261001, the System log of a Windows 11 build "
                 "26200 ARM64 virtual machine exported with wevtutil on 1 October 2026. Of the 547 rows, 476 are two "
                 "services, BITS and TrustedInstaller, changed between demand start and auto start under S-1-5-18. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders "
                 "from the FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole "
                 "microseconds, in place of python-evtx 0.8.1's conversion through a floating-point number, which "
                 "can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are "
                 "in the order the log holds them, which is the order of Record ID; on af_case2_win10, "
                 "lonewolf_win10 and the capture that is not the order of Event Time (UTC). Computer held one value "
                 "on every row of af_case2_win10 and pc_mus_001_win11. A row records that the Service Control "
                 "Manager logged the change with that SID; it does not show which program or command made it. The "
                 "provider's other events are not read here: 7045 is in Windows Service Installations and eleven "
                 "failure events are in Service Failures, and no tested log holds a 7035 or 7036 record (a control "
                 "sent to a service, a service entering a state; "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L426-L451). "
                 "A record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported; every record of the tested logs rendered, among them the 72 TPM event 27 records of the "
                 "capture's log, which python-evtx renders only with the array value types scripts/windows_evtx.py "
                 "adds. A log marked dirty is read past the chunks its header counts, and the run log "
                 "says how many records came from there. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "toggle-right",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 351 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 122 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 30 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 27 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 17 rows",
        },
    },
    "serviceFailures": {
        "name": "Service Failures",
        "description": "Eleven Service Control Manager events in the System event log about a service that failed to "
                       "start, timed out, hung, terminated or did not shut down properly: the service, the "
                       "provider's message filled in from the record and the error the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx, pefile",
        "category": "Windows",
        "notes": "Read from the System event log, named in the report's located-at line. Each record of eleven "
                 "Service Control Manager events is one row: 7000 and 7001 (a service failed to start), 7009 and "
                 "7011 (a timeout while waiting for a service), 7022 (a service hung on starting), 7023 and 7024 (a "
                 "service terminated with an error), 7031 and 7034 (a service terminated unexpectedly), 7032 (a "
                 "corrective action failed) and 7043 (a service did not shut down properly after a preshutdown "
                 "control). Message is the provider's message for the event with each %n replaced by the record's "
                 "parameter of that number and the message's line breaks written as spaces (Service Control Manager "
                 "manifest as registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources "
                 "repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L35-L65 "
                 "for 7000 and 7001, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L141-L154 "
                 "for 7009, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L166-L177 "
                 "for 7011, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L284-L326 "
                 "for 7022 to 7024, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L380-L425 "
                 "for 7031, 7032 and 7034 and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L554-L566 "
                 "for 7043; the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that repository "
                 "give the same messages and parameters). Only that provider is read, because an Event ID means "
                 "different things for different providers. Service is the parameter the message names the service "
                 "with: the first, except the second on 7009 and 7011 and the third on 7032. It is as stored: on the "
                 "60 rows of the four public images it is the name of a key under Services in the image's SYSTEM "
                 "hive on 39, the DisplayName value of one on 5 and neither on 16 (see Windows Services). Error is "
                 "the parameter the message gives as an error: the second on 7000, 7023 and 7024, the third on 7001 "
                 "and the fourth on 7032; it is blank on the other events. The tested records store it as a "
                 "parameter reference such as %%21, a placeholder for a string of the provider's parameter message "
                 "file (Microsoft, 'Event Identifiers (Event Logging)', "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/EventLog/event-identifiers.md#L80), "
                 "which the manifest gives as kernel32.dll "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L7). "
                 "Each reference is given the text of that message from the English kernel32.dll.mui in System32's "
                 "en-US folder on the volume the log was read from, as in 'The device is not ready. (%%21)'; the "
                 ".mui is named in the located-at line when it gave a reference its text, otherwise the reference is "
                 "reported as stored, and the run log says how many were given text or kept. All 49 references on "
                 "the four public images were given text; the 11 on windows11_arm_known_20261001 are reported as "
                 "stored, because that input holds the log without the .mui. Message carries the same text. "
                 "Parameters the message does not insert are not reported: the fourth of 7031 and the first of 7032, "
                 "each 1 on every tested record (8 and 1). The tested logs give 27, 5, 9 and 19 rows on "
                 "af_case2_win10, lonewolf_win10, pc_mus_001_win11 and szechuan_win10 and 16 on "
                 "windows11_arm_known_20261001, the System log of a Windows 11 build 26200 ARM64 virtual machine "
                 "exported with wevtutil on 1 October 2026: 30 of 7000, 4 of 7001, 1 of 7009, 1 of 7022, 24 of 7023, "
                 "1 of 7024, 8 of 7031, 1 of 7032, 2 of 7034 and 4 of 7043. No tested log holds a 7011, so that "
                 "event was exercised only by a constructed record in the unit tests. On szechuan_win10 the 7009 row "
                 "names a service that a 7045 record of the same log installed (see Windows Service Installations). "
                 "No tested failure record carries a UserID in its Security element, so no SID is reported. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the "
                 "FILETIME the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, "
                 "in place of python-evtx 0.8.1's conversion through a floating-point number, which can differ by "
                 "microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Computer "
                 "held one value on every row of pc_mus_001_win11. A row records what the Service Control Manager "
                 "logged; it does not by itself establish why the service failed. Not read: the provider's other "
                 "events, among them 7026 (boot-start or system-start drivers that did not load, 118 records on the "
                 "tested logs) and 7030 (a service marked interactive, 5 records); 7040 is in Service Start Type "
                 "Changes and 7045 in Windows Service Installations. A record python-evtx cannot render, or whose "
                 "XML does not parse, is counted in the run log and not reported; every record of the tested logs "
                 "rendered, among them the 72 TPM event 27 records of the capture's log, which python-evtx renders "
                 "only with the array value types scripts/windows_evtx.py adds. A log marked dirty is read "
                 "past the chunks its header counts, and the run log says how many records came from there. Reading "
                 "needs the python-evtx package (pip install python-evtx); giving the references their text needs "
                 "the pefile package (pip install pefile), and without it they are reported as stored.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',
                  '*/Windows/System32/en-US/kernel32.dll.mui'),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 16 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 27 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 19 rows",
        },
    },
}

_read = {}


def _system_logs(context):
    return sorted(str(f) for f in context.get_files_found()
                  if str(f).lower().endswith(_LOG) and not os.path.isdir(str(f)))


def service_records(context):
    """The 7040 and failure records of every System log found, and the logs read.

    The module's two artifacts are given the same staged logs one after the other, so
    the logs are read once and the result is kept while their paths, sizes and
    modification times stay the same.
    """
    key = tuple((path, os.path.getsize(path), os.path.getmtime(path))
                for path in _system_logs(context))
    if _read.get('key') != key:
        records, sources = read_event_records(context, _LOG, _LABEL, event_ids=_EVENT_IDS,
                                              provider=_PROVIDER)
        _read.clear()
        _read.update(key=key, records=records, sources=sources)
    return _read['records'], _read['sources']


class _ParameterText:
    """Text for the parameter references (%%n) a failure record stores.

    The text comes from the English (en-US) kernel32.dll.mui in the System32 folder of
    the volume the record's log was read from. A resolved reference reads
    'text (%%n)'; a reference that file does not resolve is kept as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _MESSAGE_FILE = '/windows/system32/en-us/kernel32.dll.mui'

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
        """The value with each reference the volume's kernel32.dll.mui resolves written 'text (%%n)'."""
        if not windows_messages.REFERENCE.search(value or ''):
            return value
        path = self._message_file(record)
        if path and path not in self.tables:
            self.tables[path] = windows_messages.read_message_table(path)
        table = self.tables.get(path, {})

        def shown(match):
            message = ' '.join((table.get(int(match.group(1))) or '').split())
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
                    f'no English kernel32.dll.mui on the same volume gave their text{missing}')


def change_row(record):
    """One 7040 record: the service, its name, the two start types and the SID the record carries."""
    return (record.time, record.get('param1'), record.get('param4'), record.get('param2'),
            record.get('param3'), record.user_sid, record.record_id, record.computer)


def failure_row(record, parameters):
    """One failure record: the service it names, the provider's message filled in, and its error."""
    template, service, error = _FAILURES[record.event_id]
    values = {str(number): record.get(f'param{number}') for number in range(1, 6)}
    error_text = ''
    if error:
        error_text = parameters.text(record, values[str(error)])
        values[str(error)] = error_text
    message = _INSERT.sub(lambda match: values.get(match.group(1), match.group(0)), template)
    return (record.time, record.event_id, values[str(service)], message, error_text,
            record.record_id, record.computer)


@artifact_processor
def serviceStartTypeChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Service', 'Service Name', 'Previous Start Type',
                    'New Start Type', 'User SID', 'Record ID', 'Computer')
    records, sources = service_records(context)
    data_list = [change_row(record) for record in records if record.event_id == _START_TYPE]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def serviceFailures(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Service', 'Message', 'Error',
                    'Record ID', 'Computer')
    records, sources = service_records(context)
    parameters = _ParameterText(context, 'Service Failures')
    data_list = [failure_row(record, parameters) for record in records if record.event_id in _FAILURES]
    parameters.log()
    return data_headers, data_list, '\n'.join(list(sources) + parameters.files_used())
