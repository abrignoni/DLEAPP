"""Reader for the Chromium "Simple Cache" HTTP cache format.

Modern Chromium (and therefore every current Electron app) stores its HTTP
disk cache as one file per resource, named ``<64-bit hash>_0``, inside a
``Cache_Data`` folder. Service-worker Cache Storage uses the same format.

Entry file layout (``simple_entry_format.h``)::

    SimpleFileHeader           24 bytes (20 bytes of fields + 4 padding)
        uint64 initial_magic_number   0xfcfb6d1ba7725c30
        uint32 version                5 for current Chromium
        uint32 key_length
        uint32 key_hash
    key                        key_length bytes
    stream 1                   the HTTP response body
    SimpleFileEOF (stream 1)   24 bytes
    stream 0                   the serialised HttpResponseInfo
    key SHA-256                32 bytes, only when flags & FLAG_HAS_KEY_SHA256
    SimpleFileEOF (stream 0)   24 bytes

Stream 0 holds a Chromium Pickle::

    uint32 payload_size
    int32  flags
    int64  request_time        microseconds since 1601-01-01 UTC
    int64  response_time
    uint32 raw_header_length
    raw headers                NUL-separated, status line first

Entries whose name ends in ``_1``/``_s`` (secondary streams, sparse ranges)
are not entry files and are skipped by :func:`iter_entries`.
"""

import gzip
import os
import re
import struct
import zlib
from datetime import datetime, timedelta, timezone

SIMPLE_HEADER_MAGIC = 0xFCFB6D1BA7725C30
SIMPLE_EOF_MAGIC = 0xF4FA6F45970D41D8

_FLAG_HAS_KEY_SHA256 = 2
_HEADER_FIELDS = struct.Struct("<QIII")
_EOF_FIELDS = struct.Struct("<QIII")
_EOF_SIZE = 24
# base::Time counts microseconds from 1601-01-01, the same epoch WebKit uses.
_WINDOWS_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
# Sanity window used to recognise a timestamp field: 1970-01-01 to 2120-01-01.
_MIN_BASE_TIME = 11644473600000000
_MAX_BASE_TIME = 16379827200000000
_URL_IN_KEY_RE = re.compile(r"https?://")
_STATUS_RE = re.compile(r"^HTTP/\d(?:\.\d)?\s+(\d{3})")


