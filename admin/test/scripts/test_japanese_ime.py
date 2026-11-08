"""Pin scripts/artifacts/googleJapaneseInput.py and microsoftImeJapanese.py on bytes built here.

The key derivation is checked against the test vectors in google/mozc's own
base/encryptor_test.cc (c4ed4683fb400b240e81d0a3895d024e3e21325e); everything else is made-up
values in the layouts seen on windows11_arm_japanese_ime_known_20261108.
"""
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest import mock

from Crypto.Cipher import AES

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import googleJapaneseInput as gji  # pylint: disable=wrong-import-position
from scripts.artifacts import microsoftImeJapanese as msime  # pylint: disable=wrong-import-position

# (password, salt, iv, input, encrypted) from mozc base/encryptor_test.cc kTestData.
MOZC_VECTORS = (
    (b'foohoge', b'salt', b'1111111111111111', b'foo',
     b'\x27\x32\x66\x88\x82\x33\x78\x80\x58\x29\xBF\xDD\x46\x9A\xCC\x87'),
    (b'password', b'salt', b'1111111111111111', b'a',
     b'\x2A\xA1\x73\xB0\x91\x1C\x22\x40\x55\xDB\xAB\xC0\x77\x39\xE6\x57'),
    (b'password', b'salt', b'0123456789abcdef',
     b'dhoifasoifaoishdoifahsoifdhaoishfioashdoifahisodfhaioshdfioa',
     b'\x27\x92\xD1\x4F\xCE\x71\xFF\xA0\x9E\x52\xAB\x96\xB4\x5D\x1A\x2F'
     b'\xE0\xC7\xB3\x92\xD7\xB8\x29\xB0\xEF\xD3\x51\x9F\xBD\x87\xE0\xB4'
     b'\x0A\x06\xE0\x9A\x03\x72\x48\xB3\x8F\x9A\x5E\xAC\xCD\x5D\xB8\x0B'
     b'\x01\x1D\x2C\xD7\xAA\x55\x05\x0F\x4E\xD5\x73\xC0\xCB\xE2\x10\x69'),
)


def varint(value):
    out = b''
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out += bytes([byte | 0x80])
        else:
            return out + bytes([byte])


def field(number, value):
    if isinstance(value, int):
        return varint(number << 3) + varint(value)
    if isinstance(value, str):
        value = value.encode('utf-8')
    return varint(number << 3 | 2) + varint(len(value)) + value


def history_entry(key, value, freq, when, removed=False, description=''):
    body = field(1, key) + field(2, value) + field(3, freq) + field(4, when) + field(22, 7)
    body += field(24, b'\x0c\x09\x09\x06')       # inner_segment_boundary as seen (wire type 2)
    if removed:
        body += field(8, 1)
    if description:
        body += field(6, description)
    return field(6, body)


def encrypt_history(plain, password, salt=b'S' * 32):
    pad = 16 - len(plain) % 16
    body = AES.new(gji.derive_key(password, salt), AES.MODE_CBC, b'\x00' * 16).encrypt(plain + bytes([pad]) * pad)
    return salt + body


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


class MozcCryptoTest(unittest.TestCase):
    def test_key_derivation_matches_mozc_vectors(self):
        for password, salt, iv, clear, encrypted in MOZC_VECTORS:
            out = AES.new(gji.derive_key(password, salt), AES.MODE_CBC, iv).decrypt(encrypted)
            self.assertEqual(out[:-out[-1]], clear)

    def test_history_round_trip_and_wrong_password(self):
        plain = history_entry('とうきょう', '東京', 1, 1794166948)
        data = encrypt_history(plain, b'P' * 32)
        self.assertEqual(gji.decrypt_history(data, b'P' * 32), plain)
        self.assertIsNone(gji.decrypt_history(data, b'Q' * 32))
        self.assertIsNone(gji.decrypt_history(data[:40], b'P' * 32))


