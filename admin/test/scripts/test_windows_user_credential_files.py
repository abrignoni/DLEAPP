"""Pin the rows in scripts/artifacts/windowsUserCredentialFiles.py.

The credential files are built here byte by byte (made-up GUIDs and values); the expected rows are written out.
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

from scripts.artifacts import windowsUserCredentialFiles as creds  # pylint: disable=wrong-import-position
from scripts.search_files import FileInfo  # pylint: disable=wrong-import-position

GUID_A = '0a1b2c3d-1111-2222-3333-444455556666'
GUID_B = 'ffeeddcc-aaaa-bbbb-cccc-0123456789ab'
PROVIDER = bytes.fromhex('d08c9ddf0115d1118c7a00c04fc297eb')
SID = 'S-1-5-21-1-2-3-1001'
UTC = datetime.timezone.utc


def guid_bytes(text):
    first, second, third, fourth, fifth = text.split('-')
    return struct.pack('<IHH', int(first, 16), int(second, 16), int(third, 16)) + bytes.fromhex(fourth + fifth)


def credential_file(guid, description, alg_crypt=0x6610, alg_hash=0x800e):
    desc = (description + '\x00').encode('utf-16-le')
    blob = (struct.pack('<I', 1) + PROVIDER + struct.pack('<I', 1) + guid_bytes(guid) + struct.pack('<I', 0x20000000)
            + struct.pack('<I', len(desc)) + desc + struct.pack('<II', alg_crypt, 256) + struct.pack('<I', 4) + b'salt'
            + struct.pack('<I', 0) + struct.pack('<II', alg_hash, 512) + struct.pack('<I', 2) + b'hm'
            + struct.pack('<I', 4) + b'data' + struct.pack('<I', 2) + b'sg')
    return struct.pack('<III', 1, len(blob), 0) + blob


class ImageSeeker:
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


class ArtifactTest(unittest.TestCase):
    def run_on(self, seeker_class):
        with tempfile.TemporaryDirectory() as tmp:
            appdata = pathlib.Path(tmp, 'vol', 'Users', 'lab', 'AppData')
            local = appdata / 'Local' / 'Microsoft' / 'Credentials'
            roaming = appdata / 'Roaming' / 'Microsoft' / 'Credentials'
            protect = appdata / 'Roaming' / 'Microsoft' / 'Protect' / SID
            service = pathlib.Path(tmp, 'vol', 'Windows', 'ServiceProfiles', 'LocalService', 'AppData', 'Local',
                                   'Microsoft', 'Credentials')
            system = pathlib.Path(tmp, 'vol', 'Windows', 'System32', 'config', 'systemprofile', 'AppData', 'Local',
                                  'Microsoft', 'Credentials')
            for folder in (local, roaming, protect, service, system):
                folder.mkdir(parents=True)
            made = {local / 'AAAA': credential_file(GUID_A, 'Local Credential Data'),
                    roaming / 'BBBB': credential_file(GUID_B, 'Enterprise Credential Data', 0x6603, 0x8004),
                    local / 'CCCC': b'not a credential file',
                    protect / GUID_A: b'k' * 64,
                    service / 'DDDD': credential_file(GUID_A, 'Local Credential Data'),
                    system / 'EEEE': credential_file(GUID_A, 'Local Credential Data')}
            for path, raw in made.items():
                path.write_bytes(raw)
            infos = {str(local / 'AAAA'): FileInfo('vol/a', 1668979881.5, 1673023423.25)}
            context = FakeContext(tmp, [str(path) for path in made], seeker_class(infos))
            with mock.patch.object(creds, 'logfunc') as log:
                headers, rows, _source = creds.userCredentialFiles.__wrapped__(context)
            return headers, rows, [call.args[0] for call in log.call_args_list]

    def test_an_image_gives_a_row_per_user_profile_credential_file_with_its_times(self):
        headers, rows, logged = self.run_on(ImageSeeker)
        created = datetime.datetime.fromtimestamp(1668979881.5, UTC)
        modified = datetime.datetime.fromtimestamp(1673023423.25, UTC)
        self.assertEqual(rows, [
            (created, modified, 'AAAA', 'Local', GUID_A, 'Yes', SID, 'Local Credential Data', 'CALG_AES_256',
             'CALG_SHA_512', 'lab'),
            ('', '', 'BBBB', 'Roaming', GUID_B, 'No', '', 'Enterprise Credential Data', 'CALG_3DES', 'CALG_SHA1', 'lab'),
        ])
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(logged, ['Windows User Credential Files: vol/Users/lab/AppData/Local/Microsoft/Credentials/CCCC '
                                  'did not read as a credential file (ValueError)'])

    def test_a_folder_input_leaves_the_times_blank(self):
        _headers, rows, _logged = self.run_on(FolderSeeker)
        self.assertEqual(rows[0][:2], ('', ''))

    def test_an_unnamed_algorithm_is_given_in_hex(self):
        self.assertEqual(creds._algorithm(0x66ab), '0x66AB')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
