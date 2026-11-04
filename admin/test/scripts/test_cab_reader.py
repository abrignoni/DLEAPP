"""Pin the cabinet reader (scripts/cabinet.py).

The MSZIP cabinets are written here, one block per 32 KiB as the tested CbsPersist cabs hold them. The LZX cabinets
in admin/test/data/cab were made by makecab.exe on Windows 11 from made-up inputs that cab_fixture_inputs.py rebuilds
from fixed seeds, so each decode is compared byte for byte with the file makecab was given. Four of the five LZX
fixtures fail under at least one of the readings the module docstring rejects; random_odd.w16.cab, an uncompressed
block, passes under all of them and pins the uncompressed block path.
"""
import pathlib
import struct
import sys
import unittest
import zlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# pylint: disable=wrong-import-position
import cab_fixture_inputs as inputs
from scripts import cabinet
# pylint: enable=wrong-import-position

FIXTURES = REPO_ROOT / 'admin' / 'test' / 'data' / 'cab'
LZX_CABS = {
    'aligned_records.bin': 'aligned_records.w16.cab',
    'e8_frame_ends.bin': 'e8_frame_ends.w21.cab',
    'random_odd.bin': 'random_odd.w16.cab',
    'cbs_text.log': 'cbs_text.w21.cab',
    'short_text.txt': 'short_text.w15.cab',
}


def _cab(payload, name='CbsPersist_20240101000000.log', compression=1, block=32768, recorded=None):
    """A one-folder, one-file cabinet holding payload, MSZIP blocks carrying the previous 32 KiB as history."""
    blocks, done = [], 0
    while done < len(payload):
        chunk = payload[done:done + block]
        history = payload[max(0, done - 32768):done]
        packer = zlib.compressobj(9, zlib.DEFLATED, -15, zdict=history) if history else \
            zlib.compressobj(9, zlib.DEFLATED, -15)
        blocks.append((b'CK' + packer.compress(chunk) + packer.flush(), len(chunk)))
        done += len(chunk)
    file_entry = struct.pack('<IIHHHH', len(payload) if recorded is None else recorded, 0, 0, 0, 0, 0x20) + \
        name.encode() + b'\0'
    folder_at, files_at = 36, 36 + 8
    data_at = files_at + len(file_entry)
    data = b''.join(struct.pack('<IHH', 0, len(packed), size) + packed for packed, size in blocks)
    total = data_at + len(data)
    header = b'MSCF' + struct.pack('<IIIIIBBHHHHH', 0, total, 0, files_at, 0, 3, 1, 1, 1, 0, 0, 0)
    folder = struct.pack('<IHH', data_at, len(blocks), compression)
    assert len(header) == folder_at
    return header + folder + file_entry + data


class MszipCabTest(unittest.TestCase):
    def test_a_cab_of_several_blocks_gives_its_file_back(self):
        payload = ''.join(f'2024-01-01 00:00:{n % 60:02d}, Info                  CBS    line {n}\r\n'
                          for n in range(6000)).encode('utf-8')
        name, data = cabinet.cab_member(_cab(payload))
        self.assertEqual((name, data), ('CbsPersist_20240101000000.log', payload))
        self.assertGreater(len(payload), 3 * 32768)

    def test_a_recorded_size_that_does_not_match_raises(self):
        with self.assertRaises(cabinet.CabError):
            cabinet.cab_member(_cab(b'x' * 1000, recorded=999))

    def test_quantum_and_a_file_that_is_not_a_cab_raise(self):
        with self.assertRaises(cabinet.CabError):
            cabinet.cab_member(_cab(b'x' * 1000, compression=2))
        with self.assertRaises(cabinet.CabError):
            cabinet.cab_member(b'PK\x03\x04' + b'\0' * 60)


class LzxCabTest(unittest.TestCase):
    def test_each_makecab_fixture_decodes_to_the_input_it_was_made_from(self):
        for source, cab in LZX_CABS.items():
            with self.subTest(cab=cab):
                data = (FIXTURES / cab).read_bytes()
                self.assertEqual(struct.unpack_from('<H', data, 42)[0] & 0xf, 3)
                name, out = cabinet.cab_member(data)
                self.assertEqual(name, source)
                self.assertEqual(out, inputs.INPUTS[source]())

    def test_the_fixtures_use_every_block_type(self):
        seen = set()
        original = cabinet._Bits.read  # pylint: disable=protected-access
        last = []

        def read(bits, n):
            value = original(bits, n)
            if n == 3:
                last[:] = [value]
            elif n == 24 and last:
                seen.add(last[0])
            return value
        cabinet._Bits.read = read  # pylint: disable=protected-access
        try:
            for cab in LZX_CABS.values():
                cabinet.cab_member((FIXTURES / cab).read_bytes())
        finally:
            cabinet._Bits.read = original  # pylint: disable=protected-access
        self.assertEqual(seen, {1, 2, 3})

    def test_the_e8_fixture_needs_e8_translation(self):
        data = (FIXTURES / LZX_CABS['e8_frame_ends.bin']).read_bytes()
        original = cabinet._translate_e8  # pylint: disable=protected-access
        cabinet._translate_e8 = lambda frame, start, size: None  # pylint: disable=protected-access
        try:
            untranslated = cabinet.cab_member(data)[1]
        finally:
            cabinet._translate_e8 = original  # pylint: disable=protected-access
        self.assertNotEqual(untranslated, inputs.e8_frame_ends())
        self.assertEqual(cabinet.cab_member(data)[1], inputs.e8_frame_ends())

    def test_a_cut_off_lzx_cab_raises(self):
        data = (FIXTURES / LZX_CABS['cbs_text.log']).read_bytes()
        with self.assertRaises(cabinet.CabError):
            cabinet.cab_member(data[:len(data) // 2])

    def test_an_lzx_window_outside_15_to_21_raises(self):
        data = bytearray((FIXTURES / LZX_CABS['cbs_text.log']).read_bytes())
        struct.pack_into('<H', data, 42, 3 | (22 << 8))
        with self.assertRaises(cabinet.CabError):
            cabinet.cab_member(bytes(data))


if __name__ == '__main__':
    unittest.main()
