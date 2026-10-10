"""Pin the Audit Policy artifact (scripts/artifacts/windowsAuditPolicy.py).

The values are built in the layout measured on windows11_arm_auditmap_20261010: a 12-byte header, 16-bit settings,
one spare 16-bit value and the per-category counts.
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
from scripts.artifacts import windowsAuditPolicy as ap
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

COUNTS_60 = (5, 12, 14, 3, 6, 6, 6, 4, 4)
COUNTS_59 = (5, 11, 14, 3, 6, 6, 6, 4, 4)
TAIL = '-69AE-11D9-BED3-505054503030}'
WRITTEN = datetime.datetime(2026, 10, 10, 19, 35, 37)


def policy(values, counts, spare=0):
    body = struct.pack(f'<{len(values)}H', *values) + struct.pack('<H', spare)
    return (struct.pack('<HHII', 0x100, 0, len(counts), 12 + len(body)) + body
            + struct.pack(f'<{len(counts)}H', *counts))


class _Value:
    def __init__(self, raw):
        self._raw = raw

    def raw_data(self):
        return self._raw


class _Key:
    def __init__(self, raw):
        self._raw = raw

    def values(self):
        return [] if self._raw is None else [_Value(self._raw)]

    @staticmethod
    def timestamp():
        return WRITTEN


class _Hive:
    def __init__(self, raw, present=True):
        self._raw, self._present = raw, present

    def open(self, path):
        if not self._present or path != 'Policy\\PolAdtEv':
            raise Registry.RegistryKeyNotFoundException(path)
        return _Key(self._raw)


class Layout(unittest.TestCase):
    def test_the_established_layout(self):
        layout = ap._LAYOUT_60  # pylint: disable=protected-access
        self.assertEqual(len(layout), 60)
        self.assertEqual(len({guid for _, _, guid in layout}), 60)
        self.assertEqual([sum(1 for c, _, _ in layout if c == name) for name in dict.fromkeys(c for c, _, _ in layout)],
                         list(COUNTS_60))
        self.assertEqual(layout[0], ('System', 'Security State Change', '0CCE9210'))
        self.assertEqual(layout[9], ('Logon/Logoff', 'Special Logon', '0CCE921B'))
        self.assertEqual(layout[10], ('Logon/Logoff', 'IPsec Quick Mode', '0CCE9219'))
        self.assertEqual(layout[21], ('Object Access', 'Other Object Access Events', '0CCE9227'))
        self.assertEqual(layout[34], ('Detailed Tracking', 'Process Creation', '0CCE922B'))
        self.assertEqual(layout[59], ('Account Logon', 'Kerberos Authentication Service', '0CCE9242'))

    def test_values_and_counts(self):
        values = [i % 4 for i in range(60)]
        self.assertEqual(ap.policy_values(policy(values, COUNTS_60, spare=7)), (tuple(values), COUNTS_60))

    def test_data_without_the_shape(self):
        good = policy([0] * 60, COUNTS_60)
        for raw in (b'', good[:11], good[:-1], good[:8] + struct.pack('<I', 13) + good[12:],
                    good[:8] + struct.pack('<I', 8) + good[12:], good[:4] + struct.pack('<I', 0) + good[8:],
                    good[:4] + struct.pack('<I', 10) + good[8:], policy([0] * 59, COUNTS_60)[:-2] + b'\xff\xff'):
            self.assertIsNone(ap.policy_values(raw), raw[:16])
            self.assertIsNone(ap.policy_rows(raw))

    def test_named_rows(self):
        values = [0] * 60
        values[0], values[9], values[34], values[59], values[5] = 1, 3, 2, 1, 9
        rows, named = ap.policy_rows(policy(values, COUNTS_60))
        self.assertTrue(named)
        self.assertEqual(len(rows), 60)
        self.assertEqual(rows[0], ('System', 'Security State Change', 'Success', 1, 1, '{0CCE9210' + TAIL))
        self.assertEqual(rows[9], ('Logon/Logoff', 'Special Logon', 'Success and Failure', 3, 10, '{0CCE921B' + TAIL))
        self.assertEqual(rows[34][:5], ('Detailed Tracking', 'Process Creation', 'Failure', 2, 35))
        self.assertEqual(rows[5][:5], ('Logon/Logoff', 'Logon', '', 9, 6))
        self.assertEqual(rows[1][2], 'No Auditing')

    def test_a_layout_that_is_not_established(self):
        rows, named = ap.policy_rows(policy([1, 0, 3] + [0] * 56, COUNTS_59, spare=53543))
        self.assertFalse(named)
        self.assertEqual(rows[:3], [('', '', '', 1, 1, ''), ('', '', '', 0, 2, ''), ('', '', '', 3, 3, '')])
        self.assertEqual(len(rows), 59)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Processor(unittest.TestCase):
    def run_on(self, hives):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        for name, hive in hives.items():
            path = pathlib.Path(folder.name, name, 'Windows', 'System32', 'config', 'SECURITY')
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] == 'bad':
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: pathlib.Path(p).relative_to(folder.name).as_posix()
        with mock.patch.object(ap, 'found_hives', return_value=sorted(by_path, reverse=True)), \
                mock.patch.object(ap, 'open_hive', side_effect=opened), mock.patch.object(ap, 'logfunc') as log:
            headers, rows, located = ap.windowsAuditPolicy.__wrapped__(context)
        return headers, rows, [pathlib.Path(p).relative_to(folder.name).parts[0] for p in located.split('\n') if p], \
            [call[0][0] for call in log.call_args_list]

    def test_hives(self):
        values = [0] * 60
        values[34] = 1
        headers, rows, located, logged = self.run_on({
            'a': _Hive(policy(values, COUNTS_60)), 'b': _Hive(policy([2] * 59, COUNTS_59)), 'c': 'bad',
            'd': _Hive(None), 'e': _Hive(b'', present=False), 'f': _Hive(b'\x00' * 20)})
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'Category', 'Subcategory', 'Setting', 'Value',
                                   'Position', 'Subcategory GUID', 'Source File'))
        self.assertEqual(len(rows), 119)
        when = WRITTEN.replace(tzinfo=datetime.timezone.utc)
        self.assertEqual(rows[34], (when, 'Detailed Tracking', 'Process Creation', 'Success', 1, 35,
                                    '{0CCE922B' + TAIL, 'a/Windows/System32/config/SECURITY'))
        self.assertEqual(rows[60], (when, '', '', '', 2, 1, '', 'b/Windows/System32/config/SECURITY'))
        self.assertEqual(located, ['a', 'b'])
        self.assertEqual(len(logged), 5)
        self.assertIn('b/Windows/System32/config/SECURITY holds 59 subcategory values in a layout', logged[0])
        self.assertIn('could not read c/Windows/System32/config/SECURITY: not a hive', logged[1])
        self.assertIn('d/Windows/System32/config/SECURITY holds no Policy\\PolAdtEv value', logged[2])
        self.assertIn('e/Windows/System32/config/SECURITY holds no Policy\\PolAdtEv value', logged[3])
        self.assertIn('f/Windows/System32/config/SECURITY (20 bytes) is not in a known shape', logged[4])

    def test_no_library(self):
        with mock.patch.object(ap, 'Registry', None), mock.patch.object(ap, 'logfunc') as log:
            self.assertEqual(ap.windowsAuditPolicy.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
