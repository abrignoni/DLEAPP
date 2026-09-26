"""Windows Update ReportingEvents.log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Windows\\SoftwareDistribution\\ReportingEvents.log, the tab-separated
UTF-16 text log where Windows Update records the result of each detection,
download and install step. Each line carries its time with a UTC offset, an
event ID and name, a status, a category, a result code and a message. Field
meanings and sources are in the notes.
"""

import os
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'Windows Update Reporting Events'
# Lines carry 12 tab-separated fields, or 13 with a trailing value (see notes).
_FIELD_COUNTS = (12, 13)
# 2019-03-19 05:59:52:781-0700: local date and time, milliseconds after a colon,
# and the offset from UTC.
_TIME = re.compile(r'^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}):(\d{3})([+-])(\d{2})(\d{2})$')
_EVENT = re.compile(r'^(\d+) \[([A-Z_]+)\]$')
_TITLE = re.compile(r'the following update(?: with error 0x[0-9A-Fa-f]+)?: (.+)$')

__artifacts_v2__ = {
    "windowsUpdateReportingEvents": {
        "name": "Windows Update Reporting Events",
        "description": "Windows Update detection, download and install results from "
                       "ReportingEvents.log: the time, event, status, category, result code "
                       "and message of each line, with the update title an install line "
                       "names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from Windows\\SoftwareDistribution\\ReportingEvents.log, named in the report's "
                 "located-at line; the file is decoded as UTF-16 when it opens with a byte order mark, as "
                 "it did on every tested image, and as UTF-8 otherwise. Microsoft's Japan Configuration "
                 "Manager and WSUS support team describes the file as recording the result of each Windows "
                 "Update detection, download and install step, with an error code on a line for a step "
                 "that failed, and shows the event names AGENT_DETECTION_FINISHED, AGENT_DOWNLOAD_STARTED, "
                 "AGENT_DOWNLOAD_SUCCEEDED, AGENT_INSTALLING_STARTED, AGENT_INSTALLING_PENDING and "
                 "AGENT_INSTALLING_SUCCEEDED with example lines ('ReportingEvents.log の見方', 2 February "
                 "2018, "
                 "https://github.com/jpmem/blog/blob/9851a12e7e8d542b39b55d3dcb17e31e8a017349/articles/wsus/2018-02-02_01.md#L21-L102). "
                 "Every line on the tested images held 13 tab-separated fields; the post's example lines "
                 "hold 12, without the last, so a line of 12 or 13 fields is read, and any other line is "
                 "counted in the run log and skipped (none on the tested images). Recorded Time is the "
                 "second field as stored: the local date and time with milliseconds and the offset from "
                 "UTC, which was -0700 on every line of af_case2_win10 and szechuan_win10, -0700 or -0400 "
                 "on lonewolf_win10 and -0800 or -0500 on pc_mus_001_win11. Event Time (UTC) is that time "
                 "converted with its own offset. Event ID and Event are the fourth field split into its "
                 "number and its bracketed name. Status, Category and Message are the tenth, eleventh and "
                 "twelfth fields as stored; Status held Success on every row of af_case2_win10 and "
                 "szechuan_win10. Result Code (as stored) is the eighth field, which carries the error "
                 "code on a failure line: 80246017, 80073d02 or 80246007 on the tested images' Failure "
                 "lines. Their Success lines carried 0, or 240005, 240006 or 240010, or 8024000b on every "
                 "AGENT_DOWNLOAD_CANCELED line. Client (as stored) is the ninth field, a name such as "
                 "UpdateOrchestrator, Windows Defender or <<PROCESS>>: svchost.exe on the tested images; "
                 "what it names is not established here. Identifier (as stored) is the sixth field, a GUID "
                 "that was all zeros or another GUID on detection lines and a GUID on download and install "
                 "lines of the tested images; what it identifies is not established here, so it is "
                 "reported as stored. Update Title is the text after 'the following update: ' (or after "
                 "the error code in 'the following update with error ...: ') in the message, filled on "
                 "every line of the tested images whose message names an update: the install lines. "
                 "Download and detection lines name no update title. Not reported: the first field (a GUID "
                 "per line), the third and fifth fields (1 and 101 on every line of the tested images), "
                 "the seventh field (a number whose meaning is not established here) and the thirteenth "
                 "field.",
        "paths": ("*/Windows/SoftwareDistribution/ReportingEvents.log",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 85 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 400 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 987 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 308 rows",
        },
    },
}


def utc_time(text):
    """The line's local time with its offset, as an aware UTC datetime, or ''."""
    match = _TIME.match(text.strip())
    if not match:
        return ''
    year, month, day, hour, minute, second, millis, sign, off_h, off_m = match.groups()
    try:
        offset = timedelta(hours=int(off_h), minutes=int(off_m))
        local = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                         int(millis) * 1000,
                         tzinfo=timezone(offset if sign == '+' else -offset))
    except ValueError:
        return ''
    return local.astimezone(timezone.utc)


def decode(raw):
    """The file's text: UTF-16 when it opens with a byte order mark, else UTF-8."""
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16', 'replace')
    return raw.decode('utf-8', 'replace')


def line_row(fields):
    """A report row for the tab-separated fields of one line (the first 12 are read)."""
    event = _EVENT.match(fields[3].strip())
    title = _TITLE.search(fields[11])
    return (utc_time(fields[1]), fields[1].strip(),
            event.group(1) if event else fields[3].strip(),
            event.group(2) if event else '',
            fields[9].strip(), fields[10].strip(), fields[7].strip(), fields[8].strip(),
            fields[5].strip(), fields[11].strip(), title.group(1).strip() if title else '')


@artifact_processor
def windowsUpdateReportingEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Recorded Time', 'Event ID', 'Event',
                    'Status', 'Category', 'Result Code (as stored)', 'Client (as stored)',
                    'Identifier (as stored)', 'Message', 'Update Title')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                text = decode(handle.read())
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        rows = []
        skipped = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            fields = line.split('\t')
            if len(fields) not in _FIELD_COUNTS:
                skipped += 1
                continue
            rows.append(line_row(fields))
        logfunc(f'{_LABEL}: {len(rows)} lines read from {relative}; {skipped} lines without '
                f'12 or 13 tab-separated fields skipped')
        data_list.extend(rows)
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
