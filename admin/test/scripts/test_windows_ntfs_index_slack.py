"""Pin the NTFS $I30 Index Slack artifacts (scripts/artifacts/windowsNtfsIndexSlack.py).

Index blocks are built here in the layout the artifacts read: an INDX header with its update sequence
array, an entry list that ends in an end entry, and whatever the test leaves in the space after it. The
names, times and numbers are made up.
"""
import datetime
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsNtfsIndexSlack as ix
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
BLOCK = 4096
DIRECTORY = 77 | 4 << 48                         # the reference every entry of the directory names
T1 = datetime.datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)
T2 = datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC)


def ticks(moment):
    return int((moment - datetime.datetime(1601, 1, 1, tzinfo=UTC)).total_seconds()) * 10_000_000


def entry(record, sequence, name, modified=T1, size=100, space=1, parent=DIRECTORY, sub_node=False):
    """An index entry whose key is a file name, padded to 8 bytes."""
    text = name.encode('utf-16-le')
    key = struct.pack('<QqqqqqqIIBB', parent, ticks(T1), ticks(modified), ticks(T1), ticks(T1), 4096, size,
                      0x20, 0, len(name), space) + text
    length = (16 + len(key) + 7) & ~7
    if sub_node:
        length += 8
    return struct.pack('<QHHHH', record | sequence << 48, length, len(key), 1 if sub_node else 0,
                       0).ljust(16, b'\0') + key.ljust(length - 16, b'\0')


END = struct.pack('<QHHHH', 0, 16, 0, 2, 0)


def block(live, slack=b'', gap=0, protect=True):
    """One index block: the live entries and an end entry in its entry list, then ``gap`` zero bytes and
    whatever is left in the slack."""
    entries = b''.join(live) + END
    body = bytearray(BLOCK)
    body[0:4] = b'INDX'
    struct.pack_into('<III', body, 0x18, 0x28, 0x28 + len(entries), BLOCK - 0x18)
    body[0x40:0x40 + len(entries)] = entries
    start = 0x40 + len(entries) + gap
    body[start:start + len(slack)] = slack
    if protect:
        struct.pack_into('<HH', body, 4, 0x28, 9)
        body[0x28:0x2A] = b'\x05\x00'
        for sector in range(1, 9):
            end = sector * 512
            body[0x28 + 2 * sector:0x2A + 2 * sector] = body[end - 2:end]
            body[end - 2:end] = b'\x05\x00'
    return bytes(body)


def names(entries):
    return [item[-1] for item in entries]


