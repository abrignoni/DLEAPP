"""Microsoft Defender Antivirus History Store parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the files under ProgramData\\Microsoft\\Windows Defender\\Scans\\History\\Store\\,
one row per file. The layout is the one mpdbx documents (see the notes); the RC4 key is
the one scripts/mpenginedb.py holds.
"""

import os
import re
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.mpenginedb import KEY, rc4_keystream
from scripts.windows_defender_history import filetime_utc

_LABEL = 'Microsoft Defender History Store'
_STORE_FOLDER = '/programdata/microsoft/windows defender/scans/history/store/'
_PERSIST_ID = re.compile(r'^[0-9a-fA-F]{32}$')
_PROCESS_START = re.compile(r'^pid:(\d{1,10}),ProcessStart:(\d{1,20})$')

_HEADER = 0x3C
_MAGIC_ONE = 0x01C5E8DB
_MAGIC_TWO = 0x02C5E8DB
_MAX_FILE = 16 * 1024 * 1024

_U32, _U64, _U8, _TEXT, _FIXED8 = 3, 4, 5, 6, 9

# Property names given a column of their own; every other property goes to the last column.
_OWN = {
    'CONTEXT_DATA_FILEPATH': 'path', 'CONTEXT_DATA_FILENAME': 'name',
    'CONTEXT_DATA_PROCESSNAME': 'process', 'CONTEXT_DATA_PROCESSDEVICEPATH': 'process_path',
    'CONTEXT_DATA_PROCESS_ID': 'pid', 'CONTEXT_DATA_PROCESS_PPID': 'ppid',
    'CONTEXT_DATA_SCANREASON': 'reason', 'CONTEXT_DATA_NEWLYCREATEDHINT': 'new',
    'CONTEXT_DATA_OPEN_CREATEPROCESS_HINT': 'open', 'CONTEXT_DATA_HAS_MOTW_ADS': 'motw',
    'CONTEXT_DATA_DESIREDACCESS': 'access', 'CONTEXT_DATA_DEVICE_CHARACTERISTICS': 'device',
}

