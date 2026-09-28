"""Read Linux syslog files (auth.log, secure) line by line as rsyslog writes them, for DLEAPP artifacts.

rsyslog writes a line as a time, the host name, the tag (a program name and an optional process
ID in brackets, then a colon) and the message. The time is RFC 3339 with a UTC offset in
RSYSLOG_FileFormat and a month, day and time with no year or zone in
RSYSLOG_TraditionalFileFormat.
"""

import gzip
import re
from datetime import datetime, timedelta, timezone

RFC3339 = re.compile(r'(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,6}))?(Z|[+-]\d\d:\d\d)')
_TRADITIONAL = r'[A-Z][a-z]{2} [ \d]\d \d\d:\d\d:\d\d'
LINE = re.compile(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)|' + _TRADITIONAL + r')'
                  r' (\S+) ([^\s\[:]+)(?:\[(\d+)\])?: ?(.*)', re.DOTALL)
NOT_SYSLOG = 'lines in neither syslog file format, not reported'
OTHER_PROGRAMS = 'lines from other programs, not reported'
BAD_DATE = 'RFC 3339 times that are not a calendar date, Time (UTC) left blank'


def read_file(path):
    """The bytes of a syslog file, decompressed when its name ends in .gz."""
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as handle:
        return handle.read()


def utc_time(stamp):
    """The UTC time of an RFC 3339 stamp, or '' for one with no year and no zone."""
    match = RFC3339.fullmatch(stamp)
    if not match:
        return ''
    year, month, day, hour, minute, second, fraction, offset = match.groups()
    if offset == 'Z':
        zone = timezone.utc
    else:
        delta = timedelta(hours=int(offset[1:3]), minutes=int(offset[4:6]))
        zone = timezone(-delta if offset[0] == '-' else delta)
    try:
        local = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                         int((fraction or '0').ljust(6, '0')), tzinfo=zone)
    except ValueError:
        return ''
    return local.astimezone(timezone.utc)


def syslog_lines(data, counts):
    """(line number, time as recorded, host, program, process ID, message) for each line in either
    format; lines in neither format are counted."""
    rows = []
    for number, line in enumerate(data.decode('utf-8', errors='replace').split('\n'), 1):
        line = line.rstrip('\r')
        if not line:
            continue
        match = LINE.fullmatch(line)
        if not match:
            counts[NOT_SYSLOG] += 1
            continue
        stamp, host, program, pid, message = match.groups()
        rows.append((number, stamp, host, program, pid or '', message))
    return rows


def reported_time(stamp, counts):
    """utc_time(stamp) for a line that will be reported, counting an RFC 3339 time that is not a date."""
    when = utc_time(stamp)
    if when == '' and RFC3339.fullmatch(stamp):
        counts[BAD_DATE] += 1
    return when


def program_lines(data, programs, counts):
    """(line number, UTC time, time as recorded, host, program, process ID, message) for each line
    of these programs; lines of other programs and lines in neither format are counted."""
    rows = []
    for number, stamp, host, program, pid, message in syslog_lines(data, counts):
        if program not in programs:
            counts[OTHER_PROGRAMS] += 1
            continue
        rows.append((number, reported_time(stamp, counts), stamp, host, program, pid, message))
    return rows
