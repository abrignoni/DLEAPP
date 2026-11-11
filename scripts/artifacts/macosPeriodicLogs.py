__artifacts_v2__ = {
    "macosDailyLogDiskStatus": {
        "name": "macOS Daily Log Disk Status",
        "description": "Lines of the Disk status section of each run in the periodic daily.out log on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Periodic Logs (macOS)",
        "notes": (
            'Reads the Disk status section of each run in private/var/log/daily.out. The section is the output '
            'of df: on the Magnet macOS 11.2.1 image /etc/periodic/daily/400.status-disks runs df with the '
            "flags in /etc/defaults/periodic.conf, which are -l -h there. The columns are df's own, as named on"
            ' its header line: Filesystem, Size, Used, Avail, Capacity, iused, ifree, %iused and Mounted on. A '
            'line is split on whitespace, with Mounted on kept whole from its leading slash. Inodes Used, '
            "Inodes Free and Inodes Used Percent are df's iused, ifree and %iused. A line that does not fit "
            'that layout, as other df flags would print, is shown whole in Filesystem with the other columns '
            'blank and the run log counts it; no line did on the tested images. Run Time (as stored) is the '
            'line that opens the run, written by the date command in /usr/sbin/periodic (read on the Magnet '
            'macOS 11.2.1 image): text with a zone abbreviation, not converted to UTC because the abbreviation '
            'alone does not fix an offset. A run line is recognised in the default English date layout only; '
            'other sections of the file are not read. The two macOS 11.2.1 images held 17 runs and 2 runs. Size'
            ' held one value on every row of each of them, Inodes Used Percent held one value on every row of '
            'each of them, and Avail held one value on every row of the Big Sur E01 image. When a logical '
            'extraction holds the same file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, '
            'a byte-identical copy is not read again and the run log counts it. When the views hold different '
            'bytes but give the same row, the row is reported once and Source File lists each file, one per '
            'line. '
        ),
        "paths": ('*/var/log/daily.out',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 116 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 10 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the one daily.out found holds no section)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no daily.out found)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no daily.out found)",
        },
    },
    "macosDailyLogNetworkStatus": {
        "name": "macOS Daily Log Network Interface Status",
        "description": "Lines of the Network interface status section of each run in the periodic daily.out log "
                       "on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Periodic Logs (macOS)",
        "notes": (
            'Reads the Network interface status section of each run in private/var/log/daily.out. The section '
            'is the output of netstat -i or netstat -in, per /etc/periodic/daily/420.status-network on the '
            "Magnet macOS 11.2.1 image. The columns are netstat's own: Name, Mtu, Network, Address, Ipkts, "
            'Ierrs, Opkts, Oerrs and Coll. netstat(1) says addresses can be truncated unless -W is given, and '
            'the script does not pass -W, so Network and Address values are as printed and can be cut short. A '
            'line is split on whitespace: the first two fields are Name and Mtu, the last five are the '
            'counters, and what stands between is Network and then Address, so Address is blank on a line that '
            'prints only one of the two. On the tested images every such line (111 and 8) held its one value '
            'under the Network heading. A line with fewer than seven fields or more than two between is shown '
            'whole in Name and the run log counts it; no line did on the tested images. Run Time (as stored) is'
            ' the line that opens the run, written by the date command in /usr/sbin/periodic (read on the '
            'Magnet macOS 11.2.1 image): text with a zone abbreviation, not converted to UTC because the '
            'abbreviation alone does not fix an offset. A run line is recognised in the default English date '
            'layout only; other sections of the file are not read. The two macOS 11.2.1 images held 17 runs and'
            ' 2 runs. Ierrs and Coll are identical on every row of both images, and Ierrs and Oerrs are '
            'identical and Oerrs and Coll are identical on every row of the Big Sur E01 image: each held 0 or a'
            ' dash there. When a logical extraction holds the same file under System/Volumes/Data/ or '
            'System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read again and the run log '
            'counts it. When the views hold different bytes but give the same row, the row is reported once and'
            ' Source File lists each file, one per line. '
        ),
        "paths": ('*/var/log/daily.out',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "share-2",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 482 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 22 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the one daily.out found holds no section)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no daily.out found)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no daily.out found)",
        },
    },
    "macosDailyLogSystemStatus": {
        "name": "macOS Daily Log System Status",
        "description": "Lines of the Local system status section of each run in the periodic daily.out log on "
                       "macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Periodic Logs (macOS)",
        "notes": (
            'Reads the Local system status section of each run in private/var/log/daily.out. The section is the'
            ' output of uptime, per /etc/periodic/daily/430.status-rwho on the Magnet macOS 11.2.1 image; when '
            '/var/rwho holds a file that script prints a Local network system status section from ruptime '
            'instead, which is not read. Line (as stored) is the whole line. Clock Time, Up, Users and Load '
            'Averages are its parts, which uptime(1) describes as the current time, the length of time the '
            'system has been up, the number of users and the load averages; they are blank when a line does not'
            ' have that form, which no line did on the tested images. Clock Time carries no date or zone. Run '
            'Time (as stored) is the line that opens the run, written by the date command in /usr/sbin/periodic'
            ' (read on the Magnet macOS 11.2.1 image): text with a zone abbreviation, not converted to UTC '
            'because the abbreviation alone does not fix an offset. A run line is recognised in the default '
            'English date layout only; other sections of the file are not read. The two macOS 11.2.1 images '
            'held 17 runs and 2 runs. When a logical extraction holds the same file under System/Volumes/Data/ '
            'or System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read again and the run log '
            'counts it. When the views hold different bytes but give the same row, the row is reported once and'
            ' Source File lists each file, one per line. '
        ),
        "paths": ('*/var/log/daily.out',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 17 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the one daily.out found holds no section)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no daily.out found)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no daily.out found)",
        },
    },
    "macosMonthlyLogLoginAccounting": {
        "name": "macOS Monthly Log Login Accounting",
        "description": "Lines of the login accounting section of each run in the periodic monthly.out log on "
                       "macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Periodic Logs (macOS)",
        "notes": (
            'Reads the Doing login accounting section of each run in private/var/log/monthly.out. The section '
            'is the output of ac -p, sorted, per /etc/periodic/monthly/200.accounting on the Magnet macOS '
            '11.2.1 image; ac(8) describes its figures as accumulated connect time in decimal hours and '
            'describes -p as displaying individual user totals. Each section on the tested image also held a '
            'line named total, which is kept as a row; ac(8) does not describe that line for -p. A line that is'
            ' not two fields is shown whole in Login Name; none was on the tested image. Run Time (as stored) '
            'is the line that opens the run, written by the date command in /usr/sbin/periodic (read on the '
            'Magnet macOS 11.2.1 image): text with a zone abbreviation, not converted to UTC because the '
            'abbreviation alone does not fix an offset. A run line is recognised in the default English date '
            'layout only; other sections of the file are not read. monthly.out was found only on the Magnet '
            'macOS 11.2.1 image: 2 runs with a section, 2 lines each. When a logical extraction holds the same '
            'file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy is '
            'not read again and the run log counts it. When the views hold different bytes but give the same '
            'row, the row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/var/log/monthly.out',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 4 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no monthly.out found)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no monthly.out found)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no monthly.out found)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no monthly.out found)",
        },
    },
}

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import fold_view_rows, unique_sources

