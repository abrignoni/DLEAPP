"""Pin the Store reading in scripts/artifacts/windowsDefenderHistoryStore.py.

Every file below is built by the test from the layout mpdbx documents (docs/design.md at
commit 40f926f05021d878207cd635451c00166b1132ed): a 60-byte RC4-encrypted header holding two
magic values and two section lengths, then two RC4-encrypted sections, the second a list of
typed properties. No value comes from a real device. Expected values are written out, never
read back from the code.
"""
import fnmatch
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mpenginedb import KEY, rc4_keystream  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsDefenderHistoryStore as artifact  # pylint: disable=wrong-import-position

PERSIST_ID = '0123456789ABCDEF0123456789ABCDEF'
# 2026-01-02 03:04:05.123456 UTC as a FILETIME.
START = 134117966451234560
WHEN = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)


def encrypt(data):
    stream = rc4_keystream(KEY, len(data))
    return bytes(a ^ b for a, b in zip(data, stream))


def name(text):
    raw = (text + '\0').encode('utf-16-le')
    return struct.pack('<I', len(raw)) + raw


def text(label, value):
    raw = (value + '\0').encode('utf-16-le')
    return name(label) + struct.pack('<II', 6, len(raw)) + raw


def number(label, value):
    return name(label) + struct.pack('<II', 3, value)


def flag(label, value):
    return name(label) + struct.pack('<I', 5) + bytes([value])


def fixed(label):
    return name(label) + struct.pack('<I', 9) + bytes(8)


def blob(label, data):
    return name(label) + struct.pack('<II', 8, len(data)) + data


def store(properties, first=b'', magic_two=0x02C5E8DB):
    body = b''.join(properties)
    section = struct.pack('<I', len(body)) + body
    header = bytearray(0x3C)
    struct.pack_into('<I', header, 0, 0x01C5E8DB)
    struct.pack_into('<II', header, 0x28, len(first), len(section))
    struct.pack_into('<I', header, 0x38, magic_two)
    return encrypt(bytes(header)) + encrypt(first) + encrypt(section)


def full_store():
    return store([
        text('CONTEXT_DATA_FILEPATH', '\\Device\\HarddiskVolume9\\Data'),
        text('CONTEXT_DATA_FILENAME', 'sample.bin'),
        text('CONTEXT_DATA_PROCESSNAME', 'tool.exe'),
        text('CONTEXT_DATA_PROCESSDEVICEPATH', '\\Device\\HarddiskVolume9\\Tools'),
        number('CONTEXT_DATA_PROCESS_ID', 4242),
        text('CONTEXT_DATA_PROCESS_PPID', f'pid:4242,ProcessStart:{START}'),
        number('CONTEXT_DATA_SCANREASON', 7),
        flag('CONTEXT_DATA_NEWLYCREATEDHINT', 1),
        flag('CONTEXT_DATA_HAS_MOTW_ADS', 0),
        fixed('CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT'),
        number('CONTEXT_DATA_FILE_ATTRIBUTES', 32),
        blob('Id', bytes.fromhex(PERSIST_ID)),
    ])


class FakeContext:
    def __init__(self, paths):
        self.paths = paths

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return str(path).split('/extraction', 1)[-1] if '/extraction' in str(path) else str(path)


