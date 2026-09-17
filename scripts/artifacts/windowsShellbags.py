"""Windows ShellBags parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Shellbags artifact; this
reads the BagMRU keys out of UsrClass.dat and NTUSER.DAT with python-registry and
parses the shell items itself.

ShellBags record the folders a user browsed in Explorer. Each BagMRU key is a
folder in the browse tree; its numbered values are the shell items of its child
folders and its numbered subkeys are those children, so the tree reconstructs the
folder path. Shell-item parsing follows the Windows Shell Item format (libyal
libfwsi): a 2-byte size, a 1-byte type, then type-specific data, and for file
entries a 0xBEEF0004 extension block that carries the long name.
"""

import struct
from datetime import datetime, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# BagMRU root key paths tried in each hive; the ones absent raise and are skipped.
_BAG_ROOTS = (
    "Local Settings\\Software\\Microsoft\\Windows\\Shell\\BagMRU",   # UsrClass.dat
    "Software\\Microsoft\\Windows\\Shell\\BagMRU",                   # NTUSER.DAT
    "Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU",             # NTUSER.DAT (legacy)
)
_MAX_DEPTH = 50

# Documented shell-folder GUIDs seen at the root of a browse tree. Anything not
# listed is shown as its raw {GUID}; nothing is guessed.
_KNOWN_GUIDS = {
    "20d04fe0-3aea-1069-a2d8-08002b30309d": "This PC",
    "679f85cb-0220-4080-b29b-5540cc05aab6": "Quick access",
    "b4bfcc3a-db2c-424c-b029-7fe99a87c641": "Desktop",
    "f02c1a0d-be21-4350-88b0-7367fc96ef3c": "Network",
    "031e4825-7b94-4dc3-b131-e946b44c8dd5": "Libraries",
    "21ec2020-3aea-1069-a2dd-08002b30309d": "Control Panel",
    "645ff040-5081-101b-9f08-00aa002f954e": "Recycle Bin",
}

__artifacts_v2__ = {
    "shellbags": {
        "name": "ShellBags",
        "description": "Folders browsed in Windows Explorer, reconstructed from the "
                       "BagMRU shell items in UsrClass.dat and NTUSER.DAT, with each "
                       "folder's registry last-write time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from UsrClass.dat and NTUSER.DAT, named in Source File. Each "
                 "row is one BagMRU node, that is one folder in a browse tree, from "
                 "Shell\\BagMRU in UsrClass.dat or NTUSER.DAT (the ShellNoRoam tree "
                 "is read too). Shell Path is rebuilt by walking the tree and "
                 "decoding each node's shell item; a drive shows as C:, a folder "
                 "shows its long name from the shell item's 0xBEEF0004 block or its "
                 "short (8.3) name when no long name is stored, and a root shows a "
                 "known shell-folder name where the GUID is documented or the raw "
                 "{GUID} otherwise; an item type the parser does not decode to a "
                 "name is shown as <shell item 0xNN>. A short (8.3) name such as "
                 "ANDROI~1 is shown as stored. Registry Last Write (UTC) is the BagMRU node key's own "
                 "last-write time, which Windows updates when that folder's child "
                 "list changes, so it approximates when the folder was last browsed "
                 "at or below that node, not a file time. Item Modified (UTC) is the "
                 "DOS modification date stored inside a file-entry shell item, blank "
                 "for drive and root nodes; DOS dates have two-second resolution and "
                 "carry no time zone, so it is shown as read. A ShellBags entry "
                 "records that the folder was browsed, not who was at the keyboard. "
                 "Reading the hives needs the python-registry package; the .LOG1 and "
                 ".LOG2 transaction logs are not replayed. Format: libyal libfwsi, "
                 "Windows Shell Item format, https://github.com/libyal/libfwsi/blob/"
                 "main/documentation/Windows%20Shell%20Item%20format.asciidoc; and "
                 "Velocidex, Windows.Forensics.Shellbags, https://github.com/"
                 "Velocidex/velociraptor/blob/master/artifacts/definitions/Windows/"
                 "Forensics/Shellbags.yaml",
        "paths": ("*/AppData/Local/Microsoft/Windows/[Uu]sr[Cc]lass.[Dd]at",
                  "*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt]"),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 41 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 20 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 29 rows",
        },
    },
}


