"""Lines in the macOS Wi-Fi log, private/var/log/wifi.log and its rotated copies, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosWifiLogEvents": {
        "name": "Wi-Fi Log Events",
        "description": "Lines in private/var/log/wifi.log, its rotated copies and wifi-*.log files that name networks, "
                       "interfaces, sleep and wake, the power source, IP and router addresses, the user line or USB "
                       "devices, with the time as written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads wifi.log in a folder ending var/log (private/var/log on a Mac), its rotated copies "
                 "wifi.log.N and wifi.log.N.bz2, and files named wifi-*.log in the same folder, decompressing any "
                 "copy that starts with the bzip2 signature; other names are not read. A folder's files are read "
                 "oldest first: the highest N first, then wifi-*.log files by name, then wifi.log. What the lines "
                 "mean is not established from a documenting source, so the module names nothing the line does "
                 "not say. The headers Process, PID, Interface, SSID, BSSID and File and Line are the module's "
                 "names for positions in the line; the lines use such a word themselves only in the wifi.ssid. "
                 "ids, the id= of REMEMBER WIFI NETWORK, and 'for interface'. Lines are read in the forms seen on "
                 "the tested images: on macOS 15.4 a time, [process]/pid, a number in @[ ], text in parentheses "
                 "(a name ending .m, a colon and a number on every tested line) and the message; on macOS 11.2.1 "
                 "and 14.6.1 a time, an optional category followed by a colon (such as AutoJoin or Driver Event), "
                 "the process name in angle brackets, with its pid in square brackets where written, and the "
                 "message; on all of them a time followed by text, such as the Usb Host Notification lines; and, "
                 "on the two logical extractions, the newsyslog line 'Mmm dd hh:mm:ss host newsyslog[pid]: "
                 "logfile turned over'. A line with a time and no process header, other than a Usb Host "
                 "Notification line, is joined to the entry above after a line break, its text alone when its "
                 "time is the entry's time and the whole line when it is not; on the tested images every entry "
                 "with joined lines either ends its first line with an opening bracket (such as 'optimized "
                 "channel list {(' or 'ARP offload settings ({') or is followed by a line holding its time and "
                 "nothing else. A line holding a time and then a whole line with a time of its own, which looks "
                 "like two writes run together, is two entries, the first with only that time; a macOS 15 line "
                 "with no time before it has a blank Time (as written); a line in no known form is reported with "
                 "only a message; blank lines are not reported; the run log counts each kind. An entry is "
                 "reported here when its first line is one of: caps (Detail is its description value, beginning "
                 "DarkWake, Sleep or FullWake on the tested lines), Acknowledging sleep event, driver "
                 "unavailable, driver available, WoW ENABLED, WoW successfully ENABLED, IPV4 State change, IP "
                 "Address, IP subnet mask, Router IP Address, Default Gateway IP Address, Router MAC Address, Usb "
                 "Host Notification hostNotificationUSBDeviceInserted or hostNotificationUSBDeviceRemoved (Detail "
                 "is the text between the event word and seqNum, which on inserted lines ends isApple Y or N), "
                 "Adding network, __filteredScanResultsForAutoJoin, REMEMBER WIFI NETWORK, SET WIFI PASSWORD, the "
                 "WIFICLOUDSYNC lines CLOUD --> LOCAL, LOCAL --> CLOUD and added network that name a network in "
                 "angle brackets, AUTO-JOIN STARTED, COMPLETED or DEFERRED, AUTO-HOTSPOT STARTED or COMPLETED, "
                 "airportdProcessDLILEvent naming an interface, _interfaceFlagsChanged, a "
                 "_bsd_80211_event_callback driver event other than SCAN_CACHE_UPDATED, psCallback powerSource, "
                 "REACHABILITY, user and no user logged in. Event (as written) is those words as the line writes "
                 "them, and what each records beyond its words is not established. Interface, SSID, BSSID, "
                 "Network ID (as stored) and Detail are text from the same line. SSID holds the text the line "
                 "quotes or puts in angle brackets, (null) as stored on every tested "
                 "__filteredScanResultsForAutoJoin line; the Adding network id itself begins wifi.ssid., and the "
                 "WIFICLOUDSYNC lines do not say what the bracketed text is; a REMEMBER WIFI NETWORK line carries "
                 "only an id, wifi.ssid. followed by hex digits, and SSID is those digits decoded as UTF-8, which "
                 "on the 36 Adding network lines equalled the quoted name on all 36. Every other entry is in "
                 "Wi-Fi Log Other Entries, so the two artifacts together hold every entry. Time (as written) is "
                 "the line's time as stored: weekday, month, day and time to the millisecond, with no year and no "
                 "offset from UTC (the newsyslog lines have neither weekday nor milliseconds). No source says "
                 "what clock or offset the writer used, so it is reported as text and not converted. On the "
                 "public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) one "
                 "other record puts it five hours behind UTC and a second observation is consistent with that: "
                 "the one IP Address line, Dec 24 16:48:50.952 as written, read as five hours behind UTC, is "
                 "1.952 seconds after the LeaseStartDate of 21:48:49 UTC in the root copy of "
                 "private/var/db/dhcpclient/leases/en0.plist, and, taking the year as 2025, the time as written "
                 "less the @[ ] value fell between 10:48:21 and 10:48:36 on Dec 12 on all 103,680 entries "
                 "carrying both, while the utmpx BOOT_TIME record is 15:48:19 UTC that day. On "
                 "magnet2021_macos_bigsur the lines after the 00:30 rotation line in wifi.log.0.bz2 begin at Apr "
                 "5 16:04:36.635 as written, about 12 seconds before the utmpx BOOT_TIME of 20:04:48 UTC less "
                 "four hours, which fits an offset of four hours behind UTC without proving it; no record of the "
                 "same moment was compared on the other two images. What the @[ ] value counts is not "
                 "established. When a logical extraction holds the log folder at its root and again under "
                 "System/Volumes/Data/ or System/Volumes/Update/mnt1/, the copies are read as one log captured "
                 "more than once; a rotation between the captures would give the same lines different names, "
                 "which is what this comparison shows: on mvs2026_macbookpro_macos15 the root copies of "
                 "wifi.log.0.bz2 to wifi.log.9.bz2 are byte-identical to the System/Volumes/Data copies of "
                 "wifi.log.1.bz2 to wifi.log.10.bz2, and the root wifi.log is the start of the Data copy of "
                 "wifi.log.0.bz2. So the views are read as one log: an entry (every header field and the message) "
                 "is reported as many times as the view holding it most often does, from the view with more "
                 "entries first, and the run log counts entries not reported again. Its 24 files, 14 distinct, "
                 "hold 193,142 lines in both views; they gave 103,766 entries, 515 here (169 caps, 169 "
                 "Acknowledging sleep event, 57 hostNotificationUSBDeviceRemoved, 56 driver unavailable, 56 "
                 "driver available, 2 IPV4 State change, one WoW ENABLED and one each of the five lines from IP "
                 "Address to Router MAC Address) and 103,251 in the other artifact, 4,113 of which only the "
                 "System/Volumes/Data view held. Two of its lines held two times and two had no time, each in "
                 "both views. A search of its lines for ssid found none, and SSID, BSSID and Network ID (as "
                 "stored) held no value on any of its rows. On the Magnet 2021 CTF macOS logical extraction "
                 "(macOS 11.2.1, corpus key magnet2021_macos_bigsur) the folder is held under three views with "
                 "identical files: 13 files of 14,399 lines, 9,308 of them joined to the entry above, gave 5,091 "
                 "entries, 466 here and 4,625 in the other artifact. Its rotated copies and wifi.log hold only "
                 "newsyslog lines apart from wifi.log.0.bz2, and it holds one wifi-*.log file of 14,299 lines "
                 "whose last line is a DUMP_LOGS driver event one millisecond before the time in its name; 51 of "
                 "its entries are also in wifi.log.0.bz2, and since both files are read those 51 are reported "
                 "from each. Its 466 rows include 243 __filteredScanResultsForAutoJoin rows naming 15 BSSIDs, 36 "
                 "Adding network rows, 36 AUTO-JOIN STARTED, 35 AUTO-JOIN COMPLETED and one AUTO-JOIN DEFERRED, "
                 "23 each of AUTO-HOTSPOT STARTED and COMPLETED, 30 user and 12 no user logged in rows, and 4 "
                 "hostNotificationUSBDevice rows. Every AUTO-JOIN COMPLETED, AUTO-JOIN DEFERRED and AUTO-HOTSPOT "
                 "COMPLETED line there returned 'failure', and a search of the tested files for associat, "
                 "onnected, LINK_CHANGED, SSID_CHANGED and BSSID_CHANGED found no line, so lines written for an "
                 "association, a disconnection or a join that succeeded, if wifi.log holds any, are not "
                 "recognised and go to the other artifact; an image whose wifi.log records a Wi-Fi association "
                 "would close that gap. dleapp_macos_bigsur (macOS 11.2.1) and evidencelocker_macos14 (macOS "
                 "14.6.1) each hold one wifi.log and no other file matching the declared paths, of 35 and 61 "
                 "lines: 30 and 17 rows here, all hostNotificationUSBDevice lines, which carry no process header, "
                 "so Interface, SSID, BSSID, Network ID (as stored), Process and PID held no value on any of "
                 "their rows; on dleapp_macos_bigsur Event (as written) held one value, "
                 "hostNotificationUSBDeviceInserted, on all 30 rows. Category (as written) is filled only in the "
                 "macOS 11 and 14 form, so it held no value on any row of mvs2026_macbookpro_macos15, and File "
                 "and Line (as written) and @[ ] Value (as stored) only in the macOS 15 form, so they held no "
                 "value on any row of the other three images; Category (as written) held no value on any row of "
                 "dleapp_macos_bigsur or evidencelocker_macos14 either. Known Wi-Fi Networks and Biome Wi-Fi "
                 "Connections read other records of networks. Bytes that are not valid UTF-8 are shown as the "
                 "Unicode replacement character.",
        "paths": ('*/var/log/wifi.log', '*/var/log/wifi.log.*', '*/var/log/wifi-*.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "wifi",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 30 rows",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 17 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 466 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 515 rows",
        },
    },
    "macosWifiLogEntries": {
        "name": "Wi-Fi Log Other Entries",
        "description": "Entries in private/var/log/wifi.log, its rotated copies and "
                       "wifi-*.log files that Wi-Fi Log Events does not report, with the "
                       "time as written and the line's other header fields as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads the same files as Wi-Fi Log Events, in the same order and with the same rules for line "
                 "forms, joined lines and volume views (see that artifact's notes, which also say what Time (as "
                 "written) is relative to), and reports every entry Wi-Fi Log Events does not, so the two "
                 "artifacts together hold every entry. Message holds the entry's text after its header, with any "
                 "joined lines after line breaks; Host is filled only on the newsyslog lines. On "
                 "mvs2026_macbookpro_macos15 (macOS 15.4) this gives 103,251 rows, above the 50,000-row limit for "
                 "HTML pages, so the table is in the TSV and LAVA output only: 74,548 are Processed events lines "
                 "and 28,418 Health check alive lines, 4,113 rows only the System/Volumes/Data view held, and "
                 "Category (as written) held no value on any row. On magnet2021_macos_bigsur (macOS 11.2.1) it "
                 "gives 4,625 rows, among them scan, query and monitoring requests from other processes, "
                 "_bsd_80211_event_callback SCAN_CACHE_UPDATED lines, WIFICLOUDSYNC lines other than the three "
                 "forms Wi-Fi Log Events reports, kernel lines and the newsyslog rotation lines, and File and "
                 "Line (as written) and @[ ] Value (as stored) held no value on any row. On dleapp_macos_bigsur "
                 "(macOS 11.2.1) it gives 5 rows, and Message held one value, Usb Host Notification activated, on "
                 "all 5, with Process, PID, Category (as written), File and Line (as written), @[ ] Value (as "
                 "stored) and Host holding no value on any of them. On evidencelocker_macos14 (macOS 14.6.1) it "
                 "gives 44 rows, and Category (as written), File and Line (as written), @[ ] Value (as stored) "
                 "and Host held no value on any of them.",
        "paths": ('*/var/log/wifi.log', '*/var/log/wifi.log.*', '*/var/log/wifi-*.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "wifi",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 5 rows",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 44 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 4,625 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 103,251 rows",
        },
    },
}

import bz2
import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

_TIME = r'(?P<time>[A-Z][a-z]{2} [A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2}\.\d{3})'
# The form seen on macOS 15: time, [process]/pid, @[number], (file:line), message.
_BRACKET_LINE = re.compile(_TIME + r' \[(?P<process>[^\]]+)\]/(?P<pid>\d+) @\[(?P<at>[^\]]*)\] '
                           r'\((?P<location>[^)]*)\) ?(?P<message>.*)$')
# The form seen on macOS 11 and 14: time, an optional "Category: ", <process[pid]>, message.
_ANGLE_LINE = re.compile(_TIME + r' (?:(?P<category>[A-Za-z0-9][A-Za-z0-9 ]*?): )?'
                         r'<(?P<process>[^>\[]+)(?:\[(?P<pid>\d+)\])?> ?(?P<message>.*)$')
# The macOS 15 form with no time before it.
_UNTIMED_BRACKET_LINE = re.compile(r'\[(?P<process>[^\]]+)\]/(?P<pid>\d+) @\[(?P<at>[^\]]*)\] '
                                   r'\((?P<location>[^)]*)\) ?(?P<message>.*)$')
# A time followed directly by another time: two writes run together on one line.
_DOUBLED_TIME = re.compile(_TIME + r' (?=[A-Z][a-z]{2} [A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2}\.\d{3} )')
# A time followed by text with neither header.
_TIMED_LINE = re.compile(_TIME + r' ?(?P<message>.*)$')
# The line newsyslog writes when it rotates the file: Mmm dd hh:mm:ss host process[pid]: message.
_SYSLOG_LINE = re.compile(r'(?P<time>[A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2}) (?P<host>\S+) '
                          r'(?P<process>[^\s\[]+)\[(?P<pid>\d+)\]: ?(?P<message>.*)$')
_USB = 'Usb Host Notification'

_NAME = re.compile(r'wifi\.log(?:\.(\d+)(?:\.bz2)?)?|wifi-.+\.log')
_FIRMLINK = re.compile(r'(^|/)(?:System/Volumes/Update/mnt1/|System/Volumes/Data/)+')
_MAC = r'[0-9A-Fa-f]{1,2}(?::[0-9A-Fa-f]{1,2}){5}'

# (pattern for the first line of an entry's message, event name when the pattern names none).
# Each event is the line's own words as written; nothing is named that the line does not say.
_EVENTS = [
    (re.compile(r"^caps = .*?description:'(?P<detail>[^']*)'"), 'caps'),
    (re.compile(r'^(?P<event>Acknowledging sleep event)\b'), ''),
    (re.compile(r'^(?P<event>driver (?:un)?available) \((?P<detail>[^)]*)\)'), ''),
    (re.compile(r'^Usb Host Notification (?P<iface>[a-z]+\d+) (?P<event>driver available)\b'), ''),
    (re.compile(r'^Usb Host Notification (?P<event>hostNotificationUSBDevice(?:Inserted|Removed)) '
                r'(?P<detail>.+?) seqNum \d+ Total \d+$'), ''),
    (re.compile(r'^(?P<event>WoW ENABLED) \((?P<detail>.*)\)$'), ''),
    (re.compile(r'^(?P<event>WoW successfully ENABLED) on (?P<iface>\S+)$'), ''),
    (re.compile(r'^(?P<event>IPV4 State change) for (?P<iface>\S+)$'), ''),
    (re.compile(r'^(?P<event>IP Address|IP subnet mask|Router IP Address|Default Gateway IP Address|'
                r'Router MAC Address): (?P<detail>\S+)$'), ''),
    (re.compile(r"^Adding network \['(?P<ssid>.*)' \((?P<netid>wifi\.ssid\.[0-9A-Fa-f]*)\) - "
                r"(?P<detail>.*)\]$"), 'Adding network'),
    (re.compile(r"^__filteredScanResultsForAutoJoin: \['(?P<ssid>.*)' - (?P<bssid>" + _MAC + r")\] "
                r"(?P<detail>.*)$"), '__filteredScanResultsForAutoJoin'),
    (re.compile(r'^(?P<event>REMEMBER WIFI NETWORK) \(id=(?P<netid>wifi\.ssid\.[0-9A-Fa-f]*) '
                r'(?P<detail>[^)]*)\) (?P<detail2>request received from .*)$'), ''),
    (re.compile(r'^(?P<event>SET WIFI PASSWORD) request received from (?P<detail>.*)$'), ''),
    (re.compile(r'^WIFICLOUDSYNC \S+: (?P<event>CLOUD --> LOCAL|LOCAL --> CLOUD): <(?P<ssid>.*?)> '
                r'(?P<detail>.*)$'), ''),
    (re.compile(r'^WIFICLOUDSYNC \S+: (?P<event>added network) <(?P<ssid>.*?)> '
                r'(?P<detail>to waiting for password sync list)$'), ''),
    (re.compile(r'^(?P<event>AUTO-JOIN (?:STARTED|COMPLETED|DEFERRED)|AUTO-HOTSPOT (?:STARTED|COMPLETED)) '
                r'for interface (?P<iface>[^\s,(]+)[ ,]*(?P<detail>.*)$'), ''),
    (re.compile(r'^airportdProcessDLILEvent: (?P<iface>[a-z]+\d+) (?P<detail>\S.*)$'),
     'airportdProcessDLILEvent'),
    (re.compile(r'^_interfaceFlagsChanged: (?P<iface>\S+) (?P<detail>transitioning from .*?)\.?$'),
     '_interfaceFlagsChanged'),
    (re.compile(r'^_bsd_80211_event_callback: (?P<event>(?!SCAN_CACHE_UPDATED\b)[A-Z][A-Z0-9_]+) '
                r'\((?P<iface>[^)]+)\)$'), ''),
    (re.compile(r'^psCallback: (?P<event>powerSource) = (?P<detail>.+)$'), ''),
    (re.compile(r'^<(?P<iface>[^>]+)> (?P<event>REACHABILITY) \[(?P<detail>[^\]]*)\]$'), ''),
    (re.compile(r'^(?P<event>user): (?P<detail>.+)$'), ''),
    (re.compile(r'^(?P<event>no user logged in)$'), ''),
]


def _ssid_from_id(netid):
    """The text of a wifi.ssid.<hex> network id, or '' when the hex does not decode."""
    try:
        return bytes.fromhex(netid[len('wifi.ssid.'):]).decode('utf-8')
    except ValueError:
        return ''


def _order(path):
    """Sort key putting a folder's Wi-Fi logs oldest first: highest rotation number first, then
    wifi-<time>.log files by name, then the live wifi.log."""
    name = os.path.basename(path)
    match = _NAME.fullmatch(name)
    if match.group(1) is not None:
        return (0, -int(match.group(1)), name)
    if name.startswith('wifi-'):
        return (1, 0, name)
    return (2, 0, name)


def _read(path):
    """The file's text, bunzipped when it starts with the bzip2 signature, or None when it cannot be read."""
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
        if data[:3] == b'BZh':
            data = bz2.decompress(data)
    except (OSError, EOFError, ValueError):
        return None
    return data.decode('utf-8', errors='replace')