class Reading(unittest.TestCase):
    def test_name_entry(self):
        data = entry(100, 3, 'report.docx', modified=T2, size=555)
        got = ix.name_entry(data, 0, len(data))
        self.assertEqual(got, (len(data), 100 | 3 << 48, DIRECTORY, ticks(T1), ticks(T2), ticks(T1), ticks(T1),
                               4096, 555, 0x20, 1, 'report.docx'))
        with_node = entry(100, 3, 'report.docx', sub_node=True)
        self.assertEqual(ix.name_entry(with_node, 0, len(with_node))[0], len(data) + 8)

    def test_data_that_is_not_a_name_entry(self):
        data = entry(100, 3, 'report.docx')
        self.assertIsNone(ix.name_entry(data, 0, len(data) - 8))                       # does not lie whole
        self.assertIsNone(ix.name_entry(data[:80], 0, 80))                             # too short to hold one
        self.assertIsNone(ix.name_entry(data[:10] + struct.pack('<H', 70) + data[12:], 0, len(data)))
        self.assertIsNone(ix.name_entry(data[:81] + b'\x04' + data[82:], 0, len(data)))   # name space 4
        self.assertIsNone(ix.name_entry(data[:80] + b'\x00' + data[81:], 0, len(data)))   # no characters
        nameless = entry(100, 3, '')
        self.assertIsNone(ix.name_entry(nameless, 0, len(nameless)))                   # a name of no characters
        longer = data[:8] + struct.pack('<H', len(data) + 16) + data[10:] + bytes(16)
        self.assertIsNone(ix.name_entry(longer, 0, len(longer)))                       # a length it cannot have

    def test_fix_up(self):
        good = block([entry(1, 1, 'a')])
        fixed = ix.fix_up(good)
        self.assertEqual(fixed[510:512], good[0x2A:0x2C])
        self.assertIsNone(ix.fix_up(good[:510] + b'\x99\x99' + good[512:]))
        self.assertIsNone(ix.fix_up(good[:4] + struct.pack('<HH', 4090, 9) + good[8:]))

    def test_block_size(self):
        one = block([entry(1, 1, 'a')])
        self.assertEqual(ix.block_size(one + bytes(BLOCK) + one), 4096)
        self.assertIsNone(ix.block_size(bytes(BLOCK)))
        self.assertEqual(ix.block_size(bytes(BLOCK) + one), 4096)
        self.assertEqual(ix.block_size(one + b'JUNK' + bytes(BLOCK - 4)), 4096)
        self.assertIsNone(ix.block_size(one[:100]))
        self.assertIsNone(ix.block_size(one + bytes(512)))                             # not whole blocks
        odd = one[:0x20] + struct.pack('<I', 3000) + one[0x24:]
        self.assertIsNone(ix.block_size(odd))                                          # not a power of two
        self.assertIsNone(ix.block_size(bytes(512) + one + bytes(BLOCK - 512)))       # not at a block start
        three = one[:0x20] + struct.pack('<I', 3 * BLOCK - 0x18) + one[0x24:] + bytes(2 * BLOCK)
        self.assertIsNone(ix.block_size(three))                                        # divides, no power of two

    def test_read_index(self):
        live = [entry(1, 1, 'kept.txt'), entry(2, 1, 'also kept.txt')]
        left = entry(9, 2, 'removed.txt') + entry(8, 2, 'second removed.txt')
        counts = {}
        got_live, got_slack = ix.read_index(block(live, left, gap=24) + bytes(BLOCK) + block([entry(3, 1, 'c')]),
                                            counts)
        self.assertEqual(names(got_live), ['kept.txt', 'also kept.txt', 'c'])
        first = 0x40 + len(b''.join(live)) + 16 + 24
        self.assertEqual([(offset, item[-1]) for offset, item in got_slack],
                         [(first, 'removed.txt'), (first + len(entry(9, 2, 'removed.txt')), 'second removed.txt')])
        self.assertEqual(counts, {'index blocks that do not start INDX, not read': 1})

    def test_the_entry_list_ends_at_its_end_entry(self):
        got_live, _ = ix.read_index(block([entry(1, 1, 'listed.txt'), END, entry(2, 1, 'after the end.txt')]), {})
        self.assertEqual(names(got_live), ['listed.txt'])

    def test_slack_in_a_later_block_is_placed_in_the_allocation(self):
        live = [entry(1, 1, 'kept.txt')]
        data = block(live) + block(live, entry(9, 2, 'in the second block.txt'), gap=8)
        _, slack = ix.read_index(data, {})
        self.assertEqual([(offset, item[-1]) for offset, item in slack],
                         [(BLOCK + 0x40 + len(live[0]) + 16 + 8, 'in the second block.txt')])

    def test_slack_entry_over_a_sector_end_is_read_fixed_up(self):
        live = [entry(1, 1, 'kept.txt')]
        used = 0x40 + len(live[0]) + 16
        name = 'a name that lies over the end of the first sector.txt'
        _, slack = ix.read_index(block(live, entry(9, 2, name), gap=440 - used), {})
        self.assertEqual([(offset, item[-1]) for offset, item in slack], [(440, name)])

    def test_blocks_that_are_not_read(self):
        counts = {}
        bad = block([entry(1, 1, 'a')], entry(9, 2, 'lost.txt'), gap=8)
        bad = bad[:510] + b'\x99\x99' + bad[512:]
        self.assertEqual(ix.read_index(bad + block([entry(2, 1, 'b')]), counts)[1], [])
        self.assertEqual(counts, {'index blocks whose update sequence does not check, not read': 1})
        counts = {}
        self.assertEqual(ix.read_index(b'not an index at all' + bytes(BLOCK - 19), counts), ([], []))
        self.assertEqual(counts, {'index allocations with no index block, not read': 1})


