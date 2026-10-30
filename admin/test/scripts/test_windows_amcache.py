"""Pin the InventoryApplicationFile, InventoryApplication, InventoryApplicationShortcut, InventoryDriverBinary,
InventoryDevicePnp, InventoryDeviceContainer and InventoryDriverPackage readers, and the Windows 8 format
Root\\File and Root\\Programs readers, in scripts/artifacts/windowsAmcache.py.

The hive is stood in for by small objects that answer the python-registry calls the readers make; the expected rows
are written out.
"""
import datetime
import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsAmcache as amcache  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

WRITTEN = datetime.datetime(2023, 2, 22, 18, 47, 15, 69435)
WRITTEN_UTC = WRITTEN.replace(tzinfo=datetime.timezone.utc)


class _Value:
    def __init__(self, data, name=''):
        self._data = data
        self._name = name

    def name(self):
        return self._name

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

    def values(self):
        return [_Value(data, name) for name, data in self._values.items()]

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


def _row(builder, entry):
    """The row builder's columns for a hive subkey, after the time the reader puts first."""
    record = amcache._hive_record(entry)  # pylint: disable=protected-access
    return (record.written,) + builder(record)


def _hive_only(row):
    """An artifact row from the hive alone: the hive's time, no database time, then the columns."""
    return (row[0], None) + row[1:]


DB_TIME = ('Database Row Modified (UTC)', 'datetime')


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
           '{22222222-2222-2222-2222-222222222222}', '', '{22222222-2222-2222-2222-222222222222}', '', 0,
           '10.0.0.17763', '0000aa')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ApplicationRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.application_row, _Key(MSI)), MSI_ROW)

    def test_a_store_package_entry(self):
        entry = _Key({'ProgramId': '0000cc', 'Name': 'Example.App', 'Version': '2.0.0.0', 'Publisher': 'CN=Example',
                      'Source': 'AppxPackage', 'StoreAppType': 'Win10StoreApp', 'HiddenArp': 1,
                      'OSVersionAtInstallTime': '10.0.0.19041', 'InstallDate': '',
                      'PackageFullName': 'Example.App_2.0.0.0_x64__abc', 'MsiProductCode': '',
                      'RootDirPath': 'C:\\Program Files\\WindowsApps\\Example.App_2.0.0.0_x64__abc',
                      'UninstallString': '', 'RegistryKeyPath': ''})
        self.assertEqual(_row(amcache.application_row, entry),
                         (WRITTEN_UTC, '', 'Example.App', '2.0.0.0', 'CN=Example', 'AppxPackage', 'Win10StoreApp',
                          'C:\\Program Files\\WindowsApps\\Example.App_2.0.0.0_x64__abc', '', '',
                          'Example.App_2.0.0.0_x64__abc', '', '', 1, '10.0.0.19041', '0000cc'))

    def test_a_per_user_entry_carries_its_user_sid_and_no_os_version(self):
        entry = _Key({'ProgramId': '0000dd', 'Name': 'Example Per User', 'Source': 'AddRemoveProgramPerUser',
                      'UserSid': 'S-1-5-21-1-2-3-1001', 'HiddenArp': 0, 'InstallDate': '07/30/2026 16:51:05',
                      'MsiInstallDate': '07/30/2026 00:00:00'})
        self.assertEqual(_row(amcache.application_row, entry),
                         (WRITTEN_UTC, '07/30/2026 16:51:05', 'Example Per User', '', '',
                          'AddRemoveProgramPerUser', '', '', '', '', '', '', 'S-1-5-21-1-2-3-1001', 0, '', '0000dd'))

    def test_absent_values_are_blank_and_a_stored_zero_is_kept(self):
        row = _row(amcache.application_row, _Key({'HiddenArp': 0}, written=None))
        self.assertEqual(row, (None, '', '', '', '', '', '', '', '', '', '', '', '', 0, '', ''))

    def test_a_time_that_already_carries_a_zone_is_left_alone(self):
        zone = datetime.timezone(datetime.timedelta(hours=-5))
        aware = WRITTEN.replace(tzinfo=zone)
        self.assertEqual(_row(amcache.application_row, _Key({}, written=aware))[0].utcoffset(),
                         datetime.timedelta(hours=-5))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ShortcutRowTest(unittest.TestCase):
    def test_path_and_time(self):
        path = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Example\\Example Tool.lnk'
        self.assertEqual(_row(amcache.shortcut_row, _Key({'ShortcutPath': path})), (WRITTEN_UTC, path, '', '', ''))

    def test_target_aumid_and_program_id_each_land_in_their_own_column(self):
        path = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Example\\Example Tool.lnk'
        entry = _Key({'ShortcutPath': path, 'ShortcutTargetPath': 'C:\\Program Files\\Example\\tool.exe',
                      'ShortcutAumid': '{6D809377-6AF0-444B-8957-A3773F02200E}\\Example\\tool.exe',
                      'ShortcutProgramId': '0000' + 'ab' * 20})
        self.assertEqual(_row(amcache.shortcut_row, entry),
                         (WRITTEN_UTC, path, 'C:\\Program Files\\Example\\tool.exe',
                          '{6D809377-6AF0-444B-8957-A3773F02200E}\\Example\\tool.exe', '0000' + 'ab' * 20))

    def test_an_entry_without_the_value(self):
        self.assertEqual(_row(amcache.shortcut_row, _Key({})), (WRITTEN_UTC, '', '', '', ''))


