"""uTorrent and BitTorrent classic: torrents, settings and RSS feeds, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Both programs keep bencoded stores in their data folder: resume.dat (one entry per torrent, keyed by the .torrent file
beside it), settings.dat and rss.dat. No vendor definition of these stores was used. The notes of each artifact say which
fields were compared with the client's own Web API and a timed step log on the known data, and which are reported as stored.
"""

import hashlib
import ntpath
import os
from datetime import datetime, timedelta, timezone

import bencoding
from bencoding.decoder import DecoderError

from scripts.ilapfuncs import artifact_processor, logfunc

_DECODE_ERRORS = (OSError, ValueError, TypeError, IndexError, KeyError, RecursionError, DecoderError)
_WINDOWS_EPOCH_SECONDS = 11644473600

__artifacts_v2__ = {
    "utorrentTorrents": {
        "name": "uTorrent and BitTorrent Torrents",
        "description": "Torrents in uTorrent or BitTorrent classic, from resume.dat: when each was added and "
                       "finished, its name, info-hash, save path, label, trackers and files, the address the "
                       ".torrent was added from when one is recorded, and the bytes downloaded and uploaded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "bencoding",
        "category": "uTorrent and BitTorrent",
        "platforms": ("Windows",),
        "notes": "One row per .torrent entry in a resume.dat directly inside a folder named uTorrent or BitTorrent. No vendor "
                 "definition of these fields was used. On the known data (windows11_arm_utorrent_bittorrent_known_20261122, uTorrent 3.6.0.47390 and BitTorrent 7.11.0.47391, clients on "
                 "loopback, VM time zone UTC-5) Name, Info Hash, Label, Downloaded and Uploaded equalled the client's "
                 "own Web API on all 8 rows. Added fell within 1 second of the timed step log on all 8 rows. Completed "
                 "fell within 3 seconds of the time the rig's 2-second poll logged completion on the 6 rows that "
                 "completed, and is blank on the 2 rows of the torrent that never completed. Save Path is the path "
                 "field as stored; on the known data it held the download folder joined with the torrent name on all "
                 "8 rows. Started (as stored) is the started field: it held 0 on the torrent stopped through the Web "
                 "API and 2 on the running ones; other values were not seen. Runtime and Seed Time are the runtime and "
                 "seedtime fields as stored; their unit was not established. Download URL is download_url, the address "
                 "the .torrent was added from on the known data. Files and Total Size come from the .torrent named by "
                 "the resume entry, in the same folder with the name matched ignoring case, and only when that file's "
                 "original info bytes hash to the entry's info-hash. Total Size is blank when a file entry has no "
                 "valid length. On the known data the program was closed cleanly and resume.dat held the state at "
                 "that close. A forced stop was not tested, so how current resume.dat is after one is not established. "
                 "A copy run from another folder name is not matched. Trackers held the one loopback tracker on all 8 "
                 "rows. User is the profile folder name taken from the file's path, not a value in the store. The "
                 "known data has one placeholder profile, on all 8 rows.",
        "paths": ('*/[Uu][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Rr][Ee][Ss][Uu][Mm][Ee].[Dd][Aa][Tt]', '*/[Uu][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/*.[Tt][Oo][Rr][Rr][Ee][Nn][Tt]',
                  '*/[Bb][Ii][Tt][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Rr][Ee][Ss][Uu][Mm][Ee].[Dd][Aa][Tt]', '*/[Bb][Ii][Tt][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/*.[Tt][Oo][Rr][Rr][Ee][Nn][Tt]'),
        "output_types": ["standard"],
        "artifact_icon": "download-cloud",
        "sample_data": {
            "windows11_arm_utorrent_bittorrent_known_20261122": "Windows 11 build 26200 (ARM64), uTorrent 3.6.0.47390 and BitTorrent 7.11.0.47391 | 8 rows",
        },
    },
    "utorrentSettings": {
        "name": "uTorrent and BitTorrent Settings",
        "description": "Selected values from settings.dat of uTorrent or BitTorrent classic: when the settings were "
                       "created and last saved, the stored run counter, download folders, listening port, Web UI "
                       "user name and, when the file holds them, proxy settings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "bencoding",
        "category": "uTorrent and BitTorrent",
        "platforms": ("Windows",),
        "notes": "One row per selected key that holds a value in settings.dat in a folder named uTorrent or "
                 "BitTorrent; Stored Key is the key's name. 15 of the 20 selected keys occurred on the known data. "
                 "dir_torrent_files, dir_autoload, proxy.type, proxy.proxy and proxy.port did not occur, so those five "
                 "rows are unexercised and their key names are not confirmed on these versions. born_on is read as "
                 "seconds since 1601 and settings_saved_systime as Unix seconds; on the known data (windows11_arm_utorrent_bittorrent_known_20261122, VM "
                 "time zone UTC-5) each fell within 5 seconds of the program's logged start and close. The other "
                 "values are shown as stored, with text decoded as UTF-8. Their meaning is taken from the key name and "
                 "was not otherwise established. Time (UTC) is filled only on the two time keys of each client, 4 of "
                 "30 rows on the known data, and those rows leave Value blank. User is the profile folder name taken "
                 "from the file's path. The known data has one placeholder profile, on all 30 rows. Keys outside the "
                 "selected list are not reported. That includes webui.hashword, webui.salt, cid and cids. "
                 "settings.dat.old is not read.",
        "paths": ('*/[Uu][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Ss][Ee][Tt][Tt][Ii][Nn][Gg][Ss].[Dd][Aa][Tt]', '*/[Bb][Ii][Tt][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Ss][Ee][Tt][Tt][Ii][Nn][Gg][Ss].[Dd][Aa][Tt]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "windows11_arm_utorrent_bittorrent_known_20261122": "Windows 11 build 26200 (ARM64), uTorrent 3.6.0.47390 and BitTorrent 7.11.0.47391 | 30 rows",
        },
    },
    "utorrentRss": {
        "name": "uTorrent and BitTorrent RSS",
        "description": "RSS feeds and download filters set in uTorrent or BitTorrent classic, from rss.dat.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "bencoding",
        "category": "uTorrent and BitTorrent",
        "platforms": ("Windows",),
        "notes": "One row per entry in the feeds and filters lists of rss.dat. A feed's url field holds an alias and "
                 "the address joined by a vertical bar, which the Web API returned in the same form on the known "
                 "data (windows11_arm_utorrent_bittorrent_known_20261122). There each client held one feed and one filter. On the 2 feed rows Name and URL "
                 "or Pattern are the two parts of that field and Feed ID is the feed's ident, and they matched the Web "
                 "API. On the 2 filter rows Name, URL or Pattern, Label and Feed ID (the filter's feed field) matched "
                 "the Web API. Feed rows have no label. Exclude Pattern (not_filter) and Save Folder (directory) had "
                 "no value on any row, so those two columns are unexercised. Enabled shows a stored 1 as Yes and 0 "
                 "as No, leaves a missing field blank and shows any other value as stored. Only 1 occurred, on all 4 "
                 "rows. User is the "
                 "profile folder name taken from the file's path. The known data has one placeholder profile, on all "
                 "4 rows. The history list was empty on the known data and is not read. What it holds was not "
                 "established. rss.dat.old is not read.",
        "paths": ('*/[Uu][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Rr][Ss][Ss].[Dd][Aa][Tt]', '*/[Bb][Ii][Tt][Tt][Oo][Rr][Rr][Ee][Nn][Tt]/[Rr][Ss][Ss].[Dd][Aa][Tt]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "rss",
        "sample_data": {
            "windows11_arm_utorrent_bittorrent_known_20261122": "Windows 11 build 26200 (ARM64), uTorrent 3.6.0.47390 and BitTorrent 7.11.0.47391 | 4 rows",
        },
    },
}

_SETTINGS = (
    ('born_on', 'Settings Created'),
    ('settings_saved_systime', 'Settings Last Saved'),
    ('runs_since_born', 'Program Runs'),
    ('runtime_since_born', 'Runtime Since Created (as stored)'),
    ('install_revision', 'Install Revision'),
    ('dir_active_download', 'Active Download Folder'),
    ('dir_completed_download', 'Completed Download Folder'),
    ('dir_torrent_files', 'Stored .torrent Folder'),
    ('dir_autoload', 'Auto-Load Folder'),
    ('bind_port', 'Listening Port'),
    ('net.bind_ip', 'Bind Address'),
    ('net.outgoing_ip', 'Outgoing Address'),
    ('webui.enable', 'Web UI Enabled'),
    ('webui.port', 'Web UI Port'),
    ('webui.username', 'Web UI User Name'),
    ('proxy.type', 'Proxy Type'),
    ('proxy.proxy', 'Proxy Address'),
    ('proxy.port', 'Proxy Port'),
    ('dht', 'DHT Enabled'),
    ('pex', 'Peer Exchange Enabled'),
)


def _text(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return '' if value is None else str(value)


def _unix(value):
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _windows_seconds(value):
    if not isinstance(value, int) or value <= _WINDOWS_EPOCH_SECONDS:
        return ''
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=value - _WINDOWS_EPOCH_SECONDS)
    except OverflowError:
        return ''


def _decode(path):
    with open(path, 'rb') as handle:
        value = bencoding.bdecode(handle.read())
    if not isinstance(value, dict):
        raise ValueError('not a bencoded dictionary')
    return value


def _client_user(relative):
    """The client from the store's own parent folder, and the first profile folder in the path."""
    parts = relative.replace('\\', '/').split('/')
    parent = parts[-2].lower() if len(parts) > 1 else ''
    client = {'utorrent': 'uTorrent', 'bittorrent': 'BitTorrent'}.get(parent, '')
    user = ''
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings') and index + 1 < len(parts) - 1:
            user = parts[index + 1]
            break
    return client, user


def _valid_length(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _files(info):
    if not isinstance(info, dict):
        return [], ''
    name = _text(info.get(b'name'))
    if b'files' in info:
        if not isinstance(info[b'files'], list) or not info[b'files']:
            return [], ''
        paths, total, sizes_valid = [], 0, True
        for entry in info[b'files']:
            if not isinstance(entry, dict):
                sizes_valid = False
                continue
            stored = entry.get(b'path')
            if isinstance(stored, list) and stored and all(isinstance(part, bytes) for part in stored):
                paths.append('/'.join([name] + [_text(part) for part in stored]))
            if _valid_length(entry.get(b'length')):
                total += entry[b'length']
            else:
                sizes_valid = False
        return paths, total if sizes_valid else ''
    length = info.get(b'length')
    return [name], length if _valid_length(length) else ''


def _skip_value(raw, index):
    """The offset just past the bencoded value that starts at index."""
    marker = raw[index:index + 1]
    if marker == b'i':
        return raw.index(b'e', index) + 1
    if marker in (b'l', b'd'):
        index += 1
        while raw[index:index + 1] != b'e':
            if index >= len(raw):
                raise ValueError('unterminated container')
            index = _skip_value(raw, index)
        return index + 1
    colon = raw.index(b':', index)
    length = raw[index:colon]
    if not length.isdigit():
        raise ValueError('invalid string length')
    end = colon + 1 + int(length)
    if end > len(raw):
        raise ValueError('string past the end of the file')
    return end


def _info_span(raw):
    """The original bytes of the top-level info value, which are what the info-hash covers."""
    if raw[:1] != b'd':
        return b''
    index = 1
    while raw[index:index + 1] != b'e' and index < len(raw):
        key_end = _skip_value(raw, index)
        value_end = _skip_value(raw, key_end)
        if raw[raw.index(b':', index) + 1:key_end] == b'info':
            return raw[key_end:value_end]
        index = value_end
    return b''


def _companion(staged, entry_name):
    """The staged .torrent files whose name matches the entry's, ignoring case, exact spelling first."""
    wanted = ntpath.basename(entry_name)
    exact = [path for path in staged if os.path.basename(path) == wanted]
    others = [path for path in staged
              if os.path.basename(path) != wanted and os.path.basename(path).lower() == wanted.lower()]
    return exact + others


def _torrent_info(staged, entry_name, info_hash):
    """(info dictionary, path) of the entry's .torrent, only when its info bytes hash to the recorded info-hash."""
    if not info_hash:
        return None, ''
    for path in _companion(staged, entry_name):
        try:
            with open(path, 'rb') as handle:
                raw = handle.read()
            span = _info_span(raw)
            if span and hashlib.sha1(span).digest() == info_hash:  # nosec B324
                info = bencoding.bdecode(span)
                if isinstance(info, dict):
                    return info, path
        except _DECODE_ERRORS:
            continue
    return None, ''


def _trackers(entry):
    urls = []
    stored = entry.get(b'trackers')
    if not isinstance(stored, list):
        return urls
    for item in stored:
        for url in item if isinstance(item, list) else [item]:
            if isinstance(url, bytes) and url and _text(url) not in urls:
                urls.append(_text(url))
    return urls


def _list(value):
    return value if isinstance(value, list) else []


def _enabled(value):
    """1 and 0 as Yes and No; a missing field stays blank and any other value is shown as stored."""
    if value == 1:
        return 'Yes'
    if value == 0:
        return 'No'
    return _text(value)


def _found(context, name):
    return sorted(str(f) for f in context.get_files_found()
                  if os.path.basename(str(f)).lower() == name
                  and os.path.basename(os.path.dirname(str(f))).lower() in ('utorrent', 'bittorrent')
                  and os.path.isfile(str(f)))


@artifact_processor
def utorrentTorrents(context):
    data_headers = (('Added (UTC)', 'datetime'), ('Completed (UTC)', 'datetime'), 'Client', 'Name', ('Info Hash', 'hash'),
                    'Save Path', 'Label', 'Started (as stored)', ('Downloaded (bytes)', 'number'),
                    ('Uploaded (bytes)', 'number'), ('Runtime (as stored)', 'number'), ('Seed Time (as stored)', 'number'),
                    'Trackers', 'Download URL', 'Files', ('Total Size (bytes)', 'number'), 'User')
    data_list, sources = [], []
    for path in _found(context, 'resume.dat'):
        relative = context.get_relative_path(path)
        sources.append(path)
        try:
            resume = _decode(path)
        except _DECODE_ERRORS as exc:
            logfunc(f'uTorrent and BitTorrent Torrents: {relative} did not decode ({type(exc).__name__})')
            continue
        client, user = _client_user(relative)
        folder = os.path.dirname(path)
        staged = sorted({str(f) for f in context.get_files_found()
                         if os.path.dirname(str(f)) == folder and str(f).lower().endswith('.torrent')
                         and os.path.isfile(str(f))})
        for key, entry in resume.items():
            if not isinstance(key, bytes) or not key.lower().endswith(b'.torrent') or not isinstance(entry, dict):
                continue
            raw_hash = entry.get(b'info')
            info_hash = raw_hash if isinstance(raw_hash, bytes) and len(raw_hash) == 20 else b''
            info, torrent_path = _torrent_info(staged, _text(key), info_hash)
            files, total = _files(info)
            if torrent_path:
                sources.append(torrent_path)
            data_list.append((
                _unix(entry.get(b'added_on')), _unix(entry.get(b'completed_on')), client,
                _text(entry.get(b'caption')) or _text(key)[:-len('.torrent')], info_hash.hex(), _text(entry.get(b'path')),
                _text(entry.get(b'label')), entry.get(b'started', ''), entry.get(b'downloaded', ''),
                entry.get(b'uploaded', ''), entry.get(b'runtime', ''), entry.get(b'seedtime', ''),
                '\n'.join(_trackers(entry)), _text(entry.get(b'download_url')), '\n'.join(files), total, user))
    return data_headers, data_list, '\n'.join(dict.fromkeys(sources))


@artifact_processor
def utorrentSettings(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Client', 'Setting', 'Value', 'Stored Key', 'User')
    data_list, sources = [], []
    for path in _found(context, 'settings.dat'):
        relative = context.get_relative_path(path)
        sources.append(path)
        try:
            settings = _decode(path)
        except _DECODE_ERRORS as exc:
            logfunc(f'uTorrent and BitTorrent Settings: {relative} did not decode ({type(exc).__name__})')
            continue
        client, user = _client_user(relative)
        for key, label in _SETTINGS:
            value = settings.get(key.encode())
            if value is None or value == b'':
                continue
            when = ''
            if key == 'born_on':
                when = _windows_seconds(value)
            elif key == 'settings_saved_systime':
                when = _unix(value)
            data_list.append((when, client, label, '' if when else _text(value), key, user))
    return data_headers, data_list, '\n'.join(dict.fromkeys(sources))


@artifact_processor
def utorrentRss(context):
    data_headers = ('Type', 'Client', 'Name', 'URL or Pattern', 'Exclude Pattern', 'Save Folder', 'Label',
                    ('Feed ID', 'number'), 'Enabled', 'User')
    data_list, sources = [], []
    for path in _found(context, 'rss.dat'):
        relative = context.get_relative_path(path)
        sources.append(path)
        try:
            rss = _decode(path)
        except _DECODE_ERRORS as exc:
            logfunc(f'uTorrent and BitTorrent RSS: {relative} did not decode ({type(exc).__name__})')
            continue
        client, user = _client_user(relative)
        for feed in _list(rss.get(b'feeds')):
            if not isinstance(feed, dict):
                continue
            alias, separator, url = _text(feed.get(b'url')).partition('|')
            if not separator:
                alias, url = '', alias
            data_list.append(('Feed', client, alias, url, '', '', '', feed.get(b'ident', ''),
                              _enabled(feed.get(b'enabled')), user))
        for item in _list(rss.get(b'filters')):
            if not isinstance(item, dict):
                continue
            data_list.append(('Filter', client, _text(item.get(b'name')), _text(item.get(b'filter')),
                              _text(item.get(b'not_filter')), _text(item.get(b'directory')), _text(item.get(b'label')),
                              item.get(b'feed', ''), _enabled(item.get(b'enabled')), user))
    return data_headers, data_list, '\n'.join(dict.fromkeys(sources))
