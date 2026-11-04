"""Helpers shared by the DLEAPP Windows registry artifacts.

Author: @AlexisBrignoni, Claude.

Offline hives are read with the vendored regfprobe (scripts/vendor/regfprobe.py) through
its python-registry shaped layer, CompatRegistry. Registry below stands where
python-registry's Registry module stood, so code written against python-registry 1.3.1
reads the same names: Registry.Registry(...), the two not-found exceptions, and the REG_*
numbers as Registry.RegSZ, Registry.RegBin and the rest. Registry.RegistryException is the
error for a file that is not a hive.

Key timestamps are the key's last-written FILETIME as a naive datetime in UTC, rounded to the
microsecond as python-registry rounds it; these helpers hand back aware UTC datetimes so the
report and LAVA store them as instants.

open_hive replays a dirty hive's .LOG1 and .LOG2 transaction logs, in either the format
Windows 8.1 and later write or the older one (scripts/registry_recovery.py), and logs each
damaged structure regfprobe skips while the hive is read.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.context import Context
from scripts.ilapfuncs import logfunc
from scripts.registry_recovery import recover

from scripts.vendor import regfprobe


class Registry:  # pylint: disable=too-few-public-methods
    """python-registry's Registry module, as far as DLEAPP uses it, answered by regfprobe."""

    RegistryKeyNotFoundException = regfprobe.CompatRegistry.RegistryKeyNotFoundException
    RegistryValueNotFoundException = regfprobe.CompatRegistry.RegistryValueNotFoundException
    RegistryException = regfprobe.CompatRegistry.RegistryException
    RegNone, RegSZ, RegExpandSZ, RegBin = 0, 1, 2, 3
    RegDWord, RegBigEndian, RegLink, RegMultiSZ = 4, 5, 6, 7
    RegResourceList, RegFullResourceDescriptor, RegResourceRequirementsList, RegQWord = 8, 9, 10, 11

    @staticmethod
    def Registry(source):  # pylint: disable=invalid-name
        """A hive read from a path or an open file, as it is: no transaction log is applied
        (as python-registry read it). open_hive is the way to read a hive with its logs."""
        return regfprobe.CompatRegistry(source, recover=False)

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
    """A value's raw bytes, as stored."""
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
    """A python-registry shaped view of a hive, its transaction logs replayed first when it is dirty.

    The logs are read from beside the hive, so an artifact declares them in its paths. The run
    log names each hive replayed, each dirty hive read as it is and why, and each damaged
    structure skipped while it is read.
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
    label = (context or Context).get_relative_path(str(path))
    if summary['state'] == 'recovered' and summary.get('format') == 'old':
        name, sequence, _last = summary['applied'][0]
        pages = f"{summary['pages']} dirty {'page' if summary['pages'] == 1 else 'pages'}"
        logfunc(f"Registry: {label} was dirty; wrote the {pages} of {name}, a log in the older format, "
                f"sequence {sequence}.")
    elif summary['state'] == 'recovered':
        sources = ' and '.join(name for name, _first, _last in summary['applied'])
        entries = f"{summary['entries']} transaction log {'entry' if summary['entries'] == 1 else 'entries'}"
        logfunc(f"Registry: {label} was dirty; replayed {entries}, sequence "
                f"{summary['applied'][0][1]} to {summary['applied'][-1][2]}, from {sources}.")
    elif summary['state'] == 'dirty, not recovered':
        reasons = '; '.join(f'{name}: {why}' for name, why in summary['reasons'].items())
        logfunc(f"Registry: {label} is dirty and was read as it is "
                f"({reasons or 'no transaction log beside it'}).")

    def skipped(kind, offset, reason):
        logfunc(f"Registry: {label}: skipped a damaged {kind} structure at cell 0x{offset:x} ({reason}).")
    return regfprobe.CompatRegistry(regfprobe.Hive(data, recover=False, name=os.path.basename(str(path)),
                                                   on_fault=skipped))
