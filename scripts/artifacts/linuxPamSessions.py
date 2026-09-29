"""Sessions pam_unix logged opening and closing in a Linux syslog file (auth.log or secure) and in the systemd journal,
for DLEAPP.

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
                 "are counted in the run log and not reported. PAM Sessions (journal) reports the session lines "
                 "kept only in the systemd journal, and messages written to another file are not read. A line is "
                 "read in either of rsyslog's two file formats, "
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
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 1404 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 1494 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 1454 rows",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1370 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxPamSessionsJournal": {
        "name": "PAM Sessions (journal)",
        "description": "Sessions pam_unix logged opening and closing in the systemd journal, whatever program sent "
                       "the entry, with the service, user and IDs the entry gives and the boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "One row per entry in the systemd journal files under var/log/journal and run/log/journal whose "
                 "MESSAGE is a pam_unix session line in a form PAM Sessions describes, whatever its "
                 "SYSLOG_IDENTIFIER, read with the same reader as systemd Journal (scripts/systemd_journal.py) and "
                 "in the way Cron Log (journal) reads its entries: journald keeps the name in a syslog line's tag "
                 "as SYSLOG_IDENTIFIER, the process ID in its brackets as SYSLOG_PID and the text after the tag as "
                 "MESSAGE (Reference: systemd, 'journald-syslog.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L204-L262, "
                 "with the fields written at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L433-L464), "
                 "the first value of a field an entry holds more than once is read, an entry that more than one "
                 "file holds is read once, and rows are in order of Time (UTC), then boot ID, time since boot and "
                 "sequence number. Program is SYSLOG_IDENTIFIER and Process ID SYSLOG_PID, blank for an entry that "
                 "carries none, as those of the programs PAM Sessions names as writing no process ID do; Service, "
                 "Session Event, User, UID, Login Name and Process UID have the meanings and references given for "
                 "PAM Sessions and are read from MESSAGE. Time (UTC) is the entry's realtime, the time journald "
                 "received it (Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651); "
                 "Hostname is the entry's _HOSTNAME field, Boot ID the boot the entry names and Source File the "
                 "journal file the entry was read from. Entries that are not pam_unix session lines, pam_unix "
                 "session entries in no known form, entries read a second time, and journal files that could not "
                 "be read or whose header sets an incompatible flag the reader does not know are counted in the "
                 "run log and not reported. ubuntu2604_arm64_journal holds 1,579 rows (798 opened and 781 closed), "
                 "ubuntu2604_arm64_usb 1,693 and ubuntu2604_arm64_usbstorage 2,527, from 8 boots and 10 programs "
                 "on each; Process ID is blank on 192, 192 and 194 of them, and Hostname held one value on every "
                 "row of each tested image. Four captures of auth.log from the VM these three journals come from "
                 "were compared with this artifact, matching rows on Program, Process ID, Service, Session Event, "
                 "User, UID, Login Name and Process UID with times less than 1 s apart: every one of the 1,404 PAM "
                 "Sessions rows of ubuntu2604_arm64_authlog and the 1,370 of ubuntu2604_arm64_triage was matched "
                 "by a row of ubuntu2604_arm64_journal, the 1,454 of ubuntu2604_arm64_shutdown by rows of "
                 "ubuntu2604_arm64_usbstorage and the 1,494 of ubuntu2604_arm64_cron by rows of "
                 "ubuntu2604_arm64_usb. Between each capture's first and last session line the journal holds 3 "
                 "rows with no auth.log line, all logged after systemd's Stopped rsyslog.service entry and before "
                 "its next Starting rsyslog.service entry; the other journal rows with no match are later than the "
                 "capture's last session line. On every matched row Time (UTC) here was earlier than the auth.log "
                 "line's, by 0.000003 to 0.0079 s. No tested image held an entry in two files, and the unit tests "
                 "exercise it. No member of the other 28 tested images matches the declared paths.",
        "paths": ('*/var/log/journal/*.journal', '*/var/log/journal/*.journal~', '*/run/log/journal/*.journal',
                  '*/run/log/journal/*.journal~'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
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
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 1579 rows",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 1693 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 2527 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import journal_entries, journal_sources, read_file, read_journals, reported_time, syslog_lines

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


def journal_session_rows(journals, counts):
    """(time, host, program, process ID, service, event, user, UID, login name, process UID, boot ID, source) for each
    pam_unix session entry in these journal files, whatever program sent it, oldest first."""
    rows = []
    for when, host, program, pid, message, boot, relative in journal_entries(journals, lambda program: True, counts):
        fields = session_fields(message)
        if fields is None:
            counts['pam_unix session entries in no known form, not reported' if _SESSION.fullmatch(message) else
                   'entries that are not pam_unix session lines, not reported'] += 1
            continue
        rows.append((when, host, program, pid, *fields, boot, relative))
    return rows


@artifact_processor
def linuxPamSessionsJournal(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'Process ID', 'Service', 'Session Event', 'User',
                    'UID', 'Login Name', 'Process UID', 'Boot ID', 'Source File')
    counts = Counter()
    journals, staged = read_journals(context, counts)
    data_list = journal_session_rows(journals, counts)
    if counts:
        logfunc('PAM Sessions (journal): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, journal_sources(data_list, staged)
