__artifacts_v2__ = {
    "wireLocalStorage": {
        "name": "Wire Local Storage",
        "description": "Key/value pairs from the Wire desktop app's Chromium "
                       "Local Storage (main profile and Electron partitions), "
                       "one row per key with its newest live value. Keys in the "
                       "tested corpus included an analytics (Countly) device id, "
                       "the selected and favourite video input device ids, the UI "
                       "locale and interface preferences.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Wire (Windows)",
        "notes": "Only entries for wire.com origins (the host wire.com or one of its "
                 "subdomains) and keys stored without an origin (reported as '(app)') "
                 "are reported, and only from Local Storage folders under a folder "
                 "named Wire, the name of the Wire profile folder in the tested corpus. "
                 "Origin held https://app.wire.com on all 21 rows reported from the "
                 "tested corpus. "
                 "The store keeps earlier versions of a key beside the newest one (9 of "
                 "the 21 keys reported from the tested corpus had more than one, up to "
                 "25), so each key is reported with the value carrying its highest "
                 "sequence number, and a key whose newest record is a deletion is not "
                 "reported. Chromium writes a format byte before each Local Storage key "
                 "and value, 0 for UTF-16 and 1 for Latin-1, and the artifact decodes "
                 "both by it; every key and value in the tested corpus carried the "
                 "Latin-1 byte, so the UTF-16 branch is unexercised. Reference: "
                 "Chromium, 'cached_storage_area.cc', "
                 "https://github.com/chromium/chromium/blob/b8c3e22534db19c8fe58dc0da29d943220721bb9/"
                 "third_party/blink/renderer/modules/storage/cached_storage_area.cc#L747-L768",
        "paths": ('*/Wire/*Local Storage/leveldb/*',),
        "sample_data": {
            "wire_win": "Windows, version not recorded | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Wire profile folder)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Wire profile folder)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Wire profile folder)",
        },
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
    },
}

import os
from urllib.parse import urlsplit

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.ccl import ccl_leveldb


def _leveldb_dirs(context):
    dirs = {}
    for file_found in context.get_files_found():
        file_found = str(file_found)
        parent = os.path.dirname(file_found)
        if os.path.basename(parent) == "leveldb" and \
                "Local Storage" in parent.replace("\\", "/"):
            dirs.setdefault(os.path.realpath(parent), parent)
    return list(dirs.values())


def _source_label(path):
    parts = path.replace("\\", "/").split("/")
    if "Partitions" in parts:
        i = parts.index("Partitions")
        if i + 1 < len(parts):
            return f"Partition {parts[i + 1]}"
    return "Default profile"


def _decode_storage_string(raw):
    """Decode a Local Storage key or value by its leading format byte.

    Chromium writes 0 for UTF-16 and 1 for Latin-1 before the payload. Anything
    else is returned decoded as UTF-8 with replacement, so nothing is dropped.
    """
    if not raw:
        return ""
    flag, body = raw[:1], raw[1:]
    if flag == b"\x00":
        return body.decode("utf-16-le", "replace")
    if flag == b"\x01":
        return body.decode("latin-1")
    return raw.decode("utf-8", "replace")


def _is_wire_origin(origin):
    """True for an origin whose host is wire.com or one of its subdomains.

    A substring test would also admit an unrelated host such as notwire.com.
    """
    host = urlsplit(origin).hostname or ""
    return host == "wire.com" or host.endswith(".wire.com")


@artifact_processor
def wireLocalStorage(context):
    data_list = []
    read_dirs = []

    for ldb_dir in _leveldb_dirs(context):
        label = _source_label(ldb_dir)
        try:
            db = ccl_leveldb.RawLevelDb(ldb_dir)
            records = list(db.iterate_records_raw())
            db.close()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # A store written while the app ran can end in a torn log record, which
            # the reader raises on; report it and carry on with the other stores.
            logfunc(f"Wire Local Storage: could not read '{ldb_dir}': "
                    f"{type(ex).__name__}: {ex}")
            continue

        newest = {}
        for rec in records:
            k = rec.user_key or b""
            current = newest.get(k)
            if current is None or rec.seq > current.seq:
                newest[k] = rec

        rows = []
        for k, rec in newest.items():
            if rec.state.name != "Live":
                continue
            # Skip Local Storage bookkeeping keys (VERSION, META:*, METAACCESS:*).
            if k == b"VERSION" or k.startswith(b"META"):
                continue
            if k.startswith(b"_") and b"\x00" in k:
                origin, _, item = k.partition(b"\x00")
                origin = origin[1:].decode("utf-8", "replace")
                item = _decode_storage_string(item)
            else:
                origin = ""
                item = k.decode("utf-8", "replace")
            if origin and not _is_wire_origin(origin):
                continue
            rows.append((label, origin or "(app)", item, _decode_storage_string(rec.value)[:2000]))

        read_dirs.append(ldb_dir)
        data_list.extend(rows)

    data_headers = ("Source", "Origin", "Key", "Value")
    return data_headers, data_list, "\n".join(read_dirs)
