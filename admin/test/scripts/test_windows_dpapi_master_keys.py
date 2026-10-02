"""Pin the rows in scripts/artifacts/windowsDpapiMasterKeys.py.

The files are built here byte by byte (made-up GUIDs and values); the expected rows are written out.
"""
import datetime
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDpapiMasterKeys as keys  # pylint: disable=wrong-import-position
from scripts.search_files import FileInfo  # pylint: disable=wrong-import-position

GUID_A = '0a1b2c3d-1111-2222-3333-444455556666'
GUID_B = 'ffeeddcc-aaaa-bbbb-cccc-0123456789ab'
GUID_C = '11111111-2222-3333-4444-555555555555'
UTC = datetime.timezone.utc


def key_file(name, sizes=(176, 144, 20, 0), flags=5, count=8000, hash_alg=0x800e, cipher_alg=0x6610, version=2):
    header = struct.pack('<III', version, 0, 0) + name.encode('utf-16-le').ljust(72, b'\x00') + struct.pack('<III', 0, 0, flags)
    first = struct.pack('<I', 2) + bytes(range(16)) + struct.pack('<III', count, hash_alg, cipher_alg)
    body = first.ljust(sizes[0], b'\x07')[:sizes[0]] + b'\x08' * sizes[1] + b'\x09' * sizes[2] + b'\x0a' * sizes[3]
    return header + struct.pack('<4Q', *sizes) + body


def guid_bytes(text):
    first, second, third, fourth, fifth = text.split('-')
    return struct.pack('<IHH', int(first, 16), int(second, 16), int(third, 16)) + bytes.fromhex(fourth + fifth)


def preferred_file(name, when):
    ticks = int((when - datetime.datetime(1601, 1, 1, tzinfo=UTC)).total_seconds()) * 10_000_000
    return guid_bytes(name) + struct.pack('<Q', ticks)


class ImageSeeker:
    """A raw image seeker: it lists streams, and its file times are the evidence's."""

    stream_list = ()

    def __init__(self, file_infos):
        self.file_infos = file_infos


class FolderSeeker:
    def __init__(self, file_infos):
        self.file_infos = file_infos


class FakeContext:
    def __init__(self, root, files, seeker):
        self.root = root
        self.files = files
        self.seeker = seeker

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()

    def get_seeker(self):
        return self.seeker


class FieldTest(unittest.TestCase):
    def test_the_header_fields_and_the_first_section_fields_of_a_key_file(self):
        fields, problem = keys.key_fields(key_file(GUID_A), GUID_A)
        self.assertEqual(fields, (2, 5, 8000, '0x0000800e', '0x00006610', '176, 144, 20, 0'))
        self.assertEqual(problem, '')

    def test_a_key_file_with_a_fourth_section_and_other_algorithms(self):
        raw = key_file(GUID_B, sizes=(136, 104, 0, 372), flags=0x10005, count=18000, hash_alg=0x8009, cipher_alg=0x66ab)
        self.assertEqual(keys.key_fields(raw, GUID_B.upper()), ((2, 65541, 18000, '0x00008009', '0x000066ab', '136, 104, 0, 372'), ''))

    def test_a_file_shorter_than_its_header_has_blank_fields(self):
        self.assertEqual(keys.key_fields(key_file(GUID_A)[:127], GUID_A), (('',) * 6, 'is shorter than the 128 byte header'))

    def test_a_stored_name_that_is_not_the_file_name_and_sizes_that_do_not_add_up_are_named(self):
        fields, problem = keys.key_fields(key_file(GUID_A), GUID_B)
        self.assertEqual((fields[0], problem), (2, 'stores a GUID that is not its name'))
        fields, problem = keys.key_fields(key_file(GUID_A) + b'\x00', GUID_A)
        self.assertEqual((fields[5], problem), ('176, 144, 20, 0', 'stores section sizes that do not add up to its size'))
        self.assertEqual(keys.key_fields(key_file(GUID_A) + b'\x00', GUID_B)[1], 'stores a GUID that is not its name')

    def test_a_first_section_too_small_for_the_count_and_the_algorithms_leaves_them_blank(self):
        raw = key_file(GUID_A, sizes=(31, 0, 0, 0))
        self.assertEqual(keys.key_fields(raw[:128 + 31], GUID_A)[0], (2, 5, '', '', '', '31, 0, 0, 0'))
        self.assertEqual(keys.key_fields(key_file(GUID_A, sizes=(31, 40, 0, 0)), GUID_A), ((2, 5, '', '', '', '31, 40, 0, 0'), ''))
        cut = keys.key_fields(key_file(GUID_A)[:150], GUID_A)
        self.assertEqual(cut, ((2, 5, '', '', '', '176, 144, 20, 0'), 'stores section sizes that do not add up to its size'))
        self.assertEqual(keys.key_fields(key_file(GUID_A, sizes=(32, 0, 0, 0)), GUID_A)[0][2:5], (8000, '0x0000800e', '0x00006610'))

    def test_a_preferred_file_gives_a_guid_and_a_time(self):
        when = datetime.datetime(2023, 4, 3, 17, 29, 35, tzinfo=UTC)
        self.assertEqual(keys.preferred_key(preferred_file(GUID_B, when)), (GUID_B, when))
        self.assertIsNone(keys.preferred_key(preferred_file(GUID_B, when)[:23]))
        self.assertEqual(keys.guid_text(guid_bytes(GUID_A)), GUID_A)


