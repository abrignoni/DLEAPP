"""Switches of user that su logged in a Linux syslog file (auth.log or secure), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxSu": {
        "name": "User Switches (su)",
        "description": "User switches that util-linux su logged in auth.log or secure and their rotations, with whether "
                       "they succeeded, the users on both sides and the terminal.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line in which util-linux's su recorded a switch "
                 "of user, in file order; Line is its line number in the file and Source File the file, and the "
                 "files that held a row are named in the report's located-at line. Other lines, among them the PAM "
                 "lines su's modules write (PAM Sessions reports the session ones), and lines in neither syslog "
                 "file format described below, are counted in the run log and not reported. Messages kept only in "
                 "the systemd journal, or written to another file, are not read. A line is read in either of "
                 "rsyslog's two file formats, an RFC 3339 time with a UTC offset (rsyslog 8.2512.0, "
                 "tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone. Hostname is the host name the line stores, and it "
                 "held the same value on every row of each tested image; Process ID is the process ID in the "
                 "line's tag, which su adds from util-linux 2.38 "
                 "(https://github.com/util-linux/util-linux/blob/1f5129b79ad232c79ecbac31998e96c20ff4c90c/login-utils/su-common.c#L291; "
                 "2.37 opens the log without it, "
                 "https://github.com/util-linux/util-linux/blob/50736e4998fde0fff9b7876476137a21b85bd5a6/login-utils/su-common.c#L286), "
                 "so it is blank on lines from older releases. util-linux's su writes \"(to <user>) <user> on "
                 "<terminal>\" to the auth facility under the name su, with \"FAILED SU \" in front when a PAM step "
                 "failed (util-linux 2.41.3, login-utils/su-common.c, "
                 "https://github.com/util-linux/util-linux/blob/5305e6c70b274f679329b79c0e1ef5a07e9dc1a6/login-utils/su-common.c#L287-L298), "
                 "after PAM authentication and the account checks, a required password change among them, or after "
                 "the first of them that failed "
                 "(https://github.com/util-linux/util-linux/blob/5305e6c70b274f679329b79c0e1ef5a07e9dc1a6/login-utils/su-common.c#L417-L438); "
                 "every release checked from 2.22 to 2.41.3 (2.22, 2.23, 2.24, 2.25, 2.27, 2.29 to 2.41 and "
                 "2.41.3) writes the same line (2.22, login-utils/su.c, "
                 "https://github.com/util-linux/util-linux/blob/58e6e67ad5c90cb3119700ff813883b91dca9350/login-utils/su.c#L141-L145). "
                 "Result is succeeded for the plain line and failed for FAILED SU. To User is the user su switched "
                 "to; From User is the user who ran su, in 2.41.3 the name of its real user ID (lib/pwdutils.c, "
                 "https://github.com/util-linux/util-linux/blob/5305e6c70b274f679329b79c0e1ef5a07e9dc1a6/lib/pwdutils.c#L103-L128), "
                 "blank when that has none; and Terminal is the terminal as su names it, or none when it had none. "
                 "Lines named runuser, and the lines the su in shadow's tools writes, \"Successful su for <user> by "
                 "<user>\" and \"FAILED su for <user> by <user>\" (shadow 4.17.4, lib/sulog.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/lib/sulog.c#L34-L40) "
                 "and \"+ <terminal> <user>:<user>\" and \"- <terminal> <user>:<user>\" (src/su.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/su.c#L204-L209 "
                 "and "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/su.c#L1088-L1092), "
                 "are counted, not reported; no tested image holds such a line. On ubuntu2604_arm64_triage, whose "
                 "dpkg.log records only util-linux 2.41.3 builds, auth.log and its three rotations hold 18 of "
                 "these lines, 17 succeeded and 1 failed; From User held root, To User one user and Terminal none "
                 "on every row. Each succeeded row has a pam_unix session opened line from the same su process in "
                 "the same file, 0.001 to 0.14 seconds after it. The failed row has none, and just before it, in "
                 "the same second, the file holds pam_unix's line that the user's password had expired and "
                 "pam_pwquality's line that the password change was aborted. ubuntu2604_arm64_authlog and "
                 "ubuntu2604_arm64_shutdown, later captures of the same logs, hold the same 18 rows. On "
                 "honeynet_fc7_debian5 auth.log holds no su line.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no su line)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 18 rows",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import program_lines, read_file

_PROGRAM = 'su'
# util-linux su: "[FAILED SU ](to <user switched to>) <user who ran su> on <terminal, or none>".
_SWITCH = re.compile(r"(FAILED SU )?\(to ([^)]*)\) (\S*) on (\S+)")


def switch_fields(message):
    """(result, from user, to user, terminal) from a su line, or None."""
    match = _SWITCH.fullmatch(message)
    if not match:
        return None
    failed, to_user, from_user, terminal = match.groups()
    return ('failed' if failed else 'succeeded'), from_user, to_user, terminal


def switch_rows(data, counts):
    """(time, time as recorded, host, process ID, result, from, to, terminal, line) for each su switch line of a
    syslog file; other lines are counted."""
    rows = []
    for number, when, stamp, host, _program, pid, message in program_lines(data, {_PROGRAM}, counts):
        fields = switch_fields(message)
        if fields is None:
            counts['su lines in other forms, not reported'] += 1
            continue
        rows.append((when, stamp, host, pid, *fields, number))
    return rows


@artifact_processor
def linuxSu(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Process ID', 'Result', 'From User',
                    'To User', 'Terminal', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = switch_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('User Switches (su): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
