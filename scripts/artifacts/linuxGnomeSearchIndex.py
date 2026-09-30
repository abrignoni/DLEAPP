"""Files and folders in the GNOME search index (LocalSearch, formerly Tracker Miners), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxGnomeSearchIndexFiles": {
        "name": "Search Index Files (GNOME)",
        "description": "Files and folders in the GNOME search index, with the name, size and times the indexer "
                       "recorded when it last processed each one and the time it was added to the index.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the database LocalSearch (formerly Tracker Miners), the GNOME desktop's file "
                 "indexer, keeps at .cache/tracker3/files/meta.db in a user's home folder, one row per file "
                 "or folder in its FileSystem graph (nfo:FileDataObject). When LocalSearch processes a file "
                 "it records the name and size GIO reports, the modification time, the access time and, "
                 "where GIO reports one, the creation time, and the file's URL (LocalSearch 3.11.0, "
                 "https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-miner-files-methods.c#L198-241). "
                 "It asks GIO for the modification and creation times with microseconds and for the access "
                 "time without them "
                 "(https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-file-notifier.h#L36-44), "
                 "so File Accessed holds whole seconds. When GIO gives no modification time, LocalSearch "
                 "stores the Unix epoch "
                 "(https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-miner-files-methods.c#L203-205), "
                 "so a File Modified of 1970-01-01 00:00:00 does not by itself show which happened: the 3 "
                 "rows on the tested store that held it were files whose modification time on the VM, "
                 "checked after the capture, was 0. tinysparql stores a time as Unix seconds when it is UTC "
                 "with no fraction of a second and as ISO 8601 text otherwise (tinysparql 3.11.0, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L1139-1156); "
                 "the artifact reports both as UTC. A row gives what the index held when LocalSearch last "
                 "processed that file, not the file's state when the image was made. Indexed is nrl:added in "
                 "the FileSystem graph, the time at which the transaction that first inserted the file's "
                 "resource began "
                 "(https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L1859-1871, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-update.c#L2943). "
                 "Type is Folder when the file is linked to an nfo:Folder "
                 "(https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-miner-files-methods.c#L293-304) "
                 "and File otherwise. Path is the file URL with its percent escapes decoded. MIME Type and "
                 "Metadata Graphs come from the information elements that the other graphs (on the tested "
                 "store Documents, Pictures, Audio, Video and Software) link to the file with "
                 "nie:isStoredAs. LocalSearch writes one only when an extractor handles the file's MIME "
                 "type, and for a text file without an allowed extension it writes one with no MIME type "
                 "(https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-miner-files-methods.c#L243-292, "
                 "https://gitlab.gnome.org/GNOME/localsearch/-/blob/bb5b477893df0a838e21f8ee32013200472d3404/src/indexer/tracker-miner-files-methods.c#L126-148), "
                 "so MIME Type is blank for other files, for those text files and for folders other than the "
                 "root of the index. The metadata in those graphs (such as EXIF and document text) is not "
                 "reported. Stores whose PRAGMA user_version is below 32 keep each graph in its own file "
                 "beside meta.db "
                 "(https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-data-manager.c#L1512-1548; "
                 "version list, "
                 "https://gitlab.gnome.org/GNOME/tinysparql/-/blob/df9fd707f2f6b1233a3ab5301f99802f45512230/src/libtinysparql/core/tracker-db-manager.h#L52-59); "
                 "the artifact logs them and does not read them, and none was available to test. Known data, "
                 "ubuntu2604_arm64_tracker (Ubuntu 26.04, LocalSearch 3.11.0 indexing the whole home folder, "
                 "VM clock about 5,157.9 s ahead of real time): five files written into a test folder in "
                 "Documents had each been listed by localsearch info within 2.5 s of being written. A file "
                 "whose modification time was set to 2026-01-02 03:04:05 UTC shows exactly that. After a "
                 "line was appended to a file, File Modified moved to the time of the append and Indexed "
                 "kept its first value. A deleted file and the old name of a renamed file had no row; the "
                 "renamed file had a new Indexed time, and the Resource table still held both old URLs, "
                 "which the artifact does not report. The folder holding the renamed file kept the "
                 "modification time it had before the rename. For each known file the row's name, size, the "
                 "three file times and MIME type equal what localsearch info reported, and Indexed is one of "
                 "the insertion times it listed. The store gave 44,623 rows, 14,225 folders and 30,398 "
                 "files. MIME Type was filled on 5,494 rows; Metadata Graphs named Pictures on 4,577, "
                 "Documents on 4,338 (3,445 of them with no MIME type), Audio on 20, Software on 3, and all "
                 "five on 1, the home folder at the root of the index, with inode/directory. File Created "
                 "carried microseconds on every row, File Modified on 1,789 and File Accessed on none. 7 "
                 "rows had no name, size or nie:url and take their path from the resource's URI; 2 rows had "
                 "no Indexed value. Every stored time was UTC.",
        "paths": ('*/.cache/tracker3/files/meta.db*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "ubuntu2604_arm64_tracker": "Ubuntu 26.04 LTS aarch64, LocalSearch 3.11.0 | 44623 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
        },
    },
}

import datetime
import os
import sqlite3
import urllib.parse
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

ONTOLOGY = 'http://tracker.api.gnome.org/ontology/v3/tracker#'
FILESYSTEM = ONTOLOGY + 'FileSystem'
STORED_AS = '_nie:InformationElement_nie:isStoredAs'
# PRAGMA user_version from which every graph is a set of prefixed tables in meta.db
# (TRACKER_DB_VERSION_3_10_B); earlier stores keep each graph in its own file.
UNIFIED_VERSION = 32


def tracker_time(value):
    """A stored xsd:dateTime as a UTC datetime, or None when it cannot be read.

    tinysparql binds an integer (Unix seconds) when the value is UTC with no fraction of a
    second, and ISO 8601 text otherwise.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc)
    text = str(value)
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        parsed = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(datetime.timezone.utc)


