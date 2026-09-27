"""Pin the OneDrive log reading in scripts/onedrive_odl.py and scripts/artifacts/oneDriveLogs.py.

Every file below is built by the test from the layout the reader documents; no value comes
from a real device. Expected values are written out, never read back from the code.
"""
import base64
import fnmatch
import gzip
import json
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from Crypto.Cipher import AES

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import onedrive_odl as odl  # pylint: disable=wrong-import-position
from scripts.artifacts import oneDriveLogs as artifact  # pylint: disable=wrong-import-position

KEY = bytes(range(32))
MAGIC = b'\xcc\xdd\xee\xff'
# 2026-01-02 03:04:05.678 UTC in milliseconds since 1970.
TIME = 1767323045678


def text(value):
    raw = value.encode('utf-8') if isinstance(value, str) else value
    return struct.pack('<I', len(raw)) + raw


def data(code_file, function, params=b''):
    return text(code_file) + struct.pack('<I', 7) + text(function) + params


def header(version, onedrive_version='24.1.0.1'):
    block = bytearray(0x100)
    block[0:8] = b'EBFGONED'
    struct.pack_into('<I', block, 8, version)
    raw = onedrive_version.encode()
    block[0x1C:0x1C + len(raw)] = raw
    return bytes(block)


def v2_record(timestamp, payload):
    block = bytearray(56)
    block[0:4] = MAGIC
    struct.pack_into('<Q', block, 8, timestamp)
    struct.pack_into('<I', block, 48, len(payload))
    return bytes(block) + payload


def v3_record(timestamp, payload, context=b''):
    block = bytearray(32)
    block[0:4] = MAGIC
    struct.pack_into('<H', block, 4, len(context))
    struct.pack_into('<Q', block, 8, timestamp)
    lead = context or bytes(24)
    struct.pack_into('<I', block, 24, len(lead) + len(payload))
    return bytes(block) + lead + payload


def encrypt_word(plain, key=KEY, encoding='utf-16-le'):
    raw = plain.encode(encoding)
    pad = 16 - len(raw) % 16
    cipher = AES.new(key, AES.MODE_CBC, iv=bytes(16)).encrypt(raw + bytes([pad]) * pad)
    return base64.b64encode(cipher).decode().rstrip('=').replace('/', '_').replace('+', '-')


def keystore(key=KEY, version=1, encoding='utf-8'):
    entry = {'CreatedTime': 1767323045, 'Key': base64.b64encode(key).decode() + '\x00\x00',
             'Version': version}
    return json.dumps([entry]).encode(encoding)


