"""AnyDesk connection, file transfer and trace log records for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads AnyDesk's connection_trace.txt, file_transfer_trace.txt and its trace logs
(ad.trace, ad_svc.trace, anydesk.trace) at the locations AnyDesk's support article
"What are trace files?" gives. Line layouts, text encodings and the clock each file
writes were measured on known data made between AnyDesk 9.8.3 on Windows 11 and
AnyDesk 8.1.0 on Ubuntu 26.04; the notes say what was measured and what was not.
"""

import os
import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE_BREAK = re.compile(r'\r?\n')
# Fields of a connection_trace.txt line: runs of two or more spaces, or tabs.
_SPACED = re.compile(r'\t+| {2,}')
# The date and time connection_trace.txt and file_transfer_trace.txt write.
_TEXT_TIME = re.compile(r'^(\d{4})-(\d{2})-(\d{2}), (\d{2}):(\d{2})$')
# The file name and progress text of a file_transfer_trace.txt line.
_TRANSFER_ITEM = re.compile(r"^'(.*)' \((.*)\)$")
# A trace log line: level, date and time, process and thread fields, component, message.
_TRACE_LINE = re.compile(r'^\s*(\w+)\s+(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{3})'
                         r'\s+(.*?)\s(\S+) - (.*)$')

# Trace log lines reported, matched on component and message as the known data
# shows them. The capture group, when there is one, is the Value column.
_TRACE_RULES = (
    ('Own AnyDesk ID', 'anynet.connection_mgr', re.compile(r'^New user data\. Client-ID: (\d+)\.$')),
    ('Peer address (incoming connection)', 'anynet.connection_mgr',
     re.compile(r'^\[([^\]]+)\] Incoming connection\.$')),
    ('Logged in to relay', 'anynet.any_socket', re.compile(r'^Logged in from (\S+) on relay \S+\.$')),
    ('Remote AnyDesk ID', 'anynet.any_socket', re.compile(r'^Client-ID: (\d+) \(FPR: [0-9a-f]+\)\.$')),
    ('Accepting from', 'anynet.any_socket', re.compile(r'^Accepting from (\d+)\.$')),
    ('Connecting to', 'anynet.any_socket', re.compile(r'^Connecting to (\d+)\.$')),
    ('Incoming session request', 'app.backend_session',
     re.compile(r'^Incoming session request: .* \((\d+)\)$')),
    ('Authenticated', 'app.session', re.compile(r'^\d+: (Authenticated .*)\.$')),
    ('Password not accepted', 'app.session', re.compile(r'^Passphrase not accepted\.$')),
    ('Session closed', 'app.session', re.compile(r'^Session closed (?:by remote side|locally): (\S+)\.$')),
    ('Remote OS', 'app.backend_session', re.compile(r'^Remote OS: (.*?)\s*$')),
    ('Remote OS', 'app.frontend_session', re.compile(r'^Remote OS: (.*?)\s*$')),
    ('Remote AnyDesk version', 'app.backend_session', re.compile(r'^Remote version: (.*?)\s*$')),
    ('Remote AnyDesk version', 'app.frontend_session', re.compile(r'^Remote version: (.*?)\s*$')),
    ('File transfer: preparing files', 'app.prepare_task', re.compile(r"^Preparing files in '(.*)'\.$")),
    ('File transfer: download started', 'app.local_file_transfer', re.compile(r'^Download started')),
    ('File transfer: download finished', 'app.local_file_transfer', re.compile(r'^Download finished\.$')),
    ('Command line', 'main', re.compile(r'^Command Line params: (.*)$')),
)

_WINDOWS_FOLDERS = ('/programdata/anydesk', '/appdata/roaming/anydesk')

