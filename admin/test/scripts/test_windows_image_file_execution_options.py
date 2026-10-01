"""Pin the Image File Execution Options and SilentProcessExit readers in
scripts/artifacts/windowsImageFileExecutionOptions.py.

The hive is stood in for by small objects that answer the python-registry calls the readers make; the expected rows
are written out.
"""
import datetime
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsImageFileExecutionOptions as ifeo  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

T1 = datetime.datetime(2026, 10, 1, 18, 8, 38, 430439)
T2 = datetime.datetime(2026, 10, 1, 18, 8, 42, 123310)
T3 = datetime.datetime(2026, 9, 30, 7, 0, 0)


def utc(moment):
    return moment.replace(tzinfo=datetime.timezone.utc)


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=(), subkeys=(), written=T3):
        self._name = name
        self._values = [_Value(n, d) for n, d in values]
        self._subkeys = list(subkeys)
        self._written = written

    def name(self):
        return self._name

    def values(self):
        return self._values

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
        return 'vol' + path.split('vol', 1)[1] if 'vol' in path else path


NT = 'Microsoft\\Windows NT\\CurrentVersion'
IFEO = NT + '\\Image File Execution Options'
SILENT = NT + '\\SilentProcessExit'
CMD = 'C:\\Windows\\System32\\cmd.exe /c rem example'


class DataTextTest(unittest.TestCase):
    def test_text_is_kept_and_a_number_is_hexadecimal(self):
        self.assertEqual(ifeo.data_text(_Value('Debugger', CMD)), CMD)
        self.assertEqual(ifeo.data_text(_Value('GlobalFlag', 512)), '0x200')
        self.assertEqual(ifeo.data_text(_Value('ReportingMode', 1)), '0x1')
        self.assertEqual(ifeo.data_text(_Value('GlobalFlag', 0)), '0x0')

    def test_a_number_stored_as_text_is_left_as_stored(self):
        self.assertEqual(ifeo.data_text(_Value('GlobalFlag', '0x00000200')), '0x00000200')

    def test_binary_and_multi_string_data(self):
        self.assertEqual(ifeo.data_text(_Value('x', b'\x01\x02')), '0102')
        self.assertEqual(ifeo.data_text(_Value('x', ['a.dll', 'b.dll'])), 'a.dll, b.dll')


class IfeoRowsTest(unittest.TestCase):
    def test_only_debugger_and_global_flag_are_reported(self):
        key = _Key(subkeys=[
            _Key('target.exe', [('Debugger', CMD), ('GlobalFlag', 512), ('MitigationOptions', b'\x00')], written=T1),
            _Key('other.exe', [('MitigationOptions', b'\x00'), ('CFGOptions', 1)]),
        ])
        self.assertEqual(list(ifeo.ifeo_rows(key, IFEO)), [
            (utc(T1), 'target.exe', 'Debugger', CMD, '', IFEO + '\\target.exe'),
            (utc(T1), 'target.exe', 'GlobalFlag', '0x200', '', IFEO + '\\target.exe'),
        ])

    def test_the_value_name_is_matched_without_case_and_shown_as_stored(self):
        key = _Key(subkeys=[_Key('a.exe', [('debugger', CMD), ('GLOBALFLAG', '0x200')], written=T1)])
        self.assertEqual([r[2:4] for r in ifeo.ifeo_rows(key, IFEO)], [('debugger', CMD), ('GLOBALFLAG', '0x200')])

    def test_a_filter_subkey_gives_its_own_row_with_its_path_and_time(self):
        nested = _Key('0', [('FilterFullPath', 'C:\\Tools\\target.exe'), ('Debugger', CMD)], written=T2)
        plain = _Key('1', [('FilterFullPath', 'C:\\Other\\target.exe'), ('AppExecutionAliasRedirect', 1)])
        key = _Key(subkeys=[_Key('target.exe', [('UseFilter', 1)], subkeys=[nested, plain], written=T1)])
        self.assertEqual(list(ifeo.ifeo_rows(key, IFEO)),
                         [(utc(T2), 'target.exe', 'Debugger', CMD, 'C:\\Tools\\target.exe', IFEO + '\\target.exe\\0')])

    def test_a_nested_subkey_without_a_filter_path_has_a_blank_filter_path(self):
        key = _Key(subkeys=[_Key('t.exe', subkeys=[_Key('0', [('GlobalFlag', 2)], written=T2)])])
        self.assertEqual(list(ifeo.ifeo_rows(key, IFEO)),
                         [(utc(T2), 't.exe', 'GlobalFlag', '0x2', '', IFEO + '\\t.exe\\0')])

    def test_values_on_the_key_itself_are_not_reported(self):
        key = _Key(values=[('Debugger', CMD)], subkeys=[])
        self.assertEqual(list(ifeo.ifeo_rows(key, IFEO)), [])


