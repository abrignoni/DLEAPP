"""Pin the systemd journal reader (scripts/systemd_journal.py) and the two journal artifacts.

The reader was checked against systemd 259.5's own: on the lab VM capture ubuntu2604_arm64_journal (38,220 entries
in four files) and on the four fixtures built here, every entry equals what journalctl -o export printed for the same
file, field for field, and journalctl --verify passed on each fixture. The fixtures are compact files with the keyed
hash and zstd, regular files with the Jenkins hash, XZ and the 240-byte header, regular files with the keyed hash,
LZ4 and the 256-byte header, and compact files without compression and the 264-byte header. FIXTURE_SHA256 holds
the SHA-256 of the files journalctl checked, so a change to the writer that alters them fails here first. The XZ
and zstd payloads are carried as bytes so the fixtures do not depend on the compressor installed.
"""
import hashlib
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / 'admin' / 'test' / 'scripts'))

# pylint: disable=wrong-import-position
import journal_writer as jw
from scripts import systemd_journal as sj
from scripts.artifacts import linuxJournal
from scripts.context import Context
# pylint: enable=wrong-import-position

BOOT_A = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
BOOT_B = bytes.fromhex('00112233445566778899aabbccddeeff')
LONG = b'MESSAGE=fixture long message ' + b'abcdefghijklmnopqrstuvwxyz0123456789' * 20
FRAMES = {
    'xz': {LONG: bytes.fromhex(
        'fd377a585a000000ff12d9410200210116000000742fe5a3e002ec00495d00269146c0d19457e4938a91267fcc9d09fafb5804'
        '8845ab19a36ed12d062a3f84adf2f26bd58a63b574862737b01f54939116f78acb3c9ec9e66bed85d2bfdf6d604aea6923a2f5'
        '80000000000000015ded05000000a83cdf94a8000afc020000000000595a')},
    'zstd': {LONG: bytes.fromhex(
        '28b52ffd60ed0155020014044d4553534147453d66697874757265206c6f6e67206d657373616765206162636465666768696a'
        '6b6c6d6e6f707172737475767778797a30313233343536373839010041aa53a928')},
}
VARIANTS = {
    'compact_zstd_272': dict(compact=True, keyed=True, compression='zstd', header_size=272, state=2),
    'regular_xz_jenkins_240': dict(compact=False, keyed=False, compression='xz', header_size=240, state=0,
                                   tail_entry_boot_id_flag=False),
    'regular_lz4_keyed_256': dict(compact=False, keyed=True, compression='lz4', header_size=256, state=0,
                                  tail_entry_boot_id_flag=False),
    'compact_plain_264': dict(compact=True, keyed=True, compression=None, header_size=264, state=2),
}
FIXTURE_SHA256 = {
    'compact_zstd_272': '5cecf42e10f57ff316a866d840a3ae56c1dd5e79d74be6a9bdec32e2d1174f84',
    'regular_xz_jenkins_240': 'f2e3a89536f6878683676b3b2856dfef1a9f80a62c65642f3487c9a95a4157df',
    'regular_lz4_keyed_256': '491e07385661aad0efa74b4edbc3abce0c9765cf936ec4dac4ad0d40163f9854',
    'compact_plain_264': 'b7e9133f6adfff693963eb2bd59a2f5c02fc15eaa3847ea5ffde3bb3a8cf06e8',
}


def fields(i):
    """The fields of fixture entry i: forty entries over two boots, with a long message (entry 5), a field
    written twice (7), bytes that are not UTF-8 (9) and a two-line message (11)."""
    boot = BOOT_A if i < 20 else BOOT_B
    out = [('MESSAGE', b'fixture entry %d' % i), ('PRIORITY', b'%d' % (i % 8)),
           ('SYSLOG_IDENTIFIER', b'fixture'), ('_PID', b'%d' % (100 + i)), ('_TRANSPORT', b'journal'),
           ('_BOOT_ID', boot.hex().encode()), ('_HOSTNAME', b'fixture-host')]
    if i == 5:
        out[0] = ('MESSAGE', LONG.partition(b'=')[2])
    if i == 7:
        out += [('FIXTURE_REPEAT', b'one'), ('FIXTURE_REPEAT', b'two')]
    if i == 9:
        out.append(('FIXTURE_BYTES', b'\xff\xfe\x00\x01fixture'))
    if i == 11:
        out[0] = ('MESSAGE', b'fixture entry 11 line one\nline two')
    return out


