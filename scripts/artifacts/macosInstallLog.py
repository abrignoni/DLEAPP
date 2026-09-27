"""Entries in the macOS install log, private/var/log/install.log and its rotated copies, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosInstallLog": {
        "name": "Install Log",
        "description": "Entries in private/var/log/install.log and its rotated copies: time as "
                       "written, host, process, PID and message, with the time in UTC where the "
                       "line records its offset.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Installed Software (macOS)",
        "notes": "Reads install.log in a folder ending var/log (private/var/log on a Mac) and its rotated "
                 "copies install.log.N and install.log.T followed by a number, gunzipping any copy that "
                 "starts with the gzip signature, oldest first: the highest N first, then T copies in the "
                 "order of their numbers, then install.log. Other names are not read. Both tested Mac "
                 "images carry the same rule for the install facility in "
                 "private/etc/asl/com.apple.install, which writes each message in the format "
                 "'$((Time)(JZ)) $Host $(Sender)[$(PID)]: $Message' and rotates the file with rotate=seq "
                 "and compress. Apple's syslog source writes a JZ time as the local date and time followed "
                 "by the offset from UTC that the local time zone gives for that moment, as +hh, or +hh:mm "
                 "when the offset has minutes "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/libsystem_asl.tproj/src/asl_msg.c#L1940-L1958), "
                 "and Timestamp (UTC) is that time converted with the offset the line carries. Apple's "
                 "asl.conf manual names seq copies with N counting up from 0, the most recent "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/syslogd.tproj/asl.conf.5#L684-L690), "
                 "appends .gz to a compressed copy "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/syslogd.tproj/asl.conf.5#L565-L569), "
                 "and says a seq copy is first named for its creation time in seconds since 1970 (its "
                 "example is example.log.T1340607600) until aslmanager renumbers it "
                 "(https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/syslogd.tproj/asl.conf.5#L649-L652 "
                 "and "
                 "https://github.com/apple-oss-distributions/syslog/blob/69d8586e9a599c304e1b702a9c2830e2f78126d5/syslogd.tproj/asl.conf.5#L700-L704). "
                 "No tested image held a rotated copy, so reading them is exercised only by the module's "
                 "tests. Lines of the form 'Mmm dd hh:mm:ss host process[pid]: message' carry no year and "
                 "no offset: Time as Written holds them as stored and Timestamp (UTC) is blank. A line of "
                 "neither form is joined, after a line break, to the message of the entry above it, one "
                 "before a file's first entry is reported as an entry with only a message, and a file with "
                 "no line of either form is logged and not read. On dleapp_macos_bigsur the file's 22,510 "
                 "lines gave 16,167 entries, 6,193 with an offset (-08 on 4,189 and -05 on 2,004) and "
                 "9,974 without, and 822 entries run over more than one line. When a logical extraction "
                 "holds the log folder at its root and again under System/Volumes/Data/, the two copies "
                 "are one log captured twice: an entry (time as written, host, process, PID and message) "
                 "is reported as many times as the copy holding it most often does, from the copy with "
                 "more entries first, and the run log counts the entries not reported again. The public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) holds "
                 "install.log both ways: the copy at the root, 1,614,675 bytes, is the first 1,614,675 "
                 "bytes of the copy under System/Volumes/Data, 1,633,138, so the root copy's 10,452 "
                 "entries were each reported once, from the other copy's 10,562: 10,321 with an offset "
                 "(-07, -08 or -05) and 241 without. The lines of the form Installed \"<name>\" (<version>) "
                 "were checked against InstallHistory.plist on both images: converted to UTC, each fell on "
                 "the same second as an entry with the same name and version, 13 of 13 against 16 entries "
                 "on dleapp_macos_bigsur, whose other 3 are the macOS 11.0.1, 11.1 and 11.2.1 updates, and "
                 "19 of 19 against 21 on the MacBook Pro, whose other 2 are XProtectCloudKitUpdate "
                 "entries. Bytes that are not valid UTF-8 are shown as the Unicode replacement character; "
                 "there were none in the tested files.",
        "paths": ('*/var/log/install.log', '*/var/log/install.log.*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 16,167 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import gzip
import os
import re
import zlib
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

# A line the install rule writes: local time, then its offset from UTC, host, sender[pid]: message.
_OFFSET_LINE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})([+-]\d{2}(?::\d{2})?) (\S+) '
                          r'(.+?)\[(\d+)\]: ?(.*)$')
# A line with no year and no offset: Mmm dd hh:mm:ss host sender[pid]: message.
_ZONELESS_LINE = re.compile(r'^([A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2}) (\S+) (.+?)\[(\d+)\]: ?(.*)$')
# install.log, a sequenced rotation (install.log.N) or a checkpoint named for its creation time
# (install.log.T<seconds>), either one gzip compressed.
_NAME = re.compile(r'install\.log(?:(?:\.(\d+)|\.T(\d+))(?:\.gz)?)?')
_FIRMLINK = re.compile(r'(^|/)System/Volumes/Data/')


def _utc(written, offset):
    """The UTC datetime of a local time and its +hh or +hh:mm offset, or '' when not a real time."""
    try:
        local = datetime.strptime(written, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return ''
    hours, _, minutes = offset[1:].partition(':')
    delta = timedelta(hours=int(hours), minutes=int(minutes or 0))
    return (local + delta if offset[0] == '-' else local - delta).replace(tzinfo=timezone.utc)


def _order(path):
    """Sort key putting a folder's install logs oldest first: highest sequence number first, then
    checkpoints by creation time, then the live install.log."""
    match = _NAME.fullmatch(os.path.basename(path))
    if match.group(1) is not None:
        return (0, -int(match.group(1)))
    if match.group(2) is not None:
        return (1, int(match.group(2)))
    return (2, 0)


def _read(path):
    """The file's text, gunzipped when it starts with the gzip magic, or None when it cannot be read."""
    try:
        with open(path, 'rb') as handle:
            magic = handle.read(2)
        opener = gzip.open if magic == b'\x1f\x8b' else open
        with opener(path, 'rb') as handle:
            data = handle.read()
    except (OSError, EOFError, zlib.error):
        return None
    return data.decode('utf-8', errors='replace')


