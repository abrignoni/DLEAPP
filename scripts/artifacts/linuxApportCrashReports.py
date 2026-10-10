"""Crash reports Apport writes to /var/crash on Ubuntu, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxApportCrashReports": {
        "name": "Apport Crash Reports",
        "description": "Problem reports Apport wrote to /var/crash, one row per report: the report's date, the "
                       "program that crashed with its command line and working directory, the signal, the package "
                       "and the system it ran on.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Logs (Linux)",
        "notes": "Reads the problem reports Apport writes to its report folder, /var/crash unless the "
                 "APPORT_REPORT_DIR environment variable names another (Reference: Apport 2.34.1, commit "
                 "dd6b78e17c2e6940387bc46419d6486887237430, 'apport/fileutils.py' line 35, "
                 "https://github.com/canonical/apport). A report is a text file of fields: a field starts on a line "
                 "that does not begin with a space, its key ends at the first colon, the lines after it that begin "
                 "with a space continue its value, and a value given as base64 is compressed binary data "
                 "('problem_report.py' lines 58 to 91, 151 to 163 and 185 to 212). One row is reported per file. "
                 "Date (System Local Time) is the Date field, the local time of the system when the report was "
                 "created, written without a time zone (lines 428 to 436); it is shown as year-month-day and is not "
                 "converted, because the report does not hold the zone. Problem Type is the ProblemType field. "
                 "Executable Path is the program, read from the process's exe link ('data/apport' lines 1052 to "
                 "1054). Command Line is ProcCmdline, the process's command line with a backslash doubled, a space "
                 "inside an argument written as backslash space and the arguments separated by spaces, and Working "
                 "Directory is ProcCwd, the process's current directory ('apport/report.py' lines 820 to 826 and 838 "
                 "to 844). Signal and Signal Name are the number and name of the signal that ended the process "
                 "('data/apport' lines 976 to 979). Package and Source Package are the package that owns the "
                 "executable, with its version, and its source package, and Distro Release, Architecture and Kernel "
                 "are the DistroRelease, Architecture and Uname fields ('apport/report.py' lines 506 to 532 and 612 "
                 "to 628). User ID (File Name) is the number in the file name, which Apport forms as the executable "
                 "path with slashes as underscores, or the package name, then a user ID and .crash "
                 "('apport/fileutils.py' lines 418 to 438). Executable Modified (UTC) is ExecutableTimestamp, the "
                 "modified time of the executable in whole seconds when the report was made ('apport/report.py' "
                 "lines 862 to 869). Core Dump is Yes when the report holds a CoreDump field, whose data is not "
                 "decoded here, and Other Fields names the fields the row does not show, such as the process's "
                 "environment, memory map and open files; their values are in the file. A line that starts no field "
                 "is skipped with its continuation lines and counted in the run log, where Apport refuses the file; "
                 "a file with no field is counted and not reported. Apport does not write a report for every crash: "
                 "among other cases it ignores an executable that is not likely to belong to a package "
                 "('data/apport' lines 1130 to 1139), so the absence of a report is not evidence that a program did "
                 "not crash. The reader was compared with Apport's own on the lab VM: for the two known reports the "
                 "21 text fields of each and the one binary field are those Apport's ProblemReport.load returns, and "
                 "for 300 reports written by Apport's own writer from generated values the 1,297 text fields and 88 "
                 "binary fields are the same. On ubuntu2604_arm64_apport, from a VM running Apport 2.34.1 with its "
                 "clock on America/New_York time, the 2 rows are a sleep 31337 process ended with SIGSEGV (Signal "
                 "11) and a yes dleapp_known_crash process ended with SIGABRT (Signal 6), both run from the folder "
                 "made for the test: each Date is one second after the second the signal was sent, read in that "
                 "zone, the User ID is 1000, the real user ID in the report's ProcStatus field, and both reports "
                 "hold a core dump. The VM's five earlier reports belong to root or system accounts, could not be "
                 "read by the unprivileged capture and are not in the sample. Not exercised: a package installation "
                 "failure, a kernel report, a Python traceback report, and the .upload and .uploaded marker files, "
                 "which are not read.",
        "paths": ("*/var/crash/*.crash",),
        "output_types": "standard",
        "artifact_icon": "alert-octagon",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_apport": "Ubuntu 26.04 LTS aarch64, Apport 2.34.1 | 2 rows",
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

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
# the fields a row shows, in column order after the date
SHOWN = ('ProblemType', 'ExecutablePath', 'ProcCmdline', 'Signal', 'SignalName', 'Package', 'SourcePackage',
         'ProcCwd', 'DistroRelease', 'Architecture', 'Uname')
ASCTIME = re.compile(r'[A-Z][a-z]{2} ([A-Z][a-z]{2}) ([ 0-9][0-9]) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([0-9]{4})\Z')
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
WHOLE = re.compile(r'[0-9]+\Z')


def _joined(parts):
    """The text of a value from the rest of its first line and its continuation lines, joined as Apport joins
    them: a line feed goes before a continuation line only once the value has some content."""
    value = parts[0].strip()
    for part in parts[1:]:
        value += (b'\n' if value else b'') + part
    return value.decode('utf-8', 'backslashreplace')


def report_fields(data):
    """({key: text value}, [keys whose value is base64 data], lines skipped) for the bytes of a report, read as
    Apport reads it: an entry starts on a line that does not begin with a space, its key ends at the first colon,
    and the lines after it that begin with a space continue its value. A line that should start an entry and has
    no colon is skipped with its continuation lines and counted; Apport refuses such a file."""
    fields, binary, skipped = {}, [], 0
    key, parts, skipping = None, [], True
    for line in data.split(b'\n'):
        if line.startswith(b' '):
            if not skipping:
                parts.append(line[1:])
            continue
        if key is not None and not skipping:
            fields[key] = _joined(parts)
        key, parts, skipping = None, [], True
        if not line:
            continue
        name, colon, value = line.partition(b':')
        if not colon:
            skipped += 1
            continue
        key = name.decode('ascii', 'backslashreplace')
        if value.strip() == b'base64':
            binary.append(key)
        else:
            parts, skipping = [value], False
    if key is not None and not skipping:
        fields[key] = _joined(parts)
    return fields, binary, skipped


def report_date(text):
    """A date in the form C's asctime writes, as YYYY-MM-DD HH:MM:SS; any other text as it is."""
    match = ASCTIME.match(text)
    if not match or match.group(1) not in MONTHS:
        return text
    month, day, hour, minute, second, year = match.groups()
    return f'{year}-{MONTHS.index(month) + 1:02d}-{int(day):02d} {hour}:{minute}:{second}'


