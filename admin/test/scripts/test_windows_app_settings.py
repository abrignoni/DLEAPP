"""Packaged-app settings.dat: the value decoder, and the Phone Link and Notepad artifacts that use it.

The hives are built here, cell by cell, the way the registry file format lays them out, and are
read back through open_hive and python-registry exactly as a run reads a staged hive. Every name,
string and identifier in them is invented for the test.
"""

import datetime
import os
import pathlib
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import registry_recovery as rr
from scripts import windows_app_settings as was
from scripts.artifacts import windowsNotepad, windowsPhoneLink
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
EPOCH_1601 = datetime.datetime(1601, 1, 1, tzinfo=UTC)
BASE = was.TYPE_BASE


def ticks(moment):
    """The FILETIME of an aware UTC time."""
    since = moment - EPOCH_1601
    return ((since.days * 86400 + since.seconds) * 1000000 + since.microseconds) * 10


def at(*parts):
    return datetime.datetime(*parts, tzinfo=UTC)


def setting(number, data, written):
    """A packaged-app value: type 0x5F5E100 + number, the data, then the FILETIME."""
    return BASE + number, bytes(data) + struct.pack('<Q', ticks(written))


def utf16z(text):
    return text.encode('utf-16-le') + b'\x00\x00'


def member(name, number, data):
    """One member of a composite value, padded so the next starts on a multiple of 8."""
    body = struct.pack('<III', 12 + (len(name) + 1) * 2 + len(data), number, len(name)) \
        + utf16z(name) + data
    return body + b'\x00' * (-len(body) % 8)