def _entry(number, form, fields):
    return {'form': form, 'line': number, 'time': fields.get('time') or '',
            'process': fields.get('process') or '', 'pid': fields.get('pid') or '',
            'category': fields.get('category') or '', 'location': fields.get('location') or '',
            'at': fields.get('at') or '', 'host': fields.get('host') or '',
            'message': fields.get('message') or '', 'more': []}


def _entries(text, counts):
    """One dict per entry, in the file's order.

    A line with a time and no header that is not a USB host notification is joined to the entry
    above after a line break: its text alone when its time is the entry's time, the whole line as
    written when it is not. A line holding a time and then a whole line of its own is two entries,
    the first with only that time. A line of no known form is an entry with only a message. Blank
    lines are counted and not reported.
    """
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    entries = []
    for number, line in enumerate(lines, 1):
        counts['lines'] += 1
        line = line.rstrip('\r')
        if not line.strip():
            counts['blank'] += 1
            continue
        doubled = _DOUBLED_TIME.match(line)
        if doubled:
            counts['doubled'] += 1
            entries.append(_entry(number, 'time only', {'time': doubled.group('time')}))
            line = line[doubled.end():]
        fields = None
        for form, pattern in (('bracket', _BRACKET_LINE), ('angle', _ANGLE_LINE)):
            match = pattern.match(line)
            if match:
                fields = match.groupdict()
                break
        if fields is None:
            match = _TIMED_LINE.match(line)
            if match:
                fields, form = match.groupdict(), 'timed'
                if entries and entries[-1]['form'] != 'time only' and not fields['message'].startswith(_USB):
                    same = entries[-1]['time'] == fields['time']
                    entries[-1]['more'].append(fields['message'] if same else line)
                    counts['joined'] += 1
                    continue
        if fields is None:
            for form, pattern in (('bracket', _UNTIMED_BRACKET_LINE), ('syslog', _SYSLOG_LINE)):
                match = pattern.match(line)
                if match:
                    fields = match.groupdict()
                    counts['untimed'] += form == 'bracket'
                    break
        if fields is None:
            form, fields = '', {'message': line}
            counts['unmatched'] += 1
        entries.append(_entry(number, form, fields))
    return entries


