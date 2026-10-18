"""Microsoft Sysinternals Sysmon Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Sysmon%4Operational.evtx, record by record, through
scripts/windows_evtx.EventRecordStream, and reports the Sysmon events in twelve
artifacts grouped by what they record. Every event data field is read from each
record by the name the record gives it, never by position, because the fields an
event carries differ between Sysmon schema versions. A field a record carries that
no column of its artifact shows is reported in Other Fields, by name, as stored.
"""

import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import EventRecordStream

_LOG = 'Microsoft-Windows-Sysmon%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Sysmon'

# The event names of the Sysinternals Sysmon page (see _DOCS).
_EVENTS = {
    '1': 'Process creation',
    '2': 'A process changed a file creation time',
    '3': 'Network connection',
    '4': 'Sysmon service state changed',
    '5': 'Process terminated',
    '6': 'Driver loaded',
    '7': 'Image loaded',
    '8': 'CreateRemoteThread',
    '9': 'RawAccessRead',
    '10': 'ProcessAccess',
    '11': 'FileCreate',
    '12': 'RegistryEvent (Object create and delete)',
    '13': 'RegistryEvent (Value Set)',
    '14': 'RegistryEvent (Key and Value Rename)',
    '15': 'FileCreateStreamHash',
    '16': 'ServiceConfigurationChange',
    '17': 'PipeEvent (Pipe Created)',
    '18': 'PipeEvent (Pipe Connected)',
    '19': 'WmiEvent (WmiEventFilter activity detected)',
    '20': 'WmiEvent (WmiEventConsumer activity detected)',
    '21': 'WmiEvent (WmiEventConsumerToFilter activity detected)',
    '22': 'DNSEvent (DNS query)',
    '23': 'FileDelete (File Delete archived)',
    '24': 'ClipboardChange (New content in the clipboard)',
    '25': 'ProcessTampering (Process image change)',
    '26': 'FileDeleteDetected (File Delete logged)',
    '27': 'FileBlockExecutable',
    '28': 'FileBlockShredding',
    '29': 'FileExecutableDetected',
    '255': 'Error',
}

_DOCS = ('Microsoft Sysinternals, "Sysmon", the documentation page as published in the '
         'MicrosoftDocs/sysinternals repository at commit 2fd3249 (2026-09-10), '
         'https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/'
         'sysinternals/downloads/sysmon.md?plain=1#L151-L364')

# Event data fields given as datetime columns. Sysmon writes them as
# 'YYYY-MM-DD hh:mm:ss.fff'; the page says event timestamps are in UTC.
_TIME_FIELDS = ('UtcTime', 'CreationUtcTime', 'PreviousCreationUtcTime')
_SYSMON_TIME = re.compile(r'^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?$')

# A column whose field more than one event spells differently reads every spelling.
_ALIASES = {
    'SourceProcessGuid': ('SourceProcessGuid', 'SourceProcessGUID'),
    'TargetProcessGuid': ('TargetProcessGuid', 'TargetProcessGUID'),
}


def sysmon_time(value):
    """An aware UTC datetime for a Sysmon time field, or None when the text is not that form."""
    match = _SYSMON_TIME.match(value or '')
    if not match:
        return None
    year, month, day, hour, minute, second, fraction = match.groups()
    try:
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                        int((fraction or '0').ljust(6, '0')), tzinfo=timezone.utc)
    except ValueError:
        return None


def headers_for(fields, time_fields=('UtcTime',)):
    """The column headers of an artifact that shows these event data fields."""
    return (tuple((name, 'datetime') for name in time_fields)
            + (('Time Created (UTC)', 'datetime'), 'Event ID', 'Event')
            + tuple(fields)
            + ('Other Fields', 'Event Version', 'Record ID', 'Computer'))


def sysmon_row(record, fields, time_fields=('UtcTime',)):
    """One row: the time fields, the record's own time, the event, the shown fields, then the rest."""
    shown = set()
    row = []
    for name in time_fields:
        value = record.fields.get(name)
        when = sysmon_time(value) if value is not None else None
        if when is not None:
            shown.add(name)
        row.append(when if when is not None else '')
    row.extend((record.time, record.event_id, _EVENTS.get(record.event_id, '')))
    for name in fields:
        value = ''
        for spelling in _ALIASES.get(name, (name,)):
            if spelling in record.fields:
                value = record.fields[spelling]
                shown.add(spelling)
                break
        row.append(value)
    other = '\n'.join(f'{name}: {value}' for name, value in record.fields.items() if name not in shown)
    row.extend((other, record.version, record.record_id, record.computer))
    return tuple(row)


def _stream(context, label, event_ids, fields, time_fields=('UtcTime',)):
    results = context.create_artifact_result(headers=headers_for(fields, time_fields))
    stream = EventRecordStream(context, _LOG, label, event_ids=event_ids, provider=_PROVIDER)
    for record in stream:
        results.add_row(sysmon_row(record, fields, time_fields))
    results.set_source_path('\n'.join(stream.sources))
    return results


_PROCESS_FIELDS = ('Image', 'CommandLine', 'ProcessId', 'ProcessGuid', 'User', 'ParentImage',
                   'ParentCommandLine', 'ParentProcessId', 'ParentProcessGuid', 'ParentUser',
                   'CurrentDirectory', 'IntegrityLevel', 'Hashes', 'OriginalFileName', 'FileVersion',
                   'Description', 'Product', 'Company', 'LogonGuid', 'LogonId', 'TerminalSessionId',
                   'RuleName')
