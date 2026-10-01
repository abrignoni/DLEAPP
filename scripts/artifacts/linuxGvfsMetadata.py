"""Per-file metadata GVfs keeps for GNOME applications (gvfsd-metadata trees and journals), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxGvfsMetadata": {
        "name": "GVfs Metadata",
        "description": "Keys set for files through GVfs metadata, from each metadata tree, with the file's path "
                       "within the tree, the key and its value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the tree files in .local/share/gvfs-metadata in a home folder, where gvfsd-metadata "
                 "keeps the keys set for files through GIO's metadata:: attributes, as gio set sets them "
                 "(GVfs 1.60.0, layout in "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/file-format.txt#L1-52). "
                 "Tree is the file's name: home holds paths under the home folder, written relative to it, "
                 "root holds other paths on the root file system, and another volume gets uuid- or label- "
                 "followed by its file system's UUID or label "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L3364-3398, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/meta-daemon.c#L407-410). "
                 "Path is the path within the tree, and Key and Value are a key and its value, a list value "
                 "with one item per line. A row with no key is an entry that holds no key but has a change "
                 "time, such as the folder of a removed file or a file whose only key was unset. Last "
                 "Changed (as GVfs reads it) is the stored offset plus the header's base, as GVfs reads it "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L989-996), "
                 "shown as text because it is not reliable: GVfs writes the root entry's time without "
                 "subtracting the base "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metabuilder.c#L1173-1174) "
                 "and reads it back with the base added "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2260-2261), "
                 "so the root's time grows at each write-out, and once the times span more than 2^32 s the "
                 "base is set to the latest time less 2^32 - 1 and every time at or before the new base is "
                 "stored as 1 "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metabuilder.c#L1124-1136, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metabuilder.c#L535-547). "
                 "It applies once the root entry has a change time, as when a key is set on the root itself "
                 "or a file directly under it is removed. On the tested store the root held a key, and it "
                 "read 2150-01-25, one entry 2060-07-23 and the others 2060-01-13, all after the capture. "
                 "Changes not yet merged into a tree are in the journal beside it, reported by the GVfs "
                 "Metadata Journal artifact; GVfs gives a key's value from the newest journal entry for its "
                 "path before the tree "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L1283-1357), "
                 "and this artifact does not merge them. Known data, ubuntu2604_arm64_gvfsmeta (Ubuntu "
                 "26.04, GVfs 1.60.0, VM clock about 5,157.8 s ahead of real time): gio set, gio copy "
                 "--preserve, gio move and gio remove on files in a test folder in Documents. The capture "
                 "gave 7 rows; Tree held home on all 7 rows, as the root tree held no entry, and the keys "
                 "these rows and the journal's entries give together equal what gio info reported for each "
                 "known file after the next write-out. gio copy --preserve gave the copy no key.",
        "paths": ('*/.local/share/gvfs-metadata/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS aarch64, GVfs 1.60.0 | 7 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxGvfsMetadataJournal": {
        "name": "GVfs Metadata Journal",
        "description": "Changes to GVfs metadata recorded in a metadata journal and not yet merged into its tree, "
                       "each with the time it was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the journal files in .local/share/gvfs-metadata in a home folder, named after their "
                 "tree with a -<tag>.log suffix "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metabuilder.c#L1002-1030), "
                 "one row per entry; a journal kept in $XDG_RUNTIME_DIR, as GVfs does when the home folder "
                 "is on NFS, is not read (GVfs 1.60.0, layout in "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/file-format.txt#L54-109). "
                 "gvfsd-metadata writes an entry for each change and takes Time from the clock when it "
                 "writes it "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2461, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2506, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2551, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2594, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L2638). "
                 "Operation is Set, Set list, Unset, Copy or Remove; for a Copy, Path is the destination and "
                 "Source Path the source. A list value has one item per line. The daemon merges the journal "
                 "into its tree and starts a new journal 60 s after a change "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/meta-daemon.c#L44, "
                 "https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/meta-daemon.c#L97-100), "
                 "so a journal holds the changes made since the last write-out. Entries are read up to the "
                 "first that fails its length or checksum check, as GVfs reads them "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L863-941), "
                 "and any after it are counted in the run log. GVfs gives a key's value from the newest "
                 "journal entry for its path before the tree "
                 "(https://gitlab.gnome.org/GNOME/gvfs/-/blob/d9f29d3e4238fc3c279b682269e2f7ca97bb8ec1/metadata/metatree.c#L1283-1357); "
                 "the GVfs Metadata artifact reports the tree, and neither artifact merges them. Known data, "
                 "ubuntu2604_arm64_gvfsmeta (Ubuntu 26.04, GVfs 1.60.0, VM clock about 5,157.8 s ahead of "
                 "real time): copies of the metadata folder after each step showed one entry for each gio "
                 "set and gio remove, a Copy and a Remove for a gio move, and nothing for a gio copy "
                 "--preserve, and the next write-out emptied the journal. The capture, taken within 60 s of "
                 "two more changes, gave 2 entries, each with the time of its step.",
        "paths": ('*/.local/share/gvfs-metadata/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS aarch64, GVfs 1.60.0 | 2 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
        },
    },
}

import datetime
import os
import re
import struct
import zlib
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

TREE_MAGIC = b'\xda\x1ameta'
JOURNAL_MAGIC = b'\xda\x1ajour'
OPERATIONS = {0: 'Set', 1: 'Set list', 2: 'Unset', 3: 'Copy', 4: 'Remove'}
LIST = 1 << 31
JOURNAL_NAME = re.compile(r'^(.*)-[0-9a-f]{8}\.log$')


class GvfsError(ValueError):
    pass


def _u32(data, pos):
    if pos < 0 or pos + 4 > len(data):
        raise GvfsError(f'offset {pos} outside the file')
    return struct.unpack_from('>I', data, pos)[0]


def _string(data, pos):
    end = data.find(b'\0', pos)
    if pos < 0 or pos >= len(data) or end < 0:
        raise GvfsError(f'string at {pos} not terminated')
    return data[pos:end].decode('utf-8', 'replace')


def tree_rows(data):
    """(path, key, value, last changed) for each key of each entry in a tree, breadth first as stored; an entry
    with no key but a change time gives one row with key and value None. A list value is a list of strings.
    The change time is the stored offset plus the header's base, as GVfs reads it, or None when stored as 0."""
    if data[:6] != TREE_MAGIC:
        raise GvfsError('not a GVfs metadata tree')
    if len(data) < 32:
        raise GvfsError('file shorter than a tree header')
    if data[6] != 1:
        raise GvfsError(f'tree version {data[6]}.{data[7]} not read')
    root, attributes = struct.unpack_from('>II', data, 16)
    base = struct.unpack_from('>q', data, 24)[0]
    keys = [_string(data, _u32(data, attributes + 4 + 4 * i)) for i in range(_u32(data, attributes))]
    rows, queue, seen = [], [(None, root)], set()
    while queue:
        parent, pos = queue.pop(0)
        if pos in seen:
            raise GvfsError('entry visited twice')
        seen.add(pos)
        if pos + 16 > len(data):
            raise GvfsError(f'entry at {pos} outside the file')
        name_at, children, metadata, changed = struct.unpack_from('>IIII', data, pos)
        name = _string(data, name_at)
        path = '/' if parent is None else parent.rstrip('/') + '/' + name
        when = None if changed == 0 else changed + base
        count = _u32(data, metadata) if metadata else 0
        for i in range(count):
            key_id, value_at = struct.unpack_from('>II', data, metadata + 4 + 8 * i)
            index = key_id & ~LIST
            if index >= len(keys):
                raise GvfsError(f'key {index} not in the key table')
            if key_id & LIST:
                value = [_string(data, _u32(data, value_at + 4 + 4 * j)) for j in range(_u32(data, value_at))]
            else:
                value = _string(data, value_at)
            rows.append((path, keys[index], value, when))
        if not count and when is not None:
            rows.append((path, None, None, when))
        if children:
            for i in range(_u32(data, children)):
                queue.append((path, children + 4 + 16 * i))
    return rows


