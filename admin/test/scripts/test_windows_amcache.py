"""Pin the InventoryApplication, InventoryApplicationShortcut, InventoryDriverBinary and InventoryDevicePnp readers
in scripts/artifacts/windowsAmcache.py.

The hive is stood in for by small objects that answer the python-registry calls the readers make; the expected rows
are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsAmcache as amcache  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

WRITTEN = datetime.datetime(2023, 2, 22, 18, 47, 15, 69435)
WRITTEN_UTC = WRITTEN.replace(tzinfo=datetime.timezone.utc)


class _Value:
    def __init__(self, data):
        self._data = data

    def value(self):
        return self._data


class _Key:
    def __init__(self, values=None, subkeys=(), written=WRITTEN, name=''):
        self._values = values or {}
        self._subkeys = list(subkeys)
        self._written = written
        self._name = name

    def name(self):
        return self._name

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(self._values[name])

    def subkeys(self):
        return self._subkeys

    def timestamp(self):
        return self._written


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.replace('/report/data/', '')


MSI = {'ProgramId': '0000aa', 'ProgramInstanceId': '0000bb', 'Name': 'Example Tool', 'Version': '1.2.3',
       'Publisher': 'Example Corp', 'Language': 1033, 'Source': 'Msi', 'Type': 'Application', 'StoreAppType': '',
       'MsiPackageCode': '{11111111-1111-1111-1111-111111111111}',
       'MsiProductCode': '{22222222-2222-2222-2222-222222222222}', 'HiddenArp': 0, 'InboxModernApp': 0,
       'OSVersionAtInstallTime': '10.0.0.17763', 'InstallDate': '02/20/2023 00:00:00', 'PackageFullName': '',
       'ManifestPath': '', 'BundleManifestPath': '', 'RootDirPath': 'c:\\program files\\example\\',
       'UninstallString': 'MsiExec.exe /X{22222222-2222-2222-2222-222222222222}',
       'RegistryKeyPath': 'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\'
                          '{22222222-2222-2222-2222-222222222222}'}
MSI_ROW = (WRITTEN_UTC, '02/20/2023 00:00:00', 'Example Tool', '1.2.3', 'Example Corp', 'Msi', '',
           'c:\\program files\\example\\', 'MsiExec.exe /X{22222222-2222-2222-2222-222222222222}',
           'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\'
           '{22222222-2222-2222-2222-222222222222}', '', '{22222222-2222-2222-2222-222222222222}', 0,
           '10.0.0.17763', '0000aa')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ApplicationRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(amcache.application_row(_Key(MSI)), MSI_ROW)

    def test_a_store_package_entry(self):
        entry = _Key({'ProgramId': '0000cc', 'Name': 'Example.App', 'Version': '2.0.0.0', 'Publisher': 'CN=Example',
                      'Source': 'AppxPackage', 'StoreAppType': 'Win10StoreApp', 'HiddenArp': 1,
                      'OSVersionAtInstallTime': '10.0.0.19041', 'InstallDate': '',
                      'PackageFullName': 'Example.App_2.0.0.0_x64__abc', 'MsiProductCode': '',
                      'RootDirPath': 'C:\\Program Files\\WindowsApps\\Example.App_2.0.0.0_x64__abc',
                      'UninstallString': '', 'RegistryKeyPath': ''})
        self.assertEqual(amcache.application_row(entry),
                         (WRITTEN_UTC, '', 'Example.App', '2.0.0.0', 'CN=Example', 'AppxPackage', 'Win10StoreApp',
                          'C:\\Program Files\\WindowsApps\\Example.App_2.0.0.0_x64__abc', '', '',
                          'Example.App_2.0.0.0_x64__abc', '', 1, '10.0.0.19041', '0000cc'))

    def test_absent_values_are_blank_and_a_stored_zero_is_kept(self):
        row = amcache.application_row(_Key({'HiddenArp': 0}, written=None))
        self.assertEqual(row, (None, '', '', '', '', '', '', '', '', '', '', '', 0, '', ''))

    def test_a_time_that_already_carries_a_zone_is_left_alone(self):
        zone = datetime.timezone(datetime.timedelta(hours=-5))
        aware = WRITTEN.replace(tzinfo=zone)
        self.assertEqual(amcache.application_row(_Key({}, written=aware))[0].utcoffset(),
                         datetime.timedelta(hours=-5))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ShortcutRowTest(unittest.TestCase):
    def test_path_and_time(self):
        path = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Example\\Example Tool.lnk'
        self.assertEqual(amcache.shortcut_row(_Key({'ShortcutPath': path})), (WRITTEN_UTC, path))

    def test_an_entry_without_the_value(self):
        self.assertEqual(amcache.shortcut_row(_Key({})), (WRITTEN_UTC, ''))


SHA1 = '35db8fd43dac86f8dec9e808579e412228aabbcc'
DRIVER = {'DriverName': 'example.sys', 'Inf': 'oem7.inf', 'DriverVersion': '1.2.3.4', 'Product': 'Example Product',
          'ProductVersion': '1.2', 'WdfVersion': '1.15', 'DriverCompany': 'Example Corp',
          'DriverPackageStrongName': 'example.inf_amd64_0123456789abcdef', 'Service': 'example', 'DriverInBox': '0',
          'DriverSigned': '1', 'DriverIsKernelMode': '1', 'DriverId': '0000' + SHA1,
          'DriverLastWriteTime': '09/15/2018 07:28:17', 'DriverType': '8650778', 'DriverTimeStamp': '1063335750',
          'DriverCheckSum': '264074', 'ImageSize': '274432'}
DRIVER_PATH = 'c:/windows/system32/drivers/example.sys'
DRIVER_ROW = (WRITTEN_UTC, '09/15/2018 07:28:17', DRIVER_PATH, SHA1, 'example.sys', 'example', 'Example Corp',
              'Example Product', '1.2.3.4', '0', '1', '1', 'oem7.inf', 'example.inf_amd64_0123456789abcdef',
              '1063335750')
DEVICE = {'Model': 'USB Mass Storage Device', 'Manufacturer': 'Compatible USB storage device',
          'DriverName': 'usbstor.sys', 'ParentId': 'usb\\root_hub30\\4&1&0&0', 'MatchingID': 'usb\\class_08',
          'Class': 'usb', 'ClassGuid': '{36fc9e60-c465-11cf-8056-444553540000}',
          'Description': 'Example Flash Drive', 'Enumerator': 'usb', 'Service': 'usbstor', 'InstallState': '0',
          'DeviceState': '96', 'Inf': 'usbstor.inf', 'DriverVerDate': '06-21-2006', 'InstallDate': '09-18-2020',
          'FirstInstallDate': '09-17-2020', 'DriverPackageStrongName': 'usbstor.inf_amd64_0123456789abcdef',
          'DriverVerVersion': '10.0.19041.1', 'ContainerId': '{11111111-2222-3333-4444-555555555555}',
          'ProblemCode': '0', 'Provider': 'Microsoft', 'DriverId': '0000' + SHA1,
          'BusReportedDescription': 'Example Bus Name', 'HWID': 'usb\\vid_0000&pid_0001&rev_0100,usb\\vid_0000&pid_0001',
          'COMPID': 'usb\\class_08', 'STACKID': 'x'}
DEVICE_NAME = 'usb/vid_0000&pid_0001/0123456789'
DEVICE_ROW = (WRITTEN_UTC, '09-18-2020', '09-17-2020', DEVICE_NAME, 'USB Mass Storage Device', 'Example Flash Drive',
              'Compatible USB storage device', 'usb', 'usb', 'Example Bus Name', 'usbstor', 'usbstor.sys', SHA1,
              'usb\\root_hub30\\4&1&0&0', '{11111111-2222-3333-4444-555555555555}',
              'usb\\vid_0000&pid_0001&rev_0100,usb\\vid_0000&pid_0001', 'usbstor.inf')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class DriverRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(amcache.driver_row(_Key(DRIVER, name=DRIVER_PATH)), DRIVER_ROW)

    def test_an_identifier_of_another_shape_is_shown_as_stored_and_absent_values_are_blank(self):
        row = amcache.driver_row(_Key({'DriverId': 'abc', 'DriverSigned': '0'}, name='c:/x.sys'))
        self.assertEqual(row, (WRITTEN_UTC, '', 'c:/x.sys', 'abc', '', '', '', '', '', '', '0', '', '', '', ''))
        self.assertEqual(amcache.driver_row(_Key({}, name='c:/y.sys'))[3], '')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class DeviceRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(amcache.device_row(_Key(DEVICE, name=DEVICE_NAME)), DEVICE_ROW)

    def test_an_entry_without_install_dates_or_a_driver(self):
        entry = _Key({'Model': 'Volume', 'Enumerator': 'storage', 'Class': 'volume'}, name='storage/volume/1')
        self.assertEqual(amcache.device_row(entry),
                         (WRITTEN_UTC, '', '', 'storage/volume/1', 'Volume', '', '', 'volume', 'storage', '', '', '',
                          '', '', '', '', ''))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    HIVE = '/report/data/vol/Windows/appcompat/Programs/Amcache.hve'
    OTHER = '/report/data/old/Windows/appcompat/Programs/AMCACHE.HVE'

    def run_artifact(self, function, hives, files=None):
        def opener(path):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(amcache, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(amcache, 'logfunc', side_effect=logged.append):
            result = function.__wrapped__(_Context(files if files is not None else list(hives)))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_applications_come_from_the_application_key_only(self):
        hive = _Hive({'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)]),
                      'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\a.lnk'})]),
                      'Root\\InventoryApplicationFile': _Key(subkeys=[_Key({'ProgramId': '0000aa'})])})
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheApplications, {self.HIVE: hive})
        self.assertEqual(rows, [MSI_ROW])
        self.assertEqual(len(headers), len(MSI_ROW))
        self.assertEqual(headers[0], ('Key Last Write (UTC)', 'datetime'))
        self.assertEqual(headers[1:4], ('Install Date (as stored)', 'Name', 'Version'))
        self.assertEqual(headers[12:], ('Hidden ARP (as stored)', 'OS Version At Install', 'Program ID'))
        self.assertEqual(source, self.HIVE)
        self.assertEqual(logged, [])

    def test_shortcuts_come_from_the_shortcut_key_only(self):
        hive = _Hive({'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)]),
                      'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\a.lnk'}),
                                                                         _Key({'ShortcutPath': 'c:\\b.lnk'})])})
        (headers, rows, source), _opened, _logged = self.run_artifact(amcache.amcacheShortcuts, {self.HIVE: hive})
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), 'Shortcut Path'))
        self.assertEqual(rows, [(WRITTEN_UTC, 'C:\\a.lnk'), (WRITTEN_UTC, 'c:\\b.lnk')])
        self.assertEqual(source, self.HIVE)

    def test_a_hive_without_the_key_gives_no_rows_and_is_still_named(self):
        (_headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheShortcuts, {self.HIVE: _Hive({})})
        self.assertEqual((rows, source, logged), ([], self.HIVE, []))

    def test_transaction_logs_are_not_opened_as_hives(self):
        hive = _Hive({'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)])})
        files = [self.HIVE, self.HIVE + '.LOG1', self.HIVE + '.LOG2']
        (_headers, rows, source), opened, _logged = self.run_artifact(amcache.amcacheApplications, {self.HIVE: hive},
                                                                      files)
        self.assertEqual(opened, [self.HIVE])
        self.assertEqual((len(rows), source), (1, self.HIVE))

    def test_an_unreadable_hive_is_logged_by_its_evidence_path_and_the_other_is_still_read(self):
        good = _Hive({'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI), _Key(MSI)])})
        (_headers, rows, source), _opened, logged = self.run_artifact(
            amcache.amcacheApplications, {self.HIVE: ValueError('bad header'), self.OTHER: good})
        self.assertEqual(rows, [MSI_ROW, MSI_ROW])
        self.assertEqual(source, self.OTHER)
        self.assertEqual(logged, ['Amcache: could not read vol/Windows/appcompat/Programs/Amcache.hve: bad header'])

    def test_two_hives_are_both_read_and_both_named(self):
        one = _Hive({'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\a.lnk'})])})
        two = _Hive({'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\b.lnk'})])})
        (_headers, rows, source), _opened, _logged = self.run_artifact(amcache.amcacheShortcuts,
                                                                       {self.HIVE: one, self.OTHER: two})
        self.assertEqual([r[1] for r in rows], ['C:\\a.lnk', 'C:\\b.lnk'])
        self.assertEqual(source, self.HIVE + '\n' + self.OTHER)

    def test_drivers_and_devices_come_from_their_own_keys(self):
        hive = _Hive({'Root\\InventoryDriverBinary': _Key(subkeys=[_Key(DRIVER, name=DRIVER_PATH)]),
                      'Root\\InventoryDevicePnp': _Key(subkeys=[_Key(DEVICE, name=DEVICE_NAME)]),
                      'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)])})
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDrivers, {self.HIVE: hive})
        self.assertEqual(rows, [DRIVER_ROW])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), 'Driver Last Write (as stored)', 'Driver Path',
                                   'SHA-1', 'Driver Name', 'Service', 'Company', 'Product', 'Driver Version',
                                   'In Box (as stored)', 'Signed (as stored)', 'Kernel Mode (as stored)', 'INF',
                                   'Driver Package', 'PE Timestamp (as stored)'))
        self.assertEqual((source, logged), (self.HIVE, []))
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDevices, {self.HIVE: hive})
        self.assertEqual(rows, [DEVICE_ROW])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), 'Install Date (as stored)',
                                   'First Install Date (as stored)', 'Device', 'Model', 'Description', 'Manufacturer',
                                   'Class', 'Enumerator', 'Bus Reported Description', 'Service', 'Driver Name',
                                   'Driver SHA-1', 'Parent ID', 'Container ID', 'Hardware IDs', 'INF'))
        self.assertEqual((source, logged), (self.HIVE, []))

    def test_without_python_registry_nothing_is_read(self):
        functions = (amcache.amcacheApplications, amcache.amcacheShortcuts, amcache.amcacheDrivers,
                     amcache.amcacheDevices)
        with mock.patch.object(amcache, 'Registry', None), mock.patch.object(amcache, 'logfunc') as log, \
                mock.patch.object(amcache, 'open_hive') as opened:
            for function in functions:
                _headers, rows, source = function.__wrapped__(_Context([self.HIVE]))
                self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, len(functions))


if __name__ == '__main__':
    unittest.main()