def file_user(name):
    """The number between the last two dots of a report's file name, <subject>.<number>.crash, or ''."""
    parts = name.rsplit('.', 2)
    return parts[1] if len(parts) == 3 and WHOLE.match(parts[1]) else ''


def executable_time(text):
    """The UTC time of a whole count of seconds since 1970, or '' for anything else."""
    if not WHOLE.match(text):
        return ''
    try:
        return EPOCH + timedelta(seconds=int(text))
    except OverflowError:
        return ''


@artifact_processor
def linuxApportCrashReports(context):
    data_headers = ('Date (System Local Time)', 'Problem Type', 'Executable Path', 'Command Line', 'Signal',
                    'Signal Name', 'Package', 'Source Package', 'Working Directory', 'Distro Release',
                    'Architecture', 'Kernel', 'User ID (File Name)', ('Executable Modified (UTC)', 'datetime'),
                    'Core Dump', 'Other Fields', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        fields, binary, skipped = report_fields(data)
        problems['lines that start no field, skipped'] += skipped
        if not fields and not binary:
            problems['files that hold no field, not reported'] += 1
            continue
        others = sorted(key for key in list(fields) + binary
                        if key not in SHOWN + ('Date', 'ExecutableTimestamp', 'CoreDump'))
        data_list.append((report_date(fields.get('Date', '')),) + tuple(fields.get(key, '') for key in SHOWN)
                         + (file_user(os.path.basename(path)), executable_time(fields.get('ExecutableTimestamp', '')),
                            'Yes' if 'CoreDump' in binary or 'CoreDump' in fields else 'No', ', '.join(others),
                            context.get_relative_path(path)))
        read.append(path)
    problems = +problems
    if problems:
        logfunc('Apport Crash Reports: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
