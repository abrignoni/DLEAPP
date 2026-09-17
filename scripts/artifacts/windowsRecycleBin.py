"""Windows Recycle Bin ($I) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange artifact that reads the Recycle Bin; the
implementation reads the $I file's on-disk structure directly (libyal dtformats
"Windows Recycle.Bin file formats") and is not ported from that artifact.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# When a file is sent to the Recycle Bin, Windows writes a $I metadata file
# ($Recycle.Bin\<SID>\$Ixxxxxx) that records the file's original path, its size
# and the time it was deleted, alongside a paired $R file that holds the content.
# The <SID> directory names the user whose Recycle Bin held the item; that SID
# resolves to a user profile through the SOFTWARE hive ProfileList.

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_FILETIME_EPOCH_TICKS = 116444736000000000
_TICKS_PER_SECOND = 10_000_000
_PROFILE_LIST = r"Microsoft\Windows NT\CurrentVersion\ProfileList"

__artifacts_v2__ = {
    "recycleBin": {
        "name": "Recycle Bin",
        "description": "Files sent to the Windows Recycle Bin: each item's "
                       "original path, size and deletion time from its $I "
                       "metadata file, with the user whose Recycle Bin held it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry (only to resolve the user name; the $I files are read without it)",
        "category": "Windows",
        "notes": "Rows from the $I metadata files under $Recycle.Bin, named in "
                 "Source File. Each row is one item recorded as sent to the "
                 "Recycle Bin. Deleted (UTC) is the Windows FILETIME the $I "
                 "stores at offset 16. Original Path is the item's original "
                 "location as stored in the $I (the format documentation calls "
                 "it the original filename; it holds the full path). Deleted "
                 "Size (bytes) is the original file size the $I recorded at "
                 "offset 8. User SID is the name of the $I file's parent "
                 "directory, which is the SID of the account whose Recycle Bin "
                 "held the item; User is that SID resolved to the last path "
                 "component of its ProfileImagePath in the SOFTWARE hive "
                 "ProfileList, and is blank when no SOFTWARE hive was read or the "
                 "SID is not listed there. Both $I format versions are parsed: "
                 "version 1 (Windows Vista and later) stores the path as a "
                 "fixed-length string, version 2 (Windows 10 and later) prefixes "
                 "it with a character count. Source File is the $I metadata file; "
                 "the paired $R file (the same name with $R in place of $I, in "
                 "the same directory) holds the deleted content and is not parsed "
                 "here. A $I file records that an item was sent to the Recycle "
                 "Bin; it does not record who sent it there, and the item may "
                 "since have been restored or its $R content purged while the $I "
                 "remained. Format: libyal dtformats Windows Recycle.Bin file "
                 "formats, https://github.com/libyal/dtformats/blob/"
                 "4917c9bffc631503c9dbe77dddf14023a572bcef/documentation/"
                 "Windows%20Recycle.Bin%20file%20formats.asciidoc",
        "paths": (
            '*/$[Rr]ecycle.[Bb]in/*/$[Ii]*',
            '*/Windows/System32/config/SOFTWARE',
        ),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no $I files present)",
        },
    },
}


def _utc_from_filetime(value):
    if value in (None, "", 0):
        return ""
    try:
        seconds = (int(value) - _FILETIME_EPOCH_TICKS) / _TICKS_PER_SECOND
        return _UNIX_EPOCH + timedelta(seconds=seconds)
    except (OverflowError, TypeError, ValueError):
        return ""


def _parse_i_file(data):
    """Parse $I bytes. Returns (size, deletion FILETIME, original path) or None
    for a file too short or an unrecognised format version."""
    if len(data) < 24:
        return None
    version, size, filetime = struct.unpack_from("<QQQ", data, 0)
    if version == 1:
        raw = data[24:]
    elif version == 2:
        if len(data) < 28:
            return None
        char_count = struct.unpack_from("<I", data, 24)[0]
        raw = data[28:28 + char_count * 2]
    else:
        return None
    if len(raw) % 2:
        raw = raw[:-1]
    path = raw.decode("utf-16-le", "replace").split("\x00", 1)[0]
    return size, filetime, path


def _profile_users(software_hive):
    """SID -> user name from the SOFTWARE hive ProfileList (the last component
    of each profile's ProfileImagePath)."""
    users = {}
    try:
        profiles = Registry.Registry(software_hive).open(_PROFILE_LIST)
    except Exception:  # pylint: disable=broad-exception-caught
        return users
    for profile in profiles.subkeys():
        try:
            image_path = profile.value("ProfileImagePath").value()
        except Registry.RegistryValueNotFoundException:
            continue
        if image_path:
            users[profile.name()] = image_path.replace("/", "\\").rstrip("\\").split("\\")[-1]
    return users


@artifact_processor
def recycleBin(context):
    data_headers = (('Deleted (UTC)', 'datetime'), 'Original Path',
                    'Deleted Size (bytes)', 'User', 'User SID', 'Source File')
    data_list = []
    sources = []
    files = [str(f) for f in context.get_files_found()]

    users = {}
    if Registry is not None:
        for source in files:
            if os.path.basename(source).upper() == 'SOFTWARE':
                users.update(_profile_users(source))

    for source in files:
        if not os.path.basename(source).lower().startswith('$i'):
            continue
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                parsed = _parse_i_file(handle.read())
        except OSError as exc:
            logfunc(f'Recycle Bin: could not read {relative_source}: {exc}')
            continue
        if parsed is None:
            logfunc(f'Recycle Bin: {relative_source} is not a recognised $I file')
            continue
        size, filetime, path = parsed
        sid = os.path.basename(os.path.dirname(source))
        data_list.append((_utc_from_filetime(filetime), path, size,
                          users.get(sid, ''), sid, relative_source))
        sources.append(source)

    return data_headers, data_list, "\n".join(sources)
