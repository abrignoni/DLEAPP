"""Windows Jump Lists parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Lnk / Jump List work.
The destination entries in a jump list are Windows shell links, parsed by
scripts/windows_lnk.py ([MS-SHLLINK], libyal liblnk).

A jump list is the per-application list of recent, frequent and pinned items
shown on an app's taskbar menu. Automatic destinations
(*.automaticDestinations-ms) are OLE compound files whose numbered streams are
each a shell link. Custom destinations (*.customDestinations-ms) hold the app's
own task and pinned shell links concatenated in one file. The file name is the
application identifier.
"""

import os

try:
    import olefile
except ImportError:
    olefile = None

from scripts.windows_lnk import parse_lnk, parse_destlist, target_path
from scripts.ilapfuncs import artifact_processor, logfunc

_AUTO = ".automaticdestinations-ms"
_CUSTOM = ".customdestinations-ms"

# Streams in an automatic jump list that are metadata, not shell links. DestList
# orders and time-stamps the numbered streams; DestListPropertyStore is skipped.
_NON_LINK_STREAMS = ("destlist", "destlistpropertystore")

# A shell link starts with HeaderSize 0x0000004C then the LinkCLSID.
_LNK_HEADER = b"\x4c\x00\x00\x00" + bytes.fromhex("0114020000000000c000000000000046")
_LNK_CLSID = bytes.fromhex("0114020000000000c000000000000046")

__artifacts_v2__ = {
    "windowsJumpLists": {
        "name": "Jump Lists",
        "description": "Recent, frequent and pinned items per application from Windows "
                       "jump lists, ordered most-recently-used first, with each "
                       "destination's target path, the jump list's own recorded time "
                       "and pin state, the target's recorded timestamps, size, volume "
                       "and the machine the link was made on.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-17",
        "requirements": "olefile (for automatic destinations)",
        "category": "Windows",
        "notes": "Rows from the shell links inside a user's jump list files, read "
                 "from the files named in Source File. Each row is one destination "
                 "shell link. List Type is Automatic for an .automaticDestinations-ms "
                 "file and Custom for a .customDestinations-ms file. App ID is the "
                 "jump list file name, an application identifier, as stored; it is not "
                 "resolved to an application name here. An automatic jump list is an "
                 "OLE compound file whose numbered streams are each a shell link, "
                 "ordered here by its DestList stream. MRU Position is the entry's "
                 "place in the DestList's stored order, 1 first; on the tested images "
                 "the entries are stored in descending order of Entry Recorded (UTC), "
                 "so position 1 is the entry with the most recent recorded time. Entry "
                 "Recorded (UTC) is the Windows FILETIME stored in the DestList entry, "
                 "which the format documentation labels the entry's last modification "
                 "time; it is a jump-list timestamp, not a filesystem timestamp, and "
                 "what user action set it is not established here. Pinned is Yes when "
                 "the DestList entry's pin-status field is 0 or greater and No when it "
                 "is -1, the documented unpinned value. Entry Recorded, MRU Position "
                 "and Pinned are blank for a custom jump list, which has no DestList, "
                 "and for any automatic stream the DestList does not reference. A "
                 "custom jump list holds the application's task and pinned shell links, "
                 "read by scanning for shell-link headers; a jump list entry that is "
                 "not a shell link (a plain task command, for example) is not "
                 "surfaced. Target Path is the local path stored in the link, or the "
                 "network path, or a shell path rebuilt from the link's target id "
                 "list. Target Created, Target Modified and Target Accessed (UTC) are "
                 "the target file's own timestamps recorded inside the link (Windows "
                 "FILETIMEs), blank when the link stores none. Target Size (bytes) is "
                 "the target size the link recorded (0 when none is stored). Drive "
                 "Type, Drive Serial and Volume Label are the volume the target lived "
                 "on, from the link's VolumeID; Drive Type is named from the Windows "
                 "GetDriveType constants and the other two are as stored; all three "
                 "are blank for a network or virtual target. Network Path is the UNC "
                 "path when the target is on a share, blank otherwise. Arguments is "
                 "any command line stored in the link, present for an application "
                 "launch entry and blank for a plain file link. Machine ID is the "
                 "NetBIOS name of the computer where the link was created, blank when "
                 "the link carries no such block. A jump list records that the target "
                 "was available to the application; it does not record who was at the "
                 "keyboard, and the target may since have been moved or deleted. "
                 "Reading automatic jump lists needs the olefile package; when it is "
                 "absent only custom jump lists are read. Format: the shell links "
                 "follow Microsoft [MS-SHLLINK], https://learn.microsoft.com/openspecs/"
                 "windows_protocols/ms-shllink/16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943 ; "
                 "the automatic jump list container and its DestList stream follow "
                 "libyal dtformats Jump lists format, https://github.com/libyal/"
                 "dtformats/blob/4917c9bffc631503c9dbe77dddf14023a572bcef/documentation"
                 "/Jump%20lists%20format.asciidoc",
        "paths": ("*/Microsoft/Windows/[Rr]ecent/[Aa]utomaticDestinations/"
                  "*.[Aa]utomaticDestinations-ms",
                  "*/Microsoft/Windows/[Rr]ecent/[Cc]ustomDestinations/"
                  "*.[Cc]ustomDestinations-ms"),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 71 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 28 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 66 rows",
        },
    },
}


