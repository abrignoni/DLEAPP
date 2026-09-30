"""Records the Linux audit daemon (auditd) wrote to /var/log/audit/audit.log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxAuditLog": {
        "name": "Audit Log (auditd)",
        "description": "Records auditd wrote to audit.log and its rotations: logins, authentications, sessions, sudo "
                       "commands, account and group changes, services and system calls, with the account, program "
                       "and command each record names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/audit/audit.log and its numbered rotations, gzip ones included, and reports one row"
                 " per record, in line order, file by file in name order; Line is its line number in the file and "
                 "Source File the file, and the files that held a row are named in the report's located-at line. "
                 "Non-empty lines in no audit record form are counted in the run log and not reported. auditd writes"
                 " each record as type=<type> msg=<message>, preceded by node=<name> when it is set to name the "
                 "node, and replaces a line feed inside it with a space (audit 3.1.5, src/auditd-event.c, "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/src/auditd-event.c#L298-L310),"
                 " and the kernel begins each message with audit(<seconds>.<milliseconds>:<serial>): (Linux 5.14, "
                 "kernel/audit.c, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L1871-L1872)."
                 " Time (UTC) is those seconds and milliseconds since 1970 in UTC, the time the kernel stamped the "
                 "record; Serial is the serial number, which the records of one event share; Type is the record type"
                 " as stored; and Node is the node name, blank on every row of the tested image, whose auditd wrote "
                 "none. In its ENRICHED log format auditd adds, after the record, the character 0x1D and its own "
                 "reading of the record's fields (src/auditd-event.c, "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/src/auditd-event.c#L323;"
                 " lib/libaudit.h, "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/libaudit.h#L509):"
                 " Enriched is that text as stored, and Record is the record's fields as stored, without its type, "
                 "time and serial. auditd makes that reading when it writes the record, from the accounts the system"
                 " held then: on rocky98_arm64_known the ADD_GROUP record of groupadd reads ID=\"dleappgrp\" and the "
                 "DEL_GROUP record of groupdel, written once the group was gone, ID=\"unknown(1001)\" for the same ID."
                 " A message a program sends (types 1100 to 1199 and 2100 to 2999, include/uapi/linux/audit.h, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/include/uapi/linux/audit.h#L75-L80)"
                 " is logged as the kernel's pid, uid, auid and ses fields and the program's own text in msg='...' "
                 "(kernel/audit.c, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L1056-L1073,"
                 " "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L2110-L2116"
                 " and "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L1343-L1367)."
                 " Each column is the first field of its name in the record, those outside msg='...' read before "
                 "those inside, and is blank when the record has none: Process ID is pid, UID uid, Login UID auid, "
                 "Session ses, Operation op, Account acct, ID id, Executable exe, Command cmd, Process Title "
                 "proctitle, Hostname hostname, Address addr, Terminal terminal and Result res. A Login UID or "
                 "Session of 4294967295 is the kernel's value for none set (include/uapi/linux/audit.h, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/include/uapi/linux/audit.h#L496-L497),"
                 " and Enriched writes such a Login UID as AUID=\"unset\". The library writes ? for a hostname or "
                 "terminal it does not have "
                 "(https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L499-L501)."
                 " The audit library writes acct, exe and a command's cmd in double quotes, or in hexadecimal when "
                 "the value holds a double quote, a character below 0x21 or 0x7F (lib/audit_logging.c, "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L85-L98,"
                 " "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L103-L123,"
                 " "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L489-L495,"
                 " "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L151-L166"
                 " and "
                 "https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L778-L795),"
                 " and a shadow-utils record names the account by its number in id when it gives no name "
                 "(https://github.com/linux-audit/audit-userspace/blob/f9f228e8661527fb0a064530b2dc22b78fe21c40/lib/audit_logging.c#L505-L506)."
                 " The kernel writes an executable's path and a process title the same way, also hexadecimal for a "
                 "byte above 0x7E (kernel/audit.c, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L2041-L2070"
                 " and "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/audit.c#L2168;"
                 " kernel/auditsc.c, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/auditsc.c#L1450-L1478)."
                 " So Account, Executable, Command and Process Title are shown with the quotes removed, and a value "
                 "written in hexadecimal is shown decoded as UTF-8, with any byte that is not valid UTF-8 written as"
                 " a \\x escape; every other column is shown as stored, quotes removed. Process Title is the "
                 "process's command line with the NUL bytes between its arguments shown as spaces, no longer than "
                 "the 128 bytes the kernel records (kernel/auditsc.c, "
                 "https://github.com/torvalds/linux/blob/7d2a07b769330c34b4deabeed939325c77a7ec2f/kernel/auditsc.c#L92)."
                 " The artifact does not join the records of an event into one row, interpret numeric fields such as"
                 " syscall and arch, or read audit records the systemd journal may hold. On rocky98_arm64_known "
                 "(Rocky Linux 9.8, audit 3.1.5) audit.log holds 635 records of 31 types from 570 events, from "
                 "18:43:41 to 18:55:51 UTC, and 571 carry Enriched text. The known steps listed in the README beside"
                 " that capture appear as records with Login UID 1000 from 18:52:02.00 to 18:52:02.22 UTC, between "
                 "the step log's first and last lines: ADD_GROUP and GRP_MGMT by groupadd; ADD_GROUP, ADD_USER and "
                 "USER_MGMT by useradd, with Account dleappk1 on those that name an account; USER_MGMT by usermod "
                 "and gpasswd; USER_AUTH, USER_ACCT, CRED_ACQ, USER_START, USER_END and CRED_DISP by su with Account"
                 " dleappk1; USER_CMD by sudo with Command /usr/bin/id; DEL_USER, USER_MGMT, DEL_GROUP and GRP_MGMT "
                 "by userdel; and DEL_GROUP and GRP_MGMT by groupdel. Command holds the three commands sudo ran "
                 "there, two of them written in hexadecimal, and Process Title is filled on the 32 PROCTITLE "
                 "records, 31 of them written in hexadecimal. Result is success on 507 rows, 1 on 26 (23 LOGIN and 3"
                 " CONFIG_CHANGE records), failed on 6 and blank on 96. Five of the 6 failed are the records of two "
                 "connections ssh-copy-id made at 18:48:23 UTC offering keys the VM did not yet hold, which secure "
                 "records as closed before authentication, as that README says: two USER_ERR (PAM:bad_ident), two "
                 "USER_LOGIN and one USER_AUTH (pubkey); the sixth is a CRED_ACQ (PAM:setcred) by "
                 "/usr/lib/systemd/systemd at 18:45:14 UTC. No member of the other 31 tested images matches the "
                 "declared paths.",
        "paths": ('*/var/log/audit/audit.log', '*/var/log/audit/audit.log.[0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 635 rows",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import read_file

# "[node=<name> ]type=<type> msg=audit(<seconds>.<milliseconds>:<serial>): <fields>"
_HEAD = re.compile(r'(?:node=(\S+) )?type=(\S+) msg=audit\((\d+)\.(\d{3}):(\d+)\):(?: (.*))?', re.S)
_FIELD = re.compile(r'(?:^| )([A-Za-z0-9_-]+)=("[^"]*"|\S*)')
_HEX = re.compile(r'(?:[0-9A-F]{2})+')
# Fields written as hex when they hold a character that needs encoding, and in quotes otherwise.
_ENCODED = ('acct', 'exe', 'cmd', 'proctitle')
_SEPARATOR = '\x1d'
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
NOT_AUDIT = 'non-empty lines in no audit record form, not reported'


def _text(data):
    return data.decode('utf-8', 'backslashreplace')


def record_fields(body):
    """Field name to value as stored, the first of each name, the record's own fields before those inside msg='...'."""
    start = body.find("msg='")
    end = body.rfind("'")
    if start != -1 and end > start + 4 and (start == 0 or body[start - 1] == ' '):
        parts = (body[:start] + body[end + 1:], body[start + 5:end])
    else:
        parts = (body,)
    fields = {}
    for part in parts:
        for name, value in _FIELD.findall(part):
            fields.setdefault(name, value)
    return fields


