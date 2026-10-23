"""Pin the Per-User COM Registrations artifact (scripts/artifacts/windowsUserComRegistrations.py).

The UsrClass.dat and SOFTWARE hives are built cell by cell with the builder in test_windows_app_settings.py and read
back through open_hive and python-registry, as a run reads a staged hive. Every CLSID, name and path is invented.
"""

import datetime
import fnmatch
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUserComRegistrations as com
from test_windows_app_settings import _Context, build_hive, spec, write
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1 = datetime.datetime(2031, 4, 5, 6, 7, 8, tzinfo=UTC)
T2 = datetime.datetime(2032, 5, 6, 7, 8, 9, tzinfo=UTC)
REG_SZ, REG_EXPAND_SZ = 1, 2
A = '{00000000-0000-0000-0000-00000000000A}'
B = '{00000000-0000-0000-0000-00000000000B}'
C = '{00000000-0000-0000-0000-00000000000C}'
D = '{00000000-0000-0000-0000-00000000000D}'
E = '{00000000-0000-0000-0000-00000000000E}'
F = '{00000000-0000-0000-0000-00000000000F}'
REG_MULTI_SZ = 7


def sz(text, kind=REG_SZ, name=''):
    return (name, kind, text.encode('utf-16-le') + b'\x00\x00')


def clsid(name, stamp=T1, label=None, subkeys=()):
    return spec(name, stamp, [sz(label)] if label is not None else [], list(subkeys))


def user_hive():
    return build_hive(T1, spec('CLSID', T1, (), [
        clsid(A, T2, 'Made-up In-Process Class', [
            spec('InprocServer32', T1, [sz('C:\\Users\\alice\\AppData\\Local\\MadeUp\\made.dll'),
                                        sz('Both', name='ThreadingModel')]),
            spec('ProgID', T1, [sz('MadeUp.Thing.1')])]),
        clsid(B, T1, None, [spec('LocalServer32', T1, [sz('"%SystemRoot%\\system32\\madeup.exe" -x', REG_EXPAND_SZ)])]),
        clsid(C, T1, 'Emulated', [spec('TreatAs', T1, [sz(D)])]),
        clsid(D, T1, 'Icon only', [spec('DefaultIcon', T1, [sz('x.dll,0')])]),
        clsid(F, T1, 'Both servers', [
            spec('InprocServer32', T1, [('', REG_MULTI_SZ, 'D:\\made\\a.dll'.encode('utf-16-le') + b'\0\0'
                                         + 'second'.encode('utf-16-le') + b'\0\0\0\0')]),
            spec('LocalServer32', T1, [sz('C:\\Users\\alice\\made.exe')])]),
    ]), spec('Wow6432Node', T1, (), [spec('CLSID', T1, (), [
        clsid(E, T1, 'Made-up 32-bit Class', [spec('InprocServer32', T1, [sz('%LOCALAPPDATA%\\MadeUp\\made32.dll')])]),
    ])]))


def software_hive(clsids=(A,), wow=()):
    return build_hive(T1, spec('Classes', T1, (), [
        spec('CLSID', T1, (), [clsid(name) for name in clsids]),
        spec('Wow6432Node', T1, (), [spec('CLSID', T1, (), [clsid(name) for name in wow])]),
    ]))


USR = 'Users/alice/AppData/Local/Microsoft/Windows/UsrClass.dat'
SOFT = 'Windows/System32/config/SOFTWARE'


