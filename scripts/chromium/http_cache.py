"""Read the parts of a Chromium HTTP cache entry that name and time the response.

Two pieces, both read as Chromium writes them, at chromium
33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and at the 65.0.3325.181 tag:

* The entry key. Chrome 65 keys are the request URL, preceded by
  "<upload id>/" for an upload (net/http/http_cache.cc, lines 570-583 at
  65.0.3325.181). Current keys are "<credential>/<upload id>/", then, when the
  cache is split by site, "_dk_" with an "s_" or "cn_" marker, the isolation key
  and a space, then the URL (http_cache.cc, lines 825-893); Chromium recovers
  the URL after the rightmost space of a double key (lines 783-819).
* Stream 0, the pickled HttpResponseInfo: flags, extra flags when flag bit 31
  is set, the request time, the response time, the original response time when
  extra flag RESPONSE_EXTRA_INFO_HAS_ORIGINAL_RESPONSE_TIME is set, then the raw
  headers as a pickled string (net/http/http_response_info.cc, lines 168-209;
  lines 130-158 at 65.0.3325.181). Times are base::Time internal values,
  microseconds since 1601-01-01 UTC.
"""

import struct

from scripts.chromium.cache_key import split_key  # pylint: disable=unused-import
from scripts.chromium.simple_cache import decode_body

_RESPONSE_INFO_HAS_EXTRA_FLAGS = 1 << 31
# http_response_info.cc lines 140-157.
_RESPONSE_EXTRA_INFO_HAS_ORIGINAL_RESPONSE_TIME = 1 << 2
RESPONSE_EXTRA_INFO_HAS_ZSTD_UNCOMPRESSED_BODY_SIZE = 1 << 4
_RESPONSE_INFO_VERSION_MASK = 0xFF
def parse_response_info(stream0):
    """(request time, response time, status line, headers, extra flags) of a pickled HttpResponseInfo.

    Times are base::Time internal values, or None. Returns None when the pickle
    does not hold the fields in the order Chromium writes them.
    """
    try:
        payload_size, flags = struct.unpack_from('<Ii', stream0, 0)
        if payload_size + 4 > len(stream0):
            return None
        offset = 8
        extra_flags = 0
        if flags & _RESPONSE_INFO_HAS_EXTRA_FLAGS:
            extra_flags, = struct.unpack_from('<i', stream0, offset)
            offset += 4
        # RESPONSE_INFO_MINIMUM_VERSION and RESPONSE_INFO_VERSION are both 3
        # (http_response_info.cc lines 48-51; lines 46-49 at 65.0.3325.181), and
        # InitFromPickle refuses any other version.
        if flags & _RESPONSE_INFO_VERSION_MASK != 3:
            return None
        request_time, response_time = struct.unpack_from('<qq', stream0, offset)
        offset += 16
        if extra_flags & _RESPONSE_EXTRA_INFO_HAS_ORIGINAL_RESPONSE_TIME:
            offset += 8
        header_length, = struct.unpack_from('<i', stream0, offset)
        offset += 4
        if header_length < 0 or offset + header_length > len(stream0):
            return None
        raw = stream0[offset:offset + header_length]
    except struct.error:
        return None
    status_line = ''
    headers = {}
    for chunk in raw.split(b'\x00'):
        if not chunk:
            continue
        line = chunk.decode('latin-1')
        if not status_line:
            status_line = line.strip()
        elif ':' in line:
            name, value = line.split(':', 1)
            name = name.strip().lower()
            value = value.strip()
            headers[name] = f'{headers[name]}\n{value}' if name in headers else value
    return request_time or None, response_time or None, status_line, headers, extra_flags


def stored_body(raw, extra_flags, content_encoding):
    """A cached body with Chromium's own zstd storage, then its Content-Encoding, undone.

    Chromium zstd-compresses a body on disk when it records
    RESPONSE_EXTRA_INFO_HAS_ZSTD_UNCOMPRESSED_BODY_SIZE (http_response_info.cc lines
    154-156). A body that does not decompress is returned as stored.
    """
    if raw and extra_flags & RESPONSE_EXTRA_INFO_HAS_ZSTD_UNCOMPRESSED_BODY_SIZE:
        raw = decode_body(raw, 'zstd')
    return decode_body(raw, content_encoding)
