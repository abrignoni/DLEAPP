"""Pin the Ares artifacts.

ShareL.dat files are built here with the inverse of the cipher Ares 2.4.6 applies (helper_library_db.pas), and the
registry is stood in for by small objects with the regfprobe key and value methods the artifacts call. The decoder
was also checked against the ShareL.dat Ares wrote on windows11_arm_ares_known_20261108.
"""
import hashlib
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import ares  # pylint: disable=wrong-import-position


def scramble(plain, key):
    word, out = key, bytearray()
    for byte in plain:
        cipher = byte ^ (word >> 8)
        out.append(cipher)
        word = ((cipher + word) * 23219 + 36126) & 0xFFFF
    return bytes(out)


def record(path, size, media, fields):
    detail = b''.join(bytes([kind]) + struct.pack('<H', len(value)) + value for kind, value in fields)
    detail = bytes([1]) + struct.pack('<H', len(path)) + path + detail
    head = hashlib.sha1(path).digest() + bytes([media]) + b'\0' * 4 + struct.pack('<Q', size) + b'\0' * 12
    head += struct.pack('<H', len(detail))
    return scramble(head, 13871) + scramble(detail, 13872)


LIBRARY = (b'__ARESDB1.04L_'
           + record(b'C:\\share\\song.mp3', 4000000, 1, [(2, b'A Title'), (3, b'An Artist'), (10, b'note')])
           + record('C:\\share\\caf\u00e9.txt'.encode('utf-8'), 12, 6, [(17, b'')]))


class FakeValue:
    def __init__(self, name, value):
        self._name, self._value = name, value

    def name(self):
        return self._name

    def value(self):
        return self._value


class FakeKey:
    def __init__(self, name, values=(), subkeys=()):
        self._name, self._values, self._subkeys = name, list(values), list(subkeys)

    def name(self):
        return self._name

    def values(self):
        return self._values

    def subkeys(self):
        return self._subkeys


def hexed(text):
    return text.encode('utf-8').hex().upper()


ROOT = FakeKey('Ares', [FakeValue('Personal.Nickname', hexed('someone_0a1b2c')),
                        FakeValue('Personal.GUID', '0A1B2C' + '0' * 26),
                        FakeValue('Download.Folder', hexed('D:\\Shared')),
                        FakeValue('General.Language', hexed('English'))])
HISTORY = FakeKey('Search.History', subkeys=[
    FakeKey('gen.gen', [FakeValue(hexed('first term'), ''), FakeValue(hexed('second'), '')]),
    FakeKey('audio.aut', [FakeValue(hexed('An Artist'), ''), FakeValue('not hex', '')])])
WRITTEN = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def fake_open_key(_reg, path):
    return {'Software\\Ares': ROOT, 'Software\\Ares\\Search.History': HISTORY}.get(path)


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class AresTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = pathlib.Path(self.tmp.name)
        data = root / 'Users' / 'lab' / 'AppData' / 'Local' / 'Ares' / 'Data'
        data.mkdir(parents=True)
        (data / 'ShareL.dat').write_bytes(LIBRARY + b'\x01\x02')
        hive = root / 'Users' / 'lab' / 'NTUSER.DAT'
        hive.write_bytes(b'regf')
        self.context = FakeContext(self.tmp.name, [str(data / 'ShareL.dat'), str(hive)])

    def tearDown(self):
        self.tmp.cleanup()

    def test_descramble_round_trip(self):
        self.assertEqual(ares.descramble(scramble(b'hello world', 13872), 13872), b'hello world')

    def test_read_library(self):
        records, left = ares.read_library(LIBRARY)
        self.assertEqual(left, 0)
        self.assertEqual(records[0]['path'], 'C:\\share\\song.mp3')
        self.assertEqual((records[0]['size'], records[0]['media'], records[0]['artist']), (4000000, 1, 'An Artist'))
        self.assertEqual(records[0]['sha1'], hashlib.sha1(b'C:\\share\\song.mp3').hexdigest())
        self.assertEqual((records[1]['path'], records[1]['corrupt']), ('C:\\share\\caf\u00e9.txt', True))
        with self.assertRaises(ValueError):
            ares.read_library(b'__ARESDB1.02H_')

    def test_library_artifact(self):
        with mock.patch.object(ares, 'logfunc') as log:
            headers, rows, _ = ares.aresLibrary.__wrapped__(self.context)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][3:6], ('Audio (MP3)', 'A Title', 'An Artist'))
        self.assertEqual((rows[1][3], rows[1][12], rows[1][13]), ('Document', 'Yes', 'lab'))
        self.assertTrue(any('2 bytes' in str(c) for c in log.call_args_list))

    def test_search_history_and_settings(self):
        with mock.patch.object(ares, 'open_hive', return_value=object()), \
                mock.patch.object(ares, 'open_key', side_effect=fake_open_key), \
                mock.patch.object(ares, 'key_written_utc', return_value=WRITTEN), \
                mock.patch.object(ares, 'logfunc') as log:
            _, history, _ = ares.aresSearchHistory.__wrapped__(self.context)
            _, settings, _ = ares.aresSettings.__wrapped__(self.context)
        self.assertEqual([r[1:5] for r in history],
                         [('first term', 'All', 'Search box', 'gen.gen'), ('second', 'All', 'Search box', 'gen.gen'),
                          ('An Artist', 'audio', 'Artist or author', 'audio.aut')])
        self.assertTrue(any('not hexadecimal' in str(c) for c in log.call_args_list))
        self.assertEqual([r[1:3] for r in settings],
                         [('Nickname', 'someone_0a1b2c'), ('Client GUID', '0A1B2C' + '0' * 26),
                          ('Shared Folder', 'D:\\Shared')])
        self.assertEqual({r[-1] for r in settings}, {'lab'})


if __name__ == '__main__':
    unittest.main()
