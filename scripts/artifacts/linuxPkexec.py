"""Commands pkexec logged in a Linux syslog file (auth.log or secure), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxPkexec": {
        "name": "pkexec Commands",
        "description": "Commands pkexec logged in auth.log or secure and their rotations, with the user who ran pkexec, "
                       "its message, the user the command was to run as, the terminal, the working directory and the "
                       "command.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Command Line (pkexec)",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated "
                 "rotations, gzip ones included, and reports each line in which pkexec recorded a command it was "
                 "asked to run, in file order; Line is its line number in the file and Source File the file, and "
                 "the files that held a row are named in the report's located-at line. Other lines, among them the "
                 "PAM lines pkexec's modules write (PAM Sessions reports the session ones), and lines in neither "
                 "syslog file format described below, are counted in the run log and not reported. Messages kept "
                 "only in the systemd journal, or written to another file, are not read. A line is read in either "
                 "of rsyslog's two file formats, an RFC 3339 time with a UTC offset (rsyslog 8.2512.0, "
                 "tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5), "
                 "followed by the host name, the tag and the message. Time as Recorded is the time as the line "
                 "stores it, and Time (UTC) is an RFC 3339 time converted with the offset its own line carries, "
                 "blank for a time with no year and no zone. Hostname is the host name the line stores, and it "
                 "held the same value on every row of each tested image; Process ID is the process ID in the "
                 "line's tag, pkexec's own. pkexec writes \"<user>: <message> [USER=<user>] [TTY=<terminal>] "
                 "[CWD=<directory>] [COMMAND=<command>]\" to the authpriv facility under the name pkexec (polkit "
                 "127, src/programs/pkexec.c, "
                 "https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L90-L133), "
                 "and every release checked from 0.96 to 127 (0.96, 0.105, 0.113, 0.116, 0.120 and 121 to 127) "
                 "writes the same form (0.96, "
                 "https://github.com/polkit-org/polkit/blob/83f280620c9f4f5a3021994f35b9c3baf193231c/src/programs/pkexec.c#L101). "
                 "User is the user who ran pkexec "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L621); "
                 "Message is the message; Run As is the user the command was to run as, root unless another was "
                 "named "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L635-L636); "
                 "TTY is the terminal on pkexec's standard input, or unknown "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L114-L116); "
                 "Working Directory is the directory pkexec was run from "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L628); "
                 "and Command is the program and its arguments joined with single spaces, or the user's shell when "
                 "no program was named "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L664-L731), "
                 "so an argument holding a space cannot be told from two. Working Directory ends at the first \"] "
                 "[COMMAND=\" in the line and Command runs to its final \"]\". In 127 the messages are \"Executing "
                 "command\", written after the PAM session opens and just before pkexec starts the command "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L1041-L1106), "
                 "\"Error executing command as another user: Not authorized\" and \"Error executing command as "
                 "another user: Request dismissed\", written when authorization is refused or its prompt dismissed "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L960-L975), "
                 "and two refusals of the environment, \"The value for the SHELL variable was not found in the "
                 "/etc/shells file\" and \"The value for environment variable <name> contains suspicious content\" "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L438-L453). "
                 "When no authentication agent is found pkexec only prints its refusal and writes no line "
                 "(https://github.com/polkit-org/polkit/blob/9e4894c969eecf26a3ba762f4f7a268aa0fb3e51/src/programs/pkexec.c#L956). "
                 "0.96 has no Request dismissed line "
                 "(https://github.com/polkit-org/polkit/blob/83f280620c9f4f5a3021994f35b9c3baf193231c/src/programs/pkexec.c), "
                 "which 0.105 has "
                 "(https://github.com/polkit-org/polkit/blob/7cb21aa77e0edf7fe1bc87eaf3d8d9a5a8e38746/src/programs/pkexec.c#L765-L766), "
                 "and before 121 the environment messages read \"was not found the /etc/shells file\" and \"contains "
                 "suscipious content\" (0.120, "
                 "https://github.com/polkit-org/polkit/blob/92b910ce2273daf6a76038f6bd764fa6958d4e8e/src/programs/pkexec.c#L406-L418). "
                 "On ubuntu2604_arm64_triage, whose dpkg.log records only polkit 127 builds of pkexec, auth.log "
                 "and its rotations hold 2 of these lines, both Executing command lines by the same user, run as "
                 "root with TTY unknown, and each is the line after a pam_unix session opened line for root that "
                 "pkexec wrote 0.003 seconds or less before it. ubuntu2604_arm64_authlog and "
                 "ubuntu2604_arm64_shutdown, later captures of the same logs, hold the same 2 rows. On "
                 "honeynet_fc7_debian5 auth.log holds no pkexec line.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (its auth.log holds no pkexec line)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 2 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 2 rows",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 2 rows",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import program_lines, read_file

_PROGRAM = 'pkexec'
# "<user who ran pkexec>: <message> [USER=<run as>] [TTY=<terminal>] [CWD=<directory>] [COMMAND=<command>]"
_LINE = re.compile(r"([^:]*): (.*?) \[USER=([^\]]*)\] \[TTY=([^\]]*)\] \[CWD=(.*?)\] \[COMMAND=(.*)\]", re.DOTALL)


def command_fields(message):
    """(user, message, run as, tty, working directory, command) from a pkexec line, or None."""
    match = _LINE.fullmatch(message)
    return match.groups() if match else None


def command_rows(data, counts):
    """(time, time as recorded, host, process ID, user, message, run as, tty, cwd, command, line) for each pkexec
    line of a syslog file in the form above; other lines are counted."""
    rows = []
    for number, when, stamp, host, _program, pid, message in program_lines(data, {_PROGRAM}, counts):
        fields = command_fields(message)
        if fields is None:
            counts['pkexec lines in other forms, not reported'] += 1
            continue
        rows.append((when, stamp, host, pid, *fields, number))
    return rows


@artifact_processor
def linuxPkexec(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Process ID', 'User', 'Message',
                    'Run As', 'TTY', 'Working Directory', 'Command', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = command_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('pkexec Commands: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
