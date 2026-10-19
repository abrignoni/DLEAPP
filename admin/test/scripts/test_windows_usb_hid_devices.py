"""Pin the USB Device Instances and HID Input Devices artifacts
(scripts/artifacts/windowsUsbHidDevices.py).

The hive is stood in for by small objects that answer the python-registry calls the reader
makes. Device properties are built in both layouts seen on real hives: Windows 8 and later
keep the data in the property sub-key's default value, with the property type in the value
type; Windows 7 keeps a sub-key 00000000 holding Type and Data values.
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
from scripts.artifacts import windowsUsbHidDevices as uh
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

DATES = '{83da6326-97a6-4088-9453-a1923f573b29}'
BUS = '{540b947e-8b40-45bc-a8a2-6a0b894cbda2}'
WHEN = datetime.datetime(2026, 10, 19, 12, 0, 0, tzinfo=datetime.timezone.utc)
LATER = datetime.datetime(2026, 10, 19, 13, 30, 0, tzinfo=datetime.timezone.utc)


def filetime(when):
    return struct.pack('<Q', int((when - datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc))
                                 .total_seconds() * 10_000_000))


def utf16(text):
    return (text + '\x00').encode('utf-16-le')


class _Value:
    def __init__(self, name, data, kind=1):
        self._name, self._data, self._kind = name, data, kind

    def name(self):
        return self._name

    def value(self):
        return self._data

    def raw_data(self):
        return self._data

    def value_type(self):
        return self._kind


class _Key:
    def __init__(self, name='', values=None, subkeys=(), typed=None):
        self._name = name
        self._values = [_Value(n, d) for n, d in (values or {}).items()]
        self._values += [_Value(n, d, k) for n, (d, k) in (typed or {}).items()]
        self._subkeys = list(subkeys)

    def name(self):
        return self._name

    def values(self):
        return self._values

    def value(self, name):
        for value in self._values:
            if value.name() == name:
                return value
        raise Registry.RegistryValueNotFoundException(name)

    def subkeys(self):
        return self._subkeys

    def subkey(self, name):
        for key in self._subkeys:
            if key.name() == name:
                return key
        raise Registry.RegistryKeyNotFoundException(name)


def new_layout(prop_id, data, kind):
    """A Windows 8 and later property sub-key: python-registry reports the low bits only."""
    return _Key(f'{prop_id:04X}', typed={'(default)': (data, kind)})


def win7_layout(prop_id, data, kind):
    return _Key(f'{prop_id:08X}', subkeys=[_Key('00000000', {'Type': struct.pack('<I', kind), 'Data': data})])


def properties(*groups):
    return _Key('Properties', subkeys=[_Key(guid, subkeys=list(nodes)) for guid, nodes in groups])


KEYBOARD_IF = _Key('6&abc&0&0000', {'Service': 'HidUsb', 'ParentIdPrefix': '7&def&0',
                                     'DeviceDesc': '@input.inf,%hid.devicedesc%;USB Input Device',
                                     'ContainerID': '{c1}'},
                   subkeys=[properties((DATES, [new_layout(101, filetime(WHEN), 0x10),
                                                new_layout(102, filetime(LATER), 0x10)]),
                                       (BUS, [new_layout(4, utf16('Board'), 0x12)]))])
COMPOSITE = _Key('SERIAL1', {'Service': 'usbccgp', 'ParentIdPrefix': '6&abc&0', 'ContainerID': '{c1}'},
                 subkeys=[properties((DATES, [win7_layout(101, filetime(WHEN), 0x10),
                                              # a FILETIME property stored with another type is not read
                                              win7_layout(102, filetime(LATER), 0x12)]))])
HUB = _Key('4&root&0', {'Service': 'usbhub', 'ParentIdPrefix': '5&hub&0'})
NO_SERIAL = _Key('5&hub&0&3', {'Service': 'USBSTOR', 'FriendlyName': 'Disk'})
USB = _Key('USB', subkeys=[
    _Key('ROOT_HUB30', subkeys=[HUB]),
    _Key('VID_16D0&PID_0753', subkeys=[COMPOSITE]),
    _Key('VID_16D0&PID_0753&MI_00', subkeys=[KEYBOARD_IF]),
    _Key('VID_0781&PID_5599', subkeys=[NO_SERIAL])])
HID = _Key('HID', subkeys=[
    _Key('VID_16D0&PID_0753&MI_00', subkeys=[
        _Key('7&def&0&0000', {'Service': 'kbdhid', 'DeviceDesc': '@keyboard.inf,%x%;HID Keyboard Device',
                              'Mfg': 'Plain text', 'ContainerID': '{c1}'})]),
    # a prefix of another instance's prefix must not match: 7&de is not 7&def&0
    _Key('VEN_27C6&Col01', subkeys=[_Key('7&def&00000', {'Service': 'mouhid'})])])


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


HIVE = _Hive({'Select': _Key(values={'Current': 1}), r'ControlSet001\Enum\USB': USB,
              r'ControlSet001\Enum\HID': HID})


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Properties(unittest.TestCase):
    def test_both_layouts_and_the_type_check(self):
        self.assertEqual(uh._date(KEYBOARD_IF, 101), WHEN)  # pylint: disable=protected-access
        self.assertEqual(uh._date(KEYBOARD_IF, 102), LATER)  # pylint: disable=protected-access
        self.assertEqual(uh._date(COMPOSITE, 101), WHEN)  # pylint: disable=protected-access
        self.assertEqual(uh._date(COMPOSITE, 102), '')  # pylint: disable=protected-access
        self.assertEqual(uh._date(NO_SERIAL, 101), '')  # pylint: disable=protected-access
        self.assertEqual(uh._string_property(KEYBOARD_IF, BUS, 4), 'Board')  # pylint: disable=protected-access

    def test_display(self):
        self.assertEqual(uh._display('@usb.inf,%k%;USB Composite Device'), 'USB Composite Device')  # pylint: disable=protected-access
        self.assertEqual(uh._display('Plain; text'), 'Plain; text')  # pylint: disable=protected-access
        self.assertEqual(uh._display(['a', '', 'b']), 'a, b')  # pylint: disable=protected-access


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Processors(unittest.TestCase):
    def run_both(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        hive = pathlib.Path(folder.name, 'Windows', 'System32', 'config', 'SYSTEM')
        log = hive.with_name('SYSTEM.LOG1')
        hive.parent.mkdir(parents=True)
        hive.write_bytes(b'')
        log.write_bytes(b'')
        context = mock.Mock()
        context.get_files_found.return_value = [str(hive), str(log)]
        context.get_relative_path.side_effect = lambda p: pathlib.Path(p).relative_to(folder.name).as_posix()
        with mock.patch.object(uh, 'open_hive', return_value=HIVE), mock.patch.object(uh, 'logfunc') as logged:
            usb = uh.usbAllDevices.__wrapped__(context)
            hid = uh.hidDevices.__wrapped__(context)
        return str(hive), usb, hid, [call[0][0] for call in logged.call_args_list]

    def test_usb_rows(self):
        hive, (headers, rows, located), _hid, logged = self.run_both()
        self.assertEqual(headers[0], ('Last Connected (UTC)', 'datetime'))
        self.assertEqual(located, hive)
        relative = 'Windows/System32/config/SYSTEM'
        self.assertEqual(rows, [
            ('', WHEN, '', '16D0', '0753', '', 'SERIAL1', '', '', '', '', 'usbccgp', '', '', '{c1}', relative),
            (LATER, WHEN, '', '16D0', '0753', '00', '6&abc&0&0000', 'Board', 'USB Input Device', '', '', 'HidUsb',
             'kbdhid (HID Keyboard Device)', 'VID_16D0&PID_0753\\SERIAL1', '{c1}', relative),
            ('', '', '', '0781', '5599', '', '5&hub&0&3', '', '', '', 'Disk', 'USBSTOR', '',
             'ROOT_HUB30\\4&root&0', '', relative)])
        self.assertIn('keys without a VID: ROOT_HUB30 (1)', logged[0])

    def test_hid_rows(self):
        hive, _usb, (headers, rows, located), _logged = self.run_both()
        self.assertEqual(len(headers), 11)
        self.assertEqual(located, hive)
        self.assertEqual([row[3:9] for row in rows], [
            ('VID_16D0&PID_0753&MI_00', '7&def&0&0000', 'kbdhid', 'HID Keyboard Device', 'Plain text',
             'VID_16D0&PID_0753&MI_00\\6&abc&0&0000'),
            ('VEN_27C6&Col01', '7&def&00000', 'mouhid', '', '', '')])

    def test_no_library(self):
        with mock.patch.object(uh, 'Registry', None), mock.patch.object(uh, 'logfunc'):
            self.assertEqual(uh.usbAllDevices.__wrapped__(mock.Mock())[1:], ([], ''))
            self.assertEqual(uh.hidDevices.__wrapped__(mock.Mock())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