_NETWORK_FIELDS = ('Image', 'ProcessId', 'ProcessGuid', 'User', 'Protocol', 'Initiated', 'SourceIp',
                   'SourcePort', 'SourceHostname', 'SourcePortName', 'SourceIsIpv6', 'DestinationIp',
                   'DestinationPort', 'DestinationHostname', 'DestinationPortName', 'DestinationIsIpv6',
                   'RuleName')
_DNS_FIELDS = ('QueryName', 'QueryStatus', 'QueryResults', 'Image', 'ProcessId', 'ProcessGuid', 'User',
               'RuleName')
_FILE_TIME_FIELDS = ('UtcTime', 'CreationUtcTime', 'PreviousCreationUtcTime')
_FILE_FIELDS = ('TargetFilename', 'Image', 'ProcessId', 'ProcessGuid', 'User', 'Hashes', 'Hash',
                'Contents', 'IsExecutable', 'Archived', 'RuleName')
_REGISTRY_FIELDS = ('EventType', 'TargetObject', 'Details', 'NewName', 'Image', 'ProcessId', 'ProcessGuid',
                    'User', 'RuleName')
_LOAD_FIELDS = ('ImageLoaded', 'Image', 'ProcessId', 'ProcessGuid', 'User', 'Hashes', 'Signed', 'Signature',
                'SignatureStatus', 'OriginalFileName', 'FileVersion', 'Description', 'Product', 'Company',
                'RuleName')
_ACCESS_FIELDS = ('SourceImage', 'SourceProcessId', 'SourceProcessGuid', 'SourceThreadId', 'SourceUser',
                  'TargetImage', 'TargetProcessId', 'TargetProcessGuid', 'TargetUser', 'GrantedAccess',
                  'CallTrace', 'NewThreadId', 'StartAddress', 'StartModule', 'StartFunction', 'RuleName')
_TAMPERING_FIELDS = ('Image', 'ProcessId', 'ProcessGuid', 'User', 'Device', 'Type', 'RuleName')
_PIPE_FIELDS = ('EventType', 'PipeName', 'Image', 'ProcessId', 'ProcessGuid', 'User', 'RuleName')
_WMI_FIELDS = ('EventType', 'Operation', 'User', 'EventNamespace', 'Name', 'Query', 'Type', 'Destination',
               'Consumer', 'Filter', 'RuleName')
_CLIPBOARD_FIELDS = ('Image', 'ProcessId', 'ProcessGuid', 'User', 'Session', 'ClientInfo', 'Hashes',
                     'Archived', 'RuleName')
_SERVICE_FIELDS = ('State', 'Version', 'SchemaVersion', 'Configuration', 'ConfigurationFileHash', 'ID',
                   'Description')


