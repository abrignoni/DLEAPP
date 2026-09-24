__artifacts_v2__ = {
    "wireServiceWorkerCache": {
        "name": "Wire Service Worker Cache",
        "description": "Assets cached on disk by the Wire web app's service "
                       "worker (Service Worker/CacheStorage). Each entry records "
                       "the requested asset URL, the resolved CDN (CloudFront) "
                       "download URL and its expiry. Cached asset bodies are Wire "
                       "end-to-end-encrypted (application/octet-stream), so they "
                       "cannot be rendered as images without the asset keys.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Wire (Windows)",
        "notes": "Parses Chromium Simple Cache entry files (*_0). No body is "
                 "decoded; only request/CDN URLs and metadata are extracted. An "
                 "entry can also be matched on any wire.com URL, which admits "
                 "responses that are not assets, so the encrypted-body note is "
                 "shown only where an /assets/ URL was resolved. 'Response Content Type' is the "
                 "value of the Content-Type header stored with the cached response, found by the "
                 "way Chromium's Cache Storage metadata encodes a response header rather than by "
                 "parsing the entry (Reference: Chromium, 'cache_storage.proto', "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/content/browser/cache_storage/cache_storage.proto#L42-L90); "
                 "on wire_win it read application/octet-stream on all 7 rows. 'CDN Expires' "
                 "reads the CloudFront Expires query parameter as Unix seconds. "
                 "Reference: AWS, 'CloudFront signed URLs (Expires is Unix time "
                 "in seconds)', https://docs.aws.amazon.com/AmazonCloudFront/"
                 "latest/DeveloperGuide/private-content-signed-urls.html",
        "paths": ('*/Wire/*Service Worker/CacheStorage/*/*/*_0',),
        "sample_data": {
            "wire_win": "Windows, version not recorded | 7 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Wire profile folder)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Wire profile folder)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Wire profile folder)",
        },
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "hard-drive",
    },
}

import os
import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor

# RFC 3986 URL characters, so a match stops at the first binary byte that
# follows the URL inside the Simple Cache entry.
_URLSAFE = r"[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]"
_ASSET_URL_RE = re.compile(r"https://" + _URLSAFE + r"+/assets/" + _URLSAFE + r"+")
_CDN_URL_RE = re.compile(r"https://prod-assets\.wire\.com/" + _URLSAFE + r"+")
_ANY_WIRE_URL_RE = re.compile(r"https://" + _URLSAFE + r"*wire\.com" + _URLSAFE + r"*")
_ASSET_ID_RE = re.compile(r"/assets/[^/]+/([0-9]+-[0-9]+-[0-9a-f-]{36})")
_EXPIRES_RE = re.compile(r"[?&]Expires=(\d+)")
# Cache Storage keeps each entry's request and response in a CacheMetadata protobuf
# (Chromium content/browser/cache_storage/cache_storage.proto). A response header is a
# CacheHeaderMap in field 4 of CacheResponse, so it is tagged 0x22 and holds its name
# (field 1, tag 0x0a) then its value (field 2, tag 0x12); a request header sits in
# field 2 of CacheRequest, tagged 0x12, so the request's Accept header cannot match.
_RESPONSE_CTYPE_RE = re.compile(rb"\x22[\x00-\x7f]\x0a\x0c(?i:content-type)\x12([\x00-\x7f])")
# CloudFront key-pair ids are upper-case alphanumeric; trim trailing cache bytes.
_KEYPAIR_TRIM_RE = re.compile(r"(Key-Pair-Id=[A-Z0-9]+).*$")


def _response_content_type(raw):
    """The Content-Type header stored with the cached response, or ''."""
    match = _RESPONSE_CTYPE_RE.search(raw)
    if not match:
        return ""
    return raw[match.end():match.end() + match.group(1)[0]].decode("latin1", "replace")


def _unix_to_dt(value):
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError, OverflowError):
        return ""


@artifact_processor
def wireServiceWorkerCache(context):
    data_list = []
    source_paths = []
    parsed = set()

    for file_found in context.get_files_found():
        file_found = str(file_found)
        if not file_found.endswith("_0"):
            continue
        real = os.path.realpath(file_found)
        if real in parsed:
            continue
        parsed.add(real)

        try:
            with open(file_found, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if b"wire.com" not in raw:
            continue

        text = raw.decode("latin1", "replace")
        req = _ASSET_URL_RE.search(text)
        req_url = req.group(0) if req else ""
        # The fallback below matches any wire.com URL, so it can pick up a
        # response that is not an asset at all. Only a resolved /assets/ URL
        # justifies saying anything about the body.
        is_asset = bool(req_url)
        if not req_url:
            any_url = _ANY_WIRE_URL_RE.search(text)
            req_url = any_url.group(0) if any_url else ""
        if not req_url:
            continue

        cdn = _CDN_URL_RE.search(text)
        cdn_url = cdn.group(0) if cdn else ""
        if cdn_url:
            cdn_url = _KEYPAIR_TRIM_RE.sub(r"\1", cdn_url)
        aid = _ASSET_ID_RE.search(req_url)
        expires = ""
        if cdn_url:
            em = _EXPIRES_RE.search(cdn_url)
            if em:
                expires = _unix_to_dt(em.group(1))
        ctype = _response_content_type(raw)

        source_paths.append(file_found)
        data_list.append((
            os.path.basename(file_found),
            req_url,
            aid.group(1) if aid else "",
            cdn_url,
            expires,
            ctype,
            len(raw),
            "Asset bodies in this cache are Wire-encrypted; not decoded here"
            if is_asset else "",
        ))

    data_headers = (
        "Cache Entry", "Request URL", "Asset ID", "CDN Download URL",
        ("CDN Expires", "datetime"), "Response Content Type",
        "Entry Size (bytes)", "Note",
    )
    return data_headers, data_list, '\n'.join(source_paths)
