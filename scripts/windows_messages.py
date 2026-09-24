"""Message-table text for the parameter references in Windows event records.

Author: @AlexisBrignoni, Claude.

An event record can store a data item as a parameter reference, %%n, which a
viewer replaces with message n from the message table of the provider's parameter
file (Microsoft Learn, 'ProviderType complex type',
https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-providertype-complextype).
The message table is a PE resource of type RT_MESSAGETABLE, 11 (Microsoft Learn,
'Resource Types', https://learn.microsoft.com/en-us/windows/win32/menurc/resource-types),
and for the language-specific text it sits in the .mui file beside the parameter
file.

`read_message_table(path)` returns {message id: text} for every message-table
resource in a PE file, using pefile to find the resources. Each resource is a
MESSAGE_RESOURCE_DATA structure: a count of MESSAGE_RESOURCE_BLOCK structures, each
naming a range of message ids and the offset, from the start of the data, of its
MESSAGE_RESOURCE_ENTRY structures; an entry is its own length in bytes, a flags
word (0x0001 for a Unicode string, 0x0000 for ANSI) and the text (Microsoft Learn,
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-message_resource_data,
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-message_resource_block
and https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-message_resource_entry).
An entry with any other flags value is skipped rather than decoded by guesswork.

`message_text(raw)` trims what FormatMessage does not print: the line break at the
end of a message and the %0 escape, which ends a message without a trailing new
line (Microsoft Learn, 'FormatMessage function',
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-formatmessage).

`read_event_value_maps(path, provider_guid)` reads the value maps a provider's event
manifest binds to its event fields. A manifest data item with a `map` attribute has
its integer shown through that name/value map (Microsoft Learn, 'DataDefinitionType
complex type',
https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-datadefinitiontype-complextype),
and the compiled manifest sits in the provider's DLL as the WEVT_TEMPLATE resource.
Its layout follows libyal's 'Windows Event manifest binary format' (libfwevt,
https://github.com/libyal/libfwevt/blob/7bfd3403b1bd1476aefbaf2e94b5562cbf724997/documentation/Windows%20Event%20manifest%20binary%20format.asciidoc):
CRIM header and provider descriptors, a WEVT provider with its element offsets, EVNT
event definitions (identifier, version, template offset), TEMP templates with 20-byte
item descriptors, and VMAP value maps of (value, message identifier) pairs. Two fields
that document leaves open were measured on the pots.dll and
microsoft-windows-kernel-power-events.dll of Windows builds 16299, 17763 and 22621: a
VMAP holds a zero word after its name offset, so its entries start at byte 20 and its
size is 20 plus 8 per entry, and the 32-bit word at byte 8 of an item descriptor is
the offset of the VMAP bound to that item (0 when none is). The message identifiers
resolve through the message table of the DLL's .mui.
"""

import re
import struct
import uuid

try:
    import pefile
except ImportError:
    pefile = None

RT_MESSAGETABLE = 11
WEVT_TEMPLATE = 'WEVT_TEMPLATE'
REFERENCE = re.compile(r'%%(\d+)')

_UNICODE = 0x0001
_ANSI = 0x0000


def message_text(raw):
    """The text FormatMessage prints for a message, without its line ending or %0."""
    text = raw.rstrip('\x00').rstrip('\r\n')
    if text.endswith('%0'):
        text = text[:-2]
    return text


def parse_message_table(data):
    """{message id: text} from the bytes of one MESSAGE_RESOURCE_DATA structure."""
    messages = {}
    (blocks,) = struct.unpack_from('<I', data, 0)
    for block in range(blocks):
        low, high, offset = struct.unpack_from('<III', data, 4 + 12 * block)
        for message_id in range(low, high + 1):
            length, flags = struct.unpack_from('<HH', data, offset)
            if length < 4:
                break  # a zero length would never advance; the block is malformed
            raw = data[offset + 4:offset + length]
            offset += length
            if flags == _UNICODE:
                text = raw.decode('utf-16-le', 'replace')
            elif flags == _ANSI:
                text = raw.decode('cp1252', 'replace')
            else:
                continue
            messages[message_id] = message_text(text)
    return messages


def _entries(entry):
    """The entries of the resource directory below `entry`, or () for a leaf."""
    directory = getattr(entry, 'directory', None)
    return directory.entries if directory is not None else ()


