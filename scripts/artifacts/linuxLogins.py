"""Login records Linux keeps in /var/log/wtmp and /var/log/lastlog, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxWtmp": {
        "name": "Login Records (wtmp)",
        "description": "Records read from /var/log/wtmp and its rotations, with the time, type, user, "
                       "terminal line and ID, host, IP address and process ID each one stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/wtmp and its numbered rotations, one row per reported "
                 "record in file order; a rotation compressed with gzip is read the same "
                 "way "
                 "(checked on a gzip copy of the tested file). Each record is glibc's "
                 "struct utmp "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/bits/utmp.h#L58-L89, "
                 "glibc 2.42; the same header, apart from its copyright line, is the glibc "
                 "2.43 one installed on the VM ubuntu2604_arm64_logins was taken from), read "
                 "little-endian. ut_session "
                 "and ut_tv are 32-bit fields where glibc sets __WORDSIZE_TIME64_COMPAT32, "
                 "as it does on x86 "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/sysdeps/x86/bits/wordsize.h#L11), "
                 "making 384-byte records, and 64-bit fields where it does not, as on "
                 "AArch64 "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/sysdeps/aarch64/bits/wordsize.h#L21), "
                 "making 400-byte records. The file's size picks the layout; when both "
                 "sizes or neither divide it, the layout under which more records read as "
                 "a valid, non-empty record is used, and a file for which neither layout "
                 "reads better is counted in the run log and not read. "
                 "ubuntu2604_arm64_logins has 400-byte records. honeynet_fc7_debian5 (Debian "
                 "5.0.7 on i386, glibc 2.7) has 384-byte records, and its 257 rows equal a "
                 "separate decode of that layout. Time (UTC) is ut_tv, seconds and "
                 "microseconds since "
                 "1970-01-01 UTC, which glibc describes as the time the entry was made "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/bits/utmp.h#L72-L85); "
                 "a ut_tv of zero, or one outside the dates the report can hold, is left "
                 "blank. Type is ut_type named as glibc defines its values "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/bits/utmp.h#L103-L115); "
                 "EMPTY records, records of a type glibc does not define and any bytes after "
                 "the last whole record are counted in the run log and not reported. User, "
                 "Line, Host and ID are ut_user, ut_line, "
                 "ut_host and ut_id as stored, each ending at its first NUL byte and read as "
                 "UTF-8 (a byte that is not valid UTF-8 shows as the replacement character), "
                 "and PID is ut_pid. IP Address is ut_addr_v6: OpenSSH 10.2p1 writes an IPv4 "
                 "address in its first word, an IPv6 address in all 16 bytes and an "
                 "IPv4-mapped IPv6 address as IPv4 "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/loginrec.c#L686-L703), "
                 "so the field is blank when all 16 bytes are zero, IPv4 when only its first "
                 "word is set and IPv6 otherwise. ut_exit, ut_session and the reserved bytes "
                 "are not "
                 "reported. utmp(5) says the wtmp file records all logins and logouts, a "
                 "record with a null username marking a logout "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/utmp.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n254, "
                 "lines 254 to 261), and OpenSSH's code writes a DEAD_PROCESS record for a "
                 "logout "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/loginrec.c#L651-L661). "
                 "On ubuntu2604_arm64_logins (Ubuntu 26.04, aarch64) the file held 12 "
                 "records: 2 LOGIN_PROCESS on tty1, 5 USER_PROCESS on tty2 with Host local "
                 "and 5 USER_PROCESS on pts/0 for SSH sessions, 4 of them the known "
                 "sessions started for the test from 10.211.55.2 at 06:00:41, 06:00:49 and "
                 "06:01:00 UTC and from fdb2:2c26:f4e4::1 at 06:05:54 UTC on 2026-09-28, "
                 "each record within a second of the time the session was started. It held "
                 "no DEAD_PROCESS, BOOT_TIME or RUN_LVL record, and closing each known "
                 "session added no record, so on that release this file shows when a "
                 "session started and not when it ended or when the system booted. On "
                 "honeynet_fc7_debian5 the file held 257 records from 2011-01-18 08:31:29 to "
                 "2011-02-06 14:04:39 UTC: 100 DEAD_PROCESS, 63 INIT_PROCESS, 48 "
                 "LOGIN_PROCESS, 22 RUN_LVL, 16 USER_PROCESS, each for root on a tty line, "
                 "and 8 BOOT_TIME. IP Address was blank on every row of that image, and its "
                 "last record falls in the second The Sleuth Kit's istat reports as the "
                 "file's modification time.",
        "paths": ('*/var/log/wtmp', '*/var/log/wtmp.[0-9]*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 257 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 12 rows",
        },
    },
    "linuxLastlog": {
        "name": "Last Login per Account (lastlog)",
        "description": "The record /var/log/lastlog keeps for each user ID that has one: the time, "
                       "terminal line and host of that ID's last recorded login, with the account "
                       "name /etc/passwd gives the ID on the same system.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Logins (Linux)",
        "notes": "Reads /var/log/lastlog, one row per user ID whose record is not all zero; "
                 "bytes after the last whole record are counted in the run log and not read. "
                 "OpenSSH 10.2p1 writes a user's record only when it records a login, "
                 "setting ll_time to the time it does so "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/loginrec.c#L429-L437, "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/loginrec.c#L1593), "
                 "and finds the record at the user ID times the record size "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/loginrec.c#L1552-L1553), "
                 "so UID is the record's position in the file, and the file keeps one "
                 "record per UID, each row that UID's latest recorded login only. Each "
                 "record is glibc's struct lastlog "
                 "(https://github.com/bminor/glibc/blob/d2097651cc57834dbfcaa102ddfacae0d86cfb66/bits/utmp.h#L36-L45): "
                 "ll_time is 32-bit where glibc sets __WORDSIZE_TIME64_COMPAT32 (x86, "
                 "292-byte records) and 64-bit where it does not (AArch64, 296-byte "
                 "records), and the layout is chosen as in Login Records (wtmp). "
                 "ubuntu2604_arm64_logins has 296-byte records and honeynet_fc7_debian5 "
                 "292-byte ones. Last Login (UTC) is ll_time, seconds "
                 "since 1970-01-01 UTC, left blank when it is zero or outside the dates the "
                 "report can hold, and Line and Host are ll_line and ll_host, read as the "
                 "wtmp text fields are. Account is the name on every /etc/passwd line of the "
                 "same "
                 "system whose UID field matches, joined with commas, each line read as "
                 "the seven colon-separated fields passwd(5) gives "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/passwd.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n60, "
                 "lines 60 to 65); lines beginning with #, + or - are not used. Account is "
                 "blank for a UID no line holds, and the run log says so when the same "
                 "system's etc/passwd was not found. On ubuntu2604_arm64_logins the "
                 "file held 1,001 records and 1 that was not empty, UID 1000 (parallels), "
                 "whose time and host equal the latest known SSH session's, 2026-09-28 "
                 "06:05:54 UTC from fdb2:2c26:f4e4::1. On honeynet_fc7_debian5 the file held "
                 "1,001 records and 1 that was not empty, UID 0 (root) on tty1 at 2011-02-06 "
                 "14:04:39 UTC, the same second as the last two USER_PROCESS records for root "
                 "on tty1 in that image's wtmp and as the file's modification time The Sleuth "
                 "Kit's istat reports.",
        "paths": ('*/var/log/lastlog', '*/etc/passwd'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user-check",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no var/log/lastlog)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 1 row",
        },
    },
}

import gzip
import ipaddress
import os
import struct
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

# glibc's struct utmp (bits/utmp.h): ut_type, two bytes of alignment, ut_pid, ut_line[32],
# ut_id[4], ut_user[32], ut_host[256], ut_exit (two shorts, not reported), ut_session and ut_tv,
# ut_addr_v6[4] and 20 reserved bytes. ut_session and ut_tv are 32-bit fields where glibc sets
# __WORDSIZE_TIME64_COMPAT32 (x86) and 64-bit fields where it does not (AArch64), which makes
# records of 384 and 400 bytes; the 64-bit form ends with 4 bytes of alignment.
_UTMP_LAYOUTS = (
    struct.Struct('<h2xi32s4s32s256s4sqqq16s20s4x'),
    struct.Struct('<h2xi32s4s32s256s4siIi16s20s'),
)
_TYPES = {0: 'EMPTY', 1: 'RUN_LVL', 2: 'BOOT_TIME', 3: 'NEW_TIME', 4: 'OLD_TIME', 5: 'INIT_PROCESS',
          6: 'LOGIN_PROCESS', 7: 'USER_PROCESS', 8: 'DEAD_PROCESS', 9: 'ACCOUNTING'}
# glibc's struct lastlog: ll_time, 32-bit or 64-bit as above, ll_line[32] and ll_host[256].
_LASTLOG_LAYOUTS = (struct.Struct('<q32s256s'), struct.Struct('<I32s256s'))
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_MAX_SECONDS = 2 ** 34


def _text(field):
    return field.split(b'\x00', 1)[0].decode('utf-8', errors='replace')


def _time(seconds, microseconds=0):
    if not seconds and not microseconds:
        return ''
    try:
        return _EPOCH + timedelta(seconds=seconds, microseconds=microseconds)
    except OverflowError:
        return ''


def _address(raw):
    """ut_addr_v6 as text: an IPv4 address uses only the first of its four words."""
    if not any(raw):
        return ''
    if not any(raw[4:]):
        return str(ipaddress.IPv4Address(raw[:4]))
    return str(ipaddress.IPv6Address(raw))


def _choose(layouts, data, holds):
    """The layout for data: the one whose record size divides its length, or, when both or
    neither do, the one under which more whole records hold() a valid, non-empty record;
    None when neither layout does better."""
    if not data:
        return None
    dividing = [layout for layout in layouts if not len(data) % layout.size]
    if len(dividing) == 1:
        return dividing[0]
    scores = [(sum(holds(layout.unpack_from(data, offset))
                   for offset in range(0, len(data) - layout.size + 1, layout.size)), layout)
              for layout in (dividing or layouts)]
    scores.sort(key=lambda pair: -pair[0])
    if scores[0][0] and (len(scores) == 1 or scores[0][0] > scores[1][0]):
        return scores[0][1]
    return None


def _utmp_holds(fields):
    return 1 <= fields[0] <= 9 and 0 <= fields[9] < 1_000_000 and 0 < fields[8] < _MAX_SECONDS


def utmp_layout(data):
    return _choose(_UTMP_LAYOUTS, data, _utmp_holds)


def utmp_records(data):
    """(rows, counts) for the whole records of data, or None when no single layout fits.
    A row is (time, type, user, line, host, address, pid, id); EMPTY records, records of a
    type glibc does not define and bytes after the last whole record are counted instead."""
    layout = utmp_layout(data)
    if layout is None:
        return None
    rows, counts = [], Counter()
    whole = len(data) - len(data) % layout.size
    if whole != len(data):
        counts['bytes after the last whole record, not read'] += len(data) - whole
    for offset in range(0, whole, layout.size):
        kind, pid, line, ident, user, host, _exit, _session, seconds, microseconds, address, _reserved = \
            layout.unpack_from(data, offset)
        if kind == 0:
            counts['EMPTY records, not reported'] += 1
            continue
        if kind not in _TYPES:
            counts['records of a type glibc does not define, not reported'] += 1
            continue
        rows.append((_time(seconds, microseconds), _TYPES[kind], _text(user), _text(line), _text(host),
                     _address(address), pid, _text(ident)))
    return rows, counts


def _read(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as handle:
        return handle.read()


def _lastlog_holds(fields):
    seconds, line, host = fields
    return 0 < seconds < _MAX_SECONDS and _printable(line) and _printable(host)


def _printable(field):
    text = field.split(b'\x00', 1)[0]
    return all(32 <= byte < 127 or byte >= 128 for byte in text) and not any(field[len(text):])


def lastlog_layout(data):
    return _choose(_LASTLOG_LAYOUTS, data, _lastlog_holds)


def passwd_names(data):
    """{uid: [names]} from the text of an /etc/passwd file."""
    names = {}
    for line in data.decode('utf-8', errors='replace').splitlines():
        if not line or line[0] in '#+-':
            continue
        parts = line.split(':')
        if len(parts) < 7 or not parts[2].isdigit():
            continue
        names.setdefault(int(parts[2]), []).append(parts[0])
    return names


@artifact_processor
def linuxWtmp(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Type', 'User', 'Line', 'Host', 'IP Address', 'PID', 'ID',
                    'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        relative = context.get_relative_path(path)
        try:
            data = _read(path)
        except (OSError, EOFError):
            problems['files that could not be read'] += 1
            continue
        result = utmp_records(data)
        if result is None:
            problems['files no single utmp record layout fits, not read'] += 1
            continue
        rows, counts = result
        problems.update(counts)
        data_list.extend(row + (relative,) for row in rows)
        read.append(path)
    if problems:
        logfunc('Login Records (wtmp): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxLastlog(context):
    data_headers = (('Last Login (UTC)', 'datetime'), 'Account', 'UID', 'Line', 'Host')
    data_list = []
    read = []
    problems = Counter()
    files = [str(p) for p in context.get_files_found() if not os.path.isdir(p)]
    passwd = {os.path.normpath(p): p for p in files if os.path.basename(p) == 'passwd'}
    for path in sorted(p for p in files if os.path.basename(p) == 'lastlog'):
        try:
            data = _read(path)
        except OSError:
            problems['files that could not be read'] += 1
            continue
        layout = lastlog_layout(data)
        if layout is None:
            problems['files no single lastlog record layout fits, not read'] += 1
            continue
        accounts = os.path.normpath(os.path.join(os.path.dirname(path), '..', '..', 'etc', 'passwd'))
        names = {}
        if accounts in passwd:
            try:
                names = passwd_names(_read(passwd[accounts]))
            except OSError:
                problems['passwd files that could not be read'] += 1
        else:
            problems['lastlog files with no etc/passwd beside them, so no account names'] += 1
        before = len(data_list)
        if len(data) % layout.size:
            problems['bytes after the last whole record, not read'] += len(data) % layout.size
        for uid in range(len(data) // layout.size):
            seconds, line, host = layout.unpack_from(data, uid * layout.size)
            if not seconds and not any(line) and not any(host):
                continue
            data_list.append((_time(seconds), ', '.join(names.get(uid, [])), uid, _text(line), _text(host)))
        if len(data_list) > before:
            read.append(path)
            if accounts in passwd:
                read.append(passwd[accounts])
    if problems:
        logfunc('Last Login per Account (lastlog): ' + ', '.join(
            f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
