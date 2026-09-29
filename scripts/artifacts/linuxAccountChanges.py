"""Account and group changes the shadow tools logged to a Linux syslog file (auth.log or secure) and to the systemd
journal, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxAccountChanges": {
        "name": "Account Changes",
        "description": "Lines useradd, usermod, passwd and the other shadow tools that change accounts and groups logged "
                       "to auth.log or secure and their rotations, with any account, group and caller the message names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Accounts (Linux)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line whose program is one of the shadow tools "
                 "that add, change or remove accounts and groups (useradd, userdel, usermod, groupadd, groupdel, "
                 "groupmod, passwd, chpasswd, chgpasswd, chage, gpasswd, chfn, chsh, newusers and groupmems), in "
                 "file order; Line is its line number in the file and Source File the file, and the files that "
                 "held a row are named in the report's located-at line. Lines of other programs, and lines in "
                 "neither syslog file format described below, are counted in the run log and not reported. Unless "
                 "built otherwise, these tools log to the authpriv facility with their process ID (shadow 4.17.4, "
                 "lib/defines.h, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/lib/defines.h#L117-L126, "
                 "and 4.1.1, "
                 "https://github.com/shadow-maint/shadow/blob/4e7aac1962e6fb40370549de7c0ad9ca49f49a2a/lib/defines.h#L175-L184). "
                 "honeynet_fc7_debian5's /etc/rsyslog.conf routes the auth and authpriv facilities to auth.log, "
                 "and both tested Linux images, one Debian and one Ubuntu, hold the tools' lines there. Fedora "
                 "writes the authpriv facility to secure (rsyslog.conf, "
                 "https://src.fedoraproject.org/rpms/rsyslog/blob/6acade802d1e5b33cb723af1761371f9a3a656bb/f/rsyslog.conf#_52); "
                 "no tested image carries a secure file. Account Changes (journal) reports the messages kept only "
                 "in the systemd journal, and messages written to another file are not read. A line is read in "
                 "either of rsyslog's two file formats, an RFC 3339 "
                 "time with a UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone, as on every row of honeynet_fc7_debian5. Hostname is "
                 "the host name the line stores, and it held the same value on every row of each tested image. "
                 "Program and Process ID are the program name and process ID in the line's tag, so the lines one "
                 "run of a tool wrote share a Process ID. Message is the message as stored. Account, Group and Run "
                 "By are split out of a message in one of the forms these tools pass to syslog that name an "
                 "account or a group, taken from the source of shadow 4.17.4 "
                 "(https://github.com/shadow-maint/shadow/tree/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8) and 4.1.1 "
                 "(https://github.com/shadow-maint/shadow/tree/4e7aac1962e6fb40370549de7c0ad9ca49f49a2a): 104 "
                 "forms from the tools and from the shared code that reports a change that failed "
                 "(lib/cleanup_user.c and lib/cleanup_group.c), 4.1.1 putting a name in `quotes' and 4.17.4 in "
                 "'quotes'. Account is the account the message names, for a rename the name before it; Group is "
                 "the group it names; Run By is the account passwd or gpasswd names as having run it, the login "
                 "name when that account has the process's real user ID and otherwise the account that does "
                 "(passwd.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/passwd.c#L904-L913 "
                 "and "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/passwd.c#L1117, "
                 "gpasswd.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/gpasswd.c#L906-L915, "
                 "and lib/myname.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/lib/myname.c#L25-L52, "
                 "which 4.1.1's libmisc/myname.c matches, "
                 "https://github.com/shadow-maint/shadow/blob/4e7aac1962e6fb40370549de7c0ad9ca49f49a2a/libmisc/myname.c#L18-L38). "
                 "For groupmod's 'group changed in <file> (<change>)' and the failure line 'failed to change "
                 "<file> (<change>)', Group is the name that begins the change, which groupmod writes as 'group "
                 "<name>/<GID>', or 'group <name>' for gshadow (groupmod.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/groupmod.c#L608-L613). "
                 "useradd 4.17.4 ends 'new user' with from= and the terminal on its standard input, or none when "
                 "it had none (useradd.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/useradd.c#L2104-L2109), "
                 "and 4.1.1 writes no from= "
                 "(https://github.com/shadow-maint/shadow/blob/4e7aac1962e6fb40370549de7c0ad9ca49f49a2a/src/useradd.c#L1418-L1421). "
                 "The one form 'failed to prepare the new <file> entry '<name>'' names a user when useradd writes "
                 "it and a group when usermod does (useradd.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/useradd.c#L1029, "
                 "and usermod.c, "
                 "https://github.com/shadow-maint/shadow/blob/b23a5823bc2433ac3dc8cbc20fd1d3798ee801b8/src/usermod.c#L808), "
                 "and is read that way. Messages in no such form, including PAM's lines, useradd's defaults and "
                 "those naming only a file or a user ID, leave the three columns blank. No tested file held a line "
                 "of groupdel, groupmod, chpasswd, chgpasswd, gpasswd, chfn, chsh, newusers or groupmems, so the "
                 "forms of those tools are exercised only by lines written in the form their source gives. A row "
                 "reports what a tool logged, and /etc/passwd need not agree with these lines: on "
                 "ubuntu2604_arm64_triage one of the 3 accounts userdel deleted, a system account, is in that "
                 "image's /etc/passwd, and no line in these files records it being added back. On "
                 "ubuntu2604_arm64_triage, whose dpkg.log records passwd 1:4.17.4-2ubuntu3, 49 of the 4,277 lines "
                 "of auth.log and its three rotations are these tools': 27 from groupadd, 11 useradd, 5 userdel, 4 "
                 "passwd and 2 usermod, with 28 distinct pairs of program and Process ID, each of the 9 groupadd "
                 "pairs holding 3 lines. The 11 accounts useradd created are all in the image's /etc/passwd with "
                 "the UID, GID, home and shell the line gives, and each line reads from=none; the 9 groups the "
                 "'new group' lines name are all in /etc/group with the GID the line gives. Account was filled on "
                 "22 rows, Group on 31 and Run By on 3, root on all 3, each for another account's password. "
                 "ubuntu2604_arm64_authlog holds the same 49 rows. On honeynet_fc7_debian5, whose "
                 "/var/lib/dpkg/status records passwd 1:4.1.1-6+lenny1, 3 of the 105 lines are these tools', one "
                 "each from useradd, usermod and chage. Account held the same value on all 3 rows, the account the "
                 "useradd line creates, which is in the image's /etc/passwd with the UID, GID, home and shell the "
                 "line gives, and Group and Run By were blank on every row.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user-plus",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 3 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxAccountChangesJournal": {
        "name": "Account Changes (journal)",
        "description": "Messages the shadow account tools logged to the systemd journal, with the account, group "
                       "and calling user a known message names, and the boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Accounts (Linux)",
        "notes": "One row per entry in the systemd journal files under var/log/journal and run/log/journal whose "
                 "SYSLOG_IDENTIFIER is one of the program names Account Changes reads, read with the same reader "
                 "as systemd Journal (scripts/systemd_journal.py) and in the way Cron Log (journal) reads its "
                 "entries: journald keeps the name in a syslog line's tag as SYSLOG_IDENTIFIER, the process ID in "
                 "its brackets as SYSLOG_PID and the text after the tag as MESSAGE (Reference: systemd, "
                 "'journald-syslog.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L204-L262, "
                 "with the fields written at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L433-L464), "
                 "the first value of a field an entry holds more than once is read, an entry that more than one "
                 "file holds is read once, and rows are in order of Time (UTC), then boot ID, time since boot and "
                 "sequence number. Program is SYSLOG_IDENTIFIER, Process ID SYSLOG_PID and Message MESSAGE, and "
                 "Account, Group and Run By are read from Message as Account Changes reads them, with the meanings "
                 "and references given there. journald removes whitespace at the end of a message a program sends "
                 "to the syslog socket and keeps the message as received in SYSLOG_RAW when it removed any "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L372-L397 "
                 "and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L470-L484): "
                 "on each tested image 5 userdel entries had a line feed at the end of the message removed this "
                 "way, and their Message equals the matching auth.log line's. Time (UTC) is the entry's realtime, "
                 "the time journald received it (Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651); "
                 "Hostname is the entry's _HOSTNAME field, Boot ID the boot the entry names and Source File the "
                 "journal file the entry was read from. Entries of other programs, entries read a second time, and "
                 "journal files that could not be read or whose header sets an incompatible flag the reader does "
                 "not know are counted in the run log and not reported. ubuntu2604_arm64_journal and "
                 "ubuntu2604_arm64_usb hold the same 49 rows, from 3 boots, and ubuntu2604_arm64_usbstorage 61, "
                 "from 4 boots; every row names an account, a group or a calling user, and Hostname held one value "
                 "on every row of each tested image. Four captures of auth.log from the VM these three journals "
                 "come from were compared with this artifact, matching rows on Program, Process ID, Message, "
                 "Account, Group and Run By with times less than 1 s apart: every one of the 49 Account Changes "
                 "rows of ubuntu2604_arm64_authlog and of ubuntu2604_arm64_triage was matched by a row of "
                 "ubuntu2604_arm64_journal, those of ubuntu2604_arm64_shutdown by rows of "
                 "ubuntu2604_arm64_usbstorage and those of ubuntu2604_arm64_cron by rows of ubuntu2604_arm64_usb. "
                 "The 12 other rows of ubuntu2604_arm64_usbstorage are later than the last Account Changes row of "
                 "ubuntu2604_arm64_shutdown. On every matched row Time (UTC) here was "
                 "earlier than the auth.log line's, by 0.000004 to 0.37 s. No tested image held an entry in two "
                 "files, and the unit tests exercise it. No member of the other 28 tested images matches the "
                 "declared paths.",
        "paths": ('*/var/log/journal/*.journal', '*/var/log/journal/*.journal~', '*/run/log/journal/*.journal',
                  '*/run/log/journal/*.journal~'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user-plus",
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
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 49 rows",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 61 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import journal_entries, journal_sources, program_lines, read_file, read_journals

# The shadow programs that add, remove or change accounts and groups, as their lines are tagged.
_PROGRAMS = ('useradd', 'userdel', 'usermod', 'groupadd', 'groupdel', 'groupmod', 'passwd', 'chpasswd',
             'chgpasswd', 'chage', 'gpasswd', 'chfn', 'chsh', 'newusers', 'groupmems')

# The formats those programs pass to syslog that name an account or a group, as written in the
# source of shadow 4.17.4 (a name in 'quotes') and 4.1.1 (a name in `quotes'), each with one
# letter per placeholder: A fills Account, G fills Group, B fills Run By and - fills nothing. X is
# groupmod's description of a change, which begins "group <name>", followed by "/<GID>" except
# in the gshadow one; its name fills Group.
_FORMATS = (
    # useradd
    ("new user: name=%s, UID=%u, GID=%u, home=%s, shell=%s, from=%s", 'A-----'),
    ("new user: name=%s, UID=%u, GID=%u, home=%s, shell=%s", 'A----'),
    ("new group: name=%s, GID=%u", 'G-'),
    ("add '%s' to group '%s'", 'AG'),
    ("add '%s' to shadow group '%s'", 'AG'),
    ("add `%s' to group `%s'", 'AG'),
    ("add `%s' to shadow group `%s'", 'AG'),
    ("failed adding user '%s', exit code: %d", 'A-'),
    ("failed adding user `%s', data deleted", 'A'),
    ('failed to reset the tallylog entry of user "%s"', 'A'),
    # userdel
    ("delete '%s' from group '%s'\n", 'AG'),
    ("delete '%s' from shadow group '%s'\n", 'AG'),
    ("delete `%s' from group `%s'\n", 'AG'),
    ("delete `%s' from shadow group `%s'\n", 'AG'),
    ("removed group '%s' owned by '%s'\n", 'GA'),
    ("removed shadow group '%s' owned by '%s'\n", 'GA'),
    ("removed group `%s' owned by `%s'\n", 'GA'),
    ("delete user '%s'\n", 'A'),
    ("delete user `%s'\n", 'A'),
    # usermod
    ("lock user '%s' password", 'A'),
    ("unlock user '%s' password", 'A'),
    ("change user '%s' password", 'A'),
    ("lock user `%s' password", 'A'),
    ("unlock user `%s' password", 'A'),
    ("change user `%s' password", 'A'),
    ("change user name '%s' to '%s'", 'A-'),
    ("change user name `%s' to `%s'", 'A-'),
    ("change user '%s' UID from '%d' to '%d'", 'A--'),
    ("change user '%s' GID from '%d' to '%d'", 'A--'),
    ("change user '%s' home from '%s' to '%s'", 'A--'),
    ("change user '%s' shell from '%s' to '%s'", 'A--'),
    ("change user '%s' inactive from '%ld' to '%ld'", 'A--'),
    ("change user '%s' expiration from '%s' to '%s'", 'A--'),
    ("change user `%s' UID from `%d' to `%d'", 'A--'),
    ("change user `%s' GID from `%d' to `%d'", 'A--'),
    ("change user `%s' home from `%s' to `%s'", 'A--'),
    ("change user `%s' shell from `%s' to `%s'", 'A--'),
    ("change user `%s' inactive from `%ld' to `%ld'", 'A--'),
    ("change user `%s' expiration from `%s' to `%s'", 'A--'),
    ("change '%s' to '%s' in group '%s'", 'A-G'),
    ("change '%s' to '%s' in shadow group '%s'", 'A-G'),
    ("change admin '%s' to '%s' in shadow group '%s'", 'A-G'),
    ("change `%s' to `%s' in group `%s'", 'A-G'),
    ("change `%s' to `%s' in shadow group `%s'", 'A-G'),
    ("change admin `%s' to `%s' in shadow group `%s'", 'A-G'),
    ("delete '%s' from group '%s'", 'AG'),
    ("delete '%s' from shadow group '%s'", 'AG'),
    ("delete `%s' from group `%s'", 'AG'),
    ("delete `%s' from shadow group `%s'", 'AG'),
    ("failed to prepare the new %s entry '%s'", '-G'),
    # groupadd
    ("group added to %s: name=%s, GID=%u", '-G-'),
    ("group added to %s: name=%s", '-G'),
    # groupdel
    ("group '%s' removed from %s", 'G-'),
    ("group '%s' removed\n", 'G'),
    ("remove group `%s'\n", 'G'),
    # groupmod
    ("change group `%s' to `%s'", 'G-'),
    ("change GID for `%s' to %u", 'G-'),
    ("group changed in %s (%s)", '-X'),
    # passwd
    ("Failed to crypt password with previous salt of user '%s'", 'A'),
    ("incorrect password for %s", 'A'),
    ("password locked for '%s'", 'A'),
    ("password locked for `%s'", 'A'),
    ("now < minimum age for '%s'", 'A'),
    ("now < minimum age for `%s'", 'A'),
    ("root is not authorized by SELinux to change the password of %s", 'A'),
    ("can't view or modify password information for %s", 'A'),
    ("%s: can't view or modify password information for %s", '-A'),
    ("password for '%s' changed by '%s'", 'AB'),
    ("password for `%s' changed by `%s'", 'AB'),
    # chage
    ("changed password expiry for %s", 'A'),
    # gpasswd
    ("user %s added by %s to group %s%s", 'ABG-'),
    ("user %s removed by %s from group %s%s", 'ABG-'),
    ("password of group %s removed by %s%s", 'GB-'),
    ("access to group %s restricted by %s%s", 'GB-'),
    ("administrators of group %s set by %s to %s%s", 'GB--'),
    ("members of group %s set by %s to %s%s", 'GB--'),
    ("password of group %s changed by %s%s", 'GB-'),
    ("%s failed to add user %s to group %s%s", 'BAG-'),
    ("%s failed to remove user %s from group %s%s", 'BAG-'),
    ("%s failed to remove password of group %s%s", 'BG-'),
    ("%s failed to restrict access to group %s%s", 'BG-'),
    ("%s failed to set the administrators of group %s to %s%s", 'BG--'),
    ("%s failed to set the members of group %s to %s%s", 'BG--'),
    ("%s failed to change password of group %s%s", 'BG-'),
    ("change the password for group %s by %s", 'GB'),
    ("remove password from group %s by %s", 'GB'),
    ("restrict access to group %s by %s", 'GB'),
    ("add member %s to group %s by %s", 'AGB'),
    ("remove member %s from group %s by %s", 'AGB'),
    ("set administrators of %s to %s", 'G-'),
    ("set members of %s to %s", 'G-'),
    # chfn and chsh
    ("changed user '%s' information", 'A'),
    ("changed user `%s' information", 'A'),
    ("changed user '%s' shell to '%s'", 'A-'),
    ("changed user `%s' shell to `%s'", 'A-'),
    ("can't change shell for '%s'", 'A'),
    ("can't change shell for `%s'", 'A'),
    # the shared cleanup code the programs above run when a change fails
    ("failed to add user %s", 'A'),
    ("failed to add user %s to %s", 'A-'),
    ("failed to add group %s", 'G'),
    ("failed to remove group %s", 'G'),
    ("failed to add group %s to %s", 'G-'),
    ("failed to remove group %s from %s", 'G-'),
    ("failed to change %s (%s)", '-X'),
)


def _pattern(fmt, roles):
    """A regular expression that matches a message written with fmt, one group per placeholder."""
    trailing_newline = fmt.endswith('\n')
    fmt = fmt.rstrip('\n')
    parts = re.split(r'(%l?[sdu])', fmt)
    placeholders = parts[1::2]
    if len(placeholders) != len(roles):
        raise ValueError(f'{fmt!r}: {len(placeholders)} placeholders, {len(roles)} roles')
    out = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            out.append(re.escape(part))
            continue
        role = roles[index // 2]
        if part != '%s':
            out.append(r'(-?\d+)')
        elif role in 'AGB':
            out.append(r'(\S+)')
        else:
            out.append('(.*?)')
    # A trailing line feed may be dropped, kept, or escaped as #012 by the syslog daemon.
    return re.compile(''.join(out) + (r'(?:\n|#012)?' if trailing_newline else ''), re.DOTALL)


# The one form whose name is a user when useradd writes it and a group when usermod does.
_ROLES_BY_PROGRAM = {("failed to prepare the new %s entry '%s'", 'useradd'): '-A'}
_DESCRIBED_GROUP = re.compile(r'group ([^/,\s]+)')
_COMPILED = tuple((fmt, _pattern(fmt, roles), roles) for fmt, roles in _FORMATS)


def named(message, program=''):
    """(account, group, run by) that a known shadow format names in a message program wrote, blank where it
    names none."""
    for fmt, pattern, roles in _COMPILED:
        match = pattern.fullmatch(message)
        if match:
            roles = _ROLES_BY_PROGRAM.get((fmt, program), roles)
            found = {'A': '', 'G': '', 'B': ''}
            for role, value in zip(roles, match.groups()):
                if role in found:
                    found[role] = value
                elif role == 'X':
                    described = _DESCRIBED_GROUP.match(value)
                    found['G'] = described.group(1) if described else ''
            return found['A'], found['G'], found['B']
    return '', '', ''


@artifact_processor
def linuxAccountChanges(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'Process ID', 'Message',
                    'Account', 'Group', 'Run By', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        lines = program_lines(data, _PROGRAMS, problems)
        relative = context.get_relative_path(path)
        for number, when, stamp, host, program, pid, message in lines:
            data_list.append((when, stamp, host, program, pid, message, *named(message, program), number, relative))
        if lines:
            read.append(path)
    if problems:
        logfunc('Account Changes: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def journal_change_rows(journals, counts):
    """(time, host, program, process ID, message, account, group, run by, boot ID, source) for each entry of these
    journal files from the programs Account Changes reads, oldest first."""
    return [(when, host, program, pid, message, *named(message, program), boot, relative)
            for when, host, program, pid, message, boot, relative in journal_entries(
                journals, lambda program: program in _PROGRAMS, counts)]


@artifact_processor
def linuxAccountChangesJournal(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'Process ID', 'Message', 'Account', 'Group',
                    'Run By', 'Boot ID', 'Source File')
    counts = Counter()
    journals, staged = read_journals(context, counts)
    data_list = journal_change_rows(journals, counts)
    if counts:
        logfunc('Account Changes (journal): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, journal_sources(data_list, staged)
