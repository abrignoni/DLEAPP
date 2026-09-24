"""Message-table text for Windows event parameter references (%%n).

The Defender artifacts give a field that stores a reference such as %%802 the text of
that message from the English MpEvMsg.dll.mui of the same volume. These tests build a
PE file carrying a message-table resource, laid out as winnt.h and Microsoft's
MESSAGE_RESOURCE_* documentation describe, rather than committing a Microsoft binary,
and check both the reader and which file a record's reference is resolved against.
"""
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_messages  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsDefenderEvents  # pylint: disable=wrong-import-position

UNICODE, ANSI = 0x0001, 0x0000


def message_table(blocks):
    """MESSAGE_RESOURCE_DATA bytes for [(low id, [(flags, text), ...]), ...]."""
    headers, entries = b'', b''
    offset = 4 + 12 * len(blocks)
    for low, items in blocks:
        chunk = b''
        for flags, text in items:
            raw = text.encode('utf-16-le') + b'\x00\x00' if flags == UNICODE else \
                text.encode('cp1252') + b'\x00'
            raw += b'\x00' * (-(4 + len(raw)) % 4)
            chunk += struct.pack('<HH', 4 + len(raw), flags) + raw
        headers += struct.pack('<III', low, low + len(items) - 1, offset)
        entries += chunk
        offset += len(chunk)
    return struct.pack('<I', len(blocks)) + headers + entries


def pe_with_resource(data, type_id=windows_messages.RT_MESSAGETABLE, language=1033):
    """A 32-bit PE whose one section holds a resource tree: type, name 1, language, data."""
    rva, raw_offset = 0x1000, 0x200

    def directory(entry_id, target):
        return struct.pack('<IIHHHH', 0, 0, 0, 0, 0, 1) + struct.pack('<II', entry_id, target)

    tree = (directory(type_id, 0x80000000 | 24) + directory(1, 0x80000000 | 48)
            + directory(language, 72) + struct.pack('<IIII', rva + 88, len(data), 0, 0))
    section = tree + data
    padded = section + b'\x00' * (-len(section) % 0x200)
    directories = [(0, 0)] * 16
    directories[2] = (rva, len(section))
    optional = struct.pack(
        '<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII', 0x10b, 0, 0, 0, len(padded), 0, 0, 0, 0,
        0x10000000, 0x1000, 0x200, 6, 0, 0, 0, 6, 0, 0,
        rva + (len(padded) + 0xfff) // 0x1000 * 0x1000, raw_offset, 0, 2, 0,
        0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    optional += b''.join(struct.pack('<II', *entry) for entry in directories)
    coff = struct.pack('<HHIIIHH', 0x14c, 1, 0, 0, 0, len(optional), 0x2102)
    section_header = struct.pack('<8sIIIIIIHHI', b'.rsrc', len(section), rva, len(padded),
                                 raw_offset, 0, 0, 0, 0, 0x40000040)
    headers = b'MZ' + b'\x00' * 58 + struct.pack('<I', 0x40) + b'PE\x00\x00' + coff \
        + optional + section_header
    return headers + b'\x00' * (raw_offset - len(headers)) + padded


class _TempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, relative, data):
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)


class TestReadMessageTable(_TempDir):
    """The reader returns what FormatMessage prints, for every documented encoding."""

    def test_unicode_and_ansi_entries_across_blocks(self):
        path = self.write('MpEvMsg.dll.mui', pe_with_resource(message_table([
            (802, [(UNICODE, 'Antimalware%0\r\n'), (UNICODE, 'Antispyware%0\r\n')]),
            (806, [(ANSI, 'Quick Scan%0\r\n')]),
        ])))
        self.assertEqual(windows_messages.read_message_table(path),
                         {802: 'Antimalware', 803: 'Antispyware', 806: 'Quick Scan'})

    def test_an_entry_with_undocumented_flags_is_skipped(self):
        path = self.write('x.mui', pe_with_resource(message_table([
            (1, [(UNICODE, 'one%0\r\n'), (0x0002, 'two%0\r\n'), (UNICODE, 'three%0\r\n')]),
        ])))
        self.assertEqual(windows_messages.read_message_table(path), {1: 'one', 3: 'three'})

    def test_other_resource_types_are_not_message_tables(self):
        data = message_table([(1, [(UNICODE, 'one%0\r\n')])])
        path = self.write('x.mui', pe_with_resource(data, type_id=6))  # RT_STRING
        self.assertEqual(windows_messages.read_message_table(path), {})

    def test_a_file_that_is_not_a_pe_or_is_missing_gives_nothing(self):
        self.assertEqual(windows_messages.read_message_table(self.write('x.mui', b'text')), {})
        self.assertEqual(windows_messages.read_message_table(str(self.tmp / 'absent.mui')), {})

    def test_a_zero_length_entry_ends_its_block(self):
        data = struct.pack('<IIII', 1, 5, 9, 16) + struct.pack('<HH', 0, UNICODE)
        self.assertEqual(windows_messages.parse_message_table(data), {})

    def test_message_text_drops_only_the_line_ending_and_the_final_escape(self):
        self.assertEqual(windows_messages.message_text('Antimalware%0\r\n'), 'Antimalware')
        self.assertEqual(windows_messages.message_text('Line one\r\n'), 'Line one')
        self.assertEqual(windows_messages.message_text('100%0 of %1%0'), '100%0 of %1')


