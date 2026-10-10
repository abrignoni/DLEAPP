"""Pin the Registry Autostart Points artifact (scripts/artifacts/windowsRegistryAutostartPoints.py).

The hives are stood in for by small objects that answer the python-registry calls the reader makes. The values are
the ones a default Windows 10 installation holds on the tested images, plus made-up ones.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsRegistryAutostartPoints as ap
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1 = datetime.datetime(2020, 9, 18, 21, 40, 22)
T2 = datetime.datetime(2021, 1, 2, 3, 4, 5)
W1, W2 = T1.replace(tzinfo=UTC), T2.replace(tzinfo=UTC)
WINLOGON = 'Microsoft\\Windows NT\\CurrentVersion\\Winlogon'
WINDOWS = 'Microsoft\\Windows NT\\CurrentVersion\\Windows'
SETUP = 'Microsoft\\Active Setup\\Installed Components'


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=(), written=T1):
        self._name, self._values, self._subkeys, self._written = name, values or {}, list(subkeys), written

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

    def timestamp(self):
        return self._written


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


SOFTWARE = _Hive({
    WINLOGON: _Key(values={'Shell': 'explorer.exe', 'Userinit': 'C:\\Windows\\system32\\userinit.exe,',
                           'AutoRestartShell': 1, '(default)': 'ignored'}),
    'WOW6432Node\\' + WINLOGON: _Key(values={'SHELL': 'explorer.exe'}, written=T2),
    WINDOWS: _Key(values={'AppInit_DLLs': '', 'LoadAppInit_DLLs': 0, 'RequireSignedAppInit_DLLs': 1,
                          'DesktopHeapLogging': 1}),
    SETUP: _Key(subkeys=[
        _Key('{89820200-ECBD-11cf-8B85-00AA005B4383}', {'(default)': 'Made-up component', 'StubPath': 'C:\\a.exe',
                                                       'Version': '1,0'}, written=T2),
        _Key('NoStub', {'(default)': 'No stub here', 'IsInstalled': 1}),
        _Key('>{22d6f312-b0f6-11d0-94ab-0080c74c7e95}', {'stubpath': b'\x01\xff'})]),
    'Microsoft\\NetSh': _Key(values={'2': 'ifmon.dll', 'dhcpclient': 'dhcpcmonitor.dll', '': 'ignored'}),
})
SYSTEM = _Hive({
    'Select': _Key(values={'Current': 2}),
    'ControlSet001\\Control\\Session Manager': _Key(values={'BootExecute': ['not the current set']}),
    'ControlSet002\\Control\\Session Manager': _Key(values={'BootExecute': ['autocheck autochk *', '', ''],
                                                            'SetupExecute': ['x']}),
    'ControlSet002\\Control\\Lsa': _Key(values={'Authentication Packages': ['msv1_0', ''],
                                                'Notification Packages': ['scecli', 'made', '', 'up', ''],
                                                'Security Packages': ['""', ''], 'LimitBlankPasswordUse': 1}),
    'ControlSet002\\Control\\Lsa\\OSConfig': _Key(values={'Security Packages': ['']}, written=T2),
    'ControlSet002\\Control\\Print\\Monitors': _Key(subkeys=[_Key('Local Port', {'Driver': 'localspl.dll'}),
                                                             _Key('Empty')]),
    'ControlSet002\\Services\\W32Time\\TimeProviders': _Key(subkeys=[
        _Key('NtpClient', {'DllName': '%systemroot%\\system32\\w32time.dll', 'Enabled': 1, 'InputProvider': 1})]),
})
NTUSER = _Hive({'Software\\' + WINLOGON: _Key(values={'Shell': 'C:\\Users\\a\\made-up.exe'}, written=T2)})


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Points(unittest.TestCase):
    def test_software(self):
        self.assertEqual(ap.point_rows(SOFTWARE, ap._SOFTWARE_POINTS), [  # pylint: disable=protected-access
            (W1, 'Winlogon', '', '', 'Shell', 'explorer.exe', WINLOGON),
            (W1, 'Winlogon', '', '', 'Userinit', 'C:\\Windows\\system32\\userinit.exe,', WINLOGON),
            (W2, 'Winlogon (Wow6432Node)', '', '', 'SHELL', 'explorer.exe', 'WOW6432Node\\' + WINLOGON),
            (W1, 'AppInit_DLLs', '', '', 'AppInit_DLLs', '', WINDOWS),
            (W1, 'AppInit_DLLs', '', '', 'LoadAppInit_DLLs', 0, WINDOWS),
            (W1, 'AppInit_DLLs', '', '', 'RequireSignedAppInit_DLLs', 1, WINDOWS),
            (W2, 'Active Setup', '{89820200-ECBD-11cf-8B85-00AA005B4383}', 'Made-up component', 'StubPath',
             'C:\\a.exe', SETUP + '\\{89820200-ECBD-11cf-8B85-00AA005B4383}'),
            (W1, 'Active Setup', '>{22d6f312-b0f6-11d0-94ab-0080c74c7e95}', '', 'stubpath', '01ff',
             SETUP + '\\>{22d6f312-b0f6-11d0-94ab-0080c74c7e95}'),
            (W1, 'Netsh Helper DLLs', '', '', '2', 'ifmon.dll', 'Microsoft\\NetSh'),
            (W1, 'Netsh Helper DLLs', '', '', 'dhcpclient', 'dhcpcmonitor.dll', 'Microsoft\\NetSh')])

    def test_system_reads_the_current_control_set(self):
        rows = ap.point_rows(SYSTEM, ap._SYSTEM_POINTS, 'ControlSet002\\')  # pylint: disable=protected-access
        self.assertEqual([row[1:] for row in rows], [
            ('BootExecute', '', '', 'BootExecute', 'autocheck autochk *', 'ControlSet002\\Control\\Session Manager'),
            ('LSA Packages', '', '', 'Authentication Packages', 'msv1_0', 'ControlSet002\\Control\\Lsa'),
            ('LSA Packages', '', '', 'Notification Packages', 'scecli | made |  | up', 'ControlSet002\\Control\\Lsa'),
            ('LSA Packages', '', '', 'Security Packages', '""', 'ControlSet002\\Control\\Lsa'),
            ('LSA Packages (OSConfig)', '', '', 'Security Packages', '', 'ControlSet002\\Control\\Lsa\\OSConfig'),
            ('Print Monitors', 'Local Port', '', 'Driver', 'localspl.dll',
             'ControlSet002\\Control\\Print\\Monitors\\Local Port'),
            ('Time Providers', 'NtpClient', '', 'DllName', '%systemroot%\\system32\\w32time.dll',
             'ControlSet002\\Services\\W32Time\\TimeProviders\\NtpClient'),
            ('Time Providers', 'NtpClient', '', 'Enabled', 1,
             'ControlSet002\\Services\\W32Time\\TimeProviders\\NtpClient')])
        self.assertEqual({row[0] for row in rows}, {W1, W2})

    def test_a_hive_without_the_keys(self):
        self.assertEqual(ap.point_rows(_Hive({}), ap._SOFTWARE_POINTS), [])  # pylint: disable=protected-access


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Processor(unittest.TestCase):
    def run_on(self, hives):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        for relative, hive in hives.items():
            path = pathlib.Path(folder.name, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] is None:
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda path: os.path.relpath(path, folder.name).replace(os.sep, '/')
        with mock.patch.object(ap, 'found_hives', return_value=list(reversed(sorted(by_path)))), \
                mock.patch.object(ap, 'open_hive', side_effect=opened), mock.patch.object(ap, 'logfunc') as log:
            headers, rows, located = ap.windowsRegistryAutostartPoints.__wrapped__(context)
        return headers, rows, [os.path.relpath(p, folder.name).replace(os.sep, '/') for p in located.split('\n') if p], log

    def test_three_hives(self):
        headers, rows, located, log = self.run_on({
            'C/Windows/System32/config/SOFTWARE': SOFTWARE, 'C/Windows/System32/config/SYSTEM': SYSTEM,
            'C/Users/a/NTUSER.DAT': NTUSER, 'C/Users/b/NTUSER.DAT': _Hive({}), 'C/Users/ab/NTUSER.DAT': None})
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'Location', 'Entry', 'Entry Label', 'Value',
                                   'Data', 'Scope', 'User', 'Key', 'Source File'))
        self.assertEqual(len(rows), 19)
        self.assertEqual(rows[0], (W2, 'Winlogon', '', '', 'Shell', 'C:\\Users\\a\\made-up.exe', 'User', 'a',
                                   'Software\\' + WINLOGON, 'C/Users/a/NTUSER.DAT'))
        self.assertEqual(rows[1][6:], ('Machine', '', WINLOGON, 'C/Windows/System32/config/SOFTWARE'))
        self.assertEqual(rows[11][1:6], ('BootExecute', '', '', 'BootExecute', 'autocheck autochk *'))
        self.assertEqual(rows[11][6:], ('Machine', '', 'ControlSet002\\Control\\Session Manager',
                                        'C/Windows/System32/config/SYSTEM'))
        self.assertEqual(located, ['C/Users/a/NTUSER.DAT', 'C/Windows/System32/config/SOFTWARE',
                                   'C/Windows/System32/config/SYSTEM'])
        log.assert_called_once()
        self.assertIn('could not read C/Users/ab/NTUSER.DAT: not a hive', log.call_args[0][0])

    def test_a_machine_hive_under_a_users_folder_has_no_user(self):
        rows = self.run_on({'Users/x/export/Windows/System32/config/SYSTEM': SYSTEM})[1]
        self.assertEqual({row[6:8] for row in rows}, {('Machine', '')})
        self.assertEqual(len(rows), 8)

    def test_no_library(self):
        with mock.patch.object(ap, 'Registry', None), mock.patch.object(ap, 'logfunc') as log:
            self.assertEqual(ap.windowsRegistryAutostartPoints.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
