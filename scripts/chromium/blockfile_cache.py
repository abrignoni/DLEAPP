"""Read Chromium's legacy blockfile HTTP cache.

The v3 cache consists of an ``index`` hash table, fixed-block ``data_N`` files,
and external ``f_XXXXXX`` streams. Structure sizes and address masks follow
Chromium's published ``net/disk_cache/blockfile`` format.

Author: @AlexisBrignoni, Codex
"""

import os
import re
import struct

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
_URL_RE = re.compile(r"https?://")


class BlockfileEntry:
    """One recoverable cache entry."""

    __slots__ = (
        "address", "source", "key", "url", "key_prefix", "created",
        "last_used", "request_time", "response_time", "status_code",
        "status_line", "headers", "body_size", "body_source",
        "body_address", "cache_dir",
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


def _key_to_url(key):
    matches = list(_URL_RE.finditer(key))
    if not matches:
        return key, ""
    match = matches[-1]
    return key[:match.start()], key[match.start():]


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
    item.key_prefix, item.url = _key_to_url(item.key)
    item.created = base_time_to_datetime(created)

    ranking_address = struct.unpack_from("<I", raw, 8)[0]
    ranking, _ = _read_address(cache_dir, ranking_address, 36)
    if len(ranking) >= 8:
        item.last_used = base_time_to_datetime(struct.unpack_from("<Q", ranking)[0])

    stream0, _ = _read_address(cache_dir, data_addresses[0], data_sizes[0])
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
    return item, next_address


def iter_entries(files_found):
    """Yield valid entries from each distinct Cache_Data folder represented."""
    folders = {}
    for file_found in map(str, files_found):
        parent = os.path.dirname(file_found)
        if os.path.basename(parent) == "Cache_Data":
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
