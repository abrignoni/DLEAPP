"""The lines of the general syslog files rsyslog writes (syslog, messages, kern.log, daemon.log, user.log, debug),
for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxSyslogMessages": {
        "name": "Syslog Messages",
        "description": "The lines of the general syslog files in /var/log (syslog, messages, kern.log, daemon.log, "
                       "user.log and debug, with their rotations), one row per syslog line, with its time, host, "
                       "program, process ID and message as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Logs (Linux)",
        "notes": "One row per line of /var/log/syslog, messages, kern.log, daemon.log, user.log and debug and their "
                 "numbered or dated rotations, gzip ones included, file by file in path order and within a file in "
                 "line order; Line is the line number and Source File the file, and the files read are named in the "
                 "report's located-at line. The files auth.log, secure, cron and the mail logs are not read here. A "
                 "line is split into its time, host, program, process ID and message as rsyslog writes them: "
                 "RSYSLOG_FileFormat begins with an RFC 3339 time "
                 "(https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5,"
                 " "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L49"
                 " and "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L76)"
                 " and RSYSLOG_TraditionalFileFormat with an RFC 3164 date "
                 "(https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5,"
                 " "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L46"
                 " and "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L72),"
                 " the sender's local month, day and time with no year and no zone "
                 "(https://www.rfc-editor.org/rfc/rfc3164#section-4.1.2). Time as Recorded is the time as written. "
                 "Time (UTC) is that time in UTC when it carries its own offset, and blank for an RFC 3164 date, "
                 "because the year and the zone are not recorded. Hostname is the host name as the line records it, "
                 "and it held one value on every row of each of the six tested images. Which messages reach which "
                 "file is set by the syslog daemon's configuration, which this artifact does not read, and one "
                 "message can be written to several files: on ubuntu2604_arm64_usb all 6,082 kern.log rows and on "
                 "ubuntu2604_arm64_usbstorage all 1,673 have a syslog row with the same time, host, program, process"
                 " ID and message, and on honeynet_fc7_debian5 syslog holds every row of its messages (2,001), "
                 "kern.log (2,262), daemon.log (55), debug (260) and user.log (7) files. A repeated row is therefore"
                 " not a repeated event. On the six tested images that hold these files every non-empty line of "
                 "every file read became a row, checked by counting the lines of each file: 6,946 rows from six "
                 "files on honeynet_fc7_debian5 and 1,220 from messages on rocky98_arm64_known, all with RFC 3164 "
                 "dates and so a blank Time (UTC), and 28,727 on ubuntu2604_arm64_cron, 4,992 on "
                 "ubuntu2604_arm64_crontab, 35,912 on ubuntu2604_arm64_usb and 12,402 on "
                 "ubuntu2604_arm64_usbstorage, all with RFC 3339 times. A line in neither form would be counted in "
                 "the run log and not reported; none of the tested files held one. systemd Journal reads the systemd"
                 " journal, which a system can keep beside these files.",
        "paths": ('*/var/log/syslog', '*/var/log/syslog.[0-9]*', '*/var/log/syslog-[0-9]*',
                  '*/var/log/messages', '*/var/log/messages.[0-9]*', '*/var/log/messages-[0-9]*',
                  '*/var/log/kern.log', '*/var/log/kern.log.[0-9]*', '*/var/log/kern.log-[0-9]*',
                  '*/var/log/daemon.log', '*/var/log/daemon.log.[0-9]*', '*/var/log/daemon.log-[0-9]*',
                  '*/var/log/user.log', '*/var/log/user.log.[0-9]*', '*/var/log/user.log-[0-9]*',
                  '*/var/log/debug', '*/var/log/debug.[0-9]*', '*/var/log/debug-[0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 6946 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 1220 rows",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 28727 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 4992 rows",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 35912 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 12402 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import read_file, reported_time, syslog_lines


def message_rows(data, counts):
    """(time, time as recorded, host, program, process ID, message, line) for each line of a syslog file in either
    format; lines in neither format are counted."""
    return [(reported_time(stamp, counts), stamp, host, program, pid, message, number)
            for number, stamp, host, program, pid, message in syslog_lines(data, counts)]


@artifact_processor
def linuxSyslogMessages(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'Process ID', 'Message',
                    'Line', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            counts['files that could not be read'] += 1
            continue
        rows = message_rows(data, counts)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        read.append(path)
    if counts:
        logfunc('Syslog Messages: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
