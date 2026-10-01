"""Transitions in the screen time history GNOME Shell keeps (session-active-history.json), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxGnomeScreenTimeHistory": {
        "name": "Screen Time History (GNOME Shell)",
        "description": "Entries in the screen time history GNOME Shell keeps for each user "
                       "(session-active-history.json), each a change between the Active and Inactive states with "
                       "its time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the screen time history GNOME Shell keeps for a user, session-active-history.json in the "
                 "gnome-shell folder of the user's data folder (Reference: GNOME Shell 50.1, "
                 "'js/misc/timeLimitsManager.js', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L145-L146; "
                 "'src/shell-global.c', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-global.c#L384), "
                 "one row per entry, in file order. The file is written from GNOME Shell 48.0 on "
                 "(https://github.com/GNOME/gnome-shell/blob/a2ffd14a35d3e926dcc86c06ea6d04c57ed5c1a3/js/misc/timeLimitsManager.js); "
                 "GNOME Shell 47.0's source does not name the file. GNOME Shell keeps it while the screen time "
                 "history setting (history-enabled in org.gnome.desktop.screen-time-limits, on by default in "
                 "gsettings-desktop-schemas 50.0, "
                 "https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/0b3ea8e1a25ecfc33e9f6af1b1db93c4032b84e6/schemas/org.gnome.desktop.screen-time-limits.gschema.xml.in#L8-13) "
                 "is on or parental controls session limits are set "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L305-L308), "
                 "and deletes it when it stops keeping it "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L449-L455, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L783-L793), "
                 "so a missing file is not evidence that no history was ever kept. Each entry is a change between "
                 "two states, Inactive (0) and Active (1) "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L73-L76), "
                 "with wallTimeSecs, the time of the change in whole seconds since 1970 by the system clock "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L150-L152, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L516-L518, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L611-L620). "
                 "GNOME Shell counts the user Active when logind reports the user's state as active, the user's "
                 "IdleHint is false and the system is not preparing to sleep, and Inactive otherwise "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L99-L110, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L559-L564). "
                 "Time is wallTimeSecs in UTC; Old State and New State are the entry's two states, a value other "
                 "than 0 or 1 shown as Unknown with the value and a missing one left blank; Seconds Until Next Entry "
                 "is the next entry's time minus this one's, blank on the last entry. When it starts, GNOME Shell "
                 "adds an entry to Active at the current time if the history it loaded is empty or ends Inactive "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L350-L355); "
                 "when it stops while Active it adds an entry to Inactive "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L437-L442); "
                 "and it adds an entry when it sees the state change, including when the system prepares to sleep "
                 "and when it wakes "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L566-L582, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L480-L504). "
                 "It writes the file, replacing it whole, when it stores such a change and when it stops "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L575-L577, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L444-L445, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L777-L779), "
                 "so an entry it has not stored is not in the file. Before writing it drops entries more than 14 "
                 "weeks before the current time, except the last, and any entry later than the current time "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L43, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L708-L712, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L720-L722), "
                 "and drops an entry when the next one has the same time and returns to the entry's old state "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L724-L737). "
                 "When the system clock jumps relative to the monotonic clock while GNOME Shell runs, other than "
                 "across a sleep, it adds the jump to every stored time and writes the file "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L357-L385, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L544-L557), "
                 "so earlier entries move with a clock correction; a change made while it is not running is not "
                 "applied "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L533-L537). "
                 "These were read in the source and not exercised. GNOME Shell stops loading a file at the first "
                 "entry that is not an object with the three members, holds a state other than 0 or 1 or the same "
                 "state twice, or holds a time that is not a whole number up to 2^53 - 1 or is earlier than the last "
                 "entry it kept, keeping the entries before it, so its next write leaves out that entry and every "
                 "later one "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L343-L355, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/js/misc/timeLimitsManager.js#L645-L672); "
                 "these were also read in the source and not exercised. A file in which an entry fails these checks, "
                 "with each time compared to the one before it, is counted in the run log and its entries are "
                 "reported as stored. Source File is the file a row comes from; an entry that is not a JSON object, "
                 "and a file that is not a JSON array, are counted in the run log and not reported, and a time that "
                 "is not a whole number of seconds is left blank and counted there. On ubuntu2604_arm64_screentime, "
                 "captured from a VM running GNOME Shell 50.1-0ubuntu1.2, whose deployed timeLimitsManager.js is "
                 "byte for byte the 50.1 source, the 56 rows are the file's 56 entries, 28 to Active and 28 to "
                 "Inactive in turn, from 16 to 30 September 2026 by the VM's clock, which was about 5,158 s ahead of "
                 "real time. They were written by the VM's own use, not by known steps, and were checked against the "
                 "VM's system journal. The file's birth and modification times were both the last entry's time. The "
                 "last entry, to Inactive, has the same second as a restart of systemd-logind in the journal, and no "
                 "entry followed in the 5 hours 25 minutes before the capture and logind reported the user active "
                 "when read after the capture; why no later entry was written was not established. An entry is not "
                 "written at every login or unlock: the user's GNOME Shell started at 12:24:54 UTC on 26 September "
                 "by the journal, and the file has no entry between 21:47:04 the evening before and 14:15:12 that "
                 "day; on 25 September the journal holds three GDM password authentications that unlocked the user's "
                 "keyring with no new session opened, while the file has no entry between 04:31:16 and 21:42:04. The "
                 "file holds no entry before 16 September although the journal records the user's GNOME Shell "
                 "starting on 31 August and on 7 and 11 September, all within 14 weeks of the capture; why the "
                 "earlier history is absent was not established. After the capture, setting the graphical session's "
                 "idle hint through logind and clearing it 60 s later added no entry; the user's IdleHint, which "
                 "GNOME Shell reads, did not change. No member of the other five tested images matches the declared "
                 "paths.",
        "paths": ("*/.local/share/gnome-shell/session-active-history.json",),
        "output_types": "standard",
        "artifact_icon": "clock",
        "sample_data": {
            "ubuntu2604_arm64_screentime": "Ubuntu 26.04 LTS aarch64, GNOME Shell 50.1 | 56 rows",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json
import math
import os
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

STATES = {0: 'Inactive', 1: 'Active'}
_SAFE = 2 ** 53 - 1


def _reject_constant(name):
    raise ValueError(f'{name} is not JSON')


def safe_integer(value):
    """The value as an int when it is a whole number JavaScript would call a safe integer, else None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        return None
    value = int(value)
    return value if abs(value) <= _SAFE else None


