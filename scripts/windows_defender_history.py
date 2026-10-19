"""Read Microsoft Defender DetectionHistory files.

The layout follows Joachim Metz's "Windows Defender scan DetectionHistory file
format" (libyal/dtformats) and plaso's windefender_history parser, both cited in
the artifact notes. This is an independent implementation; no code was copied.

A file is a run of values. Each value is a 32-bit data size, a 32-bit data type,
the data, then padding to the next multiple of 8 bytes from the start of the file.
A string value "Magic.Version:1.2" separates the sets of values: before the
first separator, the threat identifier and the detection GUID; after it, the
threat set; after each later separator, one resource set.
"""

import struct
import uuid
from datetime import datetime, timedelta, timezone

SEPARATOR = 'Magic.Version:1.2'

TYPE_INTEGER_32 = (0x00, 0x05, 0x06)
TYPE_INTEGER_64 = 0x08
TYPE_FILETIME = 0x0A
TYPE_STRING = 0x15
TYPE_GUID = 0x1E
TYPE_BINARY = 0x28

_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)

# Threat tracking value types (dtformats, "Threat tracking value").
_TRACK_32 = 0x03
_TRACK_64 = 0x04
_TRACK_8 = 0x05
_TRACK_STRING = 0x06
_TRACK_5_BYTES = 0x07


class Value:  # pylint: disable=too-few-public-methods
    """One value: its offset, data type and decoded data (raw bytes when not decoded)."""

    def __init__(self, offset, data_type, data, decoded):
        self.offset = offset
        self.data_type = data_type
        self.data = data
        self.decoded = decoded


def filetime_utc(value):
    """A FILETIME count as an aware UTC datetime, cut to whole microseconds; '' for 0."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _EPOCH_1601 + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def _decode(data_type, data):
    if data_type in TYPE_INTEGER_32 and len(data) == 4:
        return struct.unpack('<I', data)[0]
    if data_type == TYPE_INTEGER_64 and len(data) == 8:
        return struct.unpack('<Q', data)[0]
    if data_type == TYPE_FILETIME and len(data) == 8:
        return struct.unpack('<Q', data)[0]
    if data_type == TYPE_GUID and len(data) == 16:
        return str(uuid.UUID(bytes_le=bytes(data)))
    if data_type == TYPE_STRING and len(data) % 2 == 0:
        text = data.decode('utf-16-le', errors='replace')
        return text[:-1] if text.endswith('\x00') else text
    return bytes(data)


def read_values(data):
    """The values of a file, and a note that is '' when they end exactly at its size."""
    values = []
    offset = 0
    while offset < len(data):
        if offset + 8 > len(data):
            return values, f'{len(data) - offset} bytes at offset {offset} too short for a value'
        size, data_type = struct.unpack_from('<II', data, offset)
        end = offset + 8 + size
        if end > len(data):
            return values, (f'value at offset {offset} declares {size} bytes, past the end of '
                            f'the file')
        raw = data[offset + 8:end]
        values.append(Value(offset, data_type, raw, _decode(data_type, raw)))
        offset = min(len(data), (end + 7) // 8 * 8)
    return values, ''


def read_threat_tracking(data):
    """Threat tracking data as {key: value}, and a note that is '' when it read cleanly."""
    values = {}
    if len(data) < 4:
        return values, 'threat tracking data shorter than 4 bytes'
    first = struct.unpack_from('<I', data, 0)[0]
    if first == 1:
        if len(data) < 20:
            return values, 'threat tracking header shorter than 20 bytes'
        _, header_size, _, total_size, _ = struct.unpack_from('<5I', data, 0)
        offset, end = header_size + 4, total_size
    else:
        offset, end = 4, first
    end = min(end, len(data))
    read_any = offset < end
    while offset < end:
        try:
            key_size = struct.unpack_from('<I', data, offset)[0]
            key = data[offset + 4:offset + 4 + key_size].decode('utf-16-le').rstrip('\x00')
            offset += 4 + key_size
            value_type = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            if value_type == _TRACK_STRING:
                text_size = struct.unpack_from('<I', data, offset)[0]
                value = data[offset + 4:offset + 4 + text_size].decode('utf-16-le').rstrip('\x00')
                offset += 4 + text_size
            elif value_type == _TRACK_32:
                value = struct.unpack_from('<I', data, offset)[0]
                offset += 4
            elif value_type == _TRACK_64:
                value = struct.unpack_from('<Q', data, offset)[0]
                offset += 8
            elif value_type == _TRACK_8:
                value = data[offset]
                offset += 1
            elif value_type == _TRACK_5_BYTES:
                value = bytes(data[offset:offset + 5])
                offset += 5
            else:
                return values, f'threat tracking value type {value_type} not in the layout'
        except (struct.error, IndexError, UnicodeDecodeError):
            return values, 'threat tracking data ends inside a value'
        values[key] = value
    if read_any and offset > end:
        return values, 'threat tracking values run past their declared size'
    return values, ''


class Detection:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """The sets of one DetectionHistory file."""

    def __init__(self, values):
        self.head = []
        self.threat = []
        self.resources = []
        current = self.head
        for value in values:
            if value.data_type == TYPE_STRING and value.decoded == SEPARATOR:
                if current is self.head:
                    current = self.threat
                else:
                    current = []
                    self.resources.append(current)
                continue
            current.append(value)

    @staticmethod
    def at(values, index, *types):
        """The decoded value at index when its type is one of types, else None."""
        if index < len(values) and values[index].data_type in types:
            return values[index].decoded
        return None
