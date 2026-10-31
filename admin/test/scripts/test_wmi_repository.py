"""Pin the helpers of scripts/artifacts/windowsWmiRepository.py and the fixture it reads.

The object paths are written in the two forms the Windows 11 known data stores in
__FilterToConsumerBinding: with the \\\\.\\ROOT\\<namespace>: prefix New-CimInstance
writes, and bare, as the stock SCM Event Log binding holds them. Every value is invented.
The expected values are written out, never read back from the code.
"""
import fnmatch
import importlib.util
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=protected-access
from scripts.artifacts import windowsWmiRepository as wmi  # pylint: disable=wrong-import-position
from scripts.vendor import cimreader  # pylint: disable=wrong-import-position


def _fixture_module():
    spec = importlib.util.spec_from_file_location(
        'make_wmi_repository_fixture', REPO_ROOT / 'admin/test/scripts/make_wmi_repository_fixture.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseReference(unittest.TestCase):
    def test_prefixed(self):
        self.assertEqual(
            wmi._parse_ref('\\\\.\\ROOT\\subscription:CommandLineEventConsumer.Name="Run \\"it\\""', 'root\\default'),
            ('ROOT\\subscription', 'CommandLineEventConsumer', {'name': 'Run "it"'}))

    def test_bare_takes_the_binding_namespace(self):
        self.assertEqual(wmi._parse_ref('__EventFilter.Name="A, B"', 'root\\subscription'),
                         ('root\\subscription', '__EventFilter', {'name': 'A, B'}))

    def test_two_keys_and_a_backslash(self):
        self.assertEqual(wmi._parse_ref('X.Name="C:\\\\Fixture",Id=7', 'ns'),
                         ('ns', 'X', {'name': 'C:\\Fixture', 'id': '7'}))

    def test_not_an_object_path(self):
        self.assertIsNone(wmi._parse_ref('no key here', 'ns'))
        self.assertIsNone(wmi._parse_ref(None, 'ns'))


class Sid(unittest.TestCase):
    def test_domain_sid(self):
        data = [1, 5, 0, 0, 0, 0, 0, 5, 21, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0xE9, 0x03, 0, 0]
        self.assertEqual(wmi._sid(data), 'S-1-5-21-1-2-3-1001')

    def test_builtin_administrators(self):
        self.assertEqual(wmi._sid([1, 2, 0, 0, 0, 0, 0, 5, 32, 0, 0, 0, 0x20, 2, 0, 0]), 'S-1-5-32-544')

    def test_not_a_sid_is_shown_as_hex(self):
        self.assertEqual(wmi._sid([2, 0, 0]), '02 00 00')
        self.assertEqual(wmi._sid(None), '')


class Paths(unittest.TestCase):
    def test_pattern(self):
        (pattern,) = wmi.__artifacts_v2__['wmiRepositoryEventFilters']['paths']
        for path in ('root/Windows/System32/wbem/Repository/OBJECTS.DATA',
                     'root/WINDOWS/system32/wbem/Repository/FS/OBJECTS.MAP',
                     'root/Windows.old/Windows/System32/wbem/Repository/INDEX.BTR'):
            self.assertTrue(fnmatch.fnmatchcase(path, pattern), path)
        self.assertFalse(fnmatch.fnmatchcase('root/Users/x/Repository/OBJECTS.DATA', pattern))


class Fixture(unittest.TestCase):
    def test_reader_returns_what_the_fixture_wrote(self):
        files = _fixture_module().build()
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in files.items():
                pathlib.Path(tmp, name).write_bytes(data)
            with cimreader.open_repository(tmp) as repo:
                result = cimreader.subscriptions(repo, ('root\\subscription', 'root\\default'))
        self.assertEqual(result['errors'], [])
        rows = result['namespaces']['root\\subscription']
        kinds = sorted(r['kind'] for r in rows)
        self.assertEqual(kinds, ['__EventConsumer'] * 3 + ['__EventFilter'] * 3 + ['__FilterToConsumerBinding'] * 3)
        script = [r for r in rows if r['class'] == 'ActiveScriptEventConsumer'][0]
        self.assertEqual(script['location']['pages'], 4)
        self.assertEqual(len(result['namespaces']['root\\default']), 3)


if __name__ == '__main__':
    unittest.main()
