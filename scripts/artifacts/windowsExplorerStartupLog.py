"""Windows ExplorerStartupLog.etl (Explorer startup trace) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads ExplorerStartupLog.etl and ExplorerStartupLog_RunOnce.etl from a user profile's
AppData\\Local\\Microsoft\\Windows\\Explorer folder with scripts/etl.py and reports the Shell-Core events
9705 to 9708 they hold (enumeration of the commands of a registry key and execution of each command), and
one row per file for its trace session. The event layouts are the provider templates of Windows 11 build
26200, sourced in the notes.
"""

__artifacts_v2__ = {
    "windowsExplorerStartupLogCommands": {
        "name": "Explorer Startup Log Commands",
        "description": "Shell-Core events 9705 to 9708 in a user profile's ExplorerStartupLog.etl and "
                       "ExplorerStartupLog_RunOnce.etl trace files: the start and finish of the enumeration of "
                       "commands for a registry key and of the execution of each command, with the process ID "
                       "the finish record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Windows",
        "notes": ("Reads ExplorerStartupLog.etl and ExplorerStartupLog_RunOnce.etl from a user profile's "
                  'AppData\\Local\\Microsoft\\Windows\\Explorer folder with scripts/etl.py, which names the source of each '
                  'layout it reads. One row per Microsoft-Windows-Shell-Core (provider '
                  "30336ed4-e327-447c-9de0-51b652c86108) event 9705, 9706, 9707 or 9708. Event is the provider's "
                  "message for each without the key, command and PID it inserts: 9705 and 9706 'Started' and 'Finished "
                  "enumeration of commands for registry key', 9707 'Started execution of command' and 9708 'Finished "
                  "execution of command'. The layouts are the provider's templates, KeyName (UnicodeString) for 9705 "
                  'and 9706, Command (UnicodeString) for 9707 and PID (UInt32) then Command for 9708, as Windows 11 '
                  'build 26200 gives them through its provider metadata (Get-WinEvent -ListProvider), for version 0 of '
                  'each event; an event of another version, or whose data does not fit its template, is counted in the '
                  'run log and not reported. On the 26 files of the inputs below, written by Windows 7, 8.1, 10 and 11, '
                  'every one of these events was version 0 and used exactly the bytes of its template. Registry Key is '
                  'KeyName, Command is Command and Command Process ID is the PID of 9708, as stored less leading and '
                  "trailing whitespace; Logging Process ID is the process ID in the event's header. On the inputs below "
                  'Registry Key held three values, each a key path without its hive (one followed by a comma and a '
                  'value name), so the row does not say whether it was the machine or a user key. On the Windows 10 and '
                  '11 inputs no ExplorerStartupLog.etl held a 9705 or 9706 (eight of the nine files held 9707 and 9708, '
                  'one held none of the four), so those rows name no registry key and do not say which key or list a '
                  'command came from. Command is the stored text: on three inputs 10 rows held a command that began '
                  'with a file name and carried a closing quote with no opening quote and no folder. User Profile '
                  "Folder is the name of the folder that holds AppData in the file's path, and Log File is the file's "
                  "name; User Profile Folder held one value on the five inputs with one profile's files, and Log File "
                  'held one value on szechuan_win10 and alihadi_challenge3_win81, which had no '
                  "ExplorerStartupLog_RunOnce.etl. Event Time (UTC) is the event's own time stamp, converted the way "
                  'scripts/etl.py states. On the three files of the Windows 11 build 26200 known data (two in the input '
                  'below and the earlier ExplorerStartupLog_RunOnce.etl of the same profile; the ExplorerStartupLog.etl '
                  'there names build 26100 in its header) the time of every Shell-Core event, 7,002 in all, equalled to '
                  'the 100 ns the time tracerpt on that build gave for it, and the key, command, PID and process ID of '
                  "the 22 command events (9705 to 9708) read from them equalled tracerpt's; the report shows "
                  'microseconds. Windows also writes these events to the Shell-Core Operational event log, which '
                  'Shell-Core Run Key Command Events reads. Compared by event ID, key, command and both process IDs, 90 '
                  'of the 114 rows of the Windows 8.1, 10 and 11 inputs had a row in that artifact under 16 ms away, '
                  'and the other 24 (on pc_mus_001_win11, szechuan_win10 and the known data) were earlier than the '
                  'oldest record that artifact read. The run found no Shell-Core Operational log file in the two '
                  'Windows 7 images, so their 288 rows had nothing to be compared with. When Windows writes each file '
                  'was tested in one case only: on the build 26200 known data ExplorerStartupLog_RunOnce.etl was '
                  'rewritten at a sign-in that ran a planted HKLM RunOnce command and was not at a sign-in where the '
                  'only planted commands were HKCU Run and RunOnce ones, and ExplorerStartupLog.etl changed at neither. '
                  "Explorer Startup Log Trace Sessions lists each file's trace session. Not reported: the files' other "
                  'Shell-Core events, which that artifact counts.'),
        "paths": ("*/AppData/Local/Microsoft/Windows/Explorer/ExplorerStartupLog*.etl",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "windows11_arm_explorer_startuplog_known_20261111": "Windows 11 build 26200 (ARM64) | 12 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 14 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 16 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 8 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 18 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 36 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 114 rows",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 174 rows",
        },
    },
    "windowsExplorerStartupLogSessions": {
        "name": "Explorer Startup Log Trace Sessions",
        "description": "One row per ExplorerStartupLog.etl or ExplorerStartupLog_RunOnce.etl trace file in a "
                       "user profile: the start and end time its trace session header stores and the number of "
                       "Shell-Core events read from it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Windows",
        "notes": ("One row per ExplorerStartupLog.etl or ExplorerStartupLog_RunOnce.etl read from a user profile's "
                  'AppData\\Local\\Microsoft\\Windows\\Explorer folder with scripts/etl.py, which names the source of each '
                  "layout it reads. Trace Start (UTC) and Trace End (UTC) are StartTime and EndTime of the file's "
                  'TRACE_LOGFILE_HEADER, each a FILETIME; an EndTime of 0 is shown blank (one of the 26 files of the '
                  'inputs below, on af_case2_win10, had none). First Event (UTC) and Last Event (UTC) are the earliest '
                  "and latest time among the file's Microsoft-Windows-Shell-Core events, converted the way "
                  'scripts/etl.py states; Explorer Startup Log Commands gives what that conversion was compared with. '
                  "Shell-Core Events counts the file's events of that provider, of any ID, and Command Events (9705 to "
                  '9708) the ones Explorer Startup Log Commands reports. Events Lost and Buffers Lost are EventsLost '
                  'and BuffersLost of the same header, as stored; Events Lost held one value, 0, on all 26 files, and '
                  'Buffers Lost held one value, 0, on all 26 files. User Profile Folder is the name of the folder that '
                  "holds AppData in the file's path, and Log File is the file's name; User Profile Folder held one "
                  "value on the five inputs with one profile's files, and Log File held one value on szechuan_win10 and "
                  'alihadi_challenge3_win81, which had no ExplorerStartupLog_RunOnce.etl. When Windows writes each file '
                  'was tested in one case only: on the Windows 11 build 26200 known data ExplorerStartupLog_RunOnce.etl '
                  'was rewritten at a sign-in that ran a planted HKLM RunOnce command and was not at a sign-in where '
                  'the only planted commands were HKCU Run and RunOnce ones, and ExplorerStartupLog.etl changed at '
                  'neither; its session there started about 15 months before the file was copied. Which sign-in a '
                  "file's session belongs to is not established from the file. A file etl.py cannot read as an ETL file "
                  'is named in the run log and gets no row.'),
        "paths": ("*/AppData/Local/Microsoft/Windows/Explorer/ExplorerStartupLog*.etl",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "windows11_arm_explorer_startuplog_known_20261111": "Windows 11 build 26200 (ARM64) | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 2 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 4 rows",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 6 rows",
        },
    },
}

