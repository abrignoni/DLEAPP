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
"""

import re
import struct

try:
    import pefile
except ImportError:
    pefile = None

RT_MESSAGETABLE = 11
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