class OdlFileTest(unittest.TestCase):
    def test_version_2_records(self):
        log = odl.OdlFile(header(2) + v2_record(TIME, data('a.cpp', 'A::Run', text('abcd')))
                          + v2_record(TIME + 1, data('b.cpp', 'B::Go')))
        self.assertEqual((log.version, log.onedrive_version, log.stopped_at), (2, '24.1.0.1', None))
        self.assertEqual([(r['timestamp'], r['code_file'], r['function'], r['params'])
                          for r in log.records],
                         [(TIME, 'a.cpp', 'A::Run', b'\x04\x00\x00\x00abcd'),
                          (TIME + 1, 'b.cpp', 'B::Go', b'')])

    def test_version_3_context_block_skipped(self):
        body = (v3_record(TIME, data('a.cpp', 'A::Run'), context=b'0123456789')
                + v3_record(TIME + 2, data('b.cpp', 'B::Go', text('efgh'))))
        log = odl.OdlFile(header(3) + body)
        self.assertEqual([(r['timestamp'], r['code_file'], r['function']) for r in log.records],
                         [(TIME, 'a.cpp', 'A::Run'), (TIME + 2, 'b.cpp', 'B::Go')])
        self.assertIsNone(log.stopped_at)

    def test_gzip_body(self):
        body = v3_record(TIME, data('a.cpp', 'A::Run', text('abcd')))
        log = odl.OdlFile(header(3) + gzip.compress(body))
        self.assertEqual([r['code_file'] for r in log.records], ['a.cpp'])
        self.assertEqual(log.body_size, len(body))

    def test_gzip_stream_cut_short(self):
        body = v3_record(TIME, data('a.cpp', 'A::Run')) + v3_record(TIME + 1, data('b.cpp', 'B::Go'))
        whole = odl.OdlFile(header(3) + gzip.compress(body))
        self.assertFalse(whole.gzip_cut_short)
        cut = odl.OdlFile(header(3) + gzip.compress(body)[:-8])
        self.assertTrue(cut.gzip_cut_short)
        self.assertEqual([r['code_file'] for r in cut.records], ['a.cpp', 'b.cpp'])

    def test_reading_stops_at_a_short_or_unmarked_record(self):
        good = v2_record(TIME, data('a.cpp', 'A::Run'))
        short = v2_record(TIME, data('b.cpp', 'B::Go'))[:-3]
        log = odl.OdlFile(header(2) + good + short)
        self.assertEqual((len(log.records), log.stopped_at, log.body_size),
                         (1, len(good), len(good) + len(short)))
        log = odl.OdlFile(header(2) + good + b'\x01' + b'\x00' * 59)
        self.assertEqual((len(log.records), log.stopped_at, log.zero_bytes), (1, len(good), 0))

    def test_zero_bytes_after_the_last_record(self):
        good = v2_record(TIME, data('a.cpp', 'A::Run'))
        log = odl.OdlFile(header(2) + good + b'\x00' * 60)
        self.assertEqual((len(log.records), log.stopped_at, log.zero_bytes), (1, None, 60))

    def test_other_files_refused(self):
        with self.assertRaises(ValueError):
            odl.OdlFile(b'not a log' + bytes(300))
        with self.assertRaises(ValueError):
            odl.OdlFile(header(4) + v2_record(TIME, data('a.cpp', 'A::Run')))


class ParamTextsTest(unittest.TestCase):
    def test_texts_in_order_around_numbers(self):
        params = (struct.pack('<Q', 123) + text('C:\\Users\\a') + struct.pack('<I', 5)
                  + text('url') + text('https://example.invalid/x'))
        self.assertEqual(odl.param_texts(params),
                         ['C:\\Users\\a', 'url', 'https://example.invalid/x'])

    def test_terminator_dropped_line_breaks_kept(self):
        self.assertEqual(odl.param_texts(text('Msg-Id: 1\r\n\r\n\x00')), ['Msg-Id: 1\r\n\r\n'])

    def test_shorter_than_three_characters_not_read(self):
        self.assertEqual(odl.param_texts(text('US') + text('abc')), ['abc'])

    def test_length_must_account_for_the_text(self):
        self.assertEqual(odl.param_texts(struct.pack('<I', 396) + b'@H&;' + bytes(8)), [])
        self.assertEqual(odl.param_texts(b'\xff\xff\xff\xffx9!)'), [])

    def test_utf8_text_read_whole(self):
        self.assertEqual(odl.param_texts(text('say \u201chi\u201d now')), ['say \u201chi\u201d now'])

    def test_bytes_that_are_not_text_skipped(self):
        self.assertEqual(odl.param_texts(text(b'\xff\xfeab')), [])
        self.assertEqual(odl.param_texts(text(b'ab\x01cd')), [])


