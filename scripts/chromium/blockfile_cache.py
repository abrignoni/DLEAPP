"""Read Chromium's legacy blockfile HTTP cache.

The v3 cache consists of an ``index`` hash table, fixed-block ``data_N`` files,
and external ``f_XXXXXX`` streams. Structure sizes and address masks follow
Chromium's published ``net/disk_cache/blockfile`` format.

Author: @AlexisBrignoni, Codex
"""

import os
import struct

from scripts.chromium.cache_key import key_to_url
from scripts.chromium.simple_cache import (
    base_time_to_datetime,
    decode_body,
    parse_response_info,
)

_INDEX_MAGIC = 0xC103CAC3
_INDEX_HEADER_SIZE = 368
_DEFAULT_TABLE_LENGTH = 0x10000
_BLOCK_HEADER_SIZE = 8192
_BLOCK_SIZES = {1: 36, 2: 256, 3: 1024, 4: 4096}
_INITIALIZED_MASK = 0x80000000


class BlockfileEntry:
    """One recoverable cache entry."""

    __slots__ = (
        "address", "source", "key", "url", "key_prefix", "created",
        "last_used", "request_time", "response_time", "status_code",
        "status_line", "headers", "body_size", "body_source",
        "body_address", "cache_dir", "reuse_count", "response_info",
        "sparse_size", "sparse_address",
    )

    def __init__(self):
        self.address = 0
        self.source = ""
        self.key = ""
        self.url = ""
        self.key_prefix = ""
        self.created = ""
        self.last_used = ""
        self.request_time = ""
        self.response_time = ""
        self.status_code = ""
        self.status_line = ""
        self.headers = {}
        self.body_size = 0
        self.body_source = ""
        self.body_address = 0
        self.cache_dir = ""
        self.reuse_count = 0
        self.response_info = b""
        self.sparse_size = 0
        self.sparse_address = 0

    @property
    def content_type(self):
        return self.headers.get("content-type", "")

    @property
    def content_encoding(self):
        return self.headers.get("content-encoding", "")

    @property
    def etag(self):
        return self.headers.get("etag", "")

    def read_body(self):
        """Return the stored response body."""
        body, _ = _read_address(self.cache_dir, self.body_address, self.body_size)
        return body

    def read_sparse_data(self):
        """Return stream 2, where a sparse entry and its children keep their SparseData."""
        data, _ = _read_address(self.cache_dir, self.sparse_address, self.sparse_size)
        return data

    def decoded_body(self):
        """Return the response body with supported Content-Encoding removed."""
        return decode_body(self.read_body(), self.content_encoding.lower())


def _address_parts(address):
    return {
        "initialized": bool(address & _INITIALIZED_MASK),
        "file_type": (address >> 28) & 0x7,
        "blocks": ((address >> 24) & 0x3) + 1,
        "selector": (address >> 16) & 0xFF,
        "index": address & 0xFFFF,
        "external": address & 0x0FFFFFFF,
    }


def _read_address(cache_dir, address, size=None):
    parts = _address_parts(address)
    if not parts["initialized"]:
        return b"", ""
    if parts["file_type"] == 0:
        path = os.path.join(cache_dir, f"f_{parts['external']:06x}")
        offset = 0
        available = size
    elif parts["file_type"] in _BLOCK_SIZES:
        path = os.path.join(cache_dir, f"data_{parts['selector']}")
        block_size = _BLOCK_SIZES[parts["file_type"]]
        offset = _BLOCK_HEADER_SIZE + (parts["index"] * block_size)
        available = parts["blocks"] * block_size
        if size is not None:
            available = min(size, available)
    else:
        return b"", ""
    try:
        with open(path, "rb") as handle:
            handle.seek(offset)
            return handle.read(available), path
    except OSError:
        return b"", path