class RegistrationsTest(unittest.TestCase):
    def run_artifact(self, hives):
        with tempfile.TemporaryDirectory() as root:
            files = [write(root, relative, data) for relative, data in hives]
            with mock.patch.object(com, 'logfunc') as log:
                headers, rows, source = com.windowsUserComRegistrations.__wrapped__(_Context(root, files))
            source = [os.path.relpath(p, root) for p in source.split('\n')] if source else []
        return headers, rows, source, log

    def test_rows_columns_and_flags(self):
        headers, rows, source, log = self.run_artifact([('vol/' + USR, user_hive()),
                                                         ('vol/' + SOFT, software_hive((A,), (E,)))])
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['Key Last Written (UTC)', 'User', 'View', 'CLSID', 'Class Name', 'InprocServer32',
                                 'ThreadingModel', 'LocalServer32', 'TreatAs', 'ProgID', 'Also in SOFTWARE',
                                 'Server Under Users Folder', 'Key', 'Source File'])
        self.assertEqual([r[3] for r in rows], [A, B, C, F, E])  # D names no server and no TreatAs
        by = {r[3]: r for r in rows}
        self.assertEqual(by[A], (T2, 'alice', 'CLSID', A, 'Made-up In-Process Class',
                                 'C:\\Users\\alice\\AppData\\Local\\MadeUp\\made.dll', 'Both', '', '', 'MadeUp.Thing.1',
                                 'Yes', 'Yes', 'CLSID\\' + A, 'vol/' + USR))
        self.assertEqual(by[B][4:12], ('', '', '', '"%SystemRoot%\\system32\\madeup.exe" -x', '', '', 'No', 'No'))
        self.assertEqual(by[C][8:12], (D, '', 'No', ''))
        # Both servers: a multi-string value is joined, and a Users path in either server gives Yes.
        self.assertEqual(by[F][5:8], ('D:\\made\\a.dll | second', '', 'C:\\Users\\alice\\made.exe'))
        self.assertEqual(by[F][11], 'Yes')
        self.assertEqual(by[E][2], 'Wow6432Node\\CLSID')
        self.assertEqual(by[E][10:13], ('Yes', 'Yes', 'Wow6432Node\\CLSID\\' + E))
        self.assertEqual(source, ['vol/' + USR])
        log.assert_not_called()

    def test_without_a_software_hive_the_machine_column_is_blank(self):
        _h, rows, _s, log = self.run_artifact([('vol/' + USR, user_hive())])
        self.assertEqual({r[10] for r in rows}, {''})
        self.assertIn('no single SOFTWARE hive beside', log.call_args.args[0])

    def test_each_user_is_compared_with_the_software_hive_of_its_own_volume(self):
        _h, rows, source, _log = self.run_artifact([
            ('one/' + USR, user_hive()), ('one/' + SOFT, software_hive((A,))),
            ('two/' + USR.replace('alice', 'bob'), user_hive()), ('two/' + SOFT, software_hive((B,)))])
        got = {(r[1], r[3]): r[10] for r in rows}
        self.assertEqual(len(rows), 10)
        self.assertEqual((got[('alice', A)], got[('alice', B)]), ('Yes', 'No'))
        self.assertEqual((got[('bob', A)], got[('bob', B)]), ('No', 'Yes'))
        self.assertEqual(source, ['one/' + USR, 'two/' + USR.replace('alice', 'bob')])

    def test_a_hive_without_clsid_keys_gives_no_rows(self):
        _h, rows, source, _log = self.run_artifact([('vol/' + USR, build_hive(T1, spec('Local Settings', T1))),
                                                    ('vol/' + SOFT, software_hive())])
        self.assertEqual(rows, [])
        self.assertEqual(source, ['vol/' + USR])

    def test_under_users_folder(self):
        for path in ('C:\\Users\\a\\x.dll', '"C:\\Users\\a\\x.exe" -y', '%LOCALAPPDATA%\\x.dll', '%AppData%\\x.dll',
                     '%USERPROFILE%\\x.dll', '%SystemDrive%\\Users\\a\\x.dll', 'C:\\Documents and Settings\\a\\x.dll',
                     'c:/users/a/x.dll'):
            self.assertTrue(com.under_users_folder(path), path)
        for path in ('%SystemRoot%\\system32\\x.dll', 'C:\\Program Files\\Users\\x.dll', 'C:\\Users', 'x.dll', '',
                     'D:\\Data\\Users\\a\\x.dll', '\\\\server\\share\\Users\\a\\x.dll'):
            self.assertFalse(com.under_users_folder(path), path)

    def test_declared_paths(self):
        patterns = com.__artifacts_v2__['windowsUserComRegistrations']['paths']
        for member in ('Users/a/AppData/Local/Microsoft/Windows/UsrClass.dat',
                       'Users/a/AppData/Local/Microsoft/Windows/usrClass.dat',
                       'Users/a/AppData/Local/Microsoft/Windows/UsrClass.dat.LOG1',
                       'Windows/System32/config/SOFTWARE', 'Windows/System32/config/SOFTWARE.LOG2'):
            self.assertEqual(sum(fnmatch.fnmatchcase('x/' + member, p) for p in patterns), 1, member)
        for member in ('Users/a/Desktop/UsrClass.dat', 'Users/a/AppData/Local/Microsoft/Windows/UsrClass.dat.bak',
                       'Users/a/AppData/Local/Packages/p/SystemAppData/Helium/UserClasses.dat',
                       'Windows/System32/config/RegBack/SOFTWARE'):
            self.assertFalse(any(fnmatch.fnmatchcase('x/' + member, p) for p in patterns), member)


if __name__ == '__main__':
    unittest.main()