def journal_rows(data):
    """(time, operation, path, key, value, source path) for each entry up to the first one that fails its
    checks, and the number of entries the header records."""
    if data[:6] != JOURNAL_MAGIC or len(data) < 20:
        raise GvfsError('not a GVfs metadata journal')
    claimed = _u32(data, 16)
    rows, pos = [], 20
    while len(rows) < claimed and pos + 24 <= len(data):
        length = _u32(data, pos)
        if length % 4 or length < 24 or pos + length > len(data) or _u32(data, pos + length - 4) != length:
            break
        if zlib.crc32(data[pos + 8:pos + length]) != _u32(data, pos + 4):
            break
        mtime = struct.unpack_from('>Q', data, pos + 8)[0]
        op = data[pos + 16]
        at = pos + 17
        path = _string(data, at)
        at = data.index(b'\0', at) + 1
        key = value = source = ''
        if op in (0, 1, 2):
            key = _string(data, at)
            at = data.index(b'\0', at) + 1
            if op == 0:
                value = _string(data, at)
            elif op == 1:
                at = (at + 3) // 4 * 4
                count = _u32(data, at)
                at += 4
                value = []
                for _ in range(count):
                    value.append(_string(data, at))
                    at = data.index(b'\0', at) + 1
        elif op == 3:
            source = _string(data, at)
        rows.append((mtime, OPERATIONS.get(op, f'Unknown ({op})'), path, key, value, source))
        pos += length
    return rows, claimed


