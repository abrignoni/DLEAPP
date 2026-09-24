"""Windows PowerShell event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads two logs: the classic "Windows PowerShell" log (Windows PowerShell.evtx),
where the PowerShell engine records its engine and provider lifecycle and
pipeline execution details, and Microsoft-Windows-PowerShell/Operational, where
it records script blocks (4104), pipeline execution detail (4103) and console
start-up (40961, 40962, 53504). Event IDs and field names are sourced in the
notes.
"""

import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import classic_strings, read_event_records

_CLASSIC_LOG = 'Windows PowerShell.evtx'
_OPERATIONAL_LOG = 'Microsoft-Windows-PowerShell%4Operational.evtx'
_CLASSIC_PROVIDER = 'PowerShell'
_OPERATIONAL_PROVIDER = 'Microsoft-Windows-PowerShell'

# Engine lifecycle (400 to 403) and provider lifecycle (600, 601) event IDs,
# as PowerShell's EventLogLogProvider assigns them (see notes).
_LIFECYCLE_EVENTS = {
    '400': 'Engine lifecycle', '401': 'Engine lifecycle',
    '402': 'Engine lifecycle', '403': 'Engine lifecycle',
    '600': 'Provider lifecycle', '601': 'Provider lifecycle',
}

# Console start-up events, with the message text PowerShell's instrumentation
# manifest gives them.
_CONSOLE_EVENTS = {
    '40961': 'PowerShell console is starting up',
    '40962': 'PowerShell console is ready for user input',
    '53504': 'PowerShell has started an IPC listening thread',
}

# Keys of the "\tKey=Value" context block in classic events. A line that does
# not start with one of them continues the previous value.
_CLASSIC_KEYS = (
    'NewEngineState', 'PreviousEngineState', 'ProviderName', 'NewProviderState',
    'DetailSequence', 'DetailTotal', 'SequenceNumber', 'UserId', 'HostName',
    'HostVersion', 'HostId', 'HostApplication', 'EngineVersion', 'RunspaceId',
    'PipelineId', 'CommandName', 'CommandType', 'ScriptName', 'CommandPath',
    'CommandLine')
_CLASSIC_LINE = re.compile(r'^\t?(' + '|'.join(_CLASSIC_KEYS) + r')=(.*)$')

# Keys of the "Key = Value" ContextInfo block in 4103 events.
_CONTEXT_KEYS = (
    'Severity', 'Host Name', 'Host Version', 'Host ID', 'Host Application',
    'Engine Version', 'Runspace ID', 'Pipeline ID', 'Command Name', 'Command Type',
    'Script Name', 'Command Path', 'Sequence Number', 'User', 'Connected User',
    'Shell ID')
_CONTEXT_LINE = re.compile(r'^\s*(' + '|'.join(re.escape(k) for k in _CONTEXT_KEYS)
                           + r') = ?(.*)$')

# Standard event levels (winmeta.xml, see notes).
_LEVELS = {'1': 'Critical', '2': 'Error', '3': 'Warning', '4': 'Information',
           '5': 'Verbose'}

