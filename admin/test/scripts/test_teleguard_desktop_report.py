"""Exercise the TeleGuard CLI with real report writers and media check-ins.

All evidence here is authored by the adjacent fixture generator. Subprocesses
isolate DLEAPP's report/context globals from the rest of unittest discovery.
"""
from contextlib import closing
import csv
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from admin.test.scripts import make_teleguard_desktop_fixture as fixture  # pylint: disable=wrong-import-position

EXPECTED = {'teleguardMessages': 24, 'teleguardChatOverview': 4,
            'teleguardContacts': 12, 'teleguardMediaReferences': 4,
            'teleguardMediaFiles': 6}


class TeleGuardReportTest(unittest.TestCase):
    """Full CLI output, per-profile media identity and negative controls."""

    def run_cli(self, archive, output):
        output.mkdir()
        # Keep this test's profile in its TemporaryDirectory.
        profile_path = output.parent / (output.name + '.dlprofile')
        profile_path.write_text(
            json.dumps({'leapp': 'dleapp', 'format_version': 1,
                        'plugins': sorted(EXPECTED)}),
            encoding='utf-8')
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / 'dleapp.py'), '-t', 'zip', '-i',
             str(archive), '-o', str(output), '-m', str(profile_path)],
            cwd=REPO_ROOT, env=dict(os.environ, TZ='UTC'),
            capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        reports = list(output.glob('DLEAPP_Output_*'))
        self.assertEqual(len(reports), 1, result.stdout + result.stderr)
        return reports[0]

    def test_real_outputs_scale_and_media_keep_profile_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tree = fixture.build(root / 'extraction')
            double_archive = root / 'double.zip'
            fixture.pack(tree, double_archive)
            single_archive = root / 'single.zip'
            with zipfile.ZipFile(double_archive) as source, \
                    zipfile.ZipFile(single_archive, 'w') as output:
                for item in source.infolist():
                    self.assertNotIn('\\', item.filename)
                    if '/profile-one/' in item.filename:
                        output.writestr(item, source.read(item))
            single = self.run_cli(single_archive, root / 'single-output')
            double = self.run_cli(double_archive, root / 'double-output')
            for report, factor in ((single, 1), (double, 2)):
                manifest = json.loads((report / '_lava_data.lava').read_text(encoding='utf-8'))
                artifacts = manifest['artifacts']['TeleGuard Windows']
                counts = {a['artifact_key']: a['record_count'] for a in artifacts}
                self.assertEqual(counts, {key: value // 2 * factor for key, value in EXPECTED.items()})
                with closing(sqlite3.connect(report / '_lava_artifacts.db')) as db:
                    db.row_factory = sqlite3.Row
                    for artifact in artifacts:
                        table = artifact['tablename']
                        self.assertEqual(db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0],
                                         artifact['record_count'])
                        tsv = report / '_TSV Exports' / (artifact['name'] + '.tsv')
                        with tsv.open(encoding='utf-8-sig', newline='') as handle:
                            rows = list(csv.reader(handle, delimiter='\t'))
                        self.assertEqual(len(rows) - 1, artifact['record_count'])
                        self.assertEqual(rows[0], list(artifact['column_map'].values()))
                        html = report / '_HTML' / (artifact['name'].replace(' ', '_') + '.html')
                        self.assertTrue(html.is_file())
                        self.assertNotIn(str(report / 'data'), html.read_text(encoding='utf-8'))
                        for source in artifact['source_path'].splitlines():
                            self.assertFalse(Path(source).is_absolute())
                    messages = next(a for a in artifacts if a['artifact_key'] == 'teleguardMessages')
                    view = messages['data_views']['conversation']
                    self.assertEqual(view['conversationDiscriminatorColumn'], 'conversation_id')
                    self.assertEqual(view['directionSentValue'], 'Outgoing')
                    self.assertEqual(db.execute('SELECT COUNT(DISTINCT conversation_id) '
                                                'FROM teleguardmessages').fetchone()[0], 2 * factor)
                    for row in db.execute('SELECT * FROM teleguardmessages WHERE media IS NOT NULL'):
                        for reference_id in json.loads(row['media']):
                            item = db.execute('SELECT i.* FROM _lava_media_references r '
                                              'JOIN _lava_media_items i ON i.id=r.media_item_id '
                                              'WHERE r.id=?', (reference_id,)).fetchone()
                            self.assertIsNotNone(item)
                            self.assertEqual(Path(item['source_path']).parent,
                                             Path(row['source_file']).parent)
                            media = report / item['extraction_path']
                            expected = fixture.PDF if media.suffix == '.pdf' else (
                                fixture.JPEG_SECOND if '/profile-two/' in row['source_file']
                                else fixture.JPEG)
                            self.assertEqual(media.read_bytes(), expected)
                    for item in db.execute('SELECT * FROM _lava_media_items'):
                        self.assertTrue((report / item['extraction_path']).is_file())
                        self.assertFalse(Path(item['source_path']).is_absolute())
                    # Recognized unreferenced files and both embedded-avatar types survive.
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM teleguardmediafiles "
                                                "WHERE reference_status='Unreferenced'").fetchone()[0], factor)
                    types = {row[0] for row in db.execute(
                        'SELECT type FROM _lava_media_items WHERE is_embedded=1')}
                    self.assertEqual(types, {'image/jpeg', 'image/png'})
                    localized = db.execute("SELECT message,content_as_stored FROM teleguardmessages "
                                           "WHERE message_id='a4'").fetchone()
                    self.assertEqual(localized['message'], 'Viola')
                    self.assertEqual(json.loads(localized['content_as_stored'])['en'], 'Violet')
                with closing(sqlite3.connect(report / '_Timeline' / 'tl.db')) as db:
                    timeline = dict(db.execute('SELECT activity,COUNT(*) FROM data GROUP BY activity'))
                self.assertEqual(timeline, {a['name']: a['record_count'] for a in artifacts
                                            if a['artifact_key'] != 'teleguardMediaFiles'})

    def test_roaming_teleguard_media_stay_with_the_source_store(self):
        """The Windows app-data folder stages media without joining other trees."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tree = fixture.build(root / 'extraction')
            for profile in ('profile-one', 'profile-two'):
                old = tree / 'AppData' / 'Roaming' / profile / 'teleguard_desktop'
                old.rename(old.with_name('TeleGuard'))
            app = tree / 'AppData' / 'Roaming' / 'profile-one' / 'TeleGuard'
            (app / 'example_photo.jpeg').unlink()
            outside = tree / 'AppData' / 'Local' / 'Temp' / 'TeleGuard' / 'images'
            outside.mkdir(parents=True)
            (outside / 'example_photo.jpeg').write_bytes(fixture.JPEG)
            (outside / 'outside_only.png').write_bytes(fixture.PNG)
            archive = root / 'roaming.zip'
            fixture.pack(tree, archive)
            report = self.run_cli(archive, root / 'roaming-output')
            manifest = json.loads((report / '_lava_data.lava').read_text(encoding='utf-8'))
            artifacts = manifest['artifacts']['TeleGuard Windows']
            self.assertEqual({a['artifact_key']: a['record_count'] for a in artifacts},
                             dict(EXPECTED, teleguardMediaFiles=5))
            with closing(sqlite3.connect(report / '_lava_artifacts.db')) as db:
                references = db.execute(
                    'SELECT source_file,reference_status,media FROM teleguardmediareferences '
                    "WHERE media_file_name='example_photo.jpeg'").fetchall()
                self.assertEqual(len(references), 2)
                for source, status, media in references:
                    self.assertIn('/TeleGuard/', source)
                    if '/profile-one/' in source:
                        self.assertEqual(status, 'Missing')
                        self.assertFalse(media)
                    else:
                        self.assertEqual(status, 'Matched')
                        self.assertTrue(media)
                sources = [row[0] for row in db.execute('SELECT source_file FROM teleguardmediafiles')]
                self.assertEqual(len(sources), 5)
                self.assertTrue(all('/Roaming/' in source for source in sources))

    def test_external_cache_outputs_scale_and_keep_ambiguous_and_missing_references(self):
        """Two real writers, external files, filename aliases and a 12-entry list."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tree = fixture.build_external(root / 'extraction')
            double_archive = root / 'double.zip'
            fixture.pack(tree, double_archive)
            single_archive = root / 'single.zip'
            with zipfile.ZipFile(double_archive) as source, zipfile.ZipFile(single_archive, 'w') as output:
                for item in source.infolist():
                    if '/profile-two/' not in item.filename:
                        output.writestr(item, source.read(item))
            for archive, factor in ((single_archive, 1), (double_archive, 2)):
                report = self.run_cli(archive, root / ('output-' + str(factor)))
                manifest = json.loads((report / '_lava_data.lava').read_text(encoding='utf-8'))
                artifacts = manifest['artifacts']['TeleGuard Windows']
                expected = {'teleguardMessages': 12 * factor, 'teleguardChatOverview': 2 * factor,
                            'teleguardContacts': 6 * factor, 'teleguardMediaReferences': 13 * factor,
                            'teleguardMediaFiles': 11 * factor}
                self.assertEqual({a['artifact_key']: a['record_count'] for a in artifacts}, expected)
                with closing(sqlite3.connect(report / '_lava_artifacts.db')) as db:
                    statuses = dict(db.execute('SELECT reference_status,COUNT(*) FROM '
                                               'teleguardmediareferences GROUP BY reference_status'))
                    self.assertEqual(statuses, {'Matched': 6 * factor, 'Ambiguous': 2 * factor,
                                                'Missing': 4 * factor, 'Invalid reference': factor})
                    expiry = db.execute('SELECT content_expired_as_stored,content_expired_field_present '
                                        'FROM teleguardmediareferences WHERE message_id=?', ('a7',)).fetchall()
                    self.assertEqual(len(expiry), factor)
                    self.assertTrue(all(present == 'Yes' for _, present in expiry))
                    self.assertTrue(all(value is None or str(value) in ('0', 'False')
                                        for value, _ in expiry))
                    parent_flags = db.execute('SELECT content_expired_as_stored,content_expired_field_present '
                                              'FROM teleguardmediareferences WHERE message_id=? '
                                              "AND source_file LIKE '%/profile-one/%'", ('a5',)).fetchall()
                    self.assertEqual(len(parent_flags), 12)
                    self.assertTrue(all(str(value) in ('1', 'True') and present == 'Yes'
                                        for value, present in parent_flags))
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM teleguardmediareferences "
                                                "WHERE media_file_name='late.jpg' AND media IS NOT NULL"
                                                ).fetchone()[0], factor)
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM teleguardmediafiles "
                                                "WHERE reference_status='Unreferenced'"
                                                ).fetchone()[0], 3 * factor)
                    linked = db.execute('SELECT a.source_file,i.source_path,i.extraction_path '
                                        'FROM teleguardmediareferences a JOIN _lava_media_references r '
                                        'ON r.id=a.media JOIN _lava_media_items i ON i.id=r.media_item_id'
                                        ).fetchall()
                    self.assertEqual(len(linked), 6 * factor)
                    for source, media, extracted in linked:
                        profile = 'profile-two' if '/profile-two/' in source else 'profile-one'
                        self.assertIn('/' + profile + '/', media)
                        self.assertNotIn('/Roaming/', media)
                        path = report / extracted
                        expected_bytes = fixture.PDF if path.suffix == '.pdf' else (
                            fixture.JPEG_SECOND if profile == 'profile-two' else fixture.JPEG)
                        self.assertEqual(path.read_bytes(), expected_bytes)
                    for artifact in artifacts:
                        with (report / '_TSV Exports' / (artifact['name'] + '.tsv')).open(
                                encoding='utf-8-sig', newline='') as stream:
                            self.assertEqual(sum(1 for _ in csv.reader(stream, delimiter='\t')) - 1,
                                             expected[artifact['artifact_key']])
                with closing(sqlite3.connect(report / '_Timeline' / 'tl.db')) as db:
                    self.assertEqual(dict(db.execute('SELECT activity,COUNT(*) FROM data GROUP BY activity')),
                                     {a['name']: a['record_count'] for a in artifacts
                                      if a['artifact_key'] != 'teleguardMediaFiles'})

    def test_foreign_database_and_absent_app_produce_no_teleguard_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / 'foreign.sqlite'
            with closing(sqlite3.connect(store)) as db:
                with db:
                    db.execute('CREATE TABLE unrelated(id TEXT)')
            archive = root / 'negative.zip'
            with zipfile.ZipFile(archive, 'w') as output:
                output.write(store, 'unrelated_app/teleguard_database.db')
                output.writestr('unrelated_app/photo.jpg', fixture.JPEG)
            report = self.run_cli(archive, root / 'negative-output')
            manifest = json.loads((report / '_lava_data.lava').read_text(encoding='utf-8'))
            self.assertEqual(manifest.get('artifacts', {}).get('TeleGuard Windows', []), [])


if __name__ == '__main__':
    unittest.main()
