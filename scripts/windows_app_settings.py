"""Reader for the settings.dat hive of a Windows packaged (UWP or MSIX) app.

Author: @AlexisBrignoni, Claude.

A packaged app keeps its ApplicationData settings in Settings/settings.dat under its
package folder, AppData/Local/Packages/<package family name>. The file is an offline
registry hive; the hive is opened with open_hive (scripts/windows_registry.py), which
replays a dirty hive's .LOG1 and .LOG2 transaction logs first.

The values do not use the ordinary registry types. Their type is 0x5F5E100 plus a
type number, and the last eight bytes of every such value are a FILETIME. The value
types and the layout of a composite value are those python-registry's SettingsParse.py
decodes (Yogesh Khatri, MIT; type numbers at
https://github.com/williballenthin/python-registry/blob/4edb5d1b72597faf257878060aa68baa9c5b28df/Registry/SettingsParse.py#L38-L72,
values at L96-L137, the composite stream at L139-L165, and the mask that removes 0x100
and the trailing eight bytes at
https://github.com/williballenthin/python-registry/blob/4edb5d1b72597faf257878060aa68baa9c5b28df/Registry/RegistryParse.py#L1202-L1211).
python-registry drops the trailing eight bytes; this reader keeps them. ogmini's
Notepad-State-Library (MIT) describes them as the FILETIME of the setting's change
(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L298-L307),
and Damir Arh describes the same eight-byte suffix on every value
(https://www.damirscorner.com/blog/posts/20150117-ManipulatingSettingsDatFileWithSettingsFromWindowsStoreApps.html).
The code here is DLEAPP's own, written from those descriptions.

Type numbers 0x01 to 0x13 carry the names Windows.Foundation.PropertyType gives the
same numbers (https://learn.microsoft.com/en-us/uwp/api/windows.foundation.propertytype);
0x14 to 0x1F are the arrays in the order SettingsParse.py lists them. Point, Size and
Rect (0x11 to 0x13), which SettingsParse.py leaves undecoded, are returned as hex.
"""

import os
import struct
import uuid
from datetime import timedelta

from scripts.windows_registry import filetime_utc, key_written_utc, open_hive, user_from_path

try:
    from Registry.RegistryParse import RegistryException
except ImportError:
    RegistryException = OSError

# What reading a damaged or truncated hive can raise, from the replay or from python-registry.
HIVE_ERRORS = (OSError, ValueError, IndexError, struct.error, RegistryException)

TYPE_BASE = 0x5F5E100

TYPE_NAMES = {
    0x01: 'UInt8', 0x02: 'Int16', 0x03: 'UInt16', 0x04: 'Int32', 0x05: 'UInt32',
    0x06: 'Int64', 0x07: 'UInt64', 0x08: 'Single', 0x09: 'Double', 0x0A: 'Char16',
    0x0B: 'Boolean', 0x0C: 'String', 0x0D: 'Composite', 0x0E: 'DateTime',
    0x0F: 'TimeSpan', 0x10: 'Guid', 0x11: 'Point', 0x12: 'Size', 0x13: 'Rect',
    0x14: 'UInt8Array', 0x15: 'Int16Array', 0x16: 'UInt16Array', 0x17: 'Int32Array',
    0x18: 'UInt32Array', 0x19: 'Int64Array', 0x1A: 'UInt64Array', 0x1B: 'SingleArray',
    0x1C: 'DoubleArray', 0x1D: 'Char16Array', 0x1E: 'BooleanArray', 0x1F: 'StringArray',
}

_SCALARS = {0x01: '<B', 0x02: '<h', 0x03: '<H', 0x04: '<i', 0x05: '<I', 0x06: '<q',
            0x07: '<Q', 0x08: '<f', 0x09: '<d'}
_ARRAYS = {0x14: 'B', 0x15: 'h', 0x16: 'H', 0x17: 'i', 0x18: 'I', 0x19: 'q', 0x1A: 'Q',
           0x1B: 'f', 0x1C: 'd'}


