"""DPAPI master key file parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Lists the master key files of the Windows Protect folders (files named by a GUID), each with the times the image
records for it, whether the folder's Preferred file names it and the time that file stores, and the header fields the file stores:
version, flags, the iteration count and algorithm IDs of its first section and the sizes of its four sections. No key
is decrypted. How the layout was established is in the notes.
"""

import os
import re
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'DPAPI Master Key Files'
_GUID_NAME = re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
_HEADER = 128
_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)


__artifacts_v2__ = {
    "dpapiMasterKeyFiles": {
        "name": "DPAPI Master Key Files",
        "description": "DPAPI master key files of the Windows Protect folders (files named by a GUID), each with the "
                       "times the image records for it, whether the folder's Preferred file names it and the header "
                       "fields the file stores. No key is decrypted.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads the files the paths match in the Windows Protect folders (AppData\\Roaming\\Microsoft\\Protect "
                 "of a profile and Windows\\System32\\Microsoft\\Protect) and reports one row per file whose name is a "
                 "GUID, a DPAPI master key file. The Preferred file of a folder is read for the two Preferred "
                 "columns. No key is decrypted, and no other file of the folders is read; the tested folders also "
                 "hold files named CREDHIST, SYNCHIST, Diagnostic and Diagnostic.log and files whose names start "
                 "BK-. No Microsoft description of these files was found, so the layout was checked against the "
                 "files themselves. On all 26 tested master key files, bytes 12 to 83 hold the file's own name as "
                 "UTF-16 text, bytes 4 to 11 and 84 to 91 are zero, and the four 8-byte numbers at bytes 96 to 127 "
                 "plus the 128 bytes before them add up to the file's size; they are shown as Section Sizes, in the "
                 "order stored. The field names are those of impacket's reader of the format "
                 "(https://github.com/fortra/impacket/blob/1875828d0f2e987cd89c1bcb45f843708981a199/impacket/dpapi.py#L232-L245 "
                 "and "
                 "https://github.com/fortra/impacket/blob/1875828d0f2e987cd89c1bcb45f843708981a199/impacket/dpapi.py#L259-L266): "
                 "Version is bytes 0 to 3, Flags bytes 92 to 95, the four sections are MasterKey, BackupKey, "
                 "CredHist and DomainKey, and Iteration Count, Hash Algorithm ID and Cipher Algorithm ID are bytes "
                 "20 to 31 of the first section (MasterKeyIterationCount, HashAlgo and CryptAlgo). What the count "
                 "and the two algorithms are used for comes from that reader and was not tested here. Hash Algorithm "
                 "ID and Cipher Algorithm ID are shown as 0x and eight hexadecimal digits. Microsoft's ALG_ID page "
                 "lists the four values the tested files hold: 0x0000800e is CALG_SHA_512 and 0x00006610 "
                 "CALG_AES_256 (22 files), 0x00008009 is CALG_HMAC and 0x00006603 CALG_3DES (4 files) "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/SecCrypto/alg-id.md?plain=1#L264-L265, "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/SecCrypto/alg-id.md?plain=1#L64-L65, "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/SecCrypto/alg-id.md?plain=1#L149-L150 "
                 "and "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/SecCrypto/alg-id.md?plain=1#L39-L40). "
                 "Tested on four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 7, 5, 5 and 9 rows in that "
                 "order; the two captures of a Windows 11 build 26200 machine hold no Protect folder. Version is 2 "
                 "on every tested file. Flags is 6 on the 17 files of Windows/System32/Microsoft/Protect/S-1-5-18 "
                 "and its User subfolder, 5 on 5 files of user profiles and 0 on the other 4, which are the 4 files "
                 "with a fourth section (Section Sizes 136, 104, 0, 372); the other 22 have Section Sizes 176, 144, "
                 "20, 0. Those 4 files are in the 3 folders, all on szechuan_win10, that also hold a file whose name "
                 "starts BK-. Iteration Count is 8000 on 21 files, 18000 on those 4 and 1 on 1 file of "
                 "pc_mus_001_win11. What the Flags numbers mean is not established. Preferred is Yes when the "
                 "Preferred file of the same folder names the row's GUID, No when it names another and blank when "
                 "the folder has no Preferred file of at least 24 bytes. A Preferred file's first 16 bytes are read "
                 "as a GUID and its next 8 as a FILETIME, shown as Preferred File Time (UTC) on the Yes row. The 15 "
                 "tested Preferred files are 24 bytes each; each names a master key file of its folder, each time "
                 "the one with the latest Created (UTC), and its time is that file's created time plus 90 days to "
                 "within 0.032 seconds. So 15 rows are Yes and 11 No. What Windows does when that time passes is not "
                 "sourced here. Created (UTC) and Modified (UTC) are the created and modified times the tool's raw "
                 "image reader reports for the file; they are blank for a folder or archive input, whose copy's "
                 "times are not the evidence's (that input was exercised with a unit test only). Modified (UTC) "
                 "equals Created (UTC) on 14 of the 26 files and is later on 12. For the 21 files that have a 'DPAPI "
                 "created Master key.' row in the DPAPI Events artifact (7, 5 and 9; pc_mus_001_win11 has none) "
                 "Created (UTC) is within 0.062 seconds of that row. Master Key GUID is the file's name as the image "
                 "spells it, lower case on every tested file. Folder is the file's folder in the extraction: 9 "
                 "tested files are in Windows/System32/Microsoft/Protect/S-1-5-18, 8 in its User subfolder and 9 in "
                 "a folder named by a SID under AppData/Roaming/Microsoft/Protect of a user profile. Rows are in "
                 "path order. Version held one value, 2, on every tested image. Hash Algorithm ID, Cipher Algorithm "
                 "ID and Section Sizes held one value each on af_case2_win10, lonewolf_win10 and pc_mus_001_win11, "
                 "and Iteration Count held one value, 8000, on af_case2_win10 and lonewolf_win10. A file shorter "
                 "than 128 bytes gets a row with the header fields blank. A file whose stored name is not its name, "
                 "or whose sizes do not add up, is reported as read. Both are named in the run log. Iteration Count "
                 "and the two algorithm IDs are blank when the first section is under 32 bytes or the file ends "
                 "before them. No tested file was any of these (unit tests use constructed files).",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 7 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 5 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 9 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/AppData/Roaming/Microsoft/Protect/*", "*/Windows/System32/Microsoft/Protect/*"),
        "output_types": ["standard"],
        "artifact_icon": "key",
    },
}


def _instant(value):
    """A FileInfo time (seconds since 1970, UTC) as an aware datetime, or ''."""
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def guid_text(raw):
    """Sixteen stored bytes as the GUID text Windows writes for them, lower case."""
    first, second, third = struct.unpack_from('<IHH', raw, 0)
    return f'{first:08x}-{second:04x}-{third:04x}-{raw[8:10].hex()}-{raw[10:16].hex()}'


def preferred_key(raw):
    """(GUID, time) a Preferred file stores, or None when it is shorter than its 24 bytes."""
    if len(raw) < 24:
        return None
    ticks = struct.unpack_from('<Q', raw, 16)[0]
    try:
        stored = _FILETIME_ZERO + timedelta(microseconds=ticks // 10)
    except OverflowError:
        stored = ''
    return guid_text(raw), stored


def key_fields(raw, name):
    """((version, flags, count, hash ID, cipher ID, section sizes), problem) of a master key file.

    The fields are '' where the file is too short to hold them; problem says what did not fit, or ''.
    """
    if len(raw) < _HEADER:
        return ('',) * 6, 'is shorter than the 128 byte header'
    version = struct.unpack_from('<I', raw, 0)[0]
    flags = struct.unpack_from('<I', raw, 92)[0]
    sizes = struct.unpack_from('<4Q', raw, 96)
    problem = ''
    if raw[12:84].decode('utf-16-le', errors='replace').rstrip('\x00').lower() != name.lower():
        problem = 'stores a GUID that is not its name'
    elif _HEADER + sum(sizes) != len(raw):
        problem = 'stores section sizes that do not add up to its size'
    count = hash_id = cipher_id = ''
    if sizes[0] >= 32 and _HEADER + 32 <= len(raw):
        count, hash_alg, cipher_alg = struct.unpack_from('<III', raw, _HEADER + 20)
        hash_id, cipher_id = f'0x{hash_alg:08x}', f'0x{cipher_alg:08x}'
    return (version, flags, count, hash_id, cipher_id, ', '.join(str(size) for size in sizes)), problem


@artifact_processor
def dpapiMasterKeyFiles(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), ('Preferred File Time (UTC)', 'datetime'),
                    'Master Key GUID', 'Folder', 'Preferred', 'Version', 'Flags', 'Iteration Count', 'Hash Algorithm ID',
                    'Cipher Algorithm ID', 'Section Sizes')
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    # Only a disk image gives the evidence's own times; a folder or archive gives the times of the copy.
    from_image = hasattr(seeker, 'stream_list')
    files = [path for path in dict.fromkeys(str(p) for p in context.get_files_found()) if not os.path.isdir(path)]
    contents, sources = {}, []
    for path in sorted(files):
        name = os.path.basename(path)
        if name.lower() != 'preferred' and not _GUID_NAME.match(name):
            continue
        try:
            with open(path, 'rb') as handle:
                contents[path] = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {context.get_relative_path(path)}: {type(exc).__name__}')
            continue
        sources.append(path)
    preferred = {}
    for path, raw in contents.items():
        if os.path.basename(path).lower() == 'preferred':
            named = preferred_key(raw)
            if named is None:
                logfunc(f'{_LABEL}: {context.get_relative_path(path)} is shorter than 24 bytes and was not used')
            else:
                preferred[os.path.dirname(path)] = named
    data_list = []
    for path, raw in contents.items():
        name = os.path.basename(path)
        if name.lower() == 'preferred':
            continue
        relative = context.get_relative_path(path)
        fields, problem = key_fields(raw, name)
        if problem:
            logfunc(f'{_LABEL}: {relative} {problem}')
        info = infos.get(path)
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        named = preferred.get(os.path.dirname(path))
        chosen = '' if named is None else 'Yes' if named[0] == name.lower() else 'No'
        stored = named[1] if chosen == 'Yes' else ''
        folder = os.path.dirname(relative.replace('\\', '/'))
        data_list.append((created, modified, stored, name, folder, chosen, *fields))
    return data_headers, data_list, '\n'.join(sources)
