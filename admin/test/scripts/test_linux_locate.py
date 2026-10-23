"""Pin the locate database readers in scripts/linux_locate.py and the two artifacts in
scripts/artifacts/linuxLocateDatabases.py.

Every database here is built by the writers below, which follow the formats as their sources
describe them: plocate's db.h and database-builder.cpp (1.1.25), mlocate.db(5) (0.26) and the
LOCATE02 section of the findutils manual (4.10.0). Every path is invented. The expected values
are written out, never read back from the code under test. The plocate tests need a zstd
compressor and are skipped on a Python that has neither compression.zstd nor backports.zstd.
"""
import datetime
import fnmatch
import os
import pathlib
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import linux_locate as ll  # pylint: disable=wrong-import-position
from scripts.artifacts import linuxLocateDatabases as lld  # pylint: disable=wrong-import-position

try:
    from compression import zstd as _zstd  # pylint: disable=import-error
except ImportError:
    try:
        from backports import zstd as _zstd  # pylint: disable=import-error
    except ImportError:
        _zstd = None

UTC = datetime.timezone.utc
CONF = (b'prune_bind_mounts\x001\x00\x00prunefs\x00NFS\x00PROC\x00\x00prunenames\x00.git\x00\x00'
        b'prunepaths\x00/tmp\x00/var/spool\x00\x00')
CONF_PARSED = {'prune_bind_mounts': ['1'], 'prunefs': ['NFS', 'PROC'], 'prunenames': ['.git'],
               'prunepaths': ['/tmp', '/var/spool']}


def mlocate_db(root, directories, conf=CONF, visibility=1, version=0):
    """directories: (path, seconds, nanoseconds, [(type, name), ...]) in stored order."""
    out = b'\0mlocate' + struct.pack('>IBB2x', len(conf), version, visibility) + root + b'\0' + conf
    for path, seconds, nanoseconds, entries in directories:
        out += struct.pack('>QI4x', seconds, nanoseconds) + path + b'\0'
        for kind, name in entries:
            out += bytes([kind]) + name + b'\0'
        out += b'\2'
    return out


def locate02_db(paths):
    """Front-code the paths the way the findutils manual describes frcode doing it."""
    out = b'\0LOCATE02\0'
    previous, previous_count = b'', 0
    for path in paths:
        count = 0
        while count < min(len(previous), len(path)) and previous[count] == path[count]:
            count += 1
        diff = count - previous_count
        if -127 <= diff <= 127:
            out += bytes([diff & 0xff])
        else:
            out += b'\x80' + struct.pack('>h', diff)
        out += path[count:] + b'\0'
        previous, previous_count = path, count
    return out


def _compress(data, zdict=None):
    """zstd-compress, or with no compressor installed return the bytes as they are (for tests that never
    decompress them)."""
    if _zstd is None:
        return data
    return _zstd.compress(data, zstd_dict=zdict) if zdict else _zstd.compress(data)


def plocate_db(paths, block_size=3, order='<', dictionary=True, conf=CONF, visibility=True, max_version=2,
               version=1, dir_data=True):
    """paths: (path, None) for a path that is not a directory, (path, (seconds, nanoseconds)) for one that is."""
    names = [p for p, _ in paths]
    blocks = [b'\0'.join(names[i:i + block_size]) for i in range(0, len(names), block_size)]
    zdict = None
    if dictionary:
        samples = [b'\0'.join(names) + bytes([i]) * 40 for i in range(200)]
        zdict = _zstd.train_dict(samples, 2048)
    dict_bytes = zdict.dict_content if zdict else b''
    body = bytearray(b'\0' * 112)
    dict_off = len(body)
    body += dict_bytes
    offsets = []
    for block in blocks:
        offsets.append(len(body))
        body += _compress(block, zdict)
    offsets.append(len(body))
    index_off = len(body)
    body += struct.pack(f'{order}{len(offsets)}Q', *offsets)
    dd_off = dd_len = 0
    if dir_data:
        stream = b''.join(b'\0' if t is None else b'\1' + struct.pack(order + 'qi', *t) for _, t in paths)
        packed = _compress(stream)
        dd_off, dd_len = len(body), len(packed)
        body += packed
    conf_off = len(body)
    body += conf
    header = struct.pack(order + 'IIIIQQIIQQQQQQQ?', version, 0, 16, len(blocks), index_off, index_off,
                         max_version, len(dict_bytes), dict_off, dd_len, dd_off, 0, 0, len(conf), conf_off,
                         visibility)
    body[0:8] = b'\0plocate'
    body[8:8 + len(header)] = header
    return bytes(body)