__artifacts_v2__ = {
    "powershellEngineEvents": {
        "name": "PowerShell Engine and Provider Events",
        "description": "Engine and provider lifecycle events from the Windows "
                       "PowerShell event log, with the host application command "
                       "line and engine version each event stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Windows PowerShell.evtx, named in the report's located-at line. "
                 "Only records of the PowerShell provider with Event ID 400 to 403 (engine "
                 "lifecycle) or 600 and 601 (provider lifecycle) are read. Microsoft's "
                 "documentation for Windows PowerShell 5.1 describes engine lifecycle events "
                 "as logging the start and stop of PowerShell and provider lifecycle events "
                 "the start and stop of PowerShell providers (about_Eventlogs, "
                 "https://github.com/MicrosoftDocs/PowerShell-Docs/blob/"
                 "5f0f622fc6579cf4b635eb4ac6b99ceef091460e/reference/5.1/"
                 "Microsoft.PowerShell.Core/About/about_Eventlogs.md#L96-L98). PowerShell's "
                 "event log writer assigns 400 to the engine state Available, 401 Degraded, "
                 "402 OutOfService and 403 Stopped, and 600 and 601 to a provider Started and "
                 "Stopped (PowerShell repository at v6.0.0, EventLogLogProvider.cs, "
                 "https://github.com/PowerShell/PowerShell/blob/"
                 "2f818615bed15141c062dd185f659ed110d9c6ba/src/System.Management.Automation/"
                 "logging/eventlog/EventLogLogProvider.cs#L183-L207 and #L467-L485); the "
                 "tested records come from Windows PowerShell 5.1, whose source is not "
                 "published, and New State held Available on every 400 row and Stopped on "
                 "every 403 row on the registered images. New State, Previous State and "
                 "Provider Name are NewEngineState or NewProviderState, PreviousEngineState "
                 "and ProviderName from the context block the record stores; Previous State "
                 "is blank on 600 rows and Provider Name on 400 to 403 rows, which carry "
                 "neither. Host Application is HostApplication, which PowerShell fills with "
                 "the host process's command-line arguments joined by spaces (MshLog.cs, "
                 "https://github.com/PowerShell/PowerShell/blob/"
                 "2f818615bed15141c062dd185f659ed110d9c6ba/src/System.Management.Automation/"
                 "logging/MshLog.cs#L786). Host Name, Host Version, Engine Version, Host ID "
                 "and Runspace ID are HostName, HostVersion, EngineVersion, HostId and "
                 "RunspaceId as stored; PowerShell's source describes HostId as the ID of the "
                 "host hosting the engine (LogContext.cs, https://github.com/PowerShell/"
                 "PowerShell/blob/2f818615bed15141c062dd185f659ed110d9c6ba/src/"
                 "System.Management.Automation/logging/LogContext.cs#L42-L46). Engine "
                 "Version and Runspace ID were filled on every 400 and 403 row on the "
                 "registered images, on 2 of the 118 600 rows on af_case2_win10 and on none "
                 "of the 600 rows on the other two, and every Engine Version stored began "
                 "with 5. Host Name held one value on every row of pc_mus_001_win11 and "
                 "lonewolf_win10. These records store no account: the user SID in the record "
                 "was empty and the context block had no user field on every row on the "
                 "registered images. Event Time (UTC) is the record's TimeCreated SystemTime, "
                 "which python-evtx renders from the FILETIME the record stores, counted in "
                 "UTC (python-evtx 0.8.1, Evtx/BinaryParser.py, "
                 "https://github.com/williballenthin/python-evtx/blob/"
                 "cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the "
                 "record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. A record python-evtx "
                 "cannot render, or whose XML does not parse, is counted in the run log and "
                 "not reported; every record in this log rendered on the registered images. "
                 "Not reported: the context block's SequenceNumber, PipelineId, CommandName, "
                 "CommandType, ScriptName, CommandPath and CommandLine lines, 7 records on "
                 "af_case2_win10 written to this log by another "
                 "event source (Event ID 104), and pipeline execution details (800), which "
                 "the PowerShell Pipeline Execution Details artifact reports. Events 401, 402 "
                 "and 601 are read but appear on none of the registered images. Reading needs "
                 "the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Windows PowerShell.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 157 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 154 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 43 rows",
        },
    },
    "powershellPipelineExecution": {
        "name": "PowerShell Pipeline Execution Details",
        "description": "Pipeline execution detail events (800 in the Windows "
                       "PowerShell log, 4103 in the PowerShell Operational log) "
                       "with the command, script, user and invocation details "
                       "they store.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Windows PowerShell.evtx (PowerShell provider, Event ID 800) and "
                 "Microsoft-Windows-PowerShell%4Operational.evtx (Microsoft-Windows-PowerShell "
                 "provider, Event ID 4103), both named in the report's located-at line; "
                 "Channel is the log each record stores. PowerShell's event log writer "
                 "assigns 800 to pipeline execution detail and splits a long detail across "
                 "several 800 events (EventLogLogProvider.cs at v6.0.0, "
                 "https://github.com/PowerShell/PowerShell/blob/"
                 "2f818615bed15141c062dd185f659ed110d9c6ba/src/System.Management.Automation/"
                 "logging/eventlog/EventLogLogProvider.cs#L310-L327). PowerShell's "
                 "instrumentation manifest defines 4103 with the fields ContextInfo, UserData "
                 "and Payload (https://github.com/PowerShell/PowerShell/blob/"
                 "0817ada8e7b95717fda4483054ee8ed0f1367ac8/src/PowerShell.Core.Instrumentation/"
                 "PowerShell.Core.Instrumentation.man#L900-L911 and #L3927-L3940); that "
                 "manifest is PowerShell 7's, for its PowerShellCore provider, and the tested "
                 "4103 record carries the same field names. For 800, Command Line, Script "
                 "Name, User, Host Application and Host Name are CommandLine, ScriptName, "
                 "UserId, HostApplication and HostName from the record's context block, "
                 "Details is the pipeline execution detail text and Detail Part is "
                 "DetailSequence of DetailTotal. For 4103, Command Name, Command Type, Script "
                 "Name, User, Host Application and Host Name come from the ContextInfo block "
                 "and Details is Payload; Command Line and Detail Part are blank because 4103 "
                 "stores neither. Event Time (UTC) is the record's TimeCreated SystemTime, "
                 "which python-evtx renders from the FILETIME the record stores, counted in "
                 "UTC (python-evtx 0.8.1, https://github.com/williballenthin/python-evtx/"
                 "blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py"
                 "#L105-L113). Record ID is the record's EventRecordID and Computer the "
                 "machine name it stores. Measured: af_case2_win10 carries one 800 and one "
                 "4103 record, and pc_mus_001_win11 and lonewolf_win10 carry neither. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run "
                 "log and not reported; every record in both logs rendered on the registered "
                 "images. The absence of these events does not establish that no command "
                 "ran. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Windows PowerShell.evtx",
                  "*/Windows/System32/winevt/Logs/Microsoft-Windows-PowerShell%4Operational.evtx"),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no 800 or 4103 records)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no 800 or 4103 records)",
        },
    },
    "powershellScriptBlocks": {
        "name": "PowerShell Script Blocks",
        "description": "Script block text from event 4104 in the PowerShell "
                       "Operational log, with the parts of each script block "
                       "joined in order.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-PowerShell%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-PowerShell records with "
                 "Event ID 4104 are read. Microsoft documents 4104 as the event PowerShell "
                 "writes to this log for Script Block Logging, at Verbose level "
                 "(about_Logging for Windows PowerShell 5.1, "
                 "https://github.com/MicrosoftDocs/PowerShell-Docs/blob/5f0f622fc6579cf4b635eb4ac6b99ceef091460e/reference/5.1/Microsoft.PowerShell.Core/About/about_Logging.md#L41-L48). "
                 "PowerShell's instrumentation manifest defines its fields as "
                 "MessageNumber, MessageTotal, ScriptBlockText, ScriptBlockId and Path, "
                 "with the message 'Creating Scriptblock text (%1 of %2)' "
                 "(https://github.com/PowerShell/PowerShell/blob/0817ada8e7b95717fda4483054ee8ed0f1367ac8/src/PowerShell.Core.Instrumentation/PowerShell.Core.Instrumentation.man#L912-L923, "
                 "#L3941-L3962 and #L5467-L5468; PowerShell 7's manifest, whose field "
                 "names the tested records carry). The PowerShell team's 2015 post states "
                 "that Windows PowerShell breaks a script too large for one event into "
                 "multiple parts, recombined by sorting on MessageNumber and joining "
                 "ScriptBlockText, and that it also logs, without Script Block Logging "
                 "enabled, script blocks with content often used by malicious scripts "
                 "(https://web.archive.org/web/20260831174647/https://devblogs.microsoft.com/powershell/powershell-the-blue-team/); "
                 "in PowerShell 7's source a script block with suspicious content is "
                 "written at Warning level and any other at Verbose "
                 "(CompiledScriptBlock.cs, "
                 "https://github.com/PowerShell/PowerShell/blob/0817ada8e7b95717fda4483054ee8ed0f1367ac8/src/System.Management.Automation/engine/runtime/CompiledScriptBlock.cs#L1553-L1580). "
                 "One row per ScriptBlockId: Script Block Text is the ScriptBlockText of "
                 "its parts joined in MessageNumber order, and Parts is how many parts "
                 "were found of the MessageTotal the parts store. Checked against a "
                 "separate join of the raw records, the text matched for the 47, 3 and 1 "
                 "script blocks on af_case2_win10, pc_mus_001_win11 and lonewolf_win10, "
                 "and every block had every part; af_case2_win10 had 9 blocks split into 2 "
                 "to 12 parts. First Part Time (UTC) and Last Part Time (UTC) are the "
                 "earliest and latest TimeCreated SystemTime of the parts, which "
                 "python-evtx renders from the FILETIME each record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "First Part Time and Last Part Time are the same for a block stored in "
                 "one part, as on all 3 rows of pc_mus_001_win11. Level is the record's "
                 "level with Microsoft's name for it "
                 "(https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/WES/eventmanifestschema-leveltype-complextype.md#L70-L76): "
                 "it held 3 (Warning) on every row on the registered images. Path is the "
                 "script file the record names and is blank when it names none (10 of 47 "
                 "rows on af_case2_win10). User SID is the SID in the record's Security "
                 "element and Process ID the process ID in its Execution element, both "
                 "from the first part; User SID held one value on every row of "
                 "af_case2_win10 and pc_mus_001_win11. On pc_mus_001_win11 the Script "
                 "Block Text of the 3 rows is the same text under three Script Block IDs, "
                 "and Parts held 1 of 1 on every row. Record IDs are the EventRecordIDs of "
                 "the parts. Computer is the machine name the record stores and held one "
                 "value on every row of af_case2_win10 and pc_mus_001_win11. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in "
                 "the run log and not reported; every record in this log rendered on the "
                 "registered images. A script block records text PowerShell compiled; it "
                 "does not by itself establish who ran it or that it finished. Reading "
                 "needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-PowerShell%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 47 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
        },
    },
    "powershellConsoleEvents": {
        "name": "PowerShell Console Start-up Events",
        "description": "PowerShell console start-up events (40961, 40962) and IPC listening thread "
                       "events (53504) from the PowerShell Operational log, with the process ID "
                       "and account SID each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-PowerShell%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-PowerShell records with "
                 "Event ID 40961, 40962 or 53504 are read. Event is the message "
                 "PowerShell's instrumentation manifest gives each, for 53504 only as far "
                 "as 'listening thread': 40961 (0xA001) 'PowerShell console is starting "
                 "up', 40962 (0xA002) 'PowerShell console is ready for user input' and "
                 "53504 (0xD100) 'PowerShell has started an IPC listening thread on "
                 "process: %1 in AppDomain: %2' "
                 "(https://github.com/PowerShell/PowerShell/blob/0817ada8e7b95717fda4483054ee8ed0f1367ac8/src/PowerShell.Core.Instrumentation/PowerShell.Core.Instrumentation.man#L1746-L1767, "
                 "#L1091-L1102, #L5371-L5376 and #L5823-L5824; PowerShell 7's manifest, "
                 "whose event IDs and 53504 fields param1 and param2 the tested records "
                 "carry). Process ID is the process ID in the record's Execution element, "
                 "and for 53504 its param1, which equalled the Execution process ID on all "
                 "50 53504 rows on the registered images. AppDomain is the 53504 param2 "
                 "and is blank on 40961 and 40962 rows; it held DefaultAppDomain on every "
                 "53504 row on the registered images. User SID is the SID in the record's "
                 "Security element and held one value on every row of af_case2_win10. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. A record python-evtx "
                 "cannot render, or whose XML does not parse, is counted in the run log "
                 "and not reported; every record in this log rendered on the registered "
                 "images. On the registered images the other records in this log were 4104 "
                 "(the PowerShell Script Blocks artifact) and 4103 (the PowerShell "
                 "Pipeline Execution Details artifact). Reading needs the python-evtx "
                 "package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-PowerShell%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 61 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 56 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 19 rows",
        },
    },
}


