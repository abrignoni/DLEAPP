"""Pin the user choice reader in scripts/artifacts/windowsDefaultAppChoices.py.

The hive is stood in for by small objects that answer the python-registry calls the reader makes; the expected rows
are written out.
"""
import datetime
import pathlib
import re
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDefaultAppChoices as choices  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# The fixtures put each hive under a vol<N> folder; match it as a whole path segment, since the
# temporary folder above it can contain the letters vol.
_VOLUME = re.compile(r'[\\/]vol(?=\d)')

UTC = datetime.timezone.utc
SET = datetime.datetime(2021, 3, 4, 5, 6, 7, 800)
LATER = datetime.datetime(2022, 1, 2, 3, 4, 5, 6)
EXTS = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts'
URLS = 'Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations'
HEADERS = (('Key Last Written (UTC)', 'datetime'), 'User', 'User SID', 'Association', 'Program ID', 'Hash', 'Hash Check',
           'Registry Key')
SID = 'S-1-5-21-100-200-300-1001'
# The UserChoice hash of ('.pdf', SID, 'AppXabc', SET), computed by a separate implementation kept outside DLEAPP.
PDF_HASH = 'hJkd84duMXg='


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=(), subkeys=(), written=SET):
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

    def value(self, name):
        for value in self._values:
            if value.name() == name:
                return value
        raise Registry.RegistryValueNotFoundException(name)


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
        return 'vol' + _VOLUME.split(path, maxsplit=1)[1]


