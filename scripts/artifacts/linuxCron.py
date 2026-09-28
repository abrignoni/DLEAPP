"""Lines the Debian cron daemon and its crontab command wrote to syslog, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxCronLog": {
        "name": "Cron Log",
        "description": "Lines cron and crontab logged in syslog and cron.log: commands of jobs cron started, crontab "
                       "listings, installs, edits and removals, and cron's own messages.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Scheduled Jobs (Linux)",
        "notes": "Reads /var/log/syslog and its rotations, and /var/log/cron.log and its rotations, gzip ones "
                 "included, and reports each line whose tag names cron or crontab and whose message has the form "
                 "cron writes (below), in line order, file by file in name order; Line is its line number in the "
                 "file and Source File the file, and the files that held a row are named in the report's located-at "
                 "line. Lines of other programs, non-empty lines in neither syslog file format described below and "
                 "cron or crontab lines in another form are counted in the run log and not reported. Messages kept "
                 "only in the systemd journal, or written to another file, are not read. A line is read in either of "
                 "rsyslog's two file formats, an RFC 3339 time with a UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone and for an RFC 3339 time that is not a calendar date, "
                 "which the run log counts. Hostname is the host name the line stores, and it held the same value on "
                 "every row of each tested image; Process ID is the process ID in the line's tag. Program is the "
                 "name in the line's tag, compared by its last path part with case ignored: Ubuntu's cron "
                 "3.0pl1-200ubuntu1 logs as cron for the daemon, the name it was started under (cron.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n70), "
                 "as CRON for the process that runs a job, which upshifts that name (do_command.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n146, "
                 "lines 146 to 154), and as crontab for the crontab command (crontab.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n106); "
                 "Debian's cron logs these names from 3.0pl1-125 (debian/changelog, "
                 "https://salsa.debian.org/debian/cron/-/blob/f11daeee8ec966c044f22f0cf7d9e7a6b1bd59b3/debian/changelog#L882), "
                 "and Debian 5's cron 3.0pl1-105 logged its full paths, /usr/sbin/cron and /USR/SBIN/CRON, on "
                 "honeynet_fc7_debian5. cron writes each line as (<user>) <event> (<detail>) to the cron facility at "
                 "the info level (misc.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/misc.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n565, "
                 "lines 565 to 570): User is the text in the first parentheses, Event the event and Detail the text "
                 "in the last parentheses. A CMD line is written by the process that runs a job, just before it "
                 "starts the job's shell, whose process ID it carries (do_command.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n243, "
                 "lines 243 to 256): User is the user the job runs as, the LOGNAME cron sets for it "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n158), "
                 "and Detail is the command as cron runs it, the crontab entry's command up to its first unescaped "
                 "%, with \\% and \\\\ written as % and \\ "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n186, "
                 "lines 186 to 221); what follows that % is sent to the command's standard input and is not logged. "
                 "In Detail a control character is written as ^ and a character, the delete character as ^? and a "
                 "byte above it as a backslash and three octal digits (misc.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/misc.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n651, "
                 "lines 651 to 673), so a command's non-ASCII text shows as octal escapes. cron writes no line when "
                 "a job ends unless it was started with an -L level that adds END lines, and writes a job's process "
                 "ID inside CMD and END lines only with another level (cron.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n469 "
                 "and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n486; "
                 "cron.h, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.h?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n142, "
                 "lines 142 to 145; do_command.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n368, "
                 "lines 368 to 374, and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n685, "
                 "lines 685 to 696); the tested VM started it as /usr/sbin/cron -f -P, and neither tested image "
                 "holds an END line. LIST, REPLACE, DELETE, BEGIN EDIT and END EDIT are written by the crontab "
                 "command when a crontab is listed, installed, removed and edited (crontab.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n316, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n979, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n407, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n573 "
                 "and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n801); "
                 "User is the user who ran crontab and Detail the user whose crontab it was. An edit writes BEGIN "
                 "EDIT and END EDIT, and REPLACE between them only when crontab installed a change, which it decides "
                 "by the edited file's modification time in whole seconds "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n503, "
                 "lines 503 to 504), so an edit saved within the second in which crontab wrote the file is not "
                 "installed. RELOAD is written by the daemon when a crontab it had read before has changed "
                 "(database.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n439, "
                 "lines 439 to 463), so a new crontab writes none; User is the crontab's name, a user's own for "
                 "their crontab, *system* for /etc/crontab and *system* followed by the file name for a file in "
                 "/etc/cron.d "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n162, "
                 "lines 162 to 166, and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n192, "
                 "lines 192 to 195), and Detail the crontab file. cron's own messages carry CRON as User: on the "
                 "tested images, INFO lines the daemon wrote when it started, giving the pidfile's descriptor "
                 "(misc.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/misc.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n316, "
                 "lines 316 to 317) and whether it ran the @reboot jobs or skipped them because its reboot check "
                 "file already existed, which it takes as a restart rather than a system start (cron.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n290, "
                 "lines 290 to 305), STARTUP lines on Debian 5, and info lines when cron discarded a job's output "
                 "because it found no mail program to send it with (do_command.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n520, "
                 "lines 520 to 525). On ubuntu2604_arm64_cron, captured from a VM running cron 3.0pl1-200ubuntu1, "
                 "syslog and its three rotations hold 234 rows: 188 CMD, 20 INFO, 9 LIST, 5 info, 3 REPLACE, 3 BEGIN "
                 "EDIT, 3 END EDIT, 2 DELETE and 1 RELOAD. The known crontab steps listed in the README beside that "
                 "capture account for 16 CMD, 6 LIST, 3 REPLACE, 3 BEGIN EDIT, 3 END EDIT, 2 DELETE, the RELOAD and "
                 "the 5 info rows. The known entries' CMD rows came at each minute the crontab was installed, one "
                 "for each entry, and none after either removal; each install wrote a REPLACE and no RELOAD; the "
                 "edit whose editor saved the file in the same second wrote BEGIN EDIT and END EDIT only, and its "
                 "entry never ran; and the edit saved 1.2 seconds later wrote REPLACE between them and a RELOAD at "
                 "the next minute, after which its entry ran. The known commands show a tab as ^I, é as \\303\\251 and "
                 "the cat command up to its first unescaped %, with \\% written as %. Each minute's CMD rows for the "
                 "known entries matched in number the pam_unix(cron:session) session opened lines cron wrote to "
                 "auth.log for that user in the same second, 3, 3, 3, 3 and 4, from processes whose IDs are not "
                 "those of the CMD rows. On honeynet_fc7_debian5, whose rsyslog 3.18.6 wrote the traditional format, "
                 "syslog holds 29 rows, 5 CMD by /USR/SBIN/CRON and 16 INFO and 8 STARTUP by /usr/sbin/cron, with "
                 "Time (UTC) blank.",
        "paths": ('*/var/log/syslog', '*/var/log/syslog.*', '*/var/log/cron.log', '*/var/log/cron.log.*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "calendar",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 29 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 234 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import OTHER_PROGRAMS, read_file, reported_time, syslog_lines

# The program name's last path part, case ignored: cron (the daemon), CRON (a job's process), crontab.
_PROGRAMS = ('cron', 'crontab')
# cron's log_it(): "(<user>) <event> (<detail>)". Two events hold parentheses of their own.
_FORM = re.compile(r'\(([^()]*)\) (INSECURE MODE \((?:mode 0600 expected|group/other writable)\)|[^()]+?) \((.*)\)')


def cron_fields(message):
    """(user, event, detail) from a message in cron's own form, or None."""
    match = _FORM.fullmatch(message)
    return match.groups() if match else None


def cron_rows(data, counts):
    """(time, time as recorded, host, program, process ID, user, event, detail, line) for each cron and crontab line
    of a syslog file; other lines are counted."""
    rows = []
    for number, stamp, host, program, pid, message in syslog_lines(data, counts):
        if program.rsplit('/', 1)[-1].lower() not in _PROGRAMS:
            counts[OTHER_PROGRAMS] += 1
            continue
        fields = cron_fields(message)
        if fields is None:
            counts['cron and crontab lines in other forms, not reported'] += 1
            continue
        rows.append((reported_time(stamp, counts), stamp, host, program, pid, *fields, number))
    return rows


@artifact_processor
def linuxCronLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'Process ID', 'User',
                    'Event', 'Detail', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = cron_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Cron Log: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