def realtime(i):
    return 1790000000000000 + i * 1000000


def writer(variant, entries=40, **extra):
    kw = dict(VARIANTS[variant])
    kw.update(extra)
    w = jw.JournalWriter(frames=FRAMES.get(kw.get('compression'), {}), **kw)
    for i in range(entries):
        w.add_entry(fields(i), realtime=realtime(i), monotonic=1000000 + i * 1000, boot_id=BOOT_A if i < 20 else BOOT_B)
    return w


def fixture(variant):
    return writer(variant).bytes()


def zstd_available():
    return sj._ZSTD is not None  # pylint: disable=protected-access


class HashTest(unittest.TestCase):
    def test_siphash24_vector(self):
        # The vector systemd checks in src/test/test-siphash24.c at v259.5 (lines 15 and 50 to 53): key 00 to 0f,
        # input 00 to 0e.
        self.assertEqual(sj.siphash24(bytes(range(15)), bytes(range(16))), 0xa129ca6149be45e5)

    def test_jenkins_vectors(self):
        # driver5() in src/libsystemd/sd-journal/lookup3.c at v259.5: hashlittle2 with both initial values 0
        # gives deadbeef deadbeef for "" and 17770551 ce7226e6 for "Four score and seven years ago".
        self.assertEqual(sj.jenkins_hash64(b''), 0xdeadbeefdeadbeef)
        self.assertEqual(sj.jenkins_hash64(b'Four score and seven years ago'), 0x17770551ce7226e6)

    def test_every_length_up_to_two_blocks_is_hashed_whole(self):
        # A change in any byte, at any length the tail handling covers, changes both hashes.
        for n in range(1, 30):
            data = bytes(range(n))
            for position in range(n):
                changed = bytearray(data)
                changed[position] ^= 1
                with self.subTest(n=n, position=position):
                    self.assertNotEqual(sj.jenkins_hash64(data), sj.jenkins_hash64(bytes(changed)))
                    self.assertNotEqual(sj.siphash24(data, bytes(16)), sj.siphash24(bytes(changed), bytes(16)))


class Lz4Test(unittest.TestCase):
    def test_literals_only(self):
        self.assertEqual(sj.lz4_block(b'\x50hello', 5), b'hello')

    def test_overlapping_match_then_literals(self):
        # 'ab', then a match of 8 bytes at distance 2 (it overlaps its own output), then the literal 'c'.
        self.assertEqual(sj.lz4_block(b'\x24ab\x02\x00\x10c', 11), b'ababababab' + b'c')

    def test_long_lengths(self):
        # 20 literals (15 plus an extension byte of 5), then a match of 4 + 15 + 3 = 22 bytes at distance 20.
        src = bytes(range(65, 85))
        block = b'\xff\x05' + src + b'\x14\x00\x03' + b'\x10!'
        self.assertEqual(sj.lz4_block(block, 20 + 22 + 1), src + src + src[:2] + b'!')

    def test_bad_blocks(self):
        for block, size in ((b'\x10a\x00\x00', 5), (b'\x10a\x05\x00', 5), (b'\x50hello', 6), (b'\x50hel', 5),
                            (b'\xf0', 20)):
            with self.subTest(block=block):
                with self.assertRaises(ValueError):
                    sj.lz4_block(block, size)

    def test_writer_blocks_round_trip(self):
        for data in (b'', b'x', b'abcd' * 3, LONG, bytes(range(256)) * 3, b'a' * 1000):
            with self.subTest(size=len(data)):
                self.assertEqual(sj.lz4_block(jw.lz4_compress(data), len(data)), data)


