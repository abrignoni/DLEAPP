"""Pin how scripts/ese_rows walks an ESE table: flag-deleted nodes are not rows."""
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import ese_rows
from scripts.artifacts import windowsSearch, windowsSrum, windowsThumbcache, windowsWebcache
from scripts.vendor import impacket_ese
# pylint: enable=wrong-import-position

LEAF = impacket_ese.FLAGS_LEAF
DELETED = impacket_ese.TAG_DEFUNCT


class FakePage:
    """A table page as the reader sees one: tag 0 is the page header, data tags follow."""

    def __init__(self, tags, next_page=0, page_flags=LEAF):
        self.tags = [(0, b'')] + tags
        self.firstDataTag = 1  # pylint: disable=invalid-name
        self.tagCount = len(self.tags)  # pylint: disable=invalid-name
        self.record = {'PageFlags': page_flags, 'NextPageNumber': next_page}

    def getTag(self, index):  # pylint: disable=invalid-name
        return self.tags[index]


def tag(entry, flags=0):
    """A leaf entry with no common key and no local key, then the record's data."""
    return (flags, b'\x00\x00' + entry)


class FakeDatabase:
    def __init__(self, pages, first=1):
        self.pages = pages
        self.first = first

    def openTable(self, name):  # pylint: disable=invalid-name
        if name == 'missing':
            return None
        page = self.pages[self.first]
        return {'CurrentPageData': page, 'CurrentTag': page.firstDataTag - 1, 'TableData': name}

    def getPage(self, number):  # pylint: disable=invalid-name
        return self.pages[number]

    @staticmethod
    def _ESENT_DB__tagToRecord(_cursor, entry):  # pylint: disable=invalid-name
        if entry.startswith(b'bad'):
            raise ValueError('cannot convert')
        return {'value': entry.decode()}


def two_pages():
    return FakeDatabase({
        1: FakePage([tag(b'a'), tag(b'b', DELETED), tag(b'c')], next_page=2),
        2: FakePage([tag(b'd'), tag(b'bad record'), tag(b'e')]),
    })


class TableRowsTest(unittest.TestCase):
    def test_flag_deleted_nodes_are_skipped_and_counted(self):
        walk = ese_rows.TableRows(two_pages(), 'T')
        self.assertEqual([r['value'] for r in walk], ['a', 'c', 'd', 'e'])
        self.assertEqual((walk.deleted, walk.unreadable, walk.found, walk.capped), (1, 1, True, False))
        self.assertEqual(walk.errors, ['ValueError: cannot convert'])

    def test_a_deleted_node_is_skipped_even_when_its_data_would_convert(self):
        database = FakeDatabase({1: FakePage([tag(b'live'), tag(b'still has data', DELETED)])})
        self.assertEqual([r['value'] for r in ese_rows.TableRows(database, 'T')], ['live'])

    def test_a_page_that_is_not_a_leaf_is_passed_over(self):
        database = FakeDatabase({
            1: FakePage([tag(b'a')], next_page=2),
            2: FakePage([tag(b'never read')], next_page=3, page_flags=0),
            3: FakePage([tag(b'b')]),
        })
        self.assertEqual([r['value'] for r in ese_rows.TableRows(database, 'T')], ['a', 'b'])

    def test_the_cap_stops_the_walk_and_says_so(self):
        walk = ese_rows.TableRows(two_pages(), 'T', cap=2)
        self.assertEqual([r['value'] for r in walk], ['a'])
        self.assertTrue(walk.capped)
        self.assertIn('stopped after 2 records', walk.summary())

    def test_a_missing_table_yields_nothing(self):
        walk = ese_rows.TableRows(two_pages(), 'missing')
        self.assertEqual((list(walk), walk.found, walk.summary()), ([], False, ''))

    def test_a_special_leaf_page_is_refused(self):
        database = FakeDatabase({1: FakePage([tag(b'a')], page_flags=LEAF | impacket_ese.FLAGS_LONG_VALUE)})
        with self.assertRaises(ValueError):
            list(ese_rows.TableRows(database, 'T'))

    def test_the_summary_names_the_table_and_both_counts(self):
        walk = ese_rows.TableRows(two_pages(), 'Container_1')
        list(walk)
        self.assertEqual(walk.summary(), 'Container_1: 1 record(s) ESE marks deleted (fNDDeleted) were not read; '
                                         '1 record(s) the ESE reader could not convert were skipped '
                                         '(ValueError: cannot convert)')


class CallerTest(unittest.TestCase):
    """Each ESE artifact reads its tables through TableRows and logs what it skipped."""

    def test_webcache_reads_a_container_through_the_walk(self):
        rows = []
        with mock.patch.object(windowsWebcache, 'logfunc') as log:
            skipped = windowsWebcache._read_container(  # pylint: disable=protected-access
                two_pages(), {'Container_7'}, 7, 'History', 'dir', lambda row, name, d: (row['value'], name),
                rows, 'WebCache History', 'p/WebCacheV01.dat')
        self.assertEqual((rows, skipped), ([('a', 'History'), ('c', 'History'), ('d', 'History'), ('e', 'History')], 2))
        self.assertIn('p/WebCacheV01.dat, Container_7: 1 record(s) ESE marks deleted', log.call_args.args[0])

    def test_srum_says_when_a_table_is_missing_and_otherwise_logs_the_skips(self):
        with mock.patch.object(windowsSrum, 'logfunc') as log:
            idmap = windowsSrum._build_idmap(two_pages(), 'SRUM', 'p/SRUDB.dat')  # pylint: disable=protected-access
        self.assertEqual(len(idmap), 1)  # the fake rows carry no IdIndex, so all four share one key
        self.assertIn('p/SRUDB.dat, SruDbIdMapTable: 1 record(s) ESE marks deleted', log.call_args.args[0])
        with mock.patch.object(windowsSrum, 'logfunc') as log, \
                mock.patch.object(windowsSrum, '_IDMAP', 'missing'):
            windowsSrum._build_idmap(two_pages(), 'SRUM', 'p/SRUDB.dat')  # pylint: disable=protected-access
        self.assertIn('has no missing', log.call_args.args[0])

    def test_search_and_thumbcache_read_through_the_walk(self):
        for module in (windowsSearch, windowsThumbcache):
            source = inspect_source(module)
            self.assertIn('ese_rows.TableRows(database', source)
            self.assertNotIn('getNextRow', source)
        self.assertNotIn('getNextRow', inspect_source(windowsWebcache))
        self.assertNotIn('getNextRow', inspect_source(windowsSrum))


def inspect_source(module):
    return pathlib.Path(module.__file__).read_text(encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
