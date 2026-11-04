"""A SYSTEM credential file whose master key is not opened gives a 'decrypt failed' row, not a crash."""
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSystemCredentials as syscreds  # pylint: disable=wrong-import-position


class FakeContext:
    def __init__(self, root):
        self.root = root

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class MissingKeyTest(unittest.TestCase):
    def test_a_master_key_that_was_not_opened_gives_a_decrypt_failed_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            cred = pathlib.Path(tmp, 'vol', 'Windows', 'ServiceProfiles', 'LocalService', 'AppData', 'Local',
                                'Microsoft', 'Credentials', 'AAAA')
            cred.parent.mkdir(parents=True)
            cred.write_bytes(b'blob')
            pool = mock.Mock()
            pool.get_key.return_value = None
            credential = mock.Mock(blob=SimpleNamespace(mk_guid='0a1b2c3d-1111-2222-3333-444455556666'))
            fake = SimpleNamespace(get_bootkey=mock.Mock(return_value=b'k'), get_dpapi_system=mock.Mock(return_value=b'd'),
                                   MasterKeyPool=mock.Mock(return_value=pool),
                                   system_master_key_candidates=mock.Mock(return_value=[]),
                                   CredentialFile=mock.Mock(return_value=credential))
            rows = []
            with mock.patch.object(syscreds, 'dpapiprobe', fake), mock.patch.object(syscreds, 'logfunc') as log:
                used = syscreds._rows_for_install(  # pylint: disable=protected-access
                    FakeContext(tmp), {'SYSTEM': 'sys', 'SECURITY': 'sec'}, ['mk'], [str(cred)], rows)
            credential.decrypt.assert_not_called()
            self.assertEqual(rows, [('', '', '', '', '', '', 'decrypt failed',
                                     'vol/Windows/ServiceProfiles/LocalService/AppData/Local/Microsoft/Credentials/AAAA')])
            self.assertEqual(used, ['sys', 'sec'])
            self.assertIn('was not opened', log.call_args_list[-1].args[0])


if __name__ == '__main__':
    unittest.main()
