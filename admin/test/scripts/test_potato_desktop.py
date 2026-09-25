"""Pin the Potato Desktop app-info reader in scripts/artifacts/potatoDesktop.py.

The log text below is authored for the test; none of it comes from a real device.
"""
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import potatoDesktop  # pylint: disable=wrong-import-position

LOG_UNFINISHED = (
    "[2026.01.02 03:04:05] Logs started\n"
    "[2026.01.02 03:04:05] update channel=005, set version to 9.9.900001\n"
    "[2026.01.02 03:04:05] Launched version: 109009001, alpha: [FALSE], beta: 0, "
    "debug mode: [FALSE], test dc: [FALSE]\n"
    "[2026.01.02 03:04:05] Executable dir: /Applications/, name: Potato.app\n"
    "[2026.01.02 03:04:05] Working dir: /Users/tester/Library/Application Support/Potato Desktop/\n"
    "[2026.01.02 03:04:07] Opened '/Users/tester/x' for reading, the previous Potato Desktop "
    "launch was not finished properly :( Crash log size: 42\n")

LOG_CLEAN = (
    "[2026.02.03 04:05:06] Logs started\n"
    "[2026.02.03 04:05:06] update channel=010, set version to 9.9.900002\n"
    "[2026.02.03 04:05:06] Launched version: 109009002, alpha: [FALSE]\n"
    "[2026.02.03 04:05:06] Executable dir: /Applications/, name: Potato.app\n")


class Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return [str(f) for f in self.files]

    @staticmethod
    def get_relative_path(path):
        return 'Library/Application Support/Potato Desktop/' + pathlib.Path(path).name


class PotatoAppInfoTest(unittest.TestCase):

    def run_on(self, texts):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(potatoDesktop, 'logfunc', lambda *_: None):
            files = []
            for i, text in enumerate(texts):
                d = pathlib.Path(directory)/str(i)
                d.mkdir()
                p = d/'log.txt'
                p.write_text(text, encoding='utf-8')
                files.append(p)
            before = [p.read_bytes() for p in files]
            headers, rows, source = potatoDesktop.potatoDesktopAppInfo.__wrapped__(Context(files))
            self.assertEqual(before, [p.read_bytes() for p in files])
        return [h[0] if isinstance(h, tuple) else h for h in headers], rows, source

    def test_unfinished_launch_row(self):
        headers, rows, _source = self.run_on([LOG_UNFINISHED])
        row = dict(zip(headers, rows[0]))
        self.assertEqual(row['Log Time'], '2026.01.02 03:04:05')
        self.assertEqual(row['Version'], '9.9.900001')
        self.assertEqual(row['Numeric Version'], '109009001')
        self.assertEqual(row['Update Channel'], '005')
        self.assertEqual(row['Executable Directory'], '/Applications/')
        self.assertEqual(row['Executable Name'], 'Potato.app')
        self.assertEqual(row['Working Directory'],
                         '/Users/tester/Library/Application Support/Potato Desktop/')
        self.assertEqual(row['Previous Launch Unfinished'], 'Yes')
        self.assertEqual(row['Crash Log Size'], '42')

    def test_clean_launch_leaves_crash_fields_blank(self):
        headers, rows, _source = self.run_on([LOG_CLEAN])
        row = dict(zip(headers, rows[0]))
        self.assertEqual(row['Previous Launch Unfinished'], 'No')
        self.assertEqual(row['Crash Log Size'], '')
        self.assertEqual(row['Working Directory'], '')

    def test_one_row_per_log(self):
        _headers, rows, source = self.run_on([LOG_UNFINISHED, LOG_CLEAN])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(source.split('\n')), 2)


if __name__ == '__main__':
    unittest.main()