__artifacts_v2__ = {
    "defenderHistoryStore": {
        "name": "Microsoft Defender History Store",
        "description": "Microsoft Defender Antivirus History Store files, one row per file: "
                       "the scanned file's location and name, the process that acted on it "
                       "(name, location, process ID and start time where stored), and the "
                       "other properties Defender recorded in the file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": "The Store files read here are named by a 32-digit hexadecimal ID (12 of 12 on "
                 "the images in sample_data); a file with any other name is not read. "
                 "Its layout and RC4 scheme are those mpdbx documents in docs/design.md at "
                 "commit 40f926f05021d878207cd635451c00166b1132ed "
                 "(https://github.com/Mihir-Choudhary/mpdbx/blob/40f926f05021d878207cd635451c00166b1132ed/docs/design.md): "
                 "the first 60 bytes are RC4-encrypted and hold two magic values and the "
                 "lengths of two sections, each section is RC4-encrypted with a fresh keystream, "
                 "and the second holds named, typed properties. The key is the one "
                 "scripts/mpenginedb.py holds for mpenginedb.db. Measured on 12 files (see "
                 "sample_data), all 12 open with the two magic values, a first section of 0 "
                 "bytes, a 60-byte header plus second section equal to the file size, and a "
                 "property list that ends exactly at the end of the second section, whose leading "
                 "4-byte count equals the section's own length. The mpdbx "
                 "README at the same commit (https://github.com/Mihir-Choudhary/mpdbx/blob/40f926f05021d878207cd635451c00166b1132ed/README.md) "
                 "says the tool was validated on one Windows 11 build (Defender platform 4.18.260x); these 12 come from "
                 "Windows 10 and Windows 11 images and one Windows 11 ARM64 known-data image. "
                 "Columns: the process start time is the FILETIME in the "
                 "CONTEXT_DATA_PROCESS_PPID property (text 'pid:<N>,ProcessStart:<FILETIME>'), "
                 "present on 4 of the 12 files (pc_mus_001_win11 3 and the known-data image 1), so the first column is blank on the others "
                 "(no other time value was found in these 12 files; no scan time has been "
                 "identified in them, and mpdbx lists the scan time as unknown; FILETIME counts "
                 "100-nanosecond intervals from 1601-01-01 UTC). The scanned file's directory (Scanned File Path) and file "
                 "name (Scanned File Name) are separate properties and are reported as stored, "
                 "in the NT device form the properties hold (\\Device\\HarddiskVolumeN\\... on 11 of "
                 "the 12 files and a \\Device\\Cd... path on the other), which names a volume "
                 "number, not a drive letter; mpdbx joins them with a backslash. Process Path "
                 "is the process image's directory in the \\Device\\HarddiskVolumeN form on "
                 "all 12, "
                 "and the process image's file name is the Process Name column. Scan Reason, "
                 "Desired Access and Device Characteristics are integers reported as stored. mpdbx's design.md "
                 "names two Scan Reason values (2 on-open, 5 on-close-after-write); this "
                 "artifact does not apply those names, and no source cited here names the Desired "
                 "Access or Device Characteristics values. Newly Created Hint, "
                 "Open/CreateProcess Hint and Has MOTW ADS (the property is named "
                 "CONTEXT_DATA_HAS_MOTW_ADS, and no source cited here expands the name) are single bytes that mpdbx "
                 "types as booleans: 1 is shown as Yes and 0 as No, and what each hint "
                 "means is not established here. Other "
                 "Properties holds every property without a column of its own, as name=value "
                 "(type 9 fixed 8-byte values and length-prefixed byte values as hexadecimal, "
                 "integers as decimal, single bytes of 0 or 1 as No or Yes): on these 12 files that is "
                 "CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT, CONTEXT_DATA_FILE_AGE, "
                 "CONTEXT_DATA_FILE_LASTWRITE_AGE, CONTEXT_DATA_FILE_LASTCHANGE_AGE and "
                 "CONTEXT_DATA_FILE_ATTRIBUTES, whose units and meaning are not established "
                 "here. Column findings on the corpus runs: on lonewolf_win10, af_case2_win10 and "
                 "szechuan_win10 (8 files) Process Start (UTC) and Process ID held no value on "
                 "every row, because none of those files carries a process ID or process start "
                 "property; on lonewolf_win10 (6 rows) Scan Reason held 2, Newly Created Hint, "
                 "Open/CreateProcess Hint and Has MOTW ADS held No, and Other Properties "
                 "held CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT=0000000000000000 on all 6; on "
                 "pc_mus_001_win11 (3 rows) Scan Reason held 5, Newly Created Hint held Yes and "
                 "Device Characteristics held 395264 on all 3, and Open/CreateProcess Hint, "
                 "Desired Access and Other Properties held no value on any of them; Read Note "
                 "held no value on any row of any run. A property that occurs more than once keeps its first value in its column; "
                 "later ones go to Other Properties with a Read Note (none of the 12 files "
                 "repeats a property). Source File is the evidence-relative path "
                 "of each Store file, kept because the same Persist ID can occur in more than "
                 "one extracted folder. The Id property holds the same 16 bytes as the file name on all 12 "
                 "files and is not repeated. A row records what Defender stored about one "
                 "scan context; it does not show that the file was detected, blocked or "
                 "removed, and does not by itself establish who started the process. Not read: "
                 "the link from a Store file to the AmsiFileCache row with the same PersistId "
                 "in mpenginedb.db, which mpdbx uses to estimate a scan time (on "
                 "pc_mus_001_win11 all 3 AmsiFileCache rows carry a PersistId equal to one of "
                 "its 3 Store file names; this artifact does not join them), and the files "
                 "under Scans/History/Results and Scans/History/Service (Microsoft Defender "
                 "Detection History reads Service/DetectionHistory).",
        "paths": ('*/[Pp]rogram[Dd]ata/[Mm]icrosoft/[Ww]indows [Dd]efender/[Ss]cans/'
                  '[Hh]istory/[Ss]tore/*',),
        "platforms": ("Windows",),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 1 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (a file listing of the image shows no Defender History path; the tool was not run)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (a file listing of the image shows an empty Store folder; the tool was not run)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (a file listing of the image shows a Defender Scans/History folder with no Store folder; the tool was not run)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (a file listing of the image shows a Defender Scans/History folder with no Store folder; the tool was not run)",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (a file listing of the image shows an empty Store folder; the tool was not run)",
        },
    },
}


def _decrypt(data):
    stream = rc4_keystream(KEY, len(data))
    return bytes(a ^ b for a, b in zip(data, stream))


def _property(section, position):
    """(name, kind, value, next position) for the property at position, or raises ValueError."""
    try:
        (name_len,) = struct.unpack_from('<I', section, position)
        position += 4
        if name_len % 2 or position + name_len > len(section):
            raise ValueError('property name runs past the section')
        name = section[position:position + name_len].decode('utf-16-le').rstrip('\0')
        position += name_len
        (kind,) = struct.unpack_from('<I', section, position)
        position += 4
        if kind == _U32:
            value, position = struct.unpack_from('<I', section, position)[0], position + 4
        elif kind == _U64:
            value, position = struct.unpack_from('<Q', section, position)[0], position + 8
        elif kind == _U8:
            value, position = section[position], position + 1
        elif kind == _FIXED8:
            if position + 8 > len(section):
                raise ValueError('property value runs past the section')
            value, position = section[position:position + 8], position + 8
        else:
            (length,) = struct.unpack_from('<I', section, position)
            position += 4
            if position + length > len(section):
                raise ValueError('property value runs past the section')
            raw = section[position:position + length]
            position += length
            value = raw.decode('utf-16-le').rstrip('\0') if kind == _TEXT else raw
    except (struct.error, IndexError, UnicodeDecodeError) as exc:
        raise ValueError(f'property list unreadable: {exc}') from exc
    return name, kind, value, position


