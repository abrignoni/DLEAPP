"""Exercise the real CLI and its compact HTML, TSV and LAVA outputs together."""

import csv
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from admin.test.scripts.bitlocker_fixture import volume  # pylint: disable=wrong-import-position


class BitLockerReportTest(unittest.TestCase):
    def test_locked_raw_image_reaches_every_report_writer_and_keeps_its_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            image = root / 'synthetic.img'
            raw = volume()
            image.write_bytes(raw)
            output = root / 'reports'
            output.mkdir()
            env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), TZ='UTC')
            run = subprocess.run(
                [sys.executable, str(REPO_ROOT / 'dleapp.py'), '-t', 'raw',
                 '-i', str(image), '-o', str(output), '-m',
                 str(REPO_ROOT / 'bitlocker-metadata.dlprofile'), '--no-find-members'],
                cwd=REPO_ROOT, env=env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, check=False, timeout=90)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('Report generation Completed.', run.stdout)
            self.assertNotIn('Traceback', run.stdout + run.stderr)
            report, = output.iterdir()
            manifest = json.loads((report / '_lava_data.lava').read_text(encoding='utf-8'))
            expected = {'bitlockerKeyProtectors': 2}
            artifacts = manifest['artifacts']['BitLocker']
            self.assertEqual({a['artifact_key']: a['record_count'] for a in artifacts}, expected)
            with sqlite3.connect('file:' + str(report / '_lava_artifacts.db') + '?mode=ro', uri=True) as db:
                for item in artifacts:
                    table = '"' + item['tablename'].replace('"', '""') + '"'
                    self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],
                                     expected[item['artifact_key']])
                    self.assertNotIn(temp, item['source_path'])
                    source = report / 'data' / item['source_path']
                    self.assertTrue(source.is_file())
            self.assertEqual(list(report.rglob('tl.db')), [])
            tsvs = list(report.rglob('*.tsv'))
            self.assertEqual(len(tsvs), 1)
            for path in tsvs:
                with path.open(encoding='utf-8-sig', newline='') as handle:
                    lines = list(csv.reader(handle, delimiter='\t'))
                self.assertTrue(all(len(row) == len(lines[0]) for row in lines))
                self.assertGreater(len(lines), 1)
            htmls = list((report / '_HTML').glob('BitLocker_*.html'))
            self.assertEqual(len(htmls), 1)
            for path in htmls:
                text = path.read_text(encoding='utf-8')
                self.assertIn('<table', text)
                self.assertNotIn(temp, text)
            for removed in ('BitLocker_Volume_Metadata.html', 'BitLocker_Metadata_Copies.html',
                            'BitLocker_PCR_Bindings.html', 'BitLocker_Metadata_Entries.html',
                            'BitLocker_Metadata_Times.html'):
                self.assertFalse((report / '_HTML' / removed).exists())
            self.assertEqual(image.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
