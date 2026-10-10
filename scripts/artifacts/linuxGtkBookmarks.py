"""Folder bookmarks GNOME Files and the GTK file chooser keep (gtk-3.0/bookmarks), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxGtkBookmarks": {
        "name": "File Manager Bookmarks (GTK)",
        "description": "Folders a user bookmarked in GNOME Files or a GTK file chooser, from the bookmarks file in "
                       "the user's configuration folder: the location as a URI and the label shown in the sidebar.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the bookmarks file GTK applications share, gtk-3.0/bookmarks in the user's configuration "
                 "folder. GNOME Files reads and writes it (Reference: Nautilus 50.2.2, commit "
                 "c6592e9c7fce37ad685d0ba24720893955b7835d, 'src/nautilus-bookmark-list.c' lines 75 to 85, "
                 "https://gitlab.gnome.org/GNOME/nautilus), and so do the GTK 3 and GTK 4 file choosers (GTK "
                 "3.24.52, commit 6a0b360d473f7c546314738c0c8dd9829eb9d3c2, 'gtk/gtkbookmarksmanager.c' lines 71 to "
                 "81, and GTK 4.22.4, commit 7f99ab1a26408b6499a18f353f081e3c0598ea5c, lines 73 to 87, "
                 "https://gitlab.gnome.org/GNOME/gtk). The older .gtk-bookmarks in the home folder is read too: GTK "
                 "3 falls back to it when the first file gives no bookmark (lines 228 to 240) and GTK 4 when the "
                 "first file does not exist (lines 275 to 287), each then writing what it read to the first. A "
                 "configuration folder placed elsewhere with XDG_CONFIG_HOME is not read. Each line is a URI, "
                 "optionally followed by a space and a label (Nautilus lines 442 to 466; GTK 3 lines 95 to 113). URI "
                 "is the text before the first space, as stored, and Label is the rest of the line. Nautilus writes "
                 "a label on every line, the bookmark's name (lines 592 to 613); GTK writes one only when the "
                 "bookmark has one (GTK 3 lines 148 to 149), and a line without one is a bookmark the application "
                 "names itself. Local Path is derived: for a URI that starts with file:/// it is the path with "
                 "percent escapes decoded, and it is empty for any other URI. Rows are in file order, the order the "
                 "applications keep the bookmarks in, and Line is the line of the file. The file holds no times. A "
                 "line that starts with white space is not reported and is counted in the run log; Nautilus skips "
                 "such a line (line 448). Bytes that are not UTF-8 are shown as backslash escapes, and GTK skips a "
                 "line that holds any (GTK 3 line 104); that was tested with constructed input only. A file that "
                 "cannot be read is counted in the run log. On ubuntu2604_arm64_gtkbookmarks, from a VM running "
                 "Nautilus 50.2.2, the 10 rows are the five lines the file held before the test (Documents, Music, "
                 "Pictures, Videos and Downloads in the home folder, each with a label) and five of the six lines "
                 "appended for the test: a folder without a label, a folder with a percent escape and a three-word "
                 "label, a folder with a label, an sftp URI with a label, and a second line for the first folder; "
                 "the sixth, which starts with a space, is the one counted. With Nautilus running, moving the first "
                 "test folder with mv, trashing the second with gio trash and removing the third with rmdir left the "
                 "file byte for byte as it was 6 seconds after each step and at the capture, 34 seconds after the "
                 "lines were added, so a row can name a folder that no longer exists. "
                 "ubuntu2604_arm64_gtkbookmarks_gui continues that test in the Files window of the same running "
                 "Nautilus. Add to Bookmarks on a folder made Nautilus rewrite the file: the new bookmark became the "
                 "last line with the folder's name as its label, the line without a label got its folder's name as "
                 "one, the line starting with a space and the second line for the first folder were gone, and the "
                 "three lines whose folders no longer existed stayed. A second folder bookmarked the same way was "
                 "then moved with mv: 8 seconds later its line held the new path as the URI and still the old name "
                 "as the label, and the file's modified time was the second of the move, so for a bookmark Nautilus "
                 "followed a Label can differ from the folder's present name. Remove from Bookmarks took that "
                 "folder's line out. The capture's 10 rows are the 9 lines left from the first capture and the moved "
                 "folder's line. On ubuntu2604_arm64_gtkbookmarks_chooser a bookmark was dragged to a new place in "
                 "the sidebar of a GTK 3.24.52 file chooser, twice: each time GTK rewrote the file with the lines in "
                 "the new order and every URI and label unchanged, so the 10 rows are those of the capture before in "
                 "another order. Not exercised: renaming a bookmark, and adding or removing one in a GTK file "
                 "chooser. The file does not record when a bookmark was made or which application made it.",
        "paths": ("*/.config/gtk-3.0/bookmarks", "*/.gtk-bookmarks"),
        "output_types": "standard",
        "artifact_icon": "bookmark",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks": "Ubuntu 26.04 LTS aarch64, Nautilus 50.2.2 | 10 rows",
            "ubuntu2604_arm64_gtkbookmarks_chooser": "Ubuntu 26.04 LTS aarch64, GTK 3.24.52 | 10 rows",
            "ubuntu2604_arm64_gtkbookmarks_gui": "Ubuntu 26.04 LTS aarch64, Nautilus 50.2.2 | 10 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter
from urllib.parse import unquote_to_bytes

from scripts.ilapfuncs import artifact_processor, logfunc

WHITESPACE = ' \t\n\v\f\r'


def local_path(uri):
    """The path a file: URI with no host names, its percent escapes decoded; '' for any other URI."""
    if not uri.startswith('file:///'):
        return ''
    return unquote_to_bytes(uri[len('file://'):]).decode('utf-8', errors='backslashreplace')


def bookmark_rows(data, counts):
    """The rows for the bytes of a bookmarks file, in file order: (uri, label, local path, line number). A line is
    a URI, then optionally a space and a label."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        if not raw:
            continue
        line = raw.decode('utf-8', errors='backslashreplace')
        if line[0] in WHITESPACE:
            counts['lines that start with white space, not reported'] += 1
            continue
        uri, _, label = line.partition(' ')
        rows.append((uri, label, local_path(uri), number))
    return rows


@artifact_processor
def linuxGtkBookmarks(context):
    data_headers = ('URI', 'Label', 'Local Path', 'Line', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = bookmark_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('File Manager Bookmarks (GTK): '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
