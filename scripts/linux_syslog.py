"""Read Linux syslog files (auth.log, secure) line by line as rsyslog writes them, and the same messages in the
systemd journal, for DLEAPP artifacts.

rsyslog writes a line as a time, the host name, the tag (a program name and an optional process
ID in brackets, then a colon) and the message. The time is RFC 3339 with a UTC offset in
RSYSLOG_FileFormat and a month, day and time with no year or zone in
RSYSLOG_TraditionalFileFormat. journald keeps the tag's name as SYSLOG_IDENTIFIER, its process ID as
SYSLOG_PID and the text after the tag as MESSAGE.
"""

import gzip
import os
import re
from datetime import datetime, timedelta, timezone

from scripts import systemd_journal

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


# The systemd journal.
JOURNAL_OTHER = 'entries of other programs'
JOURNAL_REPEATED = 'entries also in another journal file, reported once'
JOURNAL_UNKNOWN_FLAGS = 'journal files not read: their incompatible flags are unknown to the reader'
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def journal_time(microseconds):
    """A journal time as a datetime, or '' for 0 or a value past 9999."""
    if not microseconds or microseconds >= 253402300800000000:
        return ''
    return _EPOCH + timedelta(microseconds=microseconds)


def _text(value):
    return value.decode('utf-8', errors='backslashreplace') if value is not None else ''


def journal_entries(journals, accept, counts, pid_field='SYSLOG_PID'):
    """(time, host, program, process ID, message, boot ID, source) for each entry of these journal files whose
    SYSLOG_IDENTIFIER accept(program) takes, oldest first; journals: (relative path, JournalFile). The process ID is
    the pid_field field. The first value of a field an entry holds more than once is read, an entry that two files hold
    is read once, and entries of other programs are counted."""
    seen = set()
    rows = []
    for relative, journal in journals:
        if journal.unknown_incompatible:
            counts[JOURNAL_UNKNOWN_FLAGS] += 1
            continue
        for entry in journal.entries():
            fields = {}
            for name, value in entry.fields:
                fields.setdefault(name, value)
            program = _text(fields.get('SYSLOG_IDENTIFIER'))
            if not accept(program):
                counts[JOURNAL_OTHER] += 1
                continue
            message = _text(fields.get('MESSAGE'))
            # The same entry in two files keeps its sequence number; two entries of one file never share one, even
            # when their time and message are the same.
            key = (entry.seqnum, entry.boot_id, entry.monotonic, entry.realtime, program, message)
            if key in seen:
                counts[JOURNAL_REPEATED] += 1
                continue
            seen.add(key)
            rows.append(((entry.realtime, entry.boot_id, entry.monotonic, entry.seqnum),
                         (journal_time(entry.realtime), _text(fields.get('_HOSTNAME')), program,
                          _text(fields.get(pid_field)), message, entry.boot_id, relative)))
    rows.sort(key=lambda item: item[0])
    return [row for _key, row in rows]


def read_journals(context, counts):
    """(journals, staged) for the journal files an artifact found: journals as journal_entries takes them, and
    staged mapping each relative path to its staged path. Files that cannot be read are counted."""
    journals = []
    staged = {}
    for path in sorted(set(map(str, context.get_files_found()))):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        staged[relative] = path
        try:
            journals.append((relative, systemd_journal.read_journal(path)))
        except (OSError, systemd_journal.JournalError) as exc:
            counts[f'journal files not read ({type(exc).__name__})'] += 1
    return journals, staged


def journal_sources(rows, staged):
    """The staged paths of the files that gave these rows, whose last column is the relative path, in row order."""
    read = []
    for row in rows:
        if staged[row[-1]] not in read:
            read.append(staged[row[-1]])
    return '\n'.join(read)