from collections import Counter  # noqa: E402  pylint: disable=wrong-import-position
from datetime import datetime, timedelta, timezone  # noqa: E402  pylint: disable=wrong-import-position
from pathlib import PurePath  # noqa: E402  pylint: disable=wrong-import-position

from scripts import etl  # noqa: E402  pylint: disable=wrong-import-position
from scripts.ilapfuncs import artifact_processor, logfunc  # noqa: E402  pylint: disable=wrong-import-position

_SHELL_CORE = '30336ed4-e327-447c-9de0-51b652c86108'       # Microsoft-Windows-Shell-Core

# (event ID, version): (message without its inserts, template), from the provider metadata of Windows 11
# build 26200 (see notes).
_EVENTS = {
    (9705, 0): ('Started enumeration of commands for registry key', (('KeyName', 'win:UnicodeString'),)),
    (9706, 0): ('Finished enumeration of commands for registry key', (('KeyName', 'win:UnicodeString'),)),
    (9707, 0): ('Started execution of command', (('Command', 'win:UnicodeString'),)),
    (9708, 0): ('Finished execution of command', (('PID', 'win:UInt32'), ('Command', 'win:UnicodeString'))),
}
_IDS = {event_id for event_id, _version in _EVENTS}
_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
_TAIL = ('appdata', 'local', 'microsoft', 'windows', 'explorer')


