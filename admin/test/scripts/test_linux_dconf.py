"""Pin how the dconf artifact reads a GVDB user database. The value bytes below were written by dconf 0.49.0 and GLib
2.88.0 on a lab VM for keys set to known values, and each expected text is the line dconf dump printed for that key."""
import os
import pathlib
import base64
import struct
import sys
import tempfile
import zlib
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxDconf as dc
# pylint: enable=wrong-import-position

KNOWN = {
    'backslash': ('6261636b5c736c617368000073',
                   "'back\\\\slash'"),
    'boolean': ('010062',
                 'true'),
    'byte': ('ff0079',
              'byte 0xff'),
    'bytes': ('010200006179',
               "b'\\001\\002'"),
    'bytestring': ('627974657300006179',
                    "b'bytes'"),
    'control': ('6c696e65310a6c696e653209746162000073',
                 "'line1\\nline2\\ttab'"),
    'dict': ('6b3100763100036b320076320003070e00617b73737d',
              "{'k1': 'v1', 'k2': 'v2'}"),
    'dict-variant': ('6e000000000000000100000000690200730000000000000078000073020f1d00617b73767d',
                      "{'n': <1>, 's': <'x'>}"),
    'double': ('9a9999999999b93f0064',
                '0.10000000000000001'),
    'double-exp': ('9c7500883ce4377e0064',
                    '1.0000000000000001e+300'),
    'double-whole': ('00000000000000400064',
                      '2.0'),
    'doubles': ('000000000000f83f000000000000d0bf006164',
                 '[1.5, -0.25]'),
    'empty-dict': ('00617b73737d',
                    '@a{ss} {}'),
    'empty-strv': ('006173',
                    '@as []'),
    'handle': ('030000000068',
                'handle 3'),
    'int16': ('fdff006e',
               'int16 -3'),
    'int32': ('2a0000000069',
               '42'),
    'int64': ('00e68ee7fdffffff0078',
               'int64 -9000000000'),
    'maybe-int': ('05000000006d69',
                   '@mi 5'),
    'maybe-just': ('686572650000006d73',
                    "@ms 'here'"),
    'maybe-nested': ('00006d6d69',
                      '@mmi just nothing'),
    'maybe-nothing': ('006d73',
                       '@ms nothing'),
    'negative': ('f9ffffff0069',
                  '-7'),
    'nested': ('6100000001000000020000000200000062000000020d1500612873616929',
                "[('a', [1, 2]), ('b', [])]"),
    'objectpath': ('2f6f72672f6578616d706c6500006f',
                    "objectpath '/org/example'"),
    'quote': ('697427732071756f746564000073',
               '"it\'s quoted"'),
    'signature': ('617b73767d000067',
                   "signature 'a{sv}'"),
    'string': ('706c61696e20737472696e67000073',
                "'plain string'"),
    'strv': ('610062000204006173',
              "['a', 'b']"),
    'tuple': ('78000000010000000102002873696229',
               "('x', 1, true)"),
    'tuple-one': ('6f6e6c790000287329',
                   "('only',)"),
    'uint16': ('ffff0071',
                'uint16 65535'),
    'uint32': ('070000000075',
                'uint32 7'),
    'uint64': ('ffffffffffffffff0074',
                'uint64 18446744073709551615'),
    'unicode': ('636166c3a920e29883000073',
                 "'café ☃'"),
    'variant': ('696e6e65720000730076',
                 "<'inner'>"),
    'variant-uint': ('0500000000750076',
                      '<uint32 5>'),
}

