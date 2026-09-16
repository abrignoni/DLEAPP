"""Windows Shell Link (.lnk) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

A shell link (.lnk) is a binary file in the Windows Shell Link Binary File
Format. This parser follows Microsoft's [MS-SHLLINK] specification and libyal
liblnk's documentation, and reuses the Windows Shell Item decoding shared with
the ShellBags parser for the LinkTargetIDList.

`parse_lnk(data)` returns a dict of the fields an examiner acts on: the target's
recorded created/modified/accessed times, the local path (or network path, or a
shell path rebuilt from the target id list), target size, the volume the target
lived on (drive type, serial, label), command-line arguments, and the machine id
the shell link recorded when it was written. It is also used by the Jump Lists
parser, whose destination streams are themselves shell links.
"""

import struct
from datetime import datetime, timedelta, timezone

# LinkCLSID 00021401-0000-0000-C000-000000000046, little-endian on disk.
_LNK_CLSID = bytes.fromhex("0114020000000000c000000000000046")

# DriveType values from the Windows GetDriveType constants (DRIVE_*).
_DRIVE_TYPE = {0: "Unknown", 1: "No root directory", 2: "Removable", 3: "Fixed",
               4: "Remote", 5: "CD-ROM", 6: "RAM disk"}

# Documented shell-folder GUIDs seen at the root of a target id list; anything
# not listed is shown as its raw {GUID}. Kept in step with windowsShellbags.py.
_KNOWN_GUIDS = {
    "20d04fe0-3aea-1069-a2d8-08002b30309d": "This PC",
    "679f85cb-0220-4080-b29b-5540cc05aab6": "Quick access",
    "b4bfcc3a-db2c-424c-b029-7fe99a87c641": "Desktop",
    "f02c1a0d-be21-4350-88b0-7367fc96ef3c": "Network",
    "031e4825-7b94-4dc3-b131-e946b44c8dd5": "Libraries",
    "21ec2020-3aea-1069-a2dd-08002b30309d": "Control Panel",
    "645ff040-5081-101b-9f08-00aa002f954e": "Recycle Bin",
}


def _filetime(value):
    """A Windows FILETIME (100-ns intervals since 1601-01-01 UTC)."""
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _guid(blob):
    if len(blob) < 16:
        return ""
    d1, d2, d3 = struct.unpack_from("<IHH", blob, 0)
    return "%08x-%04x-%04x-%s-%s" % (d1, d2, d3, blob[8:10].hex(), blob[10:16].hex())


def _beef_longname(data):
    """The UTF-16 long name inside a file entry's 0xBEEF0004 extension block."""
    idx = data.find(b"\x04\x00\xef\xbe")
    if idx < 4:
        return None
    version = struct.unpack_from("<H", data, idx - 2)[0]
    pos = idx + 4 + 8 + 2
    if version >= 7:
        pos += 16
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


def _shell_item_name(data):
    """Display name for one Windows Shell Item (libfwsi), or "" when the parser
    decodes no name. Shared shape with windowsShellbags.py's _shell_item."""
    if len(data) < 3:
        return ""
    item_type = data[2]
    if item_type == 0x1F:                       # root / known folder (GUID)
        guid = _guid(data[4:20])
        return _KNOWN_GUIDS.get(guid, "{%s}" % guid) if guid else ""
    if item_type == 0x2F:                       # volume / drive
        name = _printable(data[3:].split(b"\x00")[0].decode("ascii", "replace"))
        return name.rstrip("\\")
    if 0x30 <= item_type <= 0x3F:               # file / folder entry
        name = _beef_longname(data)
        if not name:
            name = _printable(data[14:].split(b"\x00")[0].decode("ascii", "replace"))
        return name or ""
    return _beef_longname(data) or ""


def _idlist_path(data):
    """Rebuild a shell path from a LinkTargetIDList (a run of ItemIDs)."""
    names = []
    pos = 0
    while pos + 2 <= len(data):
        size = struct.unpack_from("<H", data, pos)[0]
        if size == 0:
            break
        item = data[pos:pos + size]
        name = _shell_item_name(item)
        if name:
            names.append(name)
        pos += size
    return "\\".join(names)


def _cstr(data, off, unicode_str=False):
    if off <= 0 or off >= len(data):
        return ""
    if unicode_str:
        end = off
        while end + 1 < len(data) and data[end:end + 2] != b"\x00\x00":
            end += 2
        return data[off:end].decode("utf-16-le", "replace")
    end = data.find(b"\x00", off)
    if end < 0:
        end = len(data)
    return data[off:end].decode("latin-1", "replace")


