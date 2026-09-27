"""Pin the Spotlight store reader (scripts/macos_spotlight.py) and the Spotlight Store Files artifact.

Every store below is written by this test: a file header, a map page, the attribute tables as
property pages or as dbStr-N.map files, and record pages stored raw, as LZ4 blocks or with zlib.
No value comes from a real store. Expected values are literals.
"""
import fnmatch
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_spotlight as spotlight  # pylint: disable=wrong-import-position
from scripts.artifacts import macosSpotlightStore as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
PAGE = 4096
STORE = 'System/Volumes/Data/.Spotlight-V100/Store-V2/0A1B2C3D-0000-4000-8000-000000000001/'
RECORDED = '/System/Volumes/Data/.Spotlight-V100/Store-V2/0A1B2C3D-0000-4000-8000-000000000001/store.db'


def sv(value):
    """A Spotlight variable-size integer."""
    for extra in range(5):
        if value < 1 << (7 - extra + 8 * extra):
            first = ((0xFF << (8 - extra)) & 0xFF) | (value >> (8 * extra))
            return bytes([first]) + (value & ((1 << (8 * extra)) - 1)).to_bytes(extra, 'big')
    return b'\xff' + value.to_bytes(8, 'big')


def leb(value):
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def lz4_literals(data):
    """An LZ4 block of one literals-only sequence."""
    token = bytes([min(len(data), 15) << 4])
    extra = b''
    if len(data) >= 15:
        rest = len(data) - 15
        extra = b'\xff' * (rest // 255) + bytes([rest % 255])
    return token + extra + data


def page(kind, body, uncompressed=0):
    header = b'2pbd' + struct.pack('<4I', PAGE, 20 + len(body), kind, uncompressed)
    assert len(header) + len(body) <= PAGE
    return (header + body).ljust(PAGE, b'\x00')


def table_page(kind, entries):
    return page(kind, struct.pack('<IQ', 0, 0) + b''.join(entries))


def index_entry(index, indexes, padding=0):
    body = b'\x00' * padding + b''.join(struct.pack('<I', i) for i in indexes)
    return struct.pack('<I', index) + sv(len(body)) + body


# Attribute types: index -> (value type, property type, name). The property type's low bits mark
# a list (0x02) or a localized string (0x03).
TYPES = {
    1: (0x0B, 0x00, '_kMDItemFileName'),
    2: (0x0C, 0x00, 'kMDItemContentModificationDate'),
    3: (0x0C, 0x00, 'kMDItemContentCreationDate'),
    4: (0x0C, 0x00, 'kMDItemDateAdded'),
    5: (0x0C, 0x00, 'kMDItemLastUsedDate'),
    6: (0x0C, 0x02, 'kMDItemUsedDates'),
    7: (0x06, 0x08, 'kMDItemUseCount'),
    8: (0x0C, 0x02, 'kMDItemDownloadedDate'),
    9: (0x0B, 0x02, 'kMDItemWhereFroms'),
    10: (0x0C, 0x02, 'kMDItemUserSharedReceivedDate'),
    11: (0x0B, 0x02, 'kMDItemUserSharedReceivedSender'),
    12: (0x0B, 0x02, 'kMDItemUserSharedReceivedSenderHandle'),
    13: (0x0B, 0x02, 'kMDItemUserSharedReceivedTransport'),
    14: (0x0B, 0x00, 'kMDItemOriginSenderHandle'),
    15: (0x0F, 0x00, 'kMDItemOriginApplicationIdentifier'),
    16: (0x0F, 0x03, 'kMDItemKind'),
    17: (0x0F, 0x00, 'kMDItemContentType'),
    18: (0x07, 0x08, 'kMDItemLogicalSize'),
    19: (0x07, 0x0C, '_kMDItemOwnerUserID'),
    20: (0x00, 0x0C, '_kMDItemIsExtensionHidden'),
    21: (0x07, 0x4A, 'com_example_integer_list'),
    22: (0x08, 0x00, 'com_example_byte'),
    23: (0x08, 0x02, 'com_example_bytes'),
    24: (0x09, 0x00, 'com_example_float32'),
    25: (0x09, 0x02, 'com_example_float32_list'),
    26: (0x0A, 0x00, 'com_example_float64'),
    27: (0x0B, 0x03, 'com_example_localized_inline'),
    28: (0x0E, 0x00, 'com_example_binary'),
    29: (0x0F, 0x02, 'com_example_value_list'),
    30: (0x01, 0x00, '_kMDXXXX___DUMMY'),
}
VALUES = {1: 'public.folder', 2: 'com.apple.mail', 3: 'Folder\x16\x02', 4: 'Dossier\x16\x02fr', 5: 'public.jpeg',
          6: 'JPEG image\x16\x02', 7: 'Image JPEG\x16\x02fr', 8: 'alpha', 9: 'beta'}
LISTS = {1: [8, 9]}
LOCALIZED = {1: [3, 4], 2: [6, 7]}


def attribute(step, payload):
    return sv(step) + payload


def record(identifier, parent, updated, attributes, flags=0x42, item_identifier=0):
    """A record: size, then identifier, flags, item identifier, parent and update time, then the
    attributes as (type index, encoded value) pairs in ascending type order."""
    body = sv(identifier) + bytes([flags]) + sv(item_identifier) + sv(parent) + sv(updated)
    previous = 0
    for index, payload in attributes:
        body += sv(index - previous) + payload
        previous = index
    return struct.pack('<I', len(body)) + body


def string(text):
    data = text.encode() + b'\x00'
    return sv(len(data)) + data


def strings(*texts):
    data = b''.join(t.encode() + b'\x00' for t in texts)
    return sv(len(data)) + data


def date(seconds):
    return struct.pack('<d', seconds)


def dates(*values):
    data = b''.join(struct.pack('<d', v) for v in values)
    return sv(len(data)) + data


def file_record(identifier, parent, name, updated=1766644919000000, extra=()):
    return record(identifier, parent, updated, [
        (1, string(name)), (2, date(787948800.5)), (3, date(787900000.0)), (4, date(787950000.0)),
        *extra, (16, sv(1)), (17, sv(1)), (19, sv(501))])


def write_store(path, records_pages, recorded=RECORDED, tables='pages', types=None):
    """store.db at path, with the attribute tables as property pages or as dbStr files beside it."""
    types = TYPES if types is None else types
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pages = [b'', b'']
    if tables == 'pages':
        pages.append(table_page(0x11, [struct.pack('<IBB', i, *t[:2]) + t[2].encode() + b'\x00' for i, t in types.items()]))
        pages.append(table_page(0x21, [struct.pack('<I', i) + v.encode() + b'\x00' for i, v in VALUES.items()]))
        pages.append(table_page(0x81, [index_entry(i, v, padding=1) for i, v in LISTS.items()]))
        pages.append(table_page(0x81, [index_entry(i, v) for i, v in LOCALIZED.items()]))
        blocks = (2, 3, 0, 4, 5)
    else:
        folder = os.path.dirname(path)
        write_dbstr(folder, 1, [bytes(t[:2]) + t[2].encode() + b'\x00' for t in (types[i] for i in sorted(types))])
        write_dbstr(folder, 2, [VALUES[i].encode() + b'\x00' for i in sorted(VALUES)])
        write_dbstr(folder, 4, [sv(8) + b''.join(struct.pack('<I', i) for i in LISTS[k]) for k in sorted(LISTS)])
        write_dbstr(folder, 5, [sv(9) + b'\x00' + b''.join(struct.pack('<I', i) for i in LOCALIZED[k])
                                for k in sorted(LOCALIZED)])
        blocks = (0, 0, 0, 0, 0)
    first_record = len(pages)
    pages.extend(records_pages)
    count = len(records_pages)
    pages[1] = (b'2mbd' + struct.pack('<4I', PAGE, count, 0, 0)
                + b''.join(struct.pack('<QII', 0, first_record + i, 0) for i in range(count))).ljust(PAGE, b'\x00')
    header = bytearray(PAGE)
    header[0:4] = b'8tsd'
    struct.pack_into('<I', header, 4, 0x20901)
    struct.pack_into('<8I', header, 36, PAGE, PAGE, PAGE, *blocks)
    header[324:324 + len(recorded)] = recorded.encode()
    pages[0] = bytes(header)
    with open(path, 'wb') as handle:
        handle.write(b''.join(pages))


def write_dbstr(folder, number, bodies):
    data, offsets = bytearray(), [0]
    for body in bodies:
        offsets.append(len(data))
        data += leb(len(body)) + body
    header = b'\x00PataD\x00\x00' + struct.pack('<3I', 0, 0, 0) + struct.pack('<3I', len(data), 0, len(offsets))
    base = os.path.join(folder, f'dbStr-{number}.map.')
    with open(base + 'header', 'wb') as handle:
        handle.write(header.ljust(56, b'\x00'))
    with open(base + 'offsets', 'wb') as handle:
        handle.write(struct.pack(f'<{len(offsets)}I', *offsets))
    with open(base + 'data', 'wb') as handle:
        handle.write(bytes(data))


def raw_page(*records):
    return page(0x09, b''.join(records))


def lz4_page(*records):
    data = b''.join(records)
    half = len(data) // 2
    blocks = (b'bv41' + struct.pack('<II', half, len(lz4_literals(data[:half]))) + lz4_literals(data[:half])
              + b'bv4-' + struct.pack('<I', len(data) - half) + data[half:] + b'bv4$')
    return page(0x1009, blocks, uncompressed=20 + len(data))


def zlib_page(*records):
    data = b''.join(records)
    return page(0x09, zlib.compress(data), uncompressed=20 + len(data))


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_integers(self):
        cases = {b'\x05': 5, b'\x81\x01': 0x101, b'\xc0\x01\x00': 0x100, b'\xe1\x02\x03\x04': 0x1020304,
                 b'\xf2\x01\x02\x03\x04': 0x201020304, b'\xff' + bytes(range(1, 9)): 0x0102030405060708}
        for data, value in cases.items():
            self.assertEqual(spotlight.varint(data + b'\x99', 0), (value, len(data)), data)
        for value in (0, 127, 128, 16383, 16384, 2 ** 21, 2 ** 28, 2 ** 35, 2 ** 64 - 1):
            self.assertEqual(spotlight.varint(sv(value), 0), (value, len(sv(value))), value)
        self.assertEqual(spotlight.leb128(b'\x81\x01', 0), (129, 2))
        with self.assertRaises(spotlight.StoreError):
            spotlight.varint(b'\xc0\x01', 0)

    def test_lz4(self):
        # Literals 'abcd', then a match of 8 bytes at distance 4.
        self.assertEqual(spotlight.lz4_block(b'\x44abcd\x04\x00', 12), b'abcdabcdabcd')
        # The second block copies 6 bytes from the end of the first.
        self.assertEqual(spotlight.lz4_block(b'\x02\x06\x00', 6, prefix=b'xyzuvw'), b'xyzuvw')
        with self.assertRaises(spotlight.StoreError):
            spotlight.lz4_block(b'\x02\x06\x00', 6)
        stream = b'bv41' + struct.pack('<II', 5, 6) + lz4_literals(b'hello') + b'bv4-' + struct.pack('<I', 3) + b'abc' + b'bv4$'
        self.assertEqual(spotlight.lz4_stream(stream), b'helloabc')
        # A compressed block may copy from the block before it.
        chained = (b'bv41' + struct.pack('<II', 5, 6) + lz4_literals(b'hello') + b'bv41' + struct.pack('<II', 5, 3) + b'\x01\x05\x00'
                   + b'bv4$')
        self.assertEqual(spotlight.lz4_stream(chained), b'hellohello')
        with self.assertRaises(spotlight.StoreError):
            spotlight.lz4_stream(stream[:-4])

    def test_values_from_pages(self):
        attributes = [
            (1, string('a.jpg')), (5, date(788000000.25)), (6, dates(787968000.0, 788054400.0)), (7, sv(3)),
            (9, strings('https://example.com/a.jpg', '')), (18, sv(70000)), (20, sv(1)),
            # A list of integers is prefixed by its size as 64-bit integers: three values, 24.
            (21, sv(24) + sv(5) + sv(300) + sv(2 ** 33)),
            (22, b'\x07'), (23, sv(3) + b'\x01\x02\x03'), (24, struct.pack('<f', 1.5)),
            (25, sv(8) + struct.pack('<ff', 0.5, 2.0)), (26, struct.pack('<d', 3.25)),
            # A localized string is its first language version that is not empty.
            (27, strings('', '\x16\x02en', 'hola\x16\x02es')), (28, sv(2) + b'\xde\xad'), (29, sv(1))]
        path = os.path.join(self.root, STORE, 'store.db')
        write_store(path, [raw_page(record(40, 2, 1766644919000000, attributes, item_identifier=7))])
        store = spotlight.Store(path)
        (item,) = list(store.items())
        self.assertEqual((item.identifier, item.flags, item.item_identifier, item.parent, item.updated, item.complete),
                         (40, 0x42, 7, 2, 1766644919000000, True))
        self.assertEqual(item.attributes, {
            '_kMDItemFileName': 'a.jpg', 'kMDItemLastUsedDate': 788000000.25,
            'kMDItemUsedDates': [787968000.0, 788054400.0], 'kMDItemUseCount': 3,
            'kMDItemWhereFroms': ['https://example.com/a.jpg', ''], 'kMDItemLogicalSize': 70000,
            '_kMDItemIsExtensionHidden': 1, 'com_example_integer_list': [5, 300, 2 ** 33], 'com_example_byte': 7,
            'com_example_bytes': [1, 2, 3], 'com_example_float32': 1.5, 'com_example_float32_list': [0.5, 2.0],
            'com_example_float64': 3.25, 'com_example_localized_inline': 'hola', 'com_example_binary': b'\xde\xad',
            'com_example_value_list': ['alpha', 'beta']})
        self.assertEqual(store.recorded_path, RECORDED)
        self.assertEqual((store.incomplete, store.unreadable_pages), (0, 0))

    def test_tables_from_dbstr_files(self):
        # A type name of 200 bytes makes its dbStr value longer than 127 bytes: a two-byte size.
        types = dict(TYPES)
        long_name = '_kMDItemStateInfo_' + 'x' * 182
        types[31] = (0x06, 0x00, long_name)
        path = os.path.join(self.root, STORE, 'store.db')
        write_store(path, [zlib_page(record(41, 2, 5, [(1, string('b.txt')), (16, sv(2)), (17, sv(5)), (31, sv(9))]))],
                    tables='dbstr', types=types)
        (item,) = list(spotlight.Store(path).items())
        self.assertEqual(item.attributes, {'_kMDItemFileName': 'b.txt', 'kMDItemKind': 'JPEG image',
                                           'kMDItemContentType': 'public.jpeg', long_name: 9})
        self.assertTrue(item.complete)

    def test_record_pages_and_unreadable_values(self):
        path = os.path.join(self.root, STORE, 'store.db')
        # The second page is LZ4, the third claims compression it does not carry, and the last
        # record holds a value type this reader does not decode.
        bad = page(0x09, b'\x10\x11', uncompressed=100)
        write_store(path, [raw_page(record(50, 2, 1, [(1, string('one'))])), lz4_page(record(51, 2, 1, [(1, string('two'))]),
                                                                                  record(52, 2, 1, [(1, string('three'))])),
                           bad, raw_page(record(53, 2, 1, [(1, string('four')), (30, b'\x00')]))])
        store = spotlight.Store(path)
        items = list(store.items())
        self.assertEqual([(i.identifier, i.attributes.get('_kMDItemFileName'), i.complete) for i in items],
                         [(50, 'one', True), (51, 'two', True), (52, 'three', True), (53, 'four', False)])
        self.assertEqual((store.unreadable_pages, store.incomplete), (1, 1))

    def test_not_a_store(self):
        path = os.path.join(self.root, 'store.db')
        with open(path, 'wb') as handle:
            handle.write(bytes(36864))
        with self.assertRaises(spotlight.StoreError):
            spotlight.Store(path)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        for module in (artifact, sys.modules['scripts.macos_plists']):
            patcher = patch.object(module, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_artifact(self):
        return artifact.macosSpotlightStoreFiles.__wrapped__(Context(self.root, walk(self.root)))

    def test_files(self):
        used = (5, date(788000000.0)), (6, dates(787968000.0, 788054400.0)), (7, sv(2))
        # An empty entry of a list is left out of its cell.
        # Of a list of downloaded dates only the first is reported.
        received = ((8, dates(787990000.0, 788100000.0)), (9, strings('https://example.com/a.jpg', '', 'https://example.com/')),
                    (10, dates(787990000.0)), (11, strings('Pat')), (12, strings('+15555550100')),
                    (13, strings('com.apple.messages')), (14, string('+15555550100')), (15, sv(2)))
        older = [raw_page(
            file_record(100, 2, 'Users'), file_record(101, 100, 'pat'),
            file_record(102, 101, 'a.jpg', extra=used + received),
            # Its parent has no record in the store.
            file_record(103, 999, 'orphan.txt', updated=5),
            # A record with no file name is not reported.
            record(1, 0, 5, [(20, sv(1))]))]
        newer = [raw_page(
            file_record(100, 2, 'Users'), file_record(101, 100, 'pat'),
            file_record(102, 101, 'a.jpg', extra=used + received),
            # Updated since the older copy was written.
            file_record(103, 999, 'orphan.txt', updated=6))]
        write_store(os.path.join(self.root, STORE, 'store.db'), older)
        # The newer copy names no table page: its tables come from the dbStr files beside it.
        write_store(os.path.join(self.root, STORE, '.store.db'), newer, tables='dbstr')
        # A zero-filled copy is not a store.
        backup = os.path.join(self.root, 'Volumes/.timemachine/X/2025.backup/.Spotlight-V100/Store-V2/Y/store.db')
        os.makedirs(os.path.dirname(backup))
        with open(backup, 'wb') as handle:
            handle.write(bytes(36864))
        # Its byte-identical copy under System/Volumes/Data is not read again.
        copy = os.path.join(self.root, 'System/Volumes/Data', os.path.relpath(backup, self.root))
        os.makedirs(os.path.dirname(copy))
        shutil.copyfile(backup, copy)
        headers, rows, source = self.run_artifact()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers], [
            'Content Modified (UTC)', 'Content Created (UTC)', 'Date Added (UTC)', 'Last Used (UTC)', 'Used Dates (UTC)',
            'Use Count (as stored)', 'Downloaded (UTC)', 'Where From', 'Received Date (UTC)', 'Received Sender (as stored)',
            'Received Sender Handle (as stored)', 'Received Transport (as stored)', 'Origin Sender (as stored)',
            'Origin Application (as stored)', 'Record Updated (UTC)', 'Name', 'Path', 'Kind', 'Content Type',
            'Logical Size (as stored)', 'Owner UID (as stored)', 'File ID', 'Parent File ID', 'Source File'])
        modified = datetime(2025, 12, 20, 18, 40, 0, 500000, tzinfo=UTC)
        created = datetime(2025, 12, 20, 5, 6, 40, tzinfo=UTC)
        added = datetime(2025, 12, 20, 19, 0, tzinfo=UTC)
        updated = datetime(2025, 12, 25, 6, 41, 59, tzinfo=UTC)
        both = f'{STORE}store.db\n{STORE}.store.db'
        blank = ('',) * 11
        self.assertEqual(rows, [
            # Sorted by content modified, then path: a path whose chain stops at an unknown parent
            # sorts first. The record updated between the two copies is a row per copy.
            (modified, created, added, *blank, datetime(1970, 1, 1, 0, 0, 0, 5, tzinfo=UTC), 'orphan.txt',
             '(file ID 999)/orphan.txt', 'Folder', 'public.folder', '', 501, 103, 999, STORE + 'store.db'),
            (modified, created, added, *blank, datetime(1970, 1, 1, 0, 0, 0, 6, tzinfo=UTC), 'orphan.txt',
             '(file ID 999)/orphan.txt', 'Folder', 'public.folder', '', 501, 103, 999, STORE + '.store.db'),
            (modified, created, added, *blank, updated, 'Users', '/System/Volumes/Data/Users', 'Folder', 'public.folder', '',
             501, 100, 2, both),
            (modified, created, added, *blank, updated, 'pat', '/System/Volumes/Data/Users/pat', 'Folder', 'public.folder',
             '', 501, 101, 100, both),
            (modified, created, added, datetime(2025, 12, 21, 8, 53, 20, tzinfo=UTC),
             '2025-12-21 00:00:00\n2025-12-22 00:00:00', 2, datetime(2025, 12, 21, 6, 6, 40, tzinfo=UTC),
             'https://example.com/a.jpg\nhttps://example.com/', '2025-12-21 06:06:40', 'Pat', '+15555550100',
             'com.apple.messages', '+15555550100', 'com.apple.mail', updated, 'a.jpg',
             '/System/Volumes/Data/Users/pat/a.jpg', 'Folder', 'public.folder', '', 501, 102, 101, both)])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, STORE, n) for n in ('store.db', '.store.db')))
        backup_relative = os.path.relpath(backup, self.root)
        self.assertEqual(sorted(self.logged), sorted([
            f'Spotlight Store Files: {backup_relative} not read: not a Spotlight store database',
            'Spotlight Store Files: 1 byte-identical copy(ies) under System/Volumes/Data not read again',
            f'Spotlight Store Files: {STORE}store.db: 1 record(s) with no file name not reported']))

    def test_one_identifier_held_twice(self):
        # Two records of one copy share an identifier: each row's path ends with its own name, and
        # the folder that identifier names for the records below it is the later updated one's.
        write_store(os.path.join(self.root, STORE, 'store.db'), [raw_page(
            file_record(100, 2, 'old folder', updated=5), file_record(100, 2, 'new folder', updated=9),
            file_record(101, 100, 'a.txt'))])
        _headers, rows, _source = self.run_artifact()
        self.assertEqual(sorted((row[15], row[16]) for row in rows), [
            ('a.txt', '/System/Volumes/Data/new folder/a.txt'), ('new folder', '/System/Volumes/Data/new folder'),
            ('old folder', '/System/Volumes/Data/old folder')])

    def test_update_time_out_of_range(self):
        # An update time too large for a date leaves Record Updated blank rather than stopping the run.
        write_store(os.path.join(self.root, STORE, 'store.db'), [raw_page(file_record(100, 2, 'Users', updated=2 ** 60))])
        _headers, rows, _source = self.run_artifact()
        self.assertEqual([(row[14], row[15]) for row in rows], [('', 'Users')])

    def test_unreadable_page_and_undecoded_value(self):
        # A page that claims compression it does not carry is skipped, and a record whose value
        # cannot be decoded still gives a row with the attributes read before it; both are logged.
        bad = page(0x09, b'\x10\x11', uncompressed=100)
        write_store(os.path.join(self.root, STORE, 'store.db'),
                    [raw_page(file_record(100, 2, 'Users')), bad, raw_page(record(101, 100, 7, [(1, string('pat')), (31, b'\x00')]))])
        _headers, rows, _source = self.run_artifact()
        self.assertEqual([(row[15], row[16], row[21], row[22]) for row in rows],
                         [('Users', '/System/Volumes/Data/Users', 100, 2), ('pat', '/System/Volumes/Data/Users/pat', 101, 100)])
        self.assertEqual(rows[1][:15], ('',) * 14 + (datetime(1970, 1, 1, 0, 0, 0, 7, tzinfo=UTC),))
        self.assertEqual(self.logged, [f'Spotlight Store Files: {STORE}store.db: 1 record page(s) not read, '
                                       '1 record(s) not fully decoded'])

    def test_declared_paths(self):
        paths = artifact.__artifacts_v2__['macosSpotlightStoreFiles']['paths']
        for member in (STORE + 'store.db', STORE + '.store.db', STORE + 'dbStr-1.map.data', STORE + 'dbStr-4.map.offsets',
                       'Volumes/bkp/.Spotlight-V100/Store-V2/U/store.db'):
            self.assertTrue(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)
        for member in ('Users/pat/Library/Metadata/CoreSpotlight/index.spotlightV3/store.db', STORE + 'live.0.indexPostings'):
            self.assertFalse(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)


if __name__ == '__main__':
    unittest.main()
