"""Pin the favorite and typed-URL readers of scripts/artifacts/windowsLegacyEdge.py.

The rows are shaped like spartan.edb Favorites rows as the ESE reader returns them; every value is made up.
"""
import datetime
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsLegacyEdge as edge
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
STAMP = 133000000000000000


def fav(item, parent, title, url=None, folder=None, deleted=None, updated=STAMP):
    return {'ItemId': item, 'ParentId': parent, 'Title': title, 'URL': url, 'IsFolder': folder,
            'IsDeleted': deleted, 'DateUpdated': updated}


class FavoritesTest(unittest.TestCase):
    def test_folders_give_a_path_and_no_row_of_their_own(self):
        rows = [fav(b'bar', b'root', '_Favorites_Bar_', folder=255),
                fav(b'sub', b'bar', 'Work', folder=255),
                fav(b'f1', b'sub', 'Page', url='https://example.invalid/', deleted=0),
                fav(b'f2', b'gone', 'Top', url='https://example.invalid/top', deleted=255, updated=0)]
        found = edge.favorite_rows(rows)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0][1:], ('Page', 'https://example.invalid/', '_Favorites_Bar_ > Work', 'No'))
        self.assertEqual(found[0][0], datetime.datetime(1601, 1, 1, tzinfo=UTC)
                         + datetime.timedelta(microseconds=STAMP // 10))
        self.assertEqual(found[1], ('', 'Top', 'https://example.invalid/top', '', 'Yes'))

    def test_a_null_bit_is_blank_not_no(self):
        found = edge.favorite_rows([fav(b'f', b'x', 'T', url='https://example.invalid/', folder=None)])
        self.assertEqual(found[0][4], '')

    def test_a_parent_loop_ends(self):
        rows = [fav(b'a', b'b', 'A', folder=255), fav(b'b', b'a', 'B', folder=255),
                fav(b'f', b'a', 'F', url='https://example.invalid/')]
        self.assertEqual(edge.favorite_rows(rows)[0][3], 'B > A')


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data

    def raw_data(self):
        return self._data


class _Key:
    def __init__(self, values):
        self._values = {v.name(): v for v in values}

    def values(self):
        return list(self._values.values())

    def value(self, name):
        if name not in self._values:
            raise edge.Registry.RegistryValueNotFoundException(name)
        return self._values[name]


class RegistryTypedUrlsTest(unittest.TestCase):
    def test_entries_by_number_with_times_where_recorded(self):
        key = _Key([_Value('url10', 'https://example.invalid/ten'), _Value('url2', 'https://example.invalid/two'),
                    _Value('urlx', 'skip'), _Value('other', 'skip')])
        times = _Key([_Value('url2', struct.pack('<Q', STAMP)), _Value('url10', b'\x01\x02')])
        found = edge.registry_typed_urls(key, times)
        self.assertEqual([(name, url) for name, url, _ in found],
                         [('url2', 'https://example.invalid/two'), ('url10', 'https://example.invalid/ten')])
        self.assertNotEqual(found[0][2], '')
        self.assertEqual(found[1][2], '')

    def test_no_time_key_leaves_times_blank(self):
        found = edge.registry_typed_urls(_Key([_Value('url1', 'https://example.invalid/')]), None)
        self.assertEqual(found, [('url1', 'https://example.invalid/', '')])


if __name__ == '__main__':
    unittest.main()
