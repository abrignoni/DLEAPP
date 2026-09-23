"""Helpers shared by the DLEAPP Windows registry artifacts.

Author: @AlexisBrignoni, Claude.

Offline hives are read with python-registry. Its key timestamps are the key's
last-written FILETIME, returned as a naive datetime in UTC; these helpers hand
back aware UTC datetimes so the report and LAVA store them as instants.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)
_EPOCH_1970 = datetime(1970, 1, 1, tzinfo=timezone.utc)


def open_key(reg, path):
    """The key at path under the hive root, or None when it is absent."""
    if reg is None:
        return None
    try:
        return reg.open(path)
    except Registry.RegistryKeyNotFoundException:
        return None


def value_of(key, name, default=None):
    """A value's data, or default when the key or the value is absent."""
    if key is None:
        return default
    try:
        return key.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return default


def raw_value(key, name):
    """A value's raw bytes, for types python-registry does not decode."""
    if key is None:
        return None
    try:
        return key.value(name).raw_data()
    except Registry.RegistryValueNotFoundException:
        return None


def filetime_utc(value):
    """A FILETIME count (100 ns intervals since 1601-01-01 UTC) as an aware datetime."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _EPOCH_1601 + timedelta(microseconds=value // 10)
    except (OverflowError, ValueError):
        return ''


def filetime_bytes_utc(raw):
    """The first eight bytes of raw read as a little-endian FILETIME."""
    if isinstance(raw, (bytes, bytearray)) and len(raw) >= 8:
        return filetime_utc(struct.unpack('<Q', bytes(raw[:8]))[0])
    return ''


def unix_utc(value):
    """Seconds since 1970-01-01 UTC as an aware datetime."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _EPOCH_1970 + timedelta(seconds=value)
    except (OverflowError, ValueError):
        return ''


def signed32(value):
    """A REG_DWORD read back as the signed 32-bit integer it stores."""
    if not isinstance(value, int):
        return value
    return value - (1 << 32) if value >= (1 << 31) else value


def key_written_utc(key):
    """A key's last-written time as an aware UTC datetime."""
    if key is None:
        return ''
    stamp = key.timestamp()
    if stamp is None:
        return ''
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp


def current_control_set(system_reg):
    """The ControlSet the Select key names as Current, or ControlSet001."""
    current = value_of(open_key(system_reg, 'Select'), 'Current')
    return f'ControlSet{current:03d}' if isinstance(current, int) else 'ControlSet001'


def user_from_path(path):
    """The folder name after Users in a staged path, or ''."""
    parts = path.replace('\\', '/').split('/')
    for index, part in enumerate(parts):
        if part.lower() == 'users' and index + 1 < len(parts):
            return parts[index + 1]
    return ''


def found_hives(context, *names):
    """Every found file whose basename is one of names, compared without case."""
    wanted = {name.upper() for name in names}
    hives = []
    for found in context.get_files_found():
        found = str(found)
        if os.path.basename(found).upper() in wanted and os.path.isfile(found):
            hives.append(found)
    return hives
