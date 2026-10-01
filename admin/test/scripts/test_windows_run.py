"""Pin the Run, RunOnce, Policies\\Explorer\\Run and Load readers in scripts/artifacts/windowsRun.py.

The hives are stood in for by small objects that answer the python-registry calls the reader makes; the expected
rows are written out.
"""
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRun as run  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# the module's reader and key tables, named here once
rows_of = run._run_rows  # pylint: disable=protected-access
SOFTWARE_KEYS = run._SOFTWARE_KEYS  # pylint: disable=protected-access
NTUSER_KEYS = run._NTUSER_KEYS  # pylint: disable=protected-access
NTUSER_VALUES = run._NTUSER_VALUES  # pylint: disable=protected-access


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, values=()):
        self._values = [_Value(n, d) for n, d in values]

    def values(self):
        return self._values


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
        return path.split('/report/data/', 1)[1]


CV = 'Microsoft\\Windows\\CurrentVersion'
WINDOWS = 'Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows'
CMD = 'C:\\Windows\\System32\\cmd.exe /c rem example'
# the staged paths sit under the examiner's own Users folder, as they do on a real run
SOFTWARE = '/Users/examiner/report/data/vol/Windows/System32/config/SOFTWARE'
NTUSER = '/Users/examiner/report/data/vol/Users/alice/NTUSER.DAT'
COPIED_SOFTWARE = '/Users/examiner/report/data/vol/Users/bob/Desktop/SOFTWARE'


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class RunRowsTest(unittest.TestCase):
    def test_every_named_value_of_each_key_is_a_row_with_its_key_label(self):
        reg = _Hive({
            CV + '\\Run': _Key([('Tool', CMD), ('', 'default value data')]),
            CV + '\\RunOnce': _Key([('Once', 'once.exe')]),
            'WOW6432Node\\' + CV + '\\Run': _Key([('Tool32', 'tool32.exe')]),
            CV + '\\Policies\\Explorer\\Run': _Key([('Policy', 'policy.exe')]),
        })
        rows = list(rows_of(reg, SOFTWARE_KEYS, 'Machine', '', 'vol/SOFTWARE'))
        self.assertEqual(rows, [
            ('Tool', CMD, 'Run', 'Machine', '', 'vol/SOFTWARE'),
            ('Once', 'once.exe', 'RunOnce', 'Machine', '', 'vol/SOFTWARE'),
            ('Tool32', 'tool32.exe', 'Run (Wow6432Node)', 'Machine', '', 'vol/SOFTWARE'),
            ('Policy', 'policy.exe', 'Policies\\Explorer\\Run', 'Machine', '', 'vol/SOFTWARE'),
        ])

    def test_only_the_load_value_of_the_windows_key_is_read_whatever_its_case(self):
        reg = _Hive({
            'Software\\' + CV + '\\Policies\\Explorer\\Run': _Key([('UserPolicy', 'user.exe')]),
            WINDOWS: _Key([('Device', 'printer'), ('LOAD', CMD), ('MenuDropAlignment', '0'), ('Run', 'not read')]),
        })
        rows = list(rows_of(reg, NTUSER_KEYS, 'User', 'alice', 'vol/NTUSER.DAT', NTUSER_VALUES))
        self.assertEqual(rows, [
            ('UserPolicy', 'user.exe', 'Policies\\Explorer\\Run', 'User', 'alice', 'vol/NTUSER.DAT'),
            ('LOAD', CMD, 'Windows NT\\CurrentVersion\\Windows', 'User', 'alice', 'vol/NTUSER.DAT'),
        ])

    def test_without_value_names_the_windows_key_is_not_read(self):
        reg = _Hive({WINDOWS: _Key([('Load', CMD)])})
        self.assertEqual(list(rows_of(reg, NTUSER_KEYS, 'User', 'alice', 'x')), [])

    def test_data_that_is_not_text_is_written_as_text(self):
        reg = _Hive({CV + '\\Run': _Key([('Number', 7)])})
        rows = list(rows_of(reg, SOFTWARE_KEYS, 'Machine', '', 'x'))
        self.assertEqual(rows, [('Number', '7', 'Run', 'Machine', '', 'x')])

    def test_the_keys_read(self):
        self.assertEqual([path for _label, path in SOFTWARE_KEYS], [
            CV + '\\Run', CV + '\\RunOnce', 'WOW6432Node\\' + CV + '\\Run', 'WOW6432Node\\' + CV + '\\RunOnce',
            CV + '\\Policies\\Explorer\\Run'])
        self.assertEqual([path for _label, path in NTUSER_KEYS], [
            'Software\\' + CV + '\\Run', 'Software\\' + CV + '\\RunOnce',
            'Software\\' + CV + '\\Policies\\Explorer\\Run'])
        self.assertEqual(NTUSER_VALUES, (('Windows NT\\CurrentVersion\\Windows', WINDOWS, ('load',)),))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    def run_artifact(self, hives, files=None):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(run, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(run, 'logfunc', side_effect=logged.append):
            result = run.runKeys.__wrapped__(_Context(files if files is not None else list(hives)))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_machine_and_user_rows_and_the_load_value_only_from_a_user_hive(self):
        software = _Hive({
            CV + '\\Policies\\Explorer\\Run': _Key([('MachinePolicy', 'machine.exe')]),
            # a Windows key in the SOFTWARE hive is not where the Load value is read from
            WINDOWS: _Key([('Load', 'not read from SOFTWARE')]),
            'Microsoft\\Windows NT\\CurrentVersion\\Windows': _Key([('Load', 'not read either')]),
        })
        ntuser = _Hive({
            'Software\\' + CV + '\\Run': _Key([('Tool', CMD)]),
            WINDOWS: _Key([('Load', 'load.exe')]),
        })
        (headers, rows, source), opened, logged = self.run_artifact(
            {SOFTWARE: software, NTUSER: ntuser}, [SOFTWARE, SOFTWARE + '.LOG1', NTUSER, NTUSER + '.LOG2'])
        self.assertEqual(headers, ('Name', 'Command', 'Key', 'Scope', 'User', 'Source File'))
        self.assertEqual(rows, [
            ('MachinePolicy', 'machine.exe', 'Policies\\Explorer\\Run', 'Machine', '',
             'vol/Windows/System32/config/SOFTWARE'),
            ('Tool', CMD, 'Run', 'User', 'alice', 'vol/Users/alice/NTUSER.DAT'),
            ('Load', 'load.exe', 'Windows NT\\CurrentVersion\\Windows', 'User', 'alice', 'vol/Users/alice/NTUSER.DAT'),
        ])
        self.assertEqual(opened, [SOFTWARE, NTUSER])
        self.assertEqual(source, SOFTWARE + '\n' + NTUSER)
        self.assertEqual(logged, [])

    def test_a_machine_row_has_no_user_even_when_the_hive_sits_under_a_users_folder(self):
        software = _Hive({CV + '\\Run': _Key([('Tool', CMD)])})
        (_headers, rows, _source), _opened, _logged = self.run_artifact({COPIED_SOFTWARE: software})
        self.assertEqual(rows, [('Tool', CMD, 'Run', 'Machine', '', 'vol/Users/bob/Desktop/SOFTWARE')])

    def test_a_hive_with_no_entries_is_not_named_and_an_unreadable_one_is_logged(self):
        (_headers, rows, source), _opened, logged = self.run_artifact(
            {SOFTWARE: ValueError('bad header'), NTUSER: _Hive({})})
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(
            logged, ['Run and RunOnce Keys: could not read vol/Windows/System32/config/SOFTWARE: bad header'])

    def test_without_python_registry_nothing_is_read(self):
        with mock.patch.object(run, 'Registry', None), mock.patch.object(run, 'logfunc') as log, \
                mock.patch.object(run, 'open_hive') as opened:
            _headers, rows, source = run.runKeys.__wrapped__(_Context([SOFTWARE]))
        self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