def _utc(seconds):
    try:
        return datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _value_text(value):
    return '\n'.join(value) if isinstance(value, list) else (value or '')


def _stores(context, magic):
    for path in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(path):
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            continue
        if data[:6] == magic:
            yield path, data


@artifact_processor
def linuxGvfsMetadata(context):
    data_headers = ('Tree', 'Path', 'Key', 'Value', 'Last Changed (as GVfs reads it)', 'Source File')
    data_list, read = [], []
    for path, data in _stores(context, TREE_MAGIC):
        relative = context.get_relative_path(path)
        try:
            rows = tree_rows(data)
        except (GvfsError, struct.error) as exc:
            logfunc(f'GVfs Metadata: could not read {relative}: {exc}')
            continue
        tree = os.path.basename(path)
        for file_path, key, value, when in rows:
            moment = _utc(when) if when is not None else None
            data_list.append((tree, file_path, key or '', _value_text(value),
                              moment.strftime('%Y-%m-%d %H:%M:%S') if moment else ('' if when is None else str(when)),
                              relative))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxGvfsMetadataJournal(context):
    data_headers = (('Time', 'datetime'), 'Tree', 'Operation', 'Path', 'Key', 'Value', 'Source Path', 'Source File')
    data_list, read, counts = [], [], Counter()
    for path, data in _stores(context, JOURNAL_MAGIC):
        relative = context.get_relative_path(path)
        try:
            rows, claimed = journal_rows(data)
        except (GvfsError, struct.error) as exc:
            logfunc(f'GVfs Metadata Journal: could not read {relative}: {exc}')
            continue
        if len(rows) < claimed:
            counts['entries after the first that failed its checks, not read'] += claimed - len(rows)
        match = JOURNAL_NAME.match(os.path.basename(path))
        tree = match.group(1) if match else ''
        for mtime, operation, file_path, key, value, source in rows:
            data_list.append((_utc(mtime) or '', tree, operation, file_path, key, _value_text(value), source,
                              relative))
        read.append(path)
    if counts:
        logfunc('GVfs Metadata Journal: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