class SilentExitRowsTest(unittest.TestCase):
    def test_every_value_of_a_program_subkey_and_of_the_key_is_reported(self):
        key = _Key('SilentProcessExit', values=[('LocalDumpFolder', 'C:\\Dumps')], written=T1, subkeys=[
            _Key('target.exe', [('ReportingMode', 1), ('MonitorProcess', CMD), ('IgnoreSelfExits', 0)], written=T2)])
        self.assertEqual(list(ifeo.silent_exit_rows(key, SILENT)), [
            (utc(T1), '', 'LocalDumpFolder', 'C:\\Dumps', '', SILENT),
            (utc(T2), 'target.exe', 'ReportingMode', '0x1', '', SILENT + '\\target.exe'),
            (utc(T2), 'target.exe', 'MonitorProcess', CMD, '', SILENT + '\\target.exe'),
            (utc(T2), 'target.exe', 'IgnoreSelfExits', '0x0', '', SILENT + '\\target.exe'),
        ])

    def test_an_empty_key_gives_no_rows(self):
        self.assertEqual(list(ifeo.silent_exit_rows(_Key(subkeys=[_Key('a.exe')]), SILENT)), [])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Windows/System32/config/SOFTWARE', 'vol2/Windows/System32/config/software',
                     'vol1/Windows/System32/config/SOFTWARE.LOG1', 'vol1/Windows/System32/config/SYSTEM'):
            path = pathlib.Path(folder.name, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            self.paths.append(str(path))
        self.one, self.two = self.paths[0], self.paths[1]

    def run_artifact(self, hives, files=None):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(ifeo, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(ifeo, 'logfunc', side_effect=logged.append):
            result = ifeo.imageFileExecutionOptions.__wrapped__(_Context(files if files is not None else self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def full_hive(self):
        return _Hive({
            IFEO: _Key(subkeys=[_Key('target.exe', [('Debugger', CMD)], written=T1)]),
            SILENT: _Key(subkeys=[_Key('target.exe', [('MonitorProcess', CMD)], written=T2)]),
            'WOW6432Node\\' + IFEO: _Key(subkeys=[_Key('old32.exe', [('GlobalFlag', '0x200')], written=T3)]),
            'WOW6432Node\\' + SILENT: _Key(subkeys=[_Key('old32.exe', [('ReportingMode', 4)], written=T3)]),
        })

    def test_all_four_keys_are_read_in_order_and_only_software_hives_are_opened(self):
        (headers, rows, source), opened, logged = self.run_artifact({self.one: self.full_hive(), self.two: _Hive({})})
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'Image', 'Value Name', 'Value Data',
                                   'Filter Path', 'Registry Key'))
        self.assertEqual(rows, [
            (utc(T1), 'target.exe', 'Debugger', CMD, '', IFEO + '\\target.exe'),
            (utc(T3), 'old32.exe', 'GlobalFlag', '0x200', '', 'WOW6432Node\\' + IFEO + '\\old32.exe'),
            (utc(T2), 'target.exe', 'MonitorProcess', CMD, '', SILENT + '\\target.exe'),
            (utc(T3), 'old32.exe', 'ReportingMode', '0x4', '', 'WOW6432Node\\' + SILENT + '\\old32.exe'),
        ])
        self.assertEqual(opened, [self.one, self.two])
        self.assertEqual(source, self.one + '\n' + self.two)
        self.assertEqual(logged, [
            f'Image File Execution Options: 4 value(s) reported from vol1/Windows/System32/config/SOFTWARE; keys '
            f'present: {IFEO}, WOW6432Node\\{IFEO}, {SILENT}, WOW6432Node\\{SILENT}',
            'Image File Execution Options: 0 value(s) reported from vol2/Windows/System32/config/software; keys '
            'present: none'])

    def test_a_hive_holding_only_the_wow6432node_keys_is_still_read(self):
        hive = _Hive({
            'WOW6432Node\\' + IFEO: _Key(subkeys=[_Key('old32.exe', [('Debugger', CMD)], written=T1)]),
            'WOW6432Node\\' + SILENT: _Key(subkeys=[_Key('old32.exe', [('ReportingMode', 1)], written=T2)]),
        })
        (_headers, rows, _source), _opened, logged = self.run_artifact({self.one: hive, self.two: _Hive({})})
        self.assertEqual(rows, [
            (utc(T1), 'old32.exe', 'Debugger', CMD, '', 'WOW6432Node\\' + IFEO + '\\old32.exe'),
            (utc(T2), 'old32.exe', 'ReportingMode', '0x1', '', 'WOW6432Node\\' + SILENT + '\\old32.exe'),
        ])
        self.assertIn(f'keys present: WOW6432Node\\{IFEO}, WOW6432Node\\{SILENT}', logged[0])

    def test_an_unreadable_hive_is_logged_by_its_evidence_path_and_the_other_is_still_read(self):
        (_headers, rows, source), _opened, logged = self.run_artifact(
            {self.one: ValueError('bad header'), self.two: self.full_hive()})
        self.assertEqual(len(rows), 4)
        self.assertEqual(source, self.two)
        self.assertEqual(
            logged[0], 'Image File Execution Options: could not read vol1/Windows/System32/config/SOFTWARE: bad header')

    def test_without_python_registry_nothing_is_read(self):
        with mock.patch.object(ifeo, 'Registry', None), mock.patch.object(ifeo, 'logfunc') as log, \
                mock.patch.object(ifeo, 'open_hive') as opened:
            _headers, rows, source = ifeo.imageFileExecutionOptions.__wrapped__(_Context(self.paths))
        self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