class MozcProtoTest(unittest.TestCase):
    def test_history_fields(self):
        plain = (history_entry('せんだい', '仙台', 2, 1794169266)
                 + history_entry('ふじさん', '富士山', 0, 1794169220, removed=True, description='desc'))
        entries = gji.parse_history(plain)
        self.assertEqual([(e['key'], e['value'], e['suggestion_freq'], e['last_access_time'], e['removed'],
                           e['description']) for e in entries],
                         [('せんだい', '仙台', 2, 1794169266, False, ''),
                          ('ふじさん', '富士山', 0, 1794169220, True, 'desc')])

    def test_truncated_message_raises(self):
        with self.assertRaises(gji.ProtoError):
            gji.proto_fields(field(6, 'abc')[:-1] + b'\x0a\xff')

    def test_user_dictionary(self):
        entry_a = field(1, 'けーでぃー') + field(2, 'KD語') + field(4, 'note') + field(5, 5)
        entry_b = field(1, 'よみ') + field(2, '語')          # no pos: proto default NOUN
        storage = field(2, field(1, 123) + field(3, 'User Dictionary 1') + field(4, entry_a) + field(4, entry_b))
        self.assertEqual(gji.parse_user_dictionary(storage), [
            ('User Dictionary 1', 'けーでぃー', 'KD語', 'PERSONAL_NAME (人名)', 'note', ''),
            ('User Dictionary 1', 'よみ', '語', 'NOUN (名詞)', '', '')])


class MozcArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = pathlib.Path(self.tmp.name)
        folder = self.root / 'Users' / 'lab' / 'AppData' / 'LocalLow' / 'Google' / 'Google Japanese Input'
        folder.mkdir(parents=True)
        self.history = folder / 'history.db'
        self.key = folder / 'encrypt_key.db'
        self.history.write_bytes(encrypt_history(history_entry('わたし', '私', 1, 1794166960), b'P' * 32))
        self.key.write_bytes(b'blob')

    def tearDown(self):
        self.tmp.cleanup()

    def run_history(self, files, password):
        blob = mock.Mock(mk_guid='g')
        blob.decrypt.return_value = password
        pool = mock.Mock()
        pool.get_key.return_value = b'k' * 64
        with mock.patch.object(gji, 'recover_os_keys', return_value=(pool, {})), \
                mock.patch.object(gji.dpapiprobe, 'DpapiBlob', return_value=blob), \
                mock.patch.object(gji, 'logfunc'):
            return gji.googleJapaneseInputHistory.__wrapped__(FakeContext(self.root, files))

    def test_decrypted_rows(self):
        _headers, rows, source = self.run_history([self.history, self.key], b'P' * 32)
        self.assertEqual(rows, [(utc(1794166960), 'わたし', '私', '', 1, '', 'decrypted', 'lab')])
        self.assertEqual(source, str(self.history))

    def test_status_rows(self):
        self.assertEqual(self.run_history([self.history], b'P' * 32)[1][0][-2],
                         'not decrypted: encrypt_key.db not found')
        self.assertEqual(self.run_history([self.history, self.key], None)[1][0][-2],
                         'not decrypted: no DPAPI key recovered for encrypt_key.db')
        self.assertEqual(self.run_history([self.history, self.key], b'P' * 31)[1][0][-2],
                         'not decrypted: encrypt_key.db did not hold a 32-byte password')
        self.assertEqual(self.run_history([self.history, self.key], b'Q' * 32)[1][0][-2],
                         'not decrypted: the key did not open history.db')


def ihds_record(ftime, segments):
    body = b''
    for reading, converted in segments:
        text = reading.encode('utf-16-le') + converted.encode('utf-16-le')
        body += struct.pack('<HBBI', 8 + len(text), len(reading), len(converted), 0x41202) + text
    return struct.pack('<QHHBBH', ftime, 16 + len(body), 16, 1, len(segments), 0) + body


def ihds_file(records):
    body = b''.join(records)
    size = 32 + len(body)
    return struct.pack('<QIIIIII', 134386421637474865, size, 1, len(records), 32, 0, size) + body


