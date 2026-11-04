"""Legacy Microsoft Edge (EdgeHTML) favorites and typed URLs for DLEAPP.

Author: @AlexisBrignoni, Claude.
Legacy Edge keeps its favorites and, on later Windows 10 releases, its typed URLs in an ESE
database, spartan.edb, under the browser's package folder; earlier releases keep typed URLs
in the user's UsrClass.dat. Both browser importers that migrate this data read it there:
Chromium's Edge importer (Favorites table) and Firefox's Edge migrator (Favorites, TypedUrls
table and the TypedURLs registry key). The database is read with the ESE reader adapted from
impacket in scripts/vendor; a database in dirty shutdown is replayed in memory from its logs
by scripts/ese_recovery when that replay can be done exactly, and read as stored otherwise.
"""

import os
import struct

try:
    from scripts.vendor import impacket_ese
    from scripts import ese_recovery, ese_rows
except ImportError:
    impacket_ese = None
    ese_recovery = None
    ese_rows = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, filetime_utc, found_hives, open_hive, open_key,
                                      user_from_path)

_SPARTAN = 'spartan.edb'
_EDGE_KEY = (r'Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Storage'
             r'\microsoft.microsoftedge_8wekyb3d8bbwe\MicrosoftEdge')
_ROW_CAP = 1_000_000

