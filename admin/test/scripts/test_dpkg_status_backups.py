"""Pin the Package Status Changes (dpkg backups) artifact (scripts/artifacts/linuxDpkgStatus.py).

KNOWN_GZ is dpkg.status.3.gz from the known database of ubuntu2604_arm64_dpkgbackups byte for byte: the status file
after steps S1 and S2 (packages a 1.0 and b 1.0), copied by dpkg-db-backup with cp -p and compressed by savelog on the
lab VM, whose gzip header records the status file's time. The other copies are built here from the states the known
steps left, as that capture holds them.
"""
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxDpkgStatus as ds
# pylint: enable=wrong-import-position

KNOWN_GZ = bytes.fromhex(
    '1f8b08086975bb6a020364706b672e7374617475732e3000c58f4d4bc4400c86eff915f903dbee6e1db5832c2ed6930a'
    '05c17b26cdba43c7e93093557fbe75fd00f1e4c943e0258127cfdb138ff42816872094d2c28d0b827b253d148b3e16a5'
    '10701abfa20c70473eea3c922d76b7d7dbbec79b38bd44ec48092fc6f77c29aff49482543e3e53f0c306b699f75e85f5'
    '90e76733091e24173f458bab6a099d14ce3ee971f1493d92307d08fef083feb7b5fb07ebab29ee763e48b180b528d7df'
    '3ab5ab783e62b3368d3b592d4dcbc4a7d29e9fb12123edba6984ccf0b7e20ee00d0db9519daf010000')
KNOWN_GZ_TIME = 1790670185


def stanza(name, version, status='install ok installed', arch='all'):
    return (f'Package: {name}\nStatus: {status}\nArchitecture: {arch}\nVersion: {version}\n'
            f'Description: {name}\n\n').encode()


A2, B1, B_CONF, C1 = (stanza('dleapp-bk-a', '2.0'), stanza('dleapp-bk-b', '1.0'),
                      stanza('dleapp-bk-b', '1.0', 'deinstall ok config-files'), stanza('dleapp-bk-c', '1.0'))
D1, E1 = stanza('dleapp-bk-d', '1.0', arch='arm64'), stanza('dleapp-bk-e', '1.0')


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


class FileInfo:
    def __init__(self, source_path, modification_date):
        self.source_path, self.modification_date = source_path, modification_date


class Seeker:
    def __init__(self):
        self.file_infos = {}


class FakeContext:
    def __init__(self, paths, root, seeker):
        self.paths, self.root, self.seeker = paths, root, seeker

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


class HelperTest(unittest.TestCase):
    def test_gzip_time_of_the_known_copy(self):
        self.assertEqual(ds.gzip_time(KNOWN_GZ), utc(KNOWN_GZ_TIME))
        self.assertEqual(gzip.decompress(KNOWN_GZ).count(b'Package: '), 2)

    def test_gzip_time_absent(self):
        self.assertEqual(ds.gzip_time(gzip.compress(b'x', mtime=0)), '')
        self.assertEqual(ds.gzip_time(b'Package: x\n'), '')
        self.assertEqual(ds.gzip_time(b'\x1f\x8b\x08'), '')

    def test_changes(self):
        newer = {('a', 'all'): ('2.0', 'install ok installed'), ('b', 'all'): ('1.0', 'deinstall ok config-files'),
                 ('d', 'arm64'): ('1.0', 'install ok installed')}
        older = {('a', 'all'): ('1.0', 'install ok installed'), ('b', 'all'): ('1.0', 'install ok installed'),
                 ('c', 'all'): ('1.0', 'install ok installed'), ('d', 'arm64'): ('1.0', 'install ok installed')}
        self.assertEqual(ds.changes(newer, older), [
            ('Changed', 'a', 'all', '1.0', '2.0', 'install ok installed', 'install ok installed'),
            ('Changed', 'b', 'all', '1.0', '1.0', 'install ok installed', 'deinstall ok config-files'),
            ('In older copy only', 'c', 'all', '1.0', '', 'install ok installed', '')])
        self.assertEqual(ds.changes({('e', 'all'): ('1', 's')}, {}), [('In newer copy only', 'e', 'all', '', '1', '', 's')])

    def test_same_package_two_architectures(self):
        self.assertEqual(ds.changes({('l', 'amd64'): ('1', 's'), ('l', 'i386'): ('1', 's')}, {('l', 'amd64'): ('1', 's')}),
                         [('In newer copy only', 'l', 'i386', '', '1', '', 's')])

    def test_package_states_skips_stanzas_without_a_package(self):
        counts = ds.Counter()
        self.assertEqual(ds.package_states(A2 + b'Status: install ok installed\n\n', counts),
                         {('dleapp-bk-a', 'all'): ('2.0', 'install ok installed')})
        self.assertEqual(counts, ds.Counter({'stanzas with no Package field, not compared': 1}))


