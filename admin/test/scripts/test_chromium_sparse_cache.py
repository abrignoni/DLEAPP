"""Pin how a sparse blockfile entry is put back together from its Range_ children.

The layout follows net/disk_cache/blockfile/sparse_control.cc and disk_format_base.h at
Chromium 65.0.3325.181: the parent keeps a SparseHeader (signature, kIndexMagic, key length,
last_block, last_block_len, 40 bytes of padding) and a bitmap of its children in stream 2;
child N, keyed Range_<parent key>:<signature>:<N> in hexadecimal, holds the parent's bytes from
N * 1 MiB in stream 1, and in stream 2 the same header and a bitmap of the 1 KiB blocks it holds.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from scripts.chromium import blockfile_cache  # pylint: disable=wrong-import-position
import test_discord_blockfile_cache as fixture  # pylint: disable=wrong-import-position

MAGIC = 0xC103CAC3
SIGNATURE = 0x1D2C3B4A5F607182
MIB = 0x100000


def _header(signature=SIGNATURE, last_block=-1, last_block_len=0, magic=MAGIC):
    return struct.pack('<qIiii40x', signature, magic, 0, last_block, last_block_len)


def _bitmap(bits, size_bytes):
    out = bytearray(size_bytes)
    for bit in bits:
        out[bit // 8] |= 1 << (bit % 8)
    return bytes(out)


def _response(total):
    """An HttpResponseInfo pickle of version 3, as test_chromium_http_cache.py builds one."""
    lines = ['HTTP/1.1 206', 'content-type: video/mp4', f'content-length: {total}',
             f'content-range: bytes 0-{total - 1}/{total}']
    headers = b'\x00'.join(line.encode('latin-1') for line in lines) + b'\x00\x00'
    body = struct.pack('<i', 3) + struct.pack('<2q', 100, 200)
    body += struct.pack('<i', len(headers)) + headers + b'\x00' * (-len(headers) % 4)
    return struct.pack('<I', len(body)) + body


class SparseCache(fixture.BlockfileCache):
    """The fixture writer, with an entry whose key and three streams are given whole."""

    def add_raw(self, key, stream0, stream1, stream2, bucket=0):
        key = key.encode()
        rankings = self._store(0, struct.pack('<Q', 1))
        addresses = []
        for stream in (stream0, stream1, stream2):
            if not stream:
                addresses.append(0)
            elif len(stream) > 4 * 1024:
                addresses.append(self._store_external(stream))
            else:
                addresses.append(self._store(2, stream))
        record = bytearray(256)
        struct.pack_into('<I', record, 4, self.table[bucket])
        struct.pack_into('<I', record, 8, rankings)
        struct.pack_into('<iI', record, 32, len(key), 0)
        record[96:96 + len(key)] = key
        struct.pack_into('<4i', record, 40, len(stream0), len(stream1), len(stream2), 0)
        struct.pack_into('<4I', record, 56, *addresses, 0)
        address = self._store(1, bytes(record))
        self.table[bucket] = address
        return address


def _child_blocks(length):
    full, part = divmod(length, 1024)
    return list(range(full)), (full, part) if part else (-1, 0)


class SparseBodyTest(unittest.TestCase):
    PARENT = 'https://media.example/clip.mp4'

    def _build(self, total, children, child_signature=SIGNATURE, child_magic=MAGIC, marked=None, holes=()):
        """children: {number: bytes}; marked: {number: length the bitmap covers} when not all;
        holes: block numbers of child 0 left out of its bitmap."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__('shutil').rmtree(tmp))
        cache = SparseCache(os.path.join(tmp, 'Media Cache'), table_length=16)
        cache.add_raw(self.PARENT, _response(total), b'',
                      _header() + _bitmap(children, 4), bucket=0)
        for bucket, (number, data) in enumerate(sorted(children.items()), start=1):
            blocks, (last, last_len) = _child_blocks((marked or {}).get(number, len(data)))
            if number == 0:
                blocks = [block for block in blocks if block not in holes]
            stream2 = _header(child_signature, last, last_len, child_magic) + _bitmap(blocks, 128)
            cache.add_raw(f'Range_{self.PARENT}:{SIGNATURE:x}:{number:x}', b'', data, stream2, bucket=bucket)
        files = cache.write()
        entries = list(blockfile_cache.iter_entries(files, folder_names=('Media Cache',)))
        parent = next(e for e in entries if e.key == self.PARENT)
        return parent, blockfile_cache.sparse_children(entries)

    def test_children_that_hold_every_byte_give_the_whole_body(self):
        data = bytes(range(256)) * (MIB // 256) + b'tail' * 300
        parent, children = self._build(len(data), {0: data[:MIB], 1: data[MIB:]})
        self.assertEqual(blockfile_cache.sparse_body(parent, children, len(data)), data)

    def test_a_part_filled_last_block_counts_its_recorded_length(self):
        data = b'x' * 3000
        parent, children = self._build(3000, {0: data})
        self.assertEqual(blockfile_cache.sparse_body(parent, children, 3000), data)

    def test_a_missing_child_gives_nothing(self):
        data = b'a' * (2 * MIB + 10)
        parent, children = self._build(len(data), {0: data[:MIB], 2: data[2 * MIB:]})
        self.assertIsNone(blockfile_cache.sparse_body(parent, children, len(data)))

    def test_a_block_missing_from_the_bitmap_is_a_gap(self):
        data = b'f' * 3072
        parent, children = self._build(3072, {0: data}, holes=(1,))
        self.assertIsNone(blockfile_cache.sparse_body(parent, children, 3072))

    def test_bytes_the_bitmap_does_not_mark_are_not_read(self):
        data = b'b' * 2048
        parent, children = self._build(2048, {0: data}, marked={0: 1024})
        self.assertIsNone(blockfile_cache.sparse_body(parent, children, 2048))

    def test_a_child_with_another_signature_is_not_used(self):
        data = b'c' * 4096
        parent, children = self._build(4096, {0: data}, child_signature=SIGNATURE + 1)
        self.assertIsNone(blockfile_cache.sparse_body(parent, children, 4096))

    def test_a_child_without_the_index_magic_is_not_used(self):
        data = b'd' * 4096
        parent, children = self._build(4096, {0: data}, child_magic=0)
        self.assertIsNone(blockfile_cache.sparse_body(parent, children, 4096))

    def test_the_body_is_cut_at_the_resource_size(self):
        data = b'e' * 5000
        parent, children = self._build(4000, {0: data})
        self.assertEqual(blockfile_cache.sparse_body(parent, children, 4000), data[:4000])


class SparseMediaRowTest(unittest.TestCase):
    def test_a_complete_sparse_video_is_checked_in_and_its_body_size_kept(self):
        from scripts.artifacts import chromiumCacheRecords as module  # pylint: disable=import-outside-toplevel
        data = b'\x00\x00\x00\x08free' * 512
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = os.path.join(tmp, 'Users', 'u', 'AppData', 'Local', 'Google', 'Chrome',
                                     'User Data', 'Default', 'Media Cache')
            cache = SparseCache(cache_dir, table_length=4)
            cache.add_raw(SparseBodyTest.PARENT, _response(len(data)), b'', _header() + _bitmap([0], 4))
            blocks, (last, last_len) = _child_blocks(len(data))
            cache.add_raw(f'Range_{SparseBodyTest.PARENT}:{SIGNATURE:x}:0', b'', data,
                          _header(last_block=last, last_block_len=last_len) + _bitmap(blocks, 128), bucket=1)
            cache.write()
            checked = []
            original = module.check_in_embedded_media
            module.check_in_embedded_media = lambda source, body, **kw: checked.append(body) or 'media-ref'
            try:
                entries = list(blockfile_cache.iter_entries(
                    [os.path.join(cache_dir, 'index')], folder_names=('Media Cache',)))
                children = blockfile_cache.sparse_children(entries)
                parent = next(e for e in entries if e.key == SparseBodyTest.PARENT)
                parsed = module.parse_response_info(parent.response_info)
                self.assertIsNotNone(parsed)
                ref = module._media(parent, cache_dir, 'video/mp4', parsed[3], parsed[4], '206',  # pylint: disable=protected-access
                                    children)
            finally:
                module.check_in_embedded_media = original
        self.assertEqual(ref, 'media-ref')
        self.assertEqual(checked, [data])
        self.assertEqual(parent.body_size, 0)


if __name__ == '__main__':
    unittest.main()