FILE_SHA1 = 'da39a3ee5e6b4b0d3255bfef95601890afd80709'
FILE = {'LowerCaseLongPath': 'c:\\program files\\example\\example tool setup.exe', 'FileId': '0000' + FILE_SHA1,
        'Name': 'Example Tool Setup.exe', 'Publisher': 'example corp', 'ProductName': 'example tool',
        'Version': '1.2.3.4', 'Size': 1024, 'LinkDate': '02/20/2023 10:11:12', 'ProgramId': '0006aa',
        'BinaryType': 'pe64_amd64', 'Language': 1033, 'Usn': 4096}
FILE_NAME = 'example tool set|0123456789abcdef'
FILE_ROW = (WRITTEN_UTC, 'c:\\program files\\example\\example tool setup.exe', FILE_SHA1,
            'Example Tool Setup.exe', 'example corp', 'example tool', '1.2.3.4', 1024, '02/20/2023 10:11:12', '0006aa',
            FILE_NAME)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class FileRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.file_row, _Key(FILE, name=FILE_NAME)), FILE_ROW)

    def test_an_entry_holding_only_an_identifier_and_a_program_id(self):
        entry = _Key({'FileId': '0000' + FILE_SHA1, 'ProgramId': '0006bb'}, name='setup.exe|00112233445566')
        self.assertEqual(_row(amcache.file_row, entry),
                         (WRITTEN_UTC, '', FILE_SHA1, '', '', '', '', '', '', '0006bb', 'setup.exe|00112233445566'))

    def test_a_blank_identifier_and_a_stored_size_of_zero(self):
        row = _row(amcache.file_row, _Key({'FileId': '', 'Size': 0, 'ProgramId': '0006cc'}, written=None, name='a|1'))
        self.assertEqual(row, (None, '', '', '', '', '', '', 0, '', '0006cc', 'a|1'))


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
CONTAINER = {'ModelName': 'Example Model', 'Icon': 'c:\\windows\\system32\\ddores.dll,-2',
             'FriendlyName': 'Example Drive', 'ModelNumber': 'EX-1', 'Manufacturer': 'Example Corp',
             'ModelId': '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}', 'PrimaryCategory': 'Storage',
             'Categories': 'Storage.USB', 'IsMachineContainer': '0', 'DiscoveryMethod': 'PnP', 'IsConnected': '1',
             'IsActive': '2', 'IsPaired': '3', 'IsNetworked': '4', 'State': 9}
CONTAINER_NAME = '{11111111-2222-3333-4444-555555555555}'
CONTAINER_ROW = (WRITTEN_UTC, CONTAINER_NAME, 'Example Drive', 'Example Model', 'EX-1', 'Example Corp', 'Storage',
                 'Storage.USB', '0', '1', '2', '3', '4', 'PnP', 9, '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}',
                 'c:\\windows\\system32\\ddores.dll,-2')
PACKAGE = {'ClassGuid': '{4d36e972-e325-11ce-bfc1-08002be10318}', 'Class': 'net',
           'Directory': 'c:\\windows\\system32\\driverstore\\filerepository\\example.inf_amd64_0123456789abcdef',
           'Date': '2018-9-15', 'Version': '1.2.3.4', 'Provider': 'Example Corp', 'SubmissionId': '12345',
           'DriverInBox': '0', 'Inf': 'oem7.inf', 'Hwids': 'pci\\ven_0000&dev_0001', 'SYSFILE': 'example.sys',
           'IsActive': '1', 'FlightIds': 'x', 'RecoveryIds': 'y'}
