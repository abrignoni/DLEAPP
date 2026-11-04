"""Pin cookie_records and ieFavorites in scripts/artifacts/windowsIeFavoritesCookies.py (made-up values)."""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsIeFavoritesCookies as ie  # pylint: disable=wrong-import-position


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()

    def get_seeker(self):
        return None


class CookieTest(unittest.TestCase):
    def test_records_and_times(self):
        text = ('SITE\nabc\nexample.invalid/path/\n1024\n716854528\n30023907\n3496880416\n29656779\n*\n'
                'short\n*\n')
        records = ie.cookie_records(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][:3], ['SITE', 'abc', 'example.invalid/path/'])
        self.assertEqual(ie._filetime('30023907', '716854528').year, 2009)  # pylint: disable=protected-access


class FavoritesTest(unittest.TestCase):
    def test_a_url_file_in_favorites(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'vol', 'Users', 'lab', 'Favorites', 'Links')
            folder.mkdir(parents=True)
            (folder / 'KD.url').write_bytes(b'[{000214A0-0000-0000-C000-000000000046}]\r\nProp3=19,11\r\n'
                                            b'[InternetShortcut]\r\nIDList=\r\nURL=https://kd.example.invalid/\r\n')
            (folder / 'other.url').write_bytes(b'not an ini')
            context = FakeContext(tmp, [str(folder / 'KD.url'), str(folder / 'other.url')])
            with mock.patch.object(ie, 'logfunc'):
                headers, rows, _source = ie.ieFavorites.__wrapped__(context)
        self.assertEqual(len(headers), 8)
        self.assertEqual(rows, [('', '', 'KD', 'https://kd.example.invalid/', '', '', 'Favorites/Links', 'lab')])


if __name__ == '__main__':
    unittest.main()
