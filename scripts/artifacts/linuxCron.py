"""Lines the Debian cron daemon and its crontab command wrote to syslog, and the entries of the crontab files that
cron reads, for DLEAPP.

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
    "linuxCrontabEntries": {
        "name": "Crontab Entries",
        "description": "Lines of the files in /var/spool/cron/crontabs, /etc/crontab and /etc/cron.d, the places "
                       "Debian's and Ubuntu's cron reads crontabs from: environment settings, jobs split into "
                       "their time fields, user and command, and comments.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Scheduled Jobs (Linux)",
        "notes": "One row per line that is not blank in each file in the three places Debian's and Ubuntu's cron "
                 "reads crontabs from: a user's crontab in /var/spool/cron/crontabs, named for the user (Crontab "
                 "User), /etc/crontab (System) and each file in /etc/cron.d (cron.d) (Reference: Ubuntu cron "
                 "3.0pl1-200ubuntu1, database.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n162, "
                 "lines 162 to 166, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n169, "
                 "lines 169 to 204, and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n210, "
                 "lines 210 to 230). Debian's cron 3.0pl1-210 carries the same database.c "
                 "(https://sources.debian.org/src/cron/3.0pl1-210/database.c/), and 3.0pl1-105, whose sources are "
                 "cited below, reads the same three places (its pathnames.h, lines 31, 42, 69 and 72). Files in "
                 "folders below these, which cron does not read, and symbolic links, which are not followed, are "
                 "counted in the run log. cron skips a file whose name begins with a dot, and in /etc/cron.d one "
                 "whose name has a character other than letters, digits, _ and - "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n183, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n189 "
                 "and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n223; "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n497, "
                 "lines 497 to 524, whose pattern at lines 509 and 523 is the one used when cron is not started "
                 "with -l); the artifact reports such a file's lines and counts the file in the run log. Ubuntu's "
                 "service starts cron as /usr/sbin/cron -f -P $EXTRA_OPTS (debian/cron.service, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/debian/cron.service?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n8), "
                 "and EXTRA_OPTS was empty on the tested VM. Line is the line's number in the file, Line as "
                 "Written the line without its newline, and Source File the file; text is shown as UTF-8, with any "
                 "byte that is not valid UTF-8 written as a \\x escape. Kind is decided as cron's parser decides "
                 "between a comment, a setting and a job (env.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/env.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n144, "
                 "lines 144 to 266; entry.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n71, "
                 "lines 71 to 368). A line whose first character other than a space or tab is # is a Comment, as "
                 "cron's skip_comments treats it (misc.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/misc.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n384, "
                 "lines 384 to 417), so a job that has been commented out is a Comment row with its text in Line "
                 "as Written only. A line cron reads as an environment setting is an Environment row, with "
                 "Variable and Value as cron leaves them: quotes around the name or the value removed, whitespace "
                 "before and after the = and at the end of the value dropped, and only the first 998 characters of "
                 "the line after its leading spaces and tabs read "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/env.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n155, "
                 "lines 155 to 158, and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/env.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n235, "
                 "lines 235 to 259). Any other line is a Job. When it begins with @, Special is its text up to the "
                 "first space or tab "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n113, "
                 "lines 113 to 126); otherwise Minute, Hour, Day of Month, Month and Day of Week are its first "
                 "five runs of characters other than spaces and tabs, the text cron reads each field from "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n412, "
                 "lines 412 to 413; cron.h, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/cron.h?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n111, "
                 "lines 111 to 117). In /etc/crontab and /etc/cron.d the next run is User "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n242, "
                 "lines 242 to 255) and Command the rest of the line after the one space or tab that ended it, so "
                 "any further blanks begin the Command "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n327); "
                 "in a user's crontab Command is the rest of the line after the blanks, and User is the file's "
                 "name, which cron looks up as the crontab's account "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n229 "
                 "and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n308). "
                 "A command is reported as written: cron sends what follows its first unescaped % to the command's "
                 "standard input (do_command.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/do_command.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n186, "
                 "lines 186 to 221). A line that ends before its five time fields is Other, and so are two kinds "
                 "of line whose reading by cron the artifact does not model, each counted in the run log: a line "
                 "holding a NUL byte, at which cron's get_string stops as at the end of a line "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/misc.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n367), "
                 "and a line ending at an opening quote, where load_env reads on past the end of the line into "
                 "what its buffer held before "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/env.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n172, "
                 "lines 172 to 173, and "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/env.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n201). "
                 "The artifact does not report whether cron used a file or a line. cron ignores a whole file when "
                 "one line fails to parse (user.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/user.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n278, "
                 "lines 278 to 293), and it checks each file's owner, mode and links "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/database.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n319, "
                 "lines 319 to 416), which are not examined here. Nor does it check the time fields, because "
                 "Ubuntu's arm64 cron accepted invalid ones when tested: get_list, get_range and get_number return "
                 "char "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n38, "
                 "lines 38 to 40), which is unsigned on AArch64 (Reference: Arm, 'Procedure Call Standard for the "
                 "Arm 64-bit Architecture', "
                 "https://github.com/ARM-software/abi-aa/blob/a5e86d3fec7342719f3bd1f939ec1b8ac6438c4f/aapcs64/aapcs64.rst#L2794), "
                 "so the EOF they return for a bad field never compares equal to EOF (for example "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n174). "
                 "Measured on the lab VM: crontab -n of 3.0pl1-200ubuntu1 accepted each of five one-line files "
                 "whose minute was 70, */0, 1/5 or 5-64/30 or whose day of month was 32, and refused one beginning "
                 "@bogus; a harness built from the package's sources read the first as a job whose command was "
                 "bad-minute, the line's last word, and the same sources built with gcc's -fsigned-char rejected "
                 "all five. A cron built for another architecture was not run. So a Job row's time fields are the "
                 "line as written, not a schedule cron kept. The run log counts three cases in which cron "
                 "3.0pl1-200ubuntu1 ignores a whole file whatever its time fields: a last line with no newline "
                 "that is not blank or a comment "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/user.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n263, "
                 "lines 263 to 277), a setting or job at line 10,004 or later "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/user.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n308, "
                 "lines 308 to 317), and a command of 999 characters or more "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/entry.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n327, "
                 "lines 327 to 331). File Modified is the modified time the extraction recorded for the file. "
                 "crontab installs a user's crontab by writing a new file and renaming it over the old one "
                 "(crontab.c, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n973), "
                 "so for a crontab nothing changed after its install it is the time of that install. A file "
                 "crontab installed begins with three lines it writes "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n865, "
                 "lines 865 to 867), reported as Comment rows; for a user's crontab that begins with them, "
                 "Installed From (Header) is the file name crontab recorded and Installed On (Header) the time of "
                 "the install as ctime wrote it, in the local time of the process that ran crontab, with no zone "
                 "recorded. crontab -l leaves those lines out unless the CRONTAB_NOHEADER environment variable "
                 "begins with N or n "
                 "(https://git.launchpad.net/ubuntu/+source/cron/tree/crontab.c?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n333, "
                 "lines 333 to 338). Compared with cron's own code: a harness on the lab VM built from the "
                 "package's sources runs load_env and load_entry over a file in the loop load_user uses and prints "
                 "each setting and command. On 400 generated crontabs with valid time fields, 200 read as users' "
                 "crontabs and 200 as system ones, the harness built with gcc's defaults on the arm64 VM and the "
                 "same harness built with -fsigned-char read the same 335 settings and 2,668 commands as the "
                 "artifact, with the same user in system files. On 4,000 generated one-line files both builds read "
                 "the 1,714 lines they took as settings as the artifact did; the -fsigned-char build rejected "
                 "every other line that was not blank or a comment, the 1,995 the artifact calls Other for ending "
                 "before five fields, the 30 ending at an opening quote and 148 it reports as Jobs, while the "
                 "arm64 build accepted 56 of those 148 and read 8 of them with a different command. On generated "
                 "boundary files both builds ignored the files the run log counts, 3 with no final newline, 2 with "
                 "a line at 10,004 and 2 with a command of 999 characters, and read commands of 998. Debian's cron "
                 "read environment lines with another parser before 3.0pl1-110 (debian/changelog, "
                 "https://git.launchpad.net/ubuntu/+source/cron/tree/debian/changelog?id=4906de2a24e12e0c297bcd8164aab6d6bf76ed91#n1872, "
                 "lines 1872 to 1875). On ubuntu2604_arm64_crontab, captured from the lab VM running cron "
                 "3.0pl1-200ubuntu1, there are 41 rows from five files: 27 Comment, 4 Environment and 10 Job. The "
                 "user crontab's 13 rows are crontab's three lines and the ten lines of a known file installed "
                 "with crontab, whose commented-out job is a Comment row and whose @reboot job is the only row "
                 "with Special; its File Modified is 14:08:38 UTC, the second the known install ran, and Installed "
                 "On (Header) reads Tue Sep 29 10:08:38 2026, 4 hours behind, the offset of the VM's zone "
                 "(America/New_York) on that date. /etc/cron.d/.placeholder holds only comments and is counted in "
                 "the run log as a name cron skips. The harness read the same 6 settings and 14 commands as the "
                 "artifact from the four files of that image that hold them and from honeynet_fc7_debian5's "
                 "/etc/crontab. ubuntu2604_arm64_triage holds the same /etc/crontab, byte for byte, and 21 rows. "
                 "honeynet_fc7_debian5, whose cron is 3.0pl1-105, has 15 rows, 13 from /etc/crontab (7 Comment, 2 "
                 "Environment, 4 Job) and 2 Comment rows from /etc/cron.d/.placeholder; the first job's user field "
                 "is followed by four spaces, so its Command begins with three, and a harness built from that "
                 "version's sources (cron_3.0pl1.orig.tar.gz, "
                 "https://snapshot.debian.org/file/f8d00de4c7c0eae97bedb4a3ec10ea21d43ece84, with "
                 "cron_3.0pl1-105.diff.gz, "
                 "https://snapshot.debian.org/file/b172e9b7f2739e4366a2c35d4701f9e41aa2bb7a) read the same 2 "
                 "settings and 4 commands from it. On ubuntu2604_arm64_triage and honeynet_fc7_debian5, which hold "
                 "no user crontab, Installed On (Header), Installed From (Header) and Special are empty on every "
                 "row, and File Modified held one value on every row of each, the two files of "
                 "honeynet_fc7_debian5 carrying the same recorded time; on ubuntu2604_arm64_triage Crontab held "
                 "one value, System, on every row. Source File is kept although Crontab separates the two files of "
                 "honeynet_fc7_debian5 one to one, because /etc/cron.d can hold any number of files, which Crontab "
                 "does not tell apart (three on ubuntu2604_arm64_crontab). No member of the other twenty-seven "
                 "tested images matches the declared paths.",
        "paths": ("*/var/spool/cron/crontabs/*", "*/etc/crontab", "*/etc/cron.d/*"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "calendar",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386, cron 3.0pl1-105 | 15 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64, cron 3.0pl1-200ubuntu1 | 41 rows",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                            "paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 21 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, recorded_time, seeker_of
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


# Crontab files. The parsing follows Ubuntu's cron 3.0pl1-200ubuntu1: load_env() in env.c for environment settings,
# and for a job the fields load_entry() in entry.c reads, split as cron splits a line whose fields are valid.
_BLANKS = b' \t'
_SPACE = b' \t\n\v\f\r'  # isspace() in the C locale
_QUOTES = b'"\''
_MAX_ENVSTR = 1000
_MAX_COMMAND = 1000
_MAX_TAB_LINES = 10000
_NHEADER_LINES = 3
_HEADER = b'# DO NOT EDIT THIS FILE - edit the master and reinstall.'
_INSTALLED = re.compile(rb'# \((.*) installed on (.{24})\)')
_VERSION = b'# (Cron version -- '
UNDEFINED = 'lines ending at an opening quote, whose reading by cron depends on what its buffer held before (Kind Other)'
NO_NEWLINE = 'files whose last line has no newline, which cron ignores whole'
NUL = 'lines holding a NUL byte, which cron reads as more than one line (Kind Other)'
TOO_LONG = 'files with a line that is not blank or a comment at line 10,004 or later, which cron ignores whole'
SKIPPED_NAME = ('files whose names cron skips (a name starting with a dot, or in /etc/cron.d a name with a character '
                'other than A to Z, a to z, 0 to 9, _ and -), whose lines are reported')
_CLASSICAL = re.compile(r'[a-zA-Z0-9_-]+')
LONG_COMMAND = 'commands of 999 or more characters, for which cron ignores the whole file'
_NAMEI, _NAME, _EQ1, _EQ2, _VALUEI, _VALUE, _FINI, _ERROR = range(8)


def load_env(line):
    """(name, value) as bytes for a line cron reads as an environment setting, None for a line it does not, or
    UNDEFINED. line is the line from its first character that is not a space or tab, without its newline."""
    s = line[:_MAX_ENVSTR - 2]
    state, quote, name, value = _NAMEI, None, bytearray(), bytearray()
    target, i = name, 0
    while state != _ERROR and i < len(s):
        if state in (_NAMEI, _VALUEI):
            if s[i] in _QUOTES:
                quote = s[i]
                i += 1
                if i == len(s):
                    return UNDEFINED
            state += 1
        if state in (_NAME, _VALUE):
            if quote is not None:
                if s[i] == quote:
                    state += 1
                    i += 1
                    continue
                if state == _NAME and s[i] == ord('='):
                    state = _ERROR
                    continue
            elif state == _NAME:
                if s[i] in _SPACE:
                    i += 1
                    state += 1
                    continue
                if s[i] == ord('='):
                    state += 1
                    continue
            target.append(s[i])
            i += 1
        elif state == _EQ1:
            if s[i] == ord('='):
                state += 1
                target = value
                quote = None
            elif s[i] not in _SPACE:
                state = _ERROR
            i += 1
        else:  # _EQ2 and _FINI skip spaces; anything else moves on
            if s[i] in _SPACE:
                i += 1
            else:
                state += 1
    if state != _FINI and not (state in (_VALUE, _EQ2) and quote is None):
        return None
    value = bytes(value).rstrip(_SPACE)
    if len(value) >= 2 and value[0] in _QUOTES and value[-1] == value[0]:
        value = value[1:-1]
    return bytes(name), value


def _token(line, i):
    """(the run of characters that are not space or tab from i, the index after the blanks that follow it)."""
    j = i
    while j < len(line) and line[j] not in _BLANKS:
        j += 1
    k = j
    while k < len(line) and line[k] in _BLANKS:
        k += 1
    return line[i:j], j, k


def split_job(line, system):
    """(minute, hour, day of month, month, day of week, special, user, command) as bytes for a line cron reads as a
    job, or None when the line ends before its five time fields. line starts at its first character that is not a
    space or tab and has no newline."""
    if line[:1] == b'@':
        special, _, i = _token(line, 0)
        fields = (b'',) * 5
    else:
        special, fields, i = b'', [], 0
        for _ in range(5):
            if i >= len(line):
                return None
            field, _, i = _token(line, i)
            fields.append(field)
    user = b''
    if system:
        user, end, _ = _token(line, i)
        i = end + 1 if end < len(line) else end  # the one blank that ends the user name
    command = line[i:]
    return (*fields, special, user, command)


def _text(data):
    return data.decode('utf-8', errors='backslashreplace')


def installed_header(lines):
    """(installed on, installed from) from the three lines crontab writes at the top of a file it installs."""
    if len(lines) >= 3 and lines[0] == _HEADER and lines[2].startswith(_VERSION):
        match = _INSTALLED.fullmatch(lines[1])
        if match:
            return _text(match.group(2)), _text(match.group(1))
    return '', ''


def crontab_rows(data, system, counts):
    """(line number, kind, minute, hour, day of month, month, day of week, special, user, command, variable, value,
    line as written) for each line of a crontab that is not blank."""
    rows = []
    lines = data.split(b'\n')
    if lines[-1] == b'':
        lines.pop()
    elif lines[-1].lstrip(_BLANKS)[:1] not in (b'', b'#'):
        counts[NO_NEWLINE] += 1
    too_long = False
    for number, raw in enumerate(lines, 1):
        line = raw.lstrip(_BLANKS)
        if line[:1] == b'':
            continue
        blank = ('',) * 8
        if line[:1] == b'#':
            rows.append((number, 'Comment', *blank, '', '', _text(raw)))
            continue
        too_long = too_long or number >= _MAX_TAB_LINES + _NHEADER_LINES + 1
        env = load_env(line) if b'\0' not in line else UNDEFINED
        if env is UNDEFINED:
            counts[NUL if b'\0' in line else UNDEFINED] += 1
            rows.append((number, 'Other', *blank, '', '', _text(raw)))
        elif env is not None:
            rows.append((number, 'Environment', *blank, _text(env[0]), _text(env[1]), _text(raw)))
        else:
            job = split_job(line, system)
            if job is None:
                rows.append((number, 'Other', *blank, '', '', _text(raw)))
                continue
            if len(job[7]) >= _MAX_COMMAND - 1:
                counts[LONG_COMMAND] += 1
            rows.append((number, 'Job', *(_text(part) for part in job), '', '', _text(raw)))
    if too_long:
        counts[TOO_LONG] += 1
    return rows


def crontab_kind(relative):
    """User, System or cron.d for a path cron reads crontabs from, else None."""
    parent, name = os.path.split(relative.replace('\\', '/'))
    parent = '/' + parent.strip('/')
    if parent.endswith('/var/spool/cron/crontabs'):
        return 'User'
    if parent.endswith('/etc') and name == 'crontab':
        return 'System'
    if parent.endswith('/etc/cron.d'):
        return 'cron.d'
    return None


@artifact_processor
def linuxCrontabEntries(context):
    data_headers = (('File Modified', 'datetime'), 'Installed On (Header)', 'Crontab', 'Line', 'Kind', 'Minute',
                    'Hour', 'Day of Month', 'Month', 'Day of Week', 'Special', 'User', 'Command', 'Variable', 'Value',
                    'Line as Written', 'Installed From (Header)', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    seeker = seeker_of(context)
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        relative = context.get_relative_path(path)
        kind = crontab_kind(relative)
        if kind is None:
            counts['files in folders below the crontab folders, which cron does not read'] += 1
            continue
        link = recorded_link(seeker, path) if seeker else None
        if link is not None:
            counts['symbolic links, not followed'] += 1
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        name = os.path.basename(relative)
        if kind != 'System' and (name.startswith('.') or (kind == 'cron.d' and not _CLASSICAL.fullmatch(name))):
            counts[SKIPPED_NAME] += 1
        rows = crontab_rows(data, kind != 'User', counts)
        if not rows:
            continue
        modified = recorded_time(seeker, path, None) if seeker else ''
        installed_on, installed_from = installed_header(data.split(b'\n', 3)[:3]) if kind == 'User' else ('', '')
        owner = name if kind == 'User' else None
        for row in rows:
            number, kind_of_line, *middle, raw = row
            if owner is not None and kind_of_line == 'Job':
                middle[6] = owner
            data_list.append((modified, installed_on, kind, number, kind_of_line, *middle, raw, installed_from,
                              relative))
        read.append(path)
    if counts:
        logfunc('Crontab Entries: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