def read_store(data):
    """(properties, note): the second section's properties in order as (name, kind, value),
    and a note when the file did not read cleanly."""
    if len(data) < _HEADER:
        return [], f'file is {len(data)} bytes, shorter than the 60-byte header'
    header = _decrypt(data[:_HEADER])
    magic_one = struct.unpack_from('<I', header, 0)[0]
    first, second = struct.unpack_from('<II', header, 0x28)
    magic_two = struct.unpack_from('<I', header, 0x38)[0]
    if magic_one != _MAGIC_ONE or magic_two != _MAGIC_TWO:
        return [], 'header magic values are not the documented ones'
    if _HEADER + first + second != len(data):
        return [], (f'header sections ({first} and {second} bytes) do not fit the file size '
                    f'({len(data)} bytes)')
    section = _decrypt(data[_HEADER + first:_HEADER + first + second])
    if len(section) < 4:
        return [], 'second section is too short to hold a property count'
    notes = [f'first section holds {first} bytes, not read'] if first else []
    (declared,) = struct.unpack_from('<I', section, 0)
    if declared != len(section):
        notes.append(f'second section declares {declared} bytes; it holds {len(section)}')
    section = section[:min(declared, len(section))]
    properties, position = [], 4
    while position < len(section):
        try:
            name, kind, value, position = _property(section, position)
        except ValueError as exc:
            notes.append(f'{exc} after {len(properties)} properties')
            break
        properties.append((name, kind, value))
    return properties, '; '.join(notes)


def _show(kind, value):
    if isinstance(value, bytes):
        return value.hex()
    if kind == _U8 and value in (0, 1):
        return 'Yes' if value else 'No'
    return value


def _store_files(context):
    for path in sorted(str(f) for f in context.get_files_found()):
        relative = '/' + context.get_relative_path(path).replace('\\', '/').lower()
        if not (relative.rsplit('/', 1)[0] + '/').endswith(_STORE_FOLDER) or os.path.isdir(path):
            continue
        if _PERSIST_ID.fullmatch(os.path.basename(path)):
            yield path


@artifact_processor
def defenderHistoryStore(context):  # pylint: disable=too-many-locals
    data_headers = (('Process Start (UTC)', 'datetime'), ('Persist ID', 'hash'),
                    'Scanned File Path (as stored)', 'Scanned File Name', 'Process Name',
                    'Process Path (as stored)', ('Process ID', 'number'),
                    'Scan Reason (as stored)', 'Newly Created Hint', 'Open/CreateProcess Hint',
                    'Has MOTW ADS', 'Desired Access (as stored)',
                    'Device Characteristics (as stored)', 'Other Properties', 'Read Note',
                    'Source File')
    data_list = []
    sources = []
    for path in _store_files(context):
        relative = context.get_relative_path(path)
        sources.append(path)
        try:
            if os.path.getsize(path) > _MAX_FILE:
                logfunc(f'{_LABEL}: {relative} is larger than {_MAX_FILE} bytes, not read')
                continue
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {exc.strerror}')
            continue
        properties, note = read_store(data)
        notes = [note] if note else []
        own, other, persist_bytes = {}, [], None
        for name, kind, value in properties:
            if name in _OWN and _OWN[name] in own:
                other.append(f'{name}={_show(kind, value)}')
                notes.append(f'{name} occurs more than once; the first value is in its column')
            elif name in _OWN:
                own[_OWN[name]] = _show(kind, value)
            elif name == 'Id' and isinstance(value, bytes):
                persist_bytes = value
            else:
                other.append(f'{name}={_show(kind, value)}')
        file_id = os.path.basename(path).upper()
        if persist_bytes is not None and persist_bytes.hex().upper() != file_id:
            other.append(f'Id={persist_bytes.hex()}')
            notes.append('Id property differs from the file name')
        start, pid = '', own.get('pid', '')
        if 'ppid' in own:
            match = _PROCESS_START.match(str(own['ppid']))
            if match:
                start = filetime_utc(int(match.group(2)))
                if pid != '' and int(match.group(1)) != pid:
                    notes.append('process ID differs from the one in the start-time property')
                if pid == '':
                    pid = int(match.group(1))
            else:
                other.append(f'CONTEXT_DATA_PROCESS_PPID={own["ppid"]}')
                notes.append('process start property is not in the documented form')
        data_list.append((
            start, file_id, own.get('path', ''), own.get('name', ''), own.get('process', ''),
            own.get('process_path', ''), pid, own.get('reason', ''), own.get('new', ''),
            own.get('open', ''), own.get('motw', ''), own.get('access', ''),
            own.get('device', ''), '\n'.join(other), '; '.join(notes), relative))
        if notes:
            logfunc(f'{_LABEL}: {relative}: ' + '; '.join(notes))
    logfunc(f'{_LABEL}: {len(data_list)} Store file(s) read')
    return data_headers, data_list, '\n'.join(sources)