PACKAGE_NAME = 'example.inf_amd64_0123456789abcdef'
PACKAGE_ROW = (WRITTEN_UTC, '2018-9-15', PACKAGE_NAME, '1.2.3.4', 'Example Corp', 'net',
               '{4d36e972-e325-11ce-bfc1-08002be10318}',
               'c:\\windows\\system32\\driverstore\\filerepository\\example.inf_amd64_0123456789abcdef', 'oem7.inf',
               'pci\\ven_0000&dev_0001', 'example.sys', '0', '1', '12345')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class DriverRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.driver_row, _Key(DRIVER, name=DRIVER_PATH)), DRIVER_ROW)

    def test_an_identifier_of_another_shape_is_shown_as_stored_and_absent_values_are_blank(self):
        row = _row(amcache.driver_row, _Key({'DriverId': 'abc', 'DriverSigned': '0'}, name='c:/x.sys'))
        self.assertEqual(row, (WRITTEN_UTC, '', 'c:/x.sys', 'abc', '', '', '', '', '', '', '0', '', '', '', ''))
        self.assertEqual(_row(amcache.driver_row, _Key({}, name='c:/y.sys'))[3], '')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class DeviceRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.device_row, _Key(DEVICE, name=DEVICE_NAME)), DEVICE_ROW)

    def test_an_entry_without_install_dates_or_a_driver(self):
        entry = _Key({'Model': 'Volume', 'Enumerator': 'storage', 'Class': 'volume'}, name='storage/volume/1')
        self.assertEqual(_row(amcache.device_row, entry),
                         (WRITTEN_UTC, '', '', 'storage/volume/1', 'Volume', '', '', 'volume', 'storage', '', '', '',
                          '', '', '', '', ''))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ContainerRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.container_row, _Key(CONTAINER, name=CONTAINER_NAME)), CONTAINER_ROW)

    def test_absent_values_are_blank_and_a_stored_state_of_zero_is_kept(self):
        row = _row(amcache.container_row, _Key({'State': 0, 'IsConnected': '0'}, name='{a}'))
        self.assertEqual(row, (WRITTEN_UTC, '{a}', '', '', '', '', '', '', '', '0', '', '', '', '', 0, '', ''))

    def test_a_value_stored_as_a_number_is_left_a_number_in_every_column(self):
        row = _row(amcache.container_row, _Key({name: 7 for name in CONTAINER}, name='{c}'))
        self.assertEqual(row, (WRITTEN_UTC, '{c}') + (7,) * 15)

    def test_the_unnamed_value_is_not_reported(self):
        entry = _Key({'': 'x', 'FriendlyName': 'PC'}, name='{b}')
        self.assertEqual(_row(amcache.container_row, entry),
                         (WRITTEN_UTC, '{b}', 'PC', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class PackageRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(_row(amcache.package_row, _Key(PACKAGE, name=PACKAGE_NAME)), PACKAGE_ROW)

    def test_a_value_stored_as_a_number_is_left_a_number_in_every_column(self):
        values = {name: 7 for name in PACKAGE if name not in ('FlightIds', 'RecoveryIds')}
        row = _row(amcache.package_row, _Key(values, name='a.inf_amd64_1'))
        self.assertEqual(row, (WRITTEN_UTC, 7, 'a.inf_amd64_1') + (7,) * 11)

    def test_an_entry_without_the_active_value(self):
        entry = _Key({'Inf': 'oem1.inf', 'DriverInBox': '1', 'Date': '2006-6-21'}, name='a.inf_amd64_1')
        self.assertEqual(_row(amcache.package_row, entry),
                         (WRITTEN_UTC, '2006-6-21', 'a.inf_amd64_1', '', '', '', '', '', 'oem1.inf', '', '', '1', '',
                          ''))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    HIVE = '/report/data/vol/Windows/appcompat/Programs/Amcache.hve'
    OTHER = '/report/data/old/Windows/appcompat/Programs/AMCACHE.HVE'
    BARE = '/report/data/none/Amcache.hve'

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
        self.assertEqual(rows, [_hive_only(MSI_ROW)])
        self.assertEqual(len(headers), len(MSI_ROW) + 1)
        self.assertEqual(headers[:2], (('Key Last Write (UTC)', 'datetime'), DB_TIME))
        self.assertEqual(headers[2:5], ('Install Date (as stored)', 'Name', 'Version'))
        self.assertEqual(headers[12:], ('MSI Product Code', 'User SID', 'Hidden ARP (as stored)',
                                        'OS Version At Install', 'Program ID'))
        self.assertEqual(source, self.HIVE)
        self.assertEqual(logged, [])

    def test_shortcuts_come_from_the_shortcut_key_only(self):
        hive = _Hive({'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)]),
                      'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\a.lnk'}),
                                                                         _Key({'ShortcutPath': 'c:\\b.lnk'})])})
        (headers, rows, source), _opened, _logged = self.run_artifact(amcache.amcacheShortcuts, {self.HIVE: hive})
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'Shortcut Path', 'Target Path', 'AUMID',
                                   'Program ID'))
        self.assertEqual(rows, [(WRITTEN_UTC, None, 'C:\\a.lnk', '', '', ''),
                                (WRITTEN_UTC, None, 'c:\\b.lnk', '', '', '')])
        self.assertEqual(source, self.HIVE)

    def test_files_come_from_the_file_key_with_the_entry_key_last(self):
        hive = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[_Key(FILE, name=FILE_NAME)]),
                      'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)])})
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheApplicationFiles,
                                                                     {self.HIVE: hive})
        self.assertEqual(rows, [_hive_only(FILE_ROW)])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'File Path', 'SHA-1', 'Name', 'Publisher',
                                   'Product Name', 'Version', 'Size (bytes)', 'Link Date', 'Program ID', 'Entry Key'))
        self.assertEqual((source, logged), (self.HIVE, []))

    def test_a_hive_read_without_file_entries_or_without_the_key_is_still_named(self):
        empty = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[])})
        full = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[_Key(FILE, name=FILE_NAME),
                                                                      _Key({'ProgramId': '0006bb'}, name='b|2')])})
        (_headers, rows, source), opened, logged = self.run_artifact(
            amcache.amcacheApplicationFiles, {self.HIVE: empty, self.OTHER: full, self.BARE: _Hive({})},
            [self.HIVE, self.HIVE + '.LOG1', self.OTHER, self.BARE])
        self.assertEqual([r[-1] for r in rows], [FILE_NAME, 'b|2'])
        self.assertEqual(source, '\n'.join([self.HIVE, self.OTHER, self.BARE]))
        self.assertEqual(opened, [self.HIVE, self.OTHER, self.BARE])
        self.assertEqual(logged, [])

    def test_file_rows_of_two_hives_follow_the_order_the_files_were_found(self):
        one = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[_Key(FILE, name=FILE_NAME)])})
        two = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[_Key({'ProgramId': '0006bb'}, name='b|2')])})
        (_headers, rows, source), _opened, logged = self.run_artifact(
            amcache.amcacheApplicationFiles, {self.HIVE: one, self.BARE: _Hive({}), self.OTHER: two})
        self.assertEqual([r[-1] for r in rows], [FILE_NAME, 'b|2'])
        self.assertEqual(source, '\n'.join([self.HIVE, self.BARE, self.OTHER]))
        self.assertEqual(logged, [])

    def test_an_unreadable_hive_does_not_stop_the_file_rows_of_the_next(self):
        good = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[_Key(FILE, name=FILE_NAME)])})
        (_headers, rows, source), _opened, logged = self.run_artifact(
            amcache.amcacheApplicationFiles, {self.HIVE: ValueError('bad header'), self.OTHER: good})
        self.assertEqual((rows, source), ([_hive_only(FILE_ROW)], self.OTHER))
        self.assertEqual(logged, ['Amcache: could not read vol/Windows/appcompat/Programs/Amcache.hve: bad header'])

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
        self.assertEqual(rows, [_hive_only(MSI_ROW)] * 2)
        self.assertEqual(source, self.OTHER)
        self.assertEqual(logged, ['Amcache: could not read vol/Windows/appcompat/Programs/Amcache.hve: bad header'])

    def test_two_hives_are_both_read_and_both_named(self):
        one = _Hive({'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\a.lnk'})])})
        two = _Hive({'Root\\InventoryApplicationShortcut': _Key(subkeys=[_Key({'ShortcutPath': 'C:\\b.lnk'})])})
        (_headers, rows, source), _opened, _logged = self.run_artifact(amcache.amcacheShortcuts,
                                                                       {self.HIVE: one, self.OTHER: two})
        self.assertEqual([r[2] for r in rows], ['C:\\a.lnk', 'C:\\b.lnk'])
        self.assertEqual(source, self.HIVE + '\n' + self.OTHER)

    def test_drivers_and_devices_come_from_their_own_keys(self):
        hive = _Hive({'Root\\InventoryDriverBinary': _Key(subkeys=[_Key(DRIVER, name=DRIVER_PATH)]),
                      'Root\\InventoryDevicePnp': _Key(subkeys=[_Key(DEVICE, name=DEVICE_NAME)]),
                      'Root\\InventoryApplication': _Key(subkeys=[_Key(MSI)])})
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDrivers, {self.HIVE: hive})
        self.assertEqual(rows, [_hive_only(DRIVER_ROW)])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'Driver Last Write (as stored)', 'Driver Path',
                                   'SHA-1', 'Driver Name', 'Service', 'Company', 'Product', 'Driver Version',
                                   'In Box (as stored)', 'Signed (as stored)', 'Kernel Mode (as stored)', 'INF',
                                   'Driver Package', 'PE Timestamp (as stored)'))
        self.assertEqual((source, logged), (self.HIVE, []))
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDevices, {self.HIVE: hive})
        self.assertEqual(rows, [_hive_only(DEVICE_ROW)])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'Install Date (as stored)',
                                   'First Install Date (as stored)', 'Device', 'Model', 'Description', 'Manufacturer',
                                   'Class', 'Enumerator', 'Bus Reported Description', 'Service', 'Driver Name',
                                   'Driver SHA-1', 'Parent ID', 'Container ID', 'Hardware IDs', 'INF'))
        self.assertEqual((source, logged), (self.HIVE, []))

    def test_containers_and_packages_come_from_their_own_keys(self):
        hive = _Hive({'Root\\InventoryDeviceContainer': _Key(subkeys=[_Key(CONTAINER, name=CONTAINER_NAME)]),
                      'Root\\InventoryDriverPackage': _Key(subkeys=[_Key(PACKAGE, name=PACKAGE_NAME)]),
                      'Root\\InventoryDriverBinary': _Key(subkeys=[_Key(DRIVER, name=DRIVER_PATH)]),
                      'Root\\InventoryDevicePnp': _Key(subkeys=[_Key(DEVICE, name=DEVICE_NAME)])})
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDeviceContainers,
                                                                     {self.HIVE: hive})
        self.assertEqual(rows, [_hive_only(CONTAINER_ROW)])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'Container ID', 'Friendly Name',
                                   'Model Name', 'Model Number', 'Manufacturer', 'Primary Category', 'Categories',
                                   'Machine Container (as stored)', 'Connected (as stored)', 'Active (as stored)',
                                   'Paired (as stored)', 'Networked (as stored)', 'Discovery Method',
                                   'State (as stored)', 'Model ID', 'Icon'))
        self.assertEqual((source, logged), (self.HIVE, []))
        (headers, rows, source), _opened, logged = self.run_artifact(amcache.amcacheDriverPackages,
                                                                     {self.HIVE: hive})
        self.assertEqual(rows, [_hive_only(PACKAGE_ROW)])
        self.assertEqual(headers, (('Key Last Write (UTC)', 'datetime'), DB_TIME, 'Date (as stored)', 'Driver Package',
                                   'Version', 'Provider', 'Class', 'Class GUID', 'Directory', 'INF', 'Hardware IDs',
                                   'Files', 'In Box (as stored)', 'Active (as stored)', 'Submission ID'))
        self.assertEqual((source, logged), (self.HIVE, []))

    def test_a_hive_without_the_container_or_package_key_gives_no_rows_and_is_still_named(self):
        for function in (amcache.amcacheDeviceContainers, amcache.amcacheDriverPackages):
            (_headers, rows, source), _opened, logged = self.run_artifact(function, {self.HIVE: _Hive({})})
            self.assertEqual((rows, source, logged), ([], self.HIVE, []))

    def test_without_python_registry_nothing_is_read(self):
        functions = (amcache.amcacheApplicationFiles, amcache.amcacheApplications, amcache.amcacheShortcuts,
                     amcache.amcacheDrivers, amcache.amcacheDevices, amcache.amcacheDeviceContainers,
                     amcache.amcacheDriverPackages)
        with mock.patch.object(amcache, 'Registry', None), mock.patch.object(amcache, 'logfunc') as log, \
                mock.patch.object(amcache, 'open_hive') as opened:
            for function in functions:
                _headers, rows, source = function.__wrapped__(_Context([self.HIVE]))
                self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, len(functions))


