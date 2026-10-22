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
_UTC_TIME = re.compile(r'^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z?)$')
# Any line that begins with a time, of either form.
_LINE_TIME = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s')
# The line in the header Defender writes when its service log starts:
# "Current time: MM/DD/YYYY HH:MM:SS.fffffffff UTC (... ms since boot)".
_HEADER_UTC = re.compile(
    r'^Current time: (\d{2})/(\d{2})/(\d{4}) (\d{2}:\d{2}:\d{2})(?:\.(\d+))? UTC\b')
# How close a block's first timed line must be to its header's UTC time for the block's
# times without Z to be read as UTC. UTC offsets are whole multiples of 15 minutes, so a
# block written in a zone other than UTC differs by at least that much.
_HEADER_AGREEMENT_SECONDS = 60
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
        "last_update_date": "2026-10-22",
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
                 "with no time of its own. On pc_mus_001_win11, szechuan_win10 and "
                 "windows11_arm_defender_eicar_known_20261018 the same fields also stood on lines "
                 "that began with a time and added a Pid field. CrowdStrike's post shows that timed "
                 "form, without Pid, describes its leading time as generated in UTC, and in its case "
                 "study reads Pid as the process ID (James Lovato, CrowdStrike, 'Mind the MPLog: "
                 "Leveraging Microsoft Protection Logging for Forensic Investigations', 2022-01-20, snapshot "
                 "https://web.archive.org/web/20260305194508/https://www.crowdstrike.com/en-us/blog/how-to-use-microsoft-protection-logging-for-forensic-investigations/). "
                 "Both forms are read, the timed form with or without Pid. Process Image Name, Process "
                 "ID, Total Time (ms), Count, Max Time (ms), Max Time File and Estimated "
                 "Impact are ProcessImageName, Pid, TotalTime, Count, MaxTime, MaxTimeFile "
                 "and EstimatedImpact as stored. Microsoft's page defines TotalTime as the "
                 "cumulative duration in milliseconds spent in scans of files accessed by "
                 "the process, Count as the number of scanned files it accessed, MaxTime "
                 "as the duration in milliseconds of the longest single scan of such a "
                 "file, MaxTimeFile as the path of that file, and EstimatedImpact as the "
                 "percentage of time spent in those scans out of the period in which the "
                 "process experienced scan activity. Logged Time (as stored) is the line's "
                 "leading time as written. Its time is written in two forms: ending in Z, the form "
                 "CrowdStrike's post and Thomas Diot's artefacts.help page show (Defender support logs, "
                 "CC0-1.0, https://github.com/Qazeer/artefacts.help/blob/ec5d24fd12745691201edd1292d5f5c05fdcdb0f/pages/windows/defender_support_logs.md#L43-L49), "
                 "and without Z. No published description of the form without Z was found, and "
                 "Intrinsec's mplog_parser (MIT) matches only the form ending in Z "
                 "(https://github.com/Intrinsec/mplog_parser/blob/c8bd1cb96fbb899bccec69f84ff11a346ab16637/mplog_parser/main.py#L36). "
                 "Logged Time (UTC) is a time ending in Z read as UTC. A time without Z is read as UTC "
                 "only inside a service log block whose header line 'Current time: MM/DD/YYYY "
                 "HH:MM:SS UTC' is within 60 seconds of the block's first timed line, and is blank "
                 "otherwise, including before the file's first such header. That check rests on the "
                 "log's own header, which labels its time UTC; no published source for it was found. "
                 "On every one of the five keys below, every header was within one second of its block's "
                 "first timed line (103 headers on "
                 "windows11_arm_defender_eicar_known_20261018, 20 on pc_mus_001_win11, 9 on "
                 "szechuan_win10, 17 on af_case2_win10 and 4 on lonewolf_win10). Blocks whose "
                 "times lack Z occur only on windows11_arm_defender_eicar_known_20261018, 98 of its "
                 "103; every other block on the five keys carries times ending in Z. On "
                 "windows11_arm_defender_eicar_known_20261018, made on a lab machine whose local time "
                 "the session record gives as UTC-4, the session recorded three file writes in UTC, "
                 "and the first MPLog line naming each file carried a time without Z between 3 and 22 "
                 "milliseconds later, so in that block the form without Z was UTC (data-proven for "
                 "those three lines; the 60-second header check is what applies it to the key's other "
                 "blocks and to other images). A Per-process counts line carries no time and no Pid, so both Logged "
                 "Time columns and Process ID are blank on it; the module does not borrow a time for it "
                 "from a neighbouring line. Line Number is the line's number "
                 "in the decoded file, counting from 1 and breaking lines at CR LF, LF or "
                 "CR. A file is decoded by its byte-order mark or, without one, as UTF-16 "
                 "little-endian when NUL bytes are more than a third of its first 4,096 bytes "
                 "and as UTF-8 otherwise, with undecodable bytes replaced by U+FFFD; the MPLog on each "
                 "of the five keys began with a UTF-16 little-endian mark, and on pc_mus_001_win11 one "
                 "line that names no ProcessImageName held four replacement characters. Per key, one "
                 "MPLog each: windows11_arm_defender_eicar_known_20261018 gave 6,094 rows, 30 lines with "
                 "a time ending in Z and 6,064 with a time without Z, all carrying Pid, and Logged Time "
                 "(UTC) is filled on all 6,094; pc_mus_001_win11 gave 596 rows, 585 lines with a time "
                 "ending in Z and Pid and 11 Per-process counts lines, so Logged Time (UTC) is filled on "
                 "585; szechuan_win10 gave 17 rows, 8 lines with a time ending in Z and Pid and 9 "
                 "Per-process counts lines, so Logged Time (UTC) is filled on 8 of 17 rows and the "
                 "leading column is blank on the other 9. The MPLog files on af_case2_win10 and "
                 "lonewolf_win10 hold no line naming ProcessImageName, so this artifact reports no rows "
                 "there. A line naming ProcessImageName that matches neither form is counted in the run "
                 "log and not read; there was none on the five keys. Not read: every other "
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
                           "szechuan_win10": "Windows 10 2004 build 19041 | 17 rows",
                           "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 ARM64, Defender platform 4.18.26090.9 | 6094 rows",
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


