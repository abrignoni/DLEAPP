"""Pin the boot sector decode of NTFS Volume Information (scripts/artifacts/windowsNtfsVolumeInfo.py) on a made-up
boot sector laid out as the Linux-NTFS documentation gives."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts.windowsNtfsVolumeInfo import boot_fields
# pylint: enable=wrong-import-position


def boot(per_record=-10, sectors_per_cluster=8):
    sector = bytearray(512)
    sector[3:11] = b'NTFS    '
    struct.pack_into('<H', sector, 0x0B, 512)
    sector[0x0D] = sectors_per_cluster
    sector[0x15] = 0xF8
    struct.pack_into('<QQQ', sector, 0x28, 2_000_000, 786432, 2)
    struct.pack_into('<b', sector, 0x40, per_record)
    struct.pack_into('<Q', sector, 0x48, 0x1122334455667788)
    return bytes(sector)


class BootFieldsTest(unittest.TestCase):
    def test_a_boot_sector(self):
        fields = boot_fields(boot())
        self.assertEqual((fields['bytes_per_sector'], fields['sectors_per_cluster'], fields['cluster']), (512, 8, 4096))
        self.assertEqual((fields['total_sectors'], fields['size']), (2_000_000, 1_024_000_000))
        self.assertEqual((fields['mft_lcn'], fields['mirror_lcn']), (786432, 2))
        self.assertEqual(fields['record_size'], 1024)
        self.assertEqual(fields['serial'], 0x1122334455667788)

    def test_a_positive_record_count_is_clusters(self):
        self.assertEqual(boot_fields(boot(per_record=1, sectors_per_cluster=2))['record_size'], 1024)

    def test_not_ntfs(self):
        self.assertIsNone(boot_fields(b'\x00' * 512))
        self.assertIsNone(boot_fields(boot()[:0x40]))


if __name__ == '__main__':
    unittest.main()