FILETIME_LATER = 134373448019183342
LATER_UTC = datetime.datetime(2026, 10, 24, 19, 46, 41, 918334, tzinfo=datetime.timezone.utc)


def _make_database(path, table, columns, rows, extra_tables=()):
    """A database laid out as Windows 11 build 26200 writes it: one data table and a Metadata table."""
    connection = sqlite3.connect(path)
    names = ', '.join(f'"{name}"' for name in columns)
    connection.execute(f'CREATE TABLE "{table}" (ItemKey TEXT PRIMARY KEY, {names}, '
                       '"LastModified" INTEGER DEFAULT 0)')
    connection.execute('CREATE TABLE Metadata_0 (Name TEXT PRIMARY KEY, Value TEXT)')
    for other in extra_tables:
        connection.execute(f'CREATE TABLE "{other}" (ItemKey TEXT PRIMARY KEY, "Name" TEXT)')
        connection.execute(f'INSERT INTO "{other}" VALUES (?, ?)', ('other|1', 'not this table'))
    marks = ', '.join('?' * (len(columns) + 2))
    connection.executemany(f'INSERT INTO "{table}" VALUES ({marks})', rows)
    connection.commit()
    connection.close()


class FiletimeTest(unittest.TestCase):
    def test_a_filetime_is_a_utc_time_and_empty_or_zero_is_none(self):
        self.assertEqual(amcache._filetime(FILETIME_LATER), LATER_UTC)  # pylint: disable=protected-access
        for value in (None, 0, -1, '134373448019183342'):
            self.assertIsNone(amcache._filetime(value))  # pylint: disable=protected-access


class DatabaseRecordTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_rows_of_the_named_table_only_with_the_key_and_time_taken_out(self):
        path = os.path.join(self.folder, 'InventoryApplication.db')
        _make_database(path, 'InventoryApplication_0', ['Name', 'HiddenArp'],
                       [('a|1', 'Example', 0, FILETIME_LATER), ('b|2', None, None, 0)],
                       extra_tables=['InventoryApplicationFile_0', 'InventoryApplication_x'])
        records = amcache._database_records(path, 'InventoryApplication')  # pylint: disable=protected-access
        self.assertEqual([(r.key, r.values, r.written) for r in records],
                         [('a|1', {'Name': 'Example', 'HiddenArp': 0}, LATER_UTC),
                          ('b|2', {'Name': None, 'HiddenArp': None}, None)])

    def test_a_negative_driver_timestamp_is_read_as_the_unsigned_value(self):
        path = os.path.join(self.folder, 'InventoryDriverBinary.db')
        _make_database(path, 'InventoryDriverBinary_2', ['DriverTimeStamp', 'DriverCheckSum'],
                       [('c:/a.sys', -339481364, -5, FILETIME_LATER), ('c:/b.sys', 271750924, 7, FILETIME_LATER)])
        records = amcache._database_records(path, 'InventoryDriverBinary')  # pylint: disable=protected-access
        self.assertEqual([r.values for r in records],
                         [{'DriverTimeStamp': 3955485932, 'DriverCheckSum': -5},
                          {'DriverTimeStamp': 271750924, 'DriverCheckSum': 7}])

    def test_a_file_that_is_not_a_database_gives_none_or_raises_a_database_error(self):
        path = os.path.join(self.folder, 'InventoryApplication.db')
        with open(path, 'wb') as handle:
            handle.write(b'not a database' * 100)
        with mock.patch.object(amcache, 'logfunc'):
            try:
                result = amcache._database_records(path, 'InventoryApplication')  # pylint: disable=protected-access
            except sqlite3.DatabaseError:
                result = None
        self.assertIsNone(result)


