"""Switches of user that su logged in a Linux syslog file (auth.log or secure) and in the systemd journal, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxSu": {
        "name": "User Switches (su)",
        "description": "User switches that util-linux su logged in auth.log, secure or messages and their "
                       "rotations, with whether "
                       "they succeeded, the users on both sides and the terminal.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and /var/log/messages and "
                 "their numbered or dated "
                 "rotations, gzip ones included, and reports each line in which util-linux's su recorded a switch "
                 "of user, in file order; Line is its line number in the file and Source File the file, and the "
                 "files that held a row are named in the report's located-at line. Other lines, among them the PAM "
                 "lines su's modules write (PAM Sessions reports the session ones), and lines in neither syslog "
                 "file format described below, are counted in the run log and not reported. User Switches (su, "
                 "journal) reports the switches kept only in the systemd journal, and messages written to another "
                 "file are not read. A line is read in either of "
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
                 "so it is blank on lines from older releases, unless rsyslog took the line from the journal with "
                 "imjournal set to UsePid \"system\", which puts the process ID the journal recorded for the sender "
                 "in the tag (rsyslog 8.2510.0, plugins/imjournal/imjournal.c, "
                 "https://github.com/rsyslog/rsyslog/blob/4c8fa9960ca5d417c938b7394acba17e0f8e4196/plugins/imjournal/imjournal.c#L500-L537 "
                 "and "
                 "https://github.com/rsyslog/rsyslog/blob/4c8fa9960ca5d417c938b7394acba17e0f8e4196/plugins/imjournal/imjournal.c#L874-L876), "
                 "as the rsyslog.conf of rocky98_arm64_known sets. util-linux's su writes \"(to <user>) <user> on "
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
                 "are counted, not reported; no tested image holds such a line. The "
                 "rsyslog.conf of rocky98_arm64_known (Rocky Linux 9.8, util-linux 2.37.4) sends authpriv to "
                 "secure and every other facility at info or above, apart from mail and cron, to messages, and "
                 "there messages holds 1 row, the known su run as root to dleappk1, succeeded, From User root, To "
                 "User dleappk1 and Terminal pts/1, with the process ID of the pam_unix su-l session lines in "
                 "secure; its Time (UTC) is blank because the line stores no year and no zone. On "
                 "ubuntu2604_arm64_triage, whose "
                 "dpkg.log records only util-linux 2.41.3 builds, auth.log and its three rotations hold 18 of "
                 "these lines, 17 succeeded and 1 failed; From User held root, To User one user and Terminal none "
                 "on every row. Each succeeded row has a pam_unix session opened line from the same su process in "
                 "the same file, 0.001 to 0.14 seconds after it. The failed row has none, and just before it, in "
                 "the same second, the file holds pam_unix's line that the user's password had expired and "
                 "pam_pwquality's line that the password change was aborted. ubuntu2604_arm64_authlog and "
                 "ubuntu2604_arm64_shutdown, later captures of the same logs, hold the same 18 rows. On "
                 "honeynet_fc7_debian5 auth.log holds no su line.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*',
                  '*/var/log/messages', '*/var/log/messages[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no su line)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 1 rows",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 18 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxSuJournal": {
        "name": "User Switches (su, journal)",
        "description": "User switches that util-linux su logged in the systemd journal, with whether they "
                       "succeeded, the users on both sides, the terminal and the boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "One row per entry in the systemd journal files under var/log/journal and run/log/journal whose "
                 "SYSLOG_IDENTIFIER is su and whose MESSAGE is a switch of user in the form User Switches (su) "
                 "describes, read with the same reader as systemd Journal (scripts/systemd_journal.py) and in the "
                 "way Cron Log (journal) reads its entries: journald keeps the name in a syslog line's tag as "
                 "SYSLOG_IDENTIFIER, the process ID in its brackets as SYSLOG_PID and the text after the tag as "
                 "MESSAGE (Reference: systemd, 'journald-syslog.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L204-L262, "
                 "with the fields written at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L433-L464), "
                 "the first value of a field an entry holds more than once is read, an entry that more than one "
                 "file holds is read once, and rows are in order of Time (UTC), then boot ID, time since boot and "
                 "sequence number. Result, From User, To User and Terminal have the meanings and references given "
                 "for User Switches (su) and are read from MESSAGE; Process ID is SYSLOG_PID, which su adds from "
                 "util-linux 2.38 as described there, and it equals the journal's own _PID field on every row of "
                 "the tested images. Time (UTC) is the entry's realtime, the time journald received it (Reference: "
                 "systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651); "
                 "Hostname is the entry's _HOSTNAME field, Boot ID the boot the entry names and Source File the "
                 "journal file the entry was read from. Entries of other programs, the name being compared "
                 "exactly, su entries in other forms, entries read a second time, and journal files that could not "
                 "be read or whose header sets an incompatible flag the reader does not know are counted in the "
                 "run log and not reported. On each of the three tested images holding journal files the 38 su "
                 "entries in other forms were lines of su's PAM modules: 18 session opened and 18 session closed "
                 "lines, 1 about an expired password and 1 about an aborted password change; their SYSLOG_FACILITY "
                 "is 10 and that of every reported entry is 4. ubuntu2604_arm64_journal, ubuntu2604_arm64_usb and "
                 "ubuntu2604_arm64_usbstorage, captures of the same VM, hold the same 19 rows from 7 boots, 18 "
                 "succeeded and 1 failed, and From User, To User, Terminal and Hostname each held one value on "
                 "every row. Four captures of that VM's auth.log were compared with this artifact, matching rows "
                 "on Process ID, Result, From User, To User and Terminal with times less than 1 s apart: every one "
                 "of the 18 User Switches (su) rows of ubuntu2604_arm64_authlog and of ubuntu2604_arm64_triage was "
                 "matched by a row of ubuntu2604_arm64_journal, those of ubuntu2604_arm64_shutdown by rows of "
                 "ubuntu2604_arm64_usbstorage and those of ubuntu2604_arm64_cron by rows of ubuntu2604_arm64_usb. "
                 "The remaining row of each journal is later than the last su line of all four auth.log captures. "
                 "On every matched row Time (UTC) here was earlier than the auth.log line's, by 0.000008 to "
                 "0.00026 s. No tested image held an entry in two files, and the unit tests exercise it. No member "
                 "of the other 28 tested images matches the declared paths.",
        "paths": ('*/var/log/journal/*.journal', '*/var/log/journal/*.journal~', '*/run/log/journal/*.journal',
                  '*/run/log/journal/*.journal~'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 19 rows",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 19 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 19 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import journal_entries, journal_sources, program_lines, read_file, read_journals

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


def journal_switch_rows(journals, counts):
    """(time, host, process ID, result, from, to, terminal, boot ID, source) for each su switch entry in these journal
    files, oldest first; journals: (relative path, JournalFile). An entry two files hold is read once."""
    rows = []
    for when, host, _program, pid, message, boot, relative in journal_entries(
            journals, lambda program: program == _PROGRAM, counts):
        fields = switch_fields(message)
        if fields is None:
            counts['su entries in other forms, not reported'] += 1
            continue
        rows.append((when, host, pid, *fields, boot, relative))
    return rows


@artifact_processor
def linuxSuJournal(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Hostname', 'Process ID', 'Result', 'From User', 'To User', 'Terminal',
                    'Boot ID', 'Source File')
    counts = Counter()
    journals, staged = read_journals(context, counts)
    data_list = journal_switch_rows(journals, counts)
    if counts:
        logfunc('User Switches (su, journal): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, journal_sources(data_list, staged)
