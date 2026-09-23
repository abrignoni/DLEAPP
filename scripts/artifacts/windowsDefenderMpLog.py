"""Microsoft Defender Antivirus MPLog (Microsoft Protection Log) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

MPLog-*.log files under ProgramData\\Microsoft\\Windows Defender\\Support are
text logs. This reads only their per-process estimated performance impact lines
(ProcessImageName, TotalTime, Count, MaxTime, MaxTimeFile, EstimatedImpact),
the line type whose fields Microsoft's performance troubleshooting page
documents (see notes). Every other line type is left unread.
"""

import os
import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

# A timestamped line: "<time> ProcessImageName: <name>, Pid: <pid>, TotalTime: ...".
# The Pid field is optional: CrowdStrike's post shows the line without it.
_TIMED_LINE = re.compile(
    r'^(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+'
    r'ProcessImageName: (?P<name>.*?)(?:, Pid: (?P<pid>\d+))?, TotalTime: (?P<total>\d+), '
    r'Count: (?P<count>\d+), MaxTime: (?P<max>\d+), MaxTimeFile: (?P<file>.*), '
    r'EstimatedImpact: (?P<impact>\d+%?)\s*$')
# The form Microsoft's documentation shows, with no time of its own:
# "Per-process counts:ProcessImageName: <name>, TotalTime: ...".
_COUNTS_LINE = re.compile(
    r'^Per-process counts:ProcessImageName: (?P<name>.*?), TotalTime: (?P<total>\d+), '
    r'Count: (?P<count>\d+), MaxTime: (?P<max>\d+), MaxTimeFile: (?P<file>.*), '
    r'EstimatedImpact: (?P<impact>\d+%?)\s*$')
_UTC_TIME = re.compile(r'^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z$')
# Line breaks: CR LF, LF or CR, so Line Number counts lines the same way whichever
# of the three a file uses.
_LINE_BREAK = re.compile(r'\r\n|\r|\n')

__artifacts_v2__ = {
    "defenderMpLogProcessImpact": {
        "name": "Microsoft Defender MPLog Process Scan Impact",
        "description": "Per-process estimated performance impact lines from "
                       "Microsoft Defender MPLog files: the process image name, the "
                       "time Defender spent scanning files it accessed, the count of "
                       "those files, and the file with the longest scan.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the MPLog-*.log files under ProgramData\\Microsoft\\Windows "
                 "Defender\\Support, each named in the Source File column and in the "
                 "report's located-at line. Only lines carrying the fields Microsoft "
                 "documents for a process's estimated performance impact are read: "
                 "ProcessImageName, TotalTime, Count, MaxTime, MaxTimeFile and "
                 "EstimatedImpact (Microsoft's 'Troubleshoot performance issues related to "
                 "real-time protection', section 'Analyze the Microsoft Protection Log', "
                 "https://github.com/MicrosoftDocs/microsoft-365-docs/blob/29be83014e65f769e66c26ef6534c534309710b2/microsoft-365/security/defender-endpoint/troubleshoot-performance-issues.md#L56-L74). "
                 "That page shows the line as 'Per-process counts:ProcessImageName: ...' "
                 "with no time of its own. On pc_mus_001_win11 the same fields also stood "
                 "on lines that began with a time and added a Pid field. CrowdStrike's "
                 "post shows that timed form, without Pid, describes its leading time as "
                 "generated in UTC, and in its case study reads Pid as the process ID "
                 "(James Lovato, CrowdStrike, 'Mind the MPLog: Leveraging Microsoft "
                 "Protection Logging for Forensic Investigations', 2022-01-20, snapshot "
                 "https://web.archive.org/web/20260305194508/https://www.crowdstrike.com/en-us/blog/how-to-use-microsoft-protection-logging-for-forensic-investigations/). "
                 "Both forms are read, with or without Pid. Process Image Name, Process "
                 "ID, Total Time (ms), Count, Max Time (ms), Max Time File and Estimated "
                 "Impact are ProcessImageName, Pid, TotalTime, Count, MaxTime, MaxTimeFile "
                 "and EstimatedImpact as stored. Microsoft's page defines TotalTime as the "
                 "cumulative duration in milliseconds spent in scans of files accessed by "
                 "the process, Count as the number of scanned files it accessed, MaxTime "
                 "as the duration in milliseconds of the longest single scan of such a "
                 "file, MaxTimeFile as the path of that file, and EstimatedImpact as the "
                 "percentage of time spent in those scans out of the period in which the "
                 "process experienced scan activity. Logged Time (as stored) is the line's "
                 "leading time. Logged Time (UTC) is that time only when it ends in Z, the "
                 "form CrowdStrike's post describes as UTC, and is blank for any other "
                 "form, because no source for the zone of a time without Z was found. A "
                 "Per-process counts line carries no time and no Pid, so both Logged Time "
                 "columns and Process ID are blank on it. Line Number is the line's number "
                 "in the decoded file, counting from 1 and breaking lines at CR LF, LF or "
                 "CR. A file is decoded by its byte-order mark; each MPLog on the "
                 "registered images began with a UTF-16 little-endian mark. On "
                 "pc_mus_001_win11 the one MPLog gave 596 rows: 585 lines began with a "
                 "time ending in Z and carried Pid, and 11 were Per-process counts lines. "
                 "The MPLog files on af_case2_win10 and lonewolf_win10 hold no line naming "
                 "ProcessImageName, so this artifact reports no rows there. A line naming "
                 "ProcessImageName that matches neither form is counted in the run log and "
                 "not read; there was none on the registered images. Not read: every other "
                 "line type in the file, including the SDN, detection and EMS detection "
                 "lines CrowdStrike's post describes. A row records scan activity Defender "
                 "measured on files the named process accessed; it does not by itself "
                 "establish who ran the process or why.",
        "paths": ("*/ProgramData/Microsoft/Windows Defender/Support/MPLog-*.log",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the MPLog holds no line naming ProcessImageName)",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 596 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the MPLog holds no line naming ProcessImageName)",
                       },
    },
}


