"""Pin the bitmap aggregation in scripts/artifacts/chromiumFavicons.py.

The tables follow the version 8 schema in Chromium's favicon database source: one
favicon_bitmaps row per stored size, last_updated set for icons fetched on a visit and
last_requested for icons fetched on demand. Expected values are written out.
"""
import pathlib
import sqlite3
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumFavicons as fav  # pylint: disable=wrong-import-position


def _db():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE favicon_bitmaps (id INTEGER PRIMARY KEY, icon_id INTEGER NOT NULL, '
               'last_updated INTEGER DEFAULT 0, image_data BLOB, width INTEGER DEFAULT 0, '
               'height INTEGER DEFAULT 0, last_requested INTEGER DEFAULT 0)')
    db.executemany('INSERT INTO favicon_bitmaps (icon_id, last_updated, image_data, width, height, '
                   'last_requested) VALUES (?, ?, ?, ?, ?, ?)', [
                       (1, 100, b'small', 16, 16, 0),
                       (1, 250, b'large', 32, 32, 0),
                       (2, 0, b'touch', 96, 96, 700),
                       (3, 0, None, 16, 16, 0)])
    return db


class BitmapsTest(unittest.TestCase):
    def test_latest_times_sizes_and_largest_image(self):
        icons = fav._bitmaps(_db())  # pylint: disable=protected-access
        self.assertEqual(icons[1], (250, 0, ['16x16', '32x32'], (1024, b'large')))
        self.assertEqual(icons[2], (0, 700, ['96x96'], (9216, b'touch')))

    def test_icon_without_image_data(self):
        icons = fav._bitmaps(_db())  # pylint: disable=protected-access
        self.assertEqual(icons[3], (0, 0, ['16x16'], None))


class LabelsTest(unittest.TestCase):
    def test_persisted_icon_types(self):
        self.assertEqual(fav._ICON_TYPES, {1: 'kFavicon', 2: 'kTouchIcon',  # pylint: disable=protected-access
                                           4: 'kTouchPrecomposedIcon', 8: 'kWebManifestIcon'})


if __name__ == '__main__':
    unittest.main()