class JpnIhdsTest(unittest.TestCase):
    def test_walk(self):
        data = ihds_file([ihds_record(134386420575730000, [('ひろしま', '広島')]),
                          ihds_record(134386421263360000, [('きょう', '今日'), ('は', ''), ('てんき', '天気')])])
        records, problems = msime.parse_ihds(data)
        self.assertEqual(problems, [])
        self.assertEqual([r[1] for r in records], [[('ひろしま', '広島')],
                                                   [('きょう', '今日'), ('は', ''), ('てんき', '天気')]])

    def test_truncated_record_is_reported(self):
        data = ihds_file([ihds_record(1, [('あ', '亜')]), ihds_record(2, [('い', '伊')])])
        records, problems = msime.parse_ihds(data[:-4])
        self.assertEqual(len(records), 1)
        self.assertEqual(len(problems), 2)

    def test_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'Users', 'lab', 'AppData', 'Roaming', 'Microsoft', 'InputMethod', 'Shared')
            folder.mkdir(parents=True)
            path = folder / 'JpnIHDS.dat'
            path.write_bytes(ihds_file([ihds_record(134386421263360000, [('きょう', '今日'), ('は', '')])]))
            _h, rows, source = msime.microsoftImeJapaneseHistory.__wrapped__(FakeContext(pathlib.Path(tmp), [path]))
        self.assertEqual(rows[0][1:], ('きょうは', '今日は', 'きょう → 今日 | は', 'lab'))
        self.assertEqual(rows[0][0], datetime(2026, 11, 8, 20, 8, 46, 336000, tzinfo=timezone.utc))
        self.assertEqual(source, str(path))


XML = ('<?xml version="1.0" encoding="UTF-8"?><ddds version="1.0"><head><timestamp>1</timestamp></head><body>'
       '<History><HistorySentence t="134386421163047423" lang="0x411" is="1">'
       '<HRWord disp="今日" POS="1"><reading value="きょう"></reading></HRWord>'
       '<HRWord disp="は" POS="2"><reading value="は"></reading></HRWord>'
       '</HistorySentence></History></body></ddds>').encode('utf-8')


def ddds_file(xml, chunk=None):
    chunk = chunk or len(xml)
    blocks, done = b'', b''
    for start in range(0, len(xml), chunk):
        piece = xml[start:start + chunk]
        packer = zlib.compressobj(9, zlib.DEFLATED, -15, zdict=done[-32768:]) if done else \
            zlib.compressobj(9, zlib.DEFLATED, -15)
        block = b'CK' + packer.compress(piece) + packer.flush()
        blocks += struct.pack('<I', len(block)) + block
        done += piece
    return struct.pack('<IHHQQ', 0xC0E5510A, 24, 0, len(xml), len(xml)) + blocks


class JpnDddsTest(unittest.TestCase):
    def test_single_and_multi_block(self):
        self.assertEqual(msime.ddds_xml(ddds_file(XML)), XML)
        self.assertEqual(msime.ddds_xml(ddds_file(XML, chunk=100)), XML)

    def test_size_mismatch_is_refused(self):
        data = bytearray(ddds_file(XML))
        struct.pack_into('<Q', data, 8, len(XML) + 1)
        with self.assertRaises(msime.FormatError):
            msime.ddds_xml(bytes(data))

    def test_sentences(self):
        self.assertEqual(msime.parse_ddds(XML), [(134386421163047423, [('今日', 'きょう'), ('は', 'は')])])

    def test_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'Users', 'lab', 'AppData', 'Local', 'Microsoft', 'input', 'neutral')
            folder.mkdir(parents=True)
            path = folder / 'JpnDdds.dat'
            path.write_bytes(ddds_file(XML))
            _h, rows, _s = msime.microsoftImeJapaneseDdds.__wrapped__(FakeContext(pathlib.Path(tmp), [path]))
        self.assertEqual(rows[0][1:], ('今日は', 'きょうは', '今日 | は', 'lab'))
        self.assertEqual(rows[0][0], datetime(2026, 11, 8, 20, 8, 36, 304742, tzinfo=timezone.utc))


if __name__ == '__main__':
    unittest.main()
