"""Pin the MPLog process impact reading in scripts/artifacts/windowsDefenderMpLog.py.

Every log below is written by the test from the line shapes the module's notes describe;
no value comes from a real device. Expected values are written out, never read back from
the code.
"""
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDefenderMpLog as artifact  # pylint: disable=wrong-import-position

FOLDER = 'C/ProgramData/Microsoft/Windows Defender/Support'
IMPACT = ('ProcessImageName: example.exe, Pid: 1234, TotalTime: 50, Count: 7, MaxTime: 20, '
          'MaxTimeFile: \\Device\\HarddiskVolume3\\Temp\\a.txt, EstimatedImpact: 5%')
COUNTS = ('Per-process counts:ProcessImageName: other.exe, TotalTime: 9, Count: 2, '
          'MaxTime: 6, MaxTimeFile: \\Device\\HarddiskVolume3\\Temp\\b.txt, EstimatedImpact: 0%')


def header(current):
    """A service log header whose Current time line carries this UTC text."""
    return ['-' * 20, 'Microsoft Defender Antivirus (00000000-0000-0000-0000-000000000000) Service Log',
            'Started On 01-02-2026 03:04:05', '*' * 20, f'Current time: {current} UTC (1000 ms since boot)']


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class MpLogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_lines(self, lines, name='MPLog-20260101-000000.log'):
        path = self.root/FOLDER/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'\xff\xfe' + '\r\n'.join(lines).encode('utf-16-le'))
        _, rows, sources = artifact.defenderMpLogProcessImpact.__wrapped__(Context(self.root, [path]))
        self.assertEqual(sources, str(path))
        return rows

    def test_time_without_z_in_a_block_that_agrees_with_its_utc_header(self):
        rows = self.run_lines(header('01/02/2026 03:04:05.250000000')
                              + ['2026-01-02T03:04:05.249 first line of the block',
                                 f'2026-01-02T05:06:07.890 {IMPACT}'])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], datetime(2026, 1, 2, 5, 6, 7, 890000, tzinfo=timezone.utc))
        self.assertEqual(rows[0][1], '2026-01-02T05:06:07.890')
        self.assertEqual(rows[0][2:10], ('example.exe', '1234', '50', '7', '20',
                                         '\\Device\\HarddiskVolume3\\Temp\\a.txt', '5%', 7))

    def test_impact_line_that_is_itself_the_first_timed_line(self):
        rows = self.run_lines(header('01/02/2026 03:04:05.000000000')
                              + [f'2026-01-02T03:04:05.100 {IMPACT}'])
        self.assertEqual(rows[0][0], datetime(2026, 1, 2, 3, 4, 5, 100000, tzinfo=timezone.utc))

    def test_time_without_z_blank_when_the_block_disagrees_with_its_header(self):
        # The block's first line sits four hours from the header's UTC time.
        rows = self.run_lines(header('01/02/2026 07:04:05.000000000')
                              + ['2026-01-02T03:04:05.000 first line of the block',
                                 f'2026-01-02T05:06:07.890 {IMPACT}'])
        self.assertEqual(rows[0][0], '')
        self.assertEqual(rows[0][1], '2026-01-02T05:06:07.890')

    def test_time_without_z_blank_before_any_header(self):
        rows = self.run_lines([f'2026-01-02T05:06:07.890 {IMPACT}'])
        self.assertEqual(rows[0][0], '')

    def test_agreement_is_checked_again_in_each_block(self):
        rows = self.run_lines(header('01/02/2026 03:04:05.000000000')
                              + ['2026-01-02T03:04:05.000 first line',
                                 f'2026-01-02T03:10:00.000 {IMPACT}']
                              + header('01/03/2026 09:00:00.000000000')
                              + ['2026-01-03T04:00:00.000 first line',
                                 f'2026-01-03T04:10:00.000 {IMPACT}'])
        self.assertEqual([r[0] for r in rows],
                         [datetime(2026, 1, 2, 3, 10, tzinfo=timezone.utc), ''])

    def test_time_with_z_is_utc_without_a_header(self):
        rows = self.run_lines([f'2026-01-02T05:06:07.890Z {IMPACT}'])
        self.assertEqual(rows[0][0], datetime(2026, 1, 2, 5, 6, 7, 890000, tzinfo=timezone.utc))
        self.assertEqual(rows[0][1], '2026-01-02T05:06:07.890Z')

    def test_per_process_counts_line_has_no_time(self):
        rows = self.run_lines(header('01/02/2026 03:04:05.000000000')
                              + ['2026-01-02T03:04:05.000 first line', COUNTS])
        self.assertEqual(rows[0][:4], ('', '', 'other.exe', ''))

    def test_unmatched_line_is_counted(self):
        self.run_lines(['2026-01-02T05:06:07.890Z ProcessImageName: broken'])
        self.assertIn('1 lines naming ProcessImageName did not match', self.logged[-1])


if __name__ == '__main__':
    unittest.main()