def read_message_table(path):
    """{message id: text} from every RT_MESSAGETABLE resource in a PE file.

    Returns {} when pefile is not installed, the file is not a PE, or it carries no
    message table. A later resource does not replace an id an earlier one gave.
    """
    if pefile is None:
        return {}
    messages = {}
    try:
        pe = pefile.PE(path, fast_load=True)
    except (pefile.PEFormatError, OSError):
        return {}
    try:
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        resources = getattr(pe, 'DIRECTORY_ENTRY_RESOURCE', None)
        for type_entry in (resources.entries if resources else ()):
            if type_entry.id != RT_MESSAGETABLE:
                continue
            for name_entry in _entries(type_entry):
                for language_entry in _entries(name_entry):
                    location = language_entry.data.struct
                    try:
                        table = parse_message_table(
                            pe.get_data(location.OffsetToData, location.Size))
                    except (struct.error, pefile.PEFormatError):
                        continue
                    for message_id, text in table.items():
                        messages.setdefault(message_id, text)
    finally:
        pe.close()
    return messages


def _manifest_string(data, offset):
    """A manifest string: its size in bytes, the size field included, then UTF-16LE."""
    (size,) = struct.unpack_from('<I', data, offset)
    if size < 4 or offset + size > len(data):
        raise ValueError('manifest string runs past the manifest')
    return data[offset + 4:offset + size].decode('utf-16-le').split('\x00')[0]


def _value_map(data, offset):
    """{value: message identifier} from the VMAP at offset, or None for another element."""
    if data[offset:offset + 4] != b'VMAP':
        return None
    size, _name, _zero, count = struct.unpack_from('<IIII', data, offset + 4)
    if size != 20 + 8 * count:
        raise ValueError('VMAP size does not fit its entries')
    return dict(struct.unpack_from('<II', data, offset + 20 + 8 * entry) for entry in range(count))


def _provider_elements(data, provider_guid):
    """{element signature: offset} for the provider's WEVT entry, or {} when absent."""
    wanted = uuid.UUID(provider_guid).bytes_le
    (providers,) = struct.unpack_from('<I', data, 12)
    for index in range(providers):
        descriptor = 16 + 20 * index
        if data[descriptor:descriptor + 16] != wanted:
            continue
        (provider,) = struct.unpack_from('<I', data, descriptor + 16)
        if data[provider:provider + 4] != b'WEVT':
            return {}
        (count,) = struct.unpack_from('<I', data, provider + 12)
        elements = {}
        for element in range(count):
            (offset,) = struct.unpack_from('<I', data, provider + 20 + 8 * element)
            elements[bytes(data[offset:offset + 4])] = offset
        return elements
    return {}


def _template_value_maps(data, template):
    """{field name: {value: message identifier}} for the mapped items of one TEMP."""
    items, _names, first = struct.unpack_from('<III', data, template + 8)
    fields = {}
    for item in range(items):
        (map_offset,) = struct.unpack_from('<I', data, first + 20 * item + 8)
        (name_offset,) = struct.unpack_from('<I', data, first + 20 * item + 16)
        values = _value_map(data, map_offset) if map_offset else None
        if values is not None:
            fields[_manifest_string(data, name_offset)] = values
    return fields


def parse_event_manifest(data, provider_guid):
    """{(event id, version): {field name: {value: message identifier}}} for one provider.

    `data` is a WEVT_TEMPLATE resource. Only fields bound to a value map appear, so an
    event with none is left out. Returns {} when the resource holds no manifest for the
    provider; a structure that does not fit raises struct.error or ValueError.
    """
    if data[:4] != b'CRIM':
        return {}
    events = _provider_elements(data, provider_guid).get(b'EVNT')
    if events is None:
        return {}
    result = {}
    (count,) = struct.unpack_from('<I', data, events + 8)
    for number in range(count):
        definition = events + 16 + 48 * number
        event_id, version = struct.unpack_from('<HB', data, definition)
        (template,) = struct.unpack_from('<I', data, definition + 20)
        if template and data[template:template + 4] == b'TEMP':
            fields = _template_value_maps(data, template)
            if fields:
                result[(event_id, version)] = fields
    return result


def read_event_value_maps(path, provider_guid):
    """parse_event_manifest for the WEVT_TEMPLATE resource of a PE file.

    Returns {} when pefile is not installed, the file is not a PE, or it carries no
    event manifest for the provider that parses.
    """
    if pefile is None:
        return {}
    try:
        pe = pefile.PE(path, fast_load=True)
    except (pefile.PEFormatError, OSError):
        return {}
    try:
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        resources = getattr(pe, 'DIRECTORY_ENTRY_RESOURCE', None)
        for type_entry in (resources.entries if resources else ()):
            if type_entry.name is None or str(type_entry.name) != WEVT_TEMPLATE:
                continue
            for name_entry in _entries(type_entry):
                for language_entry in _entries(name_entry):
                    location = language_entry.data.struct
                    try:
                        maps = parse_event_manifest(
                            pe.get_data(location.OffsetToData, location.Size), provider_guid)
                    except (struct.error, ValueError, UnicodeDecodeError, pefile.PEFormatError):
                        continue
                    if maps:
                        return maps
    finally:
        pe.close()
    return {}