class DecodeTest(unittest.TestCase):
    def test_encrypted_word_round_trip(self):
        self.assertEqual(odl.decrypt_word(encrypt_word('Documents'), KEY), 'Documents')

    def test_utf32_plain_text(self):
        self.assertEqual(odl.decrypt_word(encrypt_word('Documents', encoding='utf-32-le'), KEY),
                         'Documents')
        self.assertEqual(odl.decrypt_word(encrypt_word('ab', encoding='utf-32-le'), KEY), 'ab')

    def test_decrypted_text_may_hold_line_breaks(self):
        self.assertEqual(odl.decrypt_word(encrypt_word('PNG 4 CON 0\r\n'), KEY), 'PNG 4 CON 0\r\n')

    def test_parts_joined_by_plus_decrypted(self):
        stored = '101+' + encrypt_word('LM')
        self.assertEqual(odl.decode_text(stored, KEY, {}), ('101+LM', 1, 0))
        self.assertEqual(odl.decode_text(stored, None, {}), (stored, 0, 0))
        self.assertEqual(odl.decode_text('a+b', KEY, {}), ('a+b', 0, 0))

    def test_padding_must_be_valid(self):
        raw = 'Documen\u0241'.encode('utf-16-le')
        cipher = AES.new(KEY, AES.MODE_CBC, iv=bytes(16)).encrypt(raw)
        word = base64.b64encode(cipher).decode().rstrip('=').replace('/', '_').replace('+', '-')
        self.assertIsNone(odl.decrypt_word(word, KEY))

    def test_word_must_be_base64_throughout(self):
        word = encrypt_word('Documents')
        self.assertIsNone(odl.decrypt_word(word[:10] + '$$$$' + word[10:], KEY))

    def test_words_that_do_not_decrypt(self):
        self.assertIsNone(odl.decrypt_word('ThisIsAPlainWordThatIsLong', KEY))
        self.assertIsNone(odl.decrypt_word(encrypt_word('Documents'), None))
        self.assertIsNone(odl.decrypt_word(encrypt_word('Documents'), bytes(32)))
        self.assertIsNone(odl.decrypt_word(encrypt_word('Documents')[:21], KEY))

    def test_decode_text_with_key_and_map(self):
        stored = encrypt_word('Users') + '\\JokeYakLog.txt'
        self.assertEqual(odl.decode_text(stored, KEY, {'JokeYakLog': 'report'}),
                         ('Users\\report.txt', 2, 0))
        self.assertEqual(odl.decode_text('A\\JokeYakLog', None, {'JokeYakLog': 'report'}),
                         ('A\\report', 1, 0))
        self.assertEqual(odl.decode_text('A\\Other', None, {'JokeYakLog': 'report'}),
                         ('A\\Other', 0, 0))

    def test_replacement_from_a_repeated_token_counted(self):
        mapping = {'JokeYakLog': 'report', 'CatGemWolf': 'Pictures'}
        self.assertEqual(odl.decode_text('JokeYakLog\\CatGemWolf', None, mapping, {'CatGemWolf'}),
                         ('report\\Pictures', 2, 1))


