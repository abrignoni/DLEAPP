"""qBittorrent torrents (BT_backup resume data) and session log, for DLEAPP.

Author: @AlexisBrignoni, Claude.

qBittorrent keeps one <info-hash>.fastresume (libtorrent resume data plus qBittorrent's own qBt-* keys) and one
<info-hash>.torrent per torrent in BT_backup, the queue order in BT_backup/queue, and a text session log in logs/.
Field meanings are from libtorrent and qBittorrent source cited in the notes.
"""

import os
import re
from datetime import datetime, timezone

import bencoding
from bencoding.decoder import DecoderError

from scripts.ilapfuncs import artifact_processor, logfunc

_LT = 'https://github.com/arvidn/libtorrent/blob/6da363d2994f17c0b3c0450d124cf73a31a73847/'
_QBT = 'https://github.com/qbittorrent/qBittorrent/blob/9213075dd5f7b352208361c6a84c1c115efc898e/'
_LOG_LINE = re.compile(r'^\(([NIWC])\) (\S+) - (.*)$')
_LOG_TORRENT = re.compile(r'Torrent: "(.*?)"')
_LEVELS = {'N': 'Normal', 'I': 'Info', 'W': 'Warning', 'C': 'Critical'}

__artifacts_v2__ = {
    "qbittorrentTorrents": {
        "name": "qBittorrent Torrents",
        "description": "Torrents qBittorrent had in its session, from the resume data in BT_backup: when each was "
                       "added and when its data was finished, its name, info-hash, save path, category, tags, trackers and files, and "
                       "the bytes it downloaded and uploaded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-07",
        "last_update_date": "2026-11-07",
        "requirements": "bencoding",
        "category": "qBittorrent",
        "notes": "One row per <info-hash>.fastresume file in qBittorrent's BT_backup folder (on Windows under AppData\\\\Local\\\\qBittorrent, and under qBittorrent\\\\data in a profile made with --profile), decoded with the bencoding library. qBittorrent stores this resume data when its resume data storage is the default fastresume files (https://github.com/qbittorrent/qBittorrent/blob/9213075dd5f7b352208361c6a84c1c115efc898e/src/base/bittorrent/sessionimpl.cpp#L627); a session set to its SQLite storage keeps torrents.db instead, which this artifact does not read. The file is libtorrent resume data (https://github.com/arvidn/libtorrent/blob/6da363d2994f17c0b3c0450d124cf73a31a73847/src/write_resume_data.cpp#L75-L125) with qBittorrent's own qBt- keys added (https://github.com/qbittorrent/qBittorrent/blob/9213075dd5f7b352208361c6a84c1c115efc898e/src/base/bittorrent/bencoderesumedatastorage.cpp#L455-L475). Added (UTC) and Completed (UTC) are added_time and completed_time, which libtorrent documents as POSIX times, the added time counting earlier sessions (https://github.com/arvidn/libtorrent/blob/6da363d2994f17c0b3c0450d124cf73a31a73847/include/libtorrent/add_torrent_params.hpp#L261-L266); Last Download (UTC) and Last Upload (UTC) are last_download and last_upload, the last time payload was received or sent (#L359-L364). Downloaded and Uploaded are total_downloaded and total_uploaded, Active Time and Seeding Time are active_time and seeding_time in seconds (#L250-L259). Stopped is the paused flag. Name is qBt-name when set, else libtorrent's name; Info Hash is the v1 info-hash, else the file name; Save Path is save_path as stored; Category, Tags and Comment are qBt-category, qBt-tags and qBt-comment (the torrent's own comment when qBt-comment is empty). Trackers are the tracker URLs, one per line. Files and Total Size come from the torrent's info dictionary, in the resume data or else in the <info-hash>.torrent beside it. Queue Position is the torrent's line number in BT_backup\\\\queue, the order qBittorrent reads back (https://github.com/qbittorrent/qBittorrent/blob/9213075dd5f7b352208361c6a84c1c115efc898e/src/base/bittorrent/bencoderesumedatastorage.cpp#L184-L225), blank when the hash is not listed. The certificate and private key qBittorrent can keep in the resume data (qBt-sslCertificate, qBt-sslPrivateKey) are not shown. Measured on the known data (corpus key windows11_arm_qbittorrent_known_20261107, qBittorrent 5.3.0 on Windows 11, two instances on loopback driven through the Web API): Added, Completed, Downloaded, Uploaded, Save Path, Category and Tags matched what qBittorrent's own Web API reported for the three torrents; a torrent added with its data already on disk had a Completed time equal to its Added time and downloaded nothing; one downloaded from the second instance had 400,000 bytes downloaded; one added stopped had Stopped Yes and was the only one in the queue file. Trackers held the one test tracker on all three rows. Not tested on other qBittorrent versions or on Linux or macOS, where the same file names are matched under their qBittorrent folders. A row records a torrent qBittorrent kept, not who added it or that its content was opened.",
        "paths": ('*/qBittorrent/BT_backup/*', '*/qBittorrent/data/BT_backup/*'),
        "output_types": ["standard"],
        "artifact_icon": "download-cloud",
        "sample_data": {
            "windows11_arm_qbittorrent_known_20261107": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no qBittorrent)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no qBittorrent)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no qBittorrent)",
        },
    },
    "qbittorrentLog": {
        "name": "qBittorrent Log",
        "description": "Lines of qBittorrent's session log: when the program started and stopped, torrents added "
                       "and finished, peers added, and the network settings it reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-07",
        "last_update_date": "2026-11-07",
        "requirements": "none",
        "category": "qBittorrent",
        "notes": "One row per line of qBittorrent's log file, qbittorrent.log and its rotated copies qbittorrent.log.bak and qbittorrent.log.bakN, in the logs folder beside BT_backup. qBittorrent writes each line as a level marker, (N), (I), (W) or (C) for Normal, Info, Warning and Critical, then the time, then the message (https://github.com/qbittorrent/qBittorrent/blob/9213075dd5f7b352208361c6a84c1c115efc898e/src/app/filelogger.cpp#L128-L147). Time (local, as logged) is that time as stored, written by QDateTime in ISO form in the computer's local time with no time zone recorded: on the known data (corpus key windows11_arm_qbittorrent_known_20261107, a computer set to UTC-5) each logged time was five hours behind the UTC time the test script recorded for the same step. Torrent is the name in a message's Torrent: \"...\" part, as in the Added new torrent and Torrent download finished messages. On the known data qBittorrent logged Torrent download finished for a torrent whose data was already on disk, after checking it, so that message does not by itself show a download. Log File held one name on all 34 rows of the known data and User one profile. A row records what qBittorrent logged, not who was using it.",
        "paths": ('*/qBittorrent/logs/qbittorrent.log*', '*/qBittorrent/data/logs/qbittorrent.log*'),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "windows11_arm_qbittorrent_known_20261107": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 34 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no qBittorrent)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no qBittorrent)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no qBittorrent)",
        },
    },
}


