"""Pin scripts/emule.py and the eMule artifacts.

The fixtures are files eMule 0.72a wrote on windows11_arm_emule_known_20261108 (test file names, a never-connected
client), so the readers are checked against eMule's own bytes. The other records are built here following
KnownFile.cpp and PartFile.cpp, with made-up values.
"""
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import emule  # pylint: disable=wrong-import-position
from scripts.artifacts import emule as emule_artifacts  # pylint: disable=wrong-import-position

KNOWN_MET = bytes.fromhex(
    "0f03000000fc1ef06a4ce32b2713aa112a8037bcef449acd5b0000060000000201000111006b642d656d756c652d6265"
    "74612e62696e03010002c0d401000201002720005250475654465144525745543256554b555855594a52593342474a32"
    "5544434f03010034bc85f06a07010035160000008bcd5996038d893d568aa5e984c71b0993aa0c4e0000030100190500"
    "0000fc1ef06a1536d397d53272b23198ad29bdb1c418020075648fde2f9b54228cb224f7a7b3eaef18eaffd934a99d9b"
    "b3203ed0e77ab25b060000000201000112006b642d656d756c652d67616d6d612e62696e030100028883940002010027"
    "2000554b574a335a584142544956454d4d5a454b42514e49334745504d4f574f364c03010034bc85f06a070100353e00"
    "0000a2ac9de6e00cd1523199228306a36623d8eb3bcb020002220d88bb8481d20ab6387735a46504edf773a681fcf4db"
    "8a1705e97ed33f052b7473d4967b6b4a0301001905000000fc1ef06ab2ce0f8d83dd00aa8f5cc8a60e8e18a500000600"
    "00000201000112006b642d656d756c652d616c7068612e74787403010002a00f0000020100272000345a41325a4f5436"
    "4f444141554846465952324b53454d4236523637375a345903010034bc85f06a0701003516000000e641acba7e70c00a"
    "1ca5c474a91181f47dffe79800000301001905000000"
)
PART_MET = bytes.fromhex(
    "e03284f06a930345397f8aa859f065d372337155c80000070000000201000113006b642d656d756c652d77616e746564"
    "2e62696e0301000250c30000030100180500000003010019050000000201001208003030312e70617274030200093000"
    "0000000302000a3050c30000"
)
SEARCH = bytes.fromhex(
    "fffe6b0064002d0065006d0075006c0065002d007300650061007200630068002d007400650072006d000d000a00"
)
PREFS_DAT = bytes.fromhex(
    "1497c2eca9ca0ea13d2743fdb722846fc02c00000000000000010000000000000000000000ffffffffffffffff000000"
    "0000000000150300004e020000"
)
SHAREDDIR = bytes.fromhex(
    "fffe43003a005c006b0064005f0065006d0075006c0065005c00730068006100720065005c000d000a00"
)
DOWNLOADS = bytes.fromhex(
    "fffe44006100740065003a00200020002000200020002000310031002f0038002f003200300032003600200039003a00"
    "320032003a0035003400200041004d000d000a004400690072006500630074006f00720079003a00200043003a005c00"
    "6b0064005f0065006d0075006c0065005c00540065006d0070005c000d000a000d000a00500061007200740020006600"
    "69006c00650009006500440032004b0020006c0069006e006b000d000a002d002d002d002d002d002d002d002d002d00"
    "2d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d00"
    "2d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d00"
    "2d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d002d000d00"
    "0a003000300031002e00700061007200740009006500640032006b003a002f002f007c00660069006c0065007c006b00"
    "64002d0065006d0075006c0065002d00770061006e007400650064002e00620069006e007c0035003000300030003000"
    "7c0039003300300033003400350033003900370046003800410041003800350039004600300036003500440033003700"
    "3200330033003700310035003500430038007c002f000d000a00"
)


def tag(name, tag_type, payload):
    """A tag with a one-byte name, the old long form (type, uint16 length 1, name)."""
    return bytes([tag_type]) + struct.pack('<H', 1) + bytes([name]) + payload


def str_tag(name, value):
    raw = value.encode('utf-8')
    return tag(name, emule.TAGTYPE_STRING, struct.pack('<H', len(raw)) + raw)


def u32_tag(name, value):
    return tag(name, emule.TAGTYPE_UINT32, struct.pack('<I', value))


def known_record(date, file_hash, tags):
    return struct.pack('<I', date) + file_hash + struct.pack('<H', 0) + struct.pack('<I', len(tags)) + b''.join(tags)


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def t(value):
    return datetime.fromtimestamp(value, timezone.utc)


