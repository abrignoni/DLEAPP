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
from scripts.windows_registry import open_hive

# When a file is sent to the Recycle Bin, Windows writes a $I metadata file
# ($Recycle.Bin\<SID>\$Ixxxxxx) that records the file's original path, its size
# and the time it was deleted, alongside a paired $R file that holds the content.
# The <SID> directory names the user whose Recycle Bin held the item; that SID
# resolves to a user profile through the SOFTWARE hive ProfileList.

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_FILETIME_EPOCH_TICKS = 116444736000000000
_PROFILE_LIST = r"Microsoft\Windows NT\CurrentVersion\ProfileList"

__artifacts_v2__ = {
    "recycleBin": {
        "name": "Recycle Bin",
        "description": "Files sent to the Windows Recycle Bin: each item's "
                       "original path, size and deletion time from its $I "
                       "metadata file, with the user whose Recycle Bin held it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-10-30",
        "requirements": "python-registry (only to resolve the user name; the $I files are read without it)",
        "category": "Windows",
        "notes": "Rows from the $I metadata files under $Recycle.Bin, the folder name matched in any letter case, named in "
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
                 "the paired $R file (the same name with $R in place of $I, in the same directory) holds the deleted content and is not parsed here; when it is a folder, Recycle Bin Folder Contents lists the files inside it. A $I file records that an item was sent to the Recycle "
                 "Bin; it does not record who sent it there, and the item may "
                 "since have been restored or its $R content purged while the $I "
                 "remained. A dirty hive, one whose base block's two sequence "
                 "numbers differ, is read after the entries in its .LOG1 and .LOG2 "
                 "transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format "
                 "specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "When no log in the format Windows 8.1 and later write applies, a log in the older format used before Windows 8.1 is applied instead: the first of .LOG1 and .LOG2 whose base block is valid and holds the hive's last-written time has the pages its dirty vector marks written where the vector places them (https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L620-L677, https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L742). On the 16 hives of cfreds_leakage_win7 that carry such a log as .LOG1, each copied, made dirty and given overwritten bytes in every page its log marks for the test, this rebuilt each hive byte for byte, as rla 2026.10.1 did; none of the 54 dirty hives in the 17 corpus images surveyed carries one. A lone .LOG beside a hive is not read. A replay that would give a key an earlier last-written time than the hive already holds is not applied, a check "
                 "added here beyond the specification; the run log names each hive "
                 "replayed, with the sequence numbers applied, and each dirty hive "
                 "read as it is, with the reason. Format: libyal dtformats Windows "
                 "Recycle.Bin file "
                 "formats, https://github.com/libyal/dtformats/blob/"
                 "4917c9bffc631503c9dbe77dddf14023a572bcef/documentation/"
                 "Windows%20Recycle.Bin%20file%20formats.asciidoc",
        "paths": ('*/$[Rr][Ee][Cc][Yy][Cc][Ll][Ee].[Bb][Ii][Nn]/*/$[Ii]*',
                  '*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no $I files present)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 2 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
        },
    },
    "recycleBinFolderContents": {
        "name": "Recycle Bin Folder Contents",
        "description": "Files inside a folder sent to the Recycle Bin: each file's path inside the $R folder, the "
                       "folder's original path and deletion time from its $I file, and the file's size.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-29",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per file inside a $R folder under $Recycle.Bin, the folder name matched in any letter case, named in the report's located-at line. The "
                 "format documentation describes a $R item only as holding the deleted content; on lonewolf_win10 two "
                 "$R items are folders, each with a $I file of the same name, which the existing Recycle Bin artifact "
                 "reports. Path in Folder is the file's path below the $R folder, its separators given as backslashes."
                 " Folder Original Path and Deleted (UTC) are the original path and the deletion FILETIME stored in "
                 "the $I file of the same name with $I in place of $R in the same folder, read as the Recycle Bin "
                 "artifact reads them "
                 "(https://github.com/libyal/dtformats/blob/4917c9bffc631503c9dbe77dddf14023a572bcef/documentation/Windows%20Recycle.Bin%20file%20formats.asciidoc);"
                 " Original Path joins Folder Original Path and Path in Folder. All three are blank when there is no "
                 "such $I file, or when it cannot be read or is not a recognised $I file. Size (bytes) is the size of "
                 "the file as staged. $R Folder is the folder's name and User SID the name of the folder above it. "
                 "Only files are listed: a folder inside a $R folder gives no row of its own, and an empty one none at"
                 " all. A $R file that is not a folder is not listed here and is not matched by this artifact's paths,"
                 " so this artifact does not copy its content into the report. There the two folders, of its five $R "
                 "items, hold 243 files, each one level down, and every row's original path, size and deletion time "
                 "equal those RBCmd 2026.10.1 reports for the same Recycle Bin folder, to the whole second it writes; "
                 "the other images tested hold no $R folder. A row records that the file was inside a folder sent to "
                 "the Recycle Bin when the image was made; it does not show who deleted it.",
        "paths": ('*/$[Rr][Ee][Cc][Yy][Cc][Ll][Ee].[Bb][Ii][Nn]/*/$[Rr]*/*',
                  '*/$[Rr][Ee][Cc][Yy][Cc][Ll][Ee].[Bb][Ii][Nn]/*/$[Ii]*'),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "lonewolf_win10": "Windows 10 Education build 16299 | 243 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
        },
    },
    "recycleBinInfo2": {
        "name": "Recycle Bin (INFO2)",
        "description": "Files sent to the Recycle Bin on Windows that keeps a RECYCLER folder: each entry's original path, "
                       "deletion time, index and drive number from the INFO2 file under RECYCLER, with the "
                       "user whose folder held it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "python-registry (only to resolve the user name; INFO2 is read without it)",
        "category": "Windows",
        "notes": "Rows from the INFO2 files in the per-user folders under RECYCLER, the folder name matched "
                 "in any letter case, named in Source File. Each row is one file entry. The layout is libyal "
                 "dtformats' 'Windows Recycler file formats' "
                 "(https://github.com/libyal/dtformats/blob/308ce8c38df2eb95a71b6e832b3f9803f0c4b169/documentation/Windows%20Recycler%20file%20formats.asciidoc#L90-L131): "
                 "a 20-byte header whose fourth value is the entry size, 800 bytes on Windows 2000 and later and "
                 "280 on Windows Me, then entries of that size. A file whose entry size is neither, or whose "
                 "length past the header is not a whole number of entries, is named in the run log and not "
                 "read. Deleted (UTC) is the entry's deletion FILETIME at offset 268, cut to whole "
                 "microseconds. Original Path is the UTF-16 name at offset 280, or in a 280-byte entry the "
                 "ASCII name at offset 0 read as Latin-1, since the code page is not stored; no tested file "
                 "has 280-byte entries. Index is the value the format document calls the index within the INFO2 "
                 "file, and Drive Number (as stored) the value it calls the drive number. Size (as stored) is "
                 "the value at offset 276, which the document marks as unknown, possibly the original file size. "
                 "Recycled File is the file in the same folder named D, a letter, the entry's index and the "
                 "original name's extension, when exactly one such file is there; that naming is not in the "
                 "cited document. User SID is the name of the INFO2 file's parent folder, and User is that SID "
                 "resolved through the SOFTWARE hive ProfileList as in Recycle Bin. A row records an entry the "
                 "INFO2 held when the image was made; it does not record who sent the file there, and whether an "
                 "entry marks a file since restored or emptied is not established here. Tested on "
                 "cfreds_hacking_case_winxp: one INFO2 with 4 entries of 800 bytes, its header's second value 4; "
                 "the UTF-16 and ASCII names were equal on all 4; Drive Number was 2 on all 4, each path beginning "
                 "C:; all 4 were in one SID folder, so User and User SID held one value each; each entry had exactly one Recycled File, named D, c and its index, whose size was below "
                 "Size by less than 512, Size being a whole multiple of 512 on all 4. RBCmd 2026.10.1 read the same "
                 "file and gave the same index, drive number, size, original name and deletion time, to the "
                 "microsecond, for all 4, and reported none of them as removed.",
        "paths": ('*/[Rr][Ee][Cc][Yy][Cc][Ll][Ee][Rr]/*/[Ii][Nn][Ff][Oo]2',
                  '*/[Rr][Ee][Cc][Yy][Cc][Ll][Ee][Rr]/*/[Dd]*',
                  '*/[Ww][Ii][Nn][Dd][Oo][Ww][Ss]/[Ss][Yy][Ss][Tt][Ee][Mm]32/[Cc][Oo][Nn][Ff][Ii][Gg]/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee]',
                  '*/[Ww][Ii][Nn][Dd][Oo][Ww][Ss]/[Ss][Yy][Ss][Tt][Ee][Mm]32/[Cc][Oo][Nn][Ff][Ii][Gg]/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 4 rows",
        },
    },
}


