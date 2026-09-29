"""systemd journal entries and journal files, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the journal files systemd-journald keeps in /var/log/journal (and in /run/log/journal when the journal is
not persistent) with scripts/systemd_journal.py, a reader written from systemd's own description of the format and
its code at the v259.5 tag.
"""

__artifacts_v2__ = {
    "linuxJournalEntries": {
        "name": "systemd Journal",
        "description": "Entries of the systemd journal files in /var/log/journal and /run/log/journal: when the "
                       "journal received each one, its priority, identifier and message, the process, user and "
                       "unit the journal recorded for the sender, and the entry's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "Fields systemd compressed with zstd are decoded with Python 3.14 or later, or with the "
                        "backports.zstd or zstandard package on an earlier Python",
        "category": "systemd Journal (Linux)",
        "notes": "One row per entry the reader finds in the systemd journal files under var/log/journal and "
                 "run/log/journal, where systemd-journald writes them, including files it renamed with the "
                 ".journal~ suffix after it was stopped uncleanly or found them corrupted (Reference: systemd, "
                 "'systemd-journald.service', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd-journald.service.xml#L370-L392). "
                 "The files are read by scripts/systemd_journal.py, written for DLEAPP from systemd's description "
                 "of the format and its code at the v259.5 tag (Reference: systemd, 'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L144-L183). "
                 "A file is read object by object from the end of its header, and every entry the walk meets or "
                 "the file's chain of entry arrays reaches is reported; journald writes new objects before it "
                 "links them into the chain (Reference: systemd, 'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L111-L115), "
                 "so an entry written but not yet linked is still read. A file whose header sets an incompatible "
                 "flag this reader does not know is not read, as the format description asks (Reference: systemd, "
                 "'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L260-L268), "
                 "and appears only in systemd Journal Files. Rows come file by file, in the order of each file's "
                 "first entry and then its path, and within a file in the order the entries are stored. Sequence "
                 "Number is the entry's sequence number, which the system journal and the per-user journals "
                 "written by one journald share (Reference: systemd, 'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L341-L347): "
                 "on ubuntu2604_arm64_journal the online system journal holds numbers 22,437 to 38,220 and the "
                 "online user journal 22,787 to 38,209. Time (UTC) is the entry's realtime, the wall-clock time at "
                 "which the journal received the entry, and Monotonic (s) its monotonic time in seconds, which has "
                 "to be combined with the boot ID to serve as an address for the entry (Reference: systemd, "
                 "'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L666); "
                 "Boot ID is the boot the entry names. Source Time (UTC) is the entry's "
                 "_SOURCE_REALTIME_TIMESTAMP, the earliest trusted timestamp of the message when one different "
                 "from the reception time is known (Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L273-L279). "
                 "On ubuntu2604_arm64_journal Source Time (UTC) is filled on all 21,135 entries whose Transport is "
                 "journal and all 8,159 syslog entries, and blank on all 7,263 kernel, 1,591 stdout and 72 driver "
                 "entries. Priority is the PRIORITY field as stored, with the name systemd gives the syslog levels "
                 "0 to 7 after a single digit in that range (Reference: systemd, 'syslog-util.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/syslog-util.c#L88-L97). "
                 "The journal does not validate PRIORITY, SYSLOG_IDENTIFIER or any other field whose name does not "
                 "begin with an underscore (Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L127-L131): "
                 "a known entry sent with PRIORITY=high shows high, and the two known entries sent without "
                 "PRIORITY show a blank Priority. Identifier and Message are the entry's SYSLOG_IDENTIFIER and "
                 "MESSAGE fields. Process ID, User ID, Command, Executable, Command Line, Unit, User Unit, "
                 "Transport and Hostname are the fields _PID, _UID, _COMM, _EXE, _CMDLINE, _SYSTEMD_UNIT, "
                 "_SYSTEMD_USER_UNIT, _TRANSPORT and _HOSTNAME, which systemd documents as added by the journal "
                 "and not alterable by the client (Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L199-L201); "
                 "for output read from a forked process's standard output or error, the process, user and group "
                 "numbers are those of the parent that opened the connection (Reference: systemd, "
                 "'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L209-L212). "
                 "journald drops a field whose name begins with an underscore when a client sends it over the "
                 "native protocol (Reference: systemd, 'journal-file.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/libsystemd/sd-journal/journal-file.c#L1730-L1732, "
                 "called for each field at "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-native.c#L157-L159). "
                 "Measured with a known entry: a python3 process sent SYSLOG_IDENTIFIER=sshd with _PID=1, "
                 "_COMM=sshd and _EXE=/usr/sbin/sshd, and its row shows Identifier sshd, Command python3, "
                 "Executable /usr/bin/python3.14 and the process's own ID, with none of the three underscore "
                 "fields it sent. Command, Executable and Command Line can be blank on a row whose Process ID is "
                 "filled: the known entry from logger shows Command logger and neither of the other two. Other "
                 "Fields lists the entry's other fields as NAME=value, one per line in order of name; a field an "
                 "entry holds more than once is listed once per value, as the known entry sent DLEAPP_REPEAT twice "
                 "with the values one and two shows, and a column whose field an entry holds more than once shows "
                 "each value on its own line. _BOOT_ID is left out of Other Fields when it equals Boot ID, and "
                 "_SOURCE_REALTIME_TIMESTAMP when Source Time (UTC) shows it. A value that is UTF-8 is shown as "
                 "written, except that the control characters U+0000 to U+001F other than tab and newline, and "
                 "delete, are shown as their Unicode control pictures (␛ for escape, ␡ for delete). Any other "
                 "value is shown as its length in bytes and its bytes in hex, only the first 1,024 bytes when it "
                 "is longer. The known entry with an escape sequence and bytes that are not UTF-8 shows both "
                 "forms. Entry Check is blank when the entry is reached from the file's chain of entry arrays, its "
                 "size is a whole number of items and every DATA object it names was read and matches the hash "
                 "systemd stored with it, SipHash-2-4 keyed with the file ID or, in files without the keyed hash, "
                 "Jenkins lookup3 (Reference: systemd, 'journal-file.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/libsystemd/sd-journal/journal-file.c#L1594-L1601). "
                 "Otherwise it names what was found: an entry not reached from the chain, an entry whose size is "
                 "not a whole number of items, a stored hash that does not match the payload (the field is still "
                 "shown), or an item that does not point to a DATA object or whose payload could not be decoded or "
                 "holds no \"=\" (the field is then missing from the row). Entry Check is blank on all 38,220 rows "
                 "of ubuntu2604_arm64_journal; the unit tests build damaged files for each of the other outcomes. "
                 "journald compresses a field larger than 512 bytes by default (Reference: systemd, "
                 "'journald.conf', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/journald.conf.xml#L121-L131). "
                 "XZ payloads are decoded with Python's lzma module, LZ4 payloads (an 8-byte length followed by an "
                 "LZ4 block: Reference: systemd, 'compress.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/compress.c#L269-L277) "
                 "with a decoder in scripts/systemd_journal.py, and zstd payloads with compression.zstd from "
                 "Python 3.14 or, on an earlier Python, the backports.zstd or zstandard package when one is "
                 "installed; without one, Entry Check names the item that was not decoded. "
                 "ubuntu2604_arm64_journal holds 9 zstd payloads, and read under Python 3.10 with neither package, "
                 "23 of its entries lack a field and name it in Entry Check. Checked against systemd 259.5's own "
                 "reader: every entry of ubuntu2604_arm64_journal, 38,220 entries in four files, equals what "
                 "journalctl -o export printed for the same file, field for field, and so does every entry of four "
                 "files the unit tests build in four of the layouts this reader handles (compact items with the "
                 "keyed hash and zstd; regular items with the Jenkins hash, XZ and the 240-byte header, which ends "
                 "with the fields added in systemd 189; regular items with the keyed hash, LZ4 and the 256-byte "
                 "header; compact items without compression), on each of which journalctl --verify also passed. A "
                 "sealed file's TAG objects are skipped and its seals are not verified. Only journal files present "
                 "in the extraction are read; nothing is carved from unallocated space. ubuntu2604_arm64_journal "
                 "is the lab VM's journal folder, captured after seven known steps run as its unprivileged user on "
                 "2026-09-29 from 01:16:44 to 01:16:51 UTC by the VM's clock: an entry sent with a custom field "
                 "and a field written twice, a program claiming the identifier sshd, a two-line message with an "
                 "escape sequence and bytes that are not UTF-8, a 4,024-byte message that journald stored "
                 "compressed with zstd, a priority and facility that are not numbers, a syslog entry from logger, "
                 "and two lines of standard output from systemd-cat, which share one Time (UTC) to the "
                 "microsecond. Hostname holds one value on every row, the capture coming from one machine.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 38,220 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/var/log/journal/*.journal", "*/var/log/journal/*.journal~", "*/run/log/journal/*.journal", "*/run/log/journal/*.journal~"),
        "output_types": "standard",
        "artifact_icon": "notebook",
    },
    "linuxJournalFiles": {
        "name": "systemd Journal Files",
        "description": "The systemd journal files found: the first and last entry times, state, entry count, "
                       "sequence numbers, IDs and format features each file's header records, how many entries "
                       "reading the file found, and why a file could not be read in full.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "systemd Journal (Linux)",
        "notes": "One row per systemd journal file found at the same paths as systemd Journal, with what the "
                 "file's header records and what reading the file found (Reference: systemd, 'Journal File "
                 "Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L144-L183). "
                 "First Entry (UTC) and Last Entry (UTC) are the header's head_entry_realtime and "
                 "tail_entry_realtime. State is offline, online or archived as the header records it: set online "
                 "while a writer has the file open, offline when it closes it and archived once it has been "
                 "rotated (Reference: systemd, 'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L317-L331); "
                 "another value is shown as stored. Entries (Header) is the entry count in the header, and Entries "
                 "Read the number of entries the reader found by walking the file's objects and following its "
                 "chain of entry arrays; Entries Not in Chain counts those found only by walking. First Sequence "
                 "Number and Last Sequence Number are the header's head_entry_seqnum and tail_entry_seqnum, "
                 "Sequence Number ID the ID the files of one journald share (Reference: systemd, 'Journal File "
                 "Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L341-L347), "
                 "and Machine ID, Tail Entry Boot ID and File ID the header's machine_id, tail_entry_boot_id and "
                 "file_id. When journald archives a file it renames it to its original name followed by @, the "
                 "sequence number ID, the first sequence number and the first entry's time in hex (Reference: "
                 "systemd, 'journal-file.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/libsystemd/sd-journal/journal-file.c#L4373-L4377); "
                 "on ubuntu2604_arm64_journal the names of both archived files agree with their headers. Features "
                 "names the header flags a file sets (sealed, tail entry boot ID, XZ, LZ4 or zstd compression, "
                 "keyed hash, compact) and gives any unknown flag in hex. A file with an incompatible flag this "
                 "reader does not know is listed with 0 in Entries Read and no entry is read from it, as the "
                 "format description asks (Reference: systemd, 'Journal File Format', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/docs/JOURNAL_FILE_FORMAT.md#L260-L268). "
                 "Reading describes such a flag, a file shorter than its header says, or an object walk that "
                 "stopped early: at an object that does not fit in the arena, or at bytes at the end of the arena "
                 "that are too few to hold an object and are not all zero. On ubuntu2604_arm64_journal the four "
                 "files are two archived and two online; Entries (Header) equals Entries Read on all four, Entries "
                 "Not in Chain is 0 on every row and Reading is blank on every row, while Sequence Number ID, "
                 "Machine ID and Features each hold one value on every row, the files coming from one machine and "
                 "one journald. The unit tests build files that differ: an entry not linked into the chain makes "
                 "Entries Read one more than Entries (Header), and a cut file and an unknown incompatible flag "
                 "each give a Reading.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 4 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/var/log/journal/*.journal", "*/var/log/journal/*.journal~", "*/run/log/journal/*.journal", "*/run/log/journal/*.journal~"),
        "output_types": "standard",
        "artifact_icon": "files",
    },
}

