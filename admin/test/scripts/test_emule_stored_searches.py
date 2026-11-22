"""eMule StoredSearches.met: declared counts, parent links, sources and tag names, on bytes built from the layout."""
import pathlib
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import emule  # pylint: disable=wrong-import-position
from scripts.artifacts import emule as emule_artifacts  # pylint: disable=wrong-import-position


def met_string(text):
    raw = text.encode('utf-8')
    return struct.pack('<H', len(raw)) + raw


def string_tag(name, text):
    """A TAGTYPE_STRING tag with a one-byte (int) or longer (bytes) name."""
    if isinstance(name, int):
        head = bytes([emule.TAGTYPE_STRING | 0x80, name])
    else:
        head = bytes([emule.TAGTYPE_STRING]) + struct.pack('<H', len(name)) + name
    return head + met_string(text)


def result(name, extra=()):
    tags = [string_tag(emule.FT_FILENAME, name), *extra]
    return bytes(16) + struct.pack('<IHI', 0, 0, len(tags)) + b''.join(tags)


def search(text, results, declared=None):
    head = struct.pack('<IBB', 1, 1, 0) + met_string('') + met_string(text) + met_string('')
    return head + struct.pack('<I', len(results) if declared is None else declared) + b''.join(results)


def store(*searches):
    return bytes([emule.MET_HEADER_I64TAGS, 1]) + struct.pack('<H', len(searches)) + b''.join(searches)


class StoredSearches(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name)
        self.files = []

    def add(self, profile, data):
        path = self.root / 'Users' / 'tester' / profile / 'eMule' / 'config' / 'StoredSearches.met'
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        self.files.append(str(path))
        return str(path.relative_to(self.root))

    def run_artifact(self, function):
        context = SimpleNamespace(get_files_found=lambda: self.files,
                                  get_relative_path=lambda path: str(pathlib.Path(path).relative_to(self.root)))
        headers, rows, sources = function.__wrapped__(context)
        return [dict(zip(headers, row)) for row in rows], sources.split('\n')

    def test_a_cut_file_keeps_the_declared_count_apart_from_what_was_read(self):
        whole = store(search('first', [result('a.bin'), result('b.bin')]))
        self.add('one', whole[:-3])
        rows, _sources = self.run_artifact(emule_artifacts.emuleStoredSearches)
        self.assertEqual((rows[0]['Stored Results'], rows[0]['Results Read']), (2, 1))

    def test_a_file_cut_before_the_count_leaves_it_blank(self):
        whole = store(search('first', []))
        self.add('one', whole[:-2])
        rows, _sources = self.run_artifact(emule_artifacts.emuleStoredSearches)
        self.assertEqual((rows[0]['Stored Results'], rows[0]['Results Read']), ('', 0))

    def test_same_text_results_link_to_their_own_search_and_file(self):
        first = self.add('one', store(search('same', [result('a.bin')]), search('same', [result('b.bin')])))
        second = self.add('two', store(search('same', [result('c.bin')])))
        rows, _sources = self.run_artifact(emule_artifacts.emuleStoredSearchResults)
        self.assertEqual({(r['File Name'], r['Search Order'], r['Source File']) for r in rows},
                         {('a.bin', 1, first), ('b.bin', 2, first), ('c.bin', 1, second)})
        parents, _sources = self.run_artifact(emule_artifacts.emuleStoredSearches)
        self.assertEqual({(r['Search Order'], r['Source File']) for r in parents},
                         {(1, first), (2, first), (1, second)})

    def test_every_file_read_is_a_source_even_with_no_rows(self):
        self.add('one', store(search('text', [result('a.bin')])))
        self.add('two', store(search('empty', [])))
        self.add('three', b'not a store')
        for function in (emule_artifacts.emuleStoredSearches, emule_artifacts.emuleStoredSearchResults):
            with self.subTest(function=function.__name__):
                _rows, sources = self.run_artifact(function)
                self.assertEqual(sorted(sources), sorted(self.files))

    def test_a_named_tag_and_a_numbered_tag_both_survive(self):
        extra = (string_tag(b'artist', 'named value'), string_tag(0xD0, 'numbered value'))
        self.add('one', store(search('text', [result('a.bin', extra)])))
        rows, _sources = self.run_artifact(emule_artifacts.emuleStoredSearchResults)
        other = rows[0]['Other Values']
        self.assertIn('artist [name 617274697374]=named value', other)
        self.assertIn('artist [tag 0xD0]=numbered value', other)

    def test_an_unshared_tag_name_stays_plain(self):
        self.add('one', store(search('text', [result('a.bin', (string_tag(0xD0, 'value'),))])))
        rows, _sources = self.run_artifact(emule_artifacts.emuleStoredSearchResults)
        self.assertEqual(rows[0]['Other Values'], 'artist=value')


if __name__ == '__main__':
    unittest.main()
