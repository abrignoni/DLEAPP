"""Apple System Log (ASL) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the ASL version 2 files a Mac keeps under private/var/log/asl,
private/var/log/powermanagement and private/var/log/DiagnosticMessages. Each file is
an 80-byte header followed by MSG and STR records; the reader follows the chain of
Next offsets from the header's First offset, as Apple's asl_file.c does, and decodes
each message's fixed fields, its six string fields and its key/value pairs.

A logical extraction can hold the log folders under private/var/log and under
System/Volumes/Data/private/var/log, copied at two moments. The two copies are read as
one store: a record both copies hold at the same offset of the same file, with the
same message ID, time and content, is reported once.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative

_COOKIE = b'ASL DB'
_HEADER_LEN = 80
_VERSION = 2
_RECORD_HEAD = 6            # type (2) and length (4) in front of every record
_MSG_FIXED = 116            # MSG_RECORD_FIXED_LENGTH (122) less the record head
_NO_ID = 0xFFFFFFFF         # (uint32_t)-1, which asl_file.c leaves out for UID, GID and read access
_LEVELS = {0: 'Emergency', 1: 'Alert', 2: 'Critical', 3: 'Error', 4: 'Warning', 5: 'Notice',
           6: 'Info', 7: 'Debug'}
_UT_TYPES = {0: 'EMPTY', 1: 'RUN_LVL', 2: 'BOOT_TIME', 3: 'OLD_TIME', 4: 'NEW_TIME',
             5: 'INIT_PROCESS', 6: 'LOGIN_PROCESS', 7: 'USER_PROCESS', 8: 'DEAD_PROCESS',
             9: 'ACCOUNTING', 10: 'SIGNATURE', 11: 'SHUTDOWN_TIME'}
_LOGIN_FACILITIES = ('com.apple.system.utmpx', 'com.apple.system.lastlog')
_UT_KEYS = ('ut_user', 'ut_id', 'ut_line', 'ut_pid', 'ut_type', 'ut_tv.tv_sec', 'ut_tv.tv_usec',
            'ut_host')

__artifacts_v2__ = {
    "macosAslMessages": {
        "name": "ASL Messages",
        "description": "Messages in the Apple System Log store under private/var/log/asl: time, "
                       "level, sender and process ID, facility, message text and the message's "
                       "other keys, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Apple System Log (macOS)",
        "notes": "Reads the .asl files directly in private/var/log/asl, the folder Velociraptor's "
                 "MacOS.Forensics.ASL exchange artifact reads "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Forensics.ASL.yaml#L15-L19), "
                 "in the layout Apple's syslog source gives: an 80-byte header followed by message and "
                 "string records "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/include/asl_file.h#L82-L98). "
                 "Messages are reached as asl_file.c reaches them, through the Next offset each "
                 "carries, starting at the header's First offset, and a string of up to seven bytes is "
                 "held inside its 8-byte reference instead of in a string record "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_file.c#L1254-L1271, "
                 "https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_file.c#L1516-L1593). "
                 "A file is read until a record cannot be decoded or a Next offset goes back, where "
                 "asl_file.c also stops "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_file.c#L1601-L1610), "
                 "and the run log names the file and the offset; a file whose header does not read ASL "
                 "DB version 2 is not read. On dleapp_macos_bigsur the Next chains reached 7,477 "
                 "messages in the store's four files, the count a walk of every record in file order "
                 "also gives, and each chain ended at the offset the file's header records as its last "
                 "message. Messages of the com.apple.system.utmpx and com.apple.system.lastlog "
                 "facilities are reported in ASL Login and Boot Records instead, which leaves 7,458 "
                 "here. Time (UTC) is the message's Time, seconds since 1970-01-01 UTC, with its "
                 "nanosecond field shown to the microsecond. Level is the stored level named through "
                 "asl.h "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/include/asl.h#L73-L95). "
                 "Sender, PID, Facility, Message, UID, GID, Host, Ref Process and Ref PID are the "
                 "message's fields as stored; UID and GID are blank when stored as 4294967295 and Ref "
                 "PID when 0, the values asl_file.c leaves out when it reads a message "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_file.c#L1522-L1527), "
                 "and no message on either tested image stored a UID or GID of 4294967295. A UID or "
                 "GID of 4294967294 is -2 stored unsigned, the value asl_file.c stores when a message "
                 "carries no UID or GID "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_file.c#L896-L898), "
                 "so it does not by itself name an account; it was the UID of 5,683 of the 7,458 "
                 "dleapp_macos_bigsur messages. asl.h describes Host as the sender's address set by "
                 "the server and RefPID and RefProc as the reference process for messages proxied by "
                 "launchd "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/include/asl.h#L126-L142). "
                 "Keys lists the message's other key/value pairs, one per line, as stored, and Message "
                 "ID is the ASLMessageID the server sets. Log File is the name of the file that holds "
                 "the message. asl_store.c names each file for the date of its contents, with Uuuu or "
                 "Gggg in the name when reading is limited to a user or group ID, and puts messages "
                 "that carry an ASLExpireTime in BB files named for the last day of the month they "
                 "expire "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_store.c#L45-L58), "
                 "taking the date in the Mac's local time "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_store.c#L601). "
                 "On dleapp_macos_bigsur the three daily files were G80 files, and every message's UTC "
                 "date was its file's date. The Session field and the ReadUID, ReadGID and Flags "
                 "values are not reported; on both tested images Session was empty, ReadUID "
                 "4294967295, ReadGID 80 and Flags 2 on every message. On dleapp_macos_bigsur the "
                 "7,458 messages span 2021-02-15 to 2021-02-19, with levels Critical (9), Error "
                 "(1,368), Warning (368) and Notice (5,713); com.apple.xpc.launchd sent 5,251 of them, "
                 "5,182 carry a Ref Process, and Host held two values. On the public MacBook Pro "
                 "logical extraction (macOS 15.4 build 24E248, not a registered corpus key) all 925 "
                 "messages came from syslogd: 808 'ASL Sender Statistics' records, whose keys include "
                 "sender names with a leading asterisk, and 117 configuration notices. Every one of "
                 "its messages falls between 05:00 UTC on its file's date and 05:00 UTC the next day, "
                 "so 168 of the 925 carry a UTC date one day after their file's. That extraction holds "
                 "the log folder under private/var/log and under System/Volumes/Data/private/var/log, "
                 "copied at different moments: each copy held a daily file the other lacked, and in "
                 "the file both held with different bytes every message of the smaller copy sat at the "
                 "same offset, with the same ID and content, in the larger. The two copies are read as "
                 "one store: a message both hold at the same offset of the same file, with the same "
                 "ID, time and content, is reported once and counted in the run log, and one that "
                 "differs is reported from each copy.",
        "paths": ('*/var/log/asl/*.asl',),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 7,458 rows",
        },
    },
    "macosAslLogins": {
        "name": "ASL Login and Boot Records",
        "description": "The utmpx boot, shutdown, user process and dead process entries the Apple "
                       "System Log store keeps under private/var/log/asl: time, event type, user, "
                       "terminal line, process ID and the time recorded in the entry, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Apple System Log (macOS)",
        "notes": "Reads the same files as ASL Messages, directly in private/var/log/asl and in the "
                 "same way, and reports the messages of the com.apple.system.utmpx and "
                 "com.apple.system.lastlog facilities, the facilities Apple's Libc uses when it logs a "
                 "utmpx record: USER_PROCESS to com.apple.system.lastlog and every other type to "
                 "com.apple.system.utmpx "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.c#L313-L316, "
                 "https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.h#L37-L38). "
                 "Libc writes the record's fields as the keys ut_user, ut_id, ut_line, ut_pid, "
                 "ut_type, ut_tv.tv_sec, ut_tv.tv_usec and ut_host "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.c#L258-L275). "
                 "Time (UTC) is the message's Time as in ASL Messages. Event is ut_type named through "
                 "Libc's utmpx.h and the names Libc uses in the message text "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/include/NetBSD/utmpx.h#L87-L100, "
                 "https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.c#L278-L291). "
                 "User, Line, PID, Remote Host and ID are ut_user, ut_line, ut_pid, ut_host and ut_id "
                 "as stored, and Entry Time (UTC) is ut_tv.tv_sec and ut_tv.tv_usec, seconds and "
                 "microseconds since 1970-01-01 UTC. Apple's getutxent manual page describes ut_tv as "
                 "the time the entry was created "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L107), "
                 "BOOT_TIME as the time of a system boot, DEAD_PROCESS as a session leader that "
                 "exited, USER_PROCESS as a user process and SHUTDOWN_TIME as the time of system "
                 "shutdown "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L116-L138), "
                 "and for a USER_PROCESS entry ut_user as the login name of the user and ut_host as "
                 "the hostname of a remote user "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/NetBSD/endutxent.3#L169-L176). "
                 "Libc's getlastlogx answers a user's last login from the latest "
                 "com.apple.system.lastlog message whose ut_user names them "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.c#L141-L161). "
                 "Sender, Facility and Message are the message's fields as stored, and Other Keys "
                 "lists its remaining key/value pairs, one per line. Every login and boot record on "
                 "both tested images was in a BB file and carried an ASLExpireTime 31,622,400 seconds "
                 "(366 days) after its Time; asl_store.c names a BB file for the last day of the month "
                 "its messages expire "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_store.c#L54-L58). "
                 "On dleapp_macos_bigsur the BB file held 19: 5 BOOT_TIME from bootlog, 5 USER_PROCESS "
                 "from loginwindow, 5 DEAD_PROCESS from sessionlogoutd and 4 SHUTDOWN_TIME from "
                 "shutdown, every USER_PROCESS and DEAD_PROCESS naming thisisdfir on the console line, "
                 "with Entry Time within a second of Time on all 19. On the public MacBook Pro logical "
                 "extraction (macOS 15.4 build 24E248, not a registered corpus key) three BB files "
                 "held 41 from 2025-09-04 to 2025-12-12, including 3 USER_PROCESS records from login "
                 "on the ttys000 line. On its 2 DEAD_PROCESS records from login, Entry Time equals the "
                 "Entry Time of the USER_PROCESS record with the same PID and line, about 44 minutes "
                 "before the record's Time, so Entry Time does not give the time of those records. The "
                 "BOOT_TIME records' message reads BOOT_TIME followed by the seconds and microseconds, "
                 "without the colon Libc's own message text has "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/gen/utmpx-darwin.c#L322-L326). "
                 "Remote Host was blank on every row of both images. The MacBook Pro extraction's two "
                 "copies of the log folder are read as one store, as in ASL Messages.",
        "paths": ('*/var/log/asl/*.asl',),
        "output_types": ["standard"],
        "artifact_icon": "login",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 19 rows",
        },
    },
    "macosAslPowerManagement": {
        "name": "Power Management Log (ASL)",
        "description": "Records in the ASL files under private/var/log/powermanagement: time, "
                       "domain, message text and the record's other keys, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Apple System Log (macOS)",
        "notes": "Reads the .asl files directly in private/var/log/powermanagement with the reader ASL "
                 "Messages uses, in the layout Apple's syslog source gives "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/include/asl_file.h#L82-L98). "
                 "Every record on both tested images had Sender powerd and Facility "
                 "com.apple.iokit.power and carried a com.apple.iokit.domain key, which Domain shows. "
                 "Message is the message text and Keys the record's other key/value pairs, one per "
                 "line, as stored; Time (UTC) is the message's Time as in ASL Messages. What each "
                 "domain and key records is not established here, so the values are reported as "
                 "stored. On dleapp_macos_bigsur three files held 389 records from 2021-02-15 to "
                 "2021-02-19: Assertions 350, Notification 24, and ShutdownCause, Start and "
                 "AppWakeReason 5 each. On the public MacBook Pro logical extraction (macOS 15.4 build "
                 "24E248, not a registered corpus key) 15 files held 9,891 from 2025-12-10 to "
                 "2025-12-25, among them Assertions 9,239, Sleep 84, Notification 63, DarkWake 59, "
                 "Wake 24 and ShutdownCause 3. Its two copies of the folder are read as one store as "
                 "in ASL Messages: each held a file the other lacked, and in the file both held with "
                 "different bytes every record of the smaller copy sat, unchanged, at the same offset "
                 "in the larger.",
        "paths": ('*/var/log/powermanagement/*.asl',),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 389 rows",
        },
    },
    "macosAslDiagnosticMessages": {
        "name": "Diagnostic Messages (ASL)",
        "description": "Records in the ASL files under private/var/log/DiagnosticMessages: "
                       "time, domain, sender, message text and the record's other keys, as "
                       "stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Apple System Log (macOS)",
        "notes": "Reads the .asl files directly in private/var/log/DiagnosticMessages with the reader "
                 "ASL Messages uses, in the layout Apple's syslog source gives "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/include/asl_file.h#L82-L98). "
                 "On dleapp_macos_bigsur the Mac's own private/etc/asl/com.apple.MessageTracer routes "
                 "messages carrying a com.apple.message.domain key to that folder, and every record on "
                 "both tested images carried that key, which Domain shows. Sender, PID, UID and "
                 "Message are the message's fields as stored, UID as in ASL Messages; Keys lists the "
                 "record's other key/value pairs, one per line, as stored, and Time (UTC) is the "
                 "message's Time as in ASL Messages. What each domain and key records is not "
                 "established here, so the values are reported as stored. On dleapp_macos_bigsur three "
                 "files held 1,954 records from 2021-02-15 to 2021-02-19, the most common domains "
                 "com.apple.usage.app_activetime (571), com.apple.quicktour.population (324) and "
                 "com.apple.AddressBook.accounts.summary (119). On the public MacBook Pro logical "
                 "extraction (macOS 15.4 build 24E248, not a registered corpus key) eight files held "
                 "1,670 from 2025-12-18 to 2025-12-25, most commonly "
                 "com.apple.AddressBook.accounts.summary (274) and "
                 "com.apple.telemetry.coalition_memory (245). Its two copies of the folder are read as "
                 "one store as in ASL Messages: each held a file the other lacked, and in the file "
                 "both held with different bytes every record of the smaller copy sat, unchanged, at "
                 "the same offset in the larger.",
        "paths": ('*/var/log/DiagnosticMessages/*.asl',),
        "output_types": ["standard"],
        "artifact_icon": "report-analytics",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1,954 rows",
        },
    },
}


class AslError(Exception):
    """A record the reader cannot decode; reading of that file stops there."""


def _u16(data, offset):
    return struct.unpack_from('>H', data, offset)[0]


def _u32(data, offset):
    return struct.unpack_from('>I', data, offset)[0]


def _u64(data, offset):
    return struct.unpack_from('>Q', data, offset)[0]


def fetch_string(data, ref):
    """The string an 8-byte reference names: inline when its top bit is set, else a STR record."""
    if ref == 0:
        return None
    raw = struct.pack('>Q', ref)
    if raw[0] & 0x80:
        length = raw[0] & 0x0F
        if length > 7:
            raise AslError('inline string longer than 7 bytes')
        return raw[1:1 + length].decode('utf-8', 'replace')
    if ref + _RECORD_HEAD > len(data):
        raise AslError(f'string offset {ref} past the end of the file')
    if _u16(data, ref) != 1:
        raise AslError(f'no string record at offset {ref}')
    length = _u32(data, ref + 2)
    if length == 0 or ref + _RECORD_HEAD + length > len(data):
        raise AslError(f'string record at offset {ref} runs past the end of the file')
    text = data[ref + _RECORD_HEAD:ref + _RECORD_HEAD + length]
    if text[-1] != 0 or text.index(0) != length - 1:
        raise AslError(f'string record at offset {ref} is not one NUL-terminated string')
    return text[:-1].decode('utf-8', 'replace')


def fetch_message(data, where):
    """Decode the MSG record at `where` into a dict; raises AslError when it cannot."""
    if where + _RECORD_HEAD > len(data) or _u16(data, where) != 0:
        raise AslError(f'no message record at offset {where}')
    length = _u32(data, where + 2)
    if length == 0 or where + _RECORD_HEAD + length > len(data):
        raise AslError(f'message record at offset {where} runs past the end of the file')
    buf = data[where + _RECORD_HEAD:where + _RECORD_HEAD + length]
    if length < _MSG_FIXED or length < _MSG_FIXED + _u32(buf, 56) * 8:
        raise AslError(f'message record at offset {where} is shorter than its fields')
    record = {'offset': where, 'next': _u64(buf, 0), 'mid': _u64(buf, 8), 'time': _u64(buf, 16),
              'nano': _u32(buf, 24), 'level': _u16(buf, 28), 'flags': _u16(buf, 30),
              'pid': _u32(buf, 32), 'uid': _u32(buf, 36), 'gid': _u32(buf, 40),
              'ruid': _u32(buf, 44), 'rgid': _u32(buf, 48), 'refpid': _u32(buf, 52)}
    kvcount = _u32(buf, 56)
    pos = 60
    for field in ('host', 'sender', 'facility', 'message', 'refproc', 'session'):
        record[field] = fetch_string(data, _u64(buf, pos))
        pos += 8
    pairs = []
    for _ in range(kvcount // 2):
        key = fetch_string(data, _u64(buf, pos))
        value = fetch_string(data, _u64(buf, pos + 8))
        pos += 16
        pairs.append((key, value))
    record['pairs'] = pairs
    return record


def read_asl(data):
    """(records, problem): the messages on the Next chain, and why reading stopped early, or None."""
    if len(data) < _HEADER_LEN or data[:len(_COOKIE)] != _COOKIE:
        return [], 'not an ASL file'
    version = _u32(data, 12)
    if version != _VERSION:
        return [], f'ASL version {version}, not read'
    records, cursor = [], _u64(data, 16)
    while cursor:
        try:
            record = fetch_message(data, cursor)
        except (AslError, struct.error) as ex:
            return records, f'stopped at offset {cursor}: {ex}'
        records.append(record)
        if record['next'] and record['next'] <= cursor:
            return records, f'stopped at offset {cursor}: the next offset goes back'
        cursor = record['next']
    return records, None


def _content(record):
    return tuple(record[k] for k in ('mid', 'time', 'nano', 'level', 'flags', 'pid', 'uid', 'gid',
                                     'ruid', 'rgid', 'refpid', 'host', 'sender', 'facility',
                                     'message', 'refproc', 'session')) + (tuple(record['pairs']),)


def collect(context, folder, label, keep=None):
    """(records, sources): the records of the .asl files directly under var/log/<folder>.

    `keep`, when given, selects the records to return.

    Each record carries 'file', the file's name. Copies of one file under private/var/log
    and System/Volumes/Data/private/var/log are read as one store: a record both hold at
    the same offset with the same content is returned once.
    """
    paths = []
    for found in context.get_files_found():
        path = str(found)
        relative = '/' + context.get_relative_path(path).replace('\\', '/').lstrip('/')
        if (os.path.isfile(path) and path.endswith('.asl')
                and relative.endswith(f'/var/log/{folder}/{os.path.basename(path)}')):
            paths.append(path)
    seen, records, sources = {}, [], []
    duplicates = conflicts = 0
    for path in sorted(set(paths), key=lambda p: (len(p), p)):
        relative = context.get_relative_path(path).replace('\\', '/')
        with open(path, 'rb') as handle:
            data = handle.read()
        found_records, problem = read_asl(data)
        if problem:
            logfunc(f'{label}: {relative}: {problem}')
        added = 0
        for record in found_records:
            if keep is not None and not keep(record):
                continue
            key = (canonical_relative(relative), record['offset'], record['mid'], record['time'],
                   record['nano'])
            content = _content(record)
            if key in seen:
                if content in seen[key]:
                    duplicates += 1
                    continue
                conflicts += 1
                seen[key].append(content)
            else:
                seen[key] = [content]
            record['file'] = os.path.basename(path)
            records.append(record)
            added += 1
        if added:
            sources.append(path)
    if duplicates:
        logfunc(f'{label}: {duplicates} records held by both copies of a file reported once')
    if conflicts:
        logfunc(f'{label}: {conflicts} records at the same offset and ID differ between copies; '
                f'both are reported')
    records.sort(key=lambda r: (r['time'], r['nano'], r['mid']))
    return records, sources


def record_time(seconds, nanoseconds=0):
    """Seconds since 1970-01-01 UTC, with nanoseconds shown to the microsecond; '' when unusable."""
    try:
        return (datetime.fromtimestamp(seconds, timezone.utc)
                + timedelta(microseconds=nanoseconds // 1000))
    except (OverflowError, OSError, ValueError):
        return ''


def level_name(level):
    return f'{_LEVELS[level]} ({level})' if level in _LEVELS else str(level)


def optional_id(value):
    return '' if value == _NO_ID else value


def keys_text(pairs, skip=()):
    return '\n'.join(f'{key}: {value if value is not None else ""}'
                     for key, value in pairs if key not in skip)


def first_value(pairs, key):
    for name, value in pairs:
        if name == key:
            return value if value is not None else ''
    return ''


def entry_time(pairs):
    """ut_tv.tv_sec and ut_tv.tv_usec of a utmpx message as a UTC datetime; '' when absent."""
    seconds, micros = first_value(pairs, 'ut_tv.tv_sec'), first_value(pairs, 'ut_tv.tv_usec')
    if not seconds.lstrip('-').isdigit():
        return ''
    stamp = record_time(int(seconds))
    if stamp and micros.isdigit():
        stamp += timedelta(microseconds=int(micros))
    return stamp


def event_name(pairs):
    value = first_value(pairs, 'ut_type')
    if value.isdigit() and int(value) in _UT_TYPES:
        return f'{_UT_TYPES[int(value)]} ({value})'
    return value


@artifact_processor
def macosAslMessages(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Level', 'Sender', 'PID', 'Facility', 'Message',
                    'UID', 'GID', 'Host', 'Ref Process', 'Ref PID', 'Keys', 'Message ID',
                    'Log File')
    records, sources = collect(context, 'asl', 'ASL Messages',
                               lambda r: r['facility'] not in _LOGIN_FACILITIES)
    data_list = []
    for r in records:
        data_list.append((record_time(r['time'], r['nano']), level_name(r['level']), r['sender'] or '',
                          r['pid'], r['facility'] or '', r['message'] or '', optional_id(r['uid']),
                          optional_id(r['gid']), r['host'] or '', r['refproc'] or '',
                          r['refpid'] or '', keys_text(r['pairs']), r['mid'], r['file']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosAslLogins(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Event', 'User', 'Line', 'PID',
                    ('Entry Time (UTC)', 'datetime'), 'Remote Host', 'ID', 'Sender', 'Facility',
                    'Message', 'Other Keys', 'Log File')
    records, sources = collect(context, 'asl', 'ASL Login and Boot Records',
                               lambda r: r['facility'] in _LOGIN_FACILITIES)
    data_list = []
    for r in records:
        pairs = r['pairs']
        data_list.append((record_time(r['time'], r['nano']), event_name(pairs),
                          first_value(pairs, 'ut_user'), first_value(pairs, 'ut_line'),
                          first_value(pairs, 'ut_pid'), entry_time(pairs),
                          first_value(pairs, 'ut_host'), first_value(pairs, 'ut_id'),
                          r['sender'] or '', r['facility'], r['message'] or '',
                          keys_text(pairs, _UT_KEYS), r['file']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosAslPowerManagement(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Domain', 'Message', 'Keys', 'Sender', 'PID',
                    'Log File')
    records, sources = collect(context, 'powermanagement', 'Power Management Log (ASL)')
    data_list = [(record_time(r['time'], r['nano']), first_value(r['pairs'], 'com.apple.iokit.domain'),
                  r['message'] or '', keys_text(r['pairs'], ('com.apple.iokit.domain',)),
                  r['sender'] or '', r['pid'], r['file']) for r in records]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosAslDiagnosticMessages(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Domain', 'Sender', 'Message', 'Keys', 'PID',
                    'UID', 'Log File')
    records, sources = collect(context, 'DiagnosticMessages', 'Diagnostic Messages (ASL)')
    data_list = [(record_time(r['time'], r['nano']),
                  first_value(r['pairs'], 'com.apple.message.domain'), r['sender'] or '',
                  r['message'] or '', keys_text(r['pairs'], ('com.apple.message.domain',)),
                  r['pid'], optional_id(r['uid']), r['file']) for r in records]
    return data_headers, data_list, '\n'.join(sources)
