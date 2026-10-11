"""Requests the CUPS scheduler logged in its access_log on a Linux or macOS system, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "cupsAccessLog": {
        "name": "CUPS Access Log",
        "description": "Requests the CUPS scheduler logged in access_log, one row per line: the time of the request, "
                       "the host and user it came from, the resource, the HTTP status and the IPP operation and "
                       "status, which name print job submissions and cancellations and printer changes.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Printing (CUPS)",
        "notes": "Reads access_log in the CUPS log folder and its numbered rotations, gzip ones included, and "
                 "reports one row per line. cupsd writes a line as host, a group field written as '-', user, the "
                 "time in square brackets, the request in quotes (method, resource, HTTP version), the HTTP status, "
                 "a byte count, the IPP operation and the IPP status (Reference: CUPS v2.4.16, commit "
                 "7523763f00d2063f88026d93bc5b29806240de2b, https://github.com/OpenPrinting/cups, 'scheduler/log.c' "
                 "lines 1198 to 1211, and 'man/cupsd-logs.5' lines 22 to 116). Time (UTC) is the time in the "
                 "brackets, which cupsd takes once it has read the request line ('scheduler/client.c' line 801) and "
                 "writes as local time followed by the offset from UTC ('scheduler/log.c' lines 362 to 369), "
                 "converted with that offset; Time (As Written) is the text between the brackets. Host is the "
                 "client's host name or address. User is the authenticated user name, empty when the line has '-'. "
                 "IPP Operation and IPP Status are the names cupsd wrote, empty when the line has '-'. Bytes is the "
                 "count as written; the manual describes it as the bytes in the request. The manual lists HTTP "
                 "Status 401 as Unauthorized, authentication required. With the default AccessLogLevel, actions, "
                 "cupsd leaves out read requests such as Get-Jobs and Get-Printer-Attributes when they have an IPP "
                 "response that succeeded or was not-found ('scheduler/conf.c' line 712, 'scheduler/log.c' lines "
                 "1057 to 1154), so the log mostly holds job submissions, job changes, subscriptions and "
                 "configuration changes; a read request with no IPP response is still written, as the CUPS-Get-PPD "
                 "row of the sample shows. A line in no such form is counted in the run log and not reported, and a "
                 "time that is not a calendar time leaves Time (UTC) empty and keeps the row. ubuntu2604_arm64_cups "
                 "is known data from a VM running CUPS 2.4.16 with the cups-pdf virtual printer, where a script "
                 "installed the printer and the desktop user then printed two files with lp, submitted a third on "
                 "hold and cancelled it. The 292 rows are every line of the 8 files (40, 33, 37, 37, 36, 37, 37 and "
                 "35 lines), from 2026-09-29 04:06:06 to 2026-10-06 20:18:37 UTC by the VM's clock; no line was left "
                 "out. 3 rows are Create-Job on /printers/PDF, each followed in the same second by a Send-Document "
                 "row, and each Time (UTC) is the second the script recorded for that lp command; 1 row is "
                 "Cancel-Job on /jobs/, in the second the script recorded for the cancel. 5 rows on /admin/ (2 "
                 "CUPS-Add-Modify-Printer, Resume-Printer, CUPS-Accept-Jobs and CUPS-Set-Default) fall between the "
                 "script's start and the end of the package installation that added the printer; the rows do not "
                 "name the printer. User is empty on the 7 job rows (3 Create-Job, 3 Send-Document and the "
                 "Cancel-Job), so in this sample the log does not name who printed; 34 of the 292 rows hold a user, "
                 "with two different names. The other rows are 220 Renew-Subscription, 30 Cancel-Subscription and 23 "
                 "Create-Printer-Subscriptions requests, whose client is not established, 5 requests to /admin/ "
                 "answered 401 with no IPP operation, and one CUPS-Get-PPD and one CUPS-Get-PPDs. HTTP Status is 200 "
                 "on 258 rows and 401 on 34. Host, Method and HTTP Version each held one value on all 292 rows: "
                 "localhost, POST and 1.1. Not exercised on real data: a request from another host, a GET or PUT "
                 "request, the time with microseconds that LogTimeFormat usecs writes, an offset that is not a whole "
                 "number of hours, and macOS; the time forms were tested with constructed input. A row shows that "
                 "cupsd received the request and how it answered, not that a page was printed. cupsd renames the log "
                 "to access_log.O once it passes MaxLogSize, replacing the earlier one ('scheduler/log.c' lines 261 "
                 "to 274), and a system log rotation can remove older files; a different AccessLogLevel logs more or "
                 "fewer requests, and with AccessLog set to syslog the lines go to the system log and not to this "
                 "file, so the absence of a row is not evidence that nothing was printed.",
        "paths": ("*/var/log/cups/access_log*",),
        "output_types": "standard",
        "artifact_icon": "printer",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (no member matches the declared paths; the log folder is empty)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS aarch64, CUPS 2.4.16 | 292 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import read_file

# host group user [DD/Mon/YYYY:HH:MM:SS[.uuuuuu] +ZZZZ] "method resource HTTP/version" status bytes operation status
_LINE = re.compile(r'(\S+) (\S+) (.+?) \[((\d{2})/([A-Z][a-z]{2})/(\d{4}):(\d{2}):(\d{2}):(\d{2})(?:\.(\d{6}))? '
                   r'([+-]\d{2})(-?\d{2}))\] "(\S+) (\S+) HTTP/(\d+\.\d+)" (\d+) (\d+) (\S+) (\S+)')
_MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
NOT_REQUEST = 'non-empty lines in no access_log form, not reported'
NO_TIME = 'times that are not a calendar time, Time (UTC) left blank'


def request_utc(day, month, year, hour, minute, second, micro, zone_hours, zone_minutes):
    """The UTC time of a request, or '' when the month is not one CUPS writes or the fields are not a time. CUPS
    writes the zone as the offset's whole hours with a sign and then its minutes, which carry their own minus sign
    for an offset west of UTC that is not a whole number of hours, so either field can hold the minus."""
    if month not in _MONTHS:
        return ''
    hours = int(zone_hours)
    minutes = abs(int(zone_minutes))
    offset = timedelta(hours=abs(hours), minutes=minutes)
    if zone_hours[0] == '-' or zone_minutes[0] == '-':
        offset = -offset
    try:
        local = datetime(int(year), _MONTHS.index(month) + 1, int(day), int(hour), int(minute), int(second),
                         int(micro or 0), tzinfo=timezone.utc)
        return local - offset
    except (ValueError, OverflowError):
        return ''


def access_rows(data, counts):
    """(time, time as written, host, user, method, resource, http version, status, bytes, operation, ipp status,
    line) for each request line of an access_log."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        line = raw.rstrip(b'\r').decode('utf-8', 'backslashreplace')
        if not line.strip():
            continue
        match = _LINE.fullmatch(line)
        if not match:
            counts[NOT_REQUEST] += 1
            continue
        (host, _group, user, written, day, month, year, hour, minute, second, micro, zone_hours, zone_minutes, method,
         resource, version, status, size, operation, ipp_status) = match.groups()
        when = request_utc(day, month, year, hour, minute, second, micro, zone_hours, zone_minutes)
        if when == '':
            counts[NO_TIME] += 1
        rows.append((when, written, host, '' if user == '-' else user, method, resource, version, status, size,
                     '' if operation == '-' else operation, '' if ipp_status == '-' else ipp_status, number))
    return rows


@artifact_processor
def cupsAccessLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time (As Written)', 'Host', 'User', 'Method', 'Resource',
                    'HTTP Version', 'HTTP Status', 'Bytes', 'IPP Operation', 'IPP Status', 'Line', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            counts['files that could not be read'] += 1
            continue
        rows = access_rows(data, counts)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc('CUPS Access Log: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