def _guid(blob):
    if len(blob) < 16:
        return ""
    d1, d2, d3 = struct.unpack_from("<IHH", blob, 0)
    return "%08x-%04x-%04x-%s-%s" % (d1, d2, d3, blob[8:10].hex(), blob[10:16].hex())


def _dos_datetime(value):
    """A DOS date/time dword: low word date, high word time. No time zone."""
    date = value & 0xFFFF
    time = (value >> 16) & 0xFFFF
    if not date:
        return ""
    try:
        return datetime(
            ((date >> 9) & 0x7F) + 1980, (date >> 5) & 0x0F, date & 0x1F,
            (time >> 11) & 0x1F, (time >> 5) & 0x3F, (time & 0x1F) * 2,
            tzinfo=timezone.utc)
    except ValueError:
        return ""


def _beef_longname(data):
    """The UTF-16 long name inside a file entry's 0xBEEF0004 extension block."""
    idx = data.find(b"\x04\x00\xef\xbe")
    if idx < 4:
        return None
    version = struct.unpack_from("<H", data, idx - 2)[0]
    pos = idx + 4 + 8 + 2   # signature, created+accessed DOS, unknown
    if version >= 7:
        pos += 16           # file reference + unknown
    if version < 3:
        return None
    chars = []
    while pos + 1 < len(data):
        pair = data[pos:pos + 2]
        if pair == b"\x00\x00":
            break
        chars.append(pair)
        pos += 2
    try:
        return b"".join(chars).decode("utf-16-le", "replace") or None
    except (UnicodeDecodeError, ValueError):
        return None


def _printable(text):
    return text if text and all(ch == "\t" or ord(ch) >= 0x20 for ch in text) else ""


def _shell_item(data):
    """Return (display_name, item_modified) for one shell item."""
    if len(data) < 3:
        return "", ""
    item_type = data[2]
    if item_type == 0x1F:                       # root / known folder (GUID)
        guid = _guid(data[4:20])
        return _KNOWN_GUIDS.get(guid, "{%s}" % guid) if guid else "", ""
    if item_type == 0x2F:                       # volume / drive
        name = _printable(data[3:].split(b"\x00")[0].decode("ascii", "replace"))
        return (name.rstrip("\\") or "(volume)"), ""
    if 0x30 <= item_type <= 0x3F:               # file / folder entry
        modified = ""
        if len(data) >= 12:
            modified = _dos_datetime(struct.unpack_from("<I", data, 8)[0])
        name = _beef_longname(data)
        if not name:
            name = _printable(data[14:].split(b"\x00")[0].decode("ascii", "replace"))
        return (name or "(file entry)"), modified
    # Any other type (delegate/property folders, etc.): use a long name if the
    # item carries a 0xBEEF0004 block, otherwise a neutral label. Nothing guessed.
    return (_beef_longname(data) or "<shell item 0x%02x>" % item_type), ""


def _walk(key, prefix, rows, depth=0):
    if depth > _MAX_DEPTH:
        return
    items = {int(v.name()): v.value() for v in key.values() if v.name().isdigit()}
    for sub in key.subkeys():
        if not sub.name().isdigit():
            continue
        name, modified = _shell_item(items.get(int(sub.name()), b""))
        path = prefix + [name] if name else prefix
        timestamp = sub.timestamp()
        if timestamp is not None and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        rows.append((timestamp, "\\".join(path), modified))
        _walk(sub, path, rows, depth + 1)


def _bag_rows(reg):
    rows = []
    for root_path in _BAG_ROOTS:
        try:
            root = reg.open(root_path)
        except Registry.RegistryKeyNotFoundException:
            continue
        _walk(root, [], rows)
    return rows


@artifact_processor
def shellbags(context):
    data_headers = (('Registry Last Write (UTC)', 'datetime'), 'Shell Path',
                    ('Item Modified (UTC)', 'datetime'), 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('ShellBags: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(('usrclass.dat', 'ntuser.dat'))]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            reg = Registry.Registry(source)
            for timestamp, path, modified in _bag_rows(reg):
                data_list.append((timestamp, path, modified, relative_source))
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'ShellBags: could not read {relative_source}: {exc}')
            continue
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
