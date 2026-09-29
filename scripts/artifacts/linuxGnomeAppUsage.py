"""Applications in the usage list GNOME Shell keeps (application_state), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxGnomeAppUsage": {
        "name": "Application Usage (GNOME Shell)",
        "description": "Applications in the usage list GNOME Shell keeps for each user (application_state), each "
                       "with the score GNOME Shell raises for the time the application's windows had the focus and "
                       "the application's Last Seen time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the usage list GNOME Shell keeps for each user, the application_state file in the "
                 "gnome-shell folder of the user's data folder (Reference: GNOME Shell 50.1, "
                 "'src/shell-app-usage.c', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L48 "
                 "and "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L309-L314; "
                 "'src/shell-global.c', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-global.c#L384), "
                 "which is .local/share in the home folder when $XDG_DATA_HOME is not set or is empty (Base "
                 "Directory specification, "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L136-139). "
                 "A list kept in another data folder is not read. GNOME Shell 3.32.0 and later write one context "
                 "element with an empty id, holding an application element with id, score and last-seen attributes "
                 "for each application in its list (3.32.0, "
                 "https://github.com/GNOME/gnome-shell/blob/47915f8c1117470e5351a8ec4e4bdac5e683498d/src/shell-app-usage.c#L561-L590; "
                 "50.1, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L559-L588). "
                 "GNOME Shell 3.0.0 to 3.30.2 wrote an open-window-count attribute as well, the number of the "
                 "application's windows open when the file was written (3.0.0, "
                 "https://github.com/GNOME/gnome-shell/blob/d6c3868a7c66020d1fcd8f74416ee5b2763ddee5/src/shell-app-usage.c#L678-L689; "
                 "3.30.2, "
                 "https://github.com/GNOME/gnome-shell/blob/2a36bf52cb61ac1a015bc2150807a8d47c7155e4/src/shell-app-usage.c#L730-L741), "
                 "which a change first tagged in 3.31.4 removed "
                 "(https://github.com/GNOME/gnome-shell/commit/c3ec813f6f58bb42f07d34af3e48f2f8f5d824f9). It gives "
                 "one row per application element with an id, wherever it sits in the file, each file's rows "
                 "ordered by Last Seen, most recent first, then by Application ID, with the rows without a time "
                 "last; GNOME Shell writes the elements in the order of its hash table "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L564-L566), "
                 "not by time or score. Source File is the file a row comes from, and the report's located-at line "
                 "names the files that held a row; an application element without an id, a file that is not XML "
                 "with an application-state root element and a file that cannot be read are counted in the run log "
                 "and not reported, and any other element is passed over and counted there. Application ID is the "
                 "ID GNOME Shell gives the application, the ID of its desktop file ('src/shell-app.c', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app.c#L171-L176), "
                 "as stored; GNOME Shell escapes it for XML when it writes it "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L464-L473, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L577), "
                 "and it is shown here unescaped. Score is as stored. When an application's windows lose the "
                 "focus, GNOME Shell adds to its score the whole seconds of the system clock between their gaining "
                 "and losing it, divided by 7 with the remainder dropped, so a hold of less than 6 s adds nothing "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L43, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L165-L187, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L217-L230); "
                 "when a score passes 25714, 50 hours of focus in those units, it halves every score "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L53-L66, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L153-L163, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L183-L184), "
                 "which can leave a fraction. A score is therefore a count of 7-second units of focus only until "
                 "the first halving, and a relative weight after it. When the session reports that it has gone "
                 "idle, GNOME Shell adds 4 units, 30 s, for the application that has the focus and sets its Last "
                 "Seen to 30 s after the start of its current hold "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L50, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L232-L262); "
                 "the tested session did not go idle (its idle-delay is 0, and after 34 minutes without input its "
                 "presence status was still available), so this was not exercised. Last Seen (UTC) is the "
                 "last-seen attribute, seconds since 1970 by the system clock "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L121-L125), "
                 "which GNOME Shell sets when the application's windows lose the focus "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L176) "
                 "and when the application starts running "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L211-L214). "
                 "Apart from the idle case, it is not changed while the application keeps the focus, so for an "
                 "application that had the focus when the file was written it is from before that hold. An entry "
                 "GNOME Shell creates when it sees an application's state change starts with a score and a "
                 "last-seen of 0 "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L146-L147, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L209), "
                 "and a last-seen of 0 is left blank, as is one that is not a whole number of seconds, which is "
                 "counted in the run log; on the tested VM, a desktop file whose program exits without opening a "
                 "window, launched with gtk-launch, made no entry. GNOME Shell writes the file, replacing it "
                 "whole, 300 s after a score increase finds no write pending, and writes the list as it stands "
                 "then "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L62, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L185, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L426-L434, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L531-L547); "
                 "a change after that write reaches the file only at a later write, and GNOME Shell 50.1 does not "
                 "write the list when it stops "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L324-L340), "
                 "which was read in the source and not exercised. The file holds the list as it stood when last "
                 "written, which is its modification time. Only applications whose desktop file GNOME Shell finds "
                 "when it writes are written "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L570-L573; "
                 "'src/shell-app-system.c', "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-system.c#L341-L358); "
                 "a window whose application has no desktop file is counted under an ID of its own, window:N, that "
                 "is never written "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app.c#L171-L176, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app.c#L884). "
                 "When it starts, GNOME Shell drops each application whose score is under 3214 and whose Last Seen "
                 "is more than 7 days old "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L70, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L436-L461, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L713), "
                 "again read in the source and not exercised. An application missing from the list can therefore "
                 "have been used. GNOME's remember-app-usage setting (org.gnome.desktop.privacy) being off is not "
                 "evidence that nothing was recorded: in GNOME Shell 50.1 turning it off clears the application "
                 "being watched and any pending write "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L722-L749), "
                 "but the focus handler, connected when GNOME Shell starts, does not check it "
                 "(https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L289, "
                 "https://github.com/GNOME/gnome-shell/blob/e0fdc4c13250e9a9b8ea9594c83925274f4a5dca/src/shell-app-usage.c#L217-L230), "
                 "so the next changes of focus are counted again. This was read in the source and not exercised. "
                 "On ubuntu2604_arm64_appstate, captured from a VM running GNOME Shell 50.1-0ubuntu1.2, whose "
                 "Ubuntu patches leave src/shell-app-usage.c unchanged, the 7 rows are the file's 7 application "
                 "elements: the 3 known applications and 4 earlier entries, one of them with a fraction in its "
                 "score. The known steps moved the focus between Disk Usage Analyzer, Calculator, Characters and a "
                 "test application while an AT-SPI listener logged the activation and deactivation of their "
                 "windows, and every Score and Last Seen of the known applications, in the captured file and in "
                 "the three other writes GNOME Shell made during the steps, followed from the logged holds: "
                 "Calculator's 35 is 21 for a hold of 148 s and 1, 1, 0, 8, 3 and 1 for holds of 9, 12, 2, 59, 24 "
                 "and 11 s, and its Last Seen is the second another window last took the focus from it; a 3 s hold "
                 "of Characters added nothing and moved its Last Seen; and the test application, which took the "
                 "focus when it started and kept it, was written with a score of 0 and a Last Seen after its "
                 "launch and before it took the focus. The three writes whose score increase was logged came 300.1 "
                 "to 300.6 s after it, and 35.5 s after the increase that queued the next write the file was "
                 "still, byte for byte, the earlier write. The test application, used before its desktop file was "
                 "deleted, was left out of the next write, and a window started with no desktop file got no entry. "
                 "Open Windows is blank on every row, since GNOME Shell 50.1 does not write it; it was tested with "
                 "constructed input only. No member of the other nineteen tested images matches the declared paths.",
        "paths": ("*/.local/share/gnome-shell/application_state",),
        "output_types": "standard",
        "artifact_icon": "activity",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 7 rows",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_WHOLE = re.compile(r'\d+')
_KNOWN = {'application-state', 'context', 'application'}


def last_seen_time(value):
    """The UTC time for a last-seen attribute, seconds since 1970 as GNOME Shell writes it. None for 0, which GNOME
    Shell writes when it has recorded no time, and for anything that is not a whole number of seconds."""
    if not _WHOLE.fullmatch(value or '') or int(value) == 0:
        return None
    try:
        return datetime.fromtimestamp(int(value), timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def usage_rows(data, counts):
    """Rows (last seen, application ID, score, open windows) for the text of an application_state file: one per
    application element in the file, in file order. None when the text is not XML with an application-state root
    element."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None
    if root.tag != 'application-state':
        return None
    other = sum(1 for element in root.iter() if element.tag not in _KNOWN)
    if other:
        counts['elements other than context and application, passed over'] += other
    rows = []
    for application in root.iter('application'):
        app_id = application.get('id')
        if not app_id:
            counts['application elements without an id, not reported'] += 1
            continue
        stored = application.get('last-seen')
        when = last_seen_time(stored)
        if stored is not None and when is None and not (_WHOLE.fullmatch(stored) and int(stored) == 0):
            counts['last-seen values that are not a whole number of seconds, left blank'] += 1
        rows.append((when or '', app_id, application.get('score', ''), application.get('open-window-count', '')))
    return rows


def row_order(row):
    """Most recent Last Seen first, then Application ID; rows without a time last."""
    when = row[0]
    return (when == '', -when.timestamp() if when else 0, row[1])


@artifact_processor
def linuxGnomeAppUsage(context):
    data_headers = (('Last Seen (UTC)', 'datetime'), 'Application ID', 'Score', 'Open Windows', 'Source File')
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
        rows = usage_rows(data, problems)
        if rows is None:
            problems['files that are not XML with an application-state root element, not reported'] += 1
            continue
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in sorted(rows, key=row_order))
        if rows:
            read.append(path)
    if problems:
        logfunc('Application Usage (GNOME Shell): '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