def _decode(data):
    """Decode an MPLog by its byte-order mark; UTF-16 without one when NULs dominate."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16', errors='replace')
    if data.startswith(b'\xef\xbb\xbf'):
        return data[3:].decode('utf-8', errors='replace')
    sample = data[:4096]
    if sample and sample.count(0) > len(sample) // 3:
        return data.decode('utf-16-le', errors='replace')
    return data.decode('utf-8', errors='replace')


def _utc(stored):
    """A stored time ending in Z as a UTC datetime; any other form gives ''."""
    match = _UTC_TIME.match(stored)
    if not match:
        return ''
    date_part, time_part, fraction = match.groups()
    fraction = (fraction or '').ljust(6, '0')[:6]
    try:
        return datetime.fromisoformat(f'{date_part}T{time_part}.{fraction}').replace(
            tzinfo=timezone.utc)
    except ValueError:
        return ''


@artifact_processor
def defenderMpLogProcessImpact(context):
    data_headers = (('Logged Time (UTC)', 'datetime'), 'Logged Time (as stored)',
                    'Process Image Name', 'Process ID', 'Total Time (ms)', 'Count',
                    'Max Time (ms)', 'Max Time File', 'Estimated Impact', 'Line Number',
                    'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).lower().startswith('mplog-')
                   and str(f).lower().endswith('.log')]:
        if os.path.isdir(source):
            continue
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                text = _decode(handle.read())
        except OSError as exc:
            logfunc(f'Microsoft Defender MPLog Process Scan Impact: could not read '
                    f'{relative_source}: {exc}')
            continue
        sources.append(source)
        matched = unmatched = 0
        for line_number, line in enumerate(_LINE_BREAK.split(text), start=1):
            if 'ProcessImageName:' not in line:
                continue
            match = _TIMED_LINE.match(line) or _COUNTS_LINE.match(line)
            if match is None:
                unmatched += 1
                continue
            matched += 1
            fields = match.groupdict()
            stored_time = fields.get('time') or ''
            data_list.append((
                _utc(stored_time), stored_time, fields['name'], fields.get('pid') or '',
                fields['total'], fields['count'], fields['max'], fields['file'],
                fields['impact'], line_number, relative_source))
        logfunc(f'Microsoft Defender MPLog Process Scan Impact: {matched} lines read from '
                f'{relative_source}; {unmatched} lines naming ProcessImageName did not match '
                f'the documented shape and were not read')
    return data_headers, data_list, '\n'.join(sources)
