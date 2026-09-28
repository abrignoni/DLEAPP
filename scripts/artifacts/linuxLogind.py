"""Login sessions and power events systemd-logind logged in a Linux syslog file (auth.log or secure), for DLEAPP.

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
    "linuxLogindPower": {
        "name": "Power Events (logind)",
        "description": "Lines in which systemd-logind logged a shutdown, a warning of a shutdown or sleep, a dry run, "
                       "the blocking of logins, a cancelled shutdown or the start of a seat, from auth.log or secure and "
                       "their rotations.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "System (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line in which systemd-logind recorded a "
                 "shutdown, a warning of a shutdown or sleep, a dry run, the blocking of logins, a cancelled "
                 "shutdown or the start of a seat, in file order; Line is its line number in the file and Source "
                 "File the file, and the files that held a row are named in the report's located-at line. Other "
                 "lines, and lines in neither syslog file format described below, are counted in the run log and "
                 "not reported. Messages kept only in the systemd journal, or written to another file, are not "
                 "read. A line is read in either of rsyslog's two file formats, an RFC 3339 time with a UTC offset "
                 "(rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone. Hostname is the host name the line stores, and it "
                 "held the same value on every row of each tested image; Process ID is the process ID in the "
                 "line's tag, logind's own; and Message is the line's message as stored. systemd-logind logs to "
                 "the auth facility (systemd 259.5, src/login/logind.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind.c#L1350). "
                 "Event is shutdown for \"System is powering down.\", \"System is rebooting.\", \"System is halting.\", "
                 "\"System is rebooting with kexec.\", \"System userspace is rebooting.\", \"System is performing "
                 "factory reset.\" and \"System is shutting down.\", which in 259.5 are the messages of logind's "
                 "action table and the one its shutdown line falls back to (src/login/logind-action.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-action.c#L27-L132; "
                 "src/login/logind-dbus.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L1881-L1898), "
                 "written as logind starts a shutdown "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L2020-L2021) "
                 "and before a dry run line; a wall message set for the shutdown is in parentheses in the line and "
                 "is reported as Wall Message. Event is dry run for \"Running in dry run, suppressing action.\", "
                 "which logind writes after the shutdown line when a shutdown scheduled as a dry run reaches its "
                 "time, and then it starts no shutdown "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L2658-L2669): "
                 "a shutdown row directly followed by a dry run row with the same Process ID did not shut the "
                 "system down. Event is warning for \"The system will <action> at <time>!\" and \"The system will "
                 "<action> now!\" (src/login/logind-wall.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-wall.c#L54-L88), "
                 "with Scheduled For the time the line gives, or now. logind writes the now form when a shutdown "
                 "or sleep is asked for at once "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L2449-L2456 "
                 "and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-wall.c#L136-L141) "
                 "and the at form when one is scheduled with less than 15 minutes left and again at reminder times "
                 "before it "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-wall.c#L16-L33); "
                 "a now warning can also come when a scheduled time arrives, as on ubuntu2604_arm64_triage below. "
                 "Scheduled For is kept as written, logind's own local time with its zone's abbreviation when that "
                 "fits (src/basic/time-util.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/time-util.c#L311-L432), "
                 "and is not converted. While a wall message is set, logind writes it and the warning as two lines "
                 "of one message "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-wall.c#L63-L68), "
                 "log_struct passes the message on as written, one field to a line (src/basic/log.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/log.c#L965-L976), "
                 "and journald reads the second line as the name of a binary field (src/journal/journald-native.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-native.c#L189-L201); "
                 "on ubuntu2604_arm64_shutdown neither of the two shutdowns scheduled while a wall message was set "
                 "has a warning row. Event is logins blocked for \"Creating /run/nologin, blocking further "
                 "logins...\", which logind writes five minutes before a scheduled shutdown, or at once when less "
                 "time is left "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L2545-L2563); "
                 "shutdown cancelled for \"System shutdown has been cancelled\", which logind writes when a "
                 "scheduled shutdown is cancelled while wall messages are enabled "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-dbus.c#L2886-L2903); "
                 "and seat started for \"New seat <seat>.\" (src/login/logind-seat.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-seat.c#L594-L603), "
                 "which logind writes when it starts a seat: each seat it knows as it starts up "
                 "(src/login/logind.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind.c#L1291-L1293) "
                 "and a seat added later (src/login/logind-core.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/login/logind-core.c#L327-L328). "
                 "The releases checked, every one from v219 to v259, write the shutdown and seat started lines. "
                 "The logins blocked line is written from v220 "
                 "(https://github.com/systemd/systemd/blob/dde8bb32b12c855509777ce52ff59a835155ac78/src/login/logind-dbus.c#L1762; "
                 "v219's src/login/logind-dbus.c, "
                 "https://github.com/systemd/systemd/blob/a88abde72169ddc2df77df3fa5bed30725022253/src/login/logind-dbus.c, "
                 "has none); a wall message in the shutdown line from v225, after the final period in v225 and "
                 "v226, as in \"System is rebooting. (<message>)\" "
                 "(https://github.com/systemd/systemd/blob/e1439a1472c5f691733b8ef10e702beac2496a63/src/login/logind-dbus.c#L1368-L1369), "
                 "and before it from v227 "
                 "(https://github.com/systemd/systemd/blob/c379f143a5ccdbc94a87cfca0174e7f21fa05f26/src/login/logind-dbus.c#L1371-L1374), "
                 "while the line in v224 "
                 "(https://github.com/systemd/systemd/blob/b2a0ac5e5b29c73ca7c0da23369a4769d5a91ddd/src/login/logind-dbus.c) "
                 "has none; the dry run line from v227 "
                 "(https://github.com/systemd/systemd/blob/c379f143a5ccdbc94a87cfca0174e7f21fa05f26/src/login/logind-dbus.c#L1461; "
                 "v226, "
                 "https://github.com/systemd/systemd/blob/4211d5bd135ae4c43bd2012ae5f327b1cc1596c0/src/login/logind-dbus.c, "
                 "has none); and the warning and shutdown cancelled lines from v252 (src/login/logind-utmp.c, "
                 "https://github.com/systemd/systemd/blob/e8dc52766e1fdb4f8c09c3ab654d1270e1090c8d/src/login/logind-utmp.c#L90-L94; "
                 "src/login/logind-dbus.c, "
                 "https://github.com/systemd/systemd/blob/e8dc52766e1fdb4f8c09c3ab654d1270e1090c8d/src/login/logind-dbus.c#L2327-L2331). "
                 "v251 only sends the warning and the cancellation to terminals "
                 "(https://github.com/systemd/systemd/blob/b622e95f2f59fcb58e23ddafed745eee26a0f52f/src/login/logind-utmp.c#L61-L88; "
                 "https://github.com/systemd/systemd/blob/b622e95f2f59fcb58e23ddafed745eee26a0f52f/src/login/logind-dbus.c#L2360-L2361), "
                 "so on a release before v252 neither reaches the log. On ubuntu2604_arm64_triage, whose dpkg.log "
                 "records only systemd 259.5 builds, auth.log and its three rotations hold 24 of these lines: 8 "
                 "seat started, 7 shutdown (4 \"System is powering down.\" and 3 \"System is rebooting.\"), 5 warning "
                 "and 4 logins blocked, with Wall Message blank on every row, and Time (UTC) was filled on every "
                 "row. Each of the 7 shutdown rows comes within 0.2 seconds after a warning or logins blocked row "
                 "with the same Process ID, and 3 of the 4 \"System is powering down.\" rows have no warning row "
                 "with their Process ID. One warning line, stamped 2026-08-12T05:29:47.356153-07:00, has Scheduled "
                 "For \"Wed 2026-08-12 16:30:47 +04\", in a zone other than the line's, which is 12:30:47 UTC, and a "
                 "now warning and a shutdown row follow at 12:30:47 UTC. ubuntu2604_arm64_authlog, a later capture "
                 "of the same logs, holds the same 24 rows. ubuntu2604_arm64_shutdown, a later capture from the "
                 "same VM, holds those 24 and 9 rows from shutdown tests run on it that its corpus README lists: "
                 "two dry runs, each a shutdown row for a reboot with a dry run row of the same Process ID within "
                 "0.002 seconds after it and no now warning, in a boot that continued past them; one shutdown "
                 "cancelled; and, for the two shutdowns scheduled while a wall message was set, logins blocked "
                 "rows and no warning row. The journal boot list recorded with it names 8 boots: each of the 8 "
                 "seat started rows came 5 to 9 seconds after the first journal entry of one of them, and each of "
                 "the 7 that had ended has one shutdown row, 0 to 92 seconds before its last entry. On "
                 "honeynet_fc7_debian5 auth.log holds no systemd-logind line.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "power",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no systemd-logind line)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 24 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 33 rows",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 24 rows",
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
# The line logind writes as it starts a shutdown. From v227 a wall message set for it sits in parentheses before the
# final period; v225 and v226 put it after the period.
_SHUTDOWN = re.compile(r"(System is (?:powering down|rebooting|halting|rebooting with kexec|shutting down|"
                       r"performing factory reset)|System userspace is rebooting)(?: \((.*)\)\.|\.(?: \((.*)\))?)",
                       re.DOTALL)
_WARNING = re.compile(r"The system will (.+?) (?:at (.+)|now)!", re.DOTALL)
_SEAT = re.compile(r"New seat (\S+)\.")
_FIXED = {
    'Running in dry run, suppressing action.': 'dry run',
    'Creating /run/nologin, blocking further logins...': 'logins blocked',
    'System shutdown has been cancelled': 'shutdown cancelled',
}


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


def power_fields(message):
    """(event, scheduled for, wall message) from a systemd-logind power line, or None."""
    match = _SHUTDOWN.fullmatch(message)
    if match:
        return 'shutdown', '', match.group(2) or match.group(3) or ''
    match = _WARNING.fullmatch(message)
    if match:
        return 'warning', match.group(2) or 'now', ''
    if message in _FIXED:
        return _FIXED[message], '', ''
    if _SEAT.fullmatch(message):
        return 'seat started', '', ''
    return None


def power_rows(data, counts):
    """(time, time as recorded, host, process ID, event, scheduled for, wall message, message, line) for each
    systemd-logind power line of a syslog file; other lines are counted."""
    rows = []
    for number, when, stamp, host, _program, pid, message in program_lines(data, {_PROGRAM}, counts):
        fields = power_fields(message)
        if fields is None:
            counts['systemd-logind lines in other forms, not reported'] += 1
            continue
        rows.append((when, stamp, host, pid, *fields, message, number))
    return rows


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


@artifact_processor
def linuxLogindPower(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Process ID', 'Event',
                    'Scheduled For', 'Wall Message', 'Message', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = power_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Power Events (logind): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
