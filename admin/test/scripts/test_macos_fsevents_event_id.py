"""An FSEvents event ID above the largest integer SQLite holds is reported as text.

Python's sqlite3 cannot bind an integer above 2**63 - 1, so a row carrying one made the
LAVA insert fail. The page is built here by hand; expected values are written out.
"""
import pathlib
import sqlite3
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosFSEvents  # pylint: disable=wrong-import-position


def _page(records):
    body = b''.join(path.encode() + b'\x00' + struct.pack('<QI', event_id, flags)
                    for path, event_id, flags in records)
    return b'1SLD' + struct.pack('<II', 0, 12 + len(body)) + body


class EventIdTest(unittest.TestCase):
    def test_an_event_id_above_the_sqlite_range_is_text_and_a_smaller_one_stays_a_number(self):
        rows = list(macosFSEvents._parse_stream(  # pylint: disable=protected-access
            _page([('a.txt', 18427042000980820600, 0x00008000), ('b.txt', 9223372036854775807, 0x00008000),
                   ('c.txt', 12, 0x00008000)]), 'source'))
        self.assertEqual([row[0] for row in rows], ['18427042000980820600', 9223372036854775807, 12])
        self.assertEqual([row[1] for row in rows], ['a.txt', 'b.txt', 'c.txt'])

    def test_the_rows_can_be_inserted_into_sqlite(self):
        rows = list(macosFSEvents._parse_stream(  # pylint: disable=protected-access
            _page([('a.txt', 18446744073709551615, 0x00008000)]), 'source'))
        database = sqlite3.connect(':memory:')
        self.addCleanup(database.close)
        database.execute('CREATE TABLE t (event_id TEXT, path TEXT)')
        database.executemany('INSERT INTO t VALUES (?, ?)', [row[:2] for row in rows])
        self.assertEqual(database.execute('SELECT event_id, path FROM t').fetchall(),
                         [('18446744073709551615', 'a.txt')])


if __name__ == '__main__':
    unittest.main()