def _event(entry):
    """(event, interface, ssid, bssid, network id, detail) when the entry's first line is one the
    events table reports, else None."""
    if entry['form'] not in ('bracket', 'angle', 'timed'):
        return None
    for pattern, name in _EVENTS:
        match = pattern.match(entry['message'])
        if match:
            found = match.groupdict()
            netid = found.get('netid') or ''
            ssid = found.get('ssid')
            if ssid is None:
                ssid = _ssid_from_id(netid) if netid else ''
            detail = '; '.join(part.strip() for part in (found.get('detail'), found.get('detail2')) if part)
            return (found.get('event') or name, found.get('iface') or '', ssid, found.get('bssid') or '',
                    netid, detail)
    return None


def _key(entry):
    return (entry['time'], entry['process'], entry['pid'], entry['category'], entry['location'],
            entry['at'], entry['host'], entry['message'], tuple(entry['more']))


def _records(context, label):
    """(records, sources, counts): (entry, path) for every entry to report.

    Copies of one log folder under several volume views (a logical extraction reaching the Data
    volume at the root and under System/Volumes/Data) are one log captured more than once, and a
    rotation between the captures gives the same lines different file names in each, so the views
    are read as one log: each entry is reported as many times as the view holding it most often
    does, from the view with more entries first.
    """
    stores = {}
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.isdir(path) or not _NAME.fullmatch(os.path.basename(path)):
            continue
        folder = os.path.dirname(context.get_relative_path(path)).replace('\\', '/')
        stores.setdefault(_FIRMLINK.sub(r'\1', folder, count=1), {}).setdefault(folder, []).append(path)
    counts = Counter()
    records, sources = [], []
    for views in stores.values():
        read = []
        for folder in sorted(views):
            rows = []
            for path in sorted(views[folder], key=_order):
                text = _read(path)
                if text is None:
                    logfunc(f'{label}: could not read {context.get_relative_path(path)}')
                    counts['unreadable'] += 1
                    continue
                counts['files'] += 1
                rows.extend((entry, path) for entry in _entries(text, counts))
            read.append((folder, rows))
        wanted = Counter()
        for _folder, rows in read:
            wanted |= Counter(_key(entry) for entry, _path in rows)
        done = Counter()
        # The view with more entries first; of views with as many, the one with the shortest folder,
        # which is the extraction's root view when it has one.
        for _folder, rows in sorted(read, key=lambda view: (-len(view[1]), len(view[0]), view[0])):
            for entry, path in rows:
                key = _key(entry)
                if done[key] < wanted[key]:
                    done[key] += 1
                    records.append((entry, path))
                    if path not in sources:
                        sources.append(path)
                else:
                    counts['repeated'] += 1
    return records, sources, counts