def _parse_time(date_part, time_part, fraction):
    """A naive datetime from ISO date and time parts, keeping up to microseconds."""
    fraction = (fraction or '').ljust(6, '0')[:6]
    try:
        return datetime.fromisoformat(f'{date_part}T{time_part}.{fraction}')
    except ValueError:
        return None


def _stored_time(stored):
    """(naive datetime, ends in Z) for a stored line time, or (None, False)."""
    match = _UTC_TIME.match(stored)
    if not match:
        return None, False
    date_part, time_part, fraction, zulu = match.groups()
    return _parse_time(date_part, time_part, fraction), zulu == 'Z'


def _header_utc(line):
    """The UTC time on a service log header's 'Current time:' line, or None."""
    match = _HEADER_UTC.match(line)
    if not match:
        return None
    month, day, year, time_part, fraction = match.groups()
    return _parse_time(f'{year}-{month}-{day}', time_part, fraction)


def _utc(stored, block_is_utc=False):
    """A stored time as a UTC datetime, or ''.

    A time ending in Z is UTC. A time without Z is UTC only when block_is_utc says the
    service log block it sits in had its first timed line agree with the block's
    'Current time: ... UTC' header.
    """
    parsed, zulu = _stored_time(stored)
    if parsed is None or not (zulu or block_is_utc):
        return ''
    return parsed.replace(tzinfo=timezone.utc)


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
        header_time = None
        block_checked = block_is_utc = False
        for line_number, line in enumerate(_LINE_BREAK.split(text), start=1):
            new_header = _header_utc(line)
            if new_header is not None:
                header_time = new_header
                block_checked = block_is_utc = False
                continue
            if not block_checked:
                line_time = _LINE_TIME.match(line)
                if line_time:
                    block_checked = True
                    first_time, _ = _stored_time(line_time.group(1))
                    block_is_utc = (header_time is not None and first_time is not None
                                    and abs((first_time - header_time).total_seconds())
                                    <= _HEADER_AGREEMENT_SECONDS)
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
                _utc(stored_time, block_is_utc), stored_time, fields['name'], fields.get('pid') or '',
                fields['total'], fields['count'], fields['max'], fields['file'],
                fields['impact'], line_number, relative_source))
        logfunc(f'Microsoft Defender MPLog Process Scan Impact: {matched} lines read from '
                f'{relative_source}; {unmatched} lines naming ProcessImageName did not match '
                f'the documented shape and were not read')
    return data_headers, data_list, '\n'.join(sources)
