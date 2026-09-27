"""The utmpx file macOS keeps for its current logins, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosUtmpx": {
        "name": "Current Logins (utmpx)",
        "description": "The entries in /var/run/utmpx, the file macOS keeps for its current logins: "
                       "the time recorded in each entry, its type (boot, user process, dead "
                       "process, shutdown and others), user, terminal line, process ID, remote "
                       "host and ID, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Logins (macOS)",
        "notes": "Reads /var/run/utmpx (private/var/run/utmpx on a Mac), the file in which Apple's utmpx "
                 "manual page says currently logged in users are tracked "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.5#L53-L54), "
                 "one row per record in the file's order. On a 64-bit Mac Libc writes each record as "
                 "struct utmpx32 "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.h#L86-L95 "
                 "and "
                 "https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.c#L481-L483), "
                 "a 628-byte layout with natural alignment: ut_user (256 bytes), ut_id (4), ut_line (32), "
                 "ut_pid, ut_type, two bytes of padding, ut_tv as a 32-bit seconds and a 32-bit "
                 "microseconds field "
                 "(https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/bsd/sys/_types/_timeval32.h#L33-L37), "
                 "ut_host (256) and ut_pad (64); it is read little-endian. The first record is a SIGNATURE "
                 "record whose ut_user is utmpx-1.00, which Libc writes when it creates the file and "
                 "requires when it opens one "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.c#L84 "
                 "and "
                 "https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.c#L174-L207); "
                 "a file without it is counted in the run log and not read. Libc writes a new BOOT_TIME, "
                 "OLD_TIME, NEW_TIME or RUN_LVL record over the record of the same type, and a new "
                 "INIT_PROCESS, LOGIN_PROCESS, USER_PROCESS or DEAD_PROCESS record over the process record "
                 "with the same ut_id, and appends a record when none matches, as it does for every other "
                 "type "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.c#L285-L323 "
                 "and "
                 "https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/utmpx.c#L427-L479). "
                 "The file therefore keeps only the latest of those records for each type or ut_id, not a "
                 "history; a DEAD_PROCESS written over a USER_PROCESS leaves no record of that login here. "
                 "The history is in the Apple System Log, which ASL Login and Boot Records reports. Time "
                 "(UTC) is ut_tv, seconds and microseconds since 1970-01-01 UTC, which Apple's getutxent "
                 "manual page describes as the time the entry was created "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L107). "
                 "Event is ut_type named through Libc's utmpx.h "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/include/NetBSD/utmpx.h#L87-L100), "
                 "whose manual page describes BOOT_TIME as the time of a system boot, DEAD_PROCESS as a "
                 "session leader that exited, USER_PROCESS as a user process and SHUTDOWN_TIME as the time "
                 "of system shutdown "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L116-L138); "
                 "a type outside that list is reported as its number, and EMPTY records are counted in the "
                 "run log and not reported. User, Line, PID and Remote Host are ut_user, ut_line, ut_pid "
                 "and ut_host as stored, each text field ending at its first NUL byte, and the manual page "
                 "gives ut_user for a USER_PROCESS record as the login name of the user and ut_host as the "
                 "hostname of a remote user "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L169-L176). "
                 "ID (hex) is the four bytes of ut_id in hexadecimal. On dleapp_macos_bigsur the file held "
                 "3 records after the signature: BOOT_TIME at 2021-02-19 19:20:43 UTC, a DEAD_PROCESS on "
                 "the console line and SHUTDOWN_TIME at 19:53:32 UTC. Each record's time equals, to the "
                 "microsecond, the Entry Time of an ASL Login and Boot Records row on the same image, and "
                 "that store also holds the USER_PROCESS for the same console session and four earlier "
                 "boots, on 2021-02-15 and 2021-02-17, none of which the file kept. On the public MacBook "
                 "Pro logical extraction (macOS 15.4, not a registered corpus key) the file held 3 "
                 "records: BOOT_TIME at 2025-12-12 15:48:19 UTC and two USER_PROCESS, on console and "
                 "ttys000, each equal to the Entry Time of an ASL Login and Boot Records row to the "
                 "microsecond. Remote Host was blank on every tested row. When a logical extraction holds "
                 "the same file under private/var and under System/Volumes/Data/private/var, a "
                 "byte-identical second copy is not read again, and a record that both of two differing "
                 "copies hold is reported once; both are counted in the run log. No other column separates "
                 "the files a row can come from, since two captures of the file can differ, so Source File "
                 "stays.",
        "paths": ('*/var/run/utmpx',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import struct
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative, unique_sources

# struct utmpx32, the layout Libc writes to the file on a 64-bit Mac: ut_user[256], ut_id[4],
# ut_line[32], ut_pid, ut_type, two bytes of alignment, ut_tv (tv_sec, tv_usec as 32-bit
# integers), ut_host[256], ut_pad[16].
_RECORD = struct.Struct('<256s4s32sih2xii256s64s')
_SIGNATURE_TYPE = 10
_EMPTY_TYPE = 0
_SIGNATURE_USER = b'utmpx-1.00\x00'
_EVENTS = {0: 'EMPTY', 1: 'RUN_LVL', 2: 'BOOT_TIME', 3: 'OLD_TIME', 4: 'NEW_TIME', 5: 'INIT_PROCESS',
           6: 'LOGIN_PROCESS', 7: 'USER_PROCESS', 8: 'DEAD_PROCESS', 9: 'ACCOUNTING', 10: 'SIGNATURE',
           11: 'SHUTDOWN_TIME'}
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _text(field):
    return field.split(b'\x00', 1)[0].decode('utf-8', errors='replace')


def _time(seconds, microseconds):
    if not seconds and not microseconds:
        return ''
    try:
        return _EPOCH + timedelta(seconds=seconds, microseconds=microseconds)
    except OverflowError:
        return ''


@artifact_processor
def macosUtmpx(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Event', 'User', 'Line', 'PID', 'Remote Host', 'ID (hex)',
                    'Source File')
    data_list = []
    read = []
    problems = Counter()
    seen = set()
    files = [path for path in context.get_files_found() if not os.path.isdir(path)]
    paths, _skipped = unique_sources(context, files, label='Current Logins (utmpx)')
    for path in paths:
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        first = data[:_RECORD.size]
        if len(first) < _RECORD.size or _RECORD.unpack(first)[4] != _SIGNATURE_TYPE \
                or not first.startswith(_SIGNATURE_USER):
            problems['files with no utmpx-1.00 signature record, not read'] += 1
            continue
        whole = len(data) - len(data) % _RECORD.size
        if whole != len(data):
            problems['bytes after the last whole record, not read'] += len(data) - whole
        before = len(data_list)
        for offset in range(_RECORD.size, whole, _RECORD.size):
            user, ident, line, pid, kind, seconds, microseconds, host, _pad = _RECORD.unpack_from(data, offset)
            if kind == _EMPTY_TYPE:
                problems['EMPTY records, not reported'] += 1
                continue
            row = (_time(seconds, microseconds), _EVENTS.get(kind, str(kind)), _text(user), _text(line), pid,
                   _text(host), ident.hex())
            key = (canonical_relative(relative),) + tuple(str(value) for value in row)
            if key in seen:
                problems['records the other capture of the same file also holds, not reported again'] += 1
                continue
            seen.add(key)
            data_list.append(row + (relative,))
        if len(data_list) > before:
            read.append(path)
    if problems:
        logfunc('Current Logins (utmpx): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'Current Logins (utmpx): {len(data_list)} record(s).')
    return data_headers, data_list, '\n'.join(read)
