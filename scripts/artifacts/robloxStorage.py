__artifacts_v2__ = {
    "robloxWebKitLocalStorage": {
        "name": "Roblox WebKit Local Storage",
        "description": "Key/value records retained by Roblox Desktop's embedded "
                       "WebKit origins, including real-time state, feature caches, "
                       "locale data and identity-verification state.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "UTF-16 values are decoded and JSON is normalized. Values are "
                 "reported in full and may contain tokens or credential-like data; "
                 "the parser does not determine whether they remain valid or "
                 "reusable. JSON normalization can change whitespace without "
                 "changing its data.",
        "paths": (
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/"
            "LocalStorage/localstorage.sqlite3",
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/origin",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 20 rows",
        },
    },
    "robloxIndexedDB": {
        "name": "Roblox WebKit IndexedDB",
        "description": "Database and object-store records from Roblox Desktop's "
                       "WebKit IndexedDB stores. Serialized keys and values receive "
                       "a heuristic readable-text preview and retain their raw size "
                       "for follow-up analysis.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "WebKit uses a binary structured-clone encoding. This parser does "
                 "not fully deserialize every JavaScript value type; it extracts "
                 "embedded readable strings and limits each preview to 5,000 "
                 "characters. Preview output may contain tokens or credential-like "
                 "data whose validity and reusability are not assessed.",
        "paths": (
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/"
            "IndexedDB/*/IndexedDB.sqlite3",
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/origin",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 2 rows",
        },
    },
    "robloxAssetCache": {
        "name": "Roblox Asset Cache Index",
        "description": "Roblox's rbx-storage cache index, recording cached object "
                       "identifiers, last-access times, logical sizes, hit counts, "
                       "categories, raw score values, TTL values and stored-content "
                       "signatures.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "The 16-byte IDs are opaque cache keys. Atime behaves as Unix "
                 "milliseconds and ttl, when present, behaves as Unix seconds in the "
                 "tested corpus. Score appears to be a ranking or eviction metric; "
                 "its exact semantics are unverified, so it is reported raw.",
        "paths": ("*/Library/Roblox/rbx-storage.db",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "archive",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 2479 rows",
        },
    },
    "robloxWebKitNetworkCache": {
        "name": "Roblox WebKit Network Cache",
        "description": "HTTP resources identified in Roblox Desktop's WebKit network "
                       "cache, including URL, host, heuristically recovered HTTP "
                       "metadata, record size and any companion blob size.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "WebKit's cache is an internal, versioned implementation format. "
                 "URLs and query parameters are reported in full. HTTP Date, content "
                 "type and ETag are heuristic string recoveries and can be absent or "
                 "imperfect. A companion -blob size is exact when present; otherwise "
                 "the response body may be inline or absent and is not decoded here.",
        "paths": (
            "*/Library/Caches/com.roblox.RobloxPlayer/WebKit/NetworkCache/"
            "Version */Records/*/Resource/*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 408 rows",
        },
    },
}

import json
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.roblox import (
    compact_value,
    decode_webkit_value,
    epoch_datetime,
    origin_from_webkit_file,
)

_COMMON_MIME_TYPES = {
    "application/gzip",
    "application/javascript",
    "application/json",
    "application/manifest+json",
    "application/octet-stream",
    "application/wasm",
    "application/x-javascript",
    "application/xml",
    "audio/mpeg",
    "audio/ogg",
    "font/otf",
    "font/ttf",
    "font/woff",
    "font/woff2",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/svg+xml",
    "image/webp",
    "text/css",
    "text/html",
    "text/javascript",
    "text/plain",
    "text/xml",
    "video/mp4",
    "video/webm",
}


def _source_origin(database_path):
    folder = os.path.dirname(database_path)
    for _ in range(5):
        origin_path = os.path.join(folder, "origin")
        if os.path.isfile(origin_path):
            return origin_from_webkit_file(origin_path)
        folder = os.path.dirname(folder)
    return ""