class HiveBuilder:
    """A minimal regf hive: one base block and the cells of one hive bin."""

    def __init__(self):
        self.cells = bytearray()

    def cell(self, payload):
        """Append an allocated cell and return its offset from the start of the hive bins."""
        size = -(-(4 + len(payload)) // 8) * 8
        offset = 32 + len(self.cells)
        self.cells += struct.pack('<i', -size) + payload + b'\x00' * (size - 4 - len(payload))
        return offset

    def key(self, name, parent, stamp, values=(), subkeys=(), root=False):
        """Write a key, its values and its subkeys; return the key's cell offset."""
        value_offsets = []
        for value_name, value_type, data in values:
            if len(data) <= 4:
                # Four bytes or fewer are kept in the data offset field, with the top bit set.
                size, data_offset = len(data) | 0x80000000, struct.unpack('<I', data.ljust(4, b'\0'))[0]
            else:
                size, data_offset = len(data), self.cell(data)
            encoded = value_name.encode('ascii')
            value_offsets.append(self.cell(
                b'vk' + struct.pack('<HIIIHH', len(encoded), size, data_offset, value_type,
                                    1, 0) + encoded))
        value_list = self.cell(b''.join(struct.pack('<I', o) for o in value_offsets)) \
            if value_offsets else 0xFFFFFFFF
        encoded = name.encode('ascii')
        node = bytearray(76 + len(encoded))
        node[0:2] = b'nk'
        struct.pack_into('<H', node, 2, 0x2C if root else 0x20)
        struct.pack_into('<Q', node, 4, ticks(stamp))
        struct.pack_into('<I', node, 16, parent)
        struct.pack_into('<I', node, 36, len(value_offsets))
        struct.pack_into('<I', node, 40, value_list)
        struct.pack_into('<I', node, 44, 0xFFFFFFFF)
        struct.pack_into('<I', node, 48, 0xFFFFFFFF)
        struct.pack_into('<H', node, 72, len(encoded))
        node[76:] = encoded
        offset = self.cell(bytes(node))
        children = [child(self, offset) for child in subkeys]
        if children:
            listing = b'lf' + struct.pack('<H', len(children)) + b''.join(
                struct.pack('<I', o) + b'\x00' * 4 for o in children)
            list_offset = self.cell(listing)
            node_start = offset - 32 + 4
            self.cells[node_start + 20:node_start + 24] = struct.pack('<I', len(children))
            self.cells[node_start + 28:node_start + 32] = struct.pack('<I', list_offset)
        return offset

    def bytes(self, root_offset):
        bins_size = -(-(32 + len(self.cells) + 8) // 4096) * 4096
        hbin = bytearray(bins_size)
        hbin[0:4] = b'hbin'
        struct.pack_into('<II', hbin, 4, 0, bins_size)
        hbin[32:32 + len(self.cells)] = self.cells
        free = bins_size - 32 - len(self.cells)
        struct.pack_into('<i', hbin, 32 + len(self.cells), free)
        block = bytearray(4096)
        block[0:4] = b'regf'
        struct.pack_into('<II', block, 4, 1, 1)
        struct.pack_into('<IIII', block, 20, 1, 5, 0, 1)
        struct.pack_into('<I', block, 36, root_offset)
        struct.pack_into('<I', block, 40, bins_size)
        struct.pack_into('<I', block, 508, rr.xor32(block))
        return bytes(block) + bytes(hbin)


def spec(name, stamp, values=(), subkeys=()):
    """A key description for build_hive: subkeys are specs too."""
    def build(builder, parent):
        return builder.key(name, parent, stamp, values, list(subkeys))
    return build


def build_hive(stamp, *subkeys):
    builder = HiveBuilder()
    root = builder.key('{root}', 0, stamp, (), list(subkeys), root=True)
    return builder.bytes(root)


class _Context:
    def __init__(self, root, files):
        self._root = root
        self._files = files

    def get_files_found(self):
        return list(self._files)

    def get_relative_path(self, path):
        return os.path.relpath(path, self._root)


def write(root, relative, data):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


T1 = at(2030, 1, 2, 3, 4, 5, 600000)
T2 = at(2030, 2, 3, 4, 5, 6, 700000)
T3 = at(2030, 3, 4, 5, 6, 7, 800000)


class DecodeTest(unittest.TestCase):
    def test_scalar_types_and_trailing_filetime(self):
        hive = build_hive(T1, spec('LocalState', T2, values=[
            ('AByte', *setting(0x01, b'\x07', T1)),
            ('AShort', *setting(0x02, struct.pack('<h', -2), T1)),
            ('AnInt', *setting(0x04, struct.pack('<i', -5), T1)),
            ('AUint', *setting(0x05, struct.pack('<I', 4000000000), T1)),
            ('ALong', *setting(0x06, struct.pack('<q', -7), T1)),
            ('AnUlong', *setting(0x07, struct.pack('<Q', 2 ** 63), T1)),
            ('AFloat', *setting(0x08, struct.pack('<f', 1.5), T1)),
            ('ADouble', *setting(0x09, struct.pack('<d', 3.25), T1)),
            ('AChar', *setting(0x0A, 'Q'.encode('utf-16-le'), T1)),
            ('AFlag', *setting(0x0B, b'\x01', T2)),
            ('AText', *setting(0x0C, utf16z('sample text'), T3)),
            ('ATime', *setting(0x0E, struct.pack('<q', ticks(T2)), T3)),
            ('ASpan', *setting(0x0F, struct.pack('<q', 15_000_000), T1)),
            ('AGuid', *setting(0x10, bytes(range(16)), T1)),
            ('ABlob', *setting(0x14, b'\x01\x02\xff', T1)),
            ('Ints', *setting(0x17, struct.pack('<3i', 1, -1, 2), T1)),
            ('Words', *setting(0x1F, b''.join(struct.pack('<I', len(utf16z(w))) + utf16z(w)
                                              for w in ('one', 'two')), T1)),
            ('Plain', 4, struct.pack('<I', 9)),
        ]))
        with tempfile.TemporaryDirectory() as root:
            path = write(root, 'settings.dat', hive)
            reg = was.open_settings(path)
            values = was.settings(reg.open('LocalState'))
        expect = {
            'AByte': 7, 'AShort': -2, 'AnInt': -5, 'AUint': 4000000000, 'ALong': -7,
            'AnUlong': 2 ** 63, 'AFloat': 1.5, 'ADouble': 3.25, 'AChar': 'Q', 'AFlag': True,
            'AText': 'sample text', 'ATime': T2, 'ASpan': datetime.timedelta(seconds=1.5),
            'AGuid': '03020100-0504-0706-0809-0a0b0c0d0e0f', 'ABlob': [1, 2, 255],
            'Ints': [1, -1, 2], 'Words': ['one', 'two'], 'Plain': 9,
        }
        self.assertEqual({name: s.value for name, s in values.items()}, expect)
        self.assertEqual(values['AText'].written, T3)
        self.assertEqual(values['AFlag'].written, T2)
        self.assertEqual(values['AText'].type_name, 'String')
        self.assertEqual(values['AText'].stored_type, 0x5F5E10C)
        self.assertEqual(values['Plain'].written, '')
        self.assertIsNone(values['Plain'].type_number)
        self.assertTrue(all(not s.error for s in values.values()))

    def test_composite_members_in_order(self):
        data = member('First', 0x0C, utf16z('a')) + member('Second', 0x0B, b'\x00') \
            + member('Third', 0x07, struct.pack('<Q', 42))
        hive = build_hive(T1, spec('LocalState', T1, values=[('Group', *setting(0x0D, data, T2))]))
        with tempfile.TemporaryDirectory() as root:
            values = was.settings(was.open_settings(write(root, 'settings.dat', hive))
                                  .open('LocalState'))
        group = values['Group']
        self.assertEqual(list(group.value), ['First', 'Second', 'Third'])
        self.assertEqual(group.value['Third'], ('UInt64', 42))
        self.assertEqual(group.text(), 'First=a; Second=False; Third=42')
        self.assertEqual(group.written, T2)

    def test_damaged_values_are_reported_as_stored_not_dropped(self):
        hive = build_hive(T1, spec('LocalState', T1, values=[
            ('Short', BASE + 0x0C, b'\x01\x02'),
            ('OddText', *setting(0x0C, b'\x41\x00\x42', T1)),
            ('BadGroup', *setting(0x0D, struct.pack('<III', 400, 0x0C, 1), T1)),
        ]))
        with tempfile.TemporaryDirectory() as root:
            values = was.settings(was.open_settings(write(root, 'settings.dat', hive))
                                  .open('LocalState'))
        self.assertEqual(set(values), {'Short', 'OddText', 'BadGroup'})
        self.assertIn('too short', values['Short'].error)
        self.assertEqual(values['Short'].value, '0102')
        self.assertIn('odd length', values['OddText'].error)
        self.assertEqual(values['OddText'].written, T1)
        self.assertIn('does not fit', values['BadGroup'].error)

    def test_package_hives_takes_only_the_package_settings_hive(self):
        with tempfile.TemporaryDirectory() as root:
            files = [
                write(root, 'Users/a/AppData/Local/Packages/Example.App_abc/Settings/settings.dat', b'x'),
                write(root, 'Users/a/AppData/Local/Packages/Example.App_abc/LocalState/Settings/settings.dat', b'x'),
                write(root, 'Users/a/AppData/Local/Packages/Example.AppDecoy_abc/Settings/settings.dat', b'x'),
                write(root, 'Users/a/AppData/Local/Packages/Example.App_abc/Settings/settings.dat.LOG1', b'x'),
            ]
            found = was.package_hives(_Context(root, files + files[:1]), 'Example.App')
        self.assertEqual([(rel, pkg, user) for _p, rel, pkg, user in found], [
            ('Users/a/AppData/Local/Packages/Example.App_abc/Settings/settings.dat', 'Example.App_abc', 'a')])


DEVICE = '00000000-1111-2222-3333-444444444444'
OTHER = '55555555-6666-7777-8888-999999999999'


def phone_hive(devices):
    """A Phone Link-shaped hive with the given {device id: (friendly name, written)} keys."""
    subkeys = [spec('Deleted', T1), spec('IdMap', T1)]
    for device, (name, written) in devices.items():
        subkeys.append(spec(device, T3, values=[
            ('FriendlyName', *setting(0x0C, utf16z(name), written)),
            ('Manufacturer', *setting(0x0C, utf16z('ExampleMaker'), written)),
            ('Model', *setting(0x0C, utf16z('Model X'), written)),
            ('OsVersion', *setting(0x0C, utf16z('99'), written)),
            ('SdkVersion', *setting(0x05, struct.pack('<I', 99), written)),
            ('AgentsVersion', *setting(0x0C, utf16z('1.2.3.4'), written)),
            ('PackageName', *setting(0x0C, utf16z('example.agent'), written)),
            ('AccountId', *setting(0x0C, utf16z('ACCOUNT0001'), written)),
            ('CountryIso', *setting(0x0C, utf16z('ZZ'), written)),
            ('Locale', *setting(0x0C, utf16z('ZZ'), written)),
            ('LastSeenTime', *setting(0x0E, struct.pack('<q', ticks(T1)), written)),
            ('MessagesLastUpdatedTime', *setting(0x0E, struct.pack('<q', ticks(T2)), written)),
            ('MessagesPCPermission', *setting(0x0B, b'\x01', written)),
            ('CallsDevicePermission', *setting(0x0B, b'\x00', written)),
        ], subkeys=[spec('DeviceInfo', T2, values=[
            ('NetworkOperator', *setting(0x0C, utf16z('ExampleNet'), T1)),
            ('BatteryPercent', *setting(0x04, struct.pack('<i', 42), T2)),
            ('BatteryLastUpdatedTime', *setting(0x0E, struct.pack('<q', ticks(T2)), T2)),
        ])]))
    default = next(iter(devices))
    return build_hive(T1, spec('LocalState', T1, subkeys=[spec('Devices', T2, values=[
        ('DefaultRemoteDevice', *setting(0x0C, utf16z(default), T1))], subkeys=subkeys)]))


PHONE = 'AppData/Local/Packages/Microsoft.YourPhone_8wekyb3d8bbwe/Settings/settings.dat'
NOTEPAD = 'AppData/Local/Packages/Microsoft.WindowsNotepad_8wekyb3d8bbwe/Settings/settings.dat'


class PhoneLinkDevicesTest(unittest.TestCase):
    def test_one_row_per_device_with_its_stored_times(self):
        with tempfile.TemporaryDirectory() as root:
            path = write(root, f'Users/alpha/{PHONE}', phone_hive({DEVICE: ('Phone A', T2)}))
            headers, rows, source = windowsPhoneLink.phoneLinkLinkedDevices.__wrapped__(
                _Context(root, [path]))
        self.assertEqual(len(rows), 1)
        row = dict(zip([h[0] if isinstance(h, tuple) else h for h in headers], rows[0]))
        self.assertEqual(row['Device Key Last Written'], T3)
        self.assertEqual(row['Last Seen Time (as stored)'], T1)
        self.assertEqual(row['Messages Last Updated Time (as stored)'], T2)
        self.assertEqual(row['Battery Last Updated Time (as stored)'], T2)
        self.assertEqual(row['Device Details Written'], T2)
        self.assertEqual(row['Network Operator Written'], T1)
        self.assertEqual(row['Friendly Name'], 'Phone A')
        self.assertEqual(row['SDK Version (as stored)'], 99)
        self.assertEqual(row['Battery Percent (as stored)'], 42)
        self.assertEqual(row['Default Device'], 'Yes')
        self.assertEqual(row['Permissions (as stored)'],
                         'CallsDevicePermission=False, MessagesPCPermission=True')
        self.assertEqual(row['Device ID'], DEVICE)
        self.assertEqual(row['User'], 'alpha')
        self.assertEqual(row['Source File'], f'Users/alpha/{PHONE}')
        self.assertEqual(source, path)

    def test_two_users_add_rows_and_a_decoy_package_adds_none(self):
        with tempfile.TemporaryDirectory() as root:
            files = [
                write(root, f'Users/alpha/{PHONE}', phone_hive({DEVICE: ('Phone A', T2)})),
                write(root, f'Users/beta/{PHONE}', phone_hive({OTHER: ('Phone B', T1),
                                                              DEVICE: ('Phone C', T1)})),
                write(root, 'Users/gamma/AppData/Local/Packages/Example.Decoy_x/Settings/settings.dat',
                      phone_hive({DEVICE: ('Decoy', T1)})),
            ]
            _headers, rows, _source = windowsPhoneLink.phoneLinkLinkedDevices.__wrapped__(
                _Context(root, files + files[:1]))
        self.assertEqual([(r[-2], r[8], r[15]) for r in rows], [
            ('alpha', 'Phone A', 'Yes'), ('beta', 'Phone C', 'No'), ('beta', 'Phone B', 'Yes')])

    def test_hive_without_devices_gives_no_rows_and_still_names_the_file(self):
        hive = build_hive(T1, spec('LocalState', T1), spec('RoamingState', T1))
        with tempfile.TemporaryDirectory() as root:
            path = write(root, f'Users/alpha/{PHONE}', hive)
            _headers, rows, source = windowsPhoneLink.phoneLinkLinkedDevices.__wrapped__(
                _Context(root, [path]))
        self.assertEqual((rows, source), ([], path))


class NotepadSettingsTest(unittest.TestCase):
    def test_each_value_is_a_row_and_find_and_replace_text_is_flagged(self):
        hive = build_hive(T1, spec('LocalState', T3, values=[
            ('FindString', *setting(0x0C, utf16z('needle'), T2)),
            ('ReplaceString', *setting(0x0C, utf16z('thread'), T3)),
            ('RecentFiles', *setting(0x0C, utf16z('C:\\example\\one.txt'), T1)),
            ('WordWrap', *setting(0x0B, b'\x01', T1)),
            ('WindowPositionLeft', *setting(0x04, struct.pack('<i', -8), T1)),
        ]), spec('RoamingState', T1))
        with tempfile.TemporaryDirectory() as root:
            path = write(root, f'Users/alpha/{NOTEPAD}', hive)
            headers, rows, source = windowsNotepad.windowsNotepadSettings.__wrapped__(
                _Context(root, [path]))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        table = {r[2]: dict(zip(names, r)) for r in rows}
        self.assertEqual(list(table), ['FindString', 'RecentFiles', 'ReplaceString',
                                       'WindowPositionLeft', 'WordWrap'])
        self.assertEqual(table['FindString']['Value'], 'needle')
        self.assertEqual(table['FindString']['Value Written'], T2)
        self.assertEqual(table['FindString']['Free Text (Find or Replace)'], 'Yes')
        self.assertEqual(table['ReplaceString']['Free Text (Find or Replace)'], 'Yes')
        self.assertEqual(table['RecentFiles']['Free Text (Find or Replace)'], '')
        self.assertIn('line 327', table['RecentFiles']['Documented Meaning'])
        self.assertEqual(table['WordWrap']['Value'], 'True')
        self.assertEqual(table['WindowPositionLeft']['Value'], '-8')
        self.assertEqual(table['WindowPositionLeft']['Documented Meaning'], '')
        self.assertEqual({r['Key Last Written'] for r in table.values()}, {T3})
        self.assertEqual({r['Key'] for r in table.values()}, {'LocalState'})
        self.assertEqual(source, path)

    def test_not_a_hive_is_logged_and_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            path = write(root, f'Users/alpha/{NOTEPAD}', b'not a registry hive' * 300)
            _headers, rows, source = windowsNotepad.windowsNotepadSettings.__wrapped__(
                _Context(root, [path]))
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
