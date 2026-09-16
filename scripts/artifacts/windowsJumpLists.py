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

from scripts.windows_lnk import parse_lnk, target_path
from scripts.ilapfuncs import artifact_processor, logfunc

_AUTO = ".automaticdestinations-ms"
_CUSTOM = ".customdestinations-ms"

# Streams in an automatic jump list that are metadata, not shell links.
_NON_LINK_STREAMS = ("destlist", "destlistpropertystore")

# A shell link starts with HeaderSize 0x0000004C then the LinkCLSID.
_LNK_HEADER = b"\x4c\x00\x00\x00" + bytes.fromhex("0114020000000000c000000000000046")
_LNK_CLSID = bytes.fromhex("0114020000000000c000000000000046")

__artifacts_v2__ = {
    "windowsJumpLists": {
        "name": "Jump Lists",
        "description": "Recent, frequent and pinned items per application from Windows "
                       "jump lists, with each destination's target path, recorded "
                       "timestamps, size, volume and the machine the link was made on.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "olefile (for automatic destinations)",
        "category": "Windows",
        "notes": "Rows from the shell links inside a user's jump list files, read "
                 "from the files named in Source File. Each row is one destination "
                 "shell link. List Type is Automatic for an .automaticDestinations-ms "
                 "file and Custom for a .customDestinations-ms file. App ID is the "
                 "jump list file name, an application identifier, as stored; it is not "
                 "resolved to an application name here. An automatic jump list is an "
                 "OLE compound file whose numbered streams are each a shell link; its "
                 "DestList stream, which records the entries' most-recently-used order "
                 "and a per-entry last-access time and host name, is not parsed here, "
                 "so rows are not ordered by recency and the times shown are the "
                 "target file's own recorded times rather than an access time. A "
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
                 "absent only custom jump lists are read. Format: Microsoft "
                 "[MS-SHLLINK], https://learn.microsoft.com/openspecs/windows_protocols"
                 "/ms-shllink/16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943 ; and libyal liblnk "
                 "Jump List format, https://github.com/libyal/liblnk/blob/main/"
                 "documentation/Jump%20lists%20format.asciidoc",
        "paths": ("*/Microsoft/Windows/[Rr]ecent/[Aa]utomaticDestinations/"
                  "*.[Aa]utomaticDestinations-ms",
                  "*/Microsoft/Windows/[Rr]ecent/[Cc]ustomDestinations/"
                  "*.[Cc]ustomDestinations-ms"),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 71 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 28 rows",
        },
    },
}


def _app_id(source):
    base = os.path.basename(source)
    for ext in (".automaticDestinations-ms", ".customDestinations-ms"):
        if base.lower().endswith(ext.lower()):
            return base[:-len(ext)]
    return base


def _row(parsed, list_type, app_id):
    return (parsed.get('target_modified', ''),
            parsed.get('target_created', ''),
            parsed.get('target_accessed', ''),
            list_type, app_id, target_path(parsed),
            parsed.get('target_size', ''), parsed.get('drive_type', ''),
            parsed.get('drive_serial', ''), parsed.get('volume_label', ''),
            parsed.get('network_path', ''), parsed.get('arguments', ''),
            parsed.get('machine_id', ''))


def _automatic_rows(source, app_id):
    """Each numbered stream of the OLE compound file is a shell link."""
    rows = []
    handle = olefile.OleFileIO(source)
    try:
        for entry in handle.listdir():
            name = "/".join(entry)
            if name.lower() in _NON_LINK_STREAMS:
                continue
            parsed = parse_lnk(handle.openstream(entry).read())
            if not parsed.get('error') and target_path(parsed):
                rows.append(_row(parsed, 'Automatic', app_id))
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
    data_headers = (('Target Modified (UTC)', 'datetime'),
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