class AgreesTest(unittest.TestCase):
    def test_a_hive_entry_agrees_when_each_value_it_holds_equals_the_database_value(self):
        database = amcache._Record('a|1', {'FileId': '0000ab', 'ProgramId': '0006', 'Size': 10,  # pylint: disable=protected-access
                                           'LowerCaseLongPath': 'c:\\a.exe'}, LATER_UTC)
        stub = amcache._Record('a|1', {'FileId': '0000ab', 'ProgramId': '0006'}, WRITTEN_UTC)  # pylint: disable=protected-access
        number_as_text = amcache._Record('a|1', {'Size': '10'}, WRITTEN_UTC)  # pylint: disable=protected-access
        self.assertTrue(amcache._agrees(stub, database))  # pylint: disable=protected-access
        self.assertTrue(amcache._agrees(number_as_text, database))  # pylint: disable=protected-access

    def test_a_different_value_or_a_value_the_database_lacks_disagrees(self):
        database = amcache._Record('a|1', {'Version': '2.0'}, LATER_UTC)  # pylint: disable=protected-access
        older = amcache._Record('a|1', {'Version': '1.0'}, WRITTEN_UTC)  # pylint: disable=protected-access
        extra = amcache._Record('a|1', {'Version': '2.0', 'OSVersionAtInstallTime': '10.0'}, WRITTEN_UTC)  # pylint: disable=protected-access
        empty_extra = amcache._Record('a|1', {'Version': '2.0', 'OSVersionAtInstallTime': ''}, WRITTEN_UTC)  # pylint: disable=protected-access
        self.assertFalse(amcache._agrees(older, database))  # pylint: disable=protected-access
        self.assertFalse(amcache._agrees(extra, database))  # pylint: disable=protected-access
        self.assertTrue(amcache._agrees(empty_extra, database))  # pylint: disable=protected-access


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class HiveAndDatabaseTest(unittest.TestCase):
    COLUMNS = ['ProgramId', 'FileId', 'LowerCaseLongPath', 'Name', 'Publisher', 'ProductName', 'Version', 'Size',
               'LinkDate']

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.one = os.path.join(self.root, 'C', 'Windows', 'appcompat', 'Programs')
        self.two = os.path.join(self.root, 'D', 'Windows', 'appcompat', 'Programs')
        os.makedirs(self.one)
        os.makedirs(self.two)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def database(self, folder, rows):
        path = os.path.join(folder, 'InventoryApplicationFile.db')
        _make_database(path, 'InventoryApplicationFile_0', self.COLUMNS, rows)
        return path

    def run_files(self, files, hives):
        def opener(path):
            return hives[path]
        logged = []
        with mock.patch.object(amcache, 'open_hive', side_effect=opener), \
                mock.patch.object(amcache, 'logfunc', side_effect=logged.append):
            return amcache.amcacheApplicationFiles.__wrapped__(_Context(files)), logged

    def test_a_stub_and_its_row_are_one_row_a_disagreeing_pair_two_and_a_database_only_row_its_own(self):
        hive_path = os.path.join(self.one, 'Amcache.hve')
        hive = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[
            _Key({'FileId': '0000' + FILE_SHA1, 'ProgramId': '0006aa'}, name='stub|1'),
            _Key({'FileId': '0000' + FILE_SHA1, 'Version': '1.0'}, name='old|2'),
            _Key({'ProgramId': '0006cc'}, name='hiveonly|3')])})
        database_path = self.database(self.one, [
            ('stub|1', '0006aa', '0000' + FILE_SHA1, 'c:\\a.exe', 'a.exe', '', '', '', 5, '', FILETIME_LATER),
            ('old|2', '', '0000' + FILE_SHA1, 'c:\\b.exe', 'b.exe', '', '', '2.0', 6, '', FILETIME_LATER),
            ('dbonly|4', '', '', 'c:\\d.exe', 'd.exe', '', '', '', None, '', 0)])
        ((headers, rows, source), logged) = self.run_files([hive_path, database_path], {hive_path: hive})
        self.assertEqual(headers[:2], (('Key Last Write (UTC)', 'datetime'), DB_TIME))
        self.assertEqual([(r[0], r[1], r[2], r[8], r[-1]) for r in rows],
                         [(WRITTEN_UTC, LATER_UTC, 'c:\\a.exe', 5, 'stub|1'),
                          (WRITTEN_UTC, None, '', '', 'old|2'),
                          (WRITTEN_UTC, None, '', '', 'hiveonly|3'),
                          (None, LATER_UTC, 'c:\\b.exe', 6, 'old|2'),
                          (None, None, 'c:\\d.exe', '', 'dbonly|4')])
        self.assertEqual(rows[1][7], '1.0')
        self.assertEqual(rows[3][7], '2.0')
        self.assertEqual(source, hive_path + '\n' + database_path)
        self.assertEqual(logged, ['Amcache InventoryApplicationFile: 3 hive entries, 3 database rows, '
                                  '1 reported as one row'])

    def test_a_database_is_paired_only_with_the_hive_of_its_own_folder(self):
        hive_path = os.path.join(self.one, 'Amcache.hve')
        hive = _Hive({'Root\\InventoryApplicationFile': _Key(subkeys=[
            _Key({'ProgramId': '0006aa'}, name='same|1')])})
        other_database = self.database(self.two, [
            ('same|1', '0006aa', '', 'c:\\x.exe', 'x.exe', '', '', '', 1, '', FILETIME_LATER)])
        ((_headers, rows, source), _logged) = self.run_files([hive_path, other_database], {hive_path: hive})
        self.assertEqual([(r[0], r[1], r[2]) for r in rows],
                         [(WRITTEN_UTC, None, ''), (None, LATER_UTC, 'c:\\x.exe')])
        self.assertEqual(source, hive_path + '\n' + other_database)

    def test_a_database_without_its_hive_is_read_without_python_registry(self):
        database_path = self.database(self.one, [
            ('a|1', '0006aa', '', 'c:\\a.exe', 'a.exe', '', '', '', 5, '', FILETIME_LATER)])
        with mock.patch.object(amcache, 'Registry', None):
            ((_headers, rows, source), logged) = self.run_files([database_path], {})
        self.assertEqual([(r[0], r[1], r[2]) for r in rows], [(None, LATER_UTC, 'c:\\a.exe')])
        self.assertEqual(source, database_path)
        self.assertEqual(len(logged), 1)