# The line that opens a run, as date(1) prints it by default: Sun Feb 21 22:58:30 EST 2021
_RUN_LINE = re.compile(r'^[A-Z][a-z]{2} [A-Z][a-z]{2} [ \d]\d \d\d:\d\d:\d\d \S+ \d{4}$')
_END_LINE = re.compile(r'^-- End of \w+ output --$')
_DF_LINE = re.compile(r'^(\S.*?)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+%)\s+(\d+)\s+(\d+)\s+(\d+%)\s+(/.*)$')
_UPTIME_LINE = re.compile(r'^\s*(\S+)\s+up\s+(.*?),\s+(\d+) users?,\s+load averages?:\s+(.*?)\s*$')
_DISK = 'Disk status:'
_NETWORK = 'Network interface status:'
_SYSTEM = 'Local system status:'
_ACCOUNTING = 'Doing login accounting:'


def _sections(path, headings):
    """(run line, heading, [lines]) for each wanted section of each run in a periodic output file.

    A section starts at a line equal to one of headings and ends at the next empty line, the
    next run line or the end-of-output line.
    """
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        lines = handle.read().split('\n')
    run, heading, body = '', None, []
    for line in lines:
        line = line.rstrip('\r')
        is_run = bool(_RUN_LINE.match(line))
        if heading is not None and (not line.strip() or is_run or _END_LINE.match(line)):
            yield run, heading, body
            heading, body = None, []
        if is_run:
            run = line
        elif line in headings:
            heading, body = line, []
        elif heading is not None:
            body.append(line)
    if heading is not None:
        yield run, heading, body