# Values GLib 2.88.0 serialised (and byte-swapped with g_variant_byteswap) on the lab VM, stored zlib-compressed and
# base64-encoded, with the text g_variant_print (value, TRUE) gave for each. They need 2- and 4-byte framing offsets.
LARGE = {
    'as2': ('eNqrqKA9YKikA2CoogNgSGU4xaDPyJBYDAA28JAA',
            'eNqrqKA9YKikA2CoogNgSGU4xaDPyJBYDAA28JAA',
            'eNqLVq+gA1DXUVCvpAMA2VNFB6AeCwC/kZAH'),
    'as4': ('eNrtwUEBABAABLDTylcUEdBADmG9SLFtDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4MkEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAC+tJPsWpK+LqXDl0M=',
            'eNrtwUEBABAABLDTylcUEdBADmG9SLFtDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4MkEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAC+tJPsWpK+LqXDl0M=',
            'eNrtwTERADAIBDAr3X6po15FgP+BDRVJXgoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFi5Jw0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKz8AYCQlnc='),
    'dict2': ('eNrLzh6MgIGhbFACBobi6QxgkMeAAhoYSpiMGb0ZGRKri8tqAYGsiQc=',
            'eNrLzh6MgIGhbFACBobi6QxgkAehGBqgNEMJkzGjNyNDYnVxWS0AhSyJBw==',
            'eNqrVs8elEDdSsFGvWxQAnU7HQX1PJADSzPzSsxMFCyNjIyNzY0MjM0sTE3MzU0tDCzsagGiG45O'),
    'maybe_str': ('eNrLzR0FxAIGBobcYgCds4Cd',
            'eNrLzR0FxAIGBobcYgCds4Cd',
            'eNpzyC1WUM8dBUQDdQBIbYFL'),
    'tuple2': ('eNpLTBwegCGJAsCQzGBrz8DAzsDAwMV4koFBozixOFMTACxVZnw=',
            'eNpLTBwegCGJAsCQzGBrzwAC7FyMJxkYNIoTizM1ASxAZnw=',
            'eNrTUE8cJkBdRyFaPYkCADRAPVk9VkfBXBMAphBmMg=='),
}


def unpack(text):
    return zlib.decompress(base64.b64decode(text))


def build_gvdb(entries, parent_last=False, swapped=False):
    """A GVDB file holding '/', '/org/', '/org/dleapp/', '/org/dleapp/known/' and a value item per entry.
    entries maps a key name to the raw bytes of its 'v' value. With parent_last the directory items come after
    the values that name them."""
    dirs = [('/', None), ('org/', 0), ('dleapp/', 1), ('known/', 2)]
    values = list(entries.items())
    order = ([('v', k, b) for k, b in values] + [('L', k, p) for k, p in dirs]) if parent_last else         ([('L', k, p) for k, p in dirs] + [('v', k, b) for k, b in values])
    dir_index = {k: i for i, (kind, k, _) in enumerate(order) if kind == 'L'}
    parent_of = {k: p for k, p in dirs}
    items_at = 24 + 8
    blob = bytearray(items_at + 24 * len(order))
    signature = struct.unpack('>II', struct.pack('<II', dc.SIG0, dc.SIG1)) if swapped else (dc.SIG0, dc.SIG1)
    struct.pack_into('<IIII', blob, 0, *signature, 0, 0)
    struct.pack_into('<II', blob, 16, 24, items_at + 24 * len(order))
    struct.pack_into('<II', blob, 24, 0, 0)
    for i, (kind, key, extra) in enumerate(order):
        key_start = len(blob)
        blob += key.encode()
        if kind == 'L':
            parent = 0xffffffff if parent_of[key] is None else dir_index[dirs[parent_of[key]][0]]
            vstart = vend = 0
        else:
            parent = dir_index['known/']
            while len(blob) % 8:
                blob.append(0)
            vstart = len(blob)
            blob += extra
            vend = len(blob)
        struct.pack_into('<IIIHcxII', blob, items_at + 24 * i, 0, parent, key_start, len(key.encode()),
                         kind.encode(), vstart, vend)
    return bytes(blob)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        raise ValueError('no seeker')