PLOCATE_PATHS = [
    (b'/alpha', (1700000000, 500000000)),
    (b'/beta.txt', None),
    (b'/gamma', (0, 0)),
    (b'/alpha/one.txt', None),
    (b'/alpha/sub', (1700000100, 0)),
    (b'/alpha/sub/caf\xc3\xa9.bin', None),
    (b'/alpha/sub/odd\xff', None),
]


def entries_of(db):
    return [(e.path, e.kind, e.time, e.container_time) for e in db.entries]


class MlocateTest(unittest.TestCase):
    DIRECTORIES = [
        (b'/srv/demo', 1600000000, 250, [(0, b'a.txt'), (1, b'docs'), (1, b'locked')]),
        (b'/srv/demo/docs', 1600000500, 999999999, [(0, b'b.pdf'), (1, b'empty')]),
        (b'/srv/demo/docs/empty', 0, 0, []),
    ]

    def test_paths_types_and_times(self):
        db = ll.read(mlocate_db(b'/srv/demo', self.DIRECTORIES))
        self.assertEqual(db.format, 'mlocate')
        self.assertEqual((db.root, db.version, db.visibility), ('/srv/demo', '0', 1))
        self.assertEqual(db.configuration, CONF_PARSED)
        self.assertEqual(db.problems, [])
        self.assertEqual(entries_of(db), [
            ('/srv/demo', 'directory (database root)', (1600000000, 250), None),
            ('/srv/demo/a.txt', 'not a directory', None, (1600000000, 250)),
            ('/srv/demo/docs', 'directory', (1600000500, 999999999), (1600000000, 250)),
            ('/srv/demo/locked', 'directory', None, (1600000000, 250)),
            ('/srv/demo/docs/b.pdf', 'not a directory', None, (1600000500, 999999999)),
            ('/srv/demo/docs/empty', 'directory', (0, 0), (1600000500, 999999999)),
        ])
        self.assertEqual(db.counts(), (6, 4, 2, 1))
        self.assertEqual(db.latest_directory_time(), (1600000500, 999999999))

    def test_root_slash(self):
        db = ll.read(mlocate_db(b'/', [(b'/', 1600000000, 0, [(0, b'vmlinuz'), (1, b'etc')]),
                                       (b'/etc', 1600000001, 0, [(0, b'hosts')])]))
        self.assertEqual([e.path for e in db.entries], ['/', '/vmlinuz', '/etc', '/etc/hosts'])

    def test_missing_end_marker_keeps_earlier_directories(self):
        data = mlocate_db(b'/srv/demo', self.DIRECTORIES)[:-1]
        db = ll.read(data)
        self.assertEqual(len(db.problems), 1)
        self.assertIn('have no end marker; read stopped there with 2 directories read', db.problems[0])
        self.assertEqual(len(db.entries), 6)

    def test_bad_entry_type(self):
        data = mlocate_db(b'/srv/demo', [(b'/srv/demo', 1600000000, 0, [(0, b'a'), (7, b'b')])])
        db = ll.read(data)
        self.assertIn('entry type 7 at offset', db.problems[0])
        self.assertEqual([e.path for e in db.entries], ['/srv/demo'])

    def test_unknown_version_is_read_and_flagged(self):
        db = ll.read(mlocate_db(b'/r', [(b'/r', 5, 0, [(0, b'f')])], version=3))
        self.assertEqual(db.problems, ['file format version 3; mlocate.db(5) defines only version 0'])
        self.assertEqual([e.path for e in db.entries], ['/r', '/r/f'])