class ReadStoreTest(unittest.TestCase):
    def test_every_property_is_read_in_order(self):
        properties, note = artifact.read_store(full_store())
        self.assertEqual(note, '')
        self.assertEqual([p[0] for p in properties], [
            'CONTEXT_DATA_FILEPATH', 'CONTEXT_DATA_FILENAME', 'CONTEXT_DATA_PROCESSNAME',
            'CONTEXT_DATA_PROCESSDEVICEPATH', 'CONTEXT_DATA_PROCESS_ID',
            'CONTEXT_DATA_PROCESS_PPID', 'CONTEXT_DATA_SCANREASON',
            'CONTEXT_DATA_NEWLYCREATEDHINT', 'CONTEXT_DATA_HAS_MOTW_ADS',
            'CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT', 'CONTEXT_DATA_FILE_ATTRIBUTES', 'Id'])
        self.assertEqual(properties[0][2], '\\Device\\HarddiskVolume9\\Data')
        self.assertEqual(properties[4][2], 4242)

    def test_wrong_magic_is_reported_not_read(self):
        properties, note = artifact.read_store(store([number('A', 1)], magic_two=0x12345678))
        self.assertEqual(properties, [])
        self.assertIn('magic', note)

    def test_sections_that_do_not_fit_the_file_are_reported(self):
        properties, note = artifact.read_store(full_store() + b'\0')
        self.assertEqual(properties, [])
        self.assertIn('do not fit the file size', note)

    def test_short_file_is_reported(self):
        properties, note = artifact.read_store(b'\0' * 10)
        self.assertEqual(properties, [])
        self.assertIn('shorter than the 60-byte header', note)

    def test_property_running_past_the_section_keeps_the_ones_before_it(self):
        good = number('CONTEXT_DATA_SCANREASON', 7)
        bad = name('CONTEXT_DATA_FILEPATH') + struct.pack('<II', 6, 9999)
        properties, note = artifact.read_store(store([good, bad]))
        self.assertEqual([p[0] for p in properties], ['CONTEXT_DATA_SCANREASON'])
        self.assertIn('after 1 properties', note)

    def test_truncated_fixed_property_is_reported(self):
        cut = name('CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT') + struct.pack('<I', 9) + bytes(4)
        properties, note = artifact.read_store(store([number('A', 1), cut]))
        self.assertEqual([p[0] for p in properties], ['A'])
        self.assertIn('after 1 properties', note)

    def test_a_non_empty_first_section_is_named_not_read(self):
        _, note = artifact.read_store(store([number('A', 1)], first=b'\x01\x02\x03'))
        self.assertIn('first section holds 3 bytes, not read', note)


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, files):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder) / 'extraction' / (
                'ProgramData/Microsoft/Windows Defender/Scans/History/Store')
            root.mkdir(parents=True)
            paths = []
            for file_name, data in files.items():
                path = root / file_name
                path.write_bytes(data)
                paths.append(path)
            return artifact.defenderHistoryStore.__wrapped__(FakeContext(paths)) \
                if hasattr(artifact.defenderHistoryStore, '__wrapped__') else None

    def test_row_columns(self):
        with patch.object(artifact, 'logfunc'):
            headers, rows, _ = self.run_artifact({PERSIST_ID: full_store()})
        self.assertEqual(len(rows), 1)
        row = dict(zip([h if isinstance(h, str) else h[0] for h in headers], rows[0]))
        self.assertEqual(row['Process Start (UTC)'], WHEN)
        self.assertEqual(row['Persist ID'], PERSIST_ID)
        self.assertEqual(row['Scanned File Name'], 'sample.bin')
        self.assertEqual(row['Process Name'], 'tool.exe')
        self.assertEqual(row['Process ID'], 4242)
        self.assertEqual(row['Scan Reason (as stored)'], 7)
        self.assertEqual(row['Newly Created Hint'], 'Yes')
        self.assertEqual(row['Has MOTW ADS'], 'No')
        self.assertEqual(row['Other Properties'],
                         'CONTEXT_DATA_AMSI_UAC_REQUEST_CONTEXT=0000000000000000\n'
                         'CONTEXT_DATA_FILE_ATTRIBUTES=32')
        self.assertEqual(row['Read Note'], '')

    def test_a_file_whose_name_is_not_a_persist_id_is_not_read(self):
        with patch.object(artifact, 'logfunc'):
            _, rows, _ = self.run_artifact({'not-a-persist-id': full_store()})
        self.assertEqual(rows, [])

    def test_id_property_that_differs_from_the_file_name_is_noted(self):
        data = store([blob('Id', bytes(16))])
        with patch.object(artifact, 'logfunc'):
            headers, rows, _ = self.run_artifact({PERSIST_ID: data})
        row = dict(zip([h if isinstance(h, str) else h[0] for h in headers], rows[0]))
        self.assertIn('Id property differs from the file name', row['Read Note'])
        self.assertEqual(row['Other Properties'], 'Id=' + '00' * 16)

    def test_declared_path_matches_the_store_folder_only(self):
        pattern = artifact.__artifacts_v2__['defenderHistoryStore']['paths'][0]
        base = 'C/ProgramData/Microsoft/Windows Defender/Scans/History/'
        self.assertTrue(fnmatch.fnmatch(base + 'Store/' + PERSIST_ID, pattern))
        self.assertFalse(fnmatch.fnmatch(base + 'Results/Quick/' + PERSIST_ID, pattern))


if __name__ == '__main__':
    unittest.main()