def _entries(text):
    """(utc, written, host, process, pid, message) per entry; a line of neither shape is joined to the
    entry above it, and text before a file's first entry becomes an entry with only a message."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    entries = []
    for line in lines:
        match = _OFFSET_LINE.match(line)
        if match:
            written, offset, host, process, pid, message = match.groups()
            entries.append([_utc(written, offset), written + offset, host, process, int(pid), [message]])
            continue
        match = _ZONELESS_LINE.match(line)
        if match:
            written, host, process, pid, message = match.groups()
            entries.append(['', written, host, process, int(pid), [message]])
        elif entries:
            entries[-1][5].append(line)
        else:
            entries.append(['', '', '', '', '', [line]])
    return [tuple(entry[:5]) + ('\n'.join(entry[5]),) for entry in entries]


@artifact_processor
def macosInstallLog(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Time as Written', 'Host', 'Process', 'PID',
                    'Message', 'Source File')
    data_list = []
    sources = []
    stores = {}
    for path in context.get_files_found():
        if os.path.isdir(path) or not _NAME.fullmatch(os.path.basename(path)):
            continue
        folder = os.path.dirname(context.get_relative_path(path)).replace('\\', '/')
        stores.setdefault(_FIRMLINK.sub(r'\1', folder, count=1), {}).setdefault(folder, []).append(path)
    repeated = 0
    for views in stores.values():
        read = []
        for folder in sorted(views):
            rows = []
            for path in sorted(views[folder], key=_order):
                text = _read(path)
                if text is None:
                    logfunc(f'Install Log: could not read {context.get_relative_path(path)}')
                    continue
                entries = _entries(text)
                if not any(entry[1] for entry in entries):
                    logfunc(f'Install Log: no install log line in {context.get_relative_path(path)}')
                    continue
                rows.extend((entry, path) for entry in entries)
            read.append(rows)
        # Copies of one folder under two views (a logical extraction reaching the Data volume
        # both at the root and under System/Volumes/Data) are one log captured twice: each entry
        # is reported as many times as the copy holding it most often does.
        wanted = Counter()
        for rows in read:
            wanted |= Counter(entry for entry, _path in rows)
        done = Counter()
        for rows in sorted(read, key=len, reverse=True):
            for entry, path in rows:
                if done[entry] < wanted[entry]:
                    done[entry] += 1
                    data_list.append(entry + (context.get_relative_path(path),))
                    if path not in sources:
                        sources.append(path)
                else:
                    repeated += 1
    if repeated:
        logfunc(f'Install Log: {repeated} entries held by both views of one log folder reported once')
    logfunc(f'Install Log: {len(data_list)} entries from {len(sources)} file(s).')
    return data_headers, data_list, '\n'.join(sources)
