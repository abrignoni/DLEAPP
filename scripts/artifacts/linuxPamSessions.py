"""Sessions pam_unix logged opening and closing in a Linux syslog file (auth.log or secure), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxPamSessions": {
        "name": "PAM Sessions",
        "description": "Sessions the pam_unix module logged as opened or closed in auth.log or secure and their "
                       "rotations, for any service, with the service, user and login name the line gives.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line in which the pam_unix module recorded a "
                 "session being opened or closed, whatever program wrote it, in file order; Line is its line "
                 "number in the file and Source File the file, and the files that held a row are named in the "
                 "report's located-at line. Other lines, and lines in neither syslog file format described below, "
                 "are counted in the run log and not reported. Messages kept only in the systemd journal, or "
                 "written to another file, are not read. A line is read in either of rsyslog's two file formats, "
                 "an RFC 3339 time with a UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone, as on every row of honeynet_fc7_debian5. Hostname is "
                 "the host name the line stores, and it held the same value on every row of each tested image. "
                 "Program and Process ID are the program name and process ID in the line's tag. libpam writes a "
                 "module's message after '<module>(<service>:<function>): ' to the authpriv facility (Linux-PAM "
                 "1.7.0, libpam/pam_syslog.c, "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/libpam/pam_syslog.c#L79-L81 "
                 "and "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/libpam/pam_syslog.c#L97-L98, "
                 "and 1.0.1, "
                 "https://github.com/linux-pam/linux-pam/blob/186ff16e8d12ff15d518000c17f115ccab5275a4/libpam/pam_syslog.c#L81-L83 "
                 "and "
                 "https://github.com/linux-pam/linux-pam/blob/186ff16e8d12ff15d518000c17f115ccab5275a4/libpam/pam_syslog.c#L99-L100), "
                 "and Service is the service name there. pam_unix writes 'session opened for user "
                 "<user>(uid=<UID>) by <login name>(uid=<process UID>)' in 1.7.0 and 'session opened for user "
                 "<user> by <login name>(uid=<process UID>)' in 1.0.1, and 'session closed for user <user>' in "
                 "both (modules/pam_unix/pam_unix_sess.c at 1.7.0, "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L100 "
                 "and "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L129-L131, "
                 "and at 1.0.1, "
                 "https://github.com/linux-pam/linux-pam/blob/186ff16e8d12ff15d518000c17f115ccab5275a4/modules/pam_unix/pam_unix_sess.c#L95-L96 "
                 "and "
                 "https://github.com/linux-pam/linux-pam/blob/186ff16e8d12ff15d518000c17f115ccab5275a4/modules/pam_unix/pam_unix_sess.c#L125-L126). "
                 "Session Event is opened or closed, and User is the account the session is for. UID is that "
                 "account's user ID as 1.7.0 writes it, the words 'getpwnam error' when the account could not be "
                 "looked up "
                 "(https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L92-L99), "
                 "and is blank on 1.0.1's lines and on closed lines. Login Name is the login name libpam found, "
                 "blank when it found none "
                 "(https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L87-L90): "
                 "in 1.7.0 the name getlogin() gave the process (libpam/pam_modutil_getlogin.c, "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/libpam/pam_modutil_getlogin.c#L28), "
                 "and in 1.0.1 the user utmp held for the session's terminal "
                 "(https://github.com/linux-pam/linux-pam/blob/186ff16e8d12ff15d518000c17f115ccab5275a4/libpam/pam_modutil_getlogin.c#L32-L63). "
                 "Process UID is the real user ID of the process that opened the session, from getuid(). 1.7.0 "
                 "writes neither line when pam_unix is configured with its quiet option "
                 "(https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L91 "
                 "and "
                 "https://github.com/linux-pam/linux-pam/blob/ea980d991196df67cdd56b3f65d210b73218d08a/modules/pam_unix/pam_unix_sess.c#L129), "
                 "so a missing row is not evidence that no session was opened. On ubuntu2604_arm64_triage, whose "
                 "dpkg.log records libpam-modules 1.7.0, 1,370 of the 4,277 lines of auth.log and its three "
                 "rotations are pam_unix session lines: 418 opened and 417 closed for sshd, 156 and 156 for cron, "
                 "69 and 69 for sudo, 17 and 17 for su, 21 opened and 5 closed for systemd-user, 6 and 6 for "
                 "gdm-launch-environment, 5 opened and 4 closed for gdm-password, 2 opened for polkit-1, and 1 and "
                 "1 for login. UID was filled on all 695 opened rows, and Login Name was blank on 23 of them, the "
                 "17 for su and the 6 for gdm-launch-environment. Process ID was blank on 189 rows, those of the "
                 "programs, as Program gives them, that wrote no process ID: sudo, pkexec, gdm-password], "
                 "gdm-launch-environment], (systemd), (sd-pam) and (systemd-stdio-bridge). Each of the 590 closed "
                 "rows with a Process ID has an opened row of the same program and Process ID earlier in the same "
                 "file, and 590 of the 591 opened rows with a Process ID have such a closed row. "
                 "ubuntu2604_arm64_authlog, a later capture of the same logs, holds those 1,370 rows and 34 more, "
                 "17 opened and 17 closed for sshd and cron. On honeynet_fc7_debian5, whose /var/lib/dpkg/status "
                 "records libpam-modules 1.0.1-5+lenny1, 18 of the 105 lines are pam_unix session lines, 5 opened "
                 "and 5 closed for cron and 8 opened for login, and User held the same value, root, on every row. "
                 "Each of the 8 login rows has a wtmp USER_PROCESS record for root at the same second once its "
                 "time is read in Europe/Paris, the zone the image's /etc/timezone names, and Login Name was LOGIN "
                 "on 7 of them and blank on 1.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 18 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 1404 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1370 rows",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import read_file, reported_time, syslog_lines

# libpam prefixes a module's message with "<module>(<service>:<function>): ".
_SESSION = re.compile(r'pam_unix\(([^()]*):session\): session (opened|closed) for user (.*)', re.DOTALL)
# pam_unix's own forms after "session opened for user ": Linux-PAM 1.7.0 writes the user's UID after the
# name and 1.0.1 does not; both end with the login name and the process's user ID.
_OPENED_WITH_UID = re.compile(r'(.*?)\(uid=([^()]*)\) by (.*)\(uid=(\d+)\)', re.DOTALL)
_OPENED = re.compile(r'(.*) by (.*)\(uid=(\d+)\)', re.DOTALL)


def session_fields(message):
    """(service, event, user, UID, login name, process UID) from a pam_unix session line, or None."""
    match = _SESSION.fullmatch(message)
    if match is None:
        return None
    service, event, rest = match.groups()
    if event == 'closed':
        return service, event, rest, '', '', ''
    opened = _OPENED_WITH_UID.fullmatch(rest)
    if opened:
        return (service, event, *opened.groups())
    opened = _OPENED.fullmatch(rest)
    if opened:
        user, login, process_uid = opened.groups()
        return service, event, user, '', login, process_uid
    return None


def session_rows(data, counts):
    """(time, time as recorded, host, program, process ID, service, event, user, UID, login name, process UID,
    line) for each pam_unix session line of a syslog file; other lines are counted."""
    rows = []
    for number, stamp, host, program, pid, message in syslog_lines(data, counts):
        fields = session_fields(message)
        if fields is None:
            counts['pam_unix session lines in no known form, not reported' if _SESSION.fullmatch(message) else
                   'lines that are not pam_unix session lines, not reported'] += 1
            continue
        rows.append((reported_time(stamp, counts), stamp, host, program, pid, *fields, number))
    return rows


@artifact_processor
def linuxPamSessions(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'Process ID', 'Service',
                    'Session Event', 'User', 'UID', 'Login Name', 'Process UID', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = session_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('PAM Sessions: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