class SettingsError(ValueError):
    """A value whose bytes do not fit the layout its type names."""


class Setting:
    """One decoded value: name, type number and name, value, and its stored FILETIME.

    type_number is None for a value of an ordinary registry type, whose value is what
    python-registry returns and whose written time is blank. For a composite, value is
    a dict of name to (type name, value); its members carry no time of their own.
    """

    __slots__ = ('name', 'stored_type', 'type_number', 'type_name', 'value', 'written',
                 'error')

    def __init__(self, name, stored_type, type_number, type_name, value, written, error=''):
        self.name = name
        self.stored_type = stored_type
        self.type_number = type_number
        self.type_name = type_name
        self.value = value
        self.written = written
        self.error = error

    def text(self):
        """The value as one line of text, composites and arrays included."""
        return value_text(self.value)


def value_text(value):
    """A decoded value as text: lists joined by ', ', composites as name=value pairs."""
    if isinstance(value, dict):
        return '; '.join(f'{name}={value_text(item[1])}' for name, item in value.items())
    if isinstance(value, (list, tuple)):
        return ', '.join(value_text(item) for item in value)
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return '' if value is None else str(value)


def _utf16(data):
    if len(data) % 2:
        raise SettingsError(f'a UTF-16 string of odd length {len(data)}')
    return data.decode('utf-16-le', errors='replace').rstrip('\x00')


def _string_array(data):
    strings = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise SettingsError('a string array ends inside a length field')
        size = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        if pos + size > len(data):
            raise SettingsError('a string array item runs past the value')
        strings.append(_utf16(data[pos:pos + size]))
        pos += size
    return strings


def decode_data(number, data):
    """The value of type number `number` stored in `data` (its trailing FILETIME removed)."""
    if number in _SCALARS:
        fmt = _SCALARS[number]
        if len(data) < struct.calcsize(fmt):
            raise SettingsError(f'{TYPE_NAMES[number]} needs {struct.calcsize(fmt)} bytes, '
                                f'{len(data)} stored')
        return struct.unpack_from(fmt, data, 0)[0]
    if number == 0x0A:
        return _utf16(data[:2])
    if number == 0x0B:
        if not data:
            raise SettingsError('Boolean with no byte')
        return data[0] != 0
    if number in (0x0C, 0x1D):
        return _utf16(data)
    if number == 0x0D:
        return decode_composite(data)
    if number in (0x0E, 0x0F):
        if len(data) < 8:
            raise SettingsError(f'{TYPE_NAMES[number]} needs 8 bytes, {len(data)} stored')
        ticks = struct.unpack_from('<q', data, 0)[0]
        if number == 0x0E:
            return filetime_utc(ticks)
        return timedelta(microseconds=ticks / 10)
    if number == 0x10:
        if len(data) < 16:
            raise SettingsError(f'Guid needs 16 bytes, {len(data)} stored')
        return str(uuid.UUID(bytes_le=bytes(data[:16])))
    if number in _ARRAYS:
        size = struct.calcsize('<' + _ARRAYS[number])
        if len(data) % size:
            raise SettingsError(f'{TYPE_NAMES[number]} of {len(data)} bytes is not a '
                                f'multiple of {size}')
        return list(struct.unpack_from(f'<{len(data) // size}{_ARRAYS[number]}', data, 0))
    if number == 0x1E:
        return [byte != 0 for byte in data]
    if number == 0x1F:
        return _string_array(data)
    return bytes(data).hex()


