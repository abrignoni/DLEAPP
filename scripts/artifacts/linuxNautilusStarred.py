"""Files and folders in the starred-files store of Nautilus (GNOME Files), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxNautilusStarredFiles": {
        "name": "Starred Files (GNOME Files)",
        "description": "Files and folders in the store GNOME Files (Nautilus) keeps for starred items, each with the "
                       "time it was first added to the store and whether it is still starred.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the store GNOME Files (Nautilus) keeps for starred files, a tinysparql database in "
                 ".local/share/nautilus/tags (Reference: Nautilus 50.2.2, 'src/nautilus-tag-manager.c', "
                 "https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-tag-manager.c#L672-676), "
                 "one row per file URI in its Resource table, oldest First Added first. Nautilus stars a file by "
                 "inserting its URI as a nautilus:File with nautilus:starred true and unstars it by deleting that "
                 "statement "
                 "(https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/data/ontology/nautilus.ontology#L11-20, "
                 "https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-tag-manager.c#L365-391, "
                 "https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-tag-manager.c#L337-363), "
                 "and it lets a file be starred only inside the user's home folder "
                 "(https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-tag-manager.c#L754-772). "
                 "Starred is Yes when the URI has that statement and No when the URI is in the store without it. "
                 "Path is the URI's path, percent-decoded. First Added is nrl:added, which tinysparql sets, in Unix "
                 "seconds, to the time at which the transaction that first created the URI's resource began "
                 "(tinysparql 3.11.0, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L1858-1871, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L2943). "
                 "Change Sequence is nrl:modified, a transaction counter tinysparql writes when a transaction "
                 "changes the resource, not a time "
                 "(https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L1840-1856, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L556-583, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L3017-3019): "
                 "a higher value is a later change within this store. When Nautilus sees a starred file, or a folder "
                 "above one, renamed or moved, it deletes the statement for the old URI and inserts one for the new "
                 "(https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-tag-manager.c#L802-887, "
                 "https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-file.c#L1725-1728, "
                 "https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-file-changes-queue.c#L283-287); "
                 "its handling of a removed file does not change the store "
                 "(https://gitlab.gnome.org/GNOME/nautilus/-/blob/c6592e9c7fce37ad685d0ba24720893955b7835d/src/nautilus-file-changes-queue.c#L277-281). "
                 "An added time not stored as whole seconds is left blank and counted in the run log, and a store "
                 "without Nautilus's tables is counted there and not reported. On ubuntu2604_arm64_nautilusstars, "
                 "captured from a VM running Nautilus 50.2.2 with tinysparql 3.11.0 after known steps, with the "
                 "store copied after each step, the 4 rows are the 4 file URIs in the store; the VM's clock was "
                 "about 5,158 s ahead of real time, and the times below are by that clock. Two files and a folder "
                 "were starred with clicks on the star column of the list view, and each First Added, 15:25:37, "
                 "15:25:45 and 15:25:50 UTC on 1 October 2026, is within 3 s before the time logged just after its "
                 "click. Unstarring star-bravo.txt removed its statement and left its URI and First Added in the "
                 "store, and starring it again kept that First Added and raised its Change Sequence from 3 to 7, so "
                 "First Added is the first time a path was starred, not the latest. Renaming star-alpha.txt with mv, "
                 "outside Nautilus, moved the star to the new name, whose First Added, 15:26:18, is the second of "
                 "the rename and not of the first star, and left the old name in the store with Starred No. Deleting "
                 "star-bravo.txt with rm left it in the store with Starred Yes: a row does not show that its file "
                 "still exists, and a No row is a path that was starred earlier. No member of the other four tested "
                 "images matches the declared paths.",
        "paths": ("*/.local/share/nautilus/tags/meta.db*",),
        "output_types": "standard",
        "artifact_icon": "star",
        "sample_data": {
            "ubuntu2604_arm64_nautilusstars": "Ubuntu 26.04 LTS aarch64, Nautilus 50.2.2 | 4 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

QUERY = '''
SELECT r.Uri, x."nrl:added", x."nrl:modified", f."nautilus:starred"
FROM Resource r
JOIN "rdfs:Resource" x ON x.ID = r.ID
LEFT JOIN "nautilus:File" f ON f.ID = r.ID
WHERE r.Uri LIKE 'file:%'
ORDER BY x."nrl:added", r.ID
'''
NEEDED = {'Resource', 'rdfs:Resource', 'nautilus:File'}


def uri_path(uri):
    """The path a file URI names, percent-decoded; the URI itself when it has no path."""
    path = unquote(urlsplit(uri).path)
    return path or uri


def added_time(value):
    """The UTC time for nrl:added stored as whole Unix seconds; None for anything else."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def starred_rows(db, counts):
    """Rows (first added, path, starred, change sequence) for each file URI in a starred-files store, oldest first.
    None when the store lacks the tables Nautilus's ontology gives it."""
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not NEEDED <= tables:
        return None
    rows = []
    for uri, added, modified, starred in db.execute(QUERY):
        when = added_time(added)
        if when is None:
            counts['added times not stored as whole seconds, left blank'] += 1
        rows.append((when or '', uri_path(uri), 'Yes' if starred == 1 else 'No',
                     modified if modified is not None else ''))
    return rows


@artifact_processor
def linuxNautilusStarredFiles(context):
    data_headers = (('First Added', 'datetime'), 'Path', 'Starred', 'Change Sequence')
    data_list, read, counts = [], [], Counter()
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.basename(path) != 'meta.db' or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            counts['files that could not be opened as SQLite'] += 1
            continue
        try:
            rows = starred_rows(db, counts)
        except sqlite3.Error as exc:
            logfunc(f'Starred Files (GNOME Files): could not read {relative}: {exc}')
            continue
        finally:
            db.close()
        if rows is None:
            counts['stores without the starred-files tables, not reported'] += 1
            continue
        data_list.extend(rows)
        if rows:
            read.append(path)
    if counts:
        logfunc('Starred Files (GNOME Files): ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