def _utc(filetime):
    if filetime is None or filetime <= 0:
        return ''
    return _FILETIME_EPOCH + timedelta(microseconds=filetime // 10)


def _profile(source):
    """The folder that holds AppData\\Local\\Microsoft\\Windows\\Explorer, by its place in the path."""
    parts = PurePath(str(source).replace('\\', '/')).parts
    if len(parts) >= 7 and tuple(part.lower() for part in parts[-6:-1]) == _TAIL:
        return parts[-7]
    return ''


def startup_log(data, label, problems):
    """(trace, [(EtlEvent, message, values)], Shell-Core event count) for one file's bytes.

    The events returned are Shell-Core 9705 to 9708 decoded with their templates. One of another version, or
    whose data does not fit its template, is counted in `problems` and left out."""
    trace = etl.EtlFile(data)
    found = []
    total = 0
    for event in trace.events():
        if event.provider != _SHELL_CORE:
            continue
        total += 1
        if event.event_id not in _IDS:
            continue
        known = _EVENTS.get((event.event_id, event.version))
        if known is None:
            problems[f'{label}: events {event.event_id} of version {event.version}, which has no template here'] += 1
            continue
        message, template = known
        try:
            values, left = etl.decode(event.data, template, event.pointer_size)
        except ValueError:
            problems[f'{label}: events {event.event_id} whose data ends before their template'] += 1
            continue
        if left:
            problems[f'{label}: events {event.event_id} with data left after their template'] += 1
            continue
        found.append((event, message, values))
    for problem, count in trace.problems.items():
        problems[f'{label}: {problem}'] += count
    if trace.header['clock_type'] not in (etl.CLOCK_PERFORMANCE_COUNTER, etl.CLOCK_SYSTEM_TIME):
        problems[f"{label}: a clock type of {trace.header['clock_type']}, whose event times are left blank"] += 1
    return trace, found, total


def _read(context, label):
    """[(source, trace, events, Shell-Core event count)] for each file read, in path order."""
    logs = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if not PurePath(source.replace('\\', '/')).name.lower().endswith('.etl'):
            continue
        problems = Counter()
        try:
            with open(source, 'rb') as handle:
                data = handle.read()
            trace, found, total = startup_log(data, label, problems)
        except (OSError, etl.EtlError) as exc:
            logfunc(f'{label}: {context.get_relative_path(source)} not read: {type(exc).__name__}: {exc}')
            continue
        logs.append((source, trace, found, total))
        for problem, count in sorted(problems.items()):
            logfunc(f'{problem}: {count} in {context.get_relative_path(source)}')
    return logs


@artifact_processor
def windowsExplorerStartupLogCommands(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Registry Key', 'Command',
                    'Command Process ID', 'Logging Process ID', 'User Profile Folder', 'Log File')
    logs = _read(context, 'Explorer Startup Log Commands')
    data_list = []
    for source, _trace, found, _total in logs:
        profile, name = _profile(source), PurePath(source.replace('\\', '/')).name
        rows = sorted(found, key=lambda row: (row[0].filetime or 0, row[0].buffer, row[0].offset))
        for event, message, values in rows:
            pid = values.get('PID')
            data_list.append((_utc(event.filetime), event.event_id, message, values.get('KeyName', '').strip(),
                              values.get('Command', '').strip(), '' if pid is None else pid, event.process_id,
                              profile, name))
    return data_headers, data_list, '\n'.join(source for source, *_rest in logs)


@artifact_processor
def windowsExplorerStartupLogSessions(context):
    data_headers = (('Trace Start (UTC)', 'datetime'), ('Trace End (UTC)', 'datetime'),
                    ('First Event (UTC)', 'datetime'), ('Last Event (UTC)', 'datetime'), 'User Profile Folder',
                    'Log File', 'Shell-Core Events', 'Command Events (9705 to 9708)', 'Events Lost',
                    'Buffers Lost')
    logs = _read(context, 'Explorer Startup Log Trace Sessions')
    data_list = []
    for source, trace, found, total in logs:
        header = trace.header
        times = [event.filetime for event in trace.events()
                 if event.provider == _SHELL_CORE and event.filetime]
        data_list.append((_utc(header['start_time']), _utc(header['end_time']),
                          _utc(min(times)) if times else '', _utc(max(times)) if times else '',
                          _profile(source), PurePath(source.replace('\\', '/')).name, total, len(found),
                          header['events_lost'], header['buffers_lost']))
    data_list.sort(key=lambda row: (str(row[0]), row[4], row[5]))
    return data_headers, data_list, '\n'.join(source for source, *_rest in logs)