class DecodeTest(unittest.TestCase):
    def test_every_known_value_prints_as_dconf_dump(self):
        data = build_gvdb({k: bytes.fromhex(h) for k, (h, _) in KNOWN.items()})
        got = {name: dc.gv_print(node) for name, node in dc.gvdb_values(data)}
        self.assertEqual(got, {'/org/dleapp/known/' + k: text for k, (_, text) in KNOWN.items()})

    def test_parent_after_child(self):
        data = build_gvdb({'string': bytes.fromhex(KNOWN['string'][0])}, parent_last=True)
        self.assertEqual([(n, dc.gv_print(v)) for n, v in dc.gvdb_values(data)],
                         [('/org/dleapp/known/string', "'plain string'")])

    def test_types(self):
        data = build_gvdb({k: bytes.fromhex(h) for k, (h, _) in KNOWN.items()})
        types = {name.rsplit('/', 1)[1]: node[0] for name, node in dc.gvdb_values(data)}
        self.assertEqual((types['dict-variant'], types['maybe-nested'], types['nested'], types['bytes']),
                         ('a{sv}', 'mmi', 'a(sai)', 'ay'))

    def test_bad_input(self):
        with self.assertRaises(dc.GVariantError):
            list(dc.gvdb_values(b'GVariant' + bytes(16)))
        with self.assertRaises(dc.GVariantError):
            list(dc.gvdb_values(b'short'))
        broken = build_gvdb({'string': bytes.fromhex(KNOWN['string'][0])[:-1]})
        (name, error), = dc.gvdb_values(broken)
        self.assertEqual(name, '/org/dleapp/known/string')
        self.assertIsInstance(error, dc.GVariantError)

    def test_large_values_both_byte_orders(self):
        for name, (le, be, text) in LARGE.items():
            expected = unpack(text).decode()
            self.assertEqual(dc.gv_print(dc.decode('v', unpack(le), '<')[1]), expected, name)
            self.assertEqual(dc.gv_print(dc.decode('v', unpack(be), '>')[1]), expected, name)

    def test_byte_swapped_database(self):
        data = build_gvdb({name: unpack(be) for name, (_, be, _) in LARGE.items()}, swapped=True)
        got = {n.rsplit('/', 1)[1]: dc.gv_print(v) for n, v in dc.gvdb_values(data)}
        self.assertEqual(got, {name: unpack(text).decode() for name, (_, _, text) in LARGE.items()})

    def test_printer_rules(self):
        self.assertEqual(dc.gv_print(('d', 1e300)), '1.0000000000000001e+300')
        self.assertEqual(dc.gv_print(('d', float('inf'))), 'inf')
        self.assertEqual(dc.gv_print(('s', 'a\u200bb')), "'a\\u200bb'")
        self.assertEqual(dc.gv_print(('s', 'x\U0001F600')), "'x\U0001F600'")
        self.assertEqual(dc.gv_print(('ay', [('y', 39), ('y', 0)])), 'b"\'"')
        self.assertEqual(dc.gv_print(('ay', [])), '@ay []')
        self.assertEqual(dc.gv_print(('ay', [('y', 0xe9), ('y', 0x41), ('y', 0)])), "b'\\351A'")
        self.assertEqual(dc.gv_print(('ay', [('y', 1), ('y', 0), ('y', 2)])), '[byte 0x01, 0x00, 0x02]')


class ArtifactTest(unittest.TestCase):
    def test_rows(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'home', 'a', '.config', 'dconf')
            os.makedirs(folder)
            good = os.path.join(folder, 'user')
            entries = {'uint32': bytes.fromhex(KNOWN['uint32'][0]), 'string': bytes.fromhex(KNOWN['string'][0]),
                       'broken': bytes.fromhex(KNOWN['string'][0])[:-1]}
            with open(good, 'wb') as handle:
                handle.write(build_gvdb(entries))
            other = os.path.join(root, 'home', 'b', '.config', 'dconf', 'user')
            os.makedirs(os.path.dirname(other))
            open(other, 'wb').close()
            linked = os.path.join(root, 'home', 'a', 'snap', 'x', '.config', 'dconf', 'user')
            os.makedirs(os.path.dirname(linked))
            open(linked, 'wb').close()
            with mock.patch.object(dc, 'logfunc') as log,                     mock.patch.object(dc, 'recorded_link', side_effect=lambda s, p: '/x' if p == linked else None):
                headers, rows, source = dc.linuxDconfUserSettings.__wrapped__(
                    FakeContext([other, good, linked, folder], root))
        self.assertEqual(headers, ('Path', 'Key', 'Type', 'Value', 'Source File'))
        src = 'home/a/.config/dconf/user'
        self.assertEqual(rows, [('/org/dleapp/known/', 'broken', '', '', src),
                                ('/org/dleapp/known/', 'string', 's', "'plain string'", src),
                                ('/org/dleapp/known/', 'uint32', 'u', 'uint32 7', src)])
        self.assertEqual(source, good)
        self.assertEqual([c.args[0] for c in log.call_args_list],
                         ['dconf User Settings: could not read home/b/.config/dconf/user: file shorter than a GVDB '
                          'header',
                          'dconf User Settings: 1 symbolic links to a database, not followed, 1 values that could not '
                          'be decoded, left blank'])


if __name__ == '__main__':
    unittest.main()
