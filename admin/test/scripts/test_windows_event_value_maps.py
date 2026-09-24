"""Value maps an event manifest binds to event fields, and the power events' use of them.

The System Power Events artifact names the number a Kernel-Power 42 record (Reason)
or a Power-Troubleshooter 1 record (WakeSourceType) stores, from the value map in the
provider's DLL beside the log and the English .mui beside that DLL. These tests build
the WEVT_TEMPLATE and message-table resources in PE files, laid out as libfwevt
describes with the two fields measured on Windows builds 16299, 17763 and 22621 (the
zero word in a VMAP and the VMAP offset at byte 8 of a template item), rather than
committing Microsoft binaries.
"""
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
import uuid

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_messages  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsSystemPowerEvents as power  # pylint: disable=wrong-import-position

POTS = 'cdc05e28-c449-49c6-b9d2-88cf761644df'
WAKE_MAP = 'pots:mapWakeSource'
UNICODE = 0x0001


def manifest_string(text):
    raw = text.encode('utf-16-le') + b'\x00\x00'
    return struct.pack('<I', 4 + len(raw)) + raw


def event_manifest(provider_guid, events, value_maps):
    """WEVT_TEMPLATE bytes for one provider.

    events: [(event id, version, [(item name, value map name or None), ...])]
    value_maps: {map name: {value: message identifier}}
    """
    buf = bytearray(64)                      # CRIM, one provider descriptor, WEVT, one element
    events_at = len(buf)
    buf += b'EVNT' + struct.pack('<III', 0, len(events), 0)
    definitions = len(buf)
    buf += bytes(48 * len(events))
    maps_at = {}
    for name, entries in value_maps.items():
        maps_at[name] = len(buf)
        buf += b'VMAP' + struct.pack('<IIII', 20 + 8 * len(entries), 0, 0, len(entries))
        for value, message in entries.items():
            buf += struct.pack('<II', value, message)
    for index, (event_id, version, items) in enumerate(events):
        template = len(buf)
        buf += b'TEMP' + struct.pack('<IIII', 0, len(items), len(items), 0) + bytes(20)
        items_at = len(buf)
        struct.pack_into('<I', buf, template + 16, items_at)
        buf += bytes(20 * len(items))
        for number, (item, map_name) in enumerate(items):
            struct.pack_into('<I', buf, items_at + 20 * number + 8,
                             maps_at[map_name] if map_name else 0)
            struct.pack_into('<I', buf, items_at + 20 * number + 16, len(buf))
            buf += manifest_string(item)
        struct.pack_into('<HB', buf, definitions + 48 * index, event_id, version)
        struct.pack_into('<I', buf, definitions + 48 * index + 20, template)
    for name, at in maps_at.items():
        struct.pack_into('<I', buf, at + 8, len(buf))
        buf += manifest_string(name)
    buf[0:4] = b'CRIM'
    struct.pack_into('<IHHI', buf, 4, len(buf), 3, 1, 1)
    buf[16:32] = uuid.UUID(provider_guid).bytes_le
    struct.pack_into('<I', buf, 32, 36)
    buf[36:40] = b'WEVT'
    struct.pack_into('<IIII', buf, 40, 28, 0xFFFFFFFF, 1, 0)
    struct.pack_into('<II', buf, 56, events_at, 0)
    return bytes(buf)


def message_table(messages):
    """MESSAGE_RESOURCE_DATA bytes, one block per message: {id: text}."""
    headers, entries = b'', b''
    offset = 4 + 12 * len(messages)
    for message_id, text in sorted(messages.items()):
        raw = text.encode('utf-16-le') + b'\x00\x00'
        raw += b'\x00' * (-(4 + len(raw)) % 4)
        entry = struct.pack('<HH', 4 + len(raw), UNICODE) + raw
        headers += struct.pack('<III', message_id, message_id, offset)
        entries += entry
        offset += len(entry)
    return struct.pack('<I', len(messages)) + headers + entries


def pe_with_resource(data, type_id=None, type_name=None, language=1033):
    """A 32-bit PE whose one section holds a resource tree: type, name 1, language, data.

    The type is a number (type_id) or, as for WEVT_TEMPLATE, a name (type_name).
    """
    rva, raw_offset = 0x1000, 0x200

    def directory(named, entry_name, target):
        return (struct.pack('<IIHHHH', 0, 0, 0, 0, 1 if named else 0, 0 if named else 1)
                + struct.pack('<II', entry_name, target))

    label = b''
    if type_name is not None:
        label = struct.pack('<H', len(type_name)) + type_name.encode('utf-16-le')
        label += b'\x00' * (-len(label) % 4)
        first = directory(True, 0x80000000 | 88, 0x80000000 | 24)
    else:
        first = directory(False, type_id, 0x80000000 | 24)
    tree = (first + directory(False, 1, 0x80000000 | 48) + directory(False, language, 72)
            + struct.pack('<IIII', rva + 88 + len(label), len(data), 0, 0))
    section = tree + label + data
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