def _app_id(source):
    base = os.path.basename(source)
    for ext in (".automaticDestinations-ms", ".customDestinations-ms"):
        if base.lower().endswith(ext.lower()):
            return base[:-len(ext)]
    return base


def _row(parsed, list_type, app_id, destlist=None):
    return ((destlist['entry_time'] if destlist else ''),
            (destlist['position'] if destlist else ''),
            (('Yes' if destlist['pinned'] else 'No') if destlist else ''),
            parsed.get('target_modified', ''),
            parsed.get('target_created', ''),
            parsed.get('target_accessed', ''),
            list_type, app_id, target_path(parsed),
            parsed.get('target_size', ''), parsed.get('drive_type', ''),
            parsed.get('drive_serial', ''), parsed.get('volume_label', ''),
            parsed.get('network_path', ''), parsed.get('arguments', ''),
            parsed.get('machine_id', ''))


def _automatic_rows(source, app_id):
    """Each numbered stream of the OLE compound file is a shell link. The
    DestList stream stores the entries most-recently-used first with a per-entry
    recorded time and pin status, joined to a numbered stream by its entry
    number (the numbered stream's name is that number in hexadecimal)."""
    rows = []
    handle = olefile.OleFileIO(source)
    try:
        destlist_raw = None
        numbered = {}   # int entry number -> stream name
        other = []      # non-hex-named streams that are not metadata
        for entry in handle.listdir():
            name = "/".join(entry)
            low = name.lower()
            if low in _NON_LINK_STREAMS:
                if low == 'destlist':
                    destlist_raw = handle.openstream(entry).read()
                continue
            try:
                numbered[int(name, 16)] = name
            except ValueError:
                other.append(name)

        def emit(name, destlist):
            parsed = parse_lnk(handle.openstream(name).read())
            if not parsed.get('error') and target_path(parsed):
                rows.append(_row(parsed, 'Automatic', app_id, destlist))

        emitted = set()
        for de in parse_destlist(destlist_raw) if destlist_raw else []:
            name = numbered.get(de['entry_number'])
            if name is not None and name not in emitted:
                emit(name, de)
                emitted.add(name)
        for _, name in sorted(numbered.items()):    # streams DestList did not order
            if name not in emitted:
                emit(name, None)
                emitted.add(name)
        for name in other:
            emit(name, None)
    finally:
        handle.close()
    return rows


def _custom_rows(data, app_id):
    """Shell links concatenated in a custom destinations file, found by header."""
    rows = []
    pos = 0
    while True:
        found = data.find(_LNK_CLSID, pos)
        if found < 0:
            break
        start = found - 4
        if start >= 0 and data[start:found] == b"\x4c\x00\x00\x00":
            parsed = parse_lnk(data[start:])
            if not parsed.get('error') and target_path(parsed):
                rows.append(_row(parsed, 'Custom', app_id))
        pos = found + len(_LNK_CLSID)
    return rows


@artifact_processor
def windowsJumpLists(context):
    data_headers = (('Entry Recorded (UTC)', 'datetime'),
                    'MRU Position', 'Pinned',
                    ('Target Modified (UTC)', 'datetime'),
                    ('Target Created (UTC)', 'datetime'),
                    ('Target Accessed (UTC)', 'datetime'),
                    'List Type', 'App ID', 'Target Path', 'Target Size (bytes)',
                    'Drive Type', 'Drive Serial', 'Volume Label', 'Network Path',
                    'Arguments', 'Machine ID', 'Source File')
    data_list = []
    sources = []
    warned = False
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith((_AUTO, _CUSTOM))]:
        relative_source = context.get_relative_path(source)
        app_id = _app_id(source)
        try:
            if source.lower().endswith(_AUTO):
                if olefile is None:
                    if not warned:
                        logfunc('Jump Lists: the olefile package is not installed; '
                                'automatic destinations are skipped')
                        warned = True
                    continue
                rows = _automatic_rows(source, app_id)
            else:
                with open(source, 'rb') as handle:
                    rows = _custom_rows(handle.read(), app_id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Jump Lists: could not read {relative_source}: {exc}')
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
        if rows:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)
