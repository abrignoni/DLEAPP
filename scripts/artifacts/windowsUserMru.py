"""Windows Explorer per-user MRU parsers for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange and RegRipper artifacts that read the same
NTUSER.DAT most-recently-used lists; the implementation reads the keys directly
and is not ported from those artifacts.

Covers the Run dialog history (RunMRU), the File Explorer address-bar history
(TypedPaths), the Internet Explorer typed-URL history (TypedURLs), the File
Explorer search-box history (WordWheelQuery) and the common file-dialog lists of
chosen files (OpenSavePidlMRU) and of applications with their last folder
(LastVisitedPidlMRU). The last two store shell item id lists, decoded with the
shared shell-item reader from scripts/windows_lnk.py.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.windows_lnk import _idlist_path
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import user_from_path

_EXPLORER = r"Software\Microsoft\Windows\CurrentVersion\Explorer"

__artifacts_v2__ = {
    "runMru": {
        "name": "Run Dialog MRU",
        "description": "Commands from the Windows Run dialog history (the RunMRU "
                       "key), most-recently-used first, per user.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the RunMRU key in each NTUSER.DAT, named in Source "
                 "File. Command is a value's data with the trailing \\1 marker "
                 "Windows appends removed. RunMRU orders its entries with an "
                 "MRUList string of value letters, most-recent-first; MRU Rank "
                 "is that position, 1 first. Key Last Modified (UTC) is the "
                 "RunMRU key's last-write time, shown on the rank 1 entry only "
                 "because it dates the key as a whole rather than each entry. "
                 "User is taken from the NTUSER.DAT path. An entry records a "
                 "command that was present in the Run dialog history; it does "
                 "not record who ran it. This key held no entries on the tested "
                 "images, so the reader is not exercised against populated data "
                 "here. Reading the hive requires python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (RunMRU empty)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (RunMRU empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (RunMRU empty)",
        },
    },
    "typedPaths": {
        "name": "Explorer Typed Paths",
        "description": "Paths from the File Explorer address-bar history (the "
                       "TypedPaths key), per user.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the TypedPaths key in each NTUSER.DAT, named in "
                 "Source File. Typed Path is a value's data. Entry is the value "
                 "name (url1, url2, ...); Windows numbers the most recent entry "
                 "url1. Key Last Modified (UTC) is the TypedPaths key's "
                 "last-write time, shown on the url1 entry only because it dates "
                 "the key as a whole rather than each entry. User is taken from "
                 "the NTUSER.DAT path. Reading the hive requires python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "folder",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (TypedPaths empty)",
        },
    },
    "typedUrls": {
        "name": "Internet Explorer Typed URLs",
        "description": "Addresses from the Internet Explorer typed-URL history "
                       "(the TypedURLs key), per user, with the typed time where "
                       "recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the Internet Explorer TypedURLs key in each "
                 "NTUSER.DAT, named in Source File. Typed URL is a value's data. "
                 "Entry is the value name (url1, url2, ...); Windows numbers the "
                 "most recent entry url1. Typed Time (UTC) is decoded from the "
                 "matching value in the sibling TypedURLsTime key (a Windows "
                 "FILETIME) when that key is present, and is blank otherwise, "
                 "which was the case on the tested images where Internet "
                 "Explorer was not the browser in use. User is taken from the "
                 "NTUSER.DAT path. A first-run or shipped URL can be present "
                 "without having been entered by a person. Reading the hive "
                 "requires python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
        },
    },
    "wordWheelQuery": {
        "name": "Explorer Search History",
        "description": "Search terms from the File Explorer search-box history "
                       "(the WordWheelQuery key), most-recently-used first, per "
                       "user.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the WordWheelQuery key in each NTUSER.DAT, named in "
                 "Source File. Search Term is a numbered value's data, a UTF-16 "
                 "string. MRU Rank is the entry's place in the key's MRUListEx "
                 "order, 1 first (most recently used). Key Last Modified (UTC) is "
                 "the key's last-write time, shown on the rank 1 entry only "
                 "because it dates the key as a whole rather than each entry. "
                 "User is taken from the NTUSER.DAT path. This key held no search "
                 "terms on the tested images, so the reader is not exercised "
                 "against populated data here. Reading the hive requires "
                 "python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (WordWheelQuery empty)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (WordWheelQuery empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (WordWheelQuery empty)",
        },
    },
    "openSaveMru": {
        "name": "Open and Save Dialog MRU",
        "description": "Files chosen in the Windows open and save dialogs (the "
                       "OpenSavePidlMRU key), by file type, most-recently-used "
                       "first, per user.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the OpenSavePidlMRU key in each NTUSER.DAT, named in "
                 "Source File. File Type is the extension sub-key the entry sits "
                 "under (the * sub-key is the combined list across types, so a "
                 "file can appear both under its extension and under *). File is "
                 "the shell path rebuilt from the entry's shell item id list "
                 "(the same reader the shell-link and ShellBags parsers use); it "
                 "is the item as the dialog recorded it, which may be a full path "
                 "or only a file name under a shell root such as This PC. MRU "
                 "Rank is the entry's place in the sub-key's MRUListEx order, 1 "
                 "first (most recently used). Key Last Modified (UTC) is the "
                 "extension sub-key's last-write time, shown on the rank 1 entry "
                 "only because it dates the sub-key as a whole rather than each "
                 "entry. User is taken from the NTUSER.DAT path. An entry records "
                 "that a file was chosen in an open or save dialog; it does not "
                 "record who chose it. Reading the hive requires python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 43 rows",
        },
    },
    "lastVisitedMru": {
        "name": "File Dialog Application MRU",
        "description": "Applications and the folder each last used in the Windows "
                       "open and save dialogs (the LastVisitedPidlMRU key), per "
                       "user.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the LastVisitedPidlMRU key in each NTUSER.DAT, named "
                 "in Source File. Application is the executable name the entry "
                 "stores, as stored; some entries store a class identifier "
                 "instead of a file name. Folder is the shell path rebuilt from "
                 "the entry's shell item id list, the folder that application "
                 "last used in a file dialog. MRU Rank is the entry's place in "
                 "the key's MRUListEx order, 1 first (most recently used). Key "
                 "Last Modified (UTC) is the key's last-write time, shown on the "
                 "rank 1 entry only because it dates the key as a whole rather "
                 "than each entry. User is taken from the NTUSER.DAT path. "
                 "Reading the hive requires python-registry.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "folder-open",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
        },
    },
}


def _key_time(key):
    stamp = key.timestamp()
    if stamp is None:
        return ''
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp


def _filetime_utc(value):
    if not value:
        return ''
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError):
        return ''


def _open(reg, path):
    try:
        return reg.open(path)
    except Registry.RegistryKeyNotFoundException:
        return None


def _value_bytes(key, name):
    try:
        return key.value(name).raw_data()
    except Registry.RegistryValueNotFoundException:
        return None


def _mrulistex_order(key):
    """Entry numbers from an MRUListEx value, in stored (most-recent-first) order."""
    raw = _value_bytes(key, 'MRUListEx')
    if not raw:
        return []
    order = []
    for offset in range(0, len(raw) - 3, 4):
        number = struct.unpack_from('<i', raw, offset)[0]
        if number == -1:
            break
        order.append(number)
    return order


def _numbered_url_entries(key):
    """(number, name, data) for url1/url2 style values, sorted by number."""
    entries = []
    for value in key.values():
        name = value.name()
        if name.lower().startswith('url'):
            try:
                entries.append((int(name[3:]), name, value.value()))
            except ValueError:
                continue
    entries.sort()
    return entries


def _each_hive(context, artifact):
    """Yield (reg, source, relative_source, user) for each readable NTUSER.DAT."""
    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).upper() == 'NTUSER.DAT']:
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{artifact}: could not read {relative_source}: {exc}')
            continue
        yield reg, source, relative_source, user_from_path(relative_source)


@artifact_processor
def runMru(context):
    data_headers = ('Command', 'MRU Rank', ('Key Last Modified (UTC)', 'datetime'),
                    'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Run Dialog MRU: the python-registry package is not installed')
        return data_headers, data_list, ''
    for reg, source, relative_source, user in _each_hive(context, 'Run Dialog MRU'):
        key = _open(reg, _EXPLORER + r"\RunMRU")
        if key is None:
            continue
        try:
            order = list(key.value('MRUList').value())
        except Registry.RegistryValueNotFoundException:
            order = []
        found = False
        for rank, name in enumerate(order, 1):
            try:
                command = key.value(name).value()
            except Registry.RegistryValueNotFoundException:
                continue
            if command.endswith('\\1'):
                command = command[:-2]
            data_list.append((command, rank, _key_time(key) if rank == 1 else '',
                              user, relative_source))
            found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def typedPaths(context):
    data_headers = ('Typed Path', 'Entry', ('Key Last Modified (UTC)', 'datetime'),
                    'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Explorer Typed Paths: the python-registry package is not installed')
        return data_headers, data_list, ''
    for reg, source, relative_source, user in _each_hive(context, 'Explorer Typed Paths'):
        key = _open(reg, _EXPLORER + r"\TypedPaths")
        if key is None:
            continue
        found = False
        for number, name, data in _numbered_url_entries(key):
            data_list.append((data, name, _key_time(key) if number == 1 else '',
                              user, relative_source))
            found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def typedUrls(context):
    data_headers = ('Typed URL', 'Entry', ('Typed Time (UTC)', 'datetime'),
                    'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Internet Explorer Typed URLs: the python-registry package is not installed')
        return data_headers, data_list, ''
    base = r"Software\Microsoft\Internet Explorer"
    for reg, source, relative_source, user in _each_hive(context, 'Internet Explorer Typed URLs'):
        key = _open(reg, base + r"\TypedURLs")
        if key is None:
            continue
        times = _open(reg, base + r"\TypedURLsTime")
        found = False
        for _number, name, data in _numbered_url_entries(key):
            row_time = ''
            if times is not None:
                raw = _value_bytes(times, name)
                if raw and len(raw) >= 8:
                    row_time = _filetime_utc(struct.unpack_from('<Q', raw, 0)[0])
            data_list.append((data, name, row_time, user, relative_source))
            found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def wordWheelQuery(context):
    data_headers = ('Search Term', 'MRU Rank', ('Key Last Modified (UTC)', 'datetime'),
                    'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Explorer Search History: the python-registry package is not installed')
        return data_headers, data_list, ''
    for reg, source, relative_source, user in _each_hive(context, 'Explorer Search History'):
        key = _open(reg, _EXPLORER + r"\WordWheelQuery")
        if key is None:
            continue
        found = False
        for rank, number in enumerate(_mrulistex_order(key), 1):
            raw = _value_bytes(key, str(number))
            if not raw:
                continue
            term = raw.decode('utf-16-le', 'replace').split('\x00', 1)[0]
            data_list.append((term, rank, _key_time(key) if rank == 1 else '',
                              user, relative_source))
            found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def openSaveMru(context):
    data_headers = ('File', 'File Type', 'MRU Rank',
                    ('Key Last Modified (UTC)', 'datetime'), 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Open and Save Dialog MRU: the python-registry package is not installed')
        return data_headers, data_list, ''
    for reg, source, relative_source, user in _each_hive(context, 'Open and Save Dialog MRU'):
        parent = _open(reg, _EXPLORER + r"\ComDlg32\OpenSavePidlMRU")
        if parent is None:
            continue
        found = False
        for ext_key in parent.subkeys():
            file_type = ext_key.name()
            for rank, number in enumerate(_mrulistex_order(ext_key), 1):
                raw = _value_bytes(ext_key, str(number))
                if not raw:
                    continue
                path = _idlist_path(raw)
                if not path:
                    continue
                data_list.append((path, file_type, rank,
                                  _key_time(ext_key) if rank == 1 else '',
                                  user, relative_source))
                found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def lastVisitedMru(context):
    data_headers = ('Application', 'Folder', 'MRU Rank',
                    ('Key Last Modified (UTC)', 'datetime'), 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('File Dialog Application MRU: the python-registry package is not installed')
        return data_headers, data_list, ''
    for reg, source, relative_source, user in _each_hive(context, 'File Dialog Application MRU'):
        key = _open(reg, _EXPLORER + r"\ComDlg32\LastVisitedPidlMRU")
        if key is None:
            continue
        found = False
        for rank, number in enumerate(_mrulistex_order(key), 1):
            raw = _value_bytes(key, str(number))
            if not raw:
                continue
            end = raw.find(b'\x00\x00')
            if end < 0:
                continue
            if end % 2:
                end += 1
            application = raw[:end].decode('utf-16-le', 'replace').rstrip('\x00')
            folder = _idlist_path(raw[end + 2:])
            data_list.append((application, folder, rank,
                              _key_time(key) if rank == 1 else '',
                              user, relative_source))
            found = True
        if found:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)
