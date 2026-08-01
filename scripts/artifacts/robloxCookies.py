__artifacts_v2__ = {
    "robloxCookies": {
        "name": "Roblox Cookies",
        "description": "Cookies from Roblox Desktop's macOS binary cookie store, "
                       "including domain, name, path, creation, expiry, last-access "
                       "time, flags and the stored value.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "All values are reported verbatim for evidentiary analysis. The "
                 "output can contain authentication, anti-bot, identity-verification "
                 "and session values; the parser does not test whether they remain "
                 "valid or reusable.",
        "paths": (
            "*/Library/HTTPStorages/com.roblox.RobloxPlayer.binarycookies",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 17 rows",
        },
    },
}

import plistlib
import struct
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc


_APPLE_EPOCH = 978307200
def _read_cstring(record, offset):
    if offset <= 0 or offset >= len(record):
        return ""
    end = record.find(b"\x00", offset)
    if end < 0:
        end = len(record)
    return record[offset:end].decode("utf-8", "replace")


def _apple_datetime(value):
    try:
        return datetime.fromtimestamp(float(value) + _APPLE_EPOCH,
                                      tz=timezone.utc)
    except (OSError, OverflowError, TypeError, ValueError):
        return ""


def _parse_cookie(record):
    if len(record) < 56:
        return None
    try:
        size = struct.unpack_from("<I", record, 0)[0]
        flags = struct.unpack_from("<I", record, 8)[0]
        domain_off, name_off, path_off, value_off = struct.unpack_from(
            "<IIII", record, 16)
        expires, created = struct.unpack_from("<dd", record, 40)
    except struct.error:
        return None
    if size > len(record) or min(domain_off, name_off, path_off, value_off) < 0:
        return None
    domain = _read_cstring(record, domain_off)
    name = _read_cstring(record, name_off)
    path = _read_cstring(record, path_off)
    value = _read_cstring(record, value_off)
    accessed = ""
    plist_offset = record.find(b"bplist00")
    if plist_offset >= 0:
        try:
            metadata = plistlib.loads(record[plist_offset:])
            accessed = _apple_datetime(metadata.get("AccessTime"))
        except (plistlib.InvalidFileException, ValueError, TypeError):
            pass
    return {
        "created": _apple_datetime(created),
        "accessed": accessed,
        "expires": _apple_datetime(expires),
        "domain": domain,
        "name": name,
        "path": path,
        "value": value,
        "value_length": len(value),
        "flags": f"0x{flags:08X}",
    }


def _parse_binary_cookies(path):
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return []
    if len(data) < 8 or data[:4] != b"cook":
        return []
    try:
        page_count = struct.unpack_from(">I", data, 4)[0]
        page_sizes = struct.unpack_from(
            ">" + ("I" * page_count), data, 8)
    except struct.error:
        return []
    position = 8 + (4 * page_count)
    cookies = []
    for page_size in page_sizes:
        page = data[position:position + page_size]
        position += page_size
        if len(page) < 8:
            continue
        try:
            cookie_count = struct.unpack_from("<I", page, 4)[0]
            offsets = struct.unpack_from(
                "<" + ("I" * cookie_count), page, 8)
        except struct.error:
            continue
        for offset in offsets:
            if offset + 4 > len(page):
                continue
            try:
                size = struct.unpack_from("<I", page, offset)[0]
            except struct.error:
                continue
            if size < 56 or offset + size > len(page):
                continue
            cookie = _parse_cookie(page[offset:offset + size])
            if cookie:
                cookies.append(cookie)
    return cookies


@artifact_processor
def robloxCookies(context):
    data_headers = (
        ("Created", "datetime"), ("Last Access", "datetime"),
        ("Expires", "datetime"), "Domain", "Name", "Path", "Value",
        "Value Length", "Flags", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        cookies = _parse_binary_cookies(file_found)
        if cookies:
            source_paths.append(file_found)
        for cookie in cookies:
            data_list.append((
                cookie["created"], cookie["accessed"], cookie["expires"],
                cookie["domain"], cookie["name"], cookie["path"],
                cookie["value"], cookie["value_length"], cookie["flags"],
                context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox Cookies: {len(data_list)} cookie(s).")
    return data_headers, data_list, "\n".join(source_paths)