def _utc_from_filetime(value):
    if value in (None, "", 0):
        return ""
    try:
        # Whole 100-nanosecond intervals cut to microseconds; a float division rounds to the nearest
        # microsecond and can read one microsecond later than the cut value on FILETIMEs of this century.
        return _UNIX_EPOCH + timedelta(microseconds=(int(value) - _FILETIME_EPOCH_TICKS) // 10)
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
        profiles = open_hive(software_hive).open(_PROFILE_LIST)
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


def _recycle_parts(path):
    """(SID folder, $R name, path inside the $R folder) of a file inside a $R folder, or None."""
    parts = path.replace('\\', '/').split('/')
    lowered = [part.lower() for part in parts]
    if '$recycle.bin' not in lowered:
        return None
    index = len(lowered) - 1 - lowered[::-1].index('$recycle.bin')
    rest = parts[index + 1:]
    if len(rest) < 3 or not rest[1].lower().startswith('$r'):
        return None
    return '/'.join(parts[:index + 2]), rest[1], rest[2:]


@artifact_processor
def recycleBinFolderContents(context):
    data_headers = (('Deleted (UTC)', 'datetime'), 'Original Path', 'Path in Folder', 'Size (bytes)',
                    'Folder Original Path', '$R Folder', 'User SID')
    files = [str(f) for f in context.get_files_found()]
    i_files = {}
    for source in files:
        name = os.path.basename(source)
        if name.lower().startswith('$i') and os.path.isfile(source):
            i_files[(os.path.dirname(source), name[2:].lower())] = source
    data_list = []
    sources = []
    parsed_i = {}
    for source in files:
        parts = _recycle_parts(source)
        if parts is None or not os.path.isfile(source):
            continue
        sid_folder, r_name, inside = parts
        i_source = i_files.get((sid_folder, r_name[2:].lower()))
        if i_source and i_source not in parsed_i:
            try:
                with open(i_source, 'rb') as handle:
                    parsed_i[i_source] = _parse_i_file(handle.read())
            except OSError as exc:
                logfunc(f'Recycle Bin Folder Contents: could not read {context.get_relative_path(i_source)}: {exc}')
                parsed_i[i_source] = None
            if parsed_i[i_source] is None:
                logfunc(f'Recycle Bin Folder Contents: {context.get_relative_path(i_source)} is not a recognised '
                        '$I file')
            elif i_source not in sources:
                sources.append(i_source)
        parsed = parsed_i.get(i_source) if i_source else None
        deleted, folder_path = (_utc_from_filetime(parsed[1]), parsed[2]) if parsed else ('', '')
        inside_path = '\\'.join(inside)
        original = f"{folder_path.rstrip(chr(92))}\\{inside_path}" if folder_path else ''
        data_list.append((deleted, original, inside_path, os.path.getsize(source), folder_path, r_name,
                          os.path.basename(sid_folder)))
        sources.append(source)
    return data_headers, data_list, "\n".join(sources)


_INFO2_ENTRY_SIZES = (280, 800)


def parse_info2(data):
    """(entry size, header entry count, [(index, drive, deletion FILETIME, size, name)]) or None
    for a file whose header or length does not fit the layout."""
    if len(data) < 20:
        return None
    _, count, _, entry_size, _ = struct.unpack_from("<IIIII", data, 0)
    if entry_size not in _INFO2_ENTRY_SIZES or (len(data) - 20) % entry_size:
        return None
    entries = []
    for offset in range(20, len(data), entry_size):
        entry = data[offset:offset + entry_size]
        index, drive, filetime, size = struct.unpack_from("<IIQI", entry, 260)
        if entry_size > 280:
            name = entry[280:800].decode("utf-16-le", "replace").split("\x00", 1)[0]
        else:
            name = entry[:260].split(b"\x00", 1)[0].decode("latin-1")
        entries.append((index, drive, filetime, size, name))
    return entry_size, count, entries


def _recycled_file(folder_files, index, name):
    """The one file in the folder named D, a letter, the index and the name's extension, or ''."""
    extension = os.path.splitext(name.replace("\\", "/"))[1].lower()
    wanted = [f for f in folder_files
              if len(f) > 2 and f[0] in "Dd" and f[1].isalpha()
              and os.path.splitext(f)[0][2:] == str(index) and os.path.splitext(f)[1].lower() == extension]
    return wanted[0] if len(wanted) == 1 else ''


@artifact_processor
def recycleBinInfo2(context):
    data_headers = (('Deleted (UTC)', 'datetime'), 'Original Path', 'Size (as stored)', 'Index',
                    'Drive Number (as stored)', 'Recycled File', 'User', 'User SID', 'Source File')
    data_list = []
    sources = []
    files = [str(f) for f in context.get_files_found()]

    users = {}
    if Registry is not None:
        for source in files:
            if os.path.basename(source).upper() == 'SOFTWARE':
                users.update(_profile_users(source))

    by_folder = {}
    for source in files:
        if os.path.isfile(source):
            by_folder.setdefault(os.path.dirname(source), []).append(os.path.basename(source))

    for source in files:
        if os.path.basename(source).upper() != 'INFO2' or not os.path.isfile(source):
            continue
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                parsed = parse_info2(handle.read())
        except OSError as exc:
            logfunc(f'Recycle Bin (INFO2): could not read {relative_source}: {exc}')
            continue
        if parsed is None:
            logfunc(f'Recycle Bin (INFO2): {relative_source} does not fit the INFO2 layout and was not read')
            continue
        _entry_size, _count, entries = parsed
        sid = os.path.basename(os.path.dirname(source))
        siblings = by_folder.get(os.path.dirname(source), [])
        for index, drive, filetime, size, name in entries:
            data_list.append((_utc_from_filetime(filetime), name, size, index, drive,
                              _recycled_file(siblings, index, name), users.get(sid, ''), sid, relative_source))
        sources.append(source)

    return data_headers, data_list, "\n".join(sources)