def decode_composite(data):
    """A composite value's members, {name: (type name, value)}, in stored order.

    Each member is a 32-bit total length, a 32-bit type number, a 32-bit name length in
    UTF-16 code units, the name and its terminating NUL, then the data; the next member
    starts at the next multiple of 8 after this one ends.
    """
    members = {}
    pos = 0
    while pos < len(data):
        if pos + 12 > len(data):
            raise SettingsError('a composite member header runs past the value')
        length, number, name_units = struct.unpack_from('<III', data, pos)
        body = pos + 12 + (name_units + 1) * 2
        if length < 12 or pos + length > len(data) or body > pos + length:
            raise SettingsError(f'a composite member of length {length} does not fit')
        name = data[pos + 12:pos + 12 + name_units * 2].decode('utf-16-le', errors='replace')
        try:
            value = decode_data(number, data[body:pos + length])
        except (SettingsError, struct.error, ValueError) as ex:
            value = f'undecoded ({ex}): {bytes(data[body:pos + length]).hex()}'
        members[name] = (TYPE_NAMES.get(number, f'0x{number:X}'), value)
        pos += length
        if pos % 8:
            pos += 8 - pos % 8
    return members


def stored_type_of(value):
    """The value's type exactly as the hive stores it.

    python-registry's value_type() keeps only the low twelve bits, which loses the
    0x5F5E100 base, so the full 32-bit field of the value record is read here.
    """
    return value._vkrecord.unpack_dword(0xC)  # pylint: disable=protected-access


def decode(value):
    """A Setting for one python-registry value."""
    raw_type = stored_type_of(value)
    name = value.name()
    number = raw_type - TYPE_BASE
    if number not in TYPE_NAMES:
        try:
            plain = value.value()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # python-registry raises its own exception classes for types it cannot read.
            return Setting(name, raw_type, None, f'0x{raw_type:X}', '', '', str(ex))
        return Setting(name, raw_type, None, f'0x{raw_type:X}', plain, '')
    raw = bytes(value.raw_data())
    if len(raw) < 8:
        return Setting(name, raw_type, number, TYPE_NAMES[number], raw.hex(), '',
                       f'{len(raw)} bytes, too short for the trailing FILETIME')
    written = filetime_utc(struct.unpack_from('<Q', raw, len(raw) - 8)[0])
    try:
        decoded = decode_data(number, raw[:-8])
    except (SettingsError, struct.error, ValueError) as ex:
        return Setting(name, raw_type, number, TYPE_NAMES[number], raw[:-8].hex(), written,
                       str(ex))
    return Setting(name, raw_type, number, TYPE_NAMES[number], decoded, written)


def open_settings(path, context=None):
    """The settings hive at path, opened as open_hive opens any hive."""
    return open_hive(path, context)


def settings(key):
    """{value name: Setting} for every value of a key, or {} when the key is None."""
    if key is None:
        return {}
    return {value.name(): decode(value) for value in key.values()}


def package_hives(context, family):
    """(staged path, relative path, package folder, user) of each package settings hive.

    A hive counts only when its path ends Packages/<family>_<publisher id>/Settings/
    settings.dat, compared without case, so a settings.dat deeper in the package folder,
    or one in another package, is not taken. Each staged path is taken once.
    """
    prefix = family.lower() + '_'
    found, seen = [], set()
    for item in context.get_files_found():
        path = str(item)
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        relative = context.get_relative_path(path)
        parts = relative.replace('\\', '/').split('/')
        if len(parts) < 4 or parts[-1].lower() != 'settings.dat' \
                or parts[-2].lower() != 'settings' or parts[-4].lower() != 'packages' \
                or not parts[-3].lower().startswith(prefix):
            continue
        found.append((path, relative, parts[-3], user_from_path(relative)))
    return sorted(found, key=lambda entry: entry[1])


def keys(reg):
    """(path, key, last-written time) for every key of the hive, the root first as ''."""
    root = reg.root()
    yield '', root, key_written_utc(root)
    for sub in root.subkeys():
        yield from _below(sub, sub.name())


def _below(key, path):
    yield path, key, key_written_utc(key)
    for sub in key.subkeys():
        yield from _below(sub, f'{path}\\{sub.name()}')
