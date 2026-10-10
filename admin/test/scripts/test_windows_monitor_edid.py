"""Pin the Monitors (EDID) artifact (scripts/artifacts/windowsMonitorEdid.py).

The EDID blocks are built for the test in the layout of the first 128-byte block; the hive is stood in for by small
objects that answer the python-registry calls the reader makes.
"""
import datetime
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsMonitorEdid as me
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

WRITTEN = datetime.datetime(2025, 8, 6, 12, 0, 0)
WHEN = WRITTEN.replace(tzinfo=datetime.timezone.utc)
BASE = 'ControlSet001\\Enum\\DISPLAY'


def descriptor(tag, text):
    return b'\x00\x00\x00' + bytes([tag]) + b'\x00' + (text + b'\n').ljust(13, b' ')[:13]


def edid(letters='ABC', product=0x1234, serial=0x01020304, week=6, year=2013, version=(1, 4), descriptors=(),
         valid=True):
    packed = sum((ord(c) - 64) << shift for c, shift in zip(letters, (10, 5, 0)))
    block = bytearray(128)
    block[:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    block[8:10] = struct.pack('>H', packed)
    block[10:18] = struct.pack('<HIBB', product, serial, week, year - 1990)
    block[18:20] = bytes(version)
    for start, data in zip((54, 72, 90, 108), list(descriptors) + [b'\x01' * 18] * 4):
        block[start:start + 18] = data
    block[127] = (256 - sum(block[:127])) % 256 if valid else (255 - sum(block[:127])) % 256
    return bytes(block)


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data

    def raw_data(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=()):
        self._name, self._values, self._subkeys = name, values or {}, list(subkeys)

    def name(self):
        return self._name

    def values(self):
        return [_Value(name, data) for name, data in self._values.items()]

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(name, self._values[name])

    def subkeys(self):
        return self._subkeys

    @staticmethod
    def timestamp():
        return WRITTEN


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


GOOD = edid(descriptors=(descriptor(0xfc, b'Made-up One'), descriptor(0xff, b'SN-0042'), descriptor(0xfe, b'pa\x81nel'),
                         descriptor(0xfc, b'Two')))
HIVE = _Hive({
    'Select': _Key(values={'Current': 1}),
    BASE: _Key(subkeys=[
        _Key('ABC1234', subkeys=[_Key('5&1&0&UID1', {'DeviceDesc': '@monitor.inf,%x%;Generic PnP Monitor'}),
                                 _Key('5&2&0&UID2', {'DeviceDesc': 7})]),
        _Key('Default_Monitor', subkeys=[_Key('1&0&0&UID0', {'devicedesc': 'Generic Non-PnP Monitor'})]),
        _Key('BAD0001', subkeys=[_Key('1&1')])]),
    BASE + '\\ABC1234\\5&1&0&UID1\\Device Parameters': _Key(values={'EDID': GOOD + b'\x00' * 128, 'Other': 1}),
    BASE + '\\ABC1234\\5&2&0&UID2\\Device Parameters': _Key(values={'edid': edid(week=255, serial=0, valid=False)}),
    BASE + '\\BAD0001\\1&1\\Device Parameters': _Key(values={'EDID': b'\x00' * 127}),
})


class Edid(unittest.TestCase):
    def test_fields(self):
        self.assertEqual(me.edid_fields(GOOD), {
            'manufacturer': 'ABC', 'product': '1234', 'serial': 0x01020304, 'week': 6, 'year': 2013, 'version': '1.4',
            'name': 'Made-up One | Two', 'serial_text': 'SN-0042', 'text': 'pa\\x81nel', 'checksum_ok': True})

    def test_byte_order(self):
        raw = bytearray(GOOD)
        raw[8:16] = bytes.fromhex('4c2d4154aabbccdd')
        fields = me.edid_fields(bytes(raw))
        self.assertEqual((fields['manufacturer'], fields['product'], fields['serial']), ('SAM', '5441', 0xddccbbaa))
        self.assertFalse(fields['checksum_ok'])

    def test_a_timing_descriptor_gives_no_text(self):
        fields = me.edid_fields(edid(descriptors=(b'\x01\x00\x00\xfc\x00name\n        ', descriptor(0xfd, b'range'))))
        self.assertEqual((fields['name'], fields['serial_text'], fields['text']), ('', '', ''))

    def test_text_without_a_line_feed_and_with_inner_spaces(self):
        block = b'\x00\x00\x00\xfc\x00' + b'Thirteen char'
        self.assertEqual(me.edid_fields(edid(descriptors=(block, descriptor(0xfc, b'a  b'))))['name'],
                         'Thirteen char | a  b')

    def test_product_letters_are_upper_case_and_leading_spaces_stay(self):
        fields = me.edid_fields(edid(product=0x0abc, descriptors=(descriptor(0xfc, b'  lead'),)))
        self.assertEqual((fields['product'], fields['name']), ('0ABC', '  lead'))

    def test_not_an_edid(self):
        for raw in (b'', GOOD[:127], b'\x00' * 128, b'\x01' + GOOD[1:]):
            self.assertIsNone(me.edid_fields(raw))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Rows(unittest.TestCase):
    def test_a_hive(self):
        rows, unread = me.monitor_rows(HIVE, 'ControlSet001')
        self.assertEqual(unread, 1)
        self.assertEqual(rows, [
            (WHEN, 'ABC1234', '5&1&0&UID1', '@monitor.inf,%x%;Generic PnP Monitor', 'ABC', '1234', 0x01020304, 6, 2013,
             '1.4', 'Made-up One | Two', 'SN-0042', 'pa\\x81nel', 256, 'Yes', BASE + '\\ABC1234\\5&1&0&UID1'),
            (WHEN, 'ABC1234', '5&2&0&UID2', '', 'ABC', '1234', 0, 255, 2013, '1.4', '', '', '', 128, 'No',
             BASE + '\\ABC1234\\5&2&0&UID2'),
            (WHEN, 'Default_Monitor', '1&0&0&UID0', 'Generic Non-PnP Monitor') + ('',) * 11
            + (BASE + '\\Default_Monitor\\1&0&0&UID0',),
            (WHEN, 'BAD0001', '1&1', '') + ('',) * 9 + (127, '', BASE + '\\BAD0001\\1&1')])

    def test_no_display_key(self):
        self.assertEqual(me.monitor_rows(_Hive({}), 'ControlSet001'), ([], 0))

    def test_processor(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        for name, hive in (('a', HIVE), ('ab', None), ('b', _Hive({'Select': _Key(values={'Current': 1})}))):
            path = pathlib.Path(folder.name, name, 'Windows', 'System32', 'config', 'SYSTEM')
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] is None:
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: pathlib.Path(p).relative_to(folder.name).as_posix()
        with mock.patch.object(me, 'found_hives', return_value=sorted(by_path, reverse=True)), \
                mock.patch.object(me, 'open_hive', side_effect=opened), mock.patch.object(me, 'logfunc') as log:
            headers, rows, located = me.windowsMonitorEdid.__wrapped__(context)
        self.assertEqual(len(headers), 17)
        self.assertEqual(headers[0], ('Key Last Written (UTC)', 'datetime'))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0][-1], 'a/Windows/System32/config/SYSTEM')
        self.assertEqual(located, str(pathlib.Path(folder.name, 'a', 'Windows', 'System32', 'config', 'SYSTEM')))
        logged = [call[0][0] for call in log.call_args_list]
        self.assertEqual(len(logged), 2)
        self.assertIn('1 EDID values of a/Windows/System32/config/SYSTEM are not an EDID block', logged[0])
        self.assertIn('could not read ab/Windows/System32/config/SYSTEM: not a hive', logged[1])

    def test_no_library(self):
        with mock.patch.object(me, 'Registry', None), mock.patch.object(me, 'logfunc') as log:
            self.assertEqual(me.windowsMonitorEdid.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
