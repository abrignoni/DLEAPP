"""Pin how scripts/ese_rows walks an ESE table: flag-deleted nodes are not rows, and a value
stored apart from its record is read from the long value tree."""
import pathlib
import struct
import sys
import unittest
from binascii import hexlify
from collections import OrderedDict
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
COMMON = impacket_ese.TAG_COMMON
SEPARATED = 0x05  # TAGFLD_HEADER fLongValue | fSeparated


class FakePage:
    """A table page as the reader sees one: tag 0 is the page header, data tags follow."""

    def __init__(self, tags, next_page=0, page_flags=LEAF, common=b''):
        self.tags = [(0, common)] + tags
        self.firstDataTag = 1  # pylint: disable=invalid-name
        self.tagCount = len(self.tags)  # pylint: disable=invalid-name
        self.record = {'PageFlags': page_flags, 'NextPageNumber': next_page}

    def getTag(self, index):  # pylint: disable=invalid-name
        return self.tags[index]

    def iterDataTagNums(self):  # pylint: disable=invalid-name
        return range(1, self.tagCount)


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
        return {'CurrentPageData': page, 'CurrentTag': page.firstDataTag - 1,
                'TableData': {'Columns': {}}}

    def getPage(self, number):  # pylint: disable=invalid-name
        return self.pages[number]

    def mountDB(self):  # pylint: disable=invalid-name
        pass

    def close(self):
        pass

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


# Long values. A long value ID is held little-endian in the record and big-endian in the tree.
LID = 5
STORED = struct.pack('<I', LID)
KEY = struct.pack('>I', LID)


def root(size, flags=None):
    """An LVROOT (reference count, size), or an LVROOT2 when `flags` is given."""
    return struct.pack('<II', 1, size) + (bytes([flags]) if flags is not None else b'')


def tree(*values):
    """A long value index from (key, root data, [(offset, piece data), ...]) triples."""
    index = {}
    for key, root_data, pieces in values:
        if root_data is not None:
            ese_rows.index_node(index, key, root_data)
        for offset, data in pieces:
            ese_rows.index_node(index, key + struct.pack('>I', offset), data)
    return index