class Locate02Test(unittest.TestCase):
    PATHS = [
        b'/usr/src',
        b'/usr/src/cmd/aardvark.c',
        b'/usr/src/cmd/armadillo.c',
        b'/usr/tmp/zoo',
        b'/' + b'd' * 200 + b'/x',
        b'/' + b'd' * 200 + b'/y\xfe',
        b'/z',
    ]

    def test_manual_sample_bytes(self):
        # The manual's sample: counts 0, 8, 6, -9 after the dummy entry.
        data = locate02_db(self.PATHS[:4])
        self.assertEqual(data, b'\0LOCATE02\0' + b'\x00/usr/src\0' + b'\x08/cmd/aardvark.c\0'
                         + b'\x06rmadillo.c\0' + b'\xf7tmp/zoo\0')

    def test_paths_including_two_byte_counts(self):
        data = locate02_db(self.PATHS)
        self.assertIn(b'\x80', data)
        db = ll.read(data)
        self.assertEqual(db.format, 'GNU locate (LOCATE02)')
        self.assertEqual(db.problems, [])
        self.assertEqual([e.path for e in db.entries], [
            '/usr/src', '/usr/src/cmd/aardvark.c', '/usr/src/cmd/armadillo.c', '/usr/tmp/zoo',
            '/' + 'd' * 200 + '/x', '/' + 'd' * 200 + '/y\\xfe', '/z'])
        self.assertEqual({e.kind for e in db.entries}, {'not recorded'})
        self.assertIsNone(db.latest_directory_time())

    def test_count_past_previous_path(self):
        data = b'\0LOCATE02\0' + b'\x00/a\0' + b'\x05b\0'
        db = ll.read(data)
        self.assertEqual([e.path for e in db.entries], ['/a'])
        self.assertEqual(db.problems, ['shared prefix length 5 at offset 15 is outside the previous path (2 bytes); '
                                       'read stopped there with 1 paths read'])


