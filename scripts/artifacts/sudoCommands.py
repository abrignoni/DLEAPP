"""Commands sudo logged to a Linux syslog file (auth.log or secure) and to the systemd journal, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sudoCommands": {
        "name": "sudo Commands",
        "description": "Commands sudo logged to auth.log or secure and their rotations, with the user who ran sudo and, "
                       "where the line records them, the reason for a refusal, the terminal, the working directory, the "
                       "user and group the command was to run as, and the command line.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Command Line (sudo)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, named in the report's located-at line, and reports each command "
                 "sudo logged there, in file order; Line is the line's number in the file, or the first and last "
                 "numbers when sudo wrote the command over several lines, and Source File the file. Lines of other "
                 "programs, sudo's PAM lines, sudo lines that hold no command and lines in neither syslog file "
                 "format are counted in the run log and not reported. A line is read in either of rsyslog's two "
                 "file formats, an RFC 3339 time with a UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone; for a command written over several lines both come "
                 "from the first. Hostname is the host name the line stores, and it held the same value on every "
                 "row of each tested image. Two programs write these lines. The original sudo opens syslog as "
                 "sudo, adding its process ID only when sudoers sets syslog_pid (sudo 1.9.17p2, "
                 "plugins/sudoers/logging.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/plugins/sudoers/logging.c#L1073), "
                 "and writes the name of the user who ran it (plugins/sudoers/logging.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/plugins/sudoers/logging.c#L1018) "
                 "right-aligned in eight characters, ' : ' and the message (lib/eventlog/eventlog.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L1013-L1031). "
                 "sudo-rs, which Ubuntu 26.04 runs as sudo, never opens syslog (sudo-rs 0.2.13, src/system/mod.rs, "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/system/mod.rs#L242-L254), "
                 "so its lines carry the name it was run under (syslog(3), "
                 "https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man3/syslog.3?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n41, "
                 "lines 41 to 46 and 67 to 76), and writes '<user> : TTY=<terminal> ; PWD=<directory> ; "
                 "USER=<user> ; COMMAND=<command>', leaving out the TTY part when it has no terminal "
                 "(src/sudo/pipeline.rs, "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/sudo/pipeline.rs#L266-L287). "
                 "Lines named sudo or sudo-rs are read; Program is that name, and it held the same value, sudo, on "
                 "every row of each tested image. The original sudo writes a refused command's reason first, then "
                 "the HOST, TTY, CHROOT, PWD, USER, GROUP, TSID and ENV fields it has, each followed by ' ; ', "
                 "then COMMAND= and the command and its arguments, an argument holding a space in single quotes, "
                 "with ' ; SIGNAL=' and ' ; EXIT=' after them in a record of the command's exit "
                 "(lib/eventlog/eventlog.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L144-L231). "
                 "User is the user the line names, the one who ran sudo, without the padding. Reason is the text "
                 "before the first field. TTY, Working Directory (PWD), Run As User (USER) and Run As Group "
                 "(GROUP) are those fields as stored, and Command is everything after COMMAND= apart from a "
                 "trailing SIGNAL or EXIT field. For the original sudo PWD is the directory it set the command to "
                 "run in: the one runcwd names in sudoers, or the one the user asked for where runcwd is *, and "
                 "without either the run-as user's home for a login shell or else the directory sudo was run from "
                 "(plugins/sudoers/logging.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/plugins/sudoers/logging.c#L1008-L1014, "
                 "and plugins/sudoers/check_util.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/plugins/sudoers/check_util.c#L78-L87). "
                 "For sudo-rs it is the directory sudo-rs was in when it wrote the line, or unknown when it could "
                 "not read it (src/sudo/pipeline.rs, "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/sudo/pipeline.rs#L266-L287). "
                 "Other Fields holds the HOST, CHROOT, TSID, ENV, SIGNAL and EXIT fields and any other text "
                 "between the fields, as stored. The original sudo writes the terminal without /dev/ "
                 "(https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L134-L138) "
                 "and sudo-rs writes the full device name. sudo-rs writes a space after the command even when it "
                 "has no arguments (src/common/command.rs, "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/common/command.rs#L22-L38), "
                 "and Command keeps it. The original sudo writes a command its policy allowed with no reason and a "
                 "refused one with its reason (eventlog_accept() and eventlog_reject(), "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L1320-L1373), "
                 "and a sudoers log_format of json writes JSON instead "
                 "(https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L1129-L1141), "
                 "which is not read. sudo-rs 0.2.13 writes its line just before it runs the command "
                 "(https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/sudo/pipeline.rs#L113-L119) "
                 "and writes nothing for a command it refuses: on the lab VM a sudo-rs command refused because it "
                 "needed a password added no line to auth.log (ubuntu2604_arm64_authlog), so a refusal by sudo-rs "
                 "leaves no row. A message too long for one syslog line is written over several. The original sudo "
                 "breaks it at the last space that fits, or inside a word when none does, drops the spaces at the "
                 "break, and starts each later line with '(command continued)' "
                 "(https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/lib/eventlog/eventlog.c#L993-L1050); "
                 "a row joins the parts with one space where the earlier part is shorter than the limit sudo uses "
                 "by default, 960 characters less what it allows for the prefix before the part "
                 "(include/sudo_eventlog.h, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/include/sudo_eventlog.h#L62-L63, "
                 "and plugins/sudoers/defaults.c, "
                 "https://github.com/sudo-project/sudo/blob/d1b48c651cec19fe37d1f0d3299d2283fb0f88e4/plugins/sudoers/defaults.c#L667), "
                 "and with none where it fills the limit. A sudoers syslog_maxlen other than 960 changes the limit "
                 "and so the joining, and several spaces at one break are joined as one. sudo-rs ends each part it "
                 "cuts with ' [...]' and starts the next with '[...] ' (src/log/syslog.rs, "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/log/syslog.rs#L12-L17 "
                 "and "
                 "https://github.com/trifectatechfoundation/sudo-rs/blob/965cd7b99b04faf55819606178a5e8233cfd8b9e/src/log/syslog.rs#L48-L52); "
                 "a row joins those parts with nothing added, and no tested file held one. Neither program's lines "
                 "carried a process ID on the tested images, so the parts of two commands logged at the same "
                 "moment cannot be told apart; a continuation line with no line before it to continue, and a "
                 "sudo-rs part with no part after it, are counted in the run log. On ubuntu2604_arm64_triage all "
                 "69 rows are the VM owner's use of sudo-rs: 62 have two spaces before PWD=, the empty TTY part "
                 "only sudo-rs writes, and 7 read TTY=/dev/pts/N. Reason was blank, Run As User held the same "
                 "value, root, and Run As Group and Other Fields were blank on every row of that image, and 10 "
                 "Commands end with the space sudo-rs adds. ubuntu2604_arm64_authlog holds the same 69 and three "
                 "known refusals by the original sudo (/usr/bin/sudo.ws) at 09:15:12, 09:15:13 and 09:15:14 UTC on "
                 "2026-09-28, run over SSH without a terminal: Reason 'a password is required' and no TTY on all "
                 "three, Run As User root, nobody and root, the second's argument written as 'two words' in single "
                 "quotes, and the third's 2,160-character argument written over lines 872 to 875 as parts of 82, "
                 "928, 928 and 304 characters, whose row's Command equals the command that was run. Run As Group "
                 "and Other Fields were blank on every row of that image. Time (UTC) is filled on every row of "
                 "both images.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no sudo line)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 72 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 72 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 72 rows",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 69 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "sudoCommandsJournal": {
        "name": "sudo Commands (journal)",
        "description": "Commands sudo logged to the systemd journal, with the user who ran sudo and, where the "
                       "entry records them, the reason for a refusal, the terminal, the working directory, the "
                       "user and group the command was to run as, the command line and the boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (sudo)",
        "notes": "One row per command sudo logged in the systemd journal files under var/log/journal and "
                 "run/log/journal, read with the same reader as systemd Journal (scripts/systemd_journal.py) and "
                 "in the way Cron Log (journal) reads its entries: journald keeps the name in a syslog line's tag "
                 "as SYSLOG_IDENTIFIER and the text after the tag as MESSAGE (Reference: systemd, "
                 "'journald-syslog.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L204-L262, "
                 "with the fields written at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L433-L464), "
                 "the first value of a field an entry holds more than once is read, an entry that more than one "
                 "file holds is read once, and rows are in order of Time (UTC), then boot ID, time since boot and "
                 "sequence number. Entries whose SYSLOG_IDENTIFIER is sudo or sudo-rs are read, and their messages "
                 "as sudo Commands reads the lines of auth.log: Program, User, Reason, TTY, Working Directory, Run "
                 "As User, Run As Group, Command and Other Fields have the meanings and references given there, "
                 "and a command sudo wrote over several entries is joined as sudo Commands joins lines, taking the "
                 "entries in that order. journald removes whitespace at the end of a message a program sends to "
                 "the syslog socket and keeps the message as received in SYSLOG_RAW when it removed any "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L372-L397 "
                 "and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L470-L484), "
                 "so the space sudo-rs writes after a command, which sudo Commands keeps, is not in Command here: "
                 "10 rows on each tested image held such a command, and each of their entries' SYSLOG_RAW ends "
                 "with the space. Time (UTC) is the entry's realtime, the time journald received it (Reference: "
                 "systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651), "
                 "and for a command written over several entries it is the first entry's, as are Hostname, the "
                 "entry's _HOSTNAME field, Boot ID, the boot the entry names, and Source File, the journal file "
                 "the entry was read from. Entries of other programs, sudo's PAM lines, sudo messages with no "
                 "COMMAND= field, continuation entries with no entry to continue, entries read a second time, and "
                 "journal files that could not be read or whose header sets an incompatible flag the reader does "
                 "not know are counted in the run log and not reported. No sudo entry on the tested images carried "
                 "SYSLOG_PID, and the journal's own _PID field is not used, so, as in auth.log, the artifact "
                 "cannot tell apart the parts of two commands logged at the same moment. ubuntu2604_arm64_journal "
                 "and ubuntu2604_arm64_usb hold 72 rows and "
                 "ubuntu2604_arm64_usbstorage 73, from 5 boots on each; Program held one value, sudo, on every "
                 "row, and 3 rows carry the Reason 'a password is required', the refusals by the original sudo "
                 "that sudo Commands describes, the third joined from 4 entries. Hostname held one value on every "
                 "row of each tested image, and Run As Group and Other Fields were blank on every row. Four "
                 "captures of that VM's "
                 "auth.log were compared with this artifact, matching rows on Program, User, Reason, TTY, Working "
                 "Directory, Run As User, Run As Group, Command, with the space sudo-rs adds removed, and Other "
                 "Fields, with times less than 1 s apart: every one of the 72 sudo Commands rows of "
                 "ubuntu2604_arm64_authlog and the 69 of ubuntu2604_arm64_triage was matched by a row of "
                 "ubuntu2604_arm64_journal, the 72 of ubuntu2604_arm64_shutdown by rows of "
                 "ubuntu2604_arm64_usbstorage and the 72 of ubuntu2604_arm64_cron by rows of ubuntu2604_arm64_usb. "
                 "The rows left over, the 3 refusals against ubuntu2604_arm64_triage and 1 row of "
                 "ubuntu2604_arm64_usbstorage, are later than the last sudo line of the capture they were compared "
                 "with. On every matched row Time (UTC) here was earlier than the auth.log line's, by 0.000004 to "
                 "0.00064 s. No tested image held an entry in two files, and the unit tests exercise it. No member "
                 "of the other 28 tested images matches the declared paths.",
        "paths": ('*/var/log/journal/*.journal', '*/var/log/journal/*.journal~', '*/run/log/journal/*.journal',
                  '*/run/log/journal/*.journal~'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "terminal",
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
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 72 rows",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 72 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 73 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import journal_entries, journal_sources, program_lines, read_file, read_journals

# The original sudo opens syslog as "sudo"; sudo-rs does not open it, so its lines carry the name
# it was run as.
_PROGRAMS = ('sudo', 'sudo-rs')
# "<user> : <message>", the user right-aligned in eight characters by the original sudo.
_USER = re.compile(r'\s*(\S+) : (.*)', re.DOTALL)
# The original sudo's later parts of a line too long for syslog.
_CONTINUED = '(command continued) '
# The original sudo's default limit on a syslog message (MAXSYSLOGLEN), less the "%8s : " prefix
# (3 characters and the user) or the "%8s : (command continued) " prefix (23 and the user).
_SYSLOG_MAXLEN = 960
# sudo-rs ends a part it had to cut with " [...]" and starts the next part with "[...] ".
_RS_END, _RS_START = ' [...]', '[...] '
_FIELD = re.compile(r'(HOST|TTY|CHROOT|PWD|USER|GROUP|TSID|ENV)=(.*)', re.DOTALL)
_COMMAND = re.compile(r'(?:^|; )COMMAND=')
_EXIT = re.compile(r'( ; SIGNAL=[^;]*)?( ; EXIT=-?\d+)?\Z')


def sudo_entries(lines, counts):
    """Each logged sudo message, its parts joined: dict with first and last line, UTC time, time as
    recorded, host, program, user and the message after "<user> : "."""
    entries, current = [], {}
    for number, when, stamp, host, program, _pid, message in lines:
        if current and current['cut']:
            if message.startswith(_RS_START):
                part = message[len(_RS_START):]
                current['cut'] = part.endswith(_RS_END)
                current['body'] += part[:-len(_RS_END)] if current['cut'] else part
                current['last'] = number
                continue
            counts['sudo-rs messages cut short with no part after them, reported as far as they go'] += 1
        match = _USER.fullmatch(message)
        continued = match is not None and match.group(2).startswith(_CONTINUED)
        if continued and current and not current['cut'] and match.group(1) == current['user']:
            part = match.group(2)[len(_CONTINUED):]
            current['body'] += ('' if len(current['part']) == current['limit'] else ' ') + part
            current['part'] = part
            current['limit'] = _SYSLOG_MAXLEN - (23 + len(match.group(1)))
            current['last'] = number
            continue
        if current:
            entries.append(current)
        current = {}
        if continued or message.startswith(_RS_START):
            counts['continuation lines with no line to continue, not reported'] += 1
            continue
        if match is None:
            counts['PAM lines, not reported' if message.startswith('pam_') else
                   'sudo lines that are not "<user> : <message>", not reported'] += 1
            continue
        user, body = match.groups()
        cut = body.endswith(_RS_END)
        current = {'first': number, 'last': number, 'when': when, 'stamp': stamp, 'host': host,
                   'program': program, 'user': user, 'body': body[:-len(_RS_END)] if cut else body,
                   'part': body, 'limit': _SYSLOG_MAXLEN - (3 + len(user)), 'cut': cut}
    if current and current['cut']:
        counts['sudo-rs messages cut short with no part after them, reported as far as they go'] += 1
    if current:
        entries.append(current)
    return entries


def command_fields(body):
    """(reason, TTY, working directory, run-as user, run-as group, command, other fields) from the
    message after "<user> : ", or None when it holds no COMMAND= field."""
    body = body.lstrip(' ')
    at = _COMMAND.search(body)
    if at is None:
        return None
    head = body[:at.start()].rstrip(' ')
    reason, fields, other = [], {}, []
    for token in (head.split(' ; ') if head else []):
        field = _FIELD.fullmatch(token)
        if field and field.group(1) not in fields:
            fields[field.group(1)] = field.group(2)
        elif not fields and not other:
            reason.append(token)
        else:
            other.append(token)
    command = body[at.end():]
    tail = _EXIT.search(command)
    if tail.group(0):
        other.extend(part.lstrip(' ;') for part in tail.groups() if part)
        command = command[:tail.start()]
    other[:0] = [f'{key}={fields[key]}' for key in ('HOST', 'CHROOT', 'TSID', 'ENV') if key in fields]
    return (' ; '.join(reason), fields.get('TTY', ''), fields.get('PWD', ''),
            fields.get('USER', ''), fields.get('GROUP', ''), command, ' ; '.join(other))


@artifact_processor
def sudoCommands(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'User', 'Reason', 'TTY',
                    'Working Directory', 'Run As User', 'Run As Group', 'Command', 'Other Fields', 'Line',
                    'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        relative = context.get_relative_path(path)
        before = len(data_list)
        for entry in sudo_entries(program_lines(data, _PROGRAMS, problems), problems):
            fields = command_fields(entry['body'])
            if fields is None:
                problems['sudo messages with no COMMAND= field, not reported'] += 1
                continue
            lines = str(entry['first']) if entry['last'] == entry['first'] else f"{entry['first']}-{entry['last']}"
            data_list.append((entry['when'], entry['stamp'], entry['host'], entry['program'], entry['user'], *fields,
                              lines, relative))
        if len(data_list) > before:
            read.append(path)
    if problems:
        logfunc('sudo Commands: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def journal_command_rows(journals, counts):
    """(time, host, program, user, reason, TTY, working directory, run-as user, run-as group, command, other fields,
    boot ID, source) for each command sudo logged in these journal files, oldest first, the parts of a command written
    over several entries joined as sudo_entries joins lines; journals: (relative path, JournalFile)."""
    entries = journal_entries(journals, lambda program: program in _PROGRAMS, counts)
    lines = [(number, when, '', host, program, pid, message)
             for number, (when, host, program, pid, message, _boot, _relative) in enumerate(entries)]
    rows = []
    for entry in sudo_entries(lines, counts):
        fields = command_fields(entry['body'])
        if fields is None:
            counts['sudo messages with no COMMAND= field, not reported'] += 1
            continue
        first = entries[entry['first']]
        rows.append((entry['when'], entry['host'], entry['program'], entry['user'], *fields, first[5], first[6]))
    return rows


@artifact_processor
def sudoCommandsJournal(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'User', 'Reason', 'TTY', 'Working Directory',
                    'Run As User', 'Run As Group', 'Command', 'Other Fields', 'Boot ID', 'Source File')
    counts = Counter()
    journals, staged = read_journals(context, counts)
    data_list = journal_command_rows(journals, counts)
    if counts:
        logfunc('sudo Commands (journal): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, journal_sources(data_list, staged)