class ArtifactTest(unittest.TestCase):
    ROOT = 'home/u/root/'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.seeker = Seeker()
        self.paths = []
        self.logged = []
        patcher = mock.patch.object(ds, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, source, data, when=None):
        staged = os.path.join(self.root, *source.split('/'))
        os.makedirs(os.path.dirname(staged), exist_ok=True)
        with open(staged, 'wb') as handle:
            handle.write(data)
        self.paths.append(staged)
        if when is not None:
            self.seeker.file_infos[staged] = FileInfo(source, when)
        return staged

    def known(self):
        r = self.ROOT
        self.add(r + 'var/lib/dpkg/status', A2 + B_CONF + D1 + E1, 1790670208)
        self.add(r + 'var/backups/dpkg.status.0', A2 + B_CONF + D1, 1790670204)
        self.add(r + 'var/backups/dpkg.status.1.gz', gzip.compress(A2 + B_CONF, mtime=1790670198), 1)
        self.add(r + 'var/backups/dpkg.status.2.gz', gzip.compress(A2 + B1 + C1, mtime=1790670192), 2)
        self.add(r + 'var/backups/dpkg.status.3.gz', KNOWN_GZ, 3)

    def run_artifact(self):
        return ds.dpkgStatusBackups.__wrapped__(FakeContext(self.paths, self.root, self.seeker))

    def test_headers(self):
        self.assertEqual(self.run_artifact()[0], (
            ('Newer Copy Written (UTC)', 'datetime'), ('Older Copy Written (UTC)', 'datetime'), 'Change', 'Package',
            'Architecture', 'Older Version', 'Newer Version', 'Older Status', 'Newer Status', 'Newer Copy',
            'Older Copy'))

    def test_known_copies(self):
        self.known()
        _headers, rows, source = self.run_artifact()
        r = self.ROOT
        self.assertEqual([(row[0], row[1], row[2], row[3], row[9].split('/')[-1], row[10].split('/')[-1]) for row in rows], [
            (utc(1790670208), utc(1790670204), 'In newer copy only', 'dleapp-bk-e', 'status', 'dpkg.status.0'),
            (utc(1790670204), utc(1790670198), 'In newer copy only', 'dleapp-bk-d', 'dpkg.status.0', 'dpkg.status.1.gz'),
            (utc(1790670198), utc(1790670192), 'Changed', 'dleapp-bk-b', 'dpkg.status.1.gz', 'dpkg.status.2.gz'),
            (utc(1790670198), utc(1790670192), 'In older copy only', 'dleapp-bk-c', 'dpkg.status.1.gz', 'dpkg.status.2.gz'),
            (utc(1790670192), utc(KNOWN_GZ_TIME), 'Changed', 'dleapp-bk-a', 'dpkg.status.2.gz', 'dpkg.status.3.gz'),
            (utc(1790670192), utc(KNOWN_GZ_TIME), 'In newer copy only', 'dleapp-bk-c', 'dpkg.status.2.gz', 'dpkg.status.3.gz')])
        self.assertEqual(rows[4][5:9], ('1.0', '2.0', 'install ok installed', 'install ok installed'))
        self.assertEqual(rows[0][9], r + 'var/lib/dpkg/status')
        self.assertEqual(len(source.split('\n')), 5)
        self.assertEqual(self.logged, [])

    def test_roots_kept_apart_and_one_copy_gives_nothing(self):
        self.known()
        self.add('var/lib/dpkg/status', A2, 5)
        self.add('other/var/backups/dpkg.status.0', A2, 6)
        _headers, rows, _source = self.run_artifact()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row[9].startswith(self.ROOT) and row[10].startswith(self.ROOT) for row in rows))

    def test_equal_copies_give_no_row(self):
        self.add('var/lib/dpkg/status', A2 + B1, 10)
        self.add('var/backups/dpkg.status.0', A2 + B1, 10)
        self.assertEqual(self.run_artifact()[1], [])

    def test_backup_without_current_status_and_gaps_in_numbering(self):
        self.add('var/backups/dpkg.status.1.gz', gzip.compress(A2, mtime=200), 1)
        self.add('var/backups/dpkg.status.4.gz', gzip.compress(stanza('dleapp-bk-a', '1.0'), mtime=100), 1)
        rows = self.run_artifact()[1]
        self.assertEqual([(r[0], r[1], r[2], r[5], r[6]) for r in rows], [(utc(200), utc(100), 'Changed', '1.0', '2.0')])

    def test_bad_copy_is_counted_and_skipped(self):
        self.add('var/lib/dpkg/status', A2 + E1, 10)
        self.add('var/backups/dpkg.status.0', A2, 9)
        self.add('var/backups/dpkg.status.1.gz', b'\x1f\x8b\x08\x00not gzip at all', 8)
        self.add('var/backups/dpkg.status.2.gz', gzip.compress(A2 + E1, mtime=7), 7)
        rows = self.run_artifact()[1]
        self.assertEqual([(r[2], r[3], r[9], r[10]) for r in rows], [
            ('In newer copy only', 'dleapp-bk-e', 'var/lib/dpkg/status', 'var/backups/dpkg.status.0'),
            ('In older copy only', 'dleapp-bk-e', 'var/backups/dpkg.status.0', 'var/backups/dpkg.status.2.gz')])
        self.assertEqual(self.logged, ['Package Status Changes (dpkg backups): 1 copies that could not be read, '
                                       'not compared'])

    def test_unrelated_names_not_read(self):
        self.add('var/backups/dpkg.status.old', A2, 1)
        self.add('var/backups/dpkg.status.0', A2, 2)
        self.add('var/backups/dpkg.status.1.bz2', A2 + E1, 3)
        self.add('myvar/lib/dpkg/status', A2 + E1, 4)
        opened = []
        real_read = ds._read  # pylint: disable=protected-access

        def spy(path):
            opened.append(os.path.relpath(path, self.root).replace(os.sep, '/'))
            return real_read(path)
        with mock.patch.object(ds, '_read', spy):
            self.assertEqual(self.run_artifact()[1], [])
        self.assertEqual(opened, ['var/backups/dpkg.status.0'])
        self.assertEqual(self.logged, [])

    def test_a_folder_in_the_matches_is_passed_over(self):
        self.add('var/lib/dpkg/status', A2 + E1, 10)
        self.add('var/backups/dpkg.status.0', A2, 9)
        folder = os.path.join(self.root, 'var', 'backups', 'dpkg.status.1.gz')
        os.makedirs(folder)
        self.paths.append(folder)
        self.assertEqual([r[3] for r in self.run_artifact()[1]], ['dleapp-bk-e'])
        self.assertEqual(self.logged, [])

    def test_only_copies_with_a_row_are_cited(self):
        self.add('var/lib/dpkg/status', A2 + E1, 10)
        self.add('var/backups/dpkg.status.0', A2, 9)
        self.add('var/backups/dpkg.status.1.gz', gzip.compress(A2, mtime=8), 8)
        _headers, rows, source = self.run_artifact()
        self.assertEqual(len(rows), 1)
        self.assertEqual(source.split('\n'), [os.path.join(self.root, 'var', 'lib', 'dpkg', 'status'),
                                              os.path.join(self.root, 'var', 'backups', 'dpkg.status.0')])


if __name__ == '__main__':
    unittest.main()