import os
from datetime import datetime, timedelta, timezone

from scripts import systemd_journal
from scripts.ilapfuncs import artifact_processor, logfunc

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Report columns filled from one journal field each, in column order.
COLUMN_FIELDS = (('Priority', 'PRIORITY'), ('Identifier', 'SYSLOG_IDENTIFIER'), ('Message', 'MESSAGE'),
                 ('Process ID', '_PID'), ('User ID', '_UID'), ('Command', '_COMM'), ('Executable', '_EXE'),
                 ('Command Line', '_CMDLINE'), ('Unit', '_SYSTEMD_UNIT'), ('User Unit', '_SYSTEMD_USER_UNIT'),
                 ('Transport', '_TRANSPORT'), ('Hostname', '_HOSTNAME'))
SHOWN = {field for _column, field in COLUMN_FIELDS}

# The names systemd gives syslog levels 0 to 7 (log_level_table in src/basic/syslog-util.c).
LEVELS = ('emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug')

# Control characters other than tab and newline are shown as their Unicode control pictures (U+2400 to U+241F,
# and U+2421 for DEL), so they are visible and cannot be mistaken for text.
PICTURES = {code: 0x2400 + code for code in range(32) if code not in (9, 10)}
PICTURES[127] = 0x2421

HEX_LIMIT = 1024