def _entry(cache_dir, address):
    raw, source = _read_address(cache_dir, address)
    if len(raw) < 256:
        return None, 0
    try:
        next_address = struct.unpack_from("<I", raw, 4)[0]
        reuse_count = struct.unpack_from("<i", raw, 12)[0]
        state = struct.unpack_from("<i", raw, 20)[0]
        created = struct.unpack_from("<Q", raw, 24)[0]
        key_length, long_key = struct.unpack_from("<iI", raw, 32)
        data_sizes = struct.unpack_from("<4i", raw, 40)
        data_addresses = struct.unpack_from("<4I", raw, 56)
    except struct.error:
        return None, 0
    if state != 0 or key_length <= 0 or key_length > 1_000_000:
        return None, next_address
    if long_key:
        key_raw, _ = _read_address(cache_dir, long_key, key_length)
    else:
        key_raw = raw[96:96 + key_length]
    if len(key_raw) != key_length:
        return None, next_address

    item = BlockfileEntry()
    item.cache_dir = cache_dir
    item.address = address
    item.source = source
    item.key = key_raw.rstrip(b"\x00").decode("utf-8", "replace")
    item.key_prefix, item.url = key_to_url(item.key)
    item.created = base_time_to_datetime(created)

    ranking_address = struct.unpack_from("<I", raw, 8)[0]
    ranking, _ = _read_address(cache_dir, ranking_address, 36)
    if len(ranking) >= 8:
        item.last_used = base_time_to_datetime(struct.unpack_from("<Q", ranking)[0])

    stream0, _ = _read_address(cache_dir, data_addresses[0], data_sizes[0])
    item.reuse_count = reuse_count
    item.response_info = stream0
    (request_time, response_time, item.status_line,
     item.headers) = parse_response_info(stream0)
    item.request_time = base_time_to_datetime(request_time)
    item.response_time = base_time_to_datetime(response_time)
    if item.status_line:
        pieces = item.status_line.split()
        item.status_code = pieces[1] if len(pieces) > 1 else ""

    item.body_size = max(data_sizes[1], 0)
    item.body_address = data_addresses[1]
    _, item.body_source = _read_address(
        cache_dir, data_addresses[1], min(item.body_size, 1))
    item.sparse_size = max(data_sizes[2], 0)
    item.sparse_address = data_addresses[2]
    return item, next_address


def iter_entries(files_found, folder_names=("Cache_Data",)):
    """Yield valid entries from each distinct cache folder represented.

    A cache folder is the folder of a found file when its name is one of
    ``folder_names``; only a folder whose ``index`` carries the blockfile magic
    is read. Chromium and WebView2 keep the cache in Cache_Data, while some
    Electron apps (Discord on Windows) keep it directly in a folder named Cache.
    """
    folders = {}
    for file_found in map(str, files_found):
        parent = os.path.dirname(file_found)
        if os.path.basename(parent) in folder_names:
            folders.setdefault(os.path.realpath(parent), parent)

    for cache_dir in folders.values():
        index_path = os.path.join(cache_dir, "index")
        try:
            with open(index_path, "rb") as handle:
                index = handle.read()
        except OSError:
            continue
        if len(index) < _INDEX_HEADER_SIZE:
            continue
        magic, _version = struct.unpack_from("<II", index)
        if magic != _INDEX_MAGIC:
            continue
        table_length = struct.unpack_from("<I", index, 28)[0]
        table_length = table_length or _DEFAULT_TABLE_LENGTH
        table_bytes = table_length * 4
        if len(index) < _INDEX_HEADER_SIZE + table_bytes:
            continue

        seen = set()
        for address, in struct.iter_unpack(
                "<I", index[_INDEX_HEADER_SIZE:_INDEX_HEADER_SIZE + table_bytes]):
            while address and address not in seen:
                seen.add(address)
                item, next_address = _entry(cache_dir, address)
                if item is not None:
                    yield item
                address = next_address


