"""Windows AppCompatCache (Shimcache) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Registry.AppCompatCache artifact;
this reads the SYSTEM hive's on-disk structure directly with python-registry and
parses the AppCompatCache binary value itself.

AppCompatCache, also called Shimcache, is written by the application-compatibility
engine. Each entry records a file path and the file's last-modification time. On
Windows 10 and 11 the value uses the "10ts" entry format: a 4-byte header offset
to the first entry, then entries of signature "10ts", a 4-byte unknown, a 4-byte
entry size, a 2-byte path length, the UTF-16-LE path, and an 8-byte little-endian
FILETIME.
"""

import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

_KEY = "Control\\Session Manager\\AppCompatCache"
_VALUE = "AppCompatCache"
_ENTRY_SIGNATURE = b"10ts"

__artifacts_v2__ = {
    "appCompatCache": {
        "name": "AppCompatCache (Shimcache)",
        "description": "File paths and file modification times cached by the "
                       "Windows application-compatibility engine (Shimcache), "
                       "parsed from the AppCompatCache value in the SYSTEM hive.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SYSTEM hive, named in Source File. Each row is one "
                 "AppCompatCache entry under a control set's Control\\Session "
                 "Manager\\AppCompatCache value; every ControlSet00N in the hive is "
                 "read. Only the Windows 10 and 11 \"10ts\" entry format is parsed; "
                 "a value in another format is skipped with a note in the run log. "
                 "Path is the entry's file path as stored. File Modified (UTC) is "
                 "the entry's little-endian FILETIME, which is the file's own last "
                 "modification time recorded when the file was cached, not a time "
                 "the program ran; an entry whose time is 0 or out of range is shown "
                 "blank. Some entries, for packaged (MSIX or UWP) apps, store a "
                 "tab-separated package identity (flags, architecture, package "
                 "family name and publisher) in place of a file path, and on the "
                 "tested images these were the entries carrying no File Modified "
                 "time. Cache Position is the entry's zero-based index in the "
                 "value; the engine writes newer activity toward the front, so a "
                 "lower position was cached more recently, but the position is an "
                 "ordering, not a timestamp. An AppCompatCache entry records that "
                 "the file was present and seen by the compatibility engine; on "
                 "Windows 10 and 11 it does not reliably establish that the program "
                 "was executed, so no execution indicator is reported here. Reading "
                 "the hive needs the python-registry package; its .LOG1/.LOG2 "
                 "transaction logs are not replayed. Format: Velocidex, "
                 "Windows.Registry.AppCompatCache, https://github.com/Velocidex/"
                 "velociraptor/blob/master/artifacts/definitions/Windows/Registry/"
                 "AppCompatCache.yaml",
        "paths": ("*/Windows/System32/config/SYSTEM",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 937 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 372 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 406 rows",
        },
    },
}


def _filetime_datetime(value):
    """A little-endian Windows FILETIME: 100-ns intervals since 1601-01-01 UTC."""
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _parse_win10(blob):
    """Yield (position, path, filetime_int) for a Windows 10/11 '10ts' cache."""
    if len(blob) < 4:
        return
    start = struct.unpack_from("<I", blob, 0)[0]
    if start + 4 > len(blob) or blob[start:start + 4] != _ENTRY_SIGNATURE:
        raise ValueError("not the Windows 10/11 '10ts' AppCompatCache format")
    offset = start
    position = 0
    while offset + 14 <= len(blob):
        if blob[offset:offset + 4] != _ENTRY_SIGNATURE:
            break
        entry_size = struct.unpack_from("<I", blob, offset + 8)[0]
        if entry_size <= 0:
            break
        path_len = struct.unpack_from("<H", blob, offset + 12)[0]
        path_start = offset + 14
        path_end = path_start + path_len
        time_end = path_end + 8
        if time_end > len(blob):
            break
        path = blob[path_start:path_end].decode("utf-16-le", "replace")
        filetime = struct.unpack_from("<Q", blob, path_end)[0]
        yield position, path, filetime
        position += 1
        offset += 12 + entry_size


def _control_sets(reg):
    try:
        root = reg.root()
    except Exception:  # pylint: disable=broad-exception-caught
        return []
    return [k.name() for k in root.subkeys()
            if k.name().lower().startswith("controlset")]


def _entries(reg, relative_source):
    """Yield (position, path, filetime) for every readable AppCompatCache."""
    for control_set in _control_sets(reg):
        try:
            key = reg.open("%s\\%s" % (control_set, _KEY))
        except Registry.RegistryKeyNotFoundException:
            continue
        try:
            blob = key.value(_VALUE).value()
        except Registry.RegistryValueNotFoundException:
            continue
        try:
            for row in _parse_win10(blob):
                yield row
        except ValueError as exc:
            logfunc(f"AppCompatCache: {control_set} value skipped ({exc}) in {relative_source}")


@artifact_processor
def appCompatCache(context):
    data_headers = (('File Modified (UTC)', 'datetime'), 'Path', 'Cache Position',
                    'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('AppCompatCache: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('system')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            reg = Registry.Registry(source)
            for position, path, filetime in _entries(reg, relative_source):
                data_list.append((_filetime_datetime(filetime), path, position,
                                  relative_source))
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'AppCompatCache: could not read {relative_source}: {exc}')
            continue
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