class _Context:
    def __init__(self, data_folder, files):
        self.data_folder = data_folder
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.data_folder)


class _Record:
    def __init__(self, source, version):
        self.source = source
        self.fields = {'Product Version': version}

    def get(self, name):
        return self.fields.get(name, '')


class TestDefenderParameterText(_TempDir):
    """A reference takes its text from the message file of the record's own volume."""

    INBOX = 'Program Files/Windows Defender/en-US/MpEvMsg.dll.mui'
    PLATFORM = 'ProgramData/Microsoft/Windows Defender/Platform/{}-0/en-US/MpEvMsg.dll.mui'
    LOG = 'Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx'

    def setUp(self):
        super().setUp()
        files = []
        for relative, text in (('lba0/' + self.INBOX, 'Inbox'),
                               ('lba0/' + self.PLATFORM.format('4.18.1'), 'Platform'),
                               ('lba1/' + self.INBOX, 'Other volume')):
            files.append(self.write('data/' + relative, pe_with_resource(
                message_table([(802, [(UNICODE, text + '%0\r\n')])]))))
        self.log0 = str(self.tmp / 'data/lba0' / self.LOG)
        self.log1 = str(self.tmp / 'data/lba1' / self.LOG)
        self.text = windowsDefenderEvents._ParameterText(  # pylint: disable=protected-access
            _Context(str(self.tmp / 'data'), files), 'test')

    def test_the_platform_copy_named_for_the_records_version_comes_first(self):
        self.assertEqual(self.text.text(_Record(self.log0, '4.18.1'), '%%802'),
                         'Platform (%%802)')

    def test_the_program_files_copy_serves_a_version_with_no_platform_folder(self):
        self.assertEqual(self.text.text(_Record(self.log0, '4.18.9'), '%%802'),
                         'Inbox (%%802)')

    def test_each_volume_uses_its_own_files(self):
        self.assertEqual(self.text.text(_Record(self.log1, '4.18.1'), '%%802'),
                         'Other volume (%%802)')

    def test_what_no_file_resolves_is_kept_as_stored_and_counted(self):
        self.assertEqual(self.text.text(_Record(self.log0, '4.18.1'), '%%999'), '%%999')
        elsewhere = str(self.tmp / 'data/lba2' / self.LOG)
        self.assertEqual(self.text.text(_Record(elsewhere, '4.18.1'), '%%802'), '%%802')
        self.assertEqual(self.text.kept, 2)

    def test_values_that_are_not_references_are_untouched(self):
        record = _Record(self.log0, '4.18.1')
        for value in ('Quick Scan', '', '%%802 and more', '50%%', None):
            self.assertEqual(self.text.text(record, value), value)
        self.assertEqual(self.text.kept, 0)

    def test_without_pefile_references_are_kept_as_stored(self):
        original = windows_messages.pefile
        windows_messages.pefile = None
        self.addCleanup(setattr, windows_messages, 'pefile', original)
        self.assertEqual(self.text.text(_Record(self.log0, '4.18.1'), '%%802'), '%%802')
        self.assertEqual(self.text.kept, 1)

    def test_the_files_used_are_named_for_the_source_path(self):
        self.text.text(_Record(self.log0, '4.18.1'), '%%802')
        self.text.text(_Record(self.log1, '4.18.1'), '%%802')
        self.assertEqual([os.path.relpath(p, self.tmp / 'data') for p in self.text.files()],
                         ['lba0/' + self.PLATFORM.format('4.18.1'), 'lba1/' + self.INBOX])


if __name__ == '__main__':
    unittest.main()