class KeystoreAndMapTest(unittest.TestCase):
    def test_keystore_in_utf8_and_utf16(self):
        self.assertEqual(odl.read_keystore(keystore()), KEY)
        self.assertEqual(odl.read_keystore(keystore(encoding='utf-16-le')), KEY)

    def test_other_versions_and_key_sizes_not_read(self):
        self.assertIsNone(odl.read_keystore(keystore(version=2)))
        self.assertIsNone(odl.read_keystore(keystore(key=bytes(10))))

    def test_string_map_entries_and_continuation_lines(self):
        raw = ('Tok1\tnew\nTok1\told\ncontinued\nTok2\tline1\nline2\n').encode('utf-16-le')
        self.assertEqual(odl.read_string_map(raw),
                         [('Tok1', 'new'), ('Tok1', 'old\ncontinued'), ('Tok2', 'line1\nline2')])
        self.assertEqual(odl.read_string_map(b'\xef\xbb\xbfTok\ta\n'), [('Tok', 'a')])

    def test_first_entry_used_and_repeats_with_other_texts_listed(self):
        mapping, repeated = odl.string_map([[('Tok1', 'new'), ('Tok1', 'old'), ('Tok2', 'same')],
                                            [('Tok2', 'same'), ('Tok3', 'x')]])
        self.assertEqual(mapping, {'Tok1': 'new', 'Tok2': 'same', 'Tok3': 'x'})
        self.assertEqual(repeated, {'Tok1'})

    def test_logs_root(self):
        self.assertEqual(odl.logs_root('X/Users/u/AppData/Local/Microsoft/OneDrive/logs/Personal/a.odl'),
                         'X/Users/u/AppData/Local/Microsoft/OneDrive/logs')
        self.assertEqual(odl.logs_root('X/Users/u/Library/Logs/OneDrive/ListSync/Business1/a.odl'),
                         'X/Users/u/Library/Logs/OneDrive')
        self.assertEqual(odl.logs_root('X/elsewhere/a.odl'), 'X/elsewhere')


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        logs = self.root/'Users'/'tester'/'AppData'/'Local'/'Microsoft'/'OneDrive'/'logs'
        (logs/'Personal').mkdir(parents=True)
        (logs/'Business1').mkdir()
        self.files = [logs/'Personal'/'general.keystore', logs/'Personal'/'SyncEngine.odl',
                      logs/'Business1'/'ObfuscationStringMap.txt', logs/'Business1'/'Old.odl',
                      logs/'Business1'/'notes.txt']
        self.files[0].write_bytes(keystore())
        stored = 'C:\\' + encrypt_word('Users') + '\\tester'
        self.files[1].write_bytes(header(3, '25.1.0.1') + v3_record(
            TIME, data('a.cpp', 'A::Open', struct.pack('<I', 9) + text(stored)))
            + v3_record(TIME + 1, data('b.cpp', 'B::Tick', struct.pack('<Q', 5))))
        self.files[2].write_bytes('JokeYakLog\treport\nJokeYakLog\tolder\n'.encode('utf-16-le'))
        self.files[3].write_bytes(header(2, '18.1.0.1') + v2_record(
            TIME + 3, data('c.cpp', 'C::Save', text('D:\\JokeYakLog.txt') + text('GET'))))
        self.files[4].write_text('not a log', encoding='utf-8')

    def test_rows(self):
        headers, rows, sources = artifact.oneDriveLogs.__wrapped__(Context(self.root, self.files))
        self.assertEqual(headers[0], ('Time (UTC)', 'datetime'))
        when = datetime(2026, 1, 2, 3, 4, 5, 678000, tzinfo=timezone.utc)
        self.assertEqual(rows, [
            (when.replace(microsecond=681000), 'c.cpp', 'C::Save', 'D:\\report.txt | GET',
             'D:\\JokeYakLog.txt | GET', 1, 1, 1, 'Old.odl', 'Business1', '18.1.0.1', 'tester'),
            (when, 'a.cpp', 'A::Open', 'C:\\Users\\tester',
             'C:\\' + encrypt_word('Users') + '\\tester', 1, 0, 1, 'SyncEngine.odl', 'Personal',
             '25.1.0.1', 'tester'),
        ])
        self.assertEqual(sources.splitlines(), [str(self.files[3]), str(self.files[1])])
        relative = self.files[1].relative_to(self.root)
        self.assertIn(f'OneDrive Logs: {relative}: format version 3, 2 records, 1 with parameter '
                      f'text', self.logged)

    def test_keystore_copy_used_when_the_folder_has_none(self):
        folder = self.files[0].parent
        copy = folder/'EncryptionKeyStoreCopy'/'general.keystore'
        copy.parent.mkdir()
        copy.write_bytes(keystore())
        self.files[0].unlink()
        files = [copy, self.files[1]]
        _, rows, _ = artifact.oneDriveLogs.__wrapped__(Context(self.root, files))
        self.assertEqual([(row[3], row[5]) for row in rows], [('C:\\Users\\tester', 1)])
        copy.write_bytes(keystore(key=bytes(32)))
        self.files[0].write_bytes(keystore())
        _, rows, _ = artifact.oneDriveLogs.__wrapped__(Context(self.root, [copy] + self.files[:2]))
        self.assertEqual([(row[3], row[5]) for row in rows], [('C:\\Users\\tester', 1)])

    def test_run_log_names_zero_bytes_and_a_stopped_read(self):
        folder = self.files[0].parent
        padded, broken = folder/'Padded.odl', folder/'Broken.odlgz'
        record = v2_record(TIME, data('a.cpp', 'A::Run', text('abcd')))
        padded.write_bytes(header(2) + record + bytes(40))
        broken.write_bytes(header(2) + gzip.compress(record + b'\x01' + bytes(9))[:-8])
        artifact.oneDriveLogs.__wrapped__(Context(self.root, [padded, broken]))
        name = str(padded.relative_to(self.root))
        self.assertIn(f'OneDrive Logs: {name}: format version 2, 1 record, 1 with parameter text; '
                      f'its last 40 bytes are zeros', self.logged)
        name = str(broken.relative_to(self.root))
        self.assertIn(f'OneDrive Logs: {name}: format version 2, 1 record, 1 with parameter text; '
                      f'reading stopped at byte {len(record):,} of {len(record) + 10:,} of its '
                      f'records, where no further record header was found; its gzip stream ends '
                      f'before its end marker', self.logged)

    def test_nested_folder_and_upper_case_extension(self):
        nested = self.files[0].parent.parent/'ListSync'/'Business1'
        nested.mkdir(parents=True)
        log = nested/'Sync.ODLGZ'
        log.write_bytes(header(2) + gzip.compress(v2_record(TIME, data('d.cpp', 'D::Run', text('abcd')))))
        _, rows, _ = artifact.oneDriveLogs.__wrapped__(Context(self.root, [log]))
        self.assertEqual([(row[3], row[8], row[9]) for row in rows],
                         [('abcd', 'Sync.ODLGZ', 'ListSync/Business1')])

    def test_macos_logs_folder(self):
        folder = self.root/'Users'/'macuser'/'Library'/'Logs'/'OneDrive'/'Business1'
        folder.mkdir(parents=True)
        (folder/'general.keystore').write_bytes(keystore())
        stored = '/' + encrypt_word('Documents', encoding='utf-32-le') + '/a.txt'
        (folder/'SyncEngine.odlgz').write_bytes(header(3) + gzip.compress(
            v3_record(TIME, data('e.cpp', 'E::Run', text(stored)))))
        files = [folder/'general.keystore', folder/'SyncEngine.odlgz']
        _, rows, _ = artifact.oneDriveLogs.__wrapped__(Context(self.root, files))
        self.assertEqual([(row[3], row[5], row[9], row[11]) for row in rows],
                         [('/Documents/a.txt', 1, 'Business1', 'macuser')])

    def test_declared_paths_cover_both_platforms(self):
        patterns = artifact.__artifacts_v2__['oneDriveLogs']['paths']
        for path in ('p3/Users/u/AppData/Local/Microsoft/OneDrive/logs/Personal/SyncEngine.odlgz',
                     'p3/Users/u/AppData/Local/Microsoft/OneDrive/logs/Personal/general.keystore',
                     'vol/Users/u/Library/Logs/OneDrive/Business1/SyncEngine.odl',
                     'vol/Users/u/Library/Logs/OneDrive/Business1/general.keystore'):
            self.assertTrue(any(fnmatch.fnmatch(path, pattern) for pattern in patterns), path)

    def test_unreadable_log_reported(self):
        bad = self.files[0].parent/'Broken.odl'
        bad.write_bytes(b'garbage')
        _, rows, sources = artifact.oneDriveLogs.__wrapped__(Context(self.root, [bad]))
        self.assertEqual((rows, sources), ([], ''))
        self.assertEqual(len([line for line in self.logged if 'Broken.odl not read' in line]), 1)


if __name__ == '__main__':
    unittest.main()