class ReaderTest(unittest.TestCase):
    def test_known_met_from_emule(self):
        rows = list(emule.read_known_met(KNOWN_MET))
        self.assertEqual([r['name'] for r in rows], ['kd-emule-beta.bin', 'kd-emule-gamma.bin', 'kd-emule-alpha.txt'])
        self.assertEqual([r['size'] for r in rows], [120000, 9733000, 4000])
        # Hashes computed from the shared files with an MD4 checked against RFC 1320.
        self.assertEqual(rows[2]['hash'].hex(), 'b2ce0f8d83dd00aa8f5cc8a60e8e18a5')
        self.assertEqual(rows[1]['hash'].hex(), '1536d397d53272b23198ad29bdb1c418')
        self.assertEqual({r['last_shared'] for r in rows}, {1794147772})
        self.assertEqual({r['modified'] for r in rows}, {1794121468})
        self.assertEqual({r['transferred'] for r in rows}, {None})

    def test_known_met_upload_counts_and_bom_name(self):
        name = b'\xef\xbb\xbf' + 'caf\u00e9.bin'.encode('utf-8')
        record = known_record(1700000000, b'\x11' * 16, [
            tag(emule.FT_FILENAME, emule.TAGTYPE_STRING, struct.pack('<H', len(name)) + name),
            bytes([0x80 | emule.TAGTYPE_UINT64, emule.FT_FILESIZE]) + struct.pack('<Q', 5_000_000_000),
            u32_tag(emule.FT_ATTRANSFERRED, 5), u32_tag(emule.FT_ATTRANSFERREDHI, 1),
            u32_tag(emule.FT_ATREQUESTED, 7), u32_tag(emule.FT_ATACCEPTED, 3),
            bytes([0x80 | emule.TAGTYPE_STR1 + 2, 0x7F]) + b'abc'])
        data = bytes([emule.MET_HEADER_I64TAGS]) + struct.pack('<I', 1) + record
        row = next(emule.read_known_met(data))
        self.assertEqual(row['name'], 'caf\u00e9.bin')
        self.assertEqual(row['size'], 5_000_000_000)
        self.assertEqual(row['transferred'], (1 << 32) | 5)
        self.assertEqual((row['requests'], row['accepts']), (7, 3))

    def test_known_met_refuses_other_headers_and_unknown_tag_types(self):
        with self.assertRaises(emule.EmuleFormatError):
            list(emule.read_known_met(b'\xe0' + KNOWN_MET[1:]))
        record = known_record(1, b'\x00' * 16, [tag(0x55, 0x0A, b'')])
        with self.assertRaises(emule.EmuleFormatError):
            list(emule.read_known_met(bytes([emule.MET_HEADER]) + struct.pack('<I', 1) + record))
        with self.assertRaises(emule.EmuleFormatError):
            list(emule.read_known_met(KNOWN_MET[:200]))

    def test_part_met_from_emule(self):
        row = emule.read_part_met(PART_MET)
        self.assertEqual(row['name'], 'kd-emule-wanted.bin')
        self.assertEqual(row['size'], 50000)
        self.assertEqual(row['hash'].hex(), '930345397f8aa859f065d372337155c8')
        self.assertEqual(row['modified'], 1794147378)
        self.assertIsNone(row['transferred'])
        self.assertIsNone(row['status'])
        self.assertEqual(row['gaps'], 1)

    def test_part_met_paused_and_older_layouts(self):
        tags = [str_tag(emule.FT_FILENAME, 'x.bin'), u32_tag(emule.FT_FILESIZE, 1000),
                u32_tag(emule.FT_TRANSFERRED, 400), u32_tag(emule.FT_STATUS, 1), u32_tag(emule.FT_CATEGORY, 2),
                u32_tag(emule.FT_LASTSEENCOMPLETE, 1700000500)]
        data = bytes([emule.PARTFILE_VERSION]) + known_record(1700000000, b'\x22' * 16, tags)
        row = emule.read_part_met(data)
        self.assertEqual((row['transferred'], row['status'], row['category'], row['last_seen_complete']),
                         (400, 1, 2, 1700000500))
        for version in (0xE1, 83):
            with self.assertRaises(emule.EmuleFormatError):
                emule.read_part_met(bytes([version]) + PART_MET[1:])

    def test_text_files(self):
        self.assertEqual(emule.read_utf16_lines(SEARCH), ['kd-emule-search-term'])
        self.assertEqual(emule.read_utf16_lines(SHAREDDIR, allow_ansi=True), ['C:\\kd_emule\\share\\'])
        self.assertEqual(emule.read_utf16_lines(b'C:\\old\\share\\\r\n', allow_ansi=True), ['C:\\old\\share\\'])
        with self.assertRaises(emule.EmuleFormatError):
            emule.read_utf16_lines(b'kd-term\r\n')
        written, directory, entries = emule.read_download_overview(DOWNLOADS)
        self.assertEqual((written, directory), ('11/8/2026 9:22:54 AM', 'C:\\kd_emule\\Temp\\'))
        self.assertEqual(entries[0][0], '001.part')
        self.assertEqual(emule.parse_file_link(entries[0][1]),
                         ('kd-emule-wanted.bin', 50000, '930345397f8aa859f065d372337155c8'))

    def test_preferences_dat(self):
        self.assertEqual(emule.read_preferences_dat(PREFS_DAT), (0x14, '97c2eca9ca0ea13d2743fdb722846fc0', True))
        version, user_hash, marked = emule.read_preferences_dat(b'\x13' + b'\x01' * 16)
        self.assertEqual((version, user_hash, marked), (0x13, '01' * 16, False))
        with self.assertRaises(emule.EmuleFormatError):
            emule.read_preferences_dat(b'\x14' * 10)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = pathlib.Path(self.tmp.name)
        self.files = []
        for user, temp in (('lab', 'C:\\kd\\Temp\\'), ('other', 'D:\\x\\Temp\\')):
            config = root / 'Users' / user / 'AppData' / 'Local' / 'eMule' / 'config'
            config.mkdir(parents=True)
            for name, data in (('known.met', KNOWN_MET), ('AC_SearchStrings.dat', SEARCH),
                               ('preferences.dat', PREFS_DAT), ('shareddir.dat', SHAREDDIR),
                               ('downloads.txt', DOWNLOADS)):
                (config / name).write_bytes(data)
            (config / 'preferences.ini').write_text(f'[eMule]\nNick=n-{user}\nTempDir={temp}\nTempDirs=\n'
                                                    'ProxyPassword=not-reported\n', encoding='utf-8')
            self.files += [str(p) for p in config.iterdir()]
        for folder, name in (('kd/Temp', '001.part.met'), ('x/Temp', '002.part.met'), ('elsewhere', '003.part.met')):
            (root / folder).mkdir(parents=True)
            (root / folder / name).write_bytes(PART_MET)
            self.files.append(str(root / folder / name))
        self.context = FakeContext(self.tmp.name, self.files)

    def tearDown(self):
        self.tmp.cleanup()

    def test_known_files(self):
        with mock.patch.object(emule_artifacts, 'logfunc'):
            headers, rows, sources = emule_artifacts.emuleKnownFiles.__wrapped__(self.context)
        self.assertEqual(len(rows), 6)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][0], t(1794147772))
        self.assertEqual({r[-1] for r in rows}, {'lab', 'other'})
        self.assertEqual(len(sources.split('\n')), 2)

    def test_downloads_link_to_the_profile_naming_the_folder(self):
        with mock.patch.object(emule_artifacts, 'logfunc'):
            headers, rows, _ = emule_artifacts.emuleDownloads.__wrapped__(self.context)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual({r[8]: r[9] for r in rows}, {'001.part.met': 'lab', '002.part.met': 'other', '003.part.met': ''})
        self.assertEqual(rows[0][5:8], (0, 'No', 0))

    def test_list_search_and_settings(self):
        with mock.patch.object(emule_artifacts, 'logfunc'):
            _, rows, _ = emule_artifacts.emuleDownloadList.__wrapped__(self.context)
            self.assertEqual(len(rows), 2)
            _, rows, _ = emule_artifacts.emuleSearchHistory.__wrapped__(self.context)
            self.assertEqual(rows[0][:2], (1, 'kd-emule-search-term'))
            _, rows, _ = emule_artifacts.emuleSettings.__wrapped__(self.context)
        lab = [r[:2] for r in rows if r[-1] == 'lab']
        self.assertEqual(lab, [('User Hash', '97c2eca9ca0ea13d2743fdb722846fc0'), ('Nickname', 'n-lab'),
                               ('Temp Folder', 'C:\\kd\\Temp\\'), ('Shared Folder', 'C:\\kd_emule\\share\\')])
        self.assertNotIn('not-reported', str(rows))


if __name__ == '__main__':
    unittest.main()