__artifacts_v2__ = {
    "legacyEdgeFavorites": {
        "name": "Legacy Edge Favorites",
        "description": "Favorites saved in legacy Microsoft Edge (EdgeHTML), from the Favorites table of "
                       "spartan.edb, with their folder, the time each was last updated and whether Edge "
                       "marked it deleted.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "One row per favorite (a Favorites table row whose IsFolder is not set) in each spartan.edb, "
                 "named in Source File: the live database under the Edge package's DataStore folder, and the "
                 "copies under MicrosoftEdgeBackups when present. The columns are read as Chromium's Edge "
                 "importer reads them, whose comment gives the table's schema (" "https://github.com/chromium/chromium/blob/b9c0ca47c45c16d8b6b9686a5b06c6412d49eeaf/chrome/utility/importer/edge_importer_win.cc" "#L194-L211): "
                 "Title and URL as stored, Date Updated (UTC) from DateUpdated, a little-endian Windows "
                 "FILETIME (a 0 is shown blank), and Folder from ParentId, naming each folder row the "
                 "favorite sits in by its Title, outermost first, joined by \" > \". A favorite whose "
                 "ParentId names no folder row is placed at the top, as the importer does (#L286-L293). "
                 "_Favorites_Bar_ is the folder the importer treats as the favorites bar (#L38). Is "
                 "Deleted is the IsDeleted Bit column: Yes when it holds 255 (true, as Firefox's ESE reader "
                 "reads a Bit, " "https://github.com/mozilla-firefox/firefox/blob/8cd6654295f5f314374f36df6226d21a73cbac44/" "browser/components/migration/ESEDBReader.sys.mjs#L587-L589), "
                 "No when it holds 0, and blank when the column is NULL; both importers skip a row with "
                 "IsDeleted set (" "https://github.com/chromium/chromium/blob/b9c0ca47c45c16d8b6b9686a5b06c6412d49eeaf/chrome/utility/importer/edge_importer_win.cc" "#L251-L254). On the tested databases IsDeleted was NULL on "
                 "every row. A database in dirty shutdown is replayed in memory from its transaction logs "
                 "(the LogFiles folder beside the live database, the folder itself for a backup) when "
                 "scripts/ese_recovery can reproduce every change exactly, and is otherwise read as stored, "
                 "with the reason in the run log; each tested database in dirty shutdown was read as stored. "
                 "Edge, or an importer that opens the database through Windows' own ESE engine, may see "
                 "rows a database read as stored does not show. A record ESE marks deleted is not read and "
                 "is counted in the run log. Rows of folders are not listed. Source: Chromium's Edge "
                 "importer, " "https://github.com/chromium/chromium/blob/b9c0ca47c45c16d8b6b9686a5b06c6412d49eeaf/chrome/utility/importer/edge_importer_win.cc" ".",
        "paths": (
            '*/AppData/Local/Packages/[Mm]icrosoft.[Mm]icrosoft[Ee]dge_8wekyb3d8bbwe/AC/[Mm]icrosoft[Ee]dge/User/Default/'
            'DataStore/Data/*/DBStore/spartan.edb',
            '*/AppData/Local/Packages/[Mm]icrosoft.[Mm]icrosoft[Ee]dge_8wekyb3d8bbwe/AC/[Mm]icrosoft[Ee]dge/User/Default/'
            'DataStore/Data/*/DBStore/LogFiles/*.log',
            '*/MicrosoftEdgeBackups/backups/*/DatastoreBackup/spartan.edb',
            '*/MicrosoftEdgeBackups/backups/*/DatastoreBackup/*.log',
        ),
        "output_types": ["standard"],
        "artifact_icon": "bookmark",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the Favorites table holds only a folder)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Favorites table holds a favorite)",
        },
    },
    "legacyEdgeTypedUrls": {
        "name": "Legacy Edge Typed URLs",
        "description": "Addresses typed into the legacy Microsoft Edge (EdgeHTML) address bar, from the "
                       "TypedUrls table of spartan.edb and from the browser's TypedURLs key in UsrClass.dat, "
                       "with the typed time where recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "python-registry for the UsrClass.dat key",
        "category": "Windows",
        "notes": "Rows from the two places Firefox's Edge migrator reads typed URLs from: the TypedUrls table of "
                 "spartan.edb (" "https://github.com/mozilla-firefox/firefox/blob/8cd6654295f5f314374f36df6226d21a73cbac44/" "browser/components/migration/EdgeProfileMigrator.sys.mjs#L198-L205)"
                 " and the TypedURLs key under the Edge package's storage key in the user's registry ("
                 "#L20-L23 and #L118), which is UsrClass.dat, Software\\Classes in the user's registry. Store "
                 "names which one a row came from, and Source File the file. From the table, URL is the URL "
                 "column and Typed Time (UTC) is AccessDateTimeUTC, which Firefox requires to be a LongLong "
                 "and reads as a Windows FILETIME (ESEDBReader.sys.mjs#L610-L621, #L683-L691); a 0 is shown "
                 "blank, which 3 of the 7 tested rows held. From the key, URL is the data of a value named "
                 "url followed by a number, Entry is that name, and Typed Time (UTC) is the 8-byte FILETIME "
                 "in the value of the same name in the sibling TypedURLsTime key, blank where that value is "
                 "missing (browser/components/migration/MSMigrationUtils.sys.mjs#L468-L530). Rows from the "
                 "key are listed by that number. On the tested images the key held typed URLs on Windows 10 "
                 "build 16299 and the table on builds 17763 and 19041, never both. On szechuan_win10 one "
                 "typed URL also appears in WebCache History, accessed 0.6 to 0.7 seconds after its typed "
                 "time. The table's VisitCount column is not shown: neither importer reads it, and it held 1 "
                 "on every tested row. User is taken from the path. A typed URL records what was entered in "
                 "the address bar, not who entered it. spartan.edb is read and replayed as described in "
                 "Legacy Edge Favorites; a dirty UsrClass.dat is read after its .LOG1 and .LOG2 logs are "
                 "applied, as in the other registry artifacts.",
        "paths": (
            '*/AppData/Local/Packages/[Mm]icrosoft.[Mm]icrosoft[Ee]dge_8wekyb3d8bbwe/AC/[Mm]icrosoft[Ee]dge/User/Default/'
            'DataStore/Data/*/DBStore/spartan.edb',
            '*/AppData/Local/Packages/[Mm]icrosoft.[Mm]icrosoft[Ee]dge_8wekyb3d8bbwe/AC/[Mm]icrosoft[Ee]dge/User/Default/'
            'DataStore/Data/*/DBStore/LogFiles/*.log',
            '*/MicrosoftEdgeBackups/backups/*/DatastoreBackup/spartan.edb',
            '*/MicrosoftEdgeBackups/backups/*/DatastoreBackup/*.log',
            '*/AppData/Local/Microsoft/Windows/[Uu]sr[Cc]lass.[Dd]at',
            '*/AppData/Local/Microsoft/Windows/[Uu]sr[Cc]lass.[Dd]at.LOG*',
        ),
        "output_types": ["standard"],
        "artifact_icon": "edit-3",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
        },
    },
}


def _norm_row(row):
    return {(key.decode('latin-1') if isinstance(key, (bytes, bytearray)) else key): value
            for key, value in row.items()}


def _bit(value):
    if value is None:
        return ''
    if value == 255:
        return 'Yes'
    if value == 0:
        return 'No'
    return value


def _spartan_sources(context):
    return sorted(str(found) for found in context.get_files_found()
                  if os.path.basename(str(found)).lower() == _SPARTAN and os.path.isfile(str(found)))