def parse_lnk(data):
    """Parse shell link bytes. Returns a dict of fields; a malformed link
    returns {'error': <reason>}. Never raises on ordinary bad input."""
    out = {}
    if len(data) < 76:
        return {"error": "shorter than a shell link header"}
    if struct.unpack_from("<I", data, 0)[0] != 0x4C:
        return {"error": "header size is not 0x4C"}
    if data[4:20] != _LNK_CLSID:
        return {"error": "not a shell link CLSID"}
    flags = struct.unpack_from("<I", data, 20)[0]
    out["attributes"] = struct.unpack_from("<I", data, 24)[0]
    ctime, atime, wtime = struct.unpack_from("<QQQ", data, 28)
    out["target_created"] = _filetime(ctime)
    out["target_accessed"] = _filetime(atime)
    out["target_modified"] = _filetime(wtime)
    out["target_size"] = struct.unpack_from("<I", data, 52)[0]
    for key in ("local_path", "network_path", "shell_path", "drive_type",
                "drive_serial", "volume_label", "arguments", "name",
                "relative_path", "working_dir", "machine_id"):
        out[key] = ""

    pos = 76
    if flags & 0x1:                                   # HasLinkTargetIDList
        if pos + 2 > len(data):
            return out
        idlen = struct.unpack_from("<H", data, pos)[0]
        out["shell_path"] = _idlist_path(data[pos + 2:pos + 2 + idlen])
        pos += 2 + idlen

    if (flags & 0x2) and not (flags & 0x100):         # HasLinkInfo
        li = pos
        try:
            li_size, li_hdr, li_flags = struct.unpack_from("<III", data, li)
            voloff, lbpoff, cnrloff, cpsoff = struct.unpack_from("<IIII", data, li + 12)
        except struct.error:
            return out
        lbp_uni = cps_uni = 0
        if li_hdr >= 0x24 and li + 36 <= len(data):
            lbp_uni, cps_uni = struct.unpack_from("<II", data, li + 28)
        if (li_flags & 0x1) and voloff and li + voloff + 16 <= len(data):
            v = li + voloff
            _, dtype, serial, laboff = struct.unpack_from("<IIII", data, v)
            out["drive_type"] = _DRIVE_TYPE.get(dtype, "0x%08x" % dtype)
            out["drive_serial"] = "%08X" % serial
            if laboff == 0x14 and v + 20 <= len(data):
                out["volume_label"] = _cstr(data, v + struct.unpack_from("<I", data, v + 16)[0], True)
            else:
                out["volume_label"] = _cstr(data, v + laboff)
        base = _cstr(data, li + lbpoff) if (li_flags & 0x1 and lbpoff) else ""
        if lbp_uni:
            base = _cstr(data, li + lbp_uni, True) or base
        suffix = _cstr(data, li + cpsoff) if cpsoff else ""
        if cps_uni:
            suffix = _cstr(data, li + cps_uni, True) or suffix
        out["local_path"] = base + suffix
        if (li_flags & 0x2) and cnrloff and li + cnrloff + 12 <= len(data):
            c = li + cnrloff
            netoff = struct.unpack_from("<I", data, c + 8)[0]
            out["network_path"] = _cstr(data, c + netoff) if netoff else ""
        pos = li + li_size

    unicode_str = bool(flags & 0x80)
    for key, bit in (("name", 0x4), ("relative_path", 0x8), ("working_dir", 0x10),
                     ("arguments", 0x20), ("icon", 0x40)):
        if not (flags & bit) or pos + 2 > len(data):
            continue
        count = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        nbytes = count * 2 if unicode_str else count
        chunk = data[pos:pos + nbytes]
        text = chunk.decode("utf-16-le" if unicode_str else "latin-1", "replace")
        if key != "icon":
            out[key] = text
        pos += nbytes

    while pos + 8 <= len(data):                        # ExtraData blocks
        block_size = struct.unpack_from("<I", data, pos)[0]
        if block_size < 4 or pos + block_size > len(data):
            break
        signature = struct.unpack_from("<I", data, pos + 4)[0]
        if signature == 0xA0000003 and block_size >= 0x60:   # TrackerDataBlock
            out["machine_id"] = data[pos + 16:pos + 32].split(b"\x00")[0].decode("latin-1", "replace")
        pos += block_size

    return out


def target_path(parsed):
    """The best available target locator: local path, else network path, else
    the shell path rebuilt from the target id list."""
    return parsed.get("local_path") or parsed.get("network_path") or parsed.get("shell_path") or ""