def microseconds(value):
    """A journal time (microseconds since 1970 in UTC) as a datetime, or '' for 0 or a value past 9999."""
    if not value or value >= 253402300800000000:
        return ''
    return EPOCH + timedelta(microseconds=value)


def show(value):
    """A field value as text: UTF-8 as written, with control characters shown as control pictures; other bytes
    in hex, the first 1,024 of them when there are more."""
    try:
        return value.decode('utf-8').translate(PICTURES)
    except UnicodeDecodeError:
        if len(value) > HEX_LIMIT:
            return f'[{len(value):,} bytes, not UTF-8; the first {HEX_LIMIT:,} in hex] {value[:HEX_LIMIT].hex()}'
        return f'[{len(value):,} bytes, not UTF-8] {value.hex()}'


def priority(value):
    """PRIORITY as stored, with systemd's name for a level of 0 to 7."""
    text = show(value)
    if len(text) == 1 and text in '01234567':
        return f'{text} ({LEVELS[int(text)]})'
    return text


def source_time(value):
    """_SOURCE_REALTIME_TIMESTAMP as a datetime, or None when it is not a whole number of microseconds."""
    if value is not None and value.isdigit() and len(value) <= 19:
        return microseconds(int(value))
    return None


def _journals(context):
    """(relative path, path, JournalFile) for every file found that is a journal, in order of first entry and
    then path, each file read only when its turn comes."""
    found = []
    for path in sorted(set(map(str, context.get_files_found()))):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            found.append((systemd_journal.head_entry_realtime(path), relative, path))
        except (OSError, systemd_journal.JournalError) as exc:
            logfunc(f'systemd Journal: {relative} not read: {exc}')
    for _time, relative, path in sorted(found):
        try:
            yield relative, path, systemd_journal.read_journal(path)
        except (OSError, systemd_journal.JournalError) as exc:
            logfunc(f'systemd Journal: {relative} not read: {exc}')


