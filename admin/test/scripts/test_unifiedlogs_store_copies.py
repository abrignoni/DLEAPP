"""Pin how the Unified Logs artifact reads a log store held in two copies.

A logical extraction of a Mac can hold private/var/db/diagnostics and
System/Volumes/Data/private/var/db/diagnostics, the same store reached through the Data
volume's firmlink and copied at two moments. store_copies() finds every copy of the store the
chosen root belongs to, and assemble_merged_archive() reads them as one: a file only one copy
holds comes from that copy, and a file both hold comes from the copy whose bytes begin with
the other's. The expected contents below are written out, never read back from the code.
"""
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import unifiedlogs  # pylint: disable=wrong-import-position

OLDER = {
    'diagnostics/Persist/0000000000000001.tracev3': b'only in the older copy',
    'diagnostics/Persist/0000000000000002.tracev3': b'AAAA',
    'diagnostics/timesync/0000000000000002.timesync': b'TS1',
    'diagnostics/Special/0000000000000004.tracev3': b'same bytes',
    'diagnostics/Signpost/0000000000000005.tracev3': b'XXXX',
    'diagnostics/HighVolume/0000000000000001.tracev3': b'ABCD',
    'uuidtext/AB/CDEF0123456789ABCDEF0123456780': b'format strings',
}
NEWER = {
    'diagnostics/Persist/0000000000000002.tracev3': b'AAAABBBB',
    'diagnostics/Persist/0000000000000003.tracev3': b'only in the newer copy',
    'diagnostics/timesync/0000000000000002.timesync': b'TS1TS2',
    'diagnostics/Special/0000000000000004.tracev3': b'same bytes',
    'diagnostics/Signpost/0000000000000005.tracev3': b'YYYY',
    'diagnostics/HighVolume/0000000000000001.tracev3': b'ABXDEF',
    'uuidtext/AB/CDEF0123456789ABCDEF0123456780': b'format strings',
    'uuidtext/AB/CDEF0123456789ABCDEF0123456781': b'more format strings',
}
# A store elsewhere in the extraction that is not a firmlink twin of the chosen one.
DECOY = {'diagnostics/Persist/0000000000000001.tracev3': b'another store'}


class StoreCopiesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = pathlib.Path(self._tmp.name) / 'data'
        self.older = self.data / 'private' / 'var' / 'db'
        self.newer = self.data / 'System' / 'Volumes' / 'Data' / 'private' / 'var' / 'db'
        self.decoy = self.data / 'Users' / 'someone' / 'Library' / 'db'
        self.files_found = []
        for base, contents in ((self.newer, NEWER), (self.older, OLDER), (self.decoy, DECOY)):
            for relative, payload in contents.items():
                path = base / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                self.files_found.append(str(path))

    def tearDown(self):
        self._tmp.cleanup()

    def test_both_copies_are_found_and_the_decoy_is_not(self):
        chosen = str(self.newer / 'diagnostics')
        self.assertEqual(unifiedlogs.store_copies(self.files_found, chosen),
                         [chosen, str(self.older / 'diagnostics')])
        chosen_uuidtext = str(self.older / 'uuidtext')
        self.assertEqual(unifiedlogs.store_copies(self.files_found, chosen_uuidtext),
                         [chosen_uuidtext, str(self.newer / 'uuidtext')])

    def test_the_copies_are_read_as_one_store(self):
        workdir = pathlib.Path(self._tmp.name) / 'merged'
        diagnostics = unifiedlogs.store_copies(self.files_found, str(self.newer / 'diagnostics'))
        uuidtext = unifiedlogs.store_copies(self.files_found, str(self.newer / 'uuidtext'))
        archive, summary = unifiedlogs.assemble_merged_archive(diagnostics, uuidtext, str(workdir))
        read = {str(path.relative_to(archive)): path.read_bytes()
                for path in pathlib.Path(archive).rglob('*') if path.is_file()}
        self.assertEqual(read, {
            'Persist/0000000000000001.tracev3': b'only in the older copy',
            'Persist/0000000000000002.tracev3': b'AAAABBBB',
            'Persist/0000000000000003.tracev3': b'only in the newer copy',
            'timesync/0000000000000002.timesync': b'TS1TS2',
            'Special/0000000000000004.tracev3': b'same bytes',
            'Signpost/0000000000000005.tracev3': b'YYYY',
            'HighVolume/0000000000000001.tracev3': b'ABXDEF',
            'AB/CDEF0123456789ABCDEF0123456780': b'format strings',
            'AB/CDEF0123456789ABCDEF0123456781': b'more format strings',
        })
        self.assertEqual((summary['identical'], summary['extended'], summary['disagreed']),
                         (2, 2, 2))
        self.assertEqual(summary['only_in'], {str(self.newer / 'diagnostics'): 1,
                                              str(self.older / 'diagnostics'): 1,
                                              str(self.newer / 'uuidtext'): 1})

    def test_the_extending_copy_wins_whichever_copy_comes_first(self):
        workdir = pathlib.Path(self._tmp.name) / 'merged_reversed'
        archive, summary = unifiedlogs.assemble_merged_archive(
            [str(self.older / 'diagnostics'), str(self.newer / 'diagnostics')], [], str(workdir))
        self.assertEqual((pathlib.Path(archive) / 'Persist' / '0000000000000002.tracev3').read_bytes(),
                         b'AAAABBBB')
        self.assertEqual((pathlib.Path(archive) / 'Signpost' / '0000000000000005.tracev3').read_bytes(),
                         b'XXXX')
        self.assertEqual(summary['extended'], 2)


if __name__ == '__main__':
    unittest.main()