__artifacts_v2__ = {
    "anyDeskConnections": {
        "name": "AnyDesk Connections",
        "description": "Connection requests listed in AnyDesk's connection_trace.txt, one row per line: the "
                       "time, direction, how the request ended and the other side's AnyDesk ID as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "AnyDesk",
        "notes": "AnyDesk's support article says connection_trace.txt is created when a connection request is "
                 "received, holds the date and time, whether the request was accepted or rejected and who sent "
                 "it, and sits in the folder of the client's configuration files "
                 "(https://support.anydesk.com/docs/what-are-trace-files.md, read 2026-10-31). Read from "
                 "ProgramData\\AnyDesk and AppData\\Roaming\\AnyDesk on Windows and from etc/anydesk and "
                 ".anydesk on Linux and macOS, with the ad_<prefix> folders custom builds use. Measured on the "
                 "known data (windows11_arm_anydesk_known_20261031, ubuntu2604_arm64_anydesk_known_20261031): "
                 "the Windows file is UTF-16LE without a byte order mark and the Linux file UTF-8; fields are "
                 "space aligned; times are to the minute. Windows wrote UTC: the accepted request is stamped "
                 "03:25, and the VM ran at UTC-4, so its local time was 23:25. Linux wrote the VM's local time "
                 "(America/New_York) for the same requests, so Timestamp (UTC) is filled only for files in a "
                 "Windows AnyDesk folder; on the Linux known data Timestamp (UTC) has no value on any row, and Time (as stored) there has no zone. Direction held Incoming on every Windows row and Outgoing on every Linux row, consistent with each file recording from the side that wrote it. "
                 "Status held User for the request accepted on the Windows prompt and REJECTED for the one "
                 "dismissed there. The Windows file has no line for the three password attempts that did not "
                 "authenticate; the Linux file, on the connecting side, logged all five outgoing attempts and "
                 "showed those three as REJECTED, stamped when each closed. Remote ID and Second ID Field held "
                 "the same value on every row of both files; what the second field records is not "
                 "established. Not tested: macOS, AnyDesk custom builds, and status values other than User and "
                 "REJECTED.",
        "paths": ('*/ProgramData/AnyDesk/connection_trace.txt',
                  '*/ProgramData/AnyDesk/ad_*/connection_trace.txt',
                  '*/AppData/Roaming/AnyDesk/connection_trace.txt',
                  '*/AppData/Roaming/AnyDesk/ad_*/connection_trace.txt',
                  '*/etc/anydesk/connection_trace.txt',
                  '*/.anydesk/connection_trace.txt',
                  '*/.anydesk_ad_*/connection_trace.txt'),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "windows11_arm_anydesk_known_20261031": "AnyDesk 9.8.3 on Windows 11 build 26200 (ARM64) | 2 rows",
            "ubuntu2604_arm64_anydesk_known_20261031": "AnyDesk 8.1.0 on Ubuntu 26.04 (aarch64) | 5 rows",
        },
    },
    "anyDeskFileTransfers": {
        "name": "AnyDesk File Transfers",
        "description": "File transfer records in AnyDesk's file_transfer_trace.txt, one row per line: the time, "
                       "transfer mode, start or finish, direction and the file name and size as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "AnyDesk",
        "notes": "AnyDesk's support article does not describe file_transfer_trace.txt. It was found beside "
                 "connection_trace.txt in ProgramData\\AnyDesk on Windows and etc/anydesk on Linux in the known "
                 "data (windows11_arm_anydesk_known_20261031, ubuntu2604_arm64_anydesk_known_20261031), and is "
                 "also looked for in the other folders the connections artifact reads. Measured there: tab "
                 "separated, UTF-16LE without a byte order mark on Windows and UTF-8 on Linux, times to the "
                 "minute, Windows in UTC and Linux in the VM's local time, so Timestamp (UTC) is filled only for "
                 "files in a Windows AnyDesk folder; on the Linux known data Timestamp (UTC) has no value on any row. Direction names the side of the machine that wrote the "
                 "file: the file sent from Ubuntu to Windows is upload on Ubuntu and download on Windows. Both "
                 "transfers were made with AnyDesk's File Manager, so Mode held File Manager on every row; "
                 "Clipboard transfers were not made. The one file sent twice gave two start and finish pairs. "
                 "Size is AnyDesk's rounded text (for example ~16.29 KiB out of 16.29 KiB), not a byte count. "
                 "Not tested: macOS, clipboard transfers, a transfer that did not finish.",
        "paths": ('*/ProgramData/AnyDesk/file_transfer_trace.txt',
                  '*/ProgramData/AnyDesk/ad_*/file_transfer_trace.txt',
                  '*/AppData/Roaming/AnyDesk/file_transfer_trace.txt',
                  '*/AppData/Roaming/AnyDesk/ad_*/file_transfer_trace.txt',
                  '*/etc/anydesk/file_transfer_trace.txt',
                  '*/.anydesk/file_transfer_trace.txt',
                  '*/.anydesk_ad_*/file_transfer_trace.txt'),
        "output_types": ["standard"],
        "artifact_icon": "file",
        "sample_data": {
            "windows11_arm_anydesk_known_20261031": "AnyDesk 9.8.3 on Windows 11 build 26200 (ARM64) | 6 rows",
            "ubuntu2604_arm64_anydesk_known_20261031": "AnyDesk 8.1.0 on Ubuntu 26.04 (aarch64) | 6 rows",
        },
    },
    "anyDeskTraceEvents": {
        "name": "AnyDesk Trace Events",
        "description": "Selected lines from AnyDesk's trace logs: the machine's own and the other side's AnyDesk "
                       "IDs, the peer's network address, authentication results, session ends, the other side's "
                       "OS and version, file transfers and the command line AnyDesk was started with.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "AnyDesk",
        "notes": "Trace log locations are the ones AnyDesk's support article gives for Windows 7 and later, "
                 "Linux and macOS, standard and custom builds "
                 "(https://support.anydesk.com/docs/what-are-trace-files.md, read 2026-10-31). The article does "
                 "not document the line layout or messages; the lines reported are the ones the known data "
                 "(windows11_arm_anydesk_known_20261031, ubuntu2604_arm64_anydesk_known_20261031) holds, matched "
                 "on component and message. Measured there: Own AnyDesk ID gave each machine's own ID and "
                 "Remote AnyDesk ID the other side's; Peer address (incoming connection) gave the other VM's "
                 "local network address on both sides, on three of the five requests each; Logged in to relay gave the same public address on both "
                 "sides because both VMs shared one, so whose address it is is not established; Password not "
                 "accepted marked the two attempts made with a password AnyDesk did not take; Authenticated "
                 "marked the request accepted on the Windows prompt; Session closed gave desk_rt_rejected for "
                 "the dismissed request. Level held info on every reported Linux row; on Windows it held info, warning (Password not accepted) and auth (Authenticated). The trace writes milliseconds, and wrote UTC on Windows 9.8.3 (the VM "
                 "at UTC-4) and on Linux 8.1.0 (the VM at UTC-4); macOS was not tested, and Timestamp (UTC) "
                 "is filled for every trace on that basis, beside Time (as stored). The known data was collected with "
                 "the AnyDesk service stopped. Every line not matched by a rule is left out, and the "
                 "run log counts them per file. Value is the captured text as AnyDesk wrote it: an "
                 "address and port (Logged in to relay, Peer address), an AnyDesk ID (Own and Remote AnyDesk ID, "
                 "Accepting from, Connecting to, Incoming session request), a folder path (File transfer: preparing "
                 "files) or the arguments (Command line). On Windows 9.8.3 the Remote OS value also carries the "
                 "connection flags text AnyDesk appends to that line; on Linux 8.1.0 it held the OS name alone. Not tested: "
                 "macOS, AnyDesk versions other than 9.8.3 and 8.1.0, and messages these two did not write.",
        "paths": ('*/ProgramData/AnyDesk/ad_svc.trace',
                  '*/ProgramData/AnyDesk/ad_*/ad_*_svc.trace',
                  '*/AppData/Roaming/AnyDesk/ad.trace',
                  '*/AppData/Roaming/AnyDesk/ad_*/ad_*.trace',
                  '*/var/log/anydesk.trace',
                  '*/var/log/anydesk_ad_*.trace',
                  '*/.anydesk/anydesk.trace',
                  '*/.anydesk_ad_*/anydesk_ad_*.trace'),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "windows11_arm_anydesk_known_20261031": "AnyDesk 9.8.3 on Windows 11 build 26200 (ARM64) | 58 rows",
            "ubuntu2604_arm64_anydesk_known_20261031": "AnyDesk 8.1.0 on Ubuntu 26.04 (aarch64) | 50 rows",
        },
    },
}