def state_label(value):
    """Inactive or Active for the two values of GNOME Shell's UserState, Unknown with the value for any other."""
    number = safe_integer(value)
    if number in STATES:
        return STATES[number]
    return f'Unknown ({json.dumps(value)})'


def first_rejected(history):
    """The index of the first entry that fails the checks GNOME Shell 50.1's loader applies, each time compared with
    the one before it, or None."""
    previous = 0
    for index, entry in enumerate(history):
        if not isinstance(entry, dict) or not {'oldState', 'newState', 'wallTimeSecs'} <= entry.keys():
            return index
        old, new = safe_integer(entry['oldState']), safe_integer(entry['newState'])
        when = safe_integer(entry['wallTimeSecs'])
        if old not in STATES or new not in STATES:
            return index
        if old == new or when is None or when < previous:
            return index
        previous = when
    return None


def history_rows(data, counts):
    """Rows (time, old state, new state, seconds until the next entry) for the bytes of a history file, one per entry
    that is a JSON object, in file order. None when the file is not a JSON array."""
    try:
        history = json.loads(data.decode('utf-8'), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(history, list):
        return None
    rejected = first_rejected(history)
    if rejected is not None:
        counts['files with an entry that fails the checks GNOME Shell 50.1 applies when loading, reported as stored'] += 1
    entries = [entry for entry in history if isinstance(entry, dict)]
    if len(entries) < len(history):
        counts['entries that are not JSON objects, not reported'] += len(history) - len(entries)
    times = [safe_integer(entry.get('wallTimeSecs')) for entry in entries]
    rows = []
    for index, entry in enumerate(entries):
        when = times[index]
        moment = None
        if when is not None:
            try:
                moment = datetime.fromtimestamp(when, timezone.utc)
            except (OverflowError, OSError, ValueError):
                moment = None
        if moment is None:
            counts['times that are not a whole number of seconds in range, left blank'] += 1
        following = times[index + 1] if index + 1 < len(entries) else None
        gap = following - when if when is not None and following is not None else ''
        old = state_label(entry['oldState']) if 'oldState' in entry else ''
        new = state_label(entry['newState']) if 'newState' in entry else ''
        rows.append((moment or '', old, new, gap))
    return rows


@artifact_processor
def linuxGnomeScreenTimeHistory(context):
    data_headers = (('Time', 'datetime'), 'Old State', 'New State', 'Seconds Until Next Entry', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = history_rows(data, problems)
        if rows is None:
            problems['files that are not a JSON array, not reported'] += 1
            continue
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Screen Time History (GNOME Shell): '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