__artifacts_v2__ = {
    "sysmonProcessEvents": {
        "name": "Sysmon Process Creation and Termination",
        "description": "Sysmon process creation (1) and process terminated (5) events from the "
                       "Sysmon Operational log, with the image, command line, user, parent "
                       "process, hashes and process GUID each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 1 or 5 are read. On older systems"
                 " Sysmon writes its events to the System log instead (Microsoft Sysinternals, "
                 "'Sysmon', as published in the MicrosoftDocs/sysinternals repository at commit "
                 "2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from Image to RuleName are the event data fields of "
                 "those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says the ProcessGUID field is a unique value "
                 "for the process across a domain to make event correlation easier, and that the "
                 "hash is a full hash of the file with the algorithms in the HashType field "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L162-L166);"
                 " a Process terminated record provides the UtcTime, ProcessGuid and ProcessId of "
                 "the process "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L192-L193)."
                 " Hashes is reported as stored: on every Process creation row of the corpus keys "
                 "it is algorithm=value pairs joined by commas. Process terminated records carry "
                 "no Hashes, CommandLine, parent or IntegrityLevel field, so those columns are "
                 "blank on their rows. Every Process creation record on the corpus keys is version"
                 " 5 and every Process terminated record version 3. Of the Process creation "
                 "records, those of evtx_baseline_nextron_085_win7_x86 (659), "
                 "evtx_mitre_sysmon_cc0 (14) and evtx_attack_samples_sysmon_gpl (273) carry no "
                 "ParentUser field and 1,214 more on evtx_attack_samples_sysmon_gpl carry neither "
                 "ParentUser nor OriginalFileName; the Process terminated records of "
                 "evtx_baseline_nextron_085_win7_x86 (677) and evtx_attack_samples_sysmon_gpl (46)"
                 " carry no User field. On the 31,342 rows of the corpus keys UtcTime is before "
                 "Time Created (UTC), or within the same millisecond, on 31,341 and after it on 1;"
                 " the two differ by up to 347 seconds earlier and 32,393 seconds later. What sets"
                 " the gap is not established, so the two are reported side by side. On the seven "
                 "evtx_baseline_nextron_085 keys RuleName held - on every row but 5 (3 file and 2 "
                 "registry rows), and Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 1,336 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 4,412 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 4,374 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 4,609 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 5,161 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 7,376 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 2,498 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 39 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 1,537 rows",
        },
    },
    "sysmonNetworkConnections": {
        "name": "Sysmon Network Connections",
        "description": "Sysmon network connection (3) events from the Sysmon Operational log, with"
                       " the process, protocol, Initiated flag, source and destination addresses, "
                       "ports and host names each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 3 are read. On older systems "
                 "Sysmon writes its events to the System log instead (Microsoft Sysinternals, "
                 "'Sysmon', as published in the MicrosoftDocs/sysinternals repository at commit "
                 "2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from Image to RuleName are the event data fields of "
                 "those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says the event logs TCP/UDP connections on "
                 "the machine, is disabled by default, and is linked to a process through "
                 "ProcessId and ProcessGuid, with the source and destination host names, IP "
                 "addresses, port numbers and IPv6 status "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L180-L183)."
                 " The page lists a DnsLookup configuration entry that controls reverse DNS lookup"
                 " "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L421);"
                 " how a given host name was obtained is not established. Protocol, Initiated, "
                 "SourceIsIpv6 and DestinationIsIpv6 are reported as stored; on the corpus keys "
                 "Protocol held tcp (8,332), udp (6,102) and Initiated True (10,572), False "
                 "(3,862). What Initiated records beyond its name is not stated on the page. Event"
                 " ID and Event hold one value on every row, since one event is read; SourceIsIpv6"
                 " and DestinationIsIpv6 were equal on every row of the corpus keys, and "
                 "SourceHostname, SourcePortName, DestinationHostname and DestinationPortName held"
                 " - on all 14,234 rows of the seven evtx_baseline_nextron_085 keys. Every record "
                 "on the corpus keys is version 5 and carries the same fields. On the 14,434 rows "
                 "of the corpus keys UtcTime is before Time Created (UTC), or within the same "
                 "millisecond, on 14,179 and after it on 255; the two differ by up to 132,475 "
                 "seconds earlier and 32,399 seconds later. What sets the gap is not established, "
                 "so the two are reported side by side. On the seven evtx_baseline_nextron_085 "
                 "keys RuleName held - on every row but 5 (3 file and 2 registry rows), and "
                 "Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 1,792 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 1,483 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 5,479 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 1,687 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 3,727 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 66 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 36 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 164 rows",
        },
    },
    "sysmonDnsQueries": {
        "name": "Sysmon DNS Queries",
        "description": "Sysmon DNS query (22) events from the Sysmon Operational log, with the "
                       "query name, status and results and the process each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 22 are read. On older systems "
                 "Sysmon writes its events to the System log instead (Microsoft Sysinternals, "
                 "'Sysmon', as published in the MicrosoftDocs/sysinternals repository at commit "
                 "2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from QueryName to RuleName are the event data fields of"
                 " those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says the event is generated when a process "
                 "executes a DNS query, whether the result is successful or fails, cached or not, "
                 "and that it is not available on Windows 7 and earlier "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L319-L321);"
                 " evtx_baseline_nextron_085_win7_x86 has no row. QueryStatus and QueryResults are"
                 " reported as stored; the page does not describe either, and no code is given a "
                 "meaning here. Every record on the corpus keys is version 5; the one record of "
                 "evtx_mitre_sysmon_cc0 and of evtx_attack_samples_sysmon_gpl carries no User "
                 "field. Event ID and Event hold one value on every row. On the 7,253 rows of the "
                 "corpus keys UtcTime is before Time Created (UTC), or within the same "
                 "millisecond, on 7,120 and after it on 133; the two differ by up to 12,441 "
                 "seconds earlier and 32,400 seconds later. What sets the gap is not established, "
                 "so the two are reported side by side. On the seven evtx_baseline_nextron_085 "
                 "keys RuleName held - on every row but 5 (3 file and 2 registry rows), and "
                 "Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "world-www",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 1,731 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 1,195 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 2,143 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 1,540 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 611 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 31 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 1 row",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 1 row",
        },
    },
    "sysmonFileEvents": {
        "name": "Sysmon File Events",
        "description": "Sysmon file events from the Sysmon Operational log: file creation time "
                       "changes (2), file and stream creation (11, 15), file deletion (23, 26), "
                       "blocked and detected executables and blocked shredding (27, 28, 29), with "
                       "the target file, process and hashes each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 2, 11, 15, 23, 26, 27, 28 or 29 "
                 "are read. On older systems Sysmon writes its events to the System log instead "
                 "(Microsoft Sysinternals, 'Sysmon', as published in the "
                 "MicrosoftDocs/sysinternals repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime, CreationUtcTime and PreviousCreationUtcTime and the columns from "
                 "TargetFilename to RuleName are the event data fields of those names, read from "
                 "each record by the name the record gives the field and never by position, "
                 "because records of the same event and Event Version carry different field sets "
                 "(see below). A column is blank on a row whose record does not carry that field. "
                 "Other Fields lists, one name: value line each, every event data field of the "
                 "record that no column shows. Values are reported as python-evtx renders them and"
                 " Python's XML parser reads them back, with nothing trimmed. UtcTime, "
                 "CreationUtcTime and PreviousCreationUtcTime are read as UTC times when the value"
                 " has the form YYYY-MM-DD hh:mm:ss with up to six fraction digits; the Sysmon "
                 "page says event timestamps are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. From the Sysmon page: event 2 is registered when a file "
                 "creation time is explicitly modified by a process, and many processes "
                 "legitimately do so, so it does not necessarily indicate malicious activity "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L170-L176);"
                 " event 11 is logged when a file is created or overwritten "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L245);"
                 " event 15 logs the creation of a named file stream with the hash of the file's "
                 "contents and the contents of the named stream "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L279-L285);"
                 " event 23 records a deleted file that Sysmon also saved in its archive directory"
                 " "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L325-L329),"
                 " which this artifact does not read; event 26 records a deleted file "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L342);"
                 " events 27, 28 and 29 record a blocked executable, blocked shredding and a "
                 "detected executable "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L346-L356)."
                 " CreationUtcTime and PreviousCreationUtcTime are filled only on the events that "
                 "carry them (2 carries both, 11 and 15 CreationUtcTime). Hashes, Hash, Contents, "
                 "IsExecutable and Archived are reported as stored. On the corpus keys the rows "
                 "are 11 (542,698), 26 (94,703), 2 (71,071), 15 (221), 23 (6), 29 (1) by Event ID;"
                 " no record of event 27 or 28 is on any of them, so those two are read the same "
                 "way but unexercised. Event 2 records are version 5, except 6 version 4 records "
                 "on evtx_attack_samples_sysmon_gpl, and those of "
                 "evtx_baseline_nextron_085_win7_x86 and evtx_attack_samples_sysmon_gpl carry no "
                 "User field; event 11 records are version 2, and those of "
                 "evtx_baseline_nextron_085_win7_x86, 208 of the 209 of "
                 "evtx_attack_samples_sysmon_gpl and 9 of the 48 of evtx_mitre_sysmon_cc0 carry no"
                 " User field. Archived is filled only on event 23 rows and IsExecutable on event "
                 "23 and 26 rows, so both are blank on most rows. On the 708,700 rows of the "
                 "corpus keys UtcTime is before Time Created (UTC), or within the same "
                 "millisecond, on 708,698 and after it on 2; the two differ by up to 346 seconds "
                 "earlier and 32,390 seconds later. What sets the gap is not established, so the "
                 "two are reported side by side. On the seven evtx_baseline_nextron_085 keys "
                 "RuleName held - on every row but 5 (3 file and 2 registry rows), and Computer "
                 "held one machine name on each key but evtx_baseline_nextron_085_win2022_ad, "
                 "which holds two; Event Version held one value per Event ID on each key; Other "
                 "Fields was empty on every row of all nine corpus keys, because every field those"
                 " records carry has a column. Records are read by scripts/windows_evtx.py's "
                 "EventRecordStream, one at a time rather than gathered into a list. On a log "
                 "marked dirty it also reads each intact chunk after those the file header counts "
                 "(see that module): six of the seven evtx_baseline_nextron_085 logs are marked "
                 "dirty and hold 13,822 to 19,427 records in such chunks, all of which are read. "
                 "The evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its "
                 "header's next record number (512773) is not above the highest record number its "
                 "counted chunks hold (512840); its 12,248 records in the 262 intact chunks after "
                 "them continue that numbering and are read too. The other event log artifacts "
                 "read such a log the same way. Each record's Event ID and "
                 "provider are read from its template's substitutions before it is rendered, and a"
                 " record ruled out that way is not rendered; the rest are rendered by "
                 "FastRenderer, which walks each template once per chunk. On all 6,039,417 records"
                 " of the nine corpus keys FastRenderer's XML was identical to python-evtx's own "
                 "Record.xml() rendering, and the Event ID and provider read before rendering "
                 "matched those of the rendered record. On every key the row count per Event ID "
                 "equals the count of Microsoft-Windows-Sysmon records with that Event ID made "
                 "separately with evtx 0.13.1 (the Rust evtx crate's Python binding), and no "
                 "record failed to render. A row records what Sysmon logged under the "
                 "configuration in force. The configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "file-plus",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 42,208 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 128,850 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 215,869 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 200,777 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 98,062 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 18,183 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 4,480 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 52 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 219 rows",
        },
    },
    "sysmonRegistryEvents": {
        "name": "Sysmon Registry Events",
        "description": "Sysmon registry events (12, 13, 14) from the Sysmon Operational log: key "
                       "and value creation and deletion, value set and rename, with the target "
                       "object, details, new name and process each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 12, 13 or 14 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from EventType to RuleName are the event data fields of"
                 " those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 12 covers registry key and value "
                 "create and delete operations, event 13 value modifications, recording the value "
                 "written for DWORD and QWORD values, and event 14 key and value renames with the "
                 "new name "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L252-L254,"
                 " #L268-L270 and #L274-L275), and that Sysmon abbreviates registry root key "
                 "names, for example HKLM and HKU "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L256-L264)."
                 " TargetObject, Details and NewName are reported as stored; on the corpus keys "
                 "80,024 TargetObject values begin with \\REGISTRY\\ rather than an abbreviation. On"
                 " the corpus keys EventType held CreateKey (1,577,944), SetValue (1,152,185), "
                 "DeleteKey (115,930), DeleteValue (20,468), RenameKey (3). NewName is filled only"
                 " on event 14 rows; the only event 14 records on the corpus keys are 3 on "
                 "evtx_baseline_nextron_085_win11_client. Every record is version 2; those of "
                 "evtx_baseline_nextron_085_win7_x86 and most of evtx_attack_samples_sysmon_gpl "
                 "carry no User field. On the 2,866,530 rows of the corpus keys UtcTime is before "
                 "Time Created (UTC), or within the same millisecond, on 2,866,530, by up to "
                 "346.538 seconds. What sets the gap is not established, so the two are reported "
                 "side by side. On the seven evtx_baseline_nextron_085 keys RuleName held - on "
                 "every row but 5 (3 file and 2 registry rows), and Computer held one machine name"
                 " on each key but evtx_baseline_nextron_085_win2022_ad, which holds two; Event "
                 "Version held one value per Event ID on each key; Other Fields was empty on every"
                 " row of all nine corpus keys, because every field those records carry has a "
                 "column. Records are read by scripts/windows_evtx.py's EventRecordStream, one at "
                 "a time rather than gathered into a list. On a log marked dirty it also reads "
                 "each intact chunk after those the file header counts (see that module): six of "
                 "the seven evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to "
                 "19,427 records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "database",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 54,283 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 476,572 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 1,314,679 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 488,940 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 240,501 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 195,094 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 95,666 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 477 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 318 rows",
        },
    },
    "sysmonImageLoads": {
        "name": "Sysmon Driver and Image Loads",
        "description": "Sysmon driver loaded (6) and image loaded (7) events from the Sysmon "
                       "Operational log, with the loaded file, loading process, hashes and "
                       "signature information each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 6 or 7 are read. On older systems"
                 " Sysmon writes its events to the System log instead (Microsoft Sysinternals, "
                 "'Sysmon', as published in the MicrosoftDocs/sysinternals repository at commit "
                 "2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from ImageLoaded to RuleName are the event data fields "
                 "of those names, read from each record by the name the record gives the field and"
                 " never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 6 records a driver loaded on the "
                 "system and event 7 a module loaded in a process, that event 7 is disabled by "
                 "default, and that for both the signature is created asynchronously and indicates"
                 " if the file was removed after loading "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L197-L210)."
                 " Signed, Signature and SignatureStatus are reported as stored; on the corpus "
                 "keys Signed held true (697,088), false (31,050), failed: Invalid hash (13) and "
                 "SignatureStatus Valid (697,088), Unavailable (31,050), - (13). Driver loaded "
                 "records carry no process fields, so Image, ProcessId, ProcessGuid and User are "
                 "blank on their rows. Image loaded records are version 3 and driver loaded "
                 "records version 4, or 3 on evtx_attack_samples_sysmon_gpl; the image loaded "
                 "records of evtx_baseline_nextron_085_win7_x86 (21,684) and 653 of the 654 on "
                 "evtx_attack_samples_sysmon_gpl carry no User field, and 64 of those 653 carry no"
                 " OriginalFileName either. On the 728,151 rows of the corpus keys UtcTime is "
                 "before Time Created (UTC), or within the same millisecond, on 728,151, by up to "
                 "237.057 seconds. What sets the gap is not established, so the two are reported "
                 "side by side. On the seven evtx_baseline_nextron_085 keys RuleName held - on "
                 "every row but 5 (3 file and 2 registry rows), and Computer held one machine name"
                 " on each key but evtx_baseline_nextron_085_win2022_ad, which holds two; Event "
                 "Version held one value per Event ID on each key; Other Fields was empty on every"
                 " row of all nine corpus keys, because every field those records carry has a "
                 "column. Records are read by scripts/windows_evtx.py's EventRecordStream, one at "
                 "a time rather than gathered into a list. On a log marked dirty it also reads "
                 "each intact chunk after those the file header counts (see that module): six of "
                 "the seven evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to "
                 "19,427 records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "layers",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 21,684 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 92,515 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 116,840 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 118,262 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 149,898 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 168,515 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 59,717 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 58 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 662 rows",
        },
    },
    "sysmonProcessAccess": {
        "name": "Sysmon Process Access and Remote Threads",
        "description": "Sysmon CreateRemoteThread (8) and ProcessAccess (10) events from the "
                       "Sysmon Operational log, with the source and target processes, granted "
                       "access, call trace and new thread start each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 8 or 10 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from SourceImage to RuleName are the event data fields "
                 "of those names, read from each record by the name the record gives the field and"
                 " never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 8 records a process creating a "
                 "thread in another process, with StartModule and StartFunction inferred and "
                 "possibly empty when the start address is outside loaded modules or known "
                 "exported functions "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L214-L221),"
                 " and event 10 a process opening another process "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L233-L241)."
                 " Event 10 records name their process GUID fields SourceProcessGUID and "
                 "TargetProcessGUID and event 8 records SourceProcessGuid and TargetProcessGuid; "
                 "each pair is shown in the SourceProcessGuid and TargetProcessGuid columns. "
                 "GrantedAccess and CallTrace, which only event 10 carries, and NewThreadId, "
                 "StartAddress, StartModule and StartFunction, which only event 8 carries, are "
                 "reported as stored. Event 8 records are version 2 and event 10 records version "
                 "3; those of evtx_baseline_nextron_085_win7_x86 and most of "
                 "evtx_attack_samples_sysmon_gpl carry no SourceUser or TargetUser field. On the "
                 "1,620,322 rows of the corpus keys UtcTime is before Time Created (UTC), or "
                 "within the same millisecond, on 1,620,322, by up to 53.816 seconds. What sets "
                 "the gap is not established, so the two are reported side by side. On the seven "
                 "evtx_baseline_nextron_085 keys RuleName held - on every row but 5 (3 file and 2 "
                 "registry rows), and Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "crosshair",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 6,316 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 34,329 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 60,912 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 593,160 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 891,777 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 27,401 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 6,159 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 7 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 261 rows",
        },
    },
    "sysmonRawAccessTampering": {
        "name": "Sysmon Raw Access Reads and Process Tampering",
        "description": "Sysmon RawAccessRead (9) and ProcessTampering (25) events from the Sysmon "
                       "Operational log, with the process, device and tampering type each record "
                       "carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 9 or 25 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from Image to RuleName are the event data fields of "
                 "those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 9 records a process reading from a"
                 " drive with the \\\\.\\ denotation and indicates the source process and target "
                 "device "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L225-L229),"
                 " and event 25 is generated when process hiding techniques such as hollow or "
                 "herpaderp are detected "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L337-L338)."
                 " Device and Type are reported as stored; on the corpus keys Type held Image is "
                 "locked for access (30) on the event 25 rows. Event 9 records are version 2 and "
                 "event 25 records version 5; those of evtx_baseline_nextron_085_win7_x86 carry no"
                 " User field. The page's example schema for event 9, version 2, lists no RuleName"
                 " or User field "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L434-L440),"
                 " while the version 2 records on the corpus keys other than "
                 "evtx_baseline_nextron_085_win7_x86 carry both, which is one reason every field "
                 "is read by name. On the 12,341 rows of the corpus keys UtcTime is before Time "
                 "Created (UTC), or within the same millisecond, on 12,341, by up to 62.664 "
                 "seconds. What sets the gap is not established, so the two are reported side by "
                 "side. On the seven evtx_baseline_nextron_085 keys RuleName held - on every row "
                 "but 5 (3 file and 2 registry rows), and Computer held one machine name on each "
                 "key but evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version "
                 "held one value per Event ID on each key; Other Fields was empty on every row of "
                 "all nine corpus keys, because every field those records carry has a column. "
                 "Records are read by scripts/windows_evtx.py's EventRecordStream, one at a time "
                 "rather than gathered into a list. On a log marked dirty it also reads each "
                 "intact chunk after those the file header counts (see that module): six of the "
                 "seven evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 193 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 4,492 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 2,630 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 3,782 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 393 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 739 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 112 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 0 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 0 rows",
        },
    },
    "sysmonPipeEvents": {
        "name": "Sysmon Named Pipe Events",
        "description": "Sysmon named pipe created (17) and connected (18) events from the Sysmon "
                       "Operational log, with the pipe name and process each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 17 or 18 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from EventType to RuleName are the event data fields of"
                 " those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 17 is generated when a named pipe "
                 "is created and event 18 when a named pipe connection is made between a client "
                 "and a server "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L294-L300)."
                 " EventType and PipeName are reported as stored; on the corpus keys EventType "
                 "held ConnectPipe (39,522), CreatePipe (10,627) and blank (8); the blank ones are"
                 " 8 records of evtx_attack_samples_sysmon_gpl that carry no EventType field. "
                 "Every record is version 1; the 61 of evtx_attack_samples_sysmon_gpl and 18 of "
                 "the 34 of evtx_mitre_sysmon_cc0 carry no User field, so User is blank on every "
                 "row of evtx_attack_samples_sysmon_gpl, and evtx_baseline_nextron_085_win7_x86 "
                 "holds no pipe event. On the 50,157 rows of the corpus keys UtcTime is before "
                 "Time Created (UTC), or within the same millisecond, on 50,157, by up to 41.792 "
                 "seconds. What sets the gap is not established, so the two are reported side by "
                 "side. On the seven evtx_baseline_nextron_085 keys RuleName held - on every row "
                 "but 5 (3 file and 2 registry rows), and Computer held one machine name on each "
                 "key but evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version "
                 "held one value per Event ID on each key; Other Fields was empty on every row of "
                 "all nine corpus keys, because every field those records carry has a column. "
                 "Records are read by scripts/windows_evtx.py's EventRecordStream, one at a time "
                 "rather than gathered into a list. On a log marked dirty it also reads each "
                 "intact chunk after those the file header counts (see that module): six of the "
                 "seven evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 4,736 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 7,051 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 23,956 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 4,915 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 7,120 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 2,284 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 34 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 61 rows",
        },
    },
    "sysmonWmiEvents": {
        "name": "Sysmon WMI Events",
        "description": "Sysmon WMI event filter, consumer and binding (19, 20, 21) events from the"
                       " Sysmon Operational log, with the operation, user, namespace, name, query,"
                       " destination, consumer and filter each record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 19, 20 or 21 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from EventType to RuleName are the event data fields of"
                 " those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 19 logs the WMI namespace, filter "
                 "name and filter expression of a registered WMI event filter, event 20 the "
                 "consumer name, log and destination of a registered WMI consumer, and event 21 "
                 "the consumer name and filter path of a consumer bound to a filter "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L302-L316)."
                 " Operation, EventNamespace, Name, Query, Type, Destination, Consumer and Filter "
                 "are reported as stored. No record of these events is on the seven "
                 "evtx_baseline_nextron_085 keys; the 17 rows on the two exported sets held "
                 "EventType WmiConsumerEvent (6), WmiFilterEvent (6), WmiBindingEvent (5) and "
                 "Operation Created (9), Deleted (6), Modified (2), all version 3, and RuleName "
                 "was empty on every row of evtx_attack_samples_sysmon_gpl. On the 17 rows of the "
                 "corpus keys UtcTime is before Time Created (UTC), or within the same "
                 "millisecond, on 17, by up to 0.016 seconds. What sets the gap is not "
                 "established, so the two are reported side by side. On the seven "
                 "evtx_baseline_nextron_085 keys RuleName held - on every row but 5 (3 file and 2 "
                 "registry rows), and Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "zap",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 0 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 3 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 14 rows",
        },
    },
    "sysmonClipboardChanges": {
        "name": "Sysmon Clipboard Changes",
        "description": "Sysmon clipboard change (24) events from the Sysmon Operational log, with "
                       "the process, session, client information, hashes and Archived value each "
                       "record carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 24 are read. On older systems "
                 "Sysmon writes its events to the System log instead (Microsoft Sysinternals, "
                 "'Sysmon', as published in the MicrosoftDocs/sysinternals repository at commit "
                 "2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from Image to RuleName are the event data fields of "
                 "those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says the event is generated when the system "
                 "clipboard contents change "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L333);"
                 " it does not describe the fields. Session, ClientInfo, Hashes and Archived are "
                 "reported as stored, and what Hashes was computed over is not established here. "
                 "This artifact does not read Sysmon's archive directory. Every record on the "
                 "corpus keys is version 5; those of evtx_baseline_nextron_085_win7_x86 carry no "
                 "User field. Event ID and Event hold one value on every row. On the 52 rows of "
                 "the corpus keys UtcTime is before Time Created (UTC), or within the same "
                 "millisecond, on 52, by up to 0.016 seconds. What sets the gap is not "
                 "established, so the two are reported side by side. On the seven "
                 "evtx_baseline_nextron_085 keys RuleName held - on every row but 5 (3 file and 2 "
                 "registry rows), and Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "clipboard",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 6 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 4 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 2 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 16 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 21 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 1 row",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 2 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 0 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 0 rows",
        },
    },
    "sysmonServiceEvents": {
        "name": "Sysmon Service State, Configuration and Errors",
        "description": "Sysmon service state changed (4), configuration change (16) and error "
                       "(255) events from the Sysmon Operational log, with the state, Sysmon and "
                       "schema versions, configuration, configuration hash and error each record "
                       "carries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Sysmon (Windows)",
        "notes": "Read from Microsoft-Windows-Sysmon%4Operational.evtx in "
                 "Windows/System32/winevt/Logs, named in the report's located-at line; only "
                 "Microsoft-Windows-Sysmon records with Event ID 4, 16 or 255 are read. On older "
                 "systems Sysmon writes its events to the System log instead (Microsoft "
                 "Sysinternals, 'Sysmon', as published in the MicrosoftDocs/sysinternals "
                 "repository at commit 2fd3249, "
                 "https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L153-L155);"
                 " that log, and a Sysmon log exported or archived under another name, are not "
                 "read. Event is the name that page gives the Event ID "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L160-L364)."
                 " UtcTime and the columns from State to Description are the event data fields of "
                 "those names, read from each record by the name the record gives the field and "
                 "never by position, because records of the same event and Event Version carry "
                 "different field sets (see below). A column is blank on a row whose record does "
                 "not carry that field. Other Fields lists, one name: value line each, every event"
                 " data field of the record that no column shows. Values are reported as "
                 "python-evtx renders them and Python's XML parser reads them back, with nothing "
                 "trimmed. UtcTime is read as a UTC time when the value has the form YYYY-MM-DD "
                 "hh:mm:ss with up to six fraction digits; the Sysmon page says event timestamps "
                 "are in UTC "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L156)."
                 " A value of another form is left blank there and kept as stored in Other Fields."
                 " Time Created (UTC) is the record's own TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer"
                 " arithmetic, cut to whole microseconds. Record ID is the record's EventRecordID,"
                 " Event Version the System Version of the record, and Computer the machine name "
                 "the record stores. The Sysmon page says event 4 reports the state of the Sysmon "
                 "service (started or stopped), event 16 logs changes in the Sysmon configuration,"
                 " and event 255 is generated when an error occurred within Sysmon "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L187-L188,"
                 " #L289-L290 and #L360-L364), and that events 4 and 16 cannot be filtered "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L459"
                 " and #L471). Version and SchemaVersion are the event data fields of those names "
                 "on event 4 records; Event Version is the record's own version. State, "
                 "Configuration, ConfigurationFileHash, ID and Description are reported as stored;"
                 " on the corpus keys State held Started (17), Stopped (1). Every record is "
                 "version 3. On the 99 rows of the corpus keys UtcTime is before Time Created "
                 "(UTC), or within the same millisecond, on 99, by up to 0.042 seconds. What sets "
                 "the gap is not established, so the two are reported side by side. On the seven "
                 "evtx_baseline_nextron_085 keys Computer held one machine name on each key but "
                 "evtx_baseline_nextron_085_win2022_ad, which holds two; Event Version held one "
                 "value per Event ID on each key; Other Fields was empty on every row of all nine "
                 "corpus keys, because every field those records carry has a column. Records are "
                 "read by scripts/windows_evtx.py's EventRecordStream, one at a time rather than "
                 "gathered into a list. On a log marked dirty it also reads each intact chunk "
                 "after those the file header counts (see that module): six of the seven "
                 "evtx_baseline_nextron_085 logs are marked dirty and hold 13,822 to 19,427 "
                 "records in such chunks, all of which are read. The "
                 "evtx_baseline_nextron_085_win2022_evtx log is not marked dirty, but its header's"
                 " next record number (512773) is not above the highest record number its counted "
                 "chunks hold (512840); its 12,248 records in the 262 intact chunks after them "
                 "continue that numbering and are read too. The other event log artifacts read "
                 "such a log only as far as its header counts. Each record's Event ID and provider"
                 " are read from its template's substitutions before it is rendered, and a record "
                 "ruled out that way is not rendered; the rest are rendered by FastRenderer, which"
                 " walks each template once per chunk. On all 6,039,417 records of the nine corpus"
                 " keys FastRenderer's XML was identical to python-evtx's own Record.xml() "
                 "rendering, and the Event ID and provider read before rendering matched those of "
                 "the rendered record. On every key the row count per Event ID equals the count of"
                 " Microsoft-Windows-Sysmon records with that Event ID made separately with evtx "
                 "0.13.1 (the Rust evtx crate's Python binding), and no record failed to render. A"
                 " row records what Sysmon logged under the configuration in force. The "
                 "configuration filters which events are logged "
                 "(https://github.com/MicrosoftDocs/sysinternals/blob/2fd3249657118505564fd220e672e8ea45d35916/sysinternals/downloads/sysmon.md?plain=1#L366-L370"
                 " and #L445-L449), so the absence of a row is not evidence that the activity did "
                 "not happen. Not reported: the System Level, Task, Opcode, Keywords, Channel, "
                 "Security UserID and Execution ProcessID and ThreadID of the records. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name), Sysmon Operational log | 10 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name), Sysmon Operational log | 4 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name), Sysmon Operational log | 12 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name), Sysmon Operational log | 53 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name), Sysmon Operational log | 4 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name), Sysmon Operational log | 9 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name), Sysmon Operational log | 3 rows",
            "evtx_mitre_sysmon_cc0": "Sysmon records of 25 exported logs, one per folder | 0 rows",
            "evtx_attack_samples_sysmon_gpl": "Sysmon records of 193 exported logs, one per folder | 4 rows",
        },
    },
}


