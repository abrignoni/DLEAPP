"""Pin FAT and exFAT Volume Information (scripts/artifacts/fatVolumeInfo.py) on made-up boot sectors and root
directories laid out as the Linux header and Microsoft's exFAT specification give."""
import contextlib
import gzip
import io
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
import scripts.artifacts.fatVolumeInfo as fat_volume_info
import scripts.raw_image as raw_image
from scripts.artifacts.fatVolumeInfo import boot_fields, root_label, volume_rows
from scripts.raw_image import FileSeekerRaw
from scripts.vendor import qnxprobe
# pylint: enable=wrong-import-position

FIXTURES = REPO_ROOT / 'admin' / 'test' / 'data' / 'raw_images'
# (fixture, file system, serial, root directory label, boot sector label), as The Sleuth Kit 4.15.0 fsstat gives
# them, except the FAT root directory labels, whose entries carry attribute 0x28, which fsstat prints blank
FIXTURE_ROWS = (
    ('fat12-fixture', 'FAT12', 'C5EC181F', 'FAT12FIX', 'FAT12FIX'),
    ('fat16-fixture', 'FAT16', '24191808', 'FAT16FIX', 'FAT16FIX'),
    ('fat32-deleted', 'FAT32', 'E8A408EB', 'FATDELB', 'FATDELB'),
    ('exfat-deleted', 'exFAT', '6AA38B26', 'EXFATDELB', ''),
)


def fat_sector(extended, signature=0x29):
    sector = bytearray(512)
    sector[3:11] = b'MSDOS5.0'
    struct.pack_into('<H', sector, 11, 512)
    sector[13] = 8
    struct.pack_into('<I', sector, 32, 204800)
    sector[extended + 2] = signature
    struct.pack_into('<I', sector, extended + 3, 0x1234ABCD)
    sector[extended + 7:extended + 18] = b'BOOTLABEL  '
    return bytes(sector)


def exfat_sector():
    sector = bytearray(512)
    sector[3:11] = b'EXFAT   '
    struct.pack_into('<Q', sector, 72, 131072)
    struct.pack_into('<I', sector, 100, 0xCAFE0001)
    sector[108], sector[109] = 9, 3
    return bytes(sector)


def fat_entry(name, attribute):
    entry = bytearray(32)
    entry[:11] = name
    entry[11] = attribute
    return bytes(entry)


class BootFieldsTest(unittest.TestCase):
    def test_fat32(self):
        fields = boot_fields(fat_sector(64), 'fat32')
        self.assertEqual((fields['serial'], fields['boot_label'], fields['oem']), ('1234ABCD', 'BOOTLABEL', 'MSDOS5.0'))
        self.assertEqual((fields['cluster'], fields['total_sectors'], fields['size']), (4096, 204800, 104857600))

    def test_fat16_reads_its_own_offsets(self):
        self.assertEqual(boot_fields(fat_sector(36), 'fat16')['serial'], '1234ABCD')

    def test_no_extended_signature_leaves_serial_and_label_blank(self):
        fields = boot_fields(fat_sector(64, signature=0), 'fat32')
        self.assertEqual((fields['serial'], fields['boot_label']), ('', ''))

    def test_exfat(self):
        fields = boot_fields(exfat_sector(), 'exfat')
        self.assertEqual((fields['serial'], fields['oem'], fields['boot_label']), ('CAFE0001', '', ''))
        self.assertEqual((fields['bytes_per_sector'], fields['cluster'], fields['size']), (512, 4096, 67108864))

    def test_short_sector(self):
        self.assertIsNone(boot_fields(b'\x00' * 100, 'fat32'))


class RootLabelTest(unittest.TestCase):
    def test_label_with_the_archive_bit(self):
        self.assertEqual(root_label(fat_entry(b'ROOTLABEL  ', 0x28), 'fat32'), 'ROOTLABEL')

    def test_long_name_and_deleted_entries_are_not_labels(self):
        raw = fat_entry(b'Along name ', 0x0F) + fat_entry(b'\xe5OLDLABEL  ', 0x08) + fat_entry(b'FILE    TXT', 0x20)
        self.assertEqual(root_label(raw, 'fat32'), '')

    def test_stops_at_the_end_marker(self):
        raw = bytes(32) + fat_entry(b'LATERLABEL ', 0x08)
        self.assertEqual(root_label(raw, 'fat16'), '')

    def test_exfat_label(self):
        entry = bytearray(32)
        entry[0], entry[1] = 0x83, 4
        entry[2:10] = 'Disk'.encode('utf-16-le')
        self.assertEqual(root_label(bytes(entry), 'exfat'), 'Disk')

    def test_exfat_entry_not_in_use_is_not_a_label(self):
        entry = bytearray(32)
        entry[0], entry[1] = 0x03, 4
        entry[2:10] = 'Disk'.encode('utf-16-le')
        self.assertEqual(root_label(bytes(entry), 'exfat'), '')


class VolumeRowsOnImagesTest(unittest.TestCase):
    """volume_rows through the raw image seeker's own walkers, after the seeker has walked each volume."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix='leapp_fat_volume_info_')
        self.addCleanup(shutil.rmtree, self.work, True)

    def seeker_for(self, stem):
        image = pathlib.Path(self.work) / f'{stem}.img'
        with gzip.open(FIXTURES / f'{stem}.img.gz', 'rb') as src, open(image, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        out = tempfile.mkdtemp(dir=self.work)
        with mock.patch.object(raw_image, 'logfunc', lambda *_a, **_k: None), \
                contextlib.redirect_stdout(io.StringIO()):
            seeker = FileSeekerRaw(str(image), out)
            seeker.search('*/no-such-file')
        self.addCleanup(seeker.cleanup)
        return seeker

    def test_one_row_per_volume_with_its_labels(self):
        for stem, kind, serial, root, boot in FIXTURE_ROWS:
            with self.subTest(stem):
                seeker = self.seeker_for(stem)
                logged = []
                with mock.patch.object(fat_volume_info, 'logfunc', logged.append):
                    rows = volume_rows(seeker.volumes)
                self.assertEqual(logged, [])
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0][1:5], (kind, serial, root, boot))

    def test_reading_the_root_records_nothing_on_the_walker(self):
        for stem, *_ in FIXTURE_ROWS:
            with self.subTest(stem):
                seeker = self.seeker_for(stem)
                walker = seeker.volumes[0]['walker']
                before = (qnxprobe.damage_lines(walker, 1000), getattr(walker, 'folders_not_read', 0))
                volume_rows(seeker.volumes)
                self.assertEqual((qnxprobe.damage_lines(walker, 1000), getattr(walker, 'folders_not_read', 0)), before)


if __name__ == '__main__':
    unittest.main()