UTC = datetime.timezone.utc


class OldFormatTest(unittest.TestCase):
    """Root\\File\\<volume>\\<file> and Root\\Programs\\<program>, values named by hexadecimal numbers."""

    def hive(self, programs=True):
        file_entry = _Key({'15': 'c:\\tools\\a.exe', '101': '0000' + 'ab' * 20, '6': 4096, '0': 'Product',
                           '1': 'Company', '5': '1.2.3', 'c': 'Description', '100': 'prog1',
                           '11': 130000000000000000, '12': 130000000010000000, '17': 130000000020000000,
                           'f': 1400000000, 'd': 7}, name='1a2b00000c3d')
        bare = _Key({'15': 'c:\\b.exe', '17': 0}, name='5')
        volume = _Key(subkeys=[file_entry, bare], name='{volume-guid}')
        program = _Key({'0': 'Program Name', '1': '9.0', '2': 'Vendor', '3': '1033', '6': 'Msi',
                        '7': ['HKLM\\Uninstall\\x', ''], 'a': 1600000000, 'b': 0, 'd': ['c:\\one', 'c:\\two'],
                        'f': 'pc', '10': 'pk', '11': ['{m1}'], '12': ['{m2}'], '13': 1,
                        'Files': ['{volume-guid}\\1a2b00000c3d', '{volume-guid}\\5', '', '']}, name='prog1')
        keys = {'Root\\File': _Key(subkeys=[volume])}
        if programs:
            keys['Root\\Programs'] = _Key(subkeys=[program])
        return _Hive(keys)

    def test_file_rows(self):
        rows = amcache.old_file_rows(self.hive())
        epoch = datetime.datetime(1601, 1, 1, tzinfo=UTC)
        self.assertEqual(rows[0], (
            WRITTEN_UTC, epoch + datetime.timedelta(microseconds=13000000000000000),
            epoch + datetime.timedelta(microseconds=13000000001000000),
            epoch + datetime.timedelta(microseconds=13000000002000000),
            datetime.datetime(2014, 5, 13, 16, 53, 20, tzinfo=UTC), 'c:\\tools\\a.exe', 'ab' * 20, 4096,
            'Product', 'Company', '1.2.3', 'Description', 'prog1', 'Program Name', '{volume-guid}', '1a2b00000c3d'))
        # A 0 FILETIME is blank; values the subkey does not hold are blank; no program means no name.
        self.assertEqual(rows[1], (WRITTEN_UTC, None, None, None, None, 'c:\\b.exe', '', '', '', '', '', '', '',
                                   '', '{volume-guid}', '5'))

    def test_a_program_id_without_a_programs_key_gives_no_name(self):
        self.assertEqual(amcache.old_file_rows(self.hive(programs=False))[0][13], '')

    def test_program_rows(self):
        self.assertEqual(amcache.old_program_rows(self.hive()), [(
            WRITTEN_UTC, datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=UTC), None, 'Program Name', '9.0',
            'Vendor', '1033', 'Msi', 'HKLM\\Uninstall\\x', 'c:\\one\nc:\\two', 'pc', 'pk', '{m1}', '{m2}', 2,
            '{volume-guid}\\1a2b00000c3d\n{volume-guid}\\5', 'prog1')])

    def test_a_hive_without_the_keys_gives_none(self):
        self.assertIsNone(amcache.old_file_rows(_Hive({})))
        self.assertIsNone(amcache.old_program_rows(_Hive({})))


if __name__ == '__main__':
    unittest.main()