def field_value(fields, name):
    """A field's value: quotes removed, hex decoded for the fields written that way, otherwise as stored."""
    value = fields.get(name, '')
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    if name in _ENCODED and _HEX.fullmatch(value):
        decoded = _text(bytes.fromhex(value))
        return decoded.replace('\x00', ' ').rstrip(' ') if name == 'proctitle' else decoded
    return value


def audit_rows(data, counts):
    """(time, serial, type, pid, uid, auid, ses, op, acct, id, exe, cmd, proctitle, hostname, addr, terminal, res,
    record, enriched, node, line) for each record in an audit.log."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        line = _text(raw.rstrip(b'\r'))
        if not line.strip():
            continue
        record, _, enriched = line.partition(_SEPARATOR)
        match = _HEAD.fullmatch(record)
        if not match:
            counts[NOT_AUDIT] += 1
            continue
        node, kind, seconds, millis, serial, body = match.groups()
        body = body or ''
        try:
            when = _EPOCH + timedelta(seconds=int(seconds), milliseconds=int(millis))
        except OverflowError:
            counts['times that cannot be shown, Time (UTC) left blank'] += 1
            when = ''
        fields = record_fields(body)
        value = lambda name, f=fields: field_value(f, name)
        rows.append((when, serial, kind, value('pid'), value('uid'), value('auid'), value('ses'), value('op'),
                     value('acct'), value('id'), value('exe'), value('cmd'), value('proctitle'), value('hostname'),
                     value('addr'), value('terminal'), value('res'), body, enriched, node or '', number))
    return rows


@artifact_processor
def linuxAuditLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Serial', 'Type', 'Process ID', 'UID', 'Login UID', 'Session',
                    'Operation', 'Account', 'ID', 'Executable', 'Command', 'Process Title', 'Hostname', 'Address', 'Terminal',
                    'Result', 'Record', 'Enriched', 'Node', 'Line', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = read_file(path)
        except (OSError, EOFError):
            counts['files that could not be read'] += 1
            continue
        rows = audit_rows(data, counts)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc('Audit Log (auditd): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