def _open_spartan(source, label, relative_source):
    """spartan.edb as ESE's recovery would leave it, or as stored when the replay is refused."""
    log_folder = os.path.join(os.path.dirname(source), 'LogFiles')
    if not os.path.isdir(log_folder):
        log_folder = None
    try:
        data, summary = ese_recovery.replayed_database(source, log_folder=log_folder)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        data, summary = None, f'not replayed: {type(exc).__name__}: {exc}'
    replayed = data is not None and summary.startswith('replayed')
    if replayed or 'clean shutdown' not in summary:
        logfunc(f"{label}: {relative_source}, {summary}" + ('' if replayed else '; read as stored'))
    return ese_rows.ESEDatabase(source, data=data if replayed else None)


def _table_rows(context, table, label):
    """(source, relative_source, rows) for each spartan.edb holding the table."""
    if impacket_ese is None:
        logfunc(f"{label}: the vendored ESE reader is not available")
        return
    for source in _spartan_sources(context):
        relative_source = context.get_relative_path(source)
        try:
            database = _open_spartan(source, label, relative_source)
            try:
                database.mountDB()
                walk = ese_rows.TableRows(database, table, cap=_ROW_CAP)
                rows = [_norm_row(row) for row in walk]
                if not walk.found:
                    logfunc(f"{label}: {relative_source} has no {table} table")
                elif walk.summary():
                    logfunc(f"{label}: {relative_source}, {walk.summary()}")
            finally:
                database.close()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"{label}: could not read {relative_source}: {exc}")
            continue
        yield source, relative_source, rows


def favorite_rows(rows):
    """(date updated, title, url, folder, is deleted) per favorite in one Favorites table."""
    by_id = {row.get('ItemId'): row for row in rows if row.get('ItemId') is not None}
    out = []
    for row in rows:
        if row.get('IsFolder') == 255:
            continue
        folders = []
        seen = set()
        parent = by_id.get(row.get('ParentId'))
        while parent is not None and parent.get('IsFolder') == 255 and parent.get('ItemId') not in seen:
            seen.add(parent.get('ItemId'))
            folders.append(parent.get('Title') or '')
            parent = by_id.get(parent.get('ParentId'))
        out.append((filetime_utc(row.get('DateUpdated')), row.get('Title') or '', row.get('URL') or '',
                    ' > '.join(reversed(folders)), _bit(row.get('IsDeleted'))))
    return out


@artifact_processor
def legacyEdgeFavorites(context):
    data_headers = (('Date Updated (UTC)', 'datetime'), 'Title', 'URL', 'Folder', 'Is Deleted', 'User',
               'Source File')
    data_list = []
    sources = []
    for source, relative_source, rows in _table_rows(context, 'Favorites', 'Legacy Edge Favorites'):
        built = favorite_rows(rows)
        user = user_from_path(relative_source)
        for row in built:
            data_list.append(row + (user, relative_source))
        if built:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


def registry_typed_urls(key, times):
    """(entry, url, typed time) for each urlN value of the TypedURLs key, by its number."""
    entries = []
    for value in key.values():
        name = value.name()
        if not name.lower().startswith('url'):
            continue
        try:
            number = int(name[3:])
        except ValueError:
            continue
        typed = ''
        if times is not None:
            try:
                raw = times.value(name).raw_data()
            except Registry.RegistryValueNotFoundException:
                raw = None
            if raw and len(raw) == 8:
                typed = filetime_utc(struct.unpack('<Q', raw)[0])
        entries.append((number, name, value.value(), typed))
    entries.sort()
    return [(name, url, typed) for _number, name, url, typed in entries]


@artifact_processor
def legacyEdgeTypedUrls(context):
    data_headers = (('Typed Time (UTC)', 'datetime'), 'URL', 'Entry', 'Store', 'User', 'Source File')
    data_list = []
    sources = []
    label = 'Legacy Edge Typed URLs'
    for source, relative_source, rows in _table_rows(context, 'TypedUrls', label):
        user = user_from_path(relative_source)
        for row in rows:
            data_list.append((filetime_utc(row.get('AccessDateTimeUTC')), row.get('URL') or '', '',
                              'spartan.edb TypedUrls table', user, relative_source))
        if rows:
            sources.append(source)
    if Registry is None:
        logfunc(f'{label}: the python-registry package is not installed, so UsrClass.dat is not read')
        return data_headers, data_list, '\n'.join(sources)
    for source in found_hives(context, 'USRCLASS.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative_source}: {exc}')
            continue
        key = open_key(reg, _EDGE_KEY + r'\TypedURLs')
        if key is None:
            continue
        found = registry_typed_urls(key, open_key(reg, _EDGE_KEY + r'\TypedURLsTime'))
        user = user_from_path(relative_source)
        for name, url, typed in found:
            data_list.append((typed, url, name, 'TypedURLs registry key', user, relative_source))
        if found:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
