"""Windows RecentDocs parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange RecentDocs artifact; the implementation
reads the value structure directly and is not ported from that artifact.

The numbered-value layout (a UTF-16 name followed by a shell item), the
MRUListEx ordering, and the rule that a key's LastWrite dates only its most
recently used entry are sourced from public research (see the artifact notes).
"""

import struct
from datetime import timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Explorer records recently opened files and folders per user under
# NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs.
# The root holds every recent item; subkeys hold them again split by file
# extension, plus a Folder subkey. Each numbered value is a binary blob that
# begins with the item's name in UTF-16 and is followed by a shell item. The
# MRUListEx value lists the numbered entries in most-recently-used order.

_RECENTDOCS_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"

__artifacts_v2__ = {
    "recentDocs": {
        "name": "Recent Docs",
        "description": "Files and folders recently opened through Explorer, from "
                       "the per-user RecentDocs keys: the item name, which key it "
                       "is under, its most-recently-used rank, and the open time "
                       "of the most recent item in each key.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each NTUSER.DAT, named in Source File. File / Item is "
                 "the name at the start of the numbered value, decoded from "
                 "UTF-16 and shown as stored; the shell item that follows the name "
                 "is not decoded, so a full path is not reconstructed. Key is the "
                 "RecentDocs subkey the entry sits under: Overall is the root, "
                 "which aggregates every recent item, and the extension keys and "
                 "the Folder key repeat those same items split by type, so a file "
                 "appears both under Overall and under its extension. MRU Rank is "
                 "the entry's position in that key's MRUListEx value, where 0 is "
                 "the most recently used; it is blank for a numbered entry that "
                 "MRUListEx no longer lists. Opened (UTC) is the key's LastWrite "
                 "time, which dates only the most recently used entry of each key, "
                 "so it is shown on the MRU Rank 0 entry alone and is blank for the "
                 "rest; the open time of earlier entries is not recorded. Presence "
                 "of an entry does not establish who opened the item, and an entry "
                 "can outlive the file it names. Reading the hives requires the "
                 "python-registry package. Structure and the LastWrite rule: "
                 "Jason Hale, 'The RecentDocs Key in Windows 10', Forensic 4:cast, "
                 "https://forensic4cast.com/2019/03/the-recentdocs-key-in-windows-10/",
        "paths": (r"*/Users/*/NTUSER.DAT",),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 37 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 27 rows",
        },
    },
}


def _leading_utf16_name(blob):
    """The item name at the start of a RecentDocs value, up to the UTF-16 NUL."""
    end = 0
    while end + 1 < len(blob):
        if blob[end] == 0 and blob[end + 1] == 0:
            break
        end += 2
    return blob[:end].decode('utf-16-le', errors='replace')


def _mru_order(values):
    """Map each numbered entry to its MRUListEx rank (0 = most recent)."""
    raw = values.get('MRUListEx')
    ranks = {}
    if isinstance(raw, bytes):
        rank = 0
        for offset in range(0, len(raw) - 3, 4):
            index = struct.unpack_from('<i', raw, offset)[0]
            if index == -1:
                break
            ranks[index] = rank
            rank += 1
    return ranks


def _recent_docs_key(hive_path):
    reg = Registry.Registry(hive_path)
    try:
        return reg.open(_RECENTDOCS_PATH)
    except Registry.RegistryKeyNotFoundException:
        return None


def _rows_for_key(key, label, relative_source):
    values = {v.name(): v.value() for v in key.values()}
    ranks = _mru_order(values)
    last_write = key.timestamp()
    if last_write is not None and last_write.tzinfo is None:
        last_write = last_write.replace(tzinfo=timezone.utc)
    rows = []
    for name, data in values.items():
        if not name.isdigit() or not isinstance(data, bytes):
            continue
        rank = ranks.get(int(name))
        opened = last_write if rank == 0 else ''
        rows.append((_leading_utf16_name(data), label,
                     '' if rank is None else rank, opened, relative_source))
    return rows


@artifact_processor
def recentDocs(context):
    data_headers = ('File / Item', 'Key', 'MRU Rank',
                    ('Opened (UTC)', 'datetime'), 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('RecentDocs: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).upper().endswith('NTUSER.DAT')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            root = _recent_docs_key(source)
            if root is None:
                continue
            for row in _rows_for_key(root, 'Overall', relative_source):
                data_list.append(row)
                rows_here += 1
            for sub in root.subkeys():
                for row in _rows_for_key(sub, sub.name(), relative_source):
                    data_list.append(row)
                    rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'RecentDocs: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