@unittest.skipIf(_zstd is None, 'needs compression.zstd (Python 3.14) or backports.zstd to build plocate databases')
class PlocateTest(unittest.TestCase):
    EXPECTED = [
        ('/alpha', 'directory', (1700000000, 500000000), None),
        ('/beta.txt', 'not a directory', None, None),
        ('/gamma', 'directory', (0, 0), None),
        ('/alpha/one.txt', 'not a directory', None, (1700000000, 500000000)),
        ('/alpha/sub', 'directory', (1700000100, 0), (1700000000, 500000000)),
        ('/alpha/sub/café.bin', 'not a directory', None, (1700000100, 0)),
        ('/alpha/sub/odd\\xff', 'not a directory', None, (1700000100, 0)),
    ]

    def test_with_dictionary(self):
        db = ll.read(plocate_db(PLOCATE_PATHS))
        self.assertEqual(db.problems, [])
        self.assertEqual((db.format, db.version, db.visibility), ('plocate', 'version 1, max_version 2', 1))
        self.assertEqual(db.configuration, CONF_PARSED)
        self.assertEqual(db.extra, {'byte order': 'little-endian', 'filename blocks': 3})
        self.assertEqual(entries_of(db), self.EXPECTED)
        self.assertEqual(db.counts(), (7, 3, 4, 1))

    def test_without_dictionary_big_endian(self):
        db = ll.read(plocate_db(PLOCATE_PATHS, dictionary=False, order='>', visibility=False))
        self.assertEqual(db.problems, [])
        self.assertEqual(db.extra['byte order'], 'big-endian')
        self.assertEqual(db.visibility, 0)
        self.assertEqual(entries_of(db), self.EXPECTED)

    def test_max_version_1_has_no_types_or_settings(self):
        db = ll.read(plocate_db(PLOCATE_PATHS, max_version=1, dir_data=False))
        self.assertIsNone(db.visibility)
        self.assertEqual(db.configuration, {})
        self.assertEqual({e.kind for e in db.entries}, {'not recorded'})
        self.assertEqual([e.path for e in db.entries][:2], ['/alpha', '/beta.txt'])

    def test_no_directory_data_as_plocate_build_writes(self):
        db = ll.read(plocate_db(PLOCATE_PATHS, dir_data=False))
        self.assertEqual((db.visibility, db.configuration, db.problems), (1, CONF_PARSED, []))
        self.assertEqual([(e.path, e.kind, e.time, e.container_time) for e in db.entries][:2],
                         [('/alpha', 'not recorded', None, None), ('/beta.txt', 'not recorded', None, None)])

    def test_version_0_reads_without_dictionary(self):
        db = ll.read(plocate_db(PLOCATE_PATHS, dictionary=False, max_version=0, version=0, dir_data=False))
        self.assertEqual(db.version, 'version 0, max_version 0')
        self.assertEqual(len(db.entries), 7)

    def test_short_directory_data(self):
        data = plocate_db(PLOCATE_PATHS[:3])
        db = ll.read(data[:])
        self.assertEqual(len(db.entries), 3)
        # Rebuild with one path more than the directory data covers.
        names_only = plocate_db(PLOCATE_PATHS[:3] + [(b'/delta', None)], dir_data=False)
        stream = _zstd.compress(b'\1' + struct.pack('<qi', 1700000000, 500000000) + b'\0')
        hdr = bytearray(names_only)
        off = len(hdr)
        hdr += stream
        struct.pack_into('<QQ', hdr, 56, len(stream), off)
        db = ll.read(bytes(hdr))
        self.assertEqual([e.kind for e in db.entries], ['directory', 'not a directory', 'not recorded',
                                                        'not recorded'])
        self.assertEqual(db.problems, ['directory data covers 2 of 4 paths'])

    def test_block_offset_outside_file(self):
        data = bytearray(plocate_db(PLOCATE_PATHS, dictionary=False))
        index_off = struct.unpack_from('<Q', data, 32)[0]
        struct.pack_into('<Q', data, index_off + 16, len(data) + 10)
        db = ll.read(bytes(data))
        self.assertEqual(len(db.entries), 3)
        self.assertTrue(db.problems[0].startswith('filename block 1 has offsets'))

class NoDecoderTest(unittest.TestCase):
    def test_without_a_zstd_decoder(self):
        saved = ll._ZSTD  # pylint: disable=protected-access
        ll._ZSTD = None  # pylint: disable=protected-access
        try:
            db = ll.read(plocate_db(PLOCATE_PATHS, dictionary=False))
        finally:
            ll._ZSTD = saved  # pylint: disable=protected-access
        self.assertEqual(db.entries, [])
        self.assertEqual(db.problems, [ll.ZSTD_MISSING])
        self.assertEqual(db.configuration, CONF_PARSED)
        self.assertFalse(db.paths_read)


class HelpersTest(unittest.TestCase):
    def test_directory_time(self):
        self.assertEqual(ll.directory_time(0, 0), '')
        self.assertEqual(ll.directory_time(1700000000, 123456789),
                         datetime.datetime(2023, 11, 14, 22, 13, 20, 123456, tzinfo=UTC))
        self.assertEqual(ll.directory_time(2 ** 62, 0), '')

    def test_configuration_with_empty_list(self):
        found, problem = ll.parse_configuration(b'prunenames\x00\x00prunepaths\x00/x\x00\x00')
        self.assertEqual((found, problem), ({'prunenames': [], 'prunepaths': ['/x']}, None))
        found, problem = ll.parse_configuration(b'prunepaths\x00/x')
        self.assertEqual(problem, 'the configuration block does not end with a NUL byte')

    def test_not_a_locate_database(self):
        with self.assertRaises(ValueError):
            ll.read(b'SQLite format 3\x00')


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return os.path.basename(path)