def attribute(kind, value, name=''):
    """A resident attribute, named or not, padded to 8 bytes."""
    text = name.encode('utf-16-le')
    start = (24 + len(text) + 7) & ~7
    length = (start + len(value) + 7) & ~7
    head = struct.pack('<IIBBHHHIH', kind, length, 0, len(name), 24, 0, 0, len(value), start).ljust(24, b'\0')
    return (head + text).ljust(start, b'\0') + value.ljust(length - start, b'\0')


def index_root(entries):
    """An $INDEX_ROOT value: its 16-byte header, then an index header and the entry list."""
    listed = b''.join(entries) + END
    return struct.pack('<IIIB3x', 0x30, 1, BLOCK, 1) + struct.pack('<IIII', 16, 16 + len(listed), 16 + len(listed), 0) \
        + listed


def mft_record(number, sequence, attributes, in_use=True, directory=True, base=0):
    """One 1024-byte MFT record with its update sequence array set."""
    body = b''.join(attributes) + struct.pack('<II', 0xFFFFFFFF, 0)
    flags = (1 if in_use else 0) | (2 if directory else 0)
    record = bytearray(struct.pack('<4sHHqHHHHIIQHHI', b'FILE', 48, 3, 0, sequence, 1, 56, flags, 56 + len(body),
                                   1024, base, 0, 0, number).ljust(56, b'\0') + body)
    record.extend(bytes(1024 - len(record)))
    record[48:50] = b'\x03\x00'
    for sector in (1, 2):
        end = sector * 512
        record[48 + 2 * sector:50 + 2 * sector] = record[end - 2:end]
        record[end - 2:end] = b'\x03\x00'
    return bytes(record)


def name_value(parent, name):
    text = name.encode('utf-16-le')
    return struct.pack('<QqqqqqqIIBB', parent, 1, 2, 3, 4, 0, 0, 0, 0, len(name), 1) + text


class Table(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, '$MFT')
        records = [
            mft_record(0, 1, [attribute(0x30, name_value(5 | 5 << 48, '$MFT'))], directory=False),
            mft_record(1, 4, [attribute(0x90, index_root([entry(20, 1, 'in the root.txt')]), '$I30')]),
            mft_record(2, 4, [attribute(0x90, index_root([entry(21, 1, 'not this index')]), '$SDH')]),
            mft_record(3, 7, [attribute(0x30, name_value(1 | 4 << 48, 'big directory'))]),
            mft_record(4, 1, [attribute(0x90, index_root([entry(22, 1, 'root in an extension.txt')]), '$I30')],
                       base=3 | 7 << 48),
            mft_record(5, 2, [attribute(0x30, name_value(1 | 4 << 48, 'kept.txt'))], directory=False),
            mft_record(6, 3, [attribute(0x30, name_value(1 | 4 << 48, 'deleted.txt'))], in_use=False,
                       directory=False),
            bytes(1024),
            mft_record(8, 0, [attribute(0x30, name_value(1 | 4 << 48, 'wrapped.txt'))], in_use=False,
                       directory=False),
            b'BAAD' + mft_record(9, 4, [attribute(0x90, index_root([entry(23, 1, 'x')]), '$I30')])[4:],
            mft_record(10, 2, [attribute(0x30, name_value(1 | 4 << 48, 'directory with old extensions'))]),
            mft_record(11, 1, [attribute(0x90, index_root([entry(24, 1, 'earlier use.txt')]), '$I30')],
                       base=10 | 1 << 48),
            mft_record(12, 1, [attribute(0x90, index_root([entry(25, 1, 'freed.txt')]), '$I30')],
                       base=10 | 2 << 48, in_use=False)]
        with open(self.path, 'wb') as handle:
            handle.write(b''.join(records))
        self.table = ix.MftTable(self.path)

    def test_root_entries(self):
        self.assertEqual(names(self.table.root_entries(1)), ['in the root.txt'])
        self.assertIsNone(self.table.root_entries(2))                    # an index of another name
        self.assertEqual(names(self.table.root_entries(3)), ['root in an extension.txt'])
        self.assertIsNone(self.table.root_entries(5))                    # a file
        self.assertIsNone(self.table.root_entries(7))                    # not a record
        self.assertIsNone(self.table.root_entries(9))                    # a record that does not start FILE
        self.assertIsNone(self.table.root_entries(99))                   # past the end of the $MFT
        self.assertIsNone(self.table.root_entries(10))                   # only a stale and a freed extension

    def test_state_now(self):
        state = self.table.state_now
        self.assertEqual(state(5 | 2 << 48, 1 | 4 << 48, 'kept.txt'), 'Same sequence, in use, with this name')
        self.assertEqual(state(5 | 2 << 48, 1 | 9 << 48, 'kept.txt'), 'Same sequence, in use, with this name')
        self.assertEqual(state(5 | 2 << 48, 1 | 4 << 48, 'old name.txt'), 'Same sequence, in use')
        self.assertEqual(state(5 | 2 << 48, 8 | 4 << 48, 'kept.txt'), 'Same sequence, in use')
        self.assertEqual(state(6 | 3 << 48, 1 | 4 << 48, 'deleted.txt'), 'Same sequence, not in use')
        self.assertEqual(state(6 | 2 << 48, 1 | 4 << 48, 'deleted.txt'), 'Sequence one higher, not in use')
        self.assertEqual(state(5 | 1 << 48, 1 | 4 << 48, 'kept.txt'), 'Another sequence')   # one higher, in use
        self.assertEqual(state(5 | 9 << 48, 1 | 4 << 48, 'kept.txt'), 'Another sequence')
        self.assertEqual(state(7 | 1 << 48, 1 | 4 << 48, 'x'), 'No record')
        self.assertEqual(state(99 | 1 << 48, 1 | 4 << 48, 'x'), 'No record')
        self.assertEqual(state(8 | 0xFFFF << 48, 1 | 4 << 48, 'wrapped.txt'), 'Sequence one higher, not in use')