class ArtifactTest(unittest.TestCase):
    def run_on(self, seeker_class):
        with tempfile.TemporaryDirectory() as tmp:
            user = pathlib.Path(tmp, 'vol', 'Users', 'lab', 'AppData', 'Roaming', 'Microsoft', 'Protect', 'S-1-5-21-1-2-3-1001')
            system = pathlib.Path(tmp, 'vol', 'Windows', 'System32', 'Microsoft', 'Protect', 'S-1-5-18', 'User')
            user.mkdir(parents=True)
            system.mkdir(parents=True)
            when = datetime.datetime(2023, 4, 3, 17, 29, 35, tzinfo=UTC)
            made = {user / GUID_A: key_file(GUID_A), user / GUID_B.upper(): key_file(GUID_B.upper(), flags=6, count=1),
                    user / 'Preferred': preferred_file(GUID_B, when), user / 'CREDHIST': b'x' * 24,
                    system / GUID_C: key_file(GUID_C)[:100], system / 'Diagnostic.log': b'log', user / 'BK-LAB': b'y' * 900}
            for path, raw in made.items():
                path.write_bytes(raw)
            (system / GUID_A).mkdir()
            infos = {str(user / GUID_A): FileInfo('vol/a', 1676935750.5, 1677098865.25),
                     str(user / GUID_B.upper()): FileInfo('vol/b', 1680542975.0, 1680542975.0)}
            files = [str(system / GUID_A), str(system)] + [str(path) for path in reversed(list(made))] + [str(user), str(user / GUID_A)]
            context = FakeContext(tmp, files, seeker_class(infos))
            with mock.patch.object(keys, 'logfunc') as log:
                headers, rows, source = keys.dpapiMasterKeyFiles.__wrapped__(context)
            return headers, rows, source, [call.args[0] for call in log.call_args_list], (user, system, when)

    def test_an_image_gives_one_row_per_key_file_with_its_times_and_the_preferred_file(self):
        headers, rows, source, logged, (user, system, when) = self.run_on(ImageSeeker)
        folder = 'vol/Users/lab/AppData/Roaming/Microsoft/Protect/S-1-5-21-1-2-3-1001'
        created = datetime.datetime.fromtimestamp(1676935750.5, UTC)
        modified = datetime.datetime.fromtimestamp(1677098865.25, UTC)
        made = datetime.datetime.fromtimestamp(1680542975.0, UTC)
        self.assertEqual(rows, [
            (created, modified, '', GUID_A, folder, 'No', 2, 5, 8000, '0x0000800e', '0x00006610', '176, 144, 20, 0'),
            (made, made, when, GUID_B.upper(), folder, 'Yes', 2, 6, 1, '0x0000800e', '0x00006610', '176, 144, 20, 0'),
            ('', '', '', GUID_C, 'vol/Windows/System32/Microsoft/Protect/S-1-5-18/User', '', '', '', '', '', '', ''),
        ])
        self.assertEqual(headers, (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), ('Preferred File Time (UTC)', 'datetime'),
                                   'Master Key GUID', 'Folder', 'Preferred', 'Version', 'Flags', 'Iteration Count',
                                   'Hash Algorithm ID', 'Cipher Algorithm ID', 'Section Sizes'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(source.split('\n'), [str(user / GUID_A), str(user / GUID_B.upper()), str(user / 'Preferred'), str(system / GUID_C)])
        self.assertEqual(logged, ['DPAPI Master Key Files: vol/Windows/System32/Microsoft/Protect/S-1-5-18/User/'
                                  + GUID_C + ' is shorter than the 128 byte header'])

    def test_a_folder_input_gives_no_file_times(self):
        _headers, rows, _source, _logged, _made = self.run_on(FolderSeeker)
        self.assertEqual([row[:2] for row in rows], [('', '')] * 3)
        self.assertEqual([row[5] for row in rows], ['No', 'Yes', ''])

    def test_a_preferred_file_that_is_too_short_is_logged_and_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'vol', 'Windows', 'System32', 'Microsoft', 'Protect', 'S-1-5-18')
            folder.mkdir(parents=True)
            (folder / GUID_A).write_bytes(key_file(GUID_A, flags=6))
            (folder / 'preferred').write_bytes(b'\x01' * 23)
            context = FakeContext(tmp, [str(folder / GUID_A), str(folder / 'preferred')], ImageSeeker({}))
            with mock.patch.object(keys, 'logfunc') as log:
                _headers, rows, source = keys.dpapiMasterKeyFiles.__wrapped__(context)
        self.assertEqual([(row[0], row[2], row[5], row[7]) for row in rows], [('', '', '', 6)])
        self.assertEqual(log.call_args_list, [mock.call('DPAPI Master Key Files: vol/Windows/System32/Microsoft/Protect/S-1-5-18/preferred '
                                                        'is shorter than 24 bytes and was not used')])
        self.assertEqual(len(source.split('\n')), 2)

    def test_no_file_gives_no_rows_and_no_source(self):
        context = FakeContext('/x', [], FolderSeeker({}))
        self.assertEqual(keys.dpapiMasterKeyFiles.__wrapped__(context)[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