def _text(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return '' if value is None else str(value)


def _posix(value):
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _profile_user(relative):
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings', 'home'):
            return parts[index + 1]
    return ''


def _decode(path):
    with open(path, 'rb') as handle:
        value = bencoding.bdecode(handle.read())
    if not isinstance(value, dict):
        raise ValueError('not a bencoded dictionary')
    return value


def _files(info):
    """(file paths, total size) from a torrent info dictionary."""
    if not isinstance(info, dict):
        return [], ''
    name = _text(info.get(b'name'))
    if b'files' in info and isinstance(info[b'files'], list):
        paths, total = [], 0
        for entry in info[b'files']:
            if not isinstance(entry, dict):
                continue
            parts = [_text(part) for part in entry.get(b'path', []) if isinstance(part, bytes)]
            paths.append('/'.join([name] + parts))
            total += entry.get(b'length', 0) if isinstance(entry.get(b'length'), int) else 0
        return paths, total
    length = info.get(b'length')
    return [name], length if isinstance(length, int) else ''


def _trackers(resume):
    urls = []
    for tier in resume.get(b'trackers', []) or []:
        for url in tier if isinstance(tier, list) else [tier]:
            if isinstance(url, bytes) and _text(url) not in urls:
                urls.append(_text(url))
    return urls


@artifact_processor
def qbittorrentTorrents(context):
    data_headers = (('Added (UTC)', 'datetime'), ('Completed (UTC)', 'datetime'), ('Last Download (UTC)', 'datetime'),
                    ('Last Upload (UTC)', 'datetime'), 'Name', ('Info Hash', 'hash'), 'Save Path', 'Category', 'Tags',
                    ('Downloaded (bytes)', 'number'), ('Uploaded (bytes)', 'number'),
                    ('Active Time (seconds)', 'number'), ('Seeding Time (seconds)', 'number'), 'Stopped',
                    ('Queue Position', 'number'), 'Trackers', 'Files', ('Total Size (bytes)', 'number'), 'Comment',
                    'User')
    data_list, sources = [], []
    found = sorted(str(f) for f in context.get_files_found() if os.path.isfile(str(f)))
    queues = {}
    for path in found:
        if os.path.basename(path) == 'queue':
            try:
                with open(path, 'rb') as handle:
                    order = [line.strip().decode('latin-1').lower() for line in handle if line.strip()]
            except OSError:
                continue
            queues[os.path.dirname(path)] = {value: index + 1 for index, value in enumerate(order)}
    for path in found:
        if not path.endswith('.fastresume'):
            continue
        relative = context.get_relative_path(path)
        try:
            resume = _decode(path)
        except (OSError, ValueError, TypeError, IndexError, KeyError, DecoderError) as exc:
            logfunc(f'qBittorrent Torrents: {relative} did not decode ({type(exc).__name__})')
            continue
        stem = os.path.splitext(os.path.basename(path))[0].lower()
        info_hash = resume.get(b'info-hash')
        info_hash = info_hash.hex() if isinstance(info_hash, bytes) and len(info_hash) == 20 and any(info_hash) else stem
        info = resume.get(b'info')
        if not isinstance(info, dict):
            torrent = os.path.join(os.path.dirname(path), stem + '.torrent')
            try:
                info = _decode(torrent).get(b'info') if os.path.isfile(torrent) else None
            except (OSError, ValueError, TypeError, IndexError, KeyError, DecoderError):
                info = None
        files, total = _files(info)
        name = _text(resume.get(b'qBt-name')) or _text(resume.get(b'name')) or (_text(info.get(b'name')) if isinstance(info, dict) else '')
        tags = resume.get(b'qBt-tags') or []
        comment = _text(resume.get(b'qBt-comment')) or _text(resume.get(b'comment'))
        data_list.append((
            _posix(resume.get(b'added_time')), _posix(resume.get(b'completed_time')),
            _posix(resume.get(b'last_download')), _posix(resume.get(b'last_upload')),
            name, info_hash, _text(resume.get(b'save_path')), _text(resume.get(b'qBt-category')),
            ', '.join(_text(tag) for tag in tags if isinstance(tag, bytes)),
            resume.get(b'total_downloaded', ''), resume.get(b'total_uploaded', ''),
            resume.get(b'active_time', ''), resume.get(b'seeding_time', ''),
            'Yes' if resume.get(b'paused') == 1 else 'No' if resume.get(b'paused') == 0 else '',
            queues.get(os.path.dirname(path), {}).get(stem, ''),
            '\n'.join(_trackers(resume)), '\n'.join(files), total, comment, _profile_user(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def qbittorrentLog(context):
    data_headers = ('Time (local, as logged)', 'Level', 'Message', 'Torrent', 'Log File', 'User')
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found()):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                text = handle.read().decode('utf-8', 'replace')
        except OSError as exc:
            logfunc(f'qBittorrent Log: could not read {relative} ({type(exc).__name__})')
            continue
        rows = 0
        for line in text.splitlines():
            matched = _LOG_LINE.match(line)
            if not matched:
                continue
            level, when, message = matched.groups()
            torrent = _LOG_TORRENT.search(message)
            data_list.append((when.replace('T', ' '), _LEVELS[level], message, torrent.group(1) if torrent else '',
                              os.path.basename(relative.replace('\\', '/')), _profile_user(relative)))
            rows += 1
        if rows:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
