"""Windows StartupInfo (WDI LogFiles) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the per-user XML files in Windows\\System32\\WDI\\LogFiles\\StartupInfo, named
<user SID>_StartupInfo<n>.xml. Each holds a StartupData element with the interval it
covers and one Process element per process: the program, its PID, command line,
start time, parent, and the disk and CPU usage recorded for it. Field meanings,
time handling and sources are in the notes.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'Startup Info'
_FILE_NAME = re.compile(r'^(S-1-[0-9-]+)_(StartupInfo\d+\.xml)$', re.IGNORECASE)
# StartTime and ParentStartTime are written as 2023/01/05:01:24:03.6392207.
_TIME = re.compile(r'^(\d{4})/(\d{2})/(\d{2}):(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,7}))?$')
_UNITS = {'DiskUsage': 'bytes', 'CpuUsage': 'us'}

__artifacts_v2__ = {
    "startupInfo": {
        "name": "Startup Info",
        "description": "Processes listed in the per-user StartupInfo XML files under "
                       "Windows\\System32\\WDI\\LogFiles: the program name as stored, "
                       "command line, process and parent IDs and start times, and the disk "
                       "and CPU usage recorded for each, with the user SID the file is "
                       "named for.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the XML files in Windows\\System32\\WDI\\LogFiles\\StartupInfo named <user "
                 "SID>_StartupInfo<n>.xml, each named in the report's located-at line; the files on the "
                 "tested images are UTF-16 XML. Hadar Yudovich and Martin Korman describe them as named "
                 "for the SID of the user who logged on, numbered up to five per user with the least "
                 "recently updated one overwritten at a later logon, and listing processes executed in the "
                 "first 90 seconds after the user logged on; they found them on Windows 8 and later and "
                 "not on Windows Server ('StartupInfo: Autoruns served up on a plate', DFIR Dudes, 19 July "
                 "2018, "
                 "https://medium.com/dfir-dudes/startupinfo-autoruns-served-up-on-a-plate-ba2da0c753c5, "
                 "archived at "
                 "https://web.archive.org/web/20190531012350/https://medium.com/dfir-dudes/startupinfo-autoruns-served-up-on-a-plate-ba2da0c753c5). "
                 "The tested images carry at most five files per SID. One row is reported per Process "
                 "element. Start Time (UTC) is StartTime, Program is the Name attribute, PID the PID "
                 "attribute, Command Line is CommandLine, and Parent Program, Parent PID and Parent Start "
                 "Time (UTC) are ParentName, ParentPID and ParentStartTime. Disk Usage (bytes) and CPU "
                 "Usage (microseconds) are DiskUsage and CpuUsage, whose Units attributes read bytes and "
                 "us on every row of the tested images; a value in any other unit is shown with that unit. "
                 "Started in Trace (s) is the StartedInTraceSec attribute. Interval Start (ms) and "
                 "Interval End (ms) are the StartupData element's IntervalStartMs and IntervalEndMs, which "
                 "were 90,000 ms apart in every file of the tested images. User SID and File are the two "
                 "parts of the file name. The files record no time zone. StartTime and ParentStartTime are "
                 "written as year/month/day:hour:minute:second with seven decimal places, and are reported "
                 "as UTC, truncated to microseconds, because they line up with UTC event records on the "
                 "tested images, which are set to Pacific and Eastern time: on every file that lists "
                 "processes, StartTime minus StartedInTraceSec fell 0.1 to 1.6 seconds after the StartTime "
                 "of the latest Kernel-General 12 (boot) record before it in the System log, and Interval "
                 "Start (UTC), which is StartTime minus StartedInTraceSec plus IntervalStartMs for each "
                 "row, fell 0.07 to 2.3 seconds after a User Profile Service logon notification (event 1) "
                 "for the file's SID on 15 of those 17 files. Of the other two, one lonewolf_win10 file "
                 "lay more than two hours from any logon notification for its SID in that log, and one "
                 "szechuan_win10 file lay 3,598 seconds before its user's logon notification: that "
                 "system's clock was set forward by 3,599 seconds (Kernel-General 1) 30 seconds after the "
                 "boot the file's trace began at, and adding that change to the file's times puts its "
                 "interval start 1.2 seconds after the logon notification, so a clock change after boot "
                 "left that file's times out of step with the event logs by the size of the change. On "
                 "every row of the tested images Started in Trace (s) fell within the file's interval "
                 "except the 17 rows of one lonewolf_win10 file, whose processes started 6,245 to 6,260 "
                 "seconds into the trace, long after its interval ended, so a row is not always a process "
                 "started within 90 seconds of a logon. On af_case2_win10 (build 17763) and lonewolf_win10 "
                 "(build 16299) Program held a cut-off string, C:\\Devic or C:\\Devi, on every row, and the "
                 "program path is at the start of Command Line on each of those rows; on pc_mus_001_win11 "
                 "and szechuan_win10 it held a full path on every row. Parent Start Time (UTC) was at or "
                 "before Start Time (UTC) on every row. User SID held one value on every row of "
                 "af_case2_win10, lonewolf_win10 and pc_mus_001_win11, and Parent Program held "
                 "explorer.exe on every row of af_case2_win10. A file with no Process element adds no "
                 "rows; lonewolf_win10 and szechuan_win10 each carry one. Not reported: the "
                 "ReadAheadAnalysisTime and RurLegacyResourceAttribution elements each file carries. A "
                 "file that does not parse as XML, or whose root is not StartupData, is named in the run "
                 "log and skipped; every file on the tested images parsed.",
        "paths": ("*/Windows/System32/WDI/LogFiles/StartupInfo/*_StartupInfo*.xml",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 20 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 33 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 127 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 40 rows",
        },
    },
}


def utc_time(text):
    """A StartupInfo time as an aware UTC datetime, truncated to microseconds, or ''."""
    match = _TIME.match((text or '').strip())
    if not match:
        return ''
    year, month, day, hour, minute, second, fraction = match.groups()
    try:
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                        int((fraction or '0').ljust(6, '0')[:6]), tzinfo=timezone.utc)
    except ValueError:
        return ''


def usage(element, field):
    """A usage value as stored, with its unit appended when it is not the expected one."""
    if element is None:
        return ''
    value = (element.text or '').strip()
    unit = element.get('Units', '')
    return value if unit == _UNITS[field] else f'{value} {unit}'.strip()


def interval_start(start_time, trace_seconds, interval_ms):
    """StartTime - StartedInTraceSec + IntervalStartMs, or '' when a part is missing."""
    try:
        return start_time - timedelta(seconds=float(trace_seconds)) + timedelta(
            milliseconds=int(interval_ms))
    except (TypeError, ValueError):
        return ''


def process_rows(root, sid, file_name):
    """One row per Process element of a parsed StartupData root."""
    rows = []
    start_ms = root.get('IntervalStartMs', '')
    end_ms = root.get('IntervalEndMs', '')
    for process in root:
        if process.tag != 'Process':
            continue
        started = utc_time(process.findtext('StartTime'))
        trace_seconds = process.get('StartedInTraceSec', '')
        rows.append((
            started, process.get('Name', ''), process.get('PID', ''),
            (process.findtext('CommandLine') or '').strip(),
            (process.findtext('ParentName') or '').strip(),
            (process.findtext('ParentPID') or '').strip(),
            utc_time(process.findtext('ParentStartTime')),
            usage(process.find('DiskUsage'), 'DiskUsage'),
            usage(process.find('CpuUsage'), 'CpuUsage'),
            trace_seconds,
            interval_start(started, trace_seconds, start_ms) if started else '',
            start_ms, end_ms, sid, file_name))
    return rows


@artifact_processor
def startupInfo(context):
    data_headers = (('Start Time (UTC)', 'datetime'), 'Program', 'PID', 'Command Line',
                    'Parent Program', 'Parent PID', ('Parent Start Time (UTC)', 'datetime'),
                    'Disk Usage (bytes)', 'CPU Usage (microseconds)', 'Started in Trace (s)',
                    ('Interval Start (UTC)', 'datetime'), 'Interval Start (ms)',
                    'Interval End (ms)', 'User SID', 'File')
    data_list = []
    sources = []
    for path in sorted(str(f) for f in context.get_files_found()):
        if os.path.isdir(path):
            continue
        match = _FILE_NAME.match(os.path.basename(path))
        if not match:
            continue
        relative = context.get_relative_path(path)
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError) as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        if root.tag != 'StartupData':
            logfunc(f'{_LABEL}: {relative} is not a StartupData document ({root.tag})')
            continue
        rows = process_rows(root, match.group(1), match.group(2))
        sources.append(path)
        data_list.extend(rows)
        logfunc(f'{_LABEL}: {len(rows)} processes in {relative}')
    return data_headers, data_list, '\n'.join(sources)