def decode_text(data):
    """Text of a file and how many replacement characters decoding added. UTF-16 is
    taken from a byte order mark, or from NUL in every odd position of the first bytes,
    which is how the Windows files measured here begin."""
    head = data[:64]
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        text = data.decode('utf-16', errors='replace')
        return text, text.count('�') - data.decode('utf-16', errors='ignore').count('�')
    if len(head) >= 4 and head[1::2] == b'\x00' * len(head[1::2]):
        text = data.decode('utf-16-le', errors='replace')
        return text, text.count('�') - data.decode('utf-16-le', errors='ignore').count('�')
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    text = data.decode('utf-8', errors='replace')
    return text, text.count('�') - data.count('�'.encode('utf-8'))


def in_windows_folder(path):
    """True for a file in ProgramData\\AnyDesk or AppData\\Roaming\\AnyDesk, the folders
    whose text files were measured writing UTC."""
    lowered = '/' + path.replace('\\', '/').lower()
    return any(folder + '/' in lowered for folder in _WINDOWS_FOLDERS)


def text_time(value):
    """A datetime for 'YYYY-MM-DD, HH:MM', or None."""
    match = _TEXT_TIME.match(value)
    if not match:
        return None
    try:
        return datetime(*(int(part) for part in match.groups()), tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_connection_line(line):
    """Fields of a connection_trace.txt line, or None when it is not five fields with a
    time in the second."""
    fields = [field.strip() for field in _SPACED.split(line.strip()) if field.strip()]
    if len(fields) != 5 or not _TEXT_TIME.match(fields[1]):
        return None
    return {'direction': fields[0], 'time': fields[1], 'status': fields[2],
            'id': fields[3], 'second_id': fields[4]}


def parse_transfer_line(line):
    """Fields of a file_transfer_trace.txt line, or None when it is not four tab
    separated fields after the mode with a time in the first."""
    fields = [field.strip() for field in line.split('\t') if field.strip()]
    if len(fields) != 5 or not _TEXT_TIME.match(fields[1]):
        return None
    item = _TRANSFER_ITEM.match(fields[4])
    return {'mode': fields[0], 'time': fields[1], 'event': fields[2], 'direction': fields[3],
            'name': item.group(1) if item else fields[4], 'size': item.group(2) if item else ''}


def parse_trace_line(line):
    """(level, datetime, time as stored, component, message) of a trace line, or None."""
    match = _TRACE_LINE.match(line)
    if not match:
        return None
    level, *parts = match.groups()[:8]
    component, message = match.group(10), match.group(11)
    try:
        stamp = datetime(*(int(p) for p in parts[:6]), int(parts[6]) * 1000, tzinfo=timezone.utc)
    except ValueError:
        stamp = None
    stored = f'{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:{parts[4]}:{parts[5]}.{parts[6]}'
    return level, stamp, stored, component, message


def match_trace_rule(component, message):
    """(event, value) for a reported trace line, or None."""
    for event, rule_component, pattern in _TRACE_RULES:
        if component != rule_component:
            continue
        found = pattern.match(message)
        if found:
            return event, found.group(1) if found.groups() else ''
    return None


def _read_files(context, label):
    """(relative path, text, source) for each file found."""
    results = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isdir(source):
            continue
        relative = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                text, replaced = decode_text(handle.read())
        except OSError as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        if replaced:
            logfunc(f'{label}: {relative}: {replaced} characters that could not be decoded replaced')
        results.append((relative, text, source))
    return results


@artifact_processor
def anyDeskConnections(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Time (as stored)', 'Direction', 'Status',
                    'Remote ID', 'Second ID Field', 'Line', 'Source File')
    data_list = []
    sources = []
    for relative, text, source in _read_files(context, 'AnyDesk Connections'):
        sources.append(source)
        utc = in_windows_folder(relative)
        read = unread = 0
        for number, line in enumerate(_LINE_BREAK.split(text), 1):
            if not line.strip():
                continue
            record = parse_connection_line(line)
            if record is None:
                unread += 1
                continue
            read += 1
            stamp = text_time(record['time']) if utc else None
            data_list.append((stamp or '', record['time'], record['direction'], record['status'],
                              record['id'], record['second_id'], number, relative))
        logfunc(f'AnyDesk Connections: {relative}: {read} lines read, {unread} non-blank lines not '
                f'in the five-field layout; times {"read as UTC" if utc else "left as stored"}')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def anyDeskFileTransfers(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Time (as stored)', 'Mode', 'Event', 'Direction',
                    'File Name', 'Size (as stored)', 'Line', 'Source File')
    data_list = []
    sources = []
    for relative, text, source in _read_files(context, 'AnyDesk File Transfers'):
        sources.append(source)
        utc = in_windows_folder(relative)
        read = unread = 0
        for number, line in enumerate(_LINE_BREAK.split(text), 1):
            if not line.strip():
                continue
            record = parse_transfer_line(line)
            if record is None:
                unread += 1
                continue
            read += 1
            stamp = text_time(record['time']) if utc else None
            data_list.append((stamp or '', record['time'], record['mode'], record['event'],
                              record['direction'], record['name'], record['size'], number, relative))
        logfunc(f'AnyDesk File Transfers: {relative}: {read} lines read, {unread} non-blank lines not '
                f'in the tab separated layout; times {"read as UTC" if utc else "left as stored"}')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def anyDeskTraceEvents(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Time (as stored)', 'Event', 'Value', 'Level',
                    'Component', 'Message', 'Line', 'Source File')
    data_list = []
    sources = []
    for relative, text, source in _read_files(context, 'AnyDesk Trace Events'):
        sources.append(source)
        dated = undated = reported = 0
        for number, line in enumerate(_LINE_BREAK.split(text), 1):
            if not line.strip():
                continue
            parsed = parse_trace_line(line)
            if parsed is None:
                undated += 1
                continue
            dated += 1
            level, stamp, stored, component, message = parsed
            found = match_trace_rule(component, message)
            if found is None:
                continue
            reported += 1
            data_list.append((stamp or '', stored, found[0], found[1], level, component, message,
                              number, relative))
        logfunc(f'AnyDesk Trace Events: {relative}: {dated} dated lines, {undated} other non-blank '
                f'lines; {reported} reported, {dated - reported} dated lines not reported')
    return data_headers, data_list, '\n'.join(sources)