def _choice(program='AppXabc', hashed='QUJDREVGR0g=', name='UserChoice', written=SET):
    return _Key(name, [('ProgId', program), ('Hash', hashed)], written=written)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ChoiceRowsTest(unittest.TestCase):
    def test_one_row_per_user_choice_key_with_its_time_program_id_hash_and_key_path(self):
        parent = _Key('FileExts', subkeys=[
            _Key('.PDF', subkeys=[_Key('OpenWithList', [('a', 'x.exe')]), _choice()]),
            _Key('.txt', subkeys=[_choice('txtfile', 'SElKS0xNTk8=', written=LATER)]),
            _Key('.none', subkeys=[_Key('OpenWithProgids', [('p', b'')])])])
        self.assertEqual(choices.choice_rows(parent, EXTS, 'alice'), [
            (SET.replace(tzinfo=UTC), 'alice', '', '.PDF', 'AppXabc', 'QUJDREVGR0g=', '', EXTS + '\\.PDF\\UserChoice'),
            (LATER.replace(tzinfo=UTC), 'alice', '', '.txt', 'txtfile', 'SElKS0xNTk8=', '', EXTS + '\\.txt\\UserChoice')])

    def test_a_latest_key_takes_the_program_id_from_its_subkey_and_follows_the_plain_key(self):
        latest = _Key('UserChoiceLatest', [('Hash', 'TEFURVNUSEE=')], written=LATER,
                      subkeys=[_Key('Other', [('ProgId', 'wrong')]), _Key('ProgId', [('ProgId', 'AppXnew')]),
                               _Key('Zeta', [('ProgId', 'also wrong')])])
        parent = _Key('UrlAssociations', subkeys=[_Key('http', subkeys=[_choice('AppXold'), latest])])
        self.assertEqual(choices.choice_rows(parent, URLS, 'bob'), [
            (SET.replace(tzinfo=UTC), 'bob', '', 'http', 'AppXold', 'QUJDREVGR0g=', '', URLS + '\\http\\UserChoice'),
            (LATER.replace(tzinfo=UTC), 'bob', '', 'http', 'AppXnew', 'TEFURVNUSEE=', '', URLS + '\\http\\UserChoiceLatest')])

    def test_a_program_id_value_of_the_key_wins_over_the_subkey(self):
        key = _Key('UserChoiceLatest', [('ProgId', '')], subkeys=[_Key('ProgId', [('ProgId', 'sub')])])
        rows = choices.choice_rows(_Key(subkeys=[_Key('.a', subkeys=[key])]), EXTS, '')
        self.assertEqual([row[4:6] for row in rows], [('', '')])

    def test_value_and_key_names_are_matched_without_case(self):
        old = _Key('userchoice', [('Progid', 'Applications\\notepad.exe'), ('HASH', 'h')])
        new = _Key('USERCHOICELATEST', [('hash', 'x')], subkeys=[_Key('progid', [('PROGID', 'sub')])])
        rows = choices.choice_rows(_Key(subkeys=[_Key('.log', subkeys=[old, new])]), EXTS, 'u')
        self.assertEqual([row[3:] for row in rows], [
            ('.log', 'Applications\\notepad.exe', 'h', '', EXTS + '\\.log\\userchoice'),
            ('.log', 'sub', 'x', '', EXTS + '\\.log\\USERCHOICELATEST')])

    def test_a_key_without_the_values_gives_blanks_and_values_that_are_not_text_are_left_out(self):
        bare = _Key('UserChoice')
        odd = _Key('UserChoiceLatest', [('ProgId', 7), ('Hash', b'\x01\x02')], subkeys=[_Key('ProgId', [('ProgId', b'x')])])
        rows = choices.choice_rows(_Key(subkeys=[_Key('.x', subkeys=[bare, odd])]), EXTS, 'u')
        self.assertEqual([row[4:6] for row in rows], [('', ''), ('', '')])

    def test_keys_with_other_names_are_not_read(self):
        parent = _Key(subkeys=[_Key('.x', subkeys=[_choice(name='UserChoicePrevious'), _choice(name='Choice'),
                                                    _choice(name='XUserChoice'), _choice(name='UserChoice2')]),
                               _choice(name='UserChoice')])
        self.assertEqual(choices.choice_rows(parent, EXTS, 'u'), [])

    def test_the_hash_check_with_a_sid(self):
        parent = _Key(subkeys=[_Key('.pdf', subkeys=[_choice(hashed=PDF_HASH), _choice(hashed=PDF_HASH, name='UserChoiceLatest')]),
                               _Key('.doc', subkeys=[_choice(hashed=PDF_HASH)]), _Key('.txt', subkeys=[_choice(hashed='')])])
        rows = choices.choice_rows(parent, EXTS, 'alice', SID)
        self.assertEqual([(row[2], row[3], row[6]) for row in rows], [
            (SID, '.pdf', 'Matches'), (SID, '.pdf', ''), (SID, '.doc', 'Does not match'), (SID, '.txt', '')])

    def test_a_key_with_no_time_has_a_blank_time(self):
        rows = choices.choice_rows(_Key(subkeys=[_Key('.x', subkeys=[_choice(written=None)])]), EXTS, 'u')
        self.assertEqual(rows[0][0], '')


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Users/Alice/NTUSER.DAT', 'vol1/Users/bob/NTUSER.DAT', 'vol1/Users/carol/NTUSER.DAT',
                     'vol1/Users/Alice/NTUSER.DAT.LOG1', 'vol1/Users/Alice/AppData/Local/Microsoft/Windows/UsrClass.dat'):
            # the staged path sits under the examiner's own Users folder, as a report folder often does
            path = pathlib.Path(folder.name, 'Users', 'examiner', 'report', 'data', name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            self.paths.append(str(path))
        self.alice, self.bob, self.carol = self.paths[0], self.paths[1], self.paths[2]

    def run_artifact(self, hives):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(choices, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(choices, 'logfunc', side_effect=logged.append):
            result = choices.defaultAppUserChoices.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_both_parent_keys_of_each_user_hive_are_read_under_the_user_folder_name(self):
        hives = {self.alice: _Hive({URLS: _Key(subkeys=[_Key('mailto', subkeys=[_choice('AppXmail', written=LATER)])]),
                                    EXTS: _Key(subkeys=[_Key('.pdf', subkeys=[_choice()])])}),
                 self.bob: _Hive({EXTS: _Key(subkeys=[_Key('.txt', subkeys=[_choice('txtfile')])])}),
                 self.carol: _Hive({})}
        (headers, rows, source), opened, logged = self.run_artifact(hives)
        self.assertEqual(headers, HEADERS)
        self.assertEqual([(row[1], row[3], row[4], row[7]) for row in rows], [
            ('Alice', '.pdf', 'AppXabc', EXTS + '\\.pdf\\UserChoice'),
            ('Alice', 'mailto', 'AppXmail', URLS + '\\mailto\\UserChoice'),
            ('bob', '.txt', 'txtfile', EXTS + '\\.txt\\UserChoice')])
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(opened, [self.alice, self.bob, self.carol])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, [])

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_an_unreadable_hive_is_logged_by_its_path_in_the_extraction_and_skipped(self):
        broken = _Key(subkeys=[_Key('.pdf', subkeys=[_Key('UserChoice', [('ProgId', 'x')], written='not a time')])])
        hives = {self.alice: ValueError('bad header'), self.bob: _Hive({EXTS: _Key(subkeys=[_Key('.txt', subkeys=[_choice()])])}),
                 self.carol: _Hive({URLS: _Key(subkeys=[_Key('http', subkeys=[_choice()])]), EXTS: broken})}
        (_headers, rows, source), _opened, logged = self.run_artifact(hives)
        self.assertEqual([(row[1], row[3]) for row in rows], [('bob', '.txt')])
        self.assertEqual(source, self.bob)
        self.assertEqual(logged[0], 'Default App User Choices: could not read vol1/Users/Alice/NTUSER.DAT: bad header')
        self.assertTrue(logged[1].startswith('Default App User Choices: could not read vol1/Users/carol/NTUSER.DAT: '))
        self.assertEqual(len(logged), 2)

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_the_sid_comes_from_the_software_hive_of_the_same_volume(self):
        folder = pathlib.Path(self.alice).parents[2]
        software = folder / 'Windows' / 'System32' / 'config' / 'SOFTWARE'
        elsewhere = folder.parent / 'vol2' / 'Windows' / 'System32' / 'config' / 'SOFTWARE'
        for path in (software, elsewhere):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
        self.paths += [str(software), str(elsewhere)]
        profile_list = 'Microsoft\\Windows NT\\CurrentVersion\\ProfileList'
        here = _Key(subkeys=[_Key(SID, [('ProfileImagePath', 'C:/Users/Alice\\')]),
                             _Key('S-1-5-21-1-1-1-1', [('ProfileImagePath', 'C:\\Users\\carol')]),
                             _Key('S-1-5-21-2-2-2-2', [('ProfileImagePath', 'C:\\Users\\carol')]),
                             _Key('S-1-5-18', [('ProfileImagePath', 7)])])
        there = _Key(subkeys=[_Key('S-1-5-21-9-9-9-9', [('ProfileImagePath', 'C:\\Users\\bob')])])
        hives = {self.alice: _Hive({EXTS: _Key(subkeys=[_Key('.pdf', subkeys=[_choice(hashed=PDF_HASH)])])}),
                 self.bob: _Hive({EXTS: _Key(subkeys=[_Key('.pdf', subkeys=[_choice(hashed=PDF_HASH)])])}),
                 self.carol: _Hive({EXTS: _Key(subkeys=[_Key('.pdf', subkeys=[_choice(hashed=PDF_HASH)])])}),
                 str(software): _Hive({profile_list: here}), str(elsewhere): _Hive({profile_list: there})}
        (_headers, rows, source), _opened, logged = self.run_artifact(hives)
        self.assertEqual([(row[1], row[2], row[6]) for row in rows], [('Alice', SID, 'Matches'), ('bob', '', ''), ('carol', '', '')])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol, str(software), str(elsewhere)]))
        self.assertEqual(logged, [])

    def test_without_python_registry_nothing_is_read_and_the_run_log_says_so(self):
        logged = []
        with mock.patch.object(choices, 'Registry', None), mock.patch.object(choices, 'open_hive') as opened, \
                mock.patch.object(choices, 'logfunc', side_effect=logged.append):
            headers, rows, source = choices.defaultAppUserChoices.__wrapped__(_Context(self.paths))
        self.assertEqual((headers, rows, source), (HEADERS, [], ''))
        opened.assert_not_called()
        self.assertEqual(logged, ['Default App User Choices: the python-registry package is not installed'])


if __name__ == '__main__':
    unittest.main()