# Sparse entries, as net/disk_cache/blockfile/sparse_control.cc writes them at
# https://github.com/chromium/chromium/blob/65.0.3325.181/net/disk_cache/blockfile/sparse_control.cc#L34-L59:
# the parent keeps a SparseHeader and a bitmap of its children in stream 2; each
# child, keyed Range_<parent key>:<signature>:<child number> (both in hexadecimal),
# holds up to 1 MiB of the parent's data from offset child number * 1 MiB in its
# stream 1, and in its stream 2 the parent's header and a bitmap of which 1 KiB
# blocks it holds, with last_block and last_block_len for a part-filled block.
_SPARSE_MAGIC = 0xC103CAC3   # kIndexMagic, net/disk_cache/blockfile/disk_format.h
_SPARSE_HEADER = struct.Struct("<qIiii40x")   # SparseHeader, disk_format_base.h
_CHILD_SIZE = 0x100000        # kMaxEntrySize
_SPARSE_BLOCK = 1024          # kBlockSize
_CHILD_BITS = 1024            # kNumSparseBits


def _bits(bitmap, count=None):
    count = len(bitmap) * 8 if count is None else count
    return [i for i in range(count) if bitmap[i // 8] >> (i % 8) & 1]


def _sparse_header(data):
    if len(data) < _SPARSE_HEADER.size:
        return None
    signature, magic, _key_len, last_block, last_block_len = _SPARSE_HEADER.unpack_from(data)
    if magic != _SPARSE_MAGIC:
        return None
    if not 0 <= last_block_len < _SPARSE_BLOCK:
        # As SparseControl::OpenChild does, a length out of range means no part-filled block.
        last_block, last_block_len = -1, 0
    return signature, last_block, last_block_len


def sparse_children(entries):
    """Map (parent key, signature) to {child number: entry} for every Range_ child."""
    children = {}
    for entry in entries:
        if not entry.key.startswith("Range_"):
            continue
        try:
            parent_key, signature, number = entry.key[6:].rsplit(":", 2)
            key = (parent_key, int(signature, 16))
            children.setdefault(key, {})[int(number, 16)] = entry
        except ValueError:
            continue
    return children


def _child_ranges(child, signature, base):
    """The (start, end) offsets in the parent that a child holds, as SparseControl reads them."""
    header = _sparse_header(child.read_sparse_data())
    if header is None or header[0] != signature:
        return []
    _, last_block, last_block_len = header
    data = child.read_body()
    bitmap = child.read_sparse_data()[_SPARSE_HEADER.size:_SPARSE_HEADER.size + _CHILD_BITS // 8]
    present = set(_bits(bitmap, min(_CHILD_BITS, len(bitmap) * 8)))
    ranges, block = [], 0
    while block < _CHILD_BITS:
        if block in present:
            end = block
            while end in present:
                end += 1
            stop = end * _SPARSE_BLOCK
            if end == last_block:
                stop += last_block_len
            ranges.append((block * _SPARSE_BLOCK, stop))
            block = end + 1 if end == last_block else end
        else:
            if block == last_block and last_block_len:
                ranges.append((block * _SPARSE_BLOCK, block * _SPARSE_BLOCK + last_block_len))
            block += 1
    return [(base + start, base + min(stop, len(data)), data, start)
            for start, stop in ranges if min(stop, len(data)) > start]


def sparse_body(parent, children, resource_size):
    """The parent's data put back together from its children, or None.

    Returned only when the children hold every byte from 0 to ``resource_size``
    with no gap; a child counts only if its own header carries the parent's
    signature, and only the blocks its bitmap marks are read.
    """
    if resource_size <= 0:
        return None
    header = _sparse_header(parent.read_sparse_data())
    if header is None:
        return None
    signature = header[0]
    kids = children.get((parent.key, signature), {})
    pieces = []
    for number in sorted(kids):
        pieces.extend(_child_ranges(kids[number], signature, number * _CHILD_SIZE))
    pieces.sort(key=lambda piece: piece[0])
    out = bytearray()
    for start, stop, data, data_start in pieces:
        if start > len(out):
            return None
        if stop > len(out):
            skip = len(out) - start
            out += data[data_start + skip:data_start + (stop - start)]
        if len(out) >= resource_size:
            return bytes(out[:resource_size])
    return None
