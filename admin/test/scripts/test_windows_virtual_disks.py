"""Pin identify() in scripts/artifacts/windowsVirtualDisks.py on headers built here (made-up values)."""
import pathlib
import struct
import sys
import unittest
import uuid
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsVirtualDisks as vd  # pylint: disable=wrong-import-position


def vhdx(size, parent=False):
    head = bytearray(3 << 20)
    head[0:8] = b'vhdxfile'
    creator = 'Test Creator'.encode('utf-16-le')
    head[8:8 + len(creator)] = creator
    table = 0x30000
    head[table:table + 4] = b'regi'
    struct.pack_into('<I', head, table + 8, 1)
    head[table + 16:table + 32] = uuid.UUID('8b7ca206-4790-4b9a-b8fe-575f050f886e').bytes_le
    struct.pack_into('<QI', head, table + 32, 0x200000, 0x100000)
    region = 0x200000
    head[region:region + 8] = b'metadata'
    struct.pack_into('<H', head, region + 10, 2)
    head[region + 32:region + 48] = uuid.UUID('2fa54224-cd1b-4876-b211-5dbed83bf4b8').bytes_le
    struct.pack_into('<I', head, region + 48, 0x10000)
    head[region + 64:region + 80] = uuid.UUID('caa16737-fa36-4d43-b3b6-33f0aa44e76b').bytes_le
    struct.pack_into('<I', head, region + 80, 0x10008)
    struct.pack_into('<Q', head, region + 0x10000, size)
    struct.pack_into('<II', head, region + 0x10008, 0x200000, 2 if parent else 0)
    return bytes(head)


class IdentifyTest(unittest.TestCase):
    def test_vhdx(self):
        self.assertEqual({k: v for k, v in vd.identify(vhdx(1 << 30, True), 'a.vhdx').items() if v},
                         {'format': 'VHDX', 'size': 1 << 30, 'parent': 'Yes', 'creator': 'Test Creator'})

    def test_dynamic_vhd(self):
        head = bytearray(512)
        head[0:8] = b'conectix'
        struct.pack_into('>I', head, 24, 86400)
        head[28:32] = b'vbox'
        struct.pack_into('>Q', head, 40, 8 << 30)
        struct.pack_into('>I', head, 60, 3)
        found = vd.identify(bytes(head), 'a.vhd')
        self.assertEqual((found['format'], found['size'], found['type'], found['parent'], found['creator'],
                          found['time']),
                         ('VHD', 8 << 30, 'Dynamic', 'No', 'vbox', datetime(2000, 1, 2, tzinfo=timezone.utc)))

    def test_fixed_vhd_and_others(self):
        boot = bytes(510) + b'\x55\xaa'
        self.assertIn('55 AA', vd.identify(boot, 'disk.vhd')['note'])
        self.assertEqual(vd.identify(boot, 'disk.vdi')['note'], 'no format signature in the bytes read')
        qcow = b'QFI\xfb' + struct.pack('>I', 3) + bytes(16) + struct.pack('>Q', 1 << 20)
        self.assertEqual((vd.identify(qcow, 'a.qcow2')['format'], vd.identify(qcow, 'a.qcow2')['size']),
                         ('qcow version 3', 1 << 20))
        vmdk = b'KDMV' + struct.pack('<IIQ', 1, 3, 2048)
        self.assertEqual(vd.identify(vmdk, 'a.vmdk')['size'], 2048 * 512)
        text = b'# Disk DescriptorFile\nversion=1\ncreateType="monolithicSparse"\n'
        self.assertEqual(vd.identify(text, 'a.vmdk')['type'], 'monolithicSparse (as stored)')
        vdi = b'<<< Oracle VM VirtualBox Disk Image >>>\n'.ljust(64, b'\x00') + struct.pack('<I', 0xBEDA107F) + bytes(4)
        self.assertEqual(vd.identify(vdi, 'a.vdi')['format'], 'VDI')
        self.assertEqual(vd.identify(None, 'a.vhd')['format'], '')


if __name__ == '__main__':
    unittest.main()
