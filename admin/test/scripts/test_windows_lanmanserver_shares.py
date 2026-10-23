"""Pin the LanmanServer Shares artifact (scripts/artifacts/windowsLanmanServerShares.py).

The SYSTEM hives are built cell by cell with the builder in test_windows_app_settings.py and read back through
open_hive and python-registry, as a run reads a staged hive. Every share name, path and remark is invented.
"""

import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsLanmanServerShares as lss
from test_windows_app_settings import _Context, build_hive, spec, write
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1 = datetime.datetime(2031, 4, 5, 6, 7, 8, tzinfo=UTC)
T2 = datetime.datetime(2032, 5, 6, 7, 8, 9, tzinfo=UTC)
REG_SZ, REG_BINARY, REG_DWORD, REG_MULTI_SZ = 1, 3, 4, 7


def multi(*strings):
    return b''.join(s.encode('utf-16-le') + b'\x00\x00' for s in strings) + b'\x00\x00'


def share(name, path, remark='', extra=()):
    return (name, REG_MULTI_SZ, multi('CATimeout=0', 'CSCFlags=0', 'MaxUses=4294967295', f'Path={path}',
                                      'Permissions=0', f'Remark={remark}', f'ShareName={name}', 'Type=0', *extra))


def control_set(name, stamp, shares, secured=(), security=True):
    """A ControlSet00N key holding Services\\LanmanServer\\Shares with the given values."""
    sec = [spec('Security', stamp, [(s, REG_BINARY, b'\x01\x00\x04\x80' + b'\x00' * 16) for s in secured])] \
        if security else []
    return spec(name, stamp, (), [spec('Services', stamp, (), [spec('LanmanServer', stamp, (), [
        spec('Shares', stamp, shares, sec)])])])


def select(current):
    return spec('Select', T1, [('Current', REG_DWORD, current.to_bytes(4, 'little'))])


class ShareRowsTest(unittest.TestCase):
    def run_artifact(self, hives):
        with tempfile.TemporaryDirectory() as root:
            files = [write(root, relative, data) for relative, data in hives]
            with mock.patch.object(lss, 'logfunc') as log:
                headers, rows, source = lss.windowsLanmanServerShares.__wrapped__(_Context(root, files))
            source = [os.path.relpath(p, root) for p in source.split('\n')] if source else []
        return headers, rows, source, log

    def test_every_control_set_with_the_current_one_marked(self):
        hive = build_hive(T1, select(2),
                          control_set('ControlSet001', T1, [share('Alpha', 'C:\\Alpha', 'made up'),
                                                            share('Beta$', 'D:\\Beta')], secured=('alpha',)),
                          control_set('ControlSet002', T2, [share('Alpha', 'C:\\Alpha', 'made up')]))
        headers, rows, source, log = self.run_artifact([('vol/Windows/System32/config/SYSTEM', hive)])
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['Key Last Written (UTC)', 'Control Set', 'Current Control Set', 'Value Name',
                                 'ShareName', 'Path', 'Remark', 'Type', 'Permissions', 'MaxUses', 'CSCFlags',
                                 'CATimeout', 'Other Fields', 'Security Value', 'Key', 'Source File'])
        self.assertEqual(len(rows), 3)
        self.assertEqual([r[:4] for r in rows], [(T1, 'ControlSet001', 'No', 'Alpha'), (T1, 'ControlSet001', 'No', 'Beta$'),
                                                 (T2, 'ControlSet002', 'Yes', 'Alpha')])
        self.assertEqual(rows[0][4:12], ('Alpha', 'C:\\Alpha', 'made up', '0', '0', '4294967295', '0', '0'))
        self.assertEqual([r[12:16] for r in rows], [
            ('', 'Yes', r'ControlSet001\Services\LanmanServer\Shares', 'vol/Windows/System32/config/SYSTEM'),
            ('', 'No', r'ControlSet001\Services\LanmanServer\Shares', 'vol/Windows/System32/config/SYSTEM'),
            ('', 'No', r'ControlSet002\Services\LanmanServer\Shares', 'vol/Windows/System32/config/SYSTEM')])
        self.assertEqual(source, ['vol/Windows/System32/config/SYSTEM'])
        log.assert_not_called()

    def test_other_fields_keep_what_the_columns_do_not_show(self):
        odd = share('Gamma', 'E:\\Gamma', extra=('Type=1', 'NoEqualsSign', 'Unlisted=7'))
        hive = build_hive(T1, control_set('ControlSet001', T1, [odd, ('Delta', REG_SZ, 'Path=F:\\x'.encode('utf-16-le') + b'\0\0')],
                                          security=False))
        _h, rows, _s, log = self.run_artifact([('vol/Windows/System32/config/SYSTEM', hive)])
        self.assertEqual([r[2] for r in rows], ['', ''])  # no Select key: Current Control Set blank
        self.assertEqual(rows[0][7], '0')
        self.assertEqual(rows[0][12], 'Type=1 | NoEqualsSign | Unlisted=7')
        self.assertEqual(rows[1][4:12], ('',) * 8)
        self.assertEqual(rows[1][12], 'RegSZ: Path=F:\\x')
        self.assertEqual([r[13] for r in rows], ['No', 'No'])
        log.assert_called_once()
        self.assertIn('1 values that are not a multi-string, reported in Other Fields', log.call_args.args[0])
        self.assertIn('4 strings reported in Other Fields', log.call_args.args[0])

    def test_an_empty_shares_key_gives_no_rows_and_still_names_the_hive(self):
        hive = build_hive(T1, select(1), control_set('ControlSet001', T1, []))
        _h, rows, source, _log = self.run_artifact([('vol/Windows/System32/config/SYSTEM', hive)])
        self.assertEqual(rows, [])
        self.assertEqual(source, ['vol/Windows/System32/config/SYSTEM'])

    def test_two_hives_keep_their_own_rows(self):
        first = build_hive(T1, select(1), control_set('ControlSet001', T1, [share('One', 'C:\\One')]))
        second = build_hive(T2, select(1), control_set('ControlSet001', T2, [share('Two', 'C:\\Two'),
                                                                             share('Three', 'C:\\Three')]))
        _h, rows, source, _log = self.run_artifact([('a/Windows/System32/config/SYSTEM', first),
                                                    ('b/Windows/System32/config/SYSTEM', second)])
        self.assertEqual([(r[3], r[15]) for r in rows], [('One', 'a/Windows/System32/config/SYSTEM'),
                                                         ('Two', 'b/Windows/System32/config/SYSTEM'),
                                                         ('Three', 'b/Windows/System32/config/SYSTEM')])
        self.assertEqual(source, ['a/Windows/System32/config/SYSTEM', 'b/Windows/System32/config/SYSTEM'])

    def test_split_fields(self):
        counts = Counter()
        fields, other = lss.split_fields(['ShareName=x', 'Path=C:\\y=z', '', 'Remark='], counts)
        self.assertEqual(fields, ('x', 'C:\\y=z', '', '', '', '', '', ''))
        self.assertEqual(other, '')
        self.assertEqual(counts, Counter())


if __name__ == '__main__':
    unittest.main()
