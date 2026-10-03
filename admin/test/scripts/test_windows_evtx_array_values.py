"""Pin the array value types scripts/windows_evtx.py adds to python-evtx's value lookup.

Each array is its elements stored one after another, little-endian, and renders as <string> pieces, each element as
python-evtx's own value type for it renders it.
"""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_evtx  # noqa: E402  pylint: disable=wrong-import-position

try:
    import Evtx.Nodes as nodes
except ImportError:  # pragma: no cover
    nodes = None

# The array types and their element types, written out: libyal's table of array value types.
EXPECTED = {
    0x83: ('SignedByteTypeNode', 1), 0x84: ('UnsignedByteTypeNode', 1), 0x85: ('SignedWordTypeNode', 2),
    0x86: ('UnsignedWordTypeNode', 2), 0x87: ('SignedDwordTypeNode', 4), 0x88: ('UnsignedDwordTypeNode', 4),
    0x89: ('SignedQwordTypeNode', 8), 0x8A: ('UnsignedQwordTypeNode', 8), 0x8B: ('FloatTypeNode', 4),
    0x8C: ('DoubleTypeNode', 8), 0x8F: ('GuidTypeNode', 16), 0x91: ('FiletimeTypeNode', 8),
    0x92: ('SystemtimeTypeNode', 16), 0x94: ('Hex32TypeNode', 4), 0x95: ('Hex64TypeNode', 8),
}


def value(type_, data, length=None):
    return nodes.get_variant_value(data, 0, None, None, type_, length=len(data) if length is None else length)


@unittest.skipIf(nodes is None, 'python-evtx is not installed')
class ArrayValueTest(unittest.TestCase):
    def test_the_lookup_is_the_one_with_array_support_and_installing_twice_changes_nothing(self):
        lookup = nodes.get_variant_value
        self.assertTrue(getattr(lookup, 'dleapp_arrays', False))
        windows_evtx._install_array_values()  # pylint: disable=protected-access
        self.assertIs(nodes.get_variant_value, lookup)
        self.assertFalse(getattr(lookup.original, 'dleapp_arrays', False))

    def test_the_table_is_the_fixed_width_arrays_and_each_element_size_is_python_evtx_s(self):
        self.assertEqual(windows_evtx._ARRAY_ELEMENTS, EXPECTED)  # pylint: disable=protected-access
        for name, size in EXPECTED.values():
            self.assertEqual(getattr(nodes, name)(bytes(32), 0, None, None).tag_length(), size, name)

    def test_an_array_of_unsigned_64_bit_integers(self):
        data = struct.pack('<3Q', 1, 2, 2 ** 64 - 1)
        node = value(0x8A, data)
        self.assertEqual(node.string(), '<string>1</string>\n<string>2</string>\n<string>18446744073709551615</string>\n')
        self.assertEqual((node.length(), node.tag_length()), (24, 24))

    def test_signed_values_hex_values_and_guids_render_as_python_evtx_renders_one(self):
        self.assertEqual(value(0x89, struct.pack('<2q', -1, 5)).string(), '<string>-1</string>\n<string>5</string>\n')
        self.assertEqual(value(0x83, bytes([0xFF, 0x01])).string(), '<string>-1</string>\n<string>1</string>\n')
        self.assertEqual(value(0x84, bytes([0xFF, 0x01])).string(), '<string>255</string>\n<string>1</string>\n')
        self.assertEqual(value(0x86, struct.pack('<2H', 65535, 7)).string(), '<string>65535</string>\n<string>7</string>\n')
        self.assertEqual(value(0x95, struct.pack('<Q', 0x0706050403020100)).string(), '<string>0x0706050403020100</string>\n')
        self.assertEqual(value(0x94, struct.pack('<I', 0x0A)).string(), '<string>0x0000000a</string>\n')
        guid = bytes(range(16))
        self.assertEqual(value(0x8F, guid).string(), f'<string>{nodes.GuidTypeNode(guid, 0, None, None).string()}</string>\n')

    def test_an_element_at_an_offset_is_read_from_that_offset(self):
        data = b'\xAA' * 5 + struct.pack('<2I', 9, 10)
        node = nodes.get_variant_value(data, 5, None, None, 0x88, length=8)
        self.assertEqual(node.string(), '<string>9</string>\n<string>10</string>\n')

    def test_an_empty_array_renders_nothing(self):
        self.assertEqual(value(0x8A, b'').string(), '')

    def test_a_size_that_is_not_whole_elements_or_no_size_still_raises(self):
        with self.assertRaises(ValueError):
            value(0x8A, bytes(12))
        with self.assertRaises(NotImplementedError):
            nodes.get_variant_value(bytes(8), 0, None, None, 0x8A)

    def test_other_types_go_to_python_evtx_unchanged(self):
        self.assertIsInstance(value(0x0A, struct.pack('<Q', 5)), nodes.UnsignedQwordTypeNode)
        self.assertIsInstance(value(0x81, 'a\x00'.encode('utf-16-le')), nodes.WstringArrayTypeNode)
        for left_out in (0x82, 0x8D, 0x90, 0x93):
            with self.assertRaises(KeyError):
                value(left_out, bytes(8))

    def test_classic_strings_splits_an_array_rendering(self):
        self.assertEqual(windows_evtx.classic_strings([value(0x8A, struct.pack('<2Q', 3, 4)).string()]), ['3', '4'])


if __name__ == '__main__':
    unittest.main()
