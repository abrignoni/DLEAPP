"""Split a Chromium HTTP cache entry key into its prefix, isolation key and URL.

Kept apart from the cache readers so the simple cache, blockfile cache and
http_cache modules all use this one split without importing each other.

Chrome 65 keys are the request URL, preceded by "<upload id>/" for an upload
(net/http/http_cache.cc, lines 570-583 at 65.0.3325.181). Current keys are
"<credential>/<upload id>/", then, when the cache is split by site, "_dk_" with
an "s_" or "cn_" marker, the isolation key and a space, then the URL
(http_cache.cc, lines 825-893 at chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
Chromium recovers the URL as the text after the rightmost space of a double key
(GetResourceURLFromHttpCacheKey, lines 783-819 at the same commit).
"""

import re

# Any text ahead of the numbered part is kept as stored. A "Range_" marker is the prefix
# Chromium's sparse control gives a child entry, Range_<parent key>:<signature>:<child>
# (net/disk_cache/blockfile/sparse_control.cc, lines 54-64 at chromium 33f34ef); the rest
# of such a key, the parent key and the two numbers, is kept as the URL.
_NUMBERED_PREFIX = re.compile(r'^(?:[A-Za-z]+_)?(?:\d+/){1,2}|^[A-Za-z]+_(?=_dk_|https?:)')
_DOUBLE_KEY = '_dk_'
_URL_OR_DOUBLE_KEY = re.compile(r'^(?:_dk_|[A-Za-z][A-Za-z0-9+.-]*://)')


def split_key(key):
    """(numbered prefix, isolation key, url) of a cache entry key.

    The isolation key is the text between "_dk_" and the URL, with its "s_" or
    "cn_" marker kept; it is '' for a key that is not double keyed.
    """
    if not key:
        return '', '', ''
    match = _NUMBERED_PREFIX.match(key)
    prefix = match.group(0) if match else ''
    rest = key[len(prefix):]
    if not _URL_OR_DOUBLE_KEY.match(rest):
        # Not an HTTP resource key (a quicserverinfo: entry, for one): kept whole.
        return key, '', ''
    if rest.startswith(_DOUBLE_KEY):
        space = rest.rfind(' ')
        if space < 0:
            return prefix, rest[len(_DOUBLE_KEY):], ''
        return prefix, rest[len(_DOUBLE_KEY):space], rest[space + 1:]
    return prefix, '', rest


def key_to_url(key):
    """(text ahead of the URL, URL) of a cache entry key, split as split_key splits it.

    The first part is the whole key when no URL is found in it.
    """
    _prefix, _isolation, url = split_key(key)
    if not url:
        return key or "", ""
    return key[:len(key) - len(url)], url