def read(live, slack):
    counts = {}
    got_live, got_slack = ix.read_index(block(live, b''.join(slack), gap=8), counts)
    return ix.classify(got_live, got_slack, counts) + (counts,)


class Sorting(unittest.TestCase):
    def test_classes(self):
        live = [entry(1, 1, 'kept.txt', modified=T2, size=900), entry(2, 1, 'renamed to this.txt')]
        unlisted, copies, counts = read(live, [
            entry(1, 1, 'kept.txt', modified=T2, size=900),            # identical to the live entry
            entry(1, 1, 'kept.txt', modified=T1, size=100),            # the same name, other values
            entry(2, 1, 'name it had.txt'),                            # the same file, another name
            entry(9, 2, 'gone.txt'),                                   # no entry of that file now
            entry(7, 5, 'renamed to this.txt', size=5),                # that name, of another file
            entry(9, 2, 'gone.txt'),                                   # found a second time
            entry(8, 2, 'elsewhere.txt', parent=500 | 1 << 48)])       # an entry of another directory
        self.assertEqual([(item[1][-1], item[2]) for item in unlisted],
                         [('name it had.txt', 'File, under another name'), ('gone.txt', 'No'),
                          ('renamed to this.txt', 'Name, under another file reference')])
        self.assertEqual([(item[1][-1], item[1][4], item[2][4], item[2][8]) for item in copies],
                         [('kept.txt', ticks(T1), ticks(T2), 900)])
        self.assertEqual(counts, {
            'entries in slack identical to an entry of the index, not reported': 1,
            'entries in slack found more than once in an index, reported once': 1,
            'entries in slack that name another directory as parent, not reported': 1})

    def test_overwritten_reference(self):
        tail = 0x0000000200000010
        lost = struct.pack('<Q', tail) + entry(9, 2, 'reference lost.txt')[8:]
        still = struct.pack('<Q', tail) + entry(1, 1, 'kept.txt', modified=T1)[8:]
        unlisted, copies, counts = read([entry(1, 1, 'kept.txt', modified=T2)], [lost, still])
        self.assertEqual([(item[1][1], item[1][-1]) for item in unlisted], [(tail, 'reference lost.txt')])
        self.assertEqual(copies, [])
        self.assertEqual(counts, {'entries in slack with an overwritten file reference whose name is an '
                                  'entry of the index, not reported': 1})

    def test_index_with_no_live_entry_takes_what_it_finds(self):
        unlisted, _, counts = read([], [entry(9, 2, 'a.txt', parent=500 | 1 << 48)])
        self.assertEqual(names([item[1] for item in unlisted]), ['a.txt'])
        self.assertEqual(counts, {})


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def run_artifact(self, function, files, states=None, roots=None):
        """Run an artifact over {evidence member: bytes}; a member is staged under a name with no colon."""
        infos, found = {}, []
        for member, data in files.items():
            path = os.path.join(self.folder.name, member.replace(':', '_'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(data)
            infos[path] = mock.Mock(source_path=member)
            found.append(path)
        rows = []
        result = mock.Mock()
        result.add_row.side_effect = rows.append
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_seeker.return_value = mock.Mock(file_infos=infos)
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        context.create_artifact_result.return_value = result

        class FakeTable(ix.MftTable):
            """A table with the states and index roots a test gives it, and the real state_now."""

            def __init__(self, path):                              # pylint: disable=super-init-not-called
                self.path, self.states, self.extensions = path, states or {}, {}

            def root_entries(self, number):
                return (roots or {}).get(number)

        with mock.patch.object(ix, 'logfunc') as log, mock.patch.object(ix, 'MftTable', FakeTable):
            function.__wrapped__(context)
        return rows, result, [c.args[0] for c in log.call_args_list], context

    def index(self):
        tail = struct.pack('<Q', 0x0000000200000010)
        live = [entry(1, 1, 'kept.txt', modified=T2, size=900), entry(2, 1, 'renamed to this.txt')]
        slack = [entry(1, 1, 'kept.txt', modified=T1, size=100), entry(2, 1, 'name it had.txt'),
                 entry(9, 2, 'gone.txt', space=3), tail + entry(7, 7, 'reference lost.txt')[8:]]
        return block(live, b''.join(slack), gap=8), 0x40 + len(b''.join(live)) + 16 + 8, slack

    def test_removed_names(self):
        data, first, slack = self.index()
        states = {2: (1, True, frozenset()), 9: (3, False, frozenset())}
        rows, result, logged, context = self.run_artifact(
            ix.windowsNtfsIndexSlack,
            {'vol/Users/someone/Documents:$I30': data, 'vol/$MFT': b'x', 'vol/empty:$I30': block([]),
             'vol/notes.txt': data}, states, roots={77: []})
        headers = context.create_artifact_result.call_args.kwargs['headers']
        self.assertEqual(headers[:5], (('Record Changed', 'datetime'), ('Created', 'datetime'),
                                       ('Modified', 'datetime'), ('Accessed', 'datetime'), 'File Name'))
        self.assertEqual(len(headers), 18)
        staged = 'vol/Users/someone/Documents_$I30'
        second = first + len(slack[0])
        third = second + len(slack[1])
        self.assertEqual(rows, [
            (T1, T1, T1, T1, 'name it had.txt', '/Users/someone/Documents', 'File, under another name',
             'Same sequence, in use', 2, 1, 77, 4, 100, 4096, 'Archive', 'Win32', second, staged),
            (T1, T1, T1, T1, 'gone.txt', '/Users/someone/Documents', 'No', 'Sequence one higher, not in use',
             9, 2, 77, 4, 100, 4096, 'Archive', 'Win32 and DOS', third, staged),
            (T1, T1, T1, T1, 'reference lost.txt', '/Users/someone/Documents', 'Reference overwritten',
             'Reference overwritten', '', '', 77, 4, 100, 4096, 'Archive', 'Win32', third + len(slack[2]), staged)])
        result.set_source_path.assert_called_once_with(os.path.join(self.folder.name, staged))
        self.assertEqual(logged, [])

    def test_removed_names_without_an_mft_and_the_root_directory(self):
        data, _first, _slack = self.index()
        rows, _, logged, _ = self.run_artifact(ix.windowsNtfsIndexSlack, {'vol/:$I30': data})
        self.assertEqual([(row[4], row[5], row[7]) for row in rows],
                         [('name it had.txt', '/', ''), ('gone.txt', '/', ''),
                          ('reference lost.txt', '/', 'Reference overwritten')])
        self.assertEqual(logged, ['NTFS $I30 Index Slack - Unlisted Entries: no $MFT found for vol, so its index '
                                  'roots are not read and the columns that come from the $MFT are blank'])

    def test_names_in_the_index_root_are_live(self):
        data, first, _slack = self.index()
        files = {'vol/Users/someone/Documents:$I30': data, 'vol/$MFT': b'x'}
        roots = {77: [ix.name_entry(entry(9, 2, 'gone.txt', space=3), 0, 200),
                      ix.name_entry(entry(2, 1, 'name it had.txt', size=7), 0, 200)]}
        rows, _, logged, _ = self.run_artifact(ix.windowsNtfsIndexSlack, files, roots=roots)
        self.assertEqual([row[4] for row in rows], ['reference lost.txt'])
        self.assertEqual(logged, ['NTFS $I30 Index Slack - Unlisted Entries: 1 entries in slack identical to an '
                                  'entry of the index, not reported'])
        rows, _, _, _ = self.run_artifact(ix.windowsNtfsIndexSlackCopies, files, roots=roots)
        self.assertEqual([(row[5], row[7], row[8]) for row in rows],
                         [('kept.txt', 100, 900), ('name it had.txt', 100, 7)])
        self.assertEqual(rows[0][-2], first)

    def test_an_index_root_that_cannot_be_read_is_counted(self):
        data, _first, _slack = self.index()
        rows, _, logged, _ = self.run_artifact(ix.windowsNtfsIndexSlack,
                                               {'vol/dir:$I30': data, 'vol/$MFT': b'x'}, roots={})
        self.assertEqual(len(rows), 3)
        self.assertEqual(logged, ['NTFS $I30 Index Slack - Unlisted Entries: 1 index allocations whose index root '
                                  'could not be read'])

    def test_copies_of_live_entries(self):
        data, first, _slack = self.index()
        rows, result, logged, context = self.run_artifact(
            ix.windowsNtfsIndexSlackCopies, {'vol/Users/someone/Documents:$I30': data, 'vol/$MFT': b'x'},
            roots={77: []})
        headers = context.create_artifact_result.call_args.kwargs['headers']
        self.assertEqual(headers[:2], (('Modified', 'datetime'), ('Modified Now', 'datetime')))
        self.assertEqual(len(headers), 16)
        staged = 'vol/Users/someone/Documents_$I30'
        self.assertEqual(rows, [(T1, T2, T1, T1, T1, 'kept.txt', '/Users/someone/Documents', 100, 900, 4096,
                                 'Archive', 1, 1, 'Win32', first, staged)])
        result.set_source_path.assert_called_once_with(os.path.join(self.folder.name, staged))
        self.assertEqual(logged, [])

    def test_nothing_in_the_slack(self):
        for function, words in ((ix.windowsNtfsIndexSlack, 'no unlisted entries found in the slack of 1 index'),
                                (ix.windowsNtfsIndexSlackCopies,
                                 'no copies of live entries found in the slack of 1 index')):
            rows, result, logged, _ = self.run_artifact(
                function, {'vol/dir:$I30': block([entry(1, 1, 'a')]), 'vol/$MFT': b'x'}, states={})
            self.assertEqual(rows, [])
            result.set_source_path.assert_called_once_with('')
            self.assertEqual(len(logged), 1)
            self.assertIn(words, logged[0])

    def test_no_index_found(self):
        rows, result, logged, _ = self.run_artifact(ix.windowsNtfsIndexSlack, {'vol/$MFT': b'x'}, states={})
        self.assertEqual((rows, logged), ([], []))
        result.set_source_path.assert_called_once_with('')


if __name__ == '__main__':
    unittest.main()
