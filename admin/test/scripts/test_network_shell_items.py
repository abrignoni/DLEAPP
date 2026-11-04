"""Pin how network location shell items are named, in scripts/windows_lnk.py and in windowsShellbags.py, on items
built here in the layout libyal libfwsi documents: size, class type, an unknown byte, flags, then the location as an
ASCII string and, when flag 0x80 is set, a description. Every name here is made up."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import windows_lnk
from scripts.artifacts import windowsShellbags
# pylint: enable=wrong-import-position


def item(class_type, location, description=None):
    flags = 0x80 if description is not None else 0x00
    body = bytes([class_type, 0, flags]) + location.encode('ascii') + b'\x00'
    if description is not None:
        body += description.encode('ascii') + b'\x00'
    return struct.pack('<H', len(body) + 2) + body


def idlist(*items):
    return b''.join(items) + b'\x00\x00'


CHAIN = (item(0x47, 'Entire Network'), item(0x46, 'Microsoft Windows Network', 'Microsoft Network'),
         item(0x41, 'WORKGROUP', 'Microsoft Network'), item(0x42, '\\\\server1', 'Microsoft Network'),
         item(0xC3, '\\\\server1\\share1', 'Microsoft Network'))


class NetworkItemsTest(unittest.TestCase):
    def test_a_chain_reads_network_workgroup_server_share(self):
        self.assertEqual(windows_lnk._idlist_path(idlist(*CHAIN)),  # pylint: disable=protected-access
                         'Entire Network\\Microsoft Windows Network\\WORKGROUP\\server1\\share1')

    def test_shellbags_names_each_item_the_same_way(self):
        names = [windowsShellbags._shell_item(i)[0] for i in CHAIN]  # pylint: disable=protected-access
        self.assertEqual(names, ['Entire Network', 'Microsoft Windows Network', 'WORKGROUP', 'server1', 'share1'])

    def test_an_undocumented_kind_is_left_alone(self):
        odd = item(0x4C, 'not a location')
        self.assertIsNone(windows_lnk._network_item_name(odd))  # pylint: disable=protected-access
        self.assertEqual(windowsShellbags._shell_item(odd)[0], '<shell item 0x4c>')  # pylint: disable=protected-access

    def test_a_share_name_ending_in_a_separator(self):
        self.assertEqual(windows_lnk._network_item_name(item(0x43, '\\\\server1\\share1\\')), 'share1')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
