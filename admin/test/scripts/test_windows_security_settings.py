"""Pin the Security Settings artifact (scripts/artifacts/windowsSecuritySettings.py).

The hives are stood in for by small objects that answer the python-registry calls the reader makes; the values are
made up.
"""
import datetime
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsSecuritySettings as ss
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1 = datetime.datetime(2026, 10, 10, 18, 48, 57)
T2 = datetime.datetime(2020, 9, 18, 21, 40, 22)
W1, W2 = T1.replace(tzinfo=UTC), T2.replace(tzinfo=UTC)
POLICIES = 'Microsoft\\Windows\\CurrentVersion\\Policies\\System'
WINLOGON = 'Microsoft\\Windows NT\\CurrentVersion\\Winlogon'
PS = 'Policies\\Microsoft\\Windows\\PowerShell\\'


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, values, written=T1):
        self._values, self._written = values, written

    def values(self):
        return [_Value(name, data) for name, data in self._values.items()]

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(name, self._values[name])

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
    POLICIES: _Key({'enablelua': 1, 'ConsentPromptBehaviorAdmin': 5, 'LocalAccountTokenFilterPolicy': 1,
                    'EnableVirtualization': 1}),
    POLICIES + '\\Audit': _Key({'ProcessCreationIncludeCmdLine_Enabled': 1}, T2),
    PS + 'Transcription': _Key({'EnableTranscripting': 1, 'OutputDirectory': 'C:\\t'}, T2),
    WINLOGON: _Key({'AutoAdminLogon': '1', 'DefaultUserName': 'made-up user', 'DefaultPassword': 'made-up',
                    'Shell': 'explorer.exe'}),
})
SYSTEM = _Hive({
    'Select': _Key({'Current': 2}),
    'ControlSet001\\Control\\Terminal Server': _Key({'fDenyTSConnections': 1}),
    'ControlSet002\\Control\\Terminal Server': _Key({'fDenyTSConnections': 0, 'TSEnabled': 1}, T2),
    'ControlSet002\\Control\\Terminal Server\\WinStations\\RDP-Tcp': _Key({'PortNumber': 3390}, T2),
    'ControlSet002\\Control\\SecurityProviders\\WDigest': _Key({'UseLogonCredential': 1, 'Negotiate': 0}, T2),
    'ControlSet002\\Control\\Lsa': _Key({'RunAsPPL': 2, 'NoLMHash': b'\x01\x00', 'LmCompatibilityLevel': ['a', 'b']}),
})
SOFTWARE_ROWS = [
    ('', 'Remote Desktop', 'fDenyTSConnections', '', 'No', 'Policies\\Microsoft\\Windows NT\\Terminal Services'),
    (W1, 'User Account Control', 'EnableLUA', 1, 'Yes', POLICIES),
    (W1, 'User Account Control', 'ConsentPromptBehaviorAdmin', 5, 'Yes', POLICIES),
    (W1, 'User Account Control', 'PromptOnSecureDesktop', '', 'No', POLICIES),
    (W1, 'User Account Control', 'FilterAdministratorToken', '', 'No', POLICIES),
    (W1, 'User Account Control', 'LocalAccountTokenFilterPolicy', 1, 'Yes', POLICIES),
    (W2, 'Logging', 'ProcessCreationIncludeCmdLine_Enabled', 1, 'Yes', POLICIES + '\\Audit'),
    ('', 'Logging', 'EnableScriptBlockLogging', '', 'No', PS + 'ScriptBlockLogging'),
    ('', 'Logging', 'EnableModuleLogging', '', 'No', PS + 'ModuleLogging'),
    (W2, 'Logging', 'EnableTranscripting', 1, 'Yes', PS + 'Transcription'),
    (W1, 'Automatic Logon', 'AutoAdminLogon', '1', 'Yes', WINLOGON),
    (W1, 'Automatic Logon', 'DefaultUserName', 'made-up user', 'Yes', WINLOGON),
    (W1, 'Automatic Logon', 'DefaultDomainName', '', 'No', WINLOGON),
    (W1, 'Automatic Logon', 'DefaultPassword', 'made-up', 'Yes', WINLOGON)]
SYSTEM_ROWS = [
    (W2, 'Remote Desktop', 'fDenyTSConnections', 0, 'Yes', 'ControlSet002\\Control\\Terminal Server'),
    (W2, 'Remote Desktop', 'PortNumber', 3390, 'Yes', 'ControlSet002\\Control\\Terminal Server\\WinStations\\RDP-Tcp'),
    (W1, 'LSA', 'RunAsPPL', 2, 'Yes', 'ControlSet002\\Control\\Lsa'),
    (W1, 'LSA', 'LmCompatibilityLevel', 'a | b', 'Yes', 'ControlSet002\\Control\\Lsa'),
    (W1, 'LSA', 'NoLMHash', '0100', 'Yes', 'ControlSet002\\Control\\Lsa'),
    (W2, 'LSA', 'UseLogonCredential', 1, 'Yes', 'ControlSet002\\Control\\SecurityProviders\\WDigest')]


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Settings(unittest.TestCase):
    def test_software(self):
        self.assertEqual(ss.setting_rows(SOFTWARE, ss._SOFTWARE_SETTINGS), SOFTWARE_ROWS)  # pylint: disable=protected-access

    def test_system_reads_the_named_control_set(self):
        rows = ss.setting_rows(SYSTEM, ss._SYSTEM_SETTINGS, 'ControlSet002\\')  # pylint: disable=protected-access
        self.assertEqual(rows, SYSTEM_ROWS)

    def test_an_empty_hive_gives_every_setting_as_not_stored(self):
        rows = ss.setting_rows(_Hive({}), ss._SOFTWARE_SETTINGS)  # pylint: disable=protected-access
        self.assertEqual(len(rows), 14)
        self.assertEqual({(row[0], row[3], row[4]) for row in rows}, {('', '', 'No')})

    def test_processor(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        for name, hive in (('a/Windows/System32/config/SOFTWARE', SOFTWARE), ('a/Windows/System32/config/SYSTEM', SYSTEM),
                           ('b/Windows/System32/config/SOFTWARE', None)):
            path = pathlib.Path(folder.name, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] is None:
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: pathlib.Path(p).relative_to(folder.name).as_posix()
        with mock.patch.object(ss, 'found_hives', return_value=sorted(by_path, reverse=True)), \
                mock.patch.object(ss, 'open_hive', side_effect=opened), mock.patch.object(ss, 'logfunc') as log:
            headers, rows, located = ss.windowsSecuritySettings.__wrapped__(context)
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'Area', 'Setting', 'Data', 'Stored', 'Key',
                                   'Source File'))
        self.assertEqual(rows, [row + ('a/Windows/System32/config/SOFTWARE',) for row in SOFTWARE_ROWS]
                         + [row + ('a/Windows/System32/config/SYSTEM',) for row in SYSTEM_ROWS])
        self.assertEqual(located, '\n'.join(str(pathlib.Path(folder.name, 'a', 'Windows', 'System32', 'config', name))
                                            for name in ('SOFTWARE', 'SYSTEM')))
        log.assert_called_once()
        self.assertIn('could not read b/Windows/System32/config/SOFTWARE: not a hive', log.call_args[0][0])

    def test_no_library(self):
        with mock.patch.object(ss, 'Registry', None), mock.patch.object(ss, 'logfunc') as log:
            self.assertEqual(ss.windowsSecuritySettings.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