def _classic_context(text):
    """Parse a classic event's "\\tKey=Value" block; continuation lines append."""
    context = {}
    key = None
    for line in (text or '').split('\n'):
        match = _CLASSIC_LINE.match(line)
        if match:
            key = match.group(1)
            context[key] = match.group(2).rstrip('\r')
        elif key is not None and line.strip():
            context[key] += '\n' + line.rstrip('\r')
    return context


def _info_context(text):
    """Parse a 4103 ContextInfo "Key = Value" block."""
    context = {}
    for line in (text or '').split('\n'):
        match = _CONTEXT_LINE.match(line)
        if match:
            context[match.group(1)] = match.group(2).strip()
    return context


def _level(value):
    label = _LEVELS.get(value)
    return f'{value} ({label})' if label else value


@artifact_processor
def powershellEngineEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'New State',
                    'Previous State', 'Provider Name', 'Host Application', 'Host Name',
                    'Host Version', 'Engine Version', 'Host ID', 'Runspace ID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _CLASSIC_LOG, 'PowerShell Engine and Provider Events',
        event_ids=set(_LIFECYCLE_EVENTS), provider=_CLASSIC_PROVIDER)
    data_list = []
    for record in records:
        strings = classic_strings(record.values)
        info = _classic_context(strings[2] if len(strings) > 2 else '')
        if record.event_id.startswith('4'):
            new_state = info.get('NewEngineState', '')
            previous_state = info.get('PreviousEngineState', '')
            provider_name = ''
        else:
            new_state = info.get('NewProviderState', '')
            previous_state = ''
            provider_name = info.get('ProviderName', '')
        data_list.append((
            record.time, record.event_id, _LIFECYCLE_EVENTS[record.event_id], new_state,
            previous_state, provider_name, info.get('HostApplication', ''),
            info.get('HostName', ''), info.get('HostVersion', ''),
            info.get('EngineVersion', ''), info.get('HostId', ''),
            info.get('RunspaceId', ''), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def powershellPipelineExecution(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Channel', 'Command Name',
                    'Command Type', 'Command Line', 'Script Name', 'User',
                    'Host Application', 'Details', 'Detail Part', 'Host Name',
                    'Record ID', 'Computer')
    label = 'PowerShell Pipeline Execution Details'
    classic, classic_sources = read_event_records(
        context, _CLASSIC_LOG, label, event_ids={'800'}, provider=_CLASSIC_PROVIDER)
    operational, operational_sources = read_event_records(
        context, _OPERATIONAL_LOG, label, event_ids={'4103'}, provider=_OPERATIONAL_PROVIDER)
    data_list = []
    for record in classic:
        strings = classic_strings(record.values)
        info = _classic_context(strings[1] if len(strings) > 1 else '')
        sequence, total = info.get('DetailSequence', ''), info.get('DetailTotal', '')
        data_list.append((
            record.time, record.event_id, record.channel, info.get('CommandName', ''),
            info.get('CommandType', ''), info.get('CommandLine', '').strip(),
            info.get('ScriptName', ''), info.get('UserId', ''),
            info.get('HostApplication', ''),
            (strings[2] if len(strings) > 2 else '').strip(),
            f'{sequence} of {total}' if sequence and total else '',
            info.get('HostName', ''), record.record_id, record.computer))
    for record in operational:
        info = _info_context(record.get('ContextInfo'))
        data_list.append((
            record.time, record.event_id, record.channel, info.get('Command Name', ''),
            info.get('Command Type', ''), '', info.get('Script Name', ''),
            info.get('User', ''), info.get('Host Application', ''),
            record.get('Payload'), '', info.get('Host Name', ''), record.record_id,
            record.computer))
    return data_headers, data_list, '\n'.join(classic_sources + operational_sources)


@artifact_processor
def powershellScriptBlocks(context):
    data_headers = (('First Part Time (UTC)', 'datetime'), ('Last Part Time (UTC)', 'datetime'),
                    'Script Block ID', 'Parts', 'Level', 'Path', 'Script Block Text',
                    'User SID', 'Process ID', 'Record IDs', 'Computer')
    records, sources = read_event_records(
        context, _OPERATIONAL_LOG, 'PowerShell Script Blocks', event_ids={'4104'},
        provider=_OPERATIONAL_PROVIDER)
    blocks = {}
    order = []
    for record in records:
        block_id = record.get('ScriptBlockId')
        if block_id not in blocks:
            blocks[block_id] = []
            order.append(block_id)
        blocks[block_id].append(record)
    data_list = []
    for block_id in order:
        parts = {}
        for record in blocks[block_id]:
            try:
                number = int(record.get('MessageNumber'))
            except ValueError:
                number = 0
            parts.setdefault(number, record)
        ordered = [parts[number] for number in sorted(parts)]
        first = ordered[0]
        totals = sorted({record.get('MessageTotal') for record in ordered})
        times = [record.time for record in ordered if record.time]
        data_list.append((
            min(times) if times else '', max(times) if times else '', block_id,
            f"{len(ordered)} of {'/'.join(totals)}",
            ', '.join(sorted({_level(record.level) for record in ordered})),
            first.get('Path'),
            ''.join(record.fields.get('ScriptBlockText') or '' for record in ordered),
            first.user_sid, first.process_id,
            ', '.join(record.record_id for record in ordered), first.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def powershellConsoleEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Process ID',
                    'AppDomain', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _OPERATIONAL_LOG, 'PowerShell Console Start-up Events',
        event_ids=set(_CONSOLE_EVENTS), provider=_OPERATIONAL_PROVIDER)
    data_list = []
    for record in records:
        process_id = record.process_id
        app_domain = ''
        if record.event_id == '53504':
            process_id = record.get('param1') or process_id
            app_domain = record.get('param2')
        data_list.append((
            record.time, record.event_id, _CONSOLE_EVENTS[record.event_id], process_id,
            app_domain, record.user_sid, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
