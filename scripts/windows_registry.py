"""Helpers shared by the DLEAPP Windows registry artifacts.

Author: @AlexisBrignoni, Claude.

Offline hives are read with python-registry. Its key timestamps are the key's
last-written FILETIME, returned as a naive datetime in UTC; these helpers hand
back aware UTC datetimes so the report and LAVA store them as instants.

open_hive replays a dirty hive's .LOG1 and .LOG2 transaction logs before
python-registry reads it (scripts/registry_recovery.py).
"""

import io
import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import logfunc
from scripts.registry_recovery import recover

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


def user_from_path(relative):
    """The folder name after the first folder named Users in a path, or ''.

    Pass the path within the extraction (context.get_relative_path), never the staged
    path: the staged path begins with the examiner's own report folder, which on macOS
    and Windows usually sits under the examiner's Users folder.
    """
    parts = relative.replace('\\', '/').split('/')
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


_LOG_SUFFIXES = ('.LOG1', '.LOG2')


def is_transaction_log(path):
    """Whether a file is a hive transaction log (.LOG, .LOG1 or .LOG2), by its name."""
    return os.path.basename(str(path)).upper().endswith(('.LOG', '.LOG1', '.LOG2'))


def hive_logs(path):
    """The .LOG1 and .LOG2 files staged beside a hive, matched on its name without case."""
    folder, name = os.path.split(str(path))
    wanted = {(name + suffix).upper() for suffix in _LOG_SUFFIXES}
    try:
        entries = sorted(os.listdir(folder))
    except OSError:
        return []
    return [os.path.join(folder, entry) for entry in entries
            if entry.upper() in wanted and os.path.isfile(os.path.join(folder, entry))]


def open_hive(path, context=None):
    """python-registry's view of a hive, its transaction logs replayed first when it is dirty.

    The logs are read from beside the hive, so an artifact declares them in its paths. The run
    log names each hive replayed, and each dirty hive read as it is and why.
    """
    with open(path, 'rb') as handle:
        primary = handle.read()
    logs = []
    for log in hive_logs(path):
        try:
            with open(log, 'rb') as handle:
                logs.append((os.path.basename(log), handle.read()))
        except OSError:
            continue
    data, summary = recover(primary, logs)
    label = context.get_relative_path(path) if context is not None else os.path.basename(str(path))
    if summary['state'] == 'recovered':
        sources = ' and '.join(name for name, _first, _last in summary['applied'])
        logfunc(f"Registry: {label} was dirty; replayed {summary['entries']} transaction log "
                f"entr(ies), sequence {summary['applied'][0][1]} to {summary['applied'][-1][2]}, "
                f"from {sources}.")
    elif summary['state'] == 'dirty, not recovered':
        reasons = '; '.join(f'{name}: {why}' for name, why in summary['reasons'].items())
        logfunc(f"Registry: {label} is dirty and was read as it is "
                f"({reasons or 'no transaction log beside it'}).")
    return Registry.Registry(io.BytesIO(data))