def _read(context, name, headings, label):
    """(relative path, run line, heading, lines) per section, and the files read."""
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == name]
    paths, _skipped = unique_sources(context, found, label=label)
    sections = []
    for path in paths:
        relative = context.get_relative_path(path)
        for run, heading, body in _sections(path, headings):
            sections.append((relative, run, heading, body))
    return sections, paths


@artifact_processor
def macosDailyLogDiskStatus(context):
    data_headers = ('Run Time (as stored)', 'Filesystem', 'Size', 'Used', 'Avail', 'Capacity', 'Inodes Used',
                    'Inodes Free',
                    'Inodes Used Percent', 'Mounted On', 'Source File')
    sections, paths = _read(context, 'daily.out', (_DISK,), 'macOS Daily Log Disk Status')
    rows, unparsed = [], 0
    for relative, run, _heading, body in sections:
        for line in body:
            if line.startswith('Filesystem'):
                continue
            match = _DF_LINE.match(line)
            if match:
                rows.append((run,) + match.groups() + (relative,))
            else:
                unparsed += 1
                rows.append((run, line, '', '', '', '', '', '', '', '', relative))
    if unparsed:
        logfunc(f'macOS Daily Log Disk Status: {unparsed} line(s) not split into columns, shown whole in Filesystem')
    return data_headers, fold_view_rows(rows), '\n'.join(paths)


@artifact_processor
def macosDailyLogNetworkStatus(context):
    data_headers = ('Run Time (as stored)', 'Name', 'Mtu', 'Network', 'Address', 'Ipkts', 'Ierrs', 'Opkts', 'Oerrs',
                    'Coll', 'Source File')
    sections, paths = _read(context, 'daily.out', (_NETWORK,), 'macOS Daily Log Network Interface Status')
    rows, unparsed = [], 0
    for relative, run, _heading, body in sections:
        for line in body:
            fields = line.split()
            if fields[:2] == ['Name', 'Mtu']:
                continue
            middle = fields[2:-5]
            if len(fields) < 7 or len(middle) > 2:
                unparsed += 1
                rows.append((run, line, '', '', '', '', '', '', '', '', relative))
                continue
            network = middle[0] if middle else ''
            address = middle[1] if len(middle) > 1 else ''
            rows.append((run, fields[0], fields[1], network, address) + tuple(fields[-5:]) + (relative,))
    if unparsed:
        logfunc(f'macOS Daily Log Network Interface Status: {unparsed} line(s) not split into columns, shown whole '
                'in Name')
    return data_headers, fold_view_rows(rows), '\n'.join(paths)


@artifact_processor
def macosDailyLogSystemStatus(context):
    data_headers = ('Run Time (as stored)', 'Clock Time', 'Up', 'Users', 'Load Averages', 'Line (as stored)',
                    'Source File')
    sections, paths = _read(context, 'daily.out', (_SYSTEM,), 'macOS Daily Log System Status')
    rows = []
    for relative, run, _heading, body in sections:
        for line in body:
            match = _UPTIME_LINE.match(line)
            parts = match.groups() if match else ('', '', '', '')
            rows.append((run,) + parts + (line.strip(), relative))
    return data_headers, fold_view_rows(rows), '\n'.join(paths)


@artifact_processor
def macosMonthlyLogLoginAccounting(context):
    data_headers = ('Run Time (as stored)', 'Login Name', 'Connect Time (hours)', 'Source File')
    sections, paths = _read(context, 'monthly.out', (_ACCOUNTING,), 'macOS Monthly Log Login Accounting')
    rows = []
    for relative, run, _heading, body in sections:
        for line in body:
            fields = line.split()
            if len(fields) == 2:
                rows.append((run, fields[0], fields[1], relative))
            else:
                rows.append((run, line.strip(), '', relative))
    return data_headers, fold_view_rows(rows), '\n'.join(paths)
