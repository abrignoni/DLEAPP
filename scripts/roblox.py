"""Shared helpers for Roblox Desktop artifacts.

Author: @AlexisBrignoni, Codex
"""

import json
import re
from datetime import datetime, timezone


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return None


def epoch_datetime(value):
    """Convert Unix seconds or milliseconds to an aware UTC datetime."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number <= 0:
        return ""
    if number > 100_000_000_000:
        number /= 1000
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return ""


def iso_datetime(value):
    """Parse the ISO-8601 timestamps written at the start of Roblox log lines."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""


def decode_webkit_value(value):
    """Decode WebKit Local Storage's UTF-16 blob representation."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    body = bytes(value)
    if not body:
        return ""
    for encoding in ("utf-16-le", "utf-8"):
        try:
            return body.decode(encoding).rstrip("\x00")
        except UnicodeDecodeError:
            continue
    return body.hex()


def compact_value(value, limit=None):
    """Render a scalar or compact JSON value, optionally applying a preview limit."""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    elif value is None:
        value = ""
    else:
        value = str(value)
    if limit is not None and len(value) > limit:
        return value[:limit] + "…"
    return value


def origin_from_webkit_file(path):
    """Recover the origin strings from WebKit's small binary origin file."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(4096)
    except OSError:
        return ""
    strings = re.findall(rb"[\x20-\x7e]{4,}", data)
    decoded = [item.decode("ascii", "ignore").strip("\x00") for item in strings]
    scheme = next((item for item in decoded if item in ("http", "https")), "")
    host = next((item for item in decoded if "." in item and "/" not in item), "")
    return f"{scheme}://{host}" if scheme and host else host
