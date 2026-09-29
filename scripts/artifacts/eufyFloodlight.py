"""Recordings and log events a eufy floodlight camera keeps on its own storage, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "eufyFloodlightRecordings": {
        "name": "Eufy Floodlight Recordings",
        "description": "Recordings a eufy floodlight camera kept on its own storage, with the times their first "
                       "and last frames record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Eufy (Floodlight Camera)",
        "notes": "Reads the .dat files in the camera's Camera00 folder, one row per recording file, in name "
                 "order. The camera keeps them on an ext4 volume whose superblock records /mnt/data as where it "
                 "was last mounted, and its own log names each one under /mnt/data/Camera00 when it creates and "
                 "closes it. An eMMC image of the camera can hold that volume with no partition table, "
                 "which qnxprobe 1.51 and later find. A file is read only when it starts with the four "
                 "bytes XZYH, the magic eufy's container carries (The Dveloper, 'Reverse Engineering eufy "
                 "Security Camera Videos', https://thedveloper.com/blog/eufy-zxvideo-extraction), and it has to "
                 "be a whole number of records: each record is XZYH, a type byte, a byte, a 4-byte "
                 "little-endian length and 6 more bytes, then that many bytes of payload. Video Frames counts "
                 "the type 0x14 records, whose payloads held H.264 slices in the private sample, and Audio "
                 "Frames the type 0x15 records, whose payloads held AAC ADTS frames. A file that ends inside a record or holds "
                 "another type is counted in the run log and reported with Frame Time Note 'records not read' "
                 "and no frame times or counts. This layout, and the millisecond Unix time each record carries "
                 "(at byte 30 of a video record and byte 24 of an audio record), were field mapped from a "
                 "private sample, by comparing the record times with the Unix times in milliseconds the "
                 "camera's log writes for the same recording (its write_prebuf_record_file lines) and with "
                 "each file's modified time, which lies at the file's last frame. First Frame (UTC) and Last Frame (UTC) are the earliest and latest record times "
                 "in the file and Duration is the difference in seconds. A frame time before 2000 is not taken "
                 "as a date: First Frame (UTC) and Last Frame (UTC) are then blank and Frame Time Note gives "
                 "the first frame time as stored. The clock stamping the frames and the clock the log and "
                 "the file names use can differ, so such a recording can still carry a name and log lines "
                 "with a later date. Name Time is "
                 "the time in the file's name (YYYYMMDDhhmmss) as stored, with no zone recorded, and is not "
                 "converted; it is the time of the log line recording the file's creation (field mapped from "
                 "a private sample). The video is not decoded or shown: no sequence or picture "
                 "parameter set was found in the recordings of the private sample, so the frames cannot be "
                 "played as stored. The log can name recordings the folder no longer holds, and the "
                 "snapshots it names under /mnt/data/video were not on the volume in the private sample; Eufy "
                 "Floodlight Log Events lists those log lines.",
        "sample_data": {},
        "paths": ("*/Camera00/*.dat",),
        "output_types": "standard",
    },
    "eufyFloodlightLog": {
        "name": "Eufy Floodlight Log Events",
        "description": "Selected events from a eufy floodlight camera's own daily log files.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Eufy (Floodlight Camera)",
        "notes": "Reads the camera's log folder, files named sec.YYYY-MM-DD.log, on the same volume as its "
                 "Camera00 folder. A file is read only when one of its lines comes "
                 "from security_main.c or local_storage_interface.c, source file names the camera's log "
                 "carries, and each line is '<date> <time> [LEVEL][<source file>:<function>:<line>] - "
                 "<message>'. Where two lines were written into one, the second is split off at its own "
                 "date and time. Of the lines, only these are reported, each with the Event name given here "
                 "and the message as stored in Message: System Boot (security_main.c, main, 'system "
                 "bootup'), Self Reboot ('self reboot system'), Clock Not Set ('not system time'), Clock Set "
                 "('set system time:' followed by a Unix time in seconds, given in Time in Message (UTC)), "
                 "Motion Push (push_interface.c, zx_push_message) and Push Payload (thread_wipn_post, "
                 "'Payload'), Record Trigger (pir_triger_handle_by_channel, 'record trigger' or 'PIR "
                 "trigger'), Recording Created ('creat local file:'), Recording Closed ('close file:'), "
                 "Recording Uploaded (zx_upload_hub_history_record), Snapshot Uploaded (zx_putdata_aws_s3, "
                 "'success'), App Session Opened ('set p2p connect info start.'), App Session Closed ('clear "
                 "p2p connect info finished'), App Command (zx_p2p_command_read, a message naming an "
                 "APP_CMD_ command), Bind Mode ('bind mode start'), Motion Sensitivity ('sen_value ='), and "
                 "Wi-Fi Network ('connect wifi, bssid = <address>, ssid = <name>') and Internet IP ('internet "
                 "ip:<address>') only where the value differs from the previous such line in the same file, "
                 "because the camera writes them repeatedly; a blank or cut-short bssid is not taken "
                 "as a different access point, and an internet IP line with no address is not a change. Which lines are reported, and the Event names, were chosen from a "
                 "private sample; the names are this artifact's, and what each message means beyond its own "
                 "words is not established. Log Time is the time as the line stores it, with no zone "
                 "recorded, and it is not converted. The Unix time a Clock Set message "
                 "carries is converted in Time in Message (UTC), which is how a reading can be related to "
                 "UTC. Recording File is the name of the recording a message names, which Eufy Floodlight "
                 "Recordings lists; the log can name a recording the Camera00 folder no longer holds. Lines in no form above are counted in the run log.",
        "sample_data": {},
        "paths": ("*/log/sec.*.log",),
        "output_types": "standard",
    },
}

import os
import re
import struct
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

MAGIC = b'XZYH'
HEADER = 16
VIDEO, AUDIO = 0x14, 0x15
TIME_AT = {VIDEO: 30, AUDIO: 24}
CLOCK_SET_FROM = datetime(2000, 1, 1, tzinfo=timezone.utc)
NAME_RE = re.compile(r'^(\d{14})\.dat$')


def _utc_ms(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc)


def read_recording(data):
    """(video records, audio records, [record times in ms]) or None when data is not whole XZYH records."""
    pos, video, audio, times = 0, 0, 0, []
    size = len(data)
    while pos < size:
        if size - pos < HEADER or data[pos:pos + 4] != MAGIC:
            return None
        kind = data[pos + 4]
        length = struct.unpack_from('<I', data, pos + 6)[0]
        end = pos + HEADER + length
        if kind not in TIME_AT or end > size or length < TIME_AT[kind] + 8 - HEADER:
            return None
        times.append(struct.unpack_from('<Q', data, pos + TIME_AT[kind])[0])
        if kind == VIDEO:
            video += 1
        else:
            audio += 1
        pos = end
    return video, audio, times


def recording_row(name, data):
    """The report row for one recording file, or None when it does not start with the magic."""
    if not data.startswith(MAGIC):
        return None
    match = NAME_RE.match(name)
    name_time = ''
    if match:
        d = match.group(1)
        name_time = f'{d[0:4]}-{d[4:6]}-{d[6:8]} {d[8:10]}:{d[10:12]}:{d[12:14]}'
    parsed = read_recording(data)
    if parsed is None:
        return ('', '', '', name_time, '', '', 'records not read', len(data), name)
    video, audio, times = parsed
    first, last = _utc_ms(min(times)), _utc_ms(max(times))
    if first < CLOCK_SET_FROM:
        clock = f"stamped before 2000, first frame {first.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
        return ('', '', round((max(times) - min(times)) / 1000, 3), name_time, video, audio, clock,
                len(data), name)
    return (first, last, round((max(times) - min(times)) / 1000, 3), name_time, video, audio, '',
            len(data), name)


@artifact_processor
def eufyFloodlightRecordings(context):
    data_headers = (('First Frame (UTC)', 'datetime'), ('Last Frame (UTC)', 'datetime'), 'Duration (s)',
                    'Name Time', 'Video Frames', 'Audio Frames', 'Frame Time Note', 'Size (bytes)', 'File')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        if os.path.basename(os.path.dirname(path)) != 'Camera00':
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        row = recording_row(os.path.basename(path), data)
        if row is None:
            counts['files without the XZYH magic, not reported'] += 1
            continue
        if row[6] == 'records not read':
            counts['files whose records do not read'] += 1
        data_list.append(row[:-1] + (context.get_relative_path(path),))
        read.append(path)
    if counts:
        logfunc('Eufy Floodlight Recordings: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


LINE_RE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[([A-Z]+)\]\[([^\]:]+):([^\]:]+):(\d+)\] - ?(.*)$')
SPLIT_RE = re.compile(r'(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \[[A-Z]+\]\[)')
OWN_SOURCES = ('security_main.c', 'local_storage_interface.c')
RECORDING_RE = re.compile(r'/Camera00/(\d{14}\.dat)')
UNIX_S_RE = re.compile(r'set system time:(\d{9,10})\b')

# (event, source file, function or None for any, a substring the message must hold or None)
EVENTS = (
    ('System Boot', 'security_main.c', 'main', 'system bootup'),
    ('Self Reboot', None, None, 'self reboot system'),
    ('Clock Not Set', 'sys_interface.c', 'System_SetTime', 'not system time'),
    ('Clock Set', 'sys_interface.c', 'System_SetTime', 'set system time:'),
    ('Motion Push', 'push_interface.c', 'zx_push_message', None),
    ('Push Payload', 'push_interface.c', 'thread_wipn_post', 'Payload'),
    ('Record Trigger', 'local_storage_interface.c', 'pir_triger_handle_by_channel', 'record trigger'),
    ('Record Trigger', 'local_storage_interface.c', 'pir_triger_handle_by_channel', 'PIR trigger'),
    ('Recording Created', 'local_storage_interface.c', None, 'creat local file:'),
    ('Recording Closed', 'local_storage_interface.c', None, 'close file:'),
    ('Recording Uploaded', 'as_interface.c', 'zx_upload_hub_history_record', None),
    ('Snapshot Uploaded', 'cloud_storage_interface.c', 'zx_putdata_aws_s3', 'success'),
    ('App Session Opened', 'ppcs_interface.c', 'zx_set_p2p_connect_info', 'set p2p connect info start.'),
    ('App Session Closed', 'ppcs_interface.c', 'zx_clear_p2p_connect_info', 'clear p2p connect info finished'),
    ('App Command', 'ppcs_interface.c', 'zx_p2p_command_read', 'APP_CMD_'),
    ('Bind Mode', None, 'zx_fd_key_bind_thread', 'bind mode start'),
    ('Motion Sensitivity', None, 'zx_fd_set_motion_sensivity', 'sen_value ='),
)
# Written every few seconds; reported only where the value changes within a file.
WIFI_RE = re.compile(r'connect wifi, bssid = ([^,]*), ssid = (.*)$')
MAC_RE = re.compile(r'^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')
IP_RE = re.compile(r'internet ip:(\S+)')


def changed_value(message):
    """(event, value) for a line reported only on a change, or (None, None).

    A Wi-Fi line whose bssid is not a whole address, and an internet IP line with no
    address, say nothing new, so they give no value and never count as a change."""
    if 'connect wifi,' in message:
        match = WIFI_RE.search(message)
        if not match:
            return None, None
        bssid, ssid = match.group(1).strip(), match.group(2).strip()
        return 'Wi-Fi Network', (ssid, bssid if MAC_RE.match(bssid) else None)
    if 'internet ip:' in message:
        match = IP_RE.search(message)
        return ('Internet IP', match.group(1)) if match else (None, None)
    return None, None


def split_lines(text):
    """Each (line number, record) in the text, a record written into another line split off at its time."""
    for number, line in enumerate(text.splitlines(), 1):
        for part in SPLIT_RE.split(line):
            if part.strip():
                yield number, part.rstrip()


def is_own_log(text):
    for _number, record in split_lines(text):
        match = LINE_RE.match(record)
        if match and match.group(3) in OWN_SOURCES:
            return True
    return False


def log_rows(text, counts):
    """(log time, event, message, recording file, time in message, level, source, line) per reported line."""
    rows, last = [], {}
    for number, record in split_lines(text):
        match = LINE_RE.match(record)
        if not match:
            counts['lines in no known form, not reported'] += 1
            continue
        when, level, source, function, source_line, message = match.groups()
        event = None
        for name, want_source, want_function, needle in EVENTS:
            if ((want_source is None or source == want_source)
                    and (want_function is None or function == want_function)
                    and (needle is None or needle in message)):
                event = name
                break
        if event is None:
            name, value = changed_value(message)
            if name == 'Wi-Fi Network':
                ssid, bssid = value
                known = last.get(name)
                if bssid is None and known is not None and known[0] == ssid:
                    value = known                   # same network, address not written this time
            if name is not None and last.get(name) != value:
                last[name] = value
                event = name
        if event is None:
            continue
        recording = RECORDING_RE.search(message)
        stated = UNIX_S_RE.search(message)
        rows.append((when, event, message, recording.group(1) if recording else '',
                     datetime.fromtimestamp(int(stated.group(1)), timezone.utc) if stated else '',
                     level, f'{source}:{function}:{source_line}', number))
    return rows


@artifact_processor
def eufyFloodlightLog(context):
    data_headers = ('Log Time', 'Event', 'Message', 'Recording File', ('Time in Message (UTC)', 'datetime'),
                    'Level', 'Source', 'Line', 'Log File')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        if not re.match(r'^sec\.\d{4}-\d{2}-\d{2}\.log$', os.path.basename(path)):
            continue
        try:
            with open(path, 'rb') as handle:
                text = handle.read().decode('utf-8', 'replace')
        except OSError:
            counts['files that could not be read'] += 1
            continue
        if not is_own_log(text):
            counts['files with no line from the camera program, not read'] += 1
            continue
        relative = context.get_relative_path(path)
        for row in log_rows(text, counts):
            data_list.append(row + (relative,))
        read.append(path)
    if counts:
        logfunc('Eufy Floodlight Log Events: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
