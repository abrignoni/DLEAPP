"""Pin how the shell link reader builds a target from LinkInfo (scripts/windows_lnk.py), on links built here in the
[MS-SHLLINK] layout: the common path follows the local base path when the link has a local volume, and the network
share name when it has only a share. Every name here is made up."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.windows_lnk import parse_lnk, target_path
# pylint: enable=wrong-import-position

CLSID = bytes.fromhex('0114020000000000c000000000000046')
HAS_LINK_INFO = 0x2
VOLUME_ID_AND_LOCAL_BASE_PATH, COMMON_NETWORK_RELATIVE_LINK = 0x1, 0x2


def header(flags):
    return (struct.pack('<I', 0x4C) + CLSID + struct.pack('<II', flags, 0x20) + struct.pack('<QQQ', 0, 0, 0)
            + struct.pack('<IIIH', 0, 0, 1, 0) + b'\x00' * 10)


def link_info(share=None, local_base=None, suffix=''):
    """A LinkInfo with a 0x1C byte header, then the VolumeID, local base path, network link and suffix."""
    body = b''
    flags = voloff = lbpoff = cnrloff = 0
    if local_base is not None:
        flags |= VOLUME_ID_AND_LOCAL_BASE_PATH
        voloff = 0x1C + len(body)
        body += struct.pack('<IIII', 0x11, 3, 0x1234ABCD, 0x10) + b'\x00'
        lbpoff = 0x1C + len(body)
        body += local_base.encode('latin-1') + b'\x00'
    if share is not None:
        flags |= COMMON_NETWORK_RELATIVE_LINK
        cnrloff = 0x1C + len(body)
        name = share.encode('latin-1') + b'\x00'
        body += struct.pack('<IIIII', 0x14 + len(name), 0, 0x14, 0, 0) + name
    cpsoff = 0x1C + len(body)
    body += suffix.encode('latin-1') + b'\x00'
    size = 0x1C + len(body)
    return struct.pack('<IIIIIII', size, 0x1C, flags, voloff, lbpoff, cnrloff, cpsoff) + body


def link(**kwargs):
    return header(HAS_LINK_INFO) + link_info(**kwargs) + b'\x00\x00\x00\x00'


class LinkInfoTargetTest(unittest.TestCase):
    def test_a_share_only_link_targets_the_share_and_the_path_below_it(self):
        parsed = parse_lnk(link(share='\\\\server\\share', suffix='folder\\file.txt'))
        self.assertEqual(parsed['local_path'], '')
        self.assertEqual(parsed['network_path'], '\\\\server\\share')
        self.assertEqual(target_path(parsed), '\\\\server\\share\\folder\\file.txt')

    def test_a_share_name_ending_in_a_separator_gets_no_second_one(self):
        parsed = parse_lnk(link(share='\\\\server\\share\\', suffix='file.txt'))
        self.assertEqual(target_path(parsed), '\\\\server\\share\\file.txt')

    def test_a_share_with_no_suffix_targets_the_share(self):
        parsed = parse_lnk(link(share='\\\\server\\share'))
        self.assertEqual(target_path(parsed), '\\\\server\\share')

    def test_a_local_link_keeps_its_base_path_and_suffix(self):
        parsed = parse_lnk(link(local_base='C:\\Users\\u\\', suffix='doc.txt'))
        self.assertEqual(parsed['local_path'], 'C:\\Users\\u\\doc.txt')
        self.assertEqual(target_path(parsed), 'C:\\Users\\u\\doc.txt')
        self.assertEqual(parsed['network_path'], '')


if __name__ == '__main__':
    unittest.main()