class FixtureTest(unittest.TestCase):
    def test_fixtures_are_the_files_journalctl_checked(self):
        for variant, digest in FIXTURE_SHA256.items():
            with self.subTest(variant=variant):
                self.assertEqual(hashlib.sha256(fixture(variant)).hexdigest(), digest)

    def test_each_variant_reads_back(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                journal = sj.JournalFile(fixture(variant))
                entries = list(journal.entries())
                self.assertEqual(len(entries), 40)
                self.assertEqual(journal.walk_stop, None)
                for i, entry in enumerate(entries):
                    self.assertEqual((entry.seqnum, entry.realtime, entry.monotonic), (i + 1, realtime(i), 1000000 + i * 1000))
                    self.assertEqual(entry.boot_id, (BOOT_A if i < 20 else BOOT_B).hex())
                    self.assertTrue(entry.linked)
                    expected = sorted(set(fields(i)))
                    if variant == 'compact_zstd_272' and i == 5 and not zstd_available():
                        self.assertEqual(sorted(entry.fields), [f for f in expected if f[0] != 'MESSAGE'])
                        self.assertEqual(len(entry.problems), 1)
                        self.assertIn(sj.ZSTD_MISSING, entry.problems[0])
                        continue
                    self.assertEqual(sorted(entry.fields), expected)
                    self.assertEqual(entry.problems, [])

    def test_header_facts(self):
        expected = {
            'compact_zstd_272': (['tail entry boot ID', 'keyed hash', 'zstd compression', 'compact'], 'archived'),
            'regular_xz_jenkins_240': (['XZ compression'], 'offline'),
            'regular_lz4_keyed_256': (['LZ4 compression', 'keyed hash'], 'offline'),
            'compact_plain_264': (['tail entry boot ID', 'keyed hash', 'compact'], 'archived'),
        }
        for variant, (features, state) in expected.items():
            with self.subTest(variant=variant):
                journal = sj.JournalFile(fixture(variant))
                self.assertEqual(journal.features(), features)
                self.assertEqual(sj.STATES[journal.state], state)
                self.assertEqual((journal.n_entries, journal.head_entry_seqnum, journal.tail_entry_seqnum), (40, 1, 40))
                self.assertEqual((journal.head_entry_realtime, journal.tail_entry_realtime), (realtime(0), realtime(39)))


def data_object(journal, payload):
    """Offset of the DATA object holding payload uncompressed."""
    offset = journal.header_size
    while True:
        kind, _flags, size = struct.unpack_from('<BB6xQ', journal.data, offset)
        if size == 0:
            raise AssertionError('payload not found')
        start = offset + (72 if journal.compact else 64)
        if kind == 1 and journal.data[start:offset + size] == payload:
            return offset
        offset = (offset + size + 7) & ~7


class DamageTest(unittest.TestCase):
    def test_entry_not_linked(self):
        w = writer('compact_plain_264')
        w.add_entry([('MESSAGE', b'written, never linked')], realtime=realtime(40), monotonic=2000000, link=False)
        journal = sj.JournalFile(w.bytes())
        entries = list(journal.entries())
        self.assertEqual((journal.n_entries, len(entries)), (40, 41))
        self.assertEqual(entries[-1].fields, [('MESSAGE', b'written, never linked')])
        self.assertFalse(entries[-1].linked)
        self.assertEqual(entries[-1].problems, ['not reached from the chain of entry arrays'])

    def test_changed_payload(self):
        data = bytearray(fixture('compact_plain_264'))
        journal = sj.JournalFile(bytes(data))
        offset = data_object(journal, b'MESSAGE=fixture entry 3')
        data[offset + 72 + len(b'MESSAGE=fixture entry ')] = ord('8')
        entries = list(sj.JournalFile(bytes(data)).entries())
        self.assertIn(('MESSAGE', b'fixture entry 8'), entries[3].fields)
        self.assertEqual(entries[3].problems, ['MESSAGE: the hash stored with the DATA object does not match its payload'])
        self.assertEqual(sum(bool(e.problems) for e in entries), 1)

    def test_item_not_pointing_to_data(self):
        data = bytearray(fixture('compact_plain_264'))
        journal = sj.JournalFile(bytes(data))
        first_entry, second_entry = (offset for offset, _linked in journal.entry_offsets()[:2])
        self.assertGreater(int.from_bytes(data[second_entry + 8:second_entry + 16], 'little'), 72)
        data[first_entry + 64:first_entry + 68] = second_entry.to_bytes(4, 'little')
        entry = next(sj.JournalFile(bytes(data)).entries())
        self.assertEqual(len(entry.fields), 6)
        self.assertEqual(entry.problems, [f'item 1: does not point to a DATA object (offset {second_entry})'])

    def test_truncated_file(self):
        data = fixture('compact_plain_264')
        journal = sj.JournalFile(data)
        cut = journal.entry_offsets()[30][0] + 20
        short = sj.JournalFile(data[:cut])
        self.assertIn('which does not fit in the arena that ends at offset', short.walk_stop)
        entries = list(short.entries())
        self.assertEqual(len(entries), 30)
        self.assertEqual([e.seqnum for e in entries], list(range(1, 31)))
        # The fourth entry array of the main chain was appended after entry 29, so it lies before the cut and
        # still lists entries 29 and 30: every entry left is reached from the chain.
        self.assertTrue(all(e.linked for e in entries))

    def test_arena_end(self):
        data = fixture('compact_plain_264')
        arena = int.from_bytes(data[96:104], 'little')
        padded = bytearray(data + bytes(8))
        padded[96:104] = (arena + 8).to_bytes(8, 'little')
        self.assertIsNone(sj.JournalFile(bytes(padded)).walk_stop)
        padded[-3] = 1
        self.assertEqual(sj.JournalFile(bytes(padded)).walk_stop, '8 bytes left at the end of the arena')

    def test_unknown_incompatible_flag(self):
        data = bytearray(fixture('compact_plain_264'))
        data[12:16] = (int.from_bytes(data[12:16], 'little') | 32).to_bytes(4, 'little')
        journal = sj.JournalFile(bytes(data))
        self.assertEqual(journal.unknown_incompatible, 32)
        self.assertEqual(list(journal.entries()), [])
        self.assertIn('unknown incompatible flags 0x20', journal.features())

    def test_entry_size_not_whole_items(self):
        # Two bytes more than seven four-byte items still ends inside the same eight-byte slot, so the walk goes on.
        data = bytearray(fixture('compact_plain_264'))
        entry = sj.JournalFile(bytes(data)).entry_offsets()[2][0]
        size = int.from_bytes(data[entry + 8:entry + 16], 'little')
        self.assertEqual(size, 64 + 7 * 4)
        data[entry + 8:entry + 16] = (size + 2).to_bytes(8, 'little')
        entries = list(sj.JournalFile(bytes(data)).entries())
        self.assertEqual(len(entries), 40)
        self.assertEqual(entries[2].problems, [f'the entry is {size + 2} bytes, which is not a whole number of items'])
        self.assertEqual(sorted(entries[2].fields), sorted(set(fields(2))))

    def test_payload_without_an_equals_sign(self):
        data = bytearray(fixture('compact_plain_264'))
        journal = sj.JournalFile(bytes(data))
        offset = data_object(journal, b'MESSAGE=fixture entry 3')
        data[offset + 72 + len(b'MESSAGE')] = ord('X')
        changed = sj.JournalFile(bytes(data))
        entries = list(changed.entries())
        entry = changed.entry_offsets()[3][0]
        size = int.from_bytes(data[entry + 8:entry + 16], 'little')
        items = [int.from_bytes(data[i:i + 4], 'little') for i in range(entry + 64, entry + size, 4)]
        self.assertNotIn('MESSAGE', [name for name, _value in entries[3].fields])
        self.assertEqual(entries[3].problems, [f'item {items.index(offset) + 1}: the DATA object at offset {offset} holds no "="'])

    def test_zstd_payload_without_a_decoder(self):
        # Forces the path a Python without compression.zstd, backports.zstd or zstandard takes.
        saved = sj._ZSTD  # pylint: disable=protected-access
        sj._ZSTD = None  # pylint: disable=protected-access
        try:
            entries = list(sj.JournalFile(fixture('compact_zstd_272')).entries())
        finally:
            sj._ZSTD = saved  # pylint: disable=protected-access
        self.assertNotIn('MESSAGE', [name for name, _value in entries[5].fields])
        self.assertEqual(len(entries[5].problems), 1)
        self.assertRegex(entries[5].problems[0], r'^item \d+: the DATA object at offset \d+ is ' + sj.ZSTD_MISSING + '$')
        self.assertEqual(sum(bool(e.problems) for e in entries), 1)

    def test_compressed_payload_that_does_not_decode(self):
        data = bytearray(fixture('regular_xz_jenkins_240'))
        at = bytes(data).find(FRAMES['xz'][LONG])
        data[at + 40:at + 60] = bytes(20)
        entries = list(sj.JournalFile(bytes(data)).entries())
        self.assertNotIn('MESSAGE', [name for name, _value in entries[5].fields])
        self.assertRegex(entries[5].problems[0], r'^item \d+: the DATA object at offset \d+ is XZ data could not be decoded')

    def test_not_a_journal(self):
        renamed = b'LPKSHHRX' + fixture('compact_plain_264')[8:]
        for data in (b'', b'LPKSHHRH', b'NOTAJRNL' + bytes(300), renamed):
            with self.subTest(data=data[:8]):
                with self.assertRaises(sj.JournalError):
                    sj.JournalFile(data)


class RenderTest(unittest.TestCase):
    def test_show(self):
        self.assertEqual(linuxJournal.show(b'plain\ttext\nline two'), 'plain\ttext\nline two')
        self.assertEqual(linuxJournal.show(b'\x1b[31mred\x1b[0m\x7f\x00\r'), '␛[31mred␛[0m␡␀␍')
        self.assertEqual(linuxJournal.show(b'\xff\x00'), '[2 bytes, not UTF-8] ff00')
        long_value = b'\xff' * 1500
        self.assertEqual(linuxJournal.show(long_value), '[1,500 bytes, not UTF-8; the first 1,024 in hex] ' + 'ff' * 1024)

    def test_priority(self):
        for value, text in ((b'0', '0 (emerg)'), (b'3', '3 (err)'), (b'7', '7 (debug)'), (b'8', '8'),
                            (b'high', 'high'), (b'', ''), (b'06', '06'), (b'12', '12'), (b'67', '67')):
            with self.subTest(value=value):
                self.assertEqual(linuxJournal.priority(value), text)

    def test_times(self):
        # 1,790,000,000 seconds after 1970 is 2026-09-21 14:13:20 UTC; datetime.fromtimestamp, which the reader
        # does not use, agrees.
        moment = datetime(2026, 9, 21, 14, 13, 20, 1, tzinfo=timezone.utc)
        self.assertEqual(datetime.fromtimestamp(1790000000, timezone.utc), moment.replace(microsecond=0))
        self.assertEqual(linuxJournal.microseconds(0), '')
        self.assertEqual(linuxJournal.microseconds(1790000000000001), moment)
        self.assertEqual(linuxJournal.microseconds(253402300800000000), '')
        self.assertEqual(linuxJournal.source_time(b'1790000000000001'), moment)
        for value in (None, b'', b'-5', b'12x', b'9' * 20):
            with self.subTest(value=value):
                self.assertIsNone(linuxJournal.source_time(value))


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    @staticmethod
    def create_artifact_result(**kw):
        return Context.create_artifact_result(**kw)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        folder = os.path.join(self.root, 'var', 'log', 'journal', 'm')
        os.makedirs(folder)
        self.paths = []
        for variant in ('compact_plain_264', 'regular_xz_jenkins_240'):
            path = os.path.join(folder, variant + '.journal')
            with open(path, 'wb') as handle:
                handle.write(fixture(variant))
            self.paths.append(path)
        not_journal = os.path.join(folder, 'broken.journal~')
        with open(not_journal, 'wb') as handle:
            handle.write(b'not a journal')
        self.paths.append(not_journal)

    def tearDown(self):
        self.tmp.cleanup()

    def test_headers_follow_the_column_fields(self):
        result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext(self.paths[:1], self.root))
        headers = [h[0] if isinstance(h, tuple) else h for h in result.headers]
        self.assertEqual(headers[2:14], [column for column, _field in linuxJournal.COLUMN_FIELDS])
        self.assertEqual(headers[:2] + headers[14:], ['Time (UTC)', 'Source Time (UTC)', 'Boot ID', 'Monotonic (s)',
                                                      'Sequence Number', 'Other Fields', 'Entry Check', 'Source File'])
        self.assertEqual(len(list(result)[0]), len(headers))

    def test_entries(self):
        result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext(self.paths, self.root))
        rows = list(result)
        self.assertEqual(len(rows), 80)
        headers = [h[0] if isinstance(h, tuple) else h for h in result.headers]
        row = dict(zip(headers, rows[7]))
        self.assertEqual(row['Time (UTC)'], datetime(2026, 9, 21, 14, 13, 27, tzinfo=timezone.utc))
        self.assertEqual(row['Source Time (UTC)'], '')
        self.assertEqual((row['Priority'], row['Identifier'], row['Message']), ('7 (debug)', 'fixture', 'fixture entry 7'))
        self.assertEqual((row['Process ID'], row['Transport'], row['Hostname']), ('107', 'journal', 'fixture-host'))
        self.assertEqual((row['User ID'], row['Command'], row['Unit']), ('', '', ''))
        self.assertEqual(row['Other Fields'], 'FIXTURE_REPEAT=one\nFIXTURE_REPEAT=two')
        self.assertEqual((row['Boot ID'], row['Monotonic (s)'], row['Sequence Number']), (BOOT_A.hex(), '1.007000', 8))
        self.assertEqual((row['Entry Check'], row['Source File']), ('', 'var/log/journal/m/compact_plain_264.journal'))
        self.assertEqual(dict(zip(headers, rows[9]))['Other Fields'],
                         'FIXTURE_BYTES=[11 bytes, not UTF-8] fffe000166697874757265')
        self.assertEqual(dict(zip(headers, rows[45]))['Message'], LONG.partition(b'=')[2].decode())
        self.assertEqual(dict(zip(headers, rows[51]))['Message'], 'fixture entry 11 line one\nline two')
        self.assertEqual(result.source_path, '\n'.join(self.paths[:2]))

    def test_boot_id_field_kept_when_it_differs(self):
        w = writer('compact_plain_264', entries=1)
        w.add_entry([('MESSAGE', b'm'), ('_BOOT_ID', b'other')], realtime=realtime(1), monotonic=5)
        path = self.paths[0]
        with open(path, 'wb') as handle:
            handle.write(w.bytes())
        result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext([path], self.root))
        rows = list(result)
        headers = [h[0] if isinstance(h, tuple) else h for h in result.headers]
        self.assertNotIn('_BOOT_ID', dict(zip(headers, rows[0]))['Other Fields'])
        self.assertEqual(dict(zip(headers, rows[1]))['Other Fields'], '_BOOT_ID=other')

    def test_source_time_and_other_fields(self):
        w = writer('compact_plain_264', entries=0)
        w.add_entry([('ZETA', b'z'), ('MESSAGE', b'a'), ('ALPHA', b'a'), ('_SOURCE_REALTIME_TIMESTAMP', b'1790000000000001'),
                     ('MIDDLE', b'm')], realtime=realtime(0), monotonic=5, boot_id=BOOT_A)
        w.add_entry([('MESSAGE', b'b'), ('_SOURCE_REALTIME_TIMESTAMP', b'not a time')], realtime=realtime(1), monotonic=6,
                    boot_id=BOOT_A)
        path = self.paths[0]
        with open(path, 'wb') as handle:
            handle.write(w.bytes())
        result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext([path], self.root))
        headers = [h[0] if isinstance(h, tuple) else h for h in result.headers]
        first, second = (dict(zip(headers, row)) for row in result)
        self.assertEqual(first['Source Time (UTC)'], datetime(2026, 9, 21, 14, 13, 20, 1, tzinfo=timezone.utc))
        self.assertEqual(first['Other Fields'], 'ALPHA=a\nMIDDLE=m\nZETA=z')
        self.assertEqual(second['Source Time (UTC)'], '')
        self.assertEqual(second['Other Fields'], '_SOURCE_REALTIME_TIMESTAMP=not a time')

    def test_files_in_order_of_first_entry(self):
        folder = os.path.dirname(self.paths[0])
        later, earlier = os.path.join(folder, 'a.journal'), os.path.join(folder, 'b.journal')
        # b.journal begins earlier and ends later than a.journal, so ordering by the last entry would reverse them.
        for path, times in ((later, (50, 60)), (earlier, (10, 100))):
            w = writer('compact_plain_264', entries=0)
            for n, start in enumerate(times):
                w.add_entry([('MESSAGE', b'm%d' % n)], realtime=realtime(start), monotonic=5 + n, boot_id=BOOT_A)
            with open(path, 'wb') as handle:
                handle.write(w.bytes())
        os.makedirs(os.path.join(folder, 'folder.journal'))
        paths = [later, earlier, os.path.join(folder, 'folder.journal')]
        logged = []
        with mock.patch.object(linuxJournal, 'logfunc', logged.append):
            result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext(paths, self.root))
            rows = [row[-1] for row in result]
        self.assertEqual(rows, ['var/log/journal/m/b.journal'] * 2 + ['var/log/journal/m/a.journal'] * 2)
        self.assertFalse([line for line in logged if 'folder.journal' in line], logged)
        with mock.patch.object(linuxJournal, 'logfunc', logged.append):
            _headers, rows, source = linuxJournal.linuxJournalFiles.__wrapped__(FakeContext(paths, self.root))
        self.assertEqual([row[-1] for row in rows], ['var/log/journal/m/b.journal', 'var/log/journal/m/a.journal'])
        self.assertEqual(source, earlier + '\n' + later)

    def test_entry_check_column(self):
        w = writer('compact_plain_264', entries=2)
        w.add_entry([('MESSAGE', b'unlinked')], realtime=realtime(2), monotonic=2000000, boot_id=BOOT_A, link=False)
        data = bytearray(w.bytes())
        journal = sj.JournalFile(bytes(data))
        offset = data_object(journal, b'MESSAGE=unlinked')
        data[offset + 72 + len(b'MESSAGE=')] = ord('U')
        with open(self.paths[0], 'wb') as handle:
            handle.write(data)
        result = linuxJournal.linuxJournalEntries.__wrapped__(FakeContext(self.paths[:1], self.root))
        headers = [h[0] if isinstance(h, tuple) else h for h in result.headers]
        rows = [dict(zip(headers, row)) for row in result]
        self.assertEqual([row['Entry Check'] for row in rows],
                         ['', '', 'not reached from the chain of entry arrays; MESSAGE: the hash stored with the DATA '
                                  'object does not match its payload'])
        self.assertEqual(rows[2]['Message'], 'Unlinked')

    def test_files(self):
        headers, rows, source = linuxJournal.linuxJournalFiles.__wrapped__(FakeContext(self.paths, self.root))
        self.assertEqual(len(rows), 2)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        first = dict(zip(names, rows[0]))
        self.assertEqual((first['State'], first['Entries (Header)'], first['Entries Read'], first['Entries Not in Chain']),
                         ('archived', 40, 40, 0))
        self.assertEqual((first['First Sequence Number'], first['Last Sequence Number']), (1, 40))
        self.assertEqual(first['Features'], 'tail entry boot ID, keyed hash, compact')
        self.assertEqual(first['Reading'], '')
        self.assertEqual(source, '\n'.join(self.paths[:2]))

    def test_files_count_an_entry_not_in_the_chain(self):
        w = writer('compact_plain_264')
        w.add_entry([('MESSAGE', b'unlinked')], realtime=realtime(40), monotonic=2000000, link=False)
        with open(self.paths[0], 'wb') as handle:
            handle.write(w.bytes())
        headers, rows, _source = linuxJournal.linuxJournalFiles.__wrapped__(FakeContext(self.paths[:1], self.root))
        row = dict(zip([h[0] if isinstance(h, tuple) else h for h in headers], rows[0]))
        self.assertEqual((row['Entries (Header)'], row['Entries Read'], row['Entries Not in Chain'], row['Reading']),
                         (40, 41, 1, ''))

    def test_files_report_damage(self):
        w = writer('compact_plain_264')
        w.add_entry([('MESSAGE', b'unlinked')], realtime=realtime(40), monotonic=2000000, link=False)
        data = bytearray(w.bytes())
        data[12:16] = (int.from_bytes(data[12:16], 'little') | 64).to_bytes(4, 'little')
        with open(self.paths[0], 'wb') as handle:
            handle.write(data[:-100])
        headers, rows, _source = linuxJournal.linuxJournalFiles.__wrapped__(FakeContext(self.paths[:1], self.root))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        row = dict(zip(names, rows[0]))
        self.assertEqual((row['Entries (Header)'], row['Entries Read']), (40, 0))
        self.assertIn('entries not read: incompatible flags 0x40 are unknown to this reader', row['Reading'])
        self.assertIn('shorter than the 264-byte header', row['Reading'])
        self.assertIn('the object walk stopped early: the object at offset', row['Reading'])


if __name__ == '__main__':
    unittest.main()