@artifact_processor
def sysmonProcessEvents(context):
    return _stream(context, __artifacts_v2__['sysmonProcessEvents']['name'], ('1', '5'), _PROCESS_FIELDS)


@artifact_processor
def sysmonNetworkConnections(context):
    return _stream(context, __artifacts_v2__['sysmonNetworkConnections']['name'], ('3',), _NETWORK_FIELDS)


@artifact_processor
def sysmonDnsQueries(context):
    return _stream(context, __artifacts_v2__['sysmonDnsQueries']['name'], ('22',), _DNS_FIELDS)


@artifact_processor
def sysmonFileEvents(context):
    return _stream(context, __artifacts_v2__['sysmonFileEvents']['name'], ('2', '11', '15', '23', '26', '27', '28', '29'), _FILE_FIELDS, _FILE_TIME_FIELDS)


@artifact_processor
def sysmonRegistryEvents(context):
    return _stream(context, __artifacts_v2__['sysmonRegistryEvents']['name'], ('12', '13', '14'), _REGISTRY_FIELDS)


@artifact_processor
def sysmonImageLoads(context):
    return _stream(context, __artifacts_v2__['sysmonImageLoads']['name'], ('6', '7'), _LOAD_FIELDS)


@artifact_processor
def sysmonProcessAccess(context):
    return _stream(context, __artifacts_v2__['sysmonProcessAccess']['name'], ('8', '10'), _ACCESS_FIELDS)


@artifact_processor
def sysmonRawAccessTampering(context):
    return _stream(context, __artifacts_v2__['sysmonRawAccessTampering']['name'], ('9', '25'), _TAMPERING_FIELDS)


@artifact_processor
def sysmonPipeEvents(context):
    return _stream(context, __artifacts_v2__['sysmonPipeEvents']['name'], ('17', '18'), _PIPE_FIELDS)


@artifact_processor
def sysmonWmiEvents(context):
    return _stream(context, __artifacts_v2__['sysmonWmiEvents']['name'], ('19', '20', '21'), _WMI_FIELDS)


@artifact_processor
def sysmonClipboardChanges(context):
    return _stream(context, __artifacts_v2__['sysmonClipboardChanges']['name'], ('24',), _CLIPBOARD_FIELDS)


@artifact_processor
def sysmonServiceEvents(context):
    return _stream(context, __artifacts_v2__['sysmonServiceEvents']['name'], ('4', '16', '255'), _SERVICE_FIELDS)