WAKE_EVENTS = [
    (1, 2, [('SleepTime', None), ('WakeTime', None), ('WakeSourceType', WAKE_MAP)]),
    (1, 3, [('WakeSourceType', WAKE_MAP), ('CheckpointDuration', None)]),
    (107, 1, [('TargetState', None)]),
]
WAKE_VALUES = {0: 0xD0000001, 1: 0xD0000002, 6: 0xD0000007}
WAKE_NAMES = {0xD0000001: 'Unknown', 0xD0000002: 'Power Button', 0xD0000007: 'Timer - '}


class _TempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, relative, data):
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)


class TestParseEventManifest(unittest.TestCase):
    """The manifest reader returns the maps bound to fields, per event and version."""

    def test_only_mapped_fields_of_the_provider_are_returned(self):
        data = event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES})
        self.assertEqual(windows_messages.parse_event_manifest(data, POTS),
                         {(1, 2): {'WakeSourceType': WAKE_VALUES},
                          (1, 3): {'WakeSourceType': WAKE_VALUES}})

    def test_another_provider_gives_nothing(self):
        data = event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES})
        other = '331c3b3a-2005-44c2-ac5e-77220c37d6b4'
        self.assertEqual(windows_messages.parse_event_manifest(data, other), {})
        self.assertEqual(windows_messages.parse_event_manifest(b'NOPE' + data[4:], POTS), {})

    def test_a_value_map_whose_size_does_not_fit_its_entries_raises(self):
        data = bytearray(event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES}))
        at = data.find(b'VMAP')
        struct.pack_into('<I', data, at + 4, 16 + 8 * len(WAKE_VALUES))  # the layout libfwevt prints
        with self.assertRaises(ValueError):
            windows_messages.parse_event_manifest(bytes(data), POTS)


class TestReadEventValueMaps(_TempDir):
    """The manifest is the PE resource named WEVT_TEMPLATE, and a bad one gives nothing."""

    def test_the_manifest_is_read_from_the_named_resource(self):
        data = event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES})
        path = self.write('pots.dll', pe_with_resource(data, type_name='WEVT_TEMPLATE'))
        self.assertEqual(windows_messages.read_event_value_maps(path, POTS)[(1, 2)],
                         {'WakeSourceType': WAKE_VALUES})

    def test_a_resource_of_another_type_is_not_a_manifest(self):
        data = event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES})
        path = self.write('pots.dll', pe_with_resource(data, type_id=11))
        self.assertEqual(windows_messages.read_event_value_maps(path, POTS), {})
        path = self.write('named.dll', pe_with_resource(data, type_name='MUI'))
        self.assertEqual(windows_messages.read_event_value_maps(path, POTS), {})

    def test_a_manifest_that_does_not_parse_gives_nothing(self):
        data = bytearray(event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES}))
        struct.pack_into('<I', data, data.find(b'VMAP') + 4, 1)
        path = self.write('pots.dll', pe_with_resource(bytes(data), type_name='WEVT_TEMPLATE'))
        self.assertEqual(windows_messages.read_event_value_maps(path, POTS), {})

    def test_a_missing_file_or_one_that_is_not_a_pe_gives_nothing(self):
        self.assertEqual(windows_messages.read_event_value_maps(self.write('x.dll', b'text'), POTS), {})
        self.assertEqual(windows_messages.read_event_value_maps(str(self.tmp / 'absent.dll'), POTS), {})


class TestWrittenUnderLastBuild(unittest.TestCase):
    """A number is named only for records written under the log's last boot build."""

    def test_a_log_with_one_build_names_what_follows_its_first_boot_record(self):
        boots = [(3, '17763'), (50, '17763')]
        self.assertTrue(power._written_under_last_build(4, boots))  # pylint: disable=protected-access
        self.assertTrue(power._written_under_last_build(60, boots))  # pylint: disable=protected-access

    def test_a_record_before_the_first_boot_record_is_not_named(self):
        self.assertFalse(power._written_under_last_build(2, [(3, '17763')]))  # pylint: disable=protected-access

    def test_a_record_written_under_an_earlier_build_is_not_named(self):
        boots = [(50, '17763'), (3, '17134')]  # unordered on purpose
        self.assertFalse(power._written_under_last_build(10, boots))  # pylint: disable=protected-access
        self.assertTrue(power._written_under_last_build(51, boots))  # pylint: disable=protected-access

    def test_no_boot_record_or_no_record_id_is_not_named(self):
        self.assertFalse(power._written_under_last_build(10, []))  # pylint: disable=protected-access
        self.assertFalse(power._written_under_last_build(None, [(3, '17763')]))  # pylint: disable=protected-access


class _Context:
    def __init__(self, data_folder, files):
        self.data_folder = data_folder
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.data_folder)


def _wake(value, record_id=10, version=2):
    return {'kind': power._WAKE, 'fields': {'WakeSourceType': value},  # pylint: disable=protected-access
            'record_id': record_id, 'version': version}