def base_time_to_datetime(value):
    """Convert a base::Time internal value to an aware UTC datetime."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    try:
        return _WINDOWS_EPOCH + timedelta(microseconds=value)
    except (OverflowError, OSError, ValueError):
        return ""


class CacheEntry:
    """One cached HTTP response."""

    __slots__ = ("path", "key", "url", "key_prefix", "request_time",
                 "response_time", "status_code", "status_line", "headers",
                 "body_offset", "body_size")

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))

    @property
    def content_type(self):
        return (self.headers or {}).get("content-type", "")

    @property
    def content_encoding(self):
        return (self.headers or {}).get("content-encoding", "").strip().lower()

    def read_body(self):
        """Read the raw (still compressed) response body from disk."""
        if not self.body_size:
            return b""
        try:
            with open(self.path, "rb") as handle:
                handle.seek(self.body_offset)
                return handle.read(self.body_size)
        except OSError:
            return b""

    def decoded_body(self):
        """Read the body and undo its Content-Encoding where possible.

        Returns the raw bytes when the encoding is unsupported or the data is
        truncated, so callers can still carve or hash what survived.
        """
        return decode_body(self.read_body(), self.content_encoding)


def decode_body(data, encoding):
    """Decompress ``data`` according to an HTTP Content-Encoding value."""
    if not data or not encoding:
        return data
    try:
        if encoding == "gzip":
            return gzip.decompress(data)
        if encoding == "deflate":
            try:
                return zlib.decompress(data)
            except zlib.error:
                return zlib.decompress(data, -zlib.MAX_WBITS)
        if encoding == "br":
            import brotli  # optional dependency

            return brotli.decompress(data)
        if encoding == "zstd":
            try:
                from compression import zstd  # Python 3.14+
            except ImportError:
                import zstandard

                return zstandard.ZstdDecompressor().decompress(data)
            return zstd.decompress(data)
    except Exception:
        # A partially evicted or unsupported body is still worth returning raw.
        return data
    return data


def key_to_url(key):
    """Split a Chromium cache key into its isolation prefix and the URL.

    Keys carry a network-isolation prefix such as ``1/0/`` or
    ``_dk_https://site https://site `` ahead of the request URL.
    """
    if not key:
        return "", ""
    match = _URL_IN_KEY_RE.search(key)
    if not match:
        return key, ""
    return key[:match.start()], key[match.start():]


def _plausible_time(value):
    """True when a base::Time internal value falls between 1970 and 2120."""
    return _MIN_BASE_TIME <= value <= _MAX_BASE_TIME


def _parse_response_info(stream0):
    """Pull request/response times and raw headers out of an HttpResponseInfo.

    The pickle is ``payload_size, flags, <times>, header_length, headers``, but
    the number of time fields has grown across Chromium versions (an
    original-response time was added alongside request and response time). So
    the header block is located by its status line and the times are read
    backwards from it, which keeps the parse version independent.
    """
    if len(stream0) < 28:
        return None, None, "", {}

    header_start = stream0.find(b"HTTP/")
    if header_start >= 12:
        header_length, = struct.unpack_from("<I", stream0, header_start - 4)
        times = []
        offset = header_start - 4
        while offset >= 12:
            candidate, = struct.unpack_from("<q", stream0, offset - 8)
            if not _plausible_time(candidate):
                break
            times.insert(0, candidate)
            offset -= 8
        request_time = times[0] if times else None
        response_time = times[1] if len(times) > 1 else request_time
    else:
        # No status line: fall back to the historical fixed layout, and only
        # trust the times it yields if they land in a believable range. Cache
        # Storage entries reach here and do not carry an HttpResponseInfo.
        header_start = 28
        request_time, response_time = struct.unpack_from("<qq", stream0, 8)
        header_length, = struct.unpack_from("<I", stream0, 24)
        if not _plausible_time(request_time):
            request_time = None
        if not _plausible_time(response_time):
            response_time = None
        if header_length > len(stream0) - header_start:
            header_length = 0

    raw = stream0[header_start:header_start + header_length]

    headers = {}
    status_line = ""
    for chunk in raw.split(b"\x00"):
        if not chunk:
            continue
        line = chunk.decode("latin-1")
        if not status_line and line.startswith("HTTP/"):
            status_line = line.strip()
        elif ":" in line:
            name, value = line.split(":", 1)
            name = name.strip().lower()
            value = value.strip()
            # Repeated headers (set-cookie) keep every value.
            if name in headers:
                headers[name] = f"{headers[name]}\n{value}"
            else:
                headers[name] = value
    return request_time, response_time, status_line, headers


def read_entry(path):
    """Parse one ``*_0`` Simple Cache entry file. Returns None if it is not one.

    Only the header, key and stream 0 are read; the body stays on disk until
    :meth:`CacheEntry.read_body` asks for it.
    """
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            if size < _HEADER_FIELDS.size + _EOF_SIZE:
                return None

            handle.seek(0)
            magic, _version, key_length, _key_hash = _HEADER_FIELDS.unpack(
                handle.read(_HEADER_FIELDS.size))
            if magic != SIMPLE_HEADER_MAGIC:
                return None
            if key_length <= 0 or key_length > size:
                return None

            # The header struct is padded to a multiple of 8, so the key starts
            # at 24. Fall back to the unpadded offset if that does not hold.
            key_offset = 24
            handle.seek(key_offset)
            key_bytes = handle.read(key_length)
            if not _URL_IN_KEY_RE.search(key_bytes.decode("utf-8", "replace")):
                handle.seek(_HEADER_FIELDS.size)
                alternative = handle.read(key_length)
                if _URL_IN_KEY_RE.search(alternative.decode("utf-8", "replace")):
                    key_offset = _HEADER_FIELDS.size
                    key_bytes = alternative
            key = key_bytes.decode("utf-8", "replace")

            handle.seek(size - _EOF_SIZE)
            magic0, flags0, _crc0, stream0_size = _EOF_FIELDS.unpack(
                handle.read(_EOF_FIELDS.size))
            if magic0 != SIMPLE_EOF_MAGIC:
                return None
            sha_length = 32 if flags0 & _FLAG_HAS_KEY_SHA256 else 0
            stream0_start = size - _EOF_SIZE - sha_length - stream0_size
            if stream0_start < 0 or stream0_size < 0:
                return None
            handle.seek(stream0_start)
            stream0 = handle.read(stream0_size)

            body_offset = key_offset + key_length
            body_size = 0
            if stream0_start - _EOF_SIZE >= body_offset:
                handle.seek(stream0_start - _EOF_SIZE)
                magic1, _flags1, _crc1, stream1_size = _EOF_FIELDS.unpack(
                    handle.read(_EOF_FIELDS.size))
                available = stream0_start - _EOF_SIZE - body_offset
                if magic1 == SIMPLE_EOF_MAGIC and 0 <= stream1_size <= available:
                    body_size = stream1_size
    except (OSError, struct.error, ValueError):
        return None

    request_time, response_time, status_line, headers = _parse_response_info(stream0)
    status_match = _STATUS_RE.match(status_line or "")
    prefix, url = key_to_url(key)

    return CacheEntry(
        path=path,
        key=key,
        url=url,
        key_prefix=prefix,
        request_time=request_time,
        response_time=response_time,
        status_code=int(status_match.group(1)) if status_match else None,
        status_line=status_line,
        headers=headers,
        body_offset=body_offset,
        body_size=body_size,
    )


def iter_entries(files_found, url_pattern=None):
    """Yield a :class:`CacheEntry` for every Simple Cache entry in a file list.

    ``url_pattern`` may be a compiled regex or a string; entries whose URL does
    not match are skipped without their bodies ever being read. Symlinked or
    repeated paths are only parsed once.
    """
    if isinstance(url_pattern, str):
        url_pattern = re.compile(url_pattern)

    seen = set()
    for file_found in files_found:
        file_found = str(file_found)
        if not file_found.endswith("_0"):
            continue
        try:
            real = os.path.realpath(file_found)
        except OSError:
            real = file_found
        if real in seen:
            continue
        seen.add(real)

        entry = read_entry(file_found)
        if entry is None:
            continue
        if url_pattern and not url_pattern.search(entry.url):
            continue
        yield entry
