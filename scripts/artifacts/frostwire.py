"""FrostWire torrents, shared-torrents index and folder settings, for DLEAPP.

Author: @AlexisBrignoni, Claude.

FrostWire keeps its settings in .frostwire5 in the user's home folder (Library/Preferences/FrostWire5 on macOS), with
libtorrent's resume data and the .torrent files in the libtorrent folder inside it.
Field meanings are from FrostWire and libtorrent source cited in the notes.
"""

import os
from datetime import datetime, timezone

import bencoding
from bencoding.decoder import DecoderError

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path


__artifacts_v2__ = {
    "frostwireTorrents": {
        "name": "FrostWire Torrents",
        "description": "Torrents FrostWire had in its BitTorrent session, from libtorrent's resume data: when each "
                       "was added and finished, its name, info-hash, save path, trackers and files, and the bytes "
                       "it downloaded and uploaded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "bencoding",
        "category": "FrostWire",
        "notes": "FrostWire keeps its settings in .frostwire5 in the user's home folder, Library/Preferences/FrostWire5 on macOS (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/org/limewire/util/CommonUtils.java#L399-L401); a portable copy that keeps its settings elsewhere is not matched. The known data (windows11_arm_frostwire_known_20261108) is FrostWire 7.1.3 run on Windows 11 ARM64 with the computer's default routes removed and DNS pointed at localhost; connection tests failed before and after the run (an IPv6 default route was re-learned for about half a minute mid-run and removed). User is the account folder name taken from the file path (the folder after home on Linux). One row per <info-hash>.resume file that decodes, in the libtorrent folder inside the settings folder, where FrostWire's BitTorrent engine keeps libtorrent's resume data and a copy of each .torrent (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/com/limegroup/gnutella/gui/Initializer.java#L1133-L1157, https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/common/src/main/java/com/frostwire/bittorrent/BTEngine.java#L716, #L772), decoded with the bencoding library. Added (UTC), Completed (UTC), Last Download (UTC) and Last Upload (UTC) are added_time, completed_time, last_download and last_upload, which libtorrent documents as POSIX times, the added time counting earlier sessions and the last two the last time payload was received or sent (https://github.com/arvidn/libtorrent/blob/1eb18faeae156d8dbbab42935c082f8b81f50989/include/libtorrent/add_torrent_params.hpp#L268-L273, #L366-L371, libtorrent 2.0.15, the version that wrote the known data); Downloaded, Uploaded, Active Time and Seeding Time are total_downloaded, total_uploaded, active_time and seeding_time (#L258-L266). Paused is libtorrent's paused flag, written as 0 or 1 (https://github.com/arvidn/libtorrent/blob/1eb18faeae156d8dbbab42935c082f8b81f50989/src/write_resume_data.cpp#L106) and shown as No or Yes; any other value is shown as stored. Info Hash is the resume data's info-hash; when that is absent or all zero the file name, which FrostWire sets to the v1 or v2 hash (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/common/src/main/java/com/frostwire/bittorrent/BTEngine.java#L776-L800), is shown. Save Path is save_path, the folder the torrent's data was to be written to; on the known data it was FrostWire's default data folder on both rows, not the folder set in the settings file under a name FrostWire does not read, so on the known data Save Path, not the settings, showed where the data went. Trackers are the tracker URLs, one per line; Files and Total Size come from the info dictionary in the resume data or the .torrent beside it (on the known data the resume data held the info dictionary; the .torrent fallback is exercised only by the unit test). On the known data (two torrents added offline from .torrent files, one whose data had been placed in another folder and one with no data) Added was 3 seconds after the second torrent was passed to the running FrostWire and, for the torrent passed on the command line at start, 31 seconds after the setup wizard closed, about four minutes after start, so on the known data Added was when FrostWire added the torrent to its session, not when it was requested; Downloaded, Uploaded, Active Time and Seeding Time were 0 and Paused No on both rows, and Completed (UTC), Last Download (UTC) and Last Upload (UTC) were empty on both rows because no data was transferred, so those three are source-verified only. Name and Files were identical on both rows because each torrent held one file. Not reported: frostwire-shared-torrents.db in the same folder, FrostWire's index of the torrents in its session for its relay network; it repeats the name, info-hash and files, it is pruned to the live session and FrostWire rewrites its times each time it re-indexes a torrent (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/common/src/main/java/com/frostwire/search/relay/SharedTorrentIndexer.java#L104-L160, #L295-L315). identity.dat in the same folder holds FrostWire's identity key pairs (Ed25519 and X25519) and is not matched or read; settings.dat (libtorrent's session settings) and the installation.props, intent.props and tables.props files in the settings folder are not read either. No file holding search terms was found in FrostWire's source at the cited commit: the search field's autocomplete list is built in memory (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/com/frostwire/gui/searchfield/SearchField.java#L241-L248) and the recent-searches store is never enabled (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/com/frostwire/gui/searchfield/JXSearchField.java#L437-L439). dbs/crawldb, FrostWire's crawl cache, is not reported. A row records a torrent FrostWire had in its session, not who added it or that its content was opened.",
        "paths": ('*/.frostwire5/libtorrent/*.resume', '*/.frostwire5/libtorrent/*.torrent',
                  '*/Library/Preferences/FrostWire5/libtorrent/*.resume',
                  '*/Library/Preferences/FrostWire5/libtorrent/*.torrent'),
        "output_types": ["standard"],
        "artifact_icon": "download-cloud",
        "sample_data": {
            "windows11_arm_frostwire_known_20261108": "Windows 11 build 26200 (ARM64), FrostWire 7.1.3 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "frostwireFolders": {
        "name": "FrostWire Folders",
        "description": "The download and torrent folders set in FrostWire's settings file, frostwire.props.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "FrostWire",
        "notes": "FrostWire keeps its settings in .frostwire5 in the user's home folder, Library/Preferences/FrostWire5 on macOS (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/org/limewire/util/CommonUtils.java#L399-L401); a portable copy that keeps its settings elsewhere is not matched. The known data (windows11_arm_frostwire_known_20261108) is FrostWire 7.1.3 run on Windows 11 ARM64 with the computer's default routes removed and DNS pointed at localhost; connection tests failed before and after the run (an IPv6 default route was re-learned for about half a minute mid-run and removed). User is the account folder name taken from the file path (the folder after home on Linux). Up to two rows per frostwire.props, one for each of two folder settings, when the value is set: Torrent Data Folder is the DEFAULT_TORRENT_DATA_DIR_SETTING entry, the name under which FrostWire stores its torrent data folder setting, by default a Torrent Data folder inside a FrostWire folder, under Documents on Windows and the home folder elsewhere (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/com/limegroup/gnutella/settings/SharingSettings.java#L57-L68, https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/desktop/src/main/java/com/limegroup/gnutella/util/FrostWireUtils.java#L79-L86); Torrents Folder is TORRENTS_DIR_SETTING, the folder FrostWire's engine uses for named .torrent files (https://github.com/frostwire/frostwire/blob/bde3a168836174efe38668a775de9441dd8fcbbe/common/src/main/java/com/frostwire/bittorrent/BTEngine.java#L767-L769). The values are shown with the escapes of the properties format removed. On the known data Torrent Data Folder was the default and Torrents Folder the folder set by the test script, and User held one value on all rows. A torrent's own save path is in FrostWire Torrents.",
        "paths": ('*/.frostwire5/frostwire.props', '*/Library/Preferences/FrostWire5/frostwire.props'),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "windows11_arm_frostwire_known_20261108": "Windows 11 build 26200 (ARM64), FrostWire 7.1.3 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
}

# Setting names FrostWire reads (SharingSettings.java): TORRENT_DATA_DIR_SETTING is stored under the
# DEFAULT_TORRENT_DATA_DIR_SETTING key.
_FOLDER_KEYS = (('DEFAULT_TORRENT_DATA_DIR_SETTING', 'Torrent Data Folder'),
                ('TORRENTS_DIR_SETTING', 'Torrents Folder'))


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
    if isinstance(info.get(b'files'), list):
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


def _profile_user(relative):
    user = user_from_path(relative)
    if user:
        return user
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part == 'home' and index + 1 < len(parts):
            return parts[index + 1]
    return ''


@artifact_processor
def frostwireTorrents(context):
    data_headers = (('Added (UTC)', 'datetime'), ('Completed (UTC)', 'datetime'), ('Last Download (UTC)', 'datetime'),
                    ('Last Upload (UTC)', 'datetime'), 'Name', ('Info Hash', 'hash'), 'Save Path',
                    ('Downloaded (bytes)', 'number'), ('Uploaded (bytes)', 'number'),
                    ('Active Time (seconds)', 'number'), ('Seeding Time (seconds)', 'number'), 'Paused',
                    'Trackers', 'Files', ('Total Size (bytes)', 'number'), 'User')
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found() if str(f).lower().endswith('.resume')):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            resume = _decode(path)
        except (OSError, ValueError, TypeError, IndexError, KeyError, DecoderError) as exc:
            logfunc(f'FrostWire Torrents: {relative} did not decode ({type(exc).__name__})')
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
        name = _text(resume.get(b'name')) or (_text(info.get(b'name')) if isinstance(info, dict) else '')
        paused = resume.get(b'paused')
        data_list.append((
            _posix(resume.get(b'added_time')), _posix(resume.get(b'completed_time')),
            _posix(resume.get(b'last_download')), _posix(resume.get(b'last_upload')),
            name, info_hash, _text(resume.get(b'save_path')),
            resume.get(b'total_downloaded', ''), resume.get(b'total_uploaded', ''),
            resume.get(b'active_time', ''), resume.get(b'seeding_time', ''),
            {0: 'No', 1: 'Yes'}.get(paused, '' if paused is None else str(paused)),
            '\n'.join(_trackers(resume)), '\n'.join(files), total, _profile_user(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


def _java_properties(text):
    """Key and value pairs from a Java .properties file, with the escapes Properties.store writes."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in '#!' or '=' not in line:
            continue
        key, value = line.split('=', 1)
        out, index = [], 0
        while index < len(value):
            char = value[index]
            if char == '\\' and index + 1 < len(value):
                nxt = value[index + 1]
                if nxt == 'u' and index + 6 <= len(value):
                    try:
                        out.append(chr(int(value[index + 2:index + 6], 16)))
                        index += 6
                        continue
                    except ValueError:
                        pass
                out.append({'t': '\t', 'n': '\n', 'r': '\r', 'f': '\f'}.get(nxt, nxt))
                index += 2
                continue
            out.append(char)
            index += 1
        values.setdefault(key.strip(), ''.join(out))
    return values


@artifact_processor
def frostwireFolders(context):
    data_headers = ('Setting', 'Value', 'User')
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found() if os.path.basename(str(f)) == 'frostwire.props'):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'r', encoding='latin-1') as handle:
                values = _java_properties(handle.read())
        except OSError as exc:
            logfunc(f'FrostWire Folders: {relative} not read ({exc})')
            continue
        user = _profile_user(relative)
        for key, label in _FOLDER_KEYS:
            if values.get(key):
                data_list.append((label, values[key], user))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
