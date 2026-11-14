"""Mattermost Desktop data held in Chromium containers, for DLEAPP.

Mattermost Desktop is an Electron front end for the Mattermost web app, which talks to
the server's REST API under /api/v4. JSON responses the app received can remain in the
Chromium HTTP cache, and the web app keeps its drafts in IndexedDB. This module walks the cache once and
hands the artifacts the posts, users and channels found in it.

The three object shapes are the server's own model structs: Post, User and Channel in
server/public/model/post.go, user.go and channel.go of mattermost/mattermost at v12.0.1
(commit 987e57120dca630dadbcd2638064ab66a02bb81e), the server version named by the
X-Version-Id header of the responses in the sample this was built from. An object is
recognised by a fixed set of the field names of its struct, to 12 levels of nesting in a
response. A non-post object that carries the same field names would be reported as a post;
a scheduled post (ScheduledPost embeds Draft and adds an id, scheduled_post.go) is kept out
by requiring edit_at and pending_post_id, which Post always writes and Draft does not.

The cache is read in both of Chromium's formats, the simple cache (one *_0 file per entry)
and the blockfile cache (an index file with data_N and f_ files).
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from scripts.chromium.blockfile_cache import iter_entries as blockfile_entries
from scripts.chromium.simple_cache import base_time_to_datetime, iter_entries

_API_RE = re.compile(r'^https?://[^/]+/api/v4/')

# Field names that make a JSON object one of the server's structs. Post: id, channel_id,
# user_id, create_at, message, edit_at and pending_post_id (Post writes the last two without
# omitempty, post.go lines 143 and 163). User: id, a non-empty username and one of email, roles, first_name
# (an object holding only an id and an empty username carries nothing and is left out).
# Channel: id, team_id, type, display_name and name.
_POST_FIELDS = ('id', 'channel_id', 'user_id', 'create_at', 'message', 'edit_at', 'pending_post_id')
_USER_FIELDS = ('id', 'username')
_USER_ANY = ('email', 'roles', 'first_name')
_CHANNEL_FIELDS = ('id', 'team_id', 'type', 'display_name', 'name')

CHANNEL_TYPES = {'O': 'open', 'P': 'private', 'D': 'direct', 'G': 'group'}  # ChannelType constants, channel.go lines 28-31

_MAX_DEPTH = 12


def ms_to_datetime(value):
    """Unix milliseconds, which is what the server's GetMillis writes, as an aware UTC
    datetime; '' when the value is not a positive integer or lies past year 9999."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value / 1000, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _server(url):
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'


def _when(value):
    if isinstance(value, datetime):
        return value
    return base_time_to_datetime(value)


def _is_post(obj):
    return all(name in obj for name in _POST_FIELDS) and isinstance(obj.get('id'), str)


def _is_user(obj):
    return (all(name in obj for name in _USER_FIELDS) and any(name in obj for name in _USER_ANY)
            and isinstance(obj.get('id'), str) and isinstance(obj.get('username'), str) and bool(obj['username']))


def _is_channel(obj):
    return (all(name in obj for name in _CHANNEL_FIELDS) and isinstance(obj.get('id'), str)
            and isinstance(obj.get('type'), str) and 'username' not in obj)


class Scan:
    """What one pass over the cache found. posts, users and channels map
    (server, id, update_at) to {'object' (from the newest response that held it), 'cached' (that
    response's time), 'responses', 'sources'}; entry_count is the number of Mattermost API
    responses read; too_deep counts objects below the nesting limit that were not looked at."""

    def __init__(self):
        self.posts = {}
        self.users = {}
        self.channels = {}
        self.entry_count = 0
        self.json_failures = 0
        self.too_deep = 0
        self.sources = set()


def _note(table, server, obj, cached, source):
    update_at = obj.get('update_at')
    key = (server, obj['id'], update_at if isinstance(update_at, int) else None)
    row = table.get(key)
    if row is None:
        table[key] = {'object': obj, 'cached': cached, 'responses': 1, 'sources': {source}}
        return
    row['responses'] += 1
    row['sources'].add(source)
    if cached and (not row['cached'] or cached >= row['cached']):
        # The object of the newest response is kept: a channel's last_post_at and total_msg_count
        # change without its update_at changing.
        row['cached'] = cached
        row['object'] = obj


def _walk(scan, server, node, cached, source, depth=0):
    if depth > _MAX_DEPTH:
        scan.too_deep += 1
        return
    if isinstance(node, dict):
        if _is_post(node):
            _note(scan.posts, server, node, cached, source)
        elif _is_user(node):
            _note(scan.users, server, node, cached, source)
        elif _is_channel(node):
            _note(scan.channels, server, node, cached, source)
        for value in node.values():
            if isinstance(value, (dict, list)):
                _walk(scan, server, value, cached, source, depth + 1)
    elif isinstance(node, list):
        for value in node:
            if isinstance(value, (dict, list)):
                _walk(scan, server, value, cached, source, depth + 1)


def _json_bodies(body):
    """The JSON values in a response body: one document, or one per line (ndjson), where a line that does not parse is skipped."""
    if not body:
        return []
    try:
        return [json.loads(body)]
    except (ValueError, UnicodeDecodeError):
        pass
    values = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            continue
    return values


_scans = {}


def scan_cache(files_found):
    """Read every Mattermost API response in the cache folders among files_found.
    Memoised on the file list, because the artifacts share one scan."""
    files = sorted(str(f) for f in files_found)
    entry_files = [f for f in files if f.endswith('_0')]
    index_files = [f for f in files if os.path.basename(f) == 'index']
    digest = hashlib.sha1('\n'.join(entry_files + index_files).encode('utf-8', 'replace')).hexdigest()
    cached_scan = _scans.get(digest)
    if cached_scan is not None:
        return cached_scan
    scan = Scan()
    entries = list(iter_entries(entry_files)) + list(
        blockfile_entries(index_files, folder_names=('Cache', 'Cache_Data')))
    for entry in entries:
        url = entry.url
        if not url or not _API_RE.match(url):
            continue
        status = str(entry.status_code or '')
        if status.isdigit() and int(status) >= 400:
            continue
        content_type = (entry.content_type if hasattr(entry, 'content_type') else
                        (entry.headers or {}).get('content-type', ''))
        if 'json' not in (content_type or ''):
            continue
        scan.entry_count += 1
        values = _json_bodies(entry.decoded_body())
        if not values:
            scan.json_failures += 1
            continue
        source = getattr(entry, 'body_source', '') or getattr(entry, 'source', '') or getattr(entry, 'path', '')
        scan.sources.add(source)
        for value in values:
            _walk(scan, _server(url), value, _when(entry.response_time), source)
    _scans[digest] = scan
    return scan