@artifact_processor
def robloxWebKitLocalStorage(context):
    data_headers = ("Origin", "Key", "Value", "Value Length", "Source File")
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found) != "localstorage.sqlite3":
            continue
        connection = open_sqlite_db_readonly(file_found)
        if not connection:
            continue
        try:
            rows = connection.execute(
                "SELECT key, value FROM ItemTable ORDER BY key").fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox Local Storage: could not read '{file_found}': {ex}")
            connection.close()
            continue
        connection.close()
        if rows:
            source_paths.append(file_found)
        origin = _source_origin(file_found)
        for key, raw_value in rows:
            decoded = decode_webkit_value(raw_value)
            try:
                value = compact_value(json.loads(decoded))
            except (TypeError, ValueError):
                value = compact_value(decoded)
            data_list.append((
                origin, key, value, len(decoded),
                context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox WebKit Local Storage: {len(data_list)} record(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _readable_strings(value):
    if value is None:
        return ""
    if isinstance(value, str):
        if "\x00" not in value:
            return value[:5000]
        data = value.encode("latin-1", "replace")
    else:
        data = bytes(value)
    recovered = []
    for match in re.finditer(rb"(?:[\x20-\x7e]\x00){3,}", data):
        text = match.group().decode("utf-16-le", "ignore").strip()
        if text and text not in recovered:
            recovered.append(text)
    for match in re.finditer(rb"[\x20-\x7e]{4,}", data):
        text = match.group().decode("utf-8", "ignore").strip()
        if text and text not in recovered:
            recovered.append(text)
    return " | ".join(recovered)[:5000]


@artifact_processor
def robloxIndexedDB(context):
    data_headers = (
        "Origin", "Database", "Object Store", "Record ID", "Key Preview",
        "Value Preview", "Value Size (bytes)", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found) != "IndexedDB.sqlite3":
            continue
        connection = open_sqlite_db_readonly(file_found)
        if not connection:
            continue
        try:
            info = dict(connection.execute(
                "SELECT key, value FROM IDBDatabaseInfo").fetchall())
            stores = dict(connection.execute(
                "SELECT id, name FROM ObjectStoreInfo").fetchall())
            rows = connection.execute(
                "SELECT objectStoreID, recordID, key, value FROM Records "
                "ORDER BY recordID").fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox IndexedDB: could not read '{file_found}': {ex}")
            connection.close()
            continue
        connection.close()
        if rows:
            source_paths.append(file_found)
        origin = _source_origin(file_found)
        for store_id, record_id, key, value in rows:
            key_preview = _readable_strings(key)
            value_preview = _readable_strings(value) or bytes(value).hex()[:5000]
            data_list.append((
                origin,
                info.get("DatabaseName", ""),
                stores.get(store_id, str(store_id)),
                record_id,
                key_preview,
                value_preview,
                len(value) if value is not None else 0,
                context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox WebKit IndexedDB: {len(data_list)} record(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _content_signature(content):
    if not content:
        return ""
    signatures = (
        (b"RBXH", "RBXH"),
        (b"\x89PNG\r\n\x1a\n", "PNG"),
        (b"\xff\xd8\xff", "JPEG"),
        (b"OggS", "Ogg"),
        (b"RIFF", "RIFF"),
        (b"PK\x03\x04", "ZIP"),
        (b"\x1f\x8b", "gzip"),
    )
    for marker, label in signatures:
        if bytes(content).startswith(marker):
            return label
    return bytes(content[:8]).hex().upper()


@artifact_processor
def robloxAssetCache(context):
    data_headers = (
        ("Last Access", "datetime"),
        ("TTL (database value, as Unix seconds)", "datetime"), "Cache ID",
        "Category", "Logical Size (bytes)", "Hit Count", "Score",
        "Stored Content Size (bytes)", "Content Signature", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        connection = open_sqlite_db_readonly(file_found)
        if not connection:
            continue
        try:
            rows = connection.execute(
                "SELECT hex(id), category, size, hits, atime, score, ttl, "
                "content FROM files ORDER BY atime").fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox asset cache: could not read '{file_found}': {ex}")
            connection.close()
            continue
        connection.close()
        if rows:
            source_paths.append(file_found)
        for cache_id, category, size, hits, atime, score, ttl, content in rows:
            data_list.append((
                epoch_datetime(atime),
                epoch_datetime(ttl),
                cache_id,
                category,
                size,
                hits,
                score,
                len(content) if content else 0,
                _content_signature(content),
                context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox Asset Cache Index: {len(data_list)} record(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _cache_metadata(path):
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return None

    strings = []
    for match in re.finditer(rb"(?:[\x20-\x7e]\x00){8,}", data):
        strings.append(match.group().decode("utf-16-le", "ignore"))
    for match in re.finditer(rb"[\x20-\x7e]{4,}", data):
        strings.append(match.group().decode("utf-8", "ignore"))

    url = next((item for item in strings if item.startswith(("http://", "https://"))), "")
    if not url:
        return None
    date_value = next((item for item in strings
                       if re.match(r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), ", item)), "")
    cached = ""
    if date_value:
        try:
            cached = parsedate_to_datetime(date_value)
            if isinstance(cached, datetime) and cached.tzinfo is None:
                cached = datetime(
                    cached.year, cached.month, cached.day, cached.hour,
                    cached.minute, cached.second, cached.microsecond,
                    tzinfo=timezone.utc)
        except (TypeError, ValueError):
            cached = ""
    mime = ""
    for item in strings:
        candidate = item.lower()
        base_type = candidate.split(";", 1)[0]
        if (item == candidate and base_type in _COMMON_MIME_TYPES
                and re.fullmatch(
                    r"[a-z]+/[a-z0-9][a-z0-9.+_-]*"
                    r"(?:;\s*charset=[a-z0-9._-]+)?", candidate)):
            mime = item
            break
    etag = ""
    for index, item in enumerate(strings[:-1]):
        if item.lower() == "etag":
            etag = strings[index + 1]
            break
    return cached, url, mime, etag


@artifact_processor
def robloxWebKitNetworkCache(context):
    data_headers = (
        ("Recovered HTTP Date", "datetime"), "Host", "URL",
        "Recovered Content Type (heuristic)", "Recovered ETag (heuristic)",
        "Cache Record Size (bytes)", "Companion Blob Size (bytes)",
        "Body Storage", "Source Cache File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        if file_found.endswith("-blob"):
            continue
        metadata = _cache_metadata(file_found)
        if not metadata:
            continue
        cached, url, mime, etag = metadata
        try:
            host = urlsplit(url).hostname or ""
        except ValueError:
            host = ""
        blob_path = file_found + "-blob"
        if os.path.isfile(blob_path):
            body_size = os.path.getsize(blob_path)
            body_storage = "Companion -blob file"
        else:
            body_size = ""
            body_storage = "Inline or absent (not decoded)"
        try:
            metadata_size = os.path.getsize(file_found)
        except OSError:
            metadata_size = 0
        data_list.append((
            cached, host, url, mime, etag, metadata_size, body_size,
            body_storage, context.get_relative_path(file_found),
        ))
        source_paths.append(file_found)
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime)
        else datetime.min.replace(tzinfo=timezone.utc))
    logfunc(f"Roblox WebKit Network Cache: {len(data_list)} response(s).")
    return data_headers, data_list, "\n".join(source_paths[:50])
