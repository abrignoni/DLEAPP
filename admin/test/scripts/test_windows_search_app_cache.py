"""Pin how the windowsSearchAppCache artifacts read DeviceSearchCache AppCache files.

Author: @AlexisBrignoni, Claude.

Every file here is synthetic, written with the property layout the tested AppCache files use:
a JSON array of objects whose properties are {"Value": ..., "Type": ...}. The expected values
are written out, never read back from the code under test.
"""
import ast
import datetime
import fnmatch
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSearchAppCache as cache  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
SEARCH = 'C/Users/{user}/AppData/Local/Packages/Microsoft.Windows.Search_cw5n1h2txyewy/LocalState/DeviceSearchCache'
CORTANA = 'C/Users/{user}/AppData/Local/Packages/Microsoft.Windows.Cortana_cw5n1h2txyewy/LocalState/DeviceSearchCache'
# 2020-09-18 22:00:00 UTC and 2020-09-19 00:00:00 UTC as FILETIMEs.
FIRST = 132449400000000000
SECOND = 132449472000000000


def entry(name, times_used=0, accessed=0, jump_list='[]'):
    def prop(value, kind=12):
        return {'Value': value, 'Type': kind}
    return {
        'System.AppUserModel.PackageFullName': prop('N/A'),
        'System.ConnectedSearch.JumpList': prop(jump_list),
        'System.ConnectedSearch.VoiceCommandExamples': prop('[]'),
        'System.DateAccessed': prop(accessed, 14),
        'System.FileExtension': prop('.exe'),
        'System.FileName': prop(name),
        'System.Identity': prop('id-' + name),
        'System.ItemNameDisplay': prop(name.title()),
        'System.ItemType': prop('Desktop'),
        'System.Kind': prop('program'),
        'System.ParsingName': prop('{GUID}\\' + name + '.exe'),
        'System.Software.ProductVersion': prop('1.0'),
        'System.Software.TimesUsed': prop(times_used, 5),
        'System.Tile.Background': prop(0, 5),
        'System.Tile.EncodedTargetPath': prop('C:\\Apps\\' + name + '.exe'),
        'System.Tile.SmallLogoPath': prop(''),
    }


def dumps(entries, accessed_text=None):
    """JSON text; accessed_text replaces a DateAccessed placeholder with floating-point text."""
    text = json.dumps(entries)
    if accessed_text:
        text = text.replace('"ACCESSED"', accessed_text)
    return text


JUMP = json.dumps([{'Type': 1, 'Items': [
    {'Type': 1, 'Name': 'report.docx', 'Path': 'C:\\Docs\\report.docx', 'Description': 'Doc',
     'Date': '2020-9-18', 'Points': 2.5}]}])


class AppCacheTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, folder, number, text):
        path = self.root / folder / f'AppCache{number}.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        self.files.append(str(path))
        return path

    def _run(self, function):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(cache, 'logfunc') as log:
            result = getattr(cache, function).__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def test_rows_fold_across_snapshots_and_keep_changed_values(self):
        folder = SEARCH.format(user='rick')
        self._write(folder, FIRST, dumps([
            entry('calc', 1, 'ACCESSED'), entry('idle')], '1.3244940000000001e+17'))
        self._write(folder, SECOND, dumps([
            entry('calc', 2, 132449470000000000), entry('idle')]))
        (headers, rows, source), log = self._run('windowsSearchAppCache')
        self.assertEqual(len(headers), len(rows[0]))
        first = datetime.datetime(2020, 9, 18, 22, tzinfo=UTC)
        second = datetime.datetime(2020, 9, 19, tzinfo=UTC)
        tail = ('Calc', '{GUID}\\calc.exe', 'C:\\Apps\\calc.exe', 'calc', '.exe', 'program',
                'Desktop', '1.0', 'id-calc', 'N/A', 0)
        self.assertEqual(rows, [
            (datetime.datetime(2020, 9, 18, 22, 0, 0, 1, tzinfo=UTC), first, first,
             '1.3244940000000001e+17', 1)
            + tail + (1, 'No', 'rick', f'{folder}/AppCache{FIRST}.txt'),
            (datetime.datetime(2020, 9, 18, 23, 56, 40, tzinfo=UTC), second, second,
             '132449470000000000', 2)
            + tail + (1, 'Yes', 'rick', f'{folder}/AppCache{SECOND}.txt'),
        ])
        self.assertEqual(source.split('\n'), [str(self.root / folder / f'AppCache{FIRST}.txt'),
                                              str(self.root / folder / f'AppCache{SECOND}.txt')])
        self.assertIn(f'Windows Search App Cache: {folder}: 2 entries with Times Used 0, Date '
                      'Accessed 0 and no jump list items not reported', log)

    def test_an_unchanged_entry_is_one_row_counting_its_snapshots(self):
        folder = CORTANA.format(user='jdoe')
        for number in (FIRST, SECOND):
            self._write(folder, number, dumps([entry('calc', 3, 0, JUMP)]))
        (_headers, rows, _source), _log = self._run('windowsSearchAppCache')
        self.assertEqual([(row[0], row[4], row[15], row[1], row[2], row[16]) for row in rows], [
            ('', 3, 1, datetime.datetime(2020, 9, 18, 22, tzinfo=UTC),
             datetime.datetime(2020, 9, 19, tzinfo=UTC), 2)])
        self.assertEqual(rows[0][17:], ('Yes', 'jdoe', f'{folder}/AppCache{SECOND}.txt'))

    def test_a_value_set_repeated_in_one_file_counts_that_file_once(self):
        folder = SEARCH.format(user='rick')
        self._write(folder, FIRST, dumps([entry('calc', 1, FIRST), entry('calc', 1, FIRST)]))
        (_headers, rows, _source), _log = self._run('windowsSearchAppCache')
        self.assertEqual([row[16] for row in rows], [1])

    def test_two_users_keep_their_own_rows(self):
        for user in ('rick', 'morty'):
            self._write(SEARCH.format(user=user), FIRST, dumps([entry('calc', 1, FIRST)]))
        (_headers, rows, _source), _log = self._run('windowsSearchAppCache')
        self.assertEqual(sorted(row[-2] for row in rows), ['morty', 'rick'])

    def test_jump_list_items(self):
        folder = SEARCH.format(user='rick')
        for number in (FIRST, SECOND):
            self._write(folder, number, dumps([entry('word', 0, 0, JUMP)]))
        (headers, rows, _source), _log = self._run('windowsSearchAppCacheJumpLists')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(
            '2020-9-18', datetime.datetime(2020, 9, 18, 22, tzinfo=UTC),
            datetime.datetime(2020, 9, 19, tzinfo=UTC), 'Word', '{GUID}\\word.exe', 'report.docx',
            'C:\\Docs\\report.docx', 'Doc', '1', '', '1', '2.5', 2, 'Yes', 'rick',
            f'{folder}/AppCache{SECOND}.txt')])

    def test_a_file_that_is_not_json_is_logged_and_left_out(self):
        folder = SEARCH.format(user='rick')
        self._write(folder, FIRST, '[{"System.FileName": ')
        (_headers, rows, source), log = self._run('windowsSearchAppCache')
        self.assertEqual((rows, source), ([], ''))
        self.assertTrue(any(line.startswith(f'Windows Search App Cache: could not read {folder}/')
                            for line in log))

    def test_the_paths_match_both_packages_and_not_a_lookalike(self):
        tree = ast.parse((REPO_ROOT / 'scripts' / 'artifacts' / 'windowsSearchAppCache.py')
                         .read_text(encoding='utf-8'))
        block = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and getattr(n.targets[0], 'id', '') == '__artifacts_v2__')
        patterns = block['windowsSearchAppCache']['paths']
        def hits(relative):
            return [p for p in patterns if fnmatch.fnmatchcase('root/' + relative, p)]
        self.assertEqual(len(hits(SEARCH.format(user='u') + f'/AppCache{FIRST}.txt')), 1)
        self.assertEqual(len(hits(CORTANA.format(user='u') + f'/AppCache{FIRST}.txt')), 1)
        self.assertEqual(hits(SEARCH.format(user='u') + '/SettingsCache.txt'), [])
        self.assertEqual(hits('C/Users/u/AppData/Local/Packages/windows.immersivecontrolpanel_cw5n1h2txyewy'
                              f'/LocalState/DeviceSearchCache/AppCache{FIRST}.txt'), [])


if __name__ == '__main__':
    unittest.main()