class ArtifactTest(unittest.TestCase):
    def test_rows_and_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            mdb = os.path.join(folder, 'mlocate.db')
            gdb = os.path.join(folder, 'locatedb')
            junk = os.path.join(folder, 'plocate.db')
            with open(mdb, 'wb') as handle:
                handle.write(mlocate_db(b'/srv/demo', MlocateTest.DIRECTORIES))
            with open(gdb, 'wb') as handle:
                handle.write(locate02_db([b'/a', b'/a/b']))
            with open(junk, 'wb') as handle:
                handle.write(b'not a database')
            context = _Context([junk, mdb, gdb])
            headers, rows, source = lld.locateDatabasePaths.__wrapped__(context)
            sheaders, srows, ssource = lld.locateDatabases.__wrapped__(context)
        self.assertEqual(headers[2:], ('Path', 'Entry Type', 'Database Format', 'Source File'))
        self.assertEqual(source, f'{gdb}\n{mdb}')
        self.assertEqual(ssource, source)
        stamp = datetime.datetime.fromtimestamp(1600000000, UTC)
        later = datetime.datetime(2020, 9, 13, 12, 35, tzinfo=UTC) + datetime.timedelta(microseconds=999999)
        self.assertEqual(rows, [
            ('', '', '/a', 'not recorded', 'GNU locate (LOCATE02)', 'locatedb'),
            ('', '', '/a/b', 'not recorded', 'GNU locate (LOCATE02)', 'locatedb'),
            ('', stamp, '/srv/demo', 'directory (database root)', 'mlocate', 'mlocate.db'),
            (stamp, '', '/srv/demo/a.txt', 'not a directory', 'mlocate', 'mlocate.db'),
            (stamp, later, '/srv/demo/docs', 'directory', 'mlocate', 'mlocate.db'),
            (stamp, '', '/srv/demo/locked', 'directory, no directory time stored', 'mlocate', 'mlocate.db'),
            (later, '', '/srv/demo/docs/b.pdf', 'not a directory', 'mlocate', 'mlocate.db'),
            (later, '', '/srv/demo/docs/empty', 'directory, directory time stored as 0', 'mlocate', 'mlocate.db'),
        ])
        self.assertEqual(sheaders[0], ('Latest Directory Time', 'datetime'))
        self.assertEqual(srows, [
            ('', 'GNU locate (LOCATE02)', 'LOCATE02', '', '', '', '', '', '', 2, '', '', '', '', 'locatedb'),
            (later, 'mlocate', '0', '/srv/demo', '1', '1', 'NFS\nPROC', '.git', '/tmp\n/var/spool', 6, 4, 2, 1,
             '', 'mlocate.db'),
        ])


class PathsTest(unittest.TestCase):
    def test_declared_globs(self):
        info = lld.__artifacts_v2__
        patterns = info['locateDatabasePaths']['paths']
        self.assertEqual(patterns, info['locateDatabases']['paths'])
        matching = ['root/var/lib/plocate/plocate.db', 'lba0/var/lib/mlocate/plocate.db',
                    'root/var/lib/mlocate/mlocate.db', 'root/var/cache/locate/locatedb',
                    'root/usr/local/var/locatedb']
        other = ['root/var/lib/plocate/plocate.db.tmp', 'root/var/lib/plocate/CACHEDIR.TAG',
                 'root/var/lib/mlocate/mlocate.db.XXXXXX', 'root/etc/updatedb.conf']
        for path in matching:
            self.assertEqual(sum(fnmatch.fnmatchcase(path, p) for p in patterns), 1, path)
        for path in other:
            self.assertFalse(any(fnmatch.fnmatchcase(path, p) for p in patterns), path)


if __name__ == '__main__':
    unittest.main()
