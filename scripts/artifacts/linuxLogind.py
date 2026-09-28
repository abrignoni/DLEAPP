"""Login sessions systemd-logind logged in a Linux syslog file (auth.log or secure), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxLogindSessions": {
        "name": "Login Sessions (logind)",
        "description": "Login sessions systemd-logind logged as created, logged out or removed in auth.log or secure and "
                       "their rotations, with the session ID, user, class and type the line gives.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line in which systemd-logind recorded a login "
                 "session being created, logged out or removed, in file order; Line is its line number in the file "
                 "and Source File the file, and the files that held a row are named in the report's located-at "
                 "line. Other lines, and lines in neither syslog file format described below, are counted in the "
                 "run log and not reported. Messages kept only in the systemd journal, or written to another file, "
                 "are not read. A line is read in either of rsyslog's two file formats, an RFC 3339 time with a "
                 "UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone. Hostname is the host name the line stores, and it "
                 "held the same value on every row of each tested image; Process ID is the process ID in the "
                 "line's tag, logind's own. systemd-logind logs to the auth facility (systemd 259.5, "
                 "src/login/logind.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind.c#L1350). "
                 "From v258 it writes \"New session '<ID>' of user '<user>' with class '<class>' and type "
                 "'<type>'.\" (src/login/logind-session.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L837-L848); "
                 "in the releases checked from v219 to v257 (v219, v229, v237, v238, v239, v245, v247, v249, v252, "
                 "v255, v256 and v257) it writes \"New session <ID> of user <user>.\" "
                 "(https://github.com/systemd/systemd/blob/a88abde72169ddc2df77df3fa5bed30725022253/src/login/logind-session.c#L556-L561 "
                 "at v219 and "
                 "https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/login/logind-session.c#L854-L859 "
                 "at v257), with no class or type, and Class and Type are then blank. From v239 it writes \"Session "
                 "<ID> logged out. Waiting for processes to exit.\" "
                 "(https://github.com/systemd/systemd/blob/de7436b02badc82200dc127ff190b8155769b8e7/src/login/logind-session.c#L671-L678; "
                 "v238's src/login/logind-session.c, "
                 "https://github.com/systemd/systemd/blob/738ab7502afb7663d9aacdd73e79025aa7cd0a9b/src/login/logind-session.c, "
                 "has no such line) when a session ends and logind does not stop the processes left in it "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L896-L918), "
                 "and it writes \"Removed session <ID>.\" when a session that had started is removed "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L967-L973). "
                 "Session Event is new, logged out or removed from those three forms, and systemd-logind lines in "
                 "any other form are counted in the run log and not reported. In 259.5 all three lines of a "
                 "session of class background are logged at debug level "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L837, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L914 "
                 "and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L968), "
                 "which systemd does not write unless its log level is raised (src/basic/log.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/log.c#L46), "
                 "and pam_systemd gives that class to a session whose PAM terminal is cron "
                 "(src/login/pam_systemd.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/pam_systemd.c#L944-L952), "
                 "so at the default level such sessions have no rows. Session is the session ID: the kernel audit "
                 "session ID of the session's leader process when it has one that no current session uses, and "
                 "otherwise c followed by logind's own counter (src/login/logind-dbus.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L850-L876). "
                 "User is the user name, and Class and Type are logind's names for the session's class and type "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-session.c#L1616-L1640). "
                 "On ubuntu2604_arm64_triage, whose dpkg.log records only systemd 259.5 builds, 1,305 of the 4,277 "
                 "lines of auth.log and its three rotations are these lines: 450 new, 423 logged out and 432 "
                 "removed. The 450 new rows are 418 of class user and type tty, 5 of class user and type wayland, "
                 "6 of class greeter and type wayland, and 15 of class manager and 6 of class manager-early, both "
                 "of type unspecified, and each has a pam_unix session opened line within one second: from sshd "
                 "for the 418, gdm-password for the 5, gdm-launch-environment for the 6 greeter rows and "
                 "systemd-user for the 21 manager and manager-early rows. Time (UTC) was filled on every row. IDs "
                 "are reused: 106 session IDs began sessions under more than one logind Process ID, and 23 are on "
                 "more than one new row of the same file. Each of the 855 logged out and removed rows has the same "
                 "Process ID as the latest new row with its ID before it, so pair them by ID within one Process "
                 "ID. ubuntu2604_arm64_authlog, a later capture of the same logs, holds those 1,305 rows and 39 "
                 "more, 13 each of new (class user, type tty), logged out and removed. On honeynet_fc7_debian5 "
                 "auth.log holds no systemd-logind line.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no systemd-logind line)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 1344 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1305 rows",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import program_lines, read_file

_PROGRAM = 'systemd-logind'
# systemd v258 and later name the session's class and type.
_NEW_WITH_CLASS = re.compile(r"New session '([^']*)' of user '(.*)' with class '([^']*)' and type '([^']*)'\.",
                             re.DOTALL)
# The releases before v258 write the ID and the user unquoted.
_NEW = re.compile(r"New session ([^\s']+) of user (.*)\.", re.DOTALL)
_LOGGED_OUT = re.compile(r"Session (\S+) logged out\. Waiting for processes to exit\.")
_REMOVED = re.compile(r"Removed session (\S+)\.")


def session_fields(message):
    """(event, session, user, class, type) from a systemd-logind session line, or None."""
    match = _NEW_WITH_CLASS.fullmatch(message)
    if match:
        return ('new', *match.groups())
    match = _NEW.fullmatch(message)
    if match:
        return 'new', match.group(1), match.group(2), '', ''
    match = _LOGGED_OUT.fullmatch(message)
    if match:
        return 'logged out', match.group(1), '', '', ''
    match = _REMOVED.fullmatch(message)
    if match:
        return 'removed', match.group(1), '', '', ''
    return None


def session_rows(data, counts):
    """(time, time as recorded, host, process ID, event, session, user, class, type, line) for each
    systemd-logind session line of a syslog file; other lines are counted."""
    rows = []
    for number, when, stamp, host, _program, pid, message in program_lines(data, {_PROGRAM}, counts):
        fields = session_fields(message)
        if fields is None:
            counts['systemd-logind lines in other forms, not reported'] += 1
            continue
        rows.append((when, stamp, host, pid, *fields, number))
    return rows


@artifact_processor
def linuxLogindSessions(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Process ID', 'Session Event',
                    'Session', 'User', 'Class', 'Type', 'Line', 'Source File')
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
        logfunc('Login Sessions (logind): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
