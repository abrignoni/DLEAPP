"""Power source history the UPower daemon keeps under /var/lib/upower, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxUpowerHistory": {
        "name": "UPower Power Source History",
        "description": "Readings the UPower daemon recorded for a battery or other power source (charge, rate, "
                       "voltage, time to full and time to empty), each with the time the daemon took it and the "
                       "charging state of the source.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "System (Linux)",
        "notes": "Reads the history files the UPower daemon keeps in its history folder, /var/lib/upower unless the "
                 "build names another (Reference: UPower v1.91.1, commit 57f59b584e066dddafaa11cb8137b32e6e3d15c7, "
                 "'meson.build' lines 108 to 111, https://gitlab.freedesktop.org/upower/upower); a folder set with "
                 "the UPOWER_HISTORY_DIR environment variable is not read ('src/up-history.c' lines 960 to 963). The "
                 "daemon keeps five files for a power source, history-<kind>-<id>.dat with the kinds rate, charge, "
                 "time-full, time-empty and voltage ('src/up-history.c' lines 403 and 681 to 709); a file with "
                 "another name is counted in the run log and not read. Each line is a time, a value and a state "
                 "separated by tabs ('libupower-glib/up-history-item.c' lines 184 to 191). Timestamp (UTC) is the "
                 "time, seconds since 1970 by the system clock when the daemon took the reading (lines 117 to 126). "
                 "Reading is the kind from the file name. Value is the number as stored, three decimals, and Unit is "
                 "the unit the daemon's D-Bus documentation gives: W for rate, % for charge and V for voltage "
                 "('dbus/org.freedesktop.UPower.Device.xml' line 189), seconds for time to full and time to empty "
                 "(lines 591 to 610). State is the state name as stored; the daemon writes charging, discharging, "
                 "empty, fully-charged, pending-charge, pending-discharge or unknown ('libupower-glib/up-types.c' "
                 "lines 193 to 212). Device ID is the part of the file name after the kind. For a battery the daemon "
                 "builds it from the model, the design capacity as a whole number and the serial number, leaving out "
                 "a model or serial of two characters or fewer; for another source from vendor, model and serial; "
                 "with none of these it is generic_id, and a space, dot, comma, slash, backslash, tab, quote or "
                 "question mark becomes an underscore ('src/up-device.c' lines 304 to 385). A line power source gets "
                 "no id and so no files (lines 320 to 321). Line is the line of the file a row is on, and the "
                 "report's located-at line names the files that held a row. The daemon records a reading only when "
                 "it differs from the last one it recorded for that kind and the state is not unknown "
                 "('src/up-history.c' lines 765 to 918), so the gap between two rows is not a sampling interval. "
                 "When the daemon loads a source's history it adds to each of the five kinds an entry with the time "
                 "of loading, value 0 and state unknown (lines 681 to 720); it creates no other entry in that state, "
                 "and holds as unknown a loaded line whose state it does not recognise ('libupower-glib/up-types.c' "
                 "lines 224 to 241). On ubuntu2604_arm64_upower the 25 rows with State unknown all have Value 0, and "
                 "their three distinct times are, to the second, the last three of the 14 times the VM's journal "
                 "records the upower service starting. The daemon writes the files within 10 minutes of recording a "
                 "reading, 5 seconds while a discharging source is at 10% or below, and when it stops (lines 36 to "
                 "38, 612 to 672 and 971 to 982). Each write leaves out entries more than 7 days older than the time "
                 "of writing (lines 39, 446 to 453 and 958), and this version has no setting for the 7 days; so a "
                 "file holds at most the 7 days before its last write, and the last readings before a power loss can "
                 "be missing. The daemon formats the value under the system locale ('src/up-main.c' line 206): a "
                 "value written with a dot is reported as a number and any other as stored, which was tested with "
                 "constructed input only. A line that is not three tab-separated fields with a whole number first is "
                 "counted in the run log and not reported, a time outside what a date can hold is left blank and "
                 "counted, and a file that cannot be read is counted. The artifact's reading was compared with the "
                 "daemon's own on the lab VM: GetHistory over D-Bus returned 36 charge, 430 rate, 119 time-empty, "
                 "297 time-full and 438 voltage entries for the battery, and the 12, 279, 62, 155 and 283 rows read "
                 "from the battery's files are, in time, value and state, exactly the last entries of each; every "
                 "entry before them is more than 7 days older than the file's modified time. On "
                 "ubuntu2604_arm64_upower, captured from a VM running UPower 1.91.1 whose clock was 355,629 seconds "
                 "behind real time, the 806 rows are 15 charge, 282 rate, 65 time to empty, 158 time to full and 286 "
                 "voltage, for the two ids bq40z651-100 (791 rows) and generic_id (15 rows, all State unknown); the "
                 "states are charging 630, fully-charged 122, discharging 29 and unknown 25. What the files do not "
                 "record: which user was logged in, and why a source changed state.",
        "paths": ("*/var/lib/upower/history-*.dat",),
        "output_types": "standard",
        "artifact_icon": "battery-charging",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64, UPower 1.91.1 | 806 rows",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
# the five kinds the daemon writes, with the unit its documentation gives for each
KINDS = (('time-full', 'Time to full', 's'), ('time-empty', 'Time to empty', 's'), ('charge', 'Charge', '%'),
         ('rate', 'Rate', 'W'), ('voltage', 'Voltage', 'V'))
WHOLE = re.compile(r'[+-]?[0-9]+\Z')
DECIMAL = re.compile(r'[+-]?[0-9]+(\.[0-9]+)?\Z')


def file_kind(name):
    """(reading, unit, device id) for the name of a history file, history-<kind>-<id>.dat; None for another name."""
    if not (name.startswith('history-') and name.endswith('.dat')):
        return None
    middle = name[len('history-'):-len('.dat')]
    for kind, label, unit in KINDS:
        if middle.startswith(kind + '-') and len(middle) > len(kind) + 1:
            return label, unit, middle[len(kind) + 1:]
    return None


def utc(seconds):
    """The UTC time of a count of seconds since 1970, or '' when it is outside what a datetime can hold."""
    try:
        return EPOCH + timedelta(seconds=seconds)
    except OverflowError:
        return ''


def history_rows(data, counts):
    """The rows for the bytes of a history file, in file order: (time, value, state, line number). A line is three
    fields separated by tabs: seconds since 1970, the value and the state."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        if not raw:
            continue
        parts = raw.decode('utf-8', errors='backslashreplace').split('\t')
        if len(parts) != 3 or not WHOLE.match(parts[0]):
            counts['lines that are not a time, a value and a state, not reported'] += 1
            continue
        when = utc(int(parts[0]))
        if when == '':
            counts['times outside the range of a date, left blank'] += 1
        value = float(parts[1]) if DECIMAL.match(parts[1]) else parts[1]
        rows.append((when, value, parts[2], number))
    return rows


@artifact_processor
def linuxUpowerHistory(context):
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Reading', 'Value', 'Unit', 'State', 'Device ID', 'Line')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        kind = file_kind(os.path.basename(path))
        if kind is None:
            problems['files not named for one of the five readings, not read'] += 1
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = history_rows(data, problems)
        label, unit, device = kind
        data_list.extend((when, label, value, unit, state, device, number) for when, value, state, number in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('UPower Power Source History: '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
