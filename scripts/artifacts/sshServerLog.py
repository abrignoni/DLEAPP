"""Messages the OpenSSH server wrote to a Linux syslog file (auth.log or secure) and to the systemd journal, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sshServerLog": {
        "name": "SSH Server Log",
        "description": "Messages sshd logged to auth.log or secure and their rotations, with the result, method, "
                       "user, remote address and any key of each SSH protocol 2 login attempt it logged split out.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "SSH",
        "notes": "Reads /var/log/auth.log and its numbered rotations and /var/log/secure and its numbered or dated"
                 " rotations, gzip ones included, named in the report's located-at line, and reports each line "
                 "whose program is sshd, sshd-session or sshd-auth, in file order; Line is its line number in the "
                 "file and Source File the file. Lines of other programs, and lines in neither syslog file format "
                 "described below, are counted in the run log and not reported. honeynet_fc7_debian5's "
                 "/etc/rsyslog.conf routes the auth and authpriv facilities to auth.log, and both tested Linux "
                 "images, one Debian and one Ubuntu, hold sshd's lines there. Fedora writes the authpriv facility "
                 "to secure (rsyslog.conf, "
                 "https://src.fedoraproject.org/rpms/rsyslog/blob/6acade802d1e5b33cb723af1761371f9a3a656bb/f/rsyslog.conf#_52)"
                 " and its openssh package sets sshd's facility to authpriv (the 50-redhat.conf its patch adds, "
                 "https://src.fedoraproject.org/rpms/openssh/blob/e700631185906986adc4a888f1b62d4dce311118/f/0011-openssh-8.7p1-redhat.patch#_114);"
                 " no tested image carries a secure file. SSH Server Log (journal) reports the sshd messages kept "
                 "only in the systemd journal, and messages written to another file are not read. OpenSSH 9.8 "
                 "split sshd into a listener and a per-connection "
                 "sshd-session, after which some messages carry the name sshd-session (release notes, "
                 "https://www.openssh.org/txt/release-9.8, lines 120 to 131), and 10.0 moved authentication into "
                 "sshd-auth, from which some messages may come (https://www.openssh.org/txt/release-10.0, lines 33"
                 " to 44). A line is read in either of rsyslog's two file formats: RSYSLOG_FileFormat, whose time "
                 "is an RFC 3339 time with any fractional seconds and a UTC offset or Z, followed by the host "
                 "name, the tag and the message, and RSYSLOG_TraditionalFileFormat, whose time is a month, day and"
                 " time with no year and no zone (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5,"
                 " tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5,"
                 " and the two time writers in runtime/datetime.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/runtime/datetime.c#L879-L943"
                 " and "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/runtime/datetime.c#L956-L979)."
                 " rsyslog writes a file in the first form unless configured otherwise (tools/omfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/omfile.c#L333-L340),"
                 " and Fedora's rsyslog.conf selects the second "
                 "(https://src.fedoraproject.org/rpms/rsyslog/blob/6acade802d1e5b33cb723af1761371f9a3a656bb/f/rsyslog.conf#_15)."
                 " Time as Recorded is the time as the line stores it. Time (UTC) is an RFC 3339 time converted "
                 "with the offset its own line carries; the sshd lines of ubuntu2604_arm64_triage carry four "
                 "offsets (-04:00 on 2,023, +04:00 on 123, -07:00 on 9 and +00:00 on 5), all four of them within "
                 "auth.log.3.gz. A time in the traditional form has no year and no zone and is not converted, so "
                 "Time (UTC) is blank for it; it is blank on every row of honeynet_fc7_debian5, whose "
                 "/etc/rsyslog.conf selects that form and whose /etc/timezone names Europe/Paris. Hostname, the "
                 "host name the line stores, held the same value on every row of each tested image. Program and "
                 "Process ID are the program name and process ID in the line's tag, and Program held the same "
                 "value, sshd, on every row of honeynet_fc7_debian5. Login Result, Method, User, Invalid User, "
                 "Remote Address and Remote Port are split out of a message in the form sshd writes for a login "
                 "attempt, '<result> <method> for [invalid user ]<user> from <address> port <port> ssh2[: "
                 "<details>]' (auth.c at 10.2p1, "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/auth.c#L263-L303,"
                 " and at 5.1p1, "
                 "https://github.com/openssh/openssh-portable/blob/8f42e9b75a55401fa9dfdf14d49fbe5396c6ce92/auth.c#L247-L275):"
                 " Login Result is the result (Accepted, Failed, Postponed or Partial), Method the method with any"
                 " submethod after a slash, and Invalid User is Yes when the message carries 'invalid user'. A "
                 "protocol 1 login, which 5.1p1 writes without 'ssh2' (auth1.c, "
                 "https://github.com/openssh/openssh-portable/blob/8f42e9b75a55401fa9dfdf14d49fbe5396c6ce92/auth1.c#L363),"
                 " is not split. For the publickey and hostbased methods, Key Type and Key Fingerprint are the "
                 "first two words of the details, the key's type and fingerprint as sshd wrote them "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/auth.c#L226-L261);"
                 " the fingerprint is taken with the hash sshd's FingerprintHash names, SHA256 unless set to md5 "
                 "(sshd_config.5, "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd_config.5#L684-L691),"
                 " and Key Type names the type as sshd does (ED25519 where authorized_keys stores ssh-ed25519). "
                 "For 'Invalid user <user> from <address> port <port>' "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/auth.c#L495-L496),"
                 " which 5.1p1 writes without the port "
                 "(https://github.com/openssh/openssh-portable/blob/8f42e9b75a55401fa9dfdf14d49fbe5396c6ce92/auth.c#L530-L531),"
                 " User, Invalid User, Remote Address and Remote Port are filled the same way. The fields are also"
                 " read from inside a message the monitor process relays with ' [preauth]' or ' [postauth]' "
                 "appended (monitor.c, "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/monitor.c#L480-L481),"
                 " and from inside 'message repeated <n> times: [<message>]', the line rsyslog writes for n more "
                 "identical messages from one process, stamped with the last one's time (runtime/ratelimit.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/runtime/ratelimit.c#L44-L101);"
                 " no tested file held such a line. Those columns are blank for every other message. At its "
                 "default INFO level sshd writes a failed attempt only when the user is invalid, when the method "
                 "is password, or once the connection's failures reach half of MaxAuthTries, and writes other "
                 "failed attempts, such as a public key the account does not accept, at VERBOSE "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/auth.c#L275-L280"
                 " at 10.2p1, "
                 "https://github.com/openssh/openssh-portable/blob/8f42e9b75a55401fa9dfdf14d49fbe5396c6ce92/auth.c#L256-L261"
                 " at 5.1p1), so a missing Failed row is not evidence that no attempt failed. A row reports what "
                 "sshd logged, including the address it recorded for the connection. On ubuntu2604_arm64_triage, "
                 "whose dpkg.log records openssh-server 1:10.2p1, 2,160 of the 4,277 lines of auth.log and its "
                 "three rotations are sshd's, 2,130 from sshd-session and 30 from sshd: 418 Accepted rows (416 "
                 "publickey, each with the one ED25519 fingerprint that SSH Authorized Keys reports for the "
                 "account's key, and 2 password), 5 Failed rows and 2 Invalid user rows. Each Accepted row shares "
                 "its Process ID with the one 'pam_unix(sshd:session): session opened' line after it in the same "
                 "file, and 417 of the 418 with a 'session closed' line, while every 'Disconnected from user' line"
                 " came from another process. On honeynet_fc7_debian5, whose /var/lib/dpkg/status records "
                 "openssh-server 1:5.1p1, 74 of the 105 lines are sshd's: 32 Failed rows for one invalid user from"
                 " one address (24 password and 8 none) and 8 Invalid user rows with no port. Key Type and Key "
                 "Fingerprint were blank on every row of honeynet_fc7_debian5, whose login messages name only the "
                 "password and none methods.",
        "paths": ('*/var/log/auth.log', '*/var/log/auth.log.[0-9]*',
                  '*/var/log/secure', '*/var/log/secure[.-][0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 74 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 2225 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 2315 rows",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 2311 rows",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 2160 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "sshServerLogJournal": {
        "name": "SSH Server Log (journal)",
        "description": "Entries logged to the systemd journal under the names sshd, sshd-session and sshd-auth, "
                       "with the result, method, user, remote address and any key of each SSH protocol 2 login "
                       "attempt they record split out, and the boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "SSH",
        "notes": "One row per entry in the systemd journal files under var/log/journal and run/log/journal whose "
                 "SYSLOG_IDENTIFIER is sshd, sshd-session or sshd-auth, the names SSH Server Log reads, read with "
                 "the same reader as systemd Journal (scripts/systemd_journal.py) and in the way Cron Log "
                 "(journal) reads its entries: journald keeps the name in a syslog line's tag as "
                 "SYSLOG_IDENTIFIER, the process ID in its brackets as SYSLOG_PID and the text after the tag as "
                 "MESSAGE (Reference: systemd, 'journald-syslog.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L204-L262, "
                 "with the fields written at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-syslog.c#L433-L464), "
                 "the first value of a field an entry holds more than once is read, an entry that more than one "
                 "file holds is read once, and rows are in order of Time (UTC), then boot ID, time since boot and "
                 "sequence number. Program is SYSLOG_IDENTIFIER, Process ID SYSLOG_PID and Message MESSAGE, and "
                 "Login Result, Method, User, Invalid User, Remote Address, Remote Port, Key Type and Key "
                 "Fingerprint are read from Message as SSH Server Log reads them, with the meanings and references "
                 "given there. Time (UTC) is the entry's realtime, the time journald received it (Reference: "
                 "systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651); "
                 "Hostname is the entry's _HOSTNAME field, Boot ID the boot the entry names and Source File the "
                 "journal file the entry was read from. The journal does not validate SYSLOG_IDENTIFIER or "
                 "SYSLOG_PID "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L127-L131), "
                 "so any process can send an entry under these names: each of the three tested journals holds one "
                 "row that is the known entry described for systemd Journal, which a python3 process sent with "
                 "SYSLOG_IDENTIFIER=sshd over the journal's own transport, and it is the only row whose Process ID "
                 "is blank, the entry carrying no SYSLOG_PID. Entries of other programs, entries read a second "
                 "time, and journal files that could not be read or whose header sets an incompatible flag the "
                 "reader does not know are counted in the run log and not reported. ubuntu2604_arm64_journal holds "
                 "2,450 rows, ubuntu2604_arm64_usb 2,705 and ubuntu2604_arm64_usbstorage 4,708, from 8 boots on "
                 "each, with 473, 524 and 924 Accepted rows; Key Fingerprint held one value on the rows where it "
                 "is filled, and Hostname held one value on every row of each tested image. Four captures of "
                 "auth.log from the VM these three journals come from were compared with this artifact, matching "
                 "rows on Program, Process ID and Message with times less than 1 s apart: every one of the 2,225 "
                 "SSH Server Log rows of ubuntu2604_arm64_authlog and the 2,160 of ubuntu2604_arm64_triage was "
                 "matched by a row of ubuntu2604_arm64_journal, the 2,311 of ubuntu2604_arm64_shutdown by rows of "
                 "ubuntu2604_arm64_usbstorage and the 2,315 of ubuntu2604_arm64_cron by rows of "
                 "ubuntu2604_arm64_usb. Between each capture's first and last sshd line the journal holds 5 rows "
                 "with no auth.log line, each sshd's message that it received a signal and was terminating, logged "
                 "within 0.03 s of systemd's Stopping rsyslog.service entry; the other journal rows with no match "
                 "are later than the capture's last sshd line. On every matched row the two times were within "
                 "0.007 s of each other. No tested image held an entry in two files, and the unit tests exercise "
                 "it. No member of the other 28 tested images matches the declared paths.",
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
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 2450 rows",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 2705 rows",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 4708 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import journal_entries, journal_sources, program_lines, read_file, read_journals

# The program names sshd logs under: sshd, the per-connection sshd-session from OpenSSH 9.8 and the
# pre-authentication sshd-auth from 10.0.
_PROGRAMS = ('sshd', 'sshd-session', 'sshd-auth')
# rsyslog writes a run of identical messages from one process once, as this.
_REPEATED = re.compile(r'message repeated (\d+) times: \[ ?(.*)\]', re.DOTALL)
# The monitor process appends the stage to a message it relays from the unprivileged process.
_STAGE = re.compile(r'(.*) \[(?:preauth|postauth)\]', re.DOTALL)
# auth.c auth_log(): "<result> <method>[/<submethod>] for [invalid user ]<user> from <address>
# port <port> ssh2[: <extra>]".
_AUTH = re.compile(r'(Accepted|Failed|Postponed|Partial) (\S+) for (invalid user )?(.*) from (\S+) port (\d+)'
                   r' ssh2(?:: (.*))?', re.DOTALL)
# auth.c getpwnamallow(): "Invalid user <user> from <address>", with " port <port>" in later releases.
_INVALID = re.compile(r'Invalid user (.*) from (\S+?)(?: port (\d+))?', re.DOTALL)
# Methods whose extra text begins with the key type and fingerprint (auth.c format_method_key()).
_KEY_METHODS = ('publickey', 'hostbased')


def login_fields(message):
    """(result, method, user, invalid user, address, port, key type, key fingerprint) from an sshd
    message, all blank for a message that is not a login attempt."""
    repeated = _REPEATED.fullmatch(message)
    if repeated:
        message = repeated.group(2)
    staged = _STAGE.fullmatch(message)
    if staged:
        message = staged.group(1)
    match = _AUTH.fullmatch(message)
    if match:
        result, method, invalid, user, address, port, extra = match.groups()
        key_type = fingerprint = ''
        if method.split('/')[0] in _KEY_METHODS and extra:
            words = extra.split(' ')
            if len(words) > 1:
                key_type, fingerprint = words[0], words[1].rstrip(',')
        return result, method, user, 'Yes' if invalid else '', address, port, key_type, fingerprint
    match = _INVALID.fullmatch(message)
    if match:
        user, address, port = match.groups()
        return '', '', user, 'Yes', address, port or '', '', ''
    return ('',) * 8


def log_rows(data, counts):
    """(time, time as recorded, host, program, process ID, message, line) for each sshd line."""
    return [(when, stamp, host, program, pid, message, number)
            for number, when, stamp, host, program, pid, message in program_lines(data, _PROGRAMS, counts)]


@artifact_processor
def sshServerLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Hostname', 'Program', 'Process ID',
                    'Message', 'Login Result', 'Method', 'User', 'Invalid User', 'Remote Address',
                    'Remote Port', 'Key Type', 'Key Fingerprint', 'Line', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        rows = log_rows(data, problems)
        relative = context.get_relative_path(path)
        for when, stamp, host, program, pid, message, number in rows:
            data_list.append((when, stamp, host, program, pid, message, *login_fields(message), number,
                              relative))
        if rows:
            read.append(path)
    if problems:
        logfunc('SSH Server Log: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def journal_log_rows(journals, counts):
    """(time, host, program, process ID, message, login fields..., boot ID, source) for each sshd entry in these journal
    files, oldest first; journals: (relative path, JournalFile)."""
    return [(when, host, program, pid, message, *login_fields(message), boot, relative)
            for when, host, program, pid, message, boot, relative in journal_entries(
                journals, lambda program: program in _PROGRAMS, counts)]


@artifact_processor
def sshServerLogJournal(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'Process ID', 'Message', 'Login Result',
                    'Method', 'User', 'Invalid User', 'Remote Address', 'Remote Port', 'Key Type', 'Key Fingerprint',
                    'Boot ID', 'Source File')
    counts = Counter()
    journals, staged = read_journals(context, counts)
    data_list = journal_log_rows(journals, counts)
    if counts:
        logfunc('SSH Server Log (journal): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, journal_sources(data_list, staged)