class TestValueNames(_TempDir):
    """A number takes its name from the DLL and English .mui of the log's own volume."""

    LOG = 'Windows/System32/winevt/Logs/System.evtx'
    BOOTS = [(3, '17763')]

    def setUp(self):
        super().setUp()
        files = [
            self.write('data/lba0/Windows/System32/pots.dll', pe_with_resource(
                event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES}),
                type_name='WEVT_TEMPLATE')),
            self.write('data/lba0/Windows/System32/en-US/pots.dll.mui',
                       pe_with_resource(message_table(WAKE_NAMES), type_id=11)),
            self.write('data/lba1/Windows/System32/pots.dll', pe_with_resource(
                event_manifest(POTS, WAKE_EVENTS, {WAKE_MAP: WAKE_VALUES}),
                type_name='WEVT_TEMPLATE')),
        ]
        self.log0 = str(self.tmp / 'data/lba0' / self.LOG)
        self.log1 = str(self.tmp / 'data/lba1' / self.LOG)
        self.names = power._ValueNames(_Context(str(self.tmp / 'data'), files))  # pylint: disable=protected-access

    def test_a_mapped_number_reads_name_then_number(self):
        self.assertEqual(self.names.text(self.log0, _wake('1'), self.BOOTS), 'Power Button (1)')
        self.assertEqual(self.names.text(self.log0, _wake('6', version=3), self.BOOTS),
                         'Timer - (6)')

    def test_a_volume_without_the_english_mui_keeps_the_number(self):
        self.assertEqual(self.names.text(self.log1, _wake('1'), self.BOOTS), '1')
        self.assertEqual(self.names.kept['no value map'], 1)

    def test_a_mui_without_a_message_table_keeps_the_number(self):
        self.write('data/lba1/Windows/System32/en-US/pots.dll.mui',
                   pe_with_resource(b'not a table', type_id=6))
        files = [str(p) for p in (self.tmp / 'data/lba1').rglob('*') if p.is_file()]
        names = power._ValueNames(_Context(str(self.tmp / 'data'), files))  # pylint: disable=protected-access
        self.assertEqual(names.text(self.log1, _wake('1'), self.BOOTS), '1')
        self.assertEqual(dict(names.kept), {'no value map': 1})

    def test_a_record_not_written_under_the_last_build_keeps_the_number(self):
        boots = [(3, '17134'), (20, '17763')]
        self.assertEqual(self.names.text(self.log0, _wake('1', record_id=10), boots), '1')
        self.assertEqual(self.names.text(self.log0, _wake('1', record_id=21), boots),
                         'Power Button (1)')
        self.assertEqual(self.names.kept['build'], 1)

    def test_a_number_or_version_the_map_lacks_keeps_the_number(self):
        self.assertEqual(self.names.text(self.log0, _wake('7'), self.BOOTS), '7')
        self.assertEqual(self.names.text(self.log0, _wake('1', version=0), self.BOOTS), '1')
        self.assertEqual(self.names.kept['not in the map'], 2)

    def test_without_pefile_the_number_is_kept(self):
        original = windows_messages.pefile
        windows_messages.pefile = None
        self.addCleanup(setattr, windows_messages, 'pefile', original)
        self.assertEqual(self.names.text(self.log0, _wake('1'), self.BOOTS), '1')

    def test_the_files_that_named_a_number_are_given_for_the_source_path(self):
        self.names.text(self.log0, _wake('1'), self.BOOTS)
        self.names.text(self.log1, _wake('1'), self.BOOTS)
        self.assertEqual([os.path.relpath(p, self.tmp / 'data') for p in self.names.files_used()],
                         ['lba0/Windows/System32/en-US/pots.dll.mui',
                          'lba0/Windows/System32/pots.dll'])


class TestPowerRowDetail(unittest.TestCase):
    """Detail carries the Sleep Reason of a 42 and the wake source of a Power-Troubleshooter 1."""

    def test_a_42_with_a_reason_shows_it(self):
        found = {'kind': power._SLEEP, 'fields': {'Reason': '7'}, 'values': [], 'time': '',  # pylint: disable=protected-access
                 'meaning': 'The system is entering sleep', 'computer': 'PC'}
        self.assertEqual(power._power_row(found, 'System Idle (7)')[6],  # pylint: disable=protected-access
                         'Sleep Reason: System Idle (7)')
        self.assertEqual(power._power_row(found, '')[6], '')  # pylint: disable=protected-access

    def test_a_wake_row_shows_the_type_as_given_and_the_other_fields_as_stored(self):
        found = {'kind': power._WAKE, 'values': [], 'time': '', 'computer': 'PC',  # pylint: disable=protected-access
                 'meaning': 'The system has returned from a low power state',
                 'fields': {'WakeSourceType': '6', 'WakeSourceText': 'a task', 'WakeTimerOwner': '',
                            'SleepTime': '2023-02-21 00:00:13.569344+00:00',
                            'WakeTime': '2023-02-22 18:39:30.675520+00:00'}}
        row = power._power_row(found, 'Timer - (6)')  # pylint: disable=protected-access
        self.assertEqual(row[6], 'Wake Source Type: Timer - (6); Wake Source Text: a task')
        self.assertEqual((row[1].isoformat(), row[2].isoformat()),
                         ('2023-02-21T00:00:13.569344+00:00', '2023-02-22T18:39:30.675520+00:00'))


if __name__ == '__main__':
    unittest.main()
