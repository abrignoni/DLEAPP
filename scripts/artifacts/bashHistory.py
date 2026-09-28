"""Commands bash saved in each account's .bash_history, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "bashHistory": {
        "name": "Bash History",
        "description": "Commands saved in .bash_history files, one row per command line, with the time stamp readline "
                       "wrote before them where the file has one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Command Line (bash)",
        "notes": "Reads each .bash_history the paths match, one row per line in file order "
                 "that is not a time stamp, with the line's number in the file. Readline "
                 "8.3, the history library in bash 5.3, stamps each entry it adds "
                 "(https://git.savannah.gnu.org/cgit/bash.git/tree/lib/readline/history.c?id=b8c60bc9ca365f8261fa97900b6fa939f6ebc303#n428, "
                 "line 428) with the history comment character followed by a count of "
                 "seconds "
                 "(https://git.savannah.gnu.org/cgit/bash.git/tree/lib/readline/history.c?id=b8c60bc9ca365f8261fa97900b6fa939f6ebc303#n322, "
                 "lines 322 to 337), and writes that stamp on a line of its own before the "
                 "entry only when bash is saving time stamps "
                 "(https://git.savannah.gnu.org/cgit/bash.git/tree/lib/readline/histfile.c?id=b8c60bc9ca365f8261fa97900b6fa939f6ebc303#n862, "
                 "lines 862 to 870), which bash does when the HISTTIMEFORMAT variable is "
                 "set, taking # as the comment character when none has been set "
                 "(https://git.savannah.gnu.org/cgit/bash.git/tree/variables.c?id=b8c60bc9ca365f8261fa97900b6fa939f6ebc303#n6168, "
                 "lines 6168 to 6178). A line that is # followed only by digits is read as "
                 "a stamp; a stamp written with another comment character is reported as a "
                 "command. Time (UTC) is a stamp's count read as seconds since 1970-01-01 "
                 "UTC, given to every line after it up to the next stamp, so a command "
                 "that spans several lines is several rows with one time, and lines with "
                 "no stamp before them, which is every line of a file bash wrote without "
                 "stamps, have no time. Command is the line as stored, read as UTF-8 (a "
                 "byte that is not valid UTF-8 shows as the replacement character); empty "
                 "lines are counted in the run log and not reported. Source File names the "
                 "file each row came from, since the paths can match more than one file, one in each home folder. "
                 "On ubuntu2604_arm64_triage the file held 26 lines, 4 of them stamps: the "
                 "4 commands after them are those of the known session run with "
                 "HISTTIMEFORMAT set, and every stamp reads 2026-09-28 06:45:30 UTC, the "
                 "second auth.log in the same image records for that session's login, "
                 "while the 6 commands of the earlier known session, run without it, have "
                 "no time. On pc_mus_001_win11 a .bash_history in a Windows user profile "
                 "folder held 383 lines and no stamp: 368 rows, Time (UTC) blank on all of them, and 15 empty lines. "
                 "On the public MacBook Pro logical extraction root's .bash_history, in private/var/root and "
                 "System/Volumes/Data/private/var/root, held one line each and no stamp. On honeynet_fc7_debian5 "
                 "root's .bash_history held 57 lines and no stamp: 57 rows, Time (UTC) blank on all of them.",
        "paths": ('*/.bash_history',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 57 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 368 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 22 rows",
        },
    },
}

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

# readline writes a stamp as the history comment character and a count of seconds on a line of its own.
_STAMP = re.compile(r'#(\d+)')
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _lines(data):
    lines = [line.rstrip('\r') for line in data.decode('utf-8', errors='replace').split('\n')]
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def _time(seconds):
    try:
        return _EPOCH + timedelta(seconds=seconds)
    except OverflowError:
        return ''


def history_rows(data, counts):
    """(command, time, line number) for each line of a .bash_history that is not a time stamp;
    a stamp dates every line after it up to the next one."""
    rows, when = [], ''
    for number, line in enumerate(_lines(data), 1):
        if not line:
            counts['empty lines, not reported'] += 1
            continue
        stamp = _STAMP.fullmatch(line)
        if stamp:
            when = _time(int(stamp.group(1)))
            continue
        rows.append((line, when, number))
    return rows


@artifact_processor
def bashHistory(context):
    data_headers = ('Command', ('Time (UTC)', 'datetime'), 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = history_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Bash History: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
