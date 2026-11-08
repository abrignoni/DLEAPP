"""Pin scripts/shareaza.py and the Shareaza artifacts.

admin/test/fixtures/shareaza/Library1.dat and wanted.sd are files Shareaza 2.7.10.2 wrote on
windows11_arm_shareaza_known_20261108 (test file names, a client that never connected): one file in a library
folder, one ghost record, and one download added from a magnet link with only a SHA-1.
"""
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import shareaza  # pylint: disable=wrong-import-position
from scripts.artifacts import shareaza as shareaza_artifacts  # pylint: disable=wrong-import-position

FIXTURES = REPO_ROOT / 'admin' / 'test' / 'fixtures' / 'shareaza'
LIBRARY = (FIXTURES / 'Library1.dat').read_bytes()
DOWNLOAD = (FIXTURES / 'wanted.sd').read_bytes()


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ReaderTest(unittest.TestCase):
    def test_library_from_shareaza(self):
        result = shareaza.read_library(LIBRARY)
        self.assertTrue(result['complete'])
        self.assertEqual(result['version'], 29)
        self.assertIsInstance(result['saved'], datetime)
        self.assertEqual(result['saved'].utcoffset().total_seconds(), 0)  # pylint: disable=no-member
        self.assertEqual(len(result['folders']), 3)
        self.assertEqual([f['name'] for f in result['files']], ['kd-shareaza-beta.bin'])
        beta = result['files'][0]
        # Computed from the test file.
        self.assertEqual(beta['sha1'], 'b782145c42abca81ad342fed4bf11d03418ebc54')
        self.assertEqual(beta['md5'], '5704c32a05b3bc5ef4315ca024d7788e')
        self.assertEqual(beta['ed2k'], '4df4e6caf10ece3db94f25a134d65d55')
        self.assertEqual((beta['size'], beta['shared'], beta['folder_shared']), (150000, 0, 2))
        ghost = result['ghosts'][0]
        self.assertEqual((ghost['name'], ghost['comments'], ghost['size']), ('kd-shareaza-alpha.txt', 'Ghost File', 4600))
        self.assertEqual(ghost['sha1'], '0d774fcddc738547f516e27e0c45265e51876e97')
        self.assertEqual(list(result['history']), [beta['index']])

    def test_truncated_library_keeps_what_it_read(self):
        with self.assertRaises(shareaza.ShareazaFormatError) as caught:
            shareaza.read_library(LIBRARY[:-20])
        self.assertEqual(len(caught.exception.partial['files']), 1)
        self.assertEqual(len(caught.exception.partial['folders']), 3)

    def test_library_version_and_header(self):
        with self.assertRaises(shareaza.ShareazaFormatError):
            shareaza.read_library(LIBRARY[:8] + struct.pack('<i', 30) + LIBRARY[12:])
        legacy = shareaza.read_library(LIBRARY[8:], has_header=False)
        self.assertTrue(legacy['complete'])
        self.assertEqual(legacy['saved'], '')

    def test_strings(self):
        unicode = b'\xff\xfe\xff\x02' + 'é!'.encode('utf-16-le')
        self.assertEqual(shareaza._Archive(unicode).string(), 'é!')  # pylint: disable=protected-access
        ansi = b'\x03abc'
        self.assertEqual(shareaza._Archive(ansi).string(), 'abc')  # pylint: disable=protected-access
        self.assertEqual(shareaza._Archive(b'\xff\xff\x05\x00\x00\x00').count(), 5)  # pylint: disable=protected-access

    def test_download_from_shareaza(self):
        record = shareaza.read_download(DOWNLOAD)
        self.assertEqual((record['name'], record['size'], record['version']), ('kd-shareaza-wanted.bin', 60000, 42))
        # base32 5HWLN6VTB7FDB6E5YB5YSVT5EIO6MGJT from the magnet link
        self.assertEqual(record['sha1'], 'e9ecb6fab30fca30f89dc07b89567d221de61933')
        self.assertEqual((record['tiger'], record['md5'], record['ed2k'], record['bth']), ('', '', '', ''))

    def test_download_refusals(self):
        with self.assertRaises(shareaza.ShareazaFormatError):
            shareaza.read_download(b'XYZ' + DOWNLOAD[3:])
        with self.assertRaises(shareaza.ShareazaFormatError):
            shareaza.read_download(b'SDL' + struct.pack('<i', 10) + DOWNLOAD[7:])

    def test_filetime(self):
        self.assertEqual(shareaza.filetime(0), '')
        self.assertEqual(shareaza.filetime(116444736000000000), datetime(1970, 1, 1, tzinfo=timezone.utc))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = pathlib.Path(self.tmp.name)
        self.files = []
        for user, copies in (('lab', ('Library1.dat', 'Library2.dat')), ('other', ('Library1.dat',))):
            data = root / 'Users' / user / 'AppData' / 'Roaming' / 'Shareaza' / 'Data'
            data.mkdir(parents=True)
            for name in copies:
                shutil.copyfile(FIXTURES / 'Library1.dat', data / name)
                self.files.append(str(data / name))
        incomplete = root / 'Users' / 'lab' / 'AppData' / 'Local' / 'Shareaza' / 'Incomplete'
        incomplete.mkdir(parents=True)
        shutil.copyfile(FIXTURES / 'wanted.sd', incomplete / 'wanted.sd')
        (incomplete / 'other.sd').write_bytes(b'not a download')
        self.files += [str(incomplete / 'wanted.sd'), str(incomplete / 'other.sd')]
        self.context = FakeContext(self.tmp.name, self.files)

    def tearDown(self):
        self.tmp.cleanup()

    def test_library_files_merge_copies(self):
        with mock.patch.object(shareaza_artifacts, 'logfunc'):
            headers, rows, sources = shareaza_artifacts.shareazaLibraryFiles.__wrapped__(self.context)
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(headers), len(rows[0]))
        lab = {r[3]: r for r in rows if r[-1] == 'lab'}
        self.assertEqual(lab['Ghost'][-2], 'Library1.dat, Library2.dat')
        self.assertEqual(lab['Ghost'][0], '')
        self.assertNotEqual(lab['Ghost'][1], '')
        self.assertEqual(lab['In library folder'][12:14], ('Unknown', 'Yes'))
        self.assertNotEqual(lab['In library folder'][2], '')
        self.assertEqual(len(sources.split('\n')), 3)

    def test_folders_and_downloads(self):
        with mock.patch.object(shareaza_artifacts, 'logfunc') as log:
            _, folders, _ = shareaza_artifacts.shareazaLibraryFolders.__wrapped__(self.context)
            _, downloads, _ = shareaza_artifacts.shareazaDownloads.__wrapped__(self.context)
        self.assertEqual(len(folders), 6)
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0][-1], 'lab')
        self.assertTrue(any('other.sd' in str(c) for c in log.call_args_list))


if __name__ == '__main__':
    unittest.main()