class LongValueTest(unittest.TestCase):
    def test_pieces_are_joined_in_offset_order(self):
        index = tree((KEY, root(12), [(8, b'IJKL'), (0, b'ABCDEFGH')]))
        self.assertEqual(ese_rows.chunk_size(index), 8)
        self.assertEqual(ese_rows.long_value(index, STORED, 8), (b'ABCDEFGHIJKL', None))

    def test_a_value_in_one_piece_needs_no_chunk_size(self):
        index = tree((KEY, root(5), [(0, b'hello')]))
        self.assertIsNone(ese_rows.chunk_size(index))
        self.assertEqual(ese_rows.long_value(index, STORED), (b'hello', None))

    def test_a_64_bit_id_is_told_from_a_32_bit_piece_by_its_top_bit(self):
        lid64 = 0x8000000000000007
        key64 = struct.pack('>Q', lid64)
        index = tree((key64, root(6), [(0, b'sixtyf')]))
        index.update(tree((KEY, root(4), [(0, b'abcd')])))
        # An 8-byte key is a 64-bit root when its top bit is set and a 32-bit piece otherwise.
        self.assertEqual(index[key64][0], root(6))
        self.assertEqual(index[KEY][1], [(0, b'abcd')])
        self.assertEqual(ese_rows.long_value(index, struct.pack('<Q', lid64)), (b'sixtyf', None))

    def test_a_piece_storing_less_than_the_chunk_size_is_compressed(self):
        index = tree((KEY, root(12), [(0, b'ABCDE'), (8, b'IJKL')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8), (None, 'a compressed piece'))

    def test_a_last_piece_storing_less_than_the_rest_of_the_value_is_compressed(self):
        index = tree((KEY, root(12), [(0, b'ABCDEFGH'), (8, b'IJ')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8), (None, 'a compressed piece'))

    def test_a_missing_middle_piece_is_named_missing_not_compressed(self):
        other = struct.pack('>I', 6)
        index = tree((KEY, root(20), [(0, b'ABCDEFGH'), (16, b'QRST')]),
                     (other, root(10), [(0, b'abcdefgh'), (8, b'ij')]))
        chunk = ese_rows.chunk_size(index)
        self.assertEqual(chunk, 8)
        self.assertEqual(ese_rows.long_value(index, STORED, chunk),
                         (None, 'a piece missing from the long value tree'))

    def test_missing_trailing_pieces_are_named_missing(self):
        index = tree((KEY, root(20), [(0, b'ABCDEFGH'), (8, b'IJKLMNOP')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8),
                         (None, 'a piece missing from the long value tree'))

    def test_a_missing_first_piece_is_named_missing(self):
        index = tree((KEY, root(12), [(8, b'IJKL')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8),
                         (None, 'a piece missing from the long value tree'))

    def test_a_piece_longer_than_its_chunk_is_refused(self):
        index = tree((KEY, root(12), [(0, b'ABCDEFGHI'), (8, b'IJKL')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8), (None, 'a piece longer than ESE writes one'))

    def test_an_encrypted_value_is_refused(self):
        index = tree((KEY, root(4, flags=0x01), [(0, b'\x9a\x11\x02\x7f')]))
        self.assertEqual(ese_rows.long_value(index, STORED), (None, 'the value is encrypted'))
        index = tree((KEY, root(4, flags=0x00), [(0, b'abcd')]))
        self.assertEqual(ese_rows.long_value(index, STORED), (b'abcd', None))

    def test_two_pieces_at_one_offset_are_refused(self):
        index = tree((KEY, root(16), [(0, b'ABCDEFGH'), (0, b'abcdefgh'), (8, b'IJKLMNOP')]))
        self.assertEqual(ese_rows.long_value(index, STORED, 8), (None, 'two pieces at one offset'))

    def test_a_root_too_short_to_hold_the_size_is_refused(self):
        index = tree((KEY, b'\x01\x00\x00\x00', [(0, b'abcd')]))
        self.assertEqual(ese_rows.long_value(index, STORED), (None, 'a root shorter than ESE writes one'))

    def test_an_id_with_no_root_or_of_the_wrong_length_is_refused(self):
        index = tree((KEY, None, [(0, b'abcd')]))
        self.assertEqual(ese_rows.long_value(index, STORED), (None, 'no root in the long value tree'))
        self.assertEqual(ese_rows.long_value(index, b'\x05\x00\x00'), (None, 'an ID of unexpected length'))

    def test_the_chunk_size_is_read_off_every_value(self):
        index = tree((KEY, root(20000), [(0, b'x' * 8150), (8150, b'y' * 8150), (16300, b'z' * 3700)]),
                     (struct.pack('>I', 9), root(3), [(0, b'abc')]))
        self.assertEqual(ese_rows.chunk_size(index), 8150)


class FakeTreePage:
    """A long value tree page: tag 0 holds the key prefix the page's nodes share."""

    def __init__(self, tags, page_flags, common=b''):
        self.tags = [(0, common)] + tags
        self.record = {'PageFlags': page_flags}

    def getTag(self, index):  # pylint: disable=invalid-name
        return self.tags[index]

    def iterDataTagNums(self):  # pylint: disable=invalid-name
        return range(1, len(self.tags))


def lv_node(key, value, common=None, flags=0):
    """A long value tree leaf node: a common-prefix length when the node shares the page's
    prefix, then its own key and the node's data."""
    if common is None:
        return (flags, struct.pack('<H', len(key)) + key + value)
    return (flags | COMMON, struct.pack('<HH', common, len(key)) + key + value)


def branch(child, flags=0):
    return (flags, struct.pack('<HI', 0, child))


class TreeDatabase:
    """A database holding one table whose long value tree's root page is 10."""

    def __init__(self, pages, total_pages=20):
        self.pages = pages
        self.read = []
        self._ESENT_DB__totalPages = total_pages  # pylint: disable=invalid-name
        catalog = struct.pack('<LHLLL', 2, impacket_ese.CATALOG_TYPE_LONG_VALUE, 3, 10, 0)
        self._ESENT_DB__tables = {  # pylint: disable=invalid-name
            b'T': {'LongValues': {b'LV': {'EntryData': struct.pack('<BBH', 0, 127, 4) + catalog}}}}

    def getPage(self, number):  # pylint: disable=invalid-name
        self.read.append(number)
        return self.pages[number]


class LongValueTreeTest(unittest.TestCase):
    def test_the_tree_is_read_through_its_branches_without_deleted_nodes(self):
        second = struct.pack('>I', 6)
        database = TreeDatabase({
            10: FakeTreePage([branch(11), branch(13, DELETED), branch(12), branch(11)], page_flags=0),
            # Page 11's nodes share the ID as their key prefix.
            11: FakeTreePage([lv_node(b'', root(12), common=4),
                              lv_node(struct.pack('>I', 0), b'ABCDEFGH', common=4),
                              lv_node(struct.pack('>I', 8), b'stale', common=4, flags=DELETED),
                              lv_node(struct.pack('>I', 8), b'IJKL', common=4)], page_flags=LEAF, common=KEY),
            12: FakeTreePage([lv_node(second, root(3)), lv_node(second + struct.pack('>I', 0), b'abc')],
                             page_flags=LEAF),
        })
        index = ese_rows.long_value_tree(database, 'T')
        self.assertEqual(sorted(database.read), [10, 11, 12])  # 13 is a deleted branch, 11 read once
        self.assertEqual(index, {KEY: [root(12), [(0, b'ABCDEFGH'), (8, b'IJKL')]],
                                 second: [root(3), [(0, b'abc')]]})
        self.assertEqual(ese_rows.long_value(index, STORED, ese_rows.chunk_size(index)),
                         (b'ABCDEFGHIJKL', None))

    def test_a_page_past_the_end_of_the_file_is_not_read(self):
        database = TreeDatabase({
            10: FakeTreePage([branch(11), branch(21), branch(0)], page_flags=0),
            11: FakeTreePage([lv_node(KEY, root(3)), lv_node(KEY + struct.pack('>I', 0), b'abc')], page_flags=LEAF),
        })
        index = ese_rows.long_value_tree(database, 'T')
        self.assertEqual(sorted(database.read), [10, 11])
        self.assertEqual(ese_rows.long_value(index, STORED), (b'abc', None))
        self.assertEqual(ese_rows.long_value_tree(TreeDatabase({}, total_pages=9), 'T'), {})

    def test_a_table_with_no_long_value_tree_gives_an_empty_index(self):
        database = TreeDatabase({})
        self.assertEqual(ese_rows.long_value_tree(database, 'Other'), {})


def record_bytes(tagged, variable=(), marked=False):
    """A record as ESE lays one out: no fixed columns, then the variable columns (None for an
    empty one), then the tagged directory and items, each item led by its header byte. With
    `marked`, the directory flags each item that has a header byte (formats that do not always
    carry one)."""
    ends, data, end = b'', b'', 0
    for value in variable:
        if value is None:
            ends += struct.pack('<H', end | 0x8000)
        else:
            end += len(value)
            data += value
            ends += struct.pack('<H', end)
    directory, items = b'', b''
    for ident, header, payload in tagged:
        offset = 4 * len(tagged) + len(items)
        directory += struct.pack('<HH', ident, offset | (0x4000 if marked and header is not None else 0))
        items += (bytes([header]) if header is not None else b'') + payload
    return struct.pack('<BBH', 0, 127 + len(variable), 4) + ends + data + directory + items


def column(ident, coltype):
    return {'Record': {'Identifier': ident, 'ColumnType': coltype, 'SpaceUsage': 0,
                       'CodePage': impacket_ese.CODEPAGE_UNICODE}}


COLUMNS = OrderedDict([
    (b'Var1', column(128, impacket_ese.JET_coltypBinary)),
    (b'Var2', column(129, impacket_ese.JET_coltypBinary)),
    (b'Url', column(256, impacket_ese.JET_coltypLongText)),
    (b'Blob', column(257, impacket_ese.JET_coltypLongBinary)),
    (b'Short', column(258, impacket_ese.JET_coltypBinary)),
])


class ReaderDatabase(FakeDatabase):
    """FakeDatabase whose records carry real ESE record bytes, converted by the vendored
    reader's own code."""

    def __init__(self, pages, flags_always=True):
        super().__init__(pages)
        self._ESENT_DB__DBHeader = {  # pylint: disable=invalid-name
            'Version': 0x620, 'FileFormatRevision': 17 if flags_always else 12,
            'PageSize': 32768 if flags_always else 8192}
        self._ESENT_DB__pageSize = self._ESENT_DB__DBHeader['PageSize']  # pylint: disable=invalid-name

    def openTable(self, name):  # pylint: disable=invalid-name
        cursor = super().openTable(name)
        if cursor is not None:
            cursor['TableData'] = {'Columns': COLUMNS}
        return cursor

    def _ESENT_DB__tagToRecord(self, cursor, entry):  # pylint: disable=invalid-name,arguments-differ
        return impacket_ese.ESENT_DB._ESENT_DB__tagToRecord(self, cursor, entry)  # pylint: disable=protected-access


TEXT = 'a long value in two pieces'.encode('utf-16le')  # 52 bytes


def text_tree():
    return tree((KEY, root(len(TEXT)), [(0, TEXT[:32]), (32, TEXT[32:])]))


class TaggedItemsTest(unittest.TestCase):
    def test_items_are_found_where_the_vendored_reader_finds_them(self):
        data = record_bytes([(256, SEPARATED, STORED), (257, 0x01, b'\x00\x01'), (258, 0x00, b'\x02')],
                            variable=[b'abc', None])
        self.assertEqual(ese_rows.tagged_items(data, True),
                         {256: (SEPARATED, STORED), 257: (0x01, b'\x00\x01'), 258: (0, b'\x02')})
        record = ReaderDatabase({})._ESENT_DB__tagToRecord(  # pylint: disable=protected-access
            {'TableData': {'Columns': COLUMNS}}, data)
        self.assertEqual((record[b'Var1'], record[b'Var2'], record[b'Blob'], record[b'Short']),
                         (b'616263', None, b'0001', b'02'))
        # The reader hands back the ID itself as the separated value.
        self.assertEqual(record[b'Url'], STORED.decode('utf-16le'))

    def test_the_header_byte_is_read_only_where_the_directory_marks_one(self):
        data = record_bytes([(256, SEPARATED, STORED), (258, None, b'\x02\x03')], marked=True)
        self.assertEqual(ese_rows.tagged_items(data, False), {256: (SEPARATED, STORED), 258: (0, b'\x02\x03')})

    def test_a_record_whose_variable_offsets_run_past_its_end_has_no_items(self):
        data = record_bytes([(256, SEPARATED, STORED)])
        self.assertEqual(ese_rows.tagged_items(data[:1] + bytes([200]) + data[2:], True), {})

    def test_a_record_with_no_tagged_columns_has_no_items(self):
        self.assertEqual(ese_rows.tagged_items(record_bytes([], variable=[b'abc']), True), {})


class SeparatedValueTest(unittest.TestCase):
    def walk(self, tags, index, **options):
        walk = ese_rows.TableRows(ReaderDatabase({1: FakePage(tags)}), 'Container_1', **options)
        with mock.patch.object(ese_rows, 'long_value_tree', return_value=index) as build:
            rows = list(walk)
        return walk, rows, build

    def test_a_separated_value_is_read_from_the_long_value_tree(self):
        tags = [tag(record_bytes([(256, SEPARATED, STORED), (257, 0x01, b'\x00\x01')])),
                tag(record_bytes([(256, SEPARATED, struct.pack('<I', 9))]))]
        walk, rows, build = self.walk(tags, text_tree())
        self.assertEqual(build.call_count, 1)
        self.assertEqual((rows[0][b'Url'], rows[0][b'Blob'], rows[1][b'Url']),
                         (TEXT.decode('utf-16le'), b'0001', None))
        self.assertEqual((walk.long_values, walk.long_values_blank), (1, 1))
        self.assertEqual(walk.summary(), 'Container_1: 1 value(s) stored apart from their record were read '
                                         'from the long value tree; 1 value(s) stored apart from their '
                                         'record could not be assembled and are blank (no root in the long '
                                         'value tree)')

    def test_a_binary_long_value_is_hex_as_the_reader_gives_binary(self):
        walk, rows, _build = self.walk([tag(record_bytes([(257, SEPARATED, STORED)]))], text_tree())
        self.assertEqual((rows[0][b'Blob'], walk.long_values), (hexlify(TEXT), 1))

    def test_only_the_named_columns_are_read_from_the_tree(self):
        tags = [tag(record_bytes([(256, SEPARATED, STORED)]))]
        walk, rows, build = self.walk(tags, text_tree(), long_value_columns={'Blob'})
        self.assertEqual((rows[0][b'Url'], walk.long_values, walk.summary()), (STORED.decode('utf-16le'), 0, ''))
        build.assert_not_called()
        walk, rows, _build = self.walk(tags, text_tree(), long_value_columns=lambda name: name == 'Url')
        self.assertEqual((rows[0][b'Url'], walk.long_values), (TEXT.decode('utf-16le'), 1))

    def test_an_item_ese_would_not_read_as_separated_keeps_the_readers_reading(self):
        multi = record_bytes([(257, SEPARATED | 0x08, STORED)])
        intrinsic = record_bytes([(257, 0x04, STORED)])  # fSeparated without fLongValue
        walk, rows, build = self.walk([tag(multi), tag(intrinsic)], text_tree())
        self.assertEqual((rows[0][b'Blob'], rows[1][b'Blob']), (hexlify(STORED), hexlify(STORED)))
        self.assertEqual((walk.long_values, walk.long_values_blank), (0, 0))
        build.assert_not_called()


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


class LongValueColumnsTest(unittest.TestCase):
    """Each artifact reads from the long value tree only the columns it reports."""

    def columns_passed(self, call):
        with mock.patch.object(ese_rows, 'TableRows', wraps=ese_rows.TableRows) as walk, \
                mock.patch.object(windowsWebcache, 'logfunc'), mock.patch.object(windowsSrum, 'logfunc'), \
                mock.patch.object(windowsThumbcache, 'logfunc'):
            call()
        return [c.kwargs.get('long_value_columns', 'not passed') for c in walk.call_args_list]

    def test_webcache_reads_the_container_names_and_the_url_and_filename(self):
        self.assertEqual(self.columns_passed(lambda: windowsWebcache._containers(two_pages())),  # pylint: disable=protected-access
                         [{'Name', 'Directory'}])
        self.assertEqual(self.columns_passed(lambda: windowsWebcache._read_container(  # pylint: disable=protected-access
            two_pages(), {'Container_7'}, 7, 'History', 'dir', lambda row, name, d: row, [], 'L', 'p')),
            [{'Url', 'Filename'}])

    def test_srum_reads_only_the_id_blob(self):
        with mock.patch.object(windowsSrum.impacket_ese, 'ESENT_DB', return_value=two_pages()):
            passed = self.columns_passed(lambda: windowsSrum._read_table(  # pylint: disable=protected-access
                'SRUDB.dat', 'T', lambda row, idmap: row, 'SRUM', 'p'))
        self.assertEqual(passed, [{'IdBlob'}, ()])

    def test_thumbcache_reads_the_three_properties_it_maps(self):
        with mock.patch.object(windowsThumbcache.impacket_ese, 'ESENT_DB', return_value=two_pages()):
            passed = self.columns_passed(lambda: windowsThumbcache._edb_map('Windows.edb'))  # pylint: disable=protected-access
        wanted = passed[0]
        self.assertEqual([wanted(n) for n in ('4428-System_ItemPathDisplay', '4424-System_ItemNameDisplay',
                                              '4442-System_ThumbnailCacheId', '4606-System_Search_AutoSummary',
                                              '4429-System_ItemPathDisplayNarrow')],
                         [True, True, True, False, False])


def inspect_source(module):
    return pathlib.Path(module.__file__).read_text(encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