def _row(entry, relative):
    values = {}
    for name, value in entry.fields:
        values.setdefault(name, []).append(value)
    boot = entry.boot_id
    columns = []
    for column, field in COLUMN_FIELDS:
        shown = values.get(field, [])
        render = priority if column == 'Priority' else show
        columns.append('\n'.join(render(v) for v in shown))
    source = values.get('_SOURCE_REALTIME_TIMESTAMP', [])
    source_value = source_time(source[0]) if len(source) == 1 else None
    other = []
    for name, value in sorted(entry.fields, key=lambda item: item[0]):
        if name in SHOWN:
            continue
        if name == '_SOURCE_REALTIME_TIMESTAMP' and source_value is not None:
            continue
        if name == '_BOOT_ID' and value == boot.encode():
            continue
        other.append(f'{name}={show(value)}')
    monotonic = f'{entry.monotonic // 1000000}.{entry.monotonic % 1000000:06d}'
    return ((microseconds(entry.realtime), source_value if source_value is not None else '')
            + tuple(columns)
            + (boot, monotonic, entry.seqnum, '\n'.join(other), '; '.join(entry.problems), relative))


@artifact_processor
def linuxJournalEntries(context):
    # The columns between the two times and Boot ID are COLUMN_FIELDS, in that order.
    data_headers = (('Time (UTC)', 'datetime'), ('Source Time (UTC)', 'datetime'), 'Priority', 'Identifier',
                    'Message', 'Process ID', 'User ID', 'Command', 'Executable', 'Command Line', 'Unit', 'User Unit',
                    'Transport', 'Hostname', 'Boot ID', 'Monotonic (s)', 'Sequence Number', 'Other Fields',
                    'Entry Check', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    read = []
    for relative, path, journal in _journals(context):
        if journal.unknown_incompatible:
            logfunc(f'systemd Journal: {relative} not read: it sets incompatible flags '
                    f'{journal.unknown_incompatible:#x}, which this reader does not know')
            continue
        count = unlinked = with_problems = 0
        for entry in journal.entries():
            results.add_row(_row(entry, relative))
            count += 1
            unlinked += not entry.linked
            with_problems += bool(entry.problems)
        logfunc(f'systemd Journal: {relative}: {count:,} entries, {unlinked:,} of them not reached from the chain '
                f'of entry arrays, {with_problems:,} with a problem noted in Entry Check')
        if journal.walk_stop:
            logfunc(f'systemd Journal: {relative}: the object walk stopped early: {journal.walk_stop}')
        read.append(path)
    results.set_source_path('\n'.join(read))
    return results


@artifact_processor
def linuxJournalFiles(context):
    data_headers = (('First Entry (UTC)', 'datetime'), ('Last Entry (UTC)', 'datetime'), 'State', 'Entries (Header)',
                    'Entries Read', 'Entries Not in Chain', 'First Sequence Number', 'Last Sequence Number',
                    'Sequence Number ID', 'Machine ID', 'Tail Entry Boot ID', 'File ID', 'Features', 'Reading',
                    'Source File')
    rows = []
    read = []
    for relative, path, journal in _journals(context):
        offsets = journal.entry_offsets() if not journal.unknown_incompatible else []
        reading = []
        if journal.unknown_incompatible:
            reading.append(f'entries not read: incompatible flags {journal.unknown_incompatible:#x} are unknown '
                           f'to this reader')
        if len(journal.data) < journal.header_size + journal.arena_size:
            reading.append(f'the file is {len(journal.data):,} bytes, shorter than the {journal.header_size:,}-byte '
                           f'header and {journal.arena_size:,}-byte arena the header describes')
        if journal.walk_stop:
            reading.append(f'the object walk stopped early: {journal.walk_stop}')
        rows.append((microseconds(journal.head_entry_realtime), microseconds(journal.tail_entry_realtime),
                     systemd_journal.STATES.get(journal.state, f'{journal.state} (as stored)'), journal.n_entries,
                     len(offsets), sum(1 for _offset, linked in offsets if not linked),
                     journal.head_entry_seqnum or '', journal.tail_entry_seqnum or '', journal.seqnum_id.hex(),
                     journal.machine_id.hex(), journal.tail_entry_boot_id.hex(), journal.file_id.hex(),
                     ', '.join(journal.features()), '; '.join(reading), relative))
        read.append(path)
    return data_headers, rows, '\n'.join(read)
