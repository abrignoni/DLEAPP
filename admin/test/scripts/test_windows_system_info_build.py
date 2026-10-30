"""Pin the Build row of windowsSystemInfo in scripts/artifacts/windowsSystemInfo.py: CurrentBuild with UBR,
or CurrentBuildNumber where CurrentBuild holds no number, as Windows XP's does. Every value here is made up."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsSystemInfo as system_info
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

CURRENT_VERSION = 'Microsoft\\Windows NT\\CurrentVersion'


class _Value:
    def __init__(self, data):
        self._data = data

    def value(self):
        return self._data


class _Key:
    def __init__(self, values):
        self._values = values

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(self._values[name])

    @staticmethod
    def timestamp():
        return None


class _Hive:
    def __init__(self, values):
        self._key = _Key(values)

    def open(self, path):
        if path != CURRENT_VERSION:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._key


def build_row(values):
    rows = [r for r in system_info._software_rows(_Hive(values)) if r[0] == 'Build']  # pylint: disable=protected-access
    return (rows[0][1], rows[0][2]) if rows else None


class BuildRowTest(unittest.TestCase):
    def test_current_build_with_ubr(self):
        self.assertEqual(build_row({'CurrentBuild': '19041', 'CurrentBuildNumber': '19041', 'UBR': 264}),
                         ('19041.264', CURRENT_VERSION + '\\CurrentBuild, UBR'))

    def test_a_placeholder_in_current_build_reads_current_build_number(self):
        self.assertEqual(build_row({'CurrentBuild': '1.2.3 () (placeholder)', 'CurrentBuildNumber': '2600'}),
                         ('2600', CURRENT_VERSION + '\\CurrentBuildNumber, UBR'))

    def test_a_placeholder_with_no_build_number_is_kept_as_stored(self):
        self.assertEqual(build_row({'CurrentBuild': 'not a number'}),
                         ('not a number', CURRENT_VERSION + '\\CurrentBuild, UBR'))

    def test_no_current_build_gives_no_row(self):
        self.assertIsNone(build_row({'CurrentBuildNumber': '2600'}))


if __name__ == '__main__':
    unittest.main()