def _log_counts(label, counts, shown, other):
    logfunc(f"{label}: {counts['files']} file(s) read ({counts['unreadable']} could not be read), "
            f"{counts['lines']} lines: {counts['blank']} blank, {counts['joined']} joined to the entry "
            f"above, {counts['doubled']} holding two times, {counts['untimed']} with no time, "
            f"{counts['unmatched']} of no known line form (reported with only a message)")
    if counts['repeated']:
        logfunc(f"{label}: {counts['repeated']} entries held by more than one volume view of one log "
                f"folder reported once")
    logfunc(f'{label}: {shown} rows here, {other} entries in the other Wi-Fi log artifact')


def _message(entry):
    return '\n'.join([entry['message']] + entry['more'])


@artifact_processor
def macosWifiLogEvents(context):
    data_headers = ('Time (as written)', 'Event (as written)', 'Interface', 'SSID', 'BSSID',
                    'Network ID (as stored)', 'Detail', 'Message', 'Process', 'PID', 'Category (as written)',
                    'File and Line (as written)', '@[ ] Value (as stored)', 'Source File', 'Line')
    records, sources, counts = _records(context, 'Wi-Fi Log Events')
    data_list = []
    for entry, path in records:
        event = _event(entry)
        if event is not None:
            data_list.append((entry['time'],) + event + (
                _message(entry), entry['process'], entry['pid'], entry['category'], entry['location'],
                entry['at'], context.get_relative_path(path), entry['line']))
    _log_counts('Wi-Fi Log Events', counts, len(data_list), len(records) - len(data_list))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosWifiLogEntries(context):
    data_headers = ('Time (as written)', 'Process', 'PID', 'Category (as written)',
                    'File and Line (as written)', '@[ ] Value (as stored)', 'Host', 'Message',
                    'Source File', 'Line')
    records, sources, counts = _records(context, 'Wi-Fi Log Other Entries')
    data_list = []
    for entry, path in records:
        if _event(entry) is None:
            data_list.append((entry['time'], entry['process'], entry['pid'], entry['category'],
                              entry['location'], entry['at'], entry['host'], _message(entry),
                              context.get_relative_path(path), entry['line']))
    _log_counts('Wi-Fi Log Other Entries', counts, len(data_list), len(records) - len(data_list))
    return data_headers, data_list, '\n'.join(sources)