def url_path(url):
    """A file:// URL as a path; any other URL as stored."""
    if url and url.startswith('file://'):
        return urllib.parse.unquote(url[len('file://'):])
    return url or ''


def graph_label(graph):
    return graph[len(ONTOLOGY):] if graph.startswith(ONTOLOGY) else graph


def _tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def index_rows(db, counts):
    """(indexed, modified, accessed, created, type, path, name, size, MIME types, graphs) for
    each nfo:FileDataObject in the FileSystem graph, in the order the index numbered them."""
    tables = _tables(db)
    graphs = sorted(t[:-len(STORED_AS)] for t in tables
                    if t.endswith(STORED_AS) and t[:-len(STORED_AS)] != FILESYSTEM)
    interpreted = {}
    for graph in graphs:
        for file_id, mime in db.execute(
                f'SELECT s."nie:isStoredAs", ie."nie:mimeType" FROM "{graph}{STORED_AS}" s '
                f'LEFT JOIN "{graph}_nie:InformationElement" ie ON ie.ID = s.ID'):
            interpreted.setdefault(file_id, []).append((graph_label(graph), mime or ''))
    folders = set()
    if FILESYSTEM + '_nfo:Folder' in tables:
        folders = {row[0] for row in db.execute(
            f'SELECT i.ID FROM "{FILESYSTEM}_nie:DataObject_nie:interpretedAs" i '
            f'JOIN "{FILESYSTEM}_nfo:Folder" f ON f.ID = i."nie:interpretedAs"')}
    query = (f'SELECT f.ID, f."nfo:fileName", f."nfo:fileSize", f."nfo:fileLastModified", '
             f'f."nfo:fileLastAccessed", f."nfo:fileCreated", d."nie:url", r."nrl:added", res.Uri '
             f'FROM "{FILESYSTEM}_nfo:FileDataObject" f '
             f'LEFT JOIN "{FILESYSTEM}_nie:DataObject" d ON d.ID = f.ID '
             f'LEFT JOIN "{FILESYSTEM}_rdfs:Resource" r ON r.ID = f.ID '
             f'LEFT JOIN Resource res ON res.ID = f.ID ORDER BY f.ID')
    for file_id, name, size, modified, accessed, created, url, added, uri in db.execute(query):
        times = []
        for value in (added, modified, accessed, created):
            converted = tracker_time(value)
            if converted is None and value is not None:
                counts['times that could not be read, left blank'] += 1
            times.append(converted or '')
        if url is None:
            counts['rows with no nie:url, path taken from the resource URI'] += 1
        linked = interpreted.get(file_id, [])
        yield (*times, 'Folder' if file_id in folders else 'File', url_path(url or uri), name or '',
               '' if size is None else size, ', '.join(sorted({m for _, m in linked if m})),
               ', '.join(sorted({g for g, _ in linked})))


@artifact_processor
def linuxGnomeSearchIndexFiles(context):
    data_headers = (('Indexed', 'datetime'), ('File Modified', 'datetime'), ('File Accessed', 'datetime'),
                    ('File Created', 'datetime'), 'Type', 'Path', 'Name', 'Size', 'MIME Type', 'Metadata Graphs',
                    'Source File')
    data_list, read, counts = [], [], Counter()
    for path in sorted({str(f) for f in context.get_files_found()}):
        if not path.endswith('meta.db') or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version < UNIFIED_VERSION:
                logfunc(f'Search Index Files (GNOME): {relative} is database version {version}, which keeps '
                        'each graph in its own file; not read')
                continue
            if FILESYSTEM + '_nfo:FileDataObject' not in _tables(db):
                logfunc(f'Search Index Files (GNOME): {relative} has no FileSystem graph; not read')
                continue
            data_list.extend(row + (relative,) for row in index_rows(db, counts))
            read.append(path)
        except sqlite3.Error as exc:
            logfunc(f'Search Index Files (GNOME): could not read {relative}: {exc}')
        finally:
            db.close()
    if counts:
        logfunc('Search Index Files (GNOME): ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
