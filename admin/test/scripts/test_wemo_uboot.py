"""Pin the U-Boot environment and Belkin WeMo NVRAM artifacts
(scripts/artifacts/ubootEnvironment.py and scripts/artifacts/belkinWemo.py).

Every store here is made up. The U-Boot stores follow env_t in U-Boot v2024.01
(include/env_internal.h at 866ca972): a little-endian CRC-32, a flags byte only in the
redundant layout, then NUL-separated strings ending in an empty one. The NVRM stores follow
env_image_gemtek in Belkin's libnvram.c (public copy of the WeMo firmware tree at 46d0ccd2): 'NVRM', a
CRC-32 over the bytes after the 16-byte header, an entry count and the end of the data.
"""
import binascii
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import belkinWemo as bw
from scripts.artifacts import ubootEnvironment as ue
# pylint: enable=wrong-import-position


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def env(strings, size, header=4, flags=1):
    data = (b'\x00'.join(strings) + b'\x00\x00').ljust(size - header, b'\x00')
    return struct.pack('<I', binascii.crc32(data)) + (bytes([flags]) if header == 5 else b'') + data


def nvram(strings, size, count=None):
    body = b''.join(s + b'\x00' for s in strings)
    data = (body + b'\x00').ljust(size - 16, b'\xff')
    return (b'NVRM' + struct.pack('<III', binascii.crc32(data), len(strings) if count is None else count,
                                  16 + len(body)) + data)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.paths = []
        self.logged = []
        for module in (ue, bw):
            patcher = mock.patch.object(module, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def add(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        return path

    def run_artifact(self, func):
        return func.__wrapped__(FakeContext(self.paths, self.root))

    def test_uboot_single_redundant_and_file_layouts(self):
        self.add('lba70/uboot-env.bin', env([b'bootdelay=3', b'baudrate=115200', b'flag_only'], 0x1000))
        self.add('lba90/uboot-env.bin', env([b'example_a=1', b'example_b=x=y'], 0x2000, header=5, flags=7))
        self.add('p1_lba2048_boot/uboot.env', env([b'example_c='], 0x1000))
        headers, rows, source = self.run_artifact(ue.ubootEnvironment)
        self.assertEqual(headers, ('Name', 'Value', 'Position', 'Layout', 'Folder'))
        self.assertEqual(rows, [
            ('bootdelay', '3', 1, '4-byte header, 4,096 bytes', 'lba70'),
            ('baudrate', '115200', 2, '4-byte header, 4,096 bytes', 'lba70'),
            ('flag_only', '', 3, '4-byte header, 4,096 bytes', 'lba70'),
            ('example_a', '1', 1, '5-byte header, flags byte 7, 8,192 bytes', 'lba90'),
            ('example_b', 'x=y', 2, '5-byte header, flags byte 7, 8,192 bytes', 'lba90'),
            ('example_c', '', 1, '4-byte header, 4,096 bytes', 'p1_lba2048_boot'),
        ])
        self.assertEqual(sorted(source.split('\n')), sorted(self.paths))
        self.assertEqual(self.logged, [])

    def test_uboot_store_whose_crc_fails_gives_no_row(self):
        bad = bytearray(env([b'example_a=1'], 0x1000))
        bad[10] ^= 1
        self.add('lba70/uboot-env.bin', bytes(bad))
        self.add('lba500/uboot.env', b'not a store at all')
        good = self.add('lba600/uboot-env.bin', env([b'example_b=2'], 0x1000))
        os.makedirs(os.path.join(self.root, 'lba700', 'uboot.env'))
        self.paths.append(os.path.join(self.root, 'lba700', 'uboot.env'))
        _headers, rows, source = self.run_artifact(ue.ubootEnvironment)
        self.assertEqual(rows, [('example_b', '2', 1, '4-byte header, 4,096 bytes', 'lba600')])
        self.assertEqual(source, good)
        self.assertEqual(self.logged, ['U-Boot Environment Variables: 2 files whose CRC-32 does not hold, '
                                       'not read'])

    def test_strings_after_the_empty_one_are_not_read(self):
        data = b'example_a=1\x00\x00left_over=2\x00'.ljust(0x1000 - 4, b'\x00')
        self.add('lba1/uboot-env.bin', struct.pack('<I', binascii.crc32(data)) + data)
        body = b'example_b=3\x00\x00left_over=4\x00'.ljust(0x1000 - 16, b'\xff')
        self.add('lba2/nvram.bin', b'NVRM' + struct.pack('<III', binascii.crc32(body), 1, 28) + body)
        self.assertEqual(self.run_artifact(ue.ubootEnvironment)[1],
                         [('example_a', '1', 1, '4-byte header, 4,096 bytes', 'lba1')])
        self.assertEqual(self.run_artifact(bw.belkinWemoNvram)[1], [('example_b', '3', 1, 'lba2')])

    def test_uboot_ignores_other_names(self):
        self.add('lba70/nvram.bin', env([b'example_a=1'], 0x1000))
        _headers, rows, _source = self.run_artifact(ue.ubootEnvironment)
        self.assertEqual(rows, [])

    def test_nvram_rows_and_count_check(self):
        self.add('lba1500/nvram.bin', nvram([b'example_name=Test Plug', b'example_id=000TEST000',
                                              b'no_value'], 0x3000))
        self.add('lba1600/nvram.bin', nvram([b'example_zone=1.0'], 0x1000, count=9))
        headers, rows, _source = self.run_artifact(bw.belkinWemoNvram)
        self.assertEqual(headers, ('Name', 'Value', 'Position', 'Folder'))
        self.assertEqual(rows, [
            ('example_name', 'Test Plug', 1, 'lba1500'),
            ('example_id', '000TEST000', 2, 'lba1500'),
            ('no_value', '', 3, 'lba1500'),
            ('example_zone', '1.0', 1, 'lba1600'),
        ])
        self.assertEqual(self.logged, ['Belkin WeMo NVRAM Settings: 1 stores whose header count differs '
                                       'from the strings read'])

    def test_nvram_store_that_fails_gives_no_row(self):
        bad = bytearray(nvram([b'example_name=x'], 0x1000))
        bad[20] ^= 1
        self.add('lba1/nvram.bin', bytes(bad))
        self.add('lba2/nvram.bin', b'NVRX' + nvram([b'example_name=x'], 0x1000)[4:])
        self.add('lba3/nvram.bin', b'NVRM')
        _headers, rows, source = self.run_artifact(bw.belkinWemoNvram)
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['Belkin WeMo NVRAM Settings: 3 files without an NVRM header whose '
                                       'CRC-32 holds, not read'])

    def test_header_fields_outside_the_crc_do_not_matter(self):
        store = bytearray(nvram([b'example_name=x'], 0x1000))
        store[12:16] = struct.pack('<I', 0xFFFFFFFF)      # end of data, not covered by the CRC
        self.add('lba1/nvram.bin', bytes(store))
        _headers, rows, _source = self.run_artifact(bw.belkinWemoNvram)
        self.assertEqual(rows, [('example_name', 'x', 1, 'lba1')])


if __name__ == '__main__':
    unittest.main()
