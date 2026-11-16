"""Pin the Remote Access Phonebook artifact (scripts/artifacts/windowsRasPhonebook.py).

The phonebook text follows the layout Add-VpnConnection wrote on a Windows 11 lab VM; the names,
addresses and numbers are made up; the Guid and date values are from the lab file.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsRasPhonebook as rp
# pylint: enable=wrong-import-position

PBK = '''[Made Up VPN]\r
Encoding=1\r
Type=2\r
LowDateTime=328108000\r
HighDateTime=31290750\r
Guid=364812C8FFD9844ABD481640799925B4\r
VpnStrategy=7\r
CustomDialDll=\r
CustomRasDialDll=C:\\made\\up.dll\r
PreferredDevice=WAN Miniport (IKEv2)\r
\r
NETCOMPONENTS=\r
ms_msclient=1\r
\r
MEDIA=rastapi\r
Port=VPN2-0\r
Device=WAN Miniport (IKEv2)\r
\r
DEVICE=vpn\r
PhoneNumber=vpn.example.invalid\r
AreaCode=\r
\r
[Dial]\r
Type=1\r
VpnStrategy=9\r
MEDIA=rastapi\r
Port=COM1\r
Device=Modem\r
DEVICE=modem\r
PhoneNumber=5550100\r
PhoneNumber=5550101\r
MEDIA=second\r
Port=COM2\r
'''


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, rel, text):
        path = os.path.join(self.folder.name, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(text.encode('utf-8'))
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(rp, 'logfunc'):
            return rp.windowsRasPhonebook.__wrapped__(context)

    def test_rows(self):
        user = self.write('Users/a/AppData/Roaming/Microsoft/Network/Connections/Pbk/rasphone.pbk', PBK)
        allu = self.write('ProgramData/Microsoft/Network/Connections/Pbk/rasphone.pbk', '[Only]\r\nType=5\r\n')
        headers, rows, located = self.run_artifact([user, allu])
        self.assertEqual(len(headers), 13)
        by = {r[1]: r for r in rows}
        vpn = by['Made Up VPN']
        self.assertEqual(vpn[0], datetime.datetime(2026, 11, 16, 3, 53, 44, 542000, tzinfo=datetime.timezone.utc))
        self.assertEqual(vpn[2:12], ('2 (VPN connection)', 'vpn.example.invalid', 'vpn', 'WAN Miniport (IKEv2)',
                                     'VPN2-0', '7', 'C:\\made\\up.dll',
                                     '364812C8FFD9844ABD481640799925B4', 'User', 'a'))
        dial = by['Dial']
        self.assertEqual(dial[0], '')
        self.assertEqual(dial[2:8], ('1 (Dial-up connection)', '5550100\n5550101', 'modem', 'Modem', 'COM1', '9'))
        self.assertEqual(by['Only'][2], '5 (Broadband connection)')
        self.assertEqual(by['Only'][10:12], ('All users', ''))
        self.assertEqual(sorted(located.split('\n')), sorted([user, allu]))

    def test_utf16_and_other_names(self):
        path = os.path.join(self.folder.name, 'x', 'rasphone.pbk')
        os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as handle:
            handle.write('[W]\r\nType=2\r\n'.encode('utf-16'))
        other = self.write('x/router.pbk', '[R]\r\nType=2\r\n')
        _h, rows, _l = self.run_artifact([path, other])
        self.assertEqual([r[1] for r in rows], ['W'])

    def test_paths(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        paths = rp.__artifacts_v2__['windowsRasPhonebook']['paths']
        for good in ('root/C/Users/a/AppData/Roaming/Microsoft/Network/Connections/Pbk/rasphone.pbk',
                     'root/C/ProgramData/Microsoft/Network/Connections/Pbk/rasphone.pbk',
                     'root/Documents and Settings/All Users/Application Data/Microsoft/Network/Connections/pbk/rasphone.pbk'):
            self.assertTrue(any(fnmatch.fnmatchcase(good, p) for p in paths), good)

    def test_signed_low_half_and_scope(self):
        self.assertTrue(rp._entry_time({'LowDateTime': '-1', 'HighDateTime': '31290750'}))  # pylint: disable=protected-access
        path = self.write('Windows/x/Microsoft/Network/Connections/Pbk/rasphone.pbk', '[S]\r\nType=2\r\n')
        _h, rows, _l = self.run_artifact([path])
        self.assertEqual(rows[0][10], '')


if __name__ == '__main__':
    unittest.main()
