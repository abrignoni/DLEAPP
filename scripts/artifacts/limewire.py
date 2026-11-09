"""LimeWire 5 library, downloads and settings, for DLEAPP.

Author: @AlexisBrignoni, Claude.

LimeWire 5 keeps its settings folder in %APPDATA%\\LimeWire on Windows, Library/Preferences/LimeWire on macOS and
.limewire in the home folder elsewhere. Its library, URN and download stores are Java serialization streams, read
with scripts/java_serialization.py. Field meanings are from LimeWire's GPL source (wiregit/wirecode) cited in the
notes.
"""

import os
import xml.parsers.expat
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.java_serialization import JavaObject, JavaSerializationError, loads, map_items, plain
from scripts.macos_plists import canonical_relative

__artifacts_v2__ = {
    "limewireLibraryFiles": {
        "name": "LimeWire Library Files",
        "description": "Files in LimeWire 5's library, from library5.dat, with the lists each was in (the Public "
                       "Shared list or a named list), its SHA-1, modified time and metadata from LimeWire's caches.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "LimeWire",
        "notes": "LimeWire 5 keeps its settings folder in LimeWire in the Windows application data folder (AppData/Roaming, or Application Data on Windows XP), Library/Preferences/LimeWire on macOS and .limewire in the home folder elsewhere (https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/util/LimeWireUtils.java#L380-L418); only the Windows folder was exercised, and a folder set with the LIMEWIRE_PREFS_DIR property or a portable copy is not matched. The .dat and .cache stores are Java serialization streams, read with scripts/java_serialization.py (a reader written from the stream specification and checked against a fixture written by the JDK). Field meanings are from LimeWire's GPL source, wiregit/wirecode at commit 2b22c506566ca43c750f2804cb4637921dd6d539. No vendor still distributes LimeWire, so the known data (windows11_arm_limewire_known_20261108) is LimeWire built from that source (compiled with the JDK 6 compiler and class library; the only change was to the build file) and run on Windows 11 ARM64 under a 32-bit Java 8u252 with the VM offline (default routes removed, static address with no gateway, DNS to loopback). User is the folder name after Users, Documents and Settings or home in the path, and Settings Folder the LimeWire folder the row came from. "
                 "One row per file path in the FILE_DATA map of library5.dat (or library5.bak when library5.dat "
                 "does not read), the map from each library file's path to the IDs of the lists it is in "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/library/LibraryFileData.java#L65-L71 "
                 "and #L109-L127). Lists names each ID: 0 is the default shared collection, which LimeWire creates "
                 "for the P2P network (Friend.P2P_FRIEND_ID) and shows as Public Shared "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/library/FileCollectionManagerImpl.java#L45), "
                 "and other IDs take their name from COLLECTION_NAMES; a file in no list has an empty Lists cell, "
                 "and List IDs is the list as stored. On the known data the file dragged to Public Shared had ID 0 "
                 "and the file dragged to a new list, named Untitled by LimeWire, had ID 1. Modified Time and "
                 "SHA-1 come from fileurns.cache, LimeWire's URN cache, whose key for each file holds the file's "
                 "path and File.lastModified() (milliseconds since 1970 UTC) when it was hashed "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/library/UrnCache.java#L447-L449 "
                 "and #L501-L505), matched to the library row by the exact path; on the known data Modified Time "
                 "equalled the test files' NTFS last-write time to the millisecond. Passed Dangerous-File Check "
                 "is Yes when the file's SHA-1 is in SAFE_URNS in library5.dat, the set LimeWire adds a file to "
                 "when its dangerous-file check finds nothing "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/library/LibraryImpl.java#L752-L757); "
                 "it held Yes on both rows of the known data. Metadata is the XML LimeWire keeps for the file in "
                 "the xml/data/*.sxml3 caches, keyed by file and SHA-1 "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/xml/LimeXMLReplyCollection.java), "
                 "shown as its attributes as stored; on the known data the MP3 carried the title and artist "
                 "from its ID3 tag and both files the length in seconds and the bit rate. Of the three test files "
                 "in the folder added with LimeWire's default file types (audio, video, images), the two audio "
                 "files were added and the text file was not. Not read: createtimes.cache (per SHA-1 the time "
                 "LimeWire gives a shared file, File.lastModified() when it was first shared, "
                 "https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/library/CreationTimeCache.java#L513-L532, "
                 "equal to Modified Time on the known data), ttroot.cache (Tiger Tree roots), library.dat (the "
                 "LimeWire 4 library settings, all six sets empty on the known data), and LimeWire 4.x stores. "
                 "A row records a file LimeWire had in its library, not that it was uploaded to anyone.",
        "paths": (
            '*/AppData/Roaming/LimeWire/library5.dat',
            '*/AppData/Roaming/LimeWire/library5.bak',
            '*/AppData/Roaming/LimeWire/fileurns.cache',
            '*/AppData/Roaming/LimeWire/xml/data/*.sxml3',
            '*/Application Data/LimeWire/library5.dat',
            '*/Application Data/LimeWire/library5.bak',
            '*/Application Data/LimeWire/fileurns.cache',
            '*/Application Data/LimeWire/xml/data/*.sxml3',
            '*/Library/Preferences/LimeWire/library5.dat',
            '*/Library/Preferences/LimeWire/library5.bak',
            '*/Library/Preferences/LimeWire/fileurns.cache',
            '*/Library/Preferences/LimeWire/xml/data/*.sxml3',
            '*/.limewire/library5.dat',
            '*/.limewire/library5.bak',
            '*/.limewire/fileurns.cache',
            '*/.limewire/xml/data/*.sxml3',
        ),
        "output_types": "standard",
        "artifact_icon": "music",
        "sample_data": {
            "windows11_arm_limewire_known_20261108": "Windows 11 build 26200 (ARM64), LimeWire built from wirecode 2b22c50 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
    "limewireDownloads": {
        "name": "LimeWire Downloads",
        "description": "Unfinished downloads LimeWire 5 saved in downloads.dat: name, type, SHA-1, incomplete and "
                       "save files, and when LimeWire added each to its download list.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "LimeWire",
        "notes": "LimeWire 5 keeps its settings folder in LimeWire in the Windows application data folder (AppData/Roaming, or Application Data on Windows XP), Library/Preferences/LimeWire on macOS and .limewire in the home folder elsewhere (https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/util/LimeWireUtils.java#L380-L418); only the Windows folder was exercised, and a folder set with the LIMEWIRE_PREFS_DIR property or a portable copy is not matched. The .dat and .cache stores are Java serialization streams, read with scripts/java_serialization.py (a reader written from the stream specification and checked against a fixture written by the JDK). Field meanings are from LimeWire's GPL source, wiregit/wirecode at commit 2b22c506566ca43c750f2804cb4637921dd6d539. No vendor still distributes LimeWire, so the known data (windows11_arm_limewire_known_20261108) is LimeWire built from that source (compiled with the JDK 6 compiler and class library; the only change was to the build file) and run on Windows 11 ARM64 under a 32-bit Java 8u252 with the VM offline (default routes removed, static address with no gateway, DNS to loopback). User is the folder name after Users, Documents and Settings or home in the path, and Settings Folder the LimeWire folder the row came from. "
                 "One row per download memento in downloads.dat (or downloads.bak when downloads.dat does not "
                 "read), the list LimeWire saves of the downloads it has not finished "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/downloader/serial/DownloadSerializeSettingsImpl.java#L14). "
                 "Each memento keeps its fields in a serialObjects map; Download Type is the memento's class "
                 "(Gnutella, Magnet, BT, LibTorrentBT or InNetwork, from the downloader/serial folder of the cited "
                 "commit) and the other columns are the map's entries as stored: name, defaultFileName, sha1Urn, "
                 "incompleteFile, saveFile, torrentPath, fastResumePath, contentLength and trackers. Start Date is "
                 "the limewire.download.startDate attribute, a java.util.Date (milliseconds since 1970 UTC) set "
                 "when the download enters LimeWire's download list "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/core-glue/src/main/java/org/limewire/core/impl/download/CoreDownloadListManager.java#L304-L305); "
                 "on the known data it was 1.7 seconds after the second LimeWire launch carrying the magnet link was started. Other "
                 "attributes are listed in Other Attributes. On the known data one magnet link (an invented "
                 "SHA-1 that matches no file, VM offline) was saved as a LibTorrentBT memento; on that one row "
                 "Save File, Torrent Path, Content Length, Trackers and Other Attributes held no value. The "
                 "Gnutella, Magnet, BT and InNetwork memento classes "
                 "were not exercised. A row records a download LimeWire was asked to make, not that any data "
                 "arrived.",
        "paths": (
            '*/AppData/Roaming/LimeWire/downloads.dat',
            '*/AppData/Roaming/LimeWire/downloads.bak',
            '*/Application Data/LimeWire/downloads.dat',
            '*/Application Data/LimeWire/downloads.bak',
            '*/Library/Preferences/LimeWire/downloads.dat',
            '*/Library/Preferences/LimeWire/downloads.bak',
            '*/.limewire/downloads.dat',
            '*/.limewire/downloads.bak',
        ),
        "output_types": "standard",
        "artifact_icon": "download",
        "sample_data": {
            "windows11_arm_limewire_known_20261108": "Windows 11 build 26200 (ARM64), LimeWire built from wirecode 2b22c50 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
    "limewireSettings": {
        "name": "LimeWire Settings",
        "description": "Selected values from LimeWire's limewire.props and installation.props: last shutdown "
                       "time, sessions, uptime, client ID, save folders, port, search-history and startup "
                       "options and the versions run.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "LimeWire",
        "notes": "LimeWire 5 keeps its settings folder in LimeWire in the Windows application data folder (AppData/Roaming, or Application Data on Windows XP), Library/Preferences/LimeWire on macOS and .limewire in the home folder elsewhere (https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/gnutella-core/src/main/java/com/limegroup/gnutella/util/LimeWireUtils.java#L380-L418); only the Windows folder was exercised, and a folder set with the LIMEWIRE_PREFS_DIR property or a portable copy is not matched. The .dat and .cache stores are Java serialization streams, read with scripts/java_serialization.py (a reader written from the stream specification and checked against a fixture written by the JDK). Field meanings are from LimeWire's GPL source, wiregit/wirecode at commit 2b22c506566ca43c750f2804cb4637921dd6d539. No vendor still distributes LimeWire, so the known data (windows11_arm_limewire_known_20261108) is LimeWire built from that source (compiled with the JDK 6 compiler and class library; the only change was to the build file) and run on Windows 11 ARM64 under a 32-bit Java 8u252 with the VM offline (default routes removed, static address with no gateway, DNS to loopback). User is the folder name after Users, Documents and Settings or home in the path, and Settings Folder the LimeWire folder the row came from. "
                 "One row per settings folder that holds limewire.props, read as a Java properties file (a "
                 "key written twice takes the later value, as Properties.load does). Each column is one setting, "
                 "shown as stored; an empty cell means the key is absent, and LimeWire then uses the default "
                 "named in its definition. Last Shutdown Time is LAST_SHUTDOWN_TIME, milliseconds since 1970 UTC, "
                 "which LimeWire also rewrites periodically while it runs, so it is the last time it was written, "
                 "not necessarily a clean exit "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/core-settings/src/main/java/org/limewire/core/settings/ApplicationSettings.java#L80-L88); "
                 "on the known data it was 0.2 seconds after File > Exit was sent. Sessions, Total Uptime "
                 "(seconds) and Client ID are SESSIONS, TOTAL_UPTIME and CLIENT_ID (same file, lines 25, 49 and "
                 "77). Save Folder is DIRECTORY_FOR_SAVING_FILES "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/core-settings/src/main/java/org/limewire/core/settings/SharingSettings.java#L86), "
                 "Store Save Folder is DIRETORY_FOR_SAVING_LWS_FILES, the key as LimeWire spells it, and Last "
                 "File Chooser Folder is LAST_FILECHOOSER_DIR "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/private-components/swingui/src/main/java/org/limewire/ui/swing/settings/SwingUiSettings.java#L221); "
                 "Port is PORT; Keep Search History is KEEP_SEARCH_HISTORY, default true (SwingUiSettings.java "
                 "line 113), which governs only a search list LimeWire 5 keeps in memory "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/private-components/swingui/src/main/java/org/limewire/ui/swing/search/SearchBar.java#L159-L160, "
                 "https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/private-components/swingui/src/main/java/org/limewire/ui/swing/search/LimeWireUiSearchModule.java#L38): "
                 "no file in LimeWire 5's source saves search terms, and after an offline search was typed on the "
                 "known data no file in the settings or LimeWire folders held the term (no search tab was seen, "
                 "so whether the search ran is not established). Run On Startup is RUN_ON_STARTUP and Anonymous "
                 "Statistics is ALLOW_ANONYMOUS_STATISTICS_GATHERING. Last Version Run, Previous Versions Run and "
                 "Last Java Version Run are from installation.props in the same folder "
                 "(https://github.com/wiregit/wirecode/blob/2b22c506566ca43c750f2804cb4637921dd6d539/components/core-settings/src/main/java/org/limewire/core/settings/InstallSettings.java#L79-L91); "
                 "the known data's build was made from source, so its version is the unreplaced @version@. "
                 "Values LimeWire receives from its servers (host lists, filters, advertising text) are not "
                 "shown. On the known data Keep Search History was empty (absent, so the default true).",
        "paths": (
            '*/AppData/Roaming/LimeWire/limewire.props',
            '*/AppData/Roaming/LimeWire/installation.props',
            '*/Application Data/LimeWire/limewire.props',
            '*/Application Data/LimeWire/installation.props',
            '*/Library/Preferences/LimeWire/limewire.props',
            '*/Library/Preferences/LimeWire/installation.props',
            '*/.limewire/limewire.props',
            '*/.limewire/installation.props',
        ),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {
            "windows11_arm_limewire_known_20261108": "Windows 11 build 26200 (ARM64), LimeWire built from wirecode 2b22c50 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
}

# Folders LimeWire 5 keeps its settings in (LimeWireUtils.java lines 380 to 418 at the cited commit), relative to
# the home folder; the first two are Windows APPDATA (Vista and later, then XP).
_SETTINGS_FOLDERS = (('AppData', 'Roaming', 'LimeWire'), ('Application Data', 'LimeWire'),
                     ('Library', 'Preferences', 'LimeWire'), ('.limewire',))
_HOME_PARENTS = ('Users', 'Documents and Settings', 'home')

_PUBLIC_SHARED_ID = 0  # LibraryFileData.DEFAULT_SHARED_COLLECTION_ID


def _settings_folder(relative):
    """(settings folder path inside the extraction, user, name inside the folder), or None."""
    parts = [p for p in str(relative).replace('\\', '/').split('/') if p]
    for root in _SETTINGS_FOLDERS:
        width = len(root)
        for start in range(len(parts) - width):
            if tuple(parts[start:start + width]) == root:
                home = parts[:start]
                user = home[-1] if len(home) >= 2 and home[-2] in _HOME_PARENTS else ''
                return '/'.join(parts[:start + width]), user, '/'.join(parts[start + width:])
    return None


def _group(context):
    """{folder: {'user': user, 'files': {name: staged path}}} for the files found, sorted."""
    groups = {}
    for found in sorted(str(f) for f in context.get_files_found()):
        if not os.path.isfile(found):
            continue
        located = _settings_folder(canonical_relative(context.get_relative_path(found)))
        if located is None:
            continue
        folder, user, name = located
        entry = groups.setdefault(folder, {'user': user, 'files': {}})
        entry['files'].setdefault(name, found)
    return groups


def _ms_time(value):
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value / 1000, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _first_stream(paths, label):
    """The first object of the first of `paths` that reads, and the path it came from."""
    for path in paths:
        if not path:
            continue
        try:
            with open(path, 'rb') as handle:
                contents = loads(handle.read())
            if contents:
                return contents[0], path
        except (OSError, JavaSerializationError, IndexError, ValueError) as ex:
            logfunc(f'{label}: could not read {os.path.basename(path)}: {ex}')
    return None, None


def _urn_text(obj):
    """The URN string a com.limegroup.gnutella.URN wrote (writeUTF), or ''."""
    if isinstance(obj, JavaObject):
        for item in obj.annotations.get('com.limegroup.gnutella.URN', []):
            if isinstance(item, bytes) and len(item) >= 2:
                length = int.from_bytes(item[:2], 'big')
                return item[2:2 + length].decode('utf-8', 'replace')
    return obj if isinstance(obj, str) else ''


def _urn_set_sha1(obj):
    if isinstance(obj, JavaObject):
        if 'sha1' in obj.fields:
            return _urn_text(obj.fields.get('sha1'))
        for urn in (plain(obj) if isinstance(plain(obj), list) else []):
            text = _urn_text(urn)
            if text.startswith('urn:sha1:'):
                return text
    return ''


def read_library(library_obj):
    """(file data {path: [ids]}, collection names {id: name}, safe urns set) from library5.dat's map."""
    entries = dict(plain(library_obj)) if map_items(library_obj) is not None else {}
    files = {}
    for path, ids in entries.get('FILE_DATA') or []:
        files[str(path)] = [int(i) for i in ids if isinstance(i, int)] if isinstance(ids, list) else []
    names = {k: v for k, v in (entries.get('COLLECTION_NAMES') or []) if isinstance(k, int)}
    safe = set(entries.get('SAFE_URNS') or [])
    return files, names, safe


def read_urn_cache(cache_obj):
    """{path: (modified ms, sha1 urn)} from fileurns.cache."""
    out = {}
    for key, value in map_items(cache_obj) or []:
        if not isinstance(key, JavaObject):
            continue
        items = key.annotations.get('com.limegroup.gnutella.library.UrnCache$UrnSetKey', [])
        block = next((i for i in items if isinstance(i, bytes) and len(i) >= 8), None)
        path = next((i for i in items if isinstance(i, str)), None)
        if path is None:
            continue
        modified = int.from_bytes(block[:8], 'big', signed=True) if block else None
        out[path] = (modified, _urn_set_sha1(value))
    return out


def _xml_attributes(text):
    """Attributes of the XML document's second-level elements, as name=value, or None when it does not parse.

    LimeWire writes an xsi: attribute without declaring the prefix, so the XML is parsed without namespace
    processing.
    """
    attrs = []
    depth = 0

    def start(_name, attributes):
        nonlocal depth
        if depth == 1:
            attrs.extend(f'{key}={val}' for key, val in attributes.items())
        depth += 1

    def end(_name):
        nonlocal depth
        depth -= 1

    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    try:
        parser.Parse(text, True)
    except xml.parsers.expat.ExpatError:
        return None
    return attrs


def read_xml_cache(cache_obj):
    """{path: 'attr=value; ...'} from one xml/data/*.sxml3 cache."""
    out = {}
    for key, value in map_items(cache_obj) or []:
        if not isinstance(key, JavaObject) or not isinstance(value, str):
            continue
        path = plain(key.fields.get('file'))
        if not isinstance(path, str):
            continue
        attrs = _xml_attributes(value)
        if attrs is None:
            out[path] = value
            continue
        out[path] = '; '.join(attrs)
    return out


@artifact_processor
def limewireLibraryFiles(context):
    data_list, sources = [], []
    for folder, group in _group(context).items():
        files = group['files']
        library, library_path = _first_stream([files.get('library5.dat'), files.get('library5.bak')],
                                              'LimeWire Library Files')
        if library is None:
            continue
        sources.append(library_path)
        file_data, names, safe = read_library(library)
        urns = {}
        urn_obj, urn_path = _first_stream([files.get('fileurns.cache')], 'LimeWire Library Files')
        if urn_obj is not None:
            urns = read_urn_cache(urn_obj)
            sources.append(urn_path)
        metadata = {}
        for name in sorted(n for n in files if n.startswith('xml/data/') and n.endswith('.sxml3')):
            xml_obj, xml_path = _first_stream([files[name]], 'LimeWire Library Files')
            if xml_obj is not None:
                metadata.update(read_xml_cache(xml_obj))
                sources.append(xml_path)
        for path in sorted(file_data):
            ids = file_data[path]
            lists = ['Public Shared' if i == _PUBLIC_SHARED_ID else names.get(i, f'list {i}') for i in ids]
            modified, sha1 = urns.get(path, (None, ''))
            data_list.append((_ms_time(modified), path, '\n'.join(lists), ', '.join(str(i) for i in ids),
                              sha1, ('Yes' if sha1 in safe else 'No') if sha1 else '',
                              metadata.get(path, ''), group['user'], folder))
    data_headers = (('Modified Time', 'datetime'), 'File Path', 'Lists', 'List IDs', 'SHA-1',
                    'Passed Dangerous-File Check', 'Metadata', 'User', 'Settings Folder')
    return data_headers, data_list, '\n'.join(sources)


_DOWNLOAD_FIELDS = ('name', 'defaultFileName', 'sha1Urn', 'incompleteFile', 'saveFile', 'torrentPath',
                    'fastResumePath', 'contentLength', 'trackers')


def read_downloads(obj):
    """One dict per download memento in downloads.dat's list."""
    rows = []
    for memento in plain(obj) if isinstance(plain(obj), list) else []:
        if not isinstance(memento, JavaObject):
            continue
        serial = dict(plain(memento.fields.get('serialObjects')) or [])
        row = {'type': memento.classname.rsplit('.', 1)[-1].replace('DownloadMementoImpl', '')}
        for field in _DOWNLOAD_FIELDS:
            value = plain(serial.get(field))
            if isinstance(value, list):
                value = '\n'.join(str(plain(v)) for v in value)
            row[field] = _urn_text(value) if field == 'sha1Urn' else ('' if value is None else value)
        start, other = '', []
        attributes = serial.get('attributes')
        for key, value in plain(attributes) if isinstance(plain(attributes), list) else []:
            if key == 'limewire.download.startDate' and isinstance(value, JavaObject):
                block = next((i for i in value.annotations.get('java.util.Date', []) if isinstance(i, bytes)), b'')
                start = _ms_time(int.from_bytes(block[:8], 'big', signed=True)) if len(block) >= 8 else ''
            else:
                other.append(f'{key}={plain(value)}')
        row['start'] = start
        row['other'] = '\n'.join(other)
        rows.append(row)
    return rows


@artifact_processor
def limewireDownloads(context):
    data_list, sources = [], []
    for folder, group in _group(context).items():
        files = group['files']
        obj, path = _first_stream([files.get('downloads.dat'), files.get('downloads.bak')], 'LimeWire Downloads')
        if obj is None:
            continue
        sources.append(path)
        for row in read_downloads(obj):
            data_list.append((row['start'], row['name'], row['type'], row['defaultFileName'], row['sha1Urn'],
                              row['incompleteFile'], row['saveFile'], row['torrentPath'], row['fastResumePath'],
                              row['contentLength'], row['trackers'], row['other'], group['user'], folder))
    data_headers = (('Start Date', 'datetime'), 'Name', 'Download Type', 'Default File Name', 'SHA-1',
                    'Incomplete File', 'Save File', 'Torrent Path', 'Fast Resume Path', 'Content Length',
                    'Trackers', 'Other Attributes', 'User', 'Settings Folder')
    return data_headers, data_list, '\n'.join(sources)


def java_properties(text):
    """Key and value pairs from a Java .properties file; a repeated key takes the later value."""
    values = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].lstrip()
        index += 1
        if not line or line[0] in '#!':
            continue
        while line.endswith('\\') and not line.endswith('\\\\') and index < len(lines):
            line = line[:-1] + lines[index].lstrip()
            index += 1
        cut = next((i for i, c in enumerate(line) if c in '=:' and (i == 0 or line[i - 1] != '\\')), None)
        if cut is None:
            continue
        key, value = line[:cut].strip(), line[cut + 1:].lstrip()
        out, pos = [], 0
        while pos < len(value):
            char = value[pos]
            if char == '\\' and pos + 1 < len(value):
                nxt = value[pos + 1]
                if nxt == 'u' and pos + 6 <= len(value):
                    try:
                        out.append(chr(int(value[pos + 2:pos + 6], 16)))
                        pos += 6
                        continue
                    except ValueError:
                        pass
                out.append({'t': '\t', 'n': '\n', 'r': '\r', 'f': '\f'}.get(nxt, nxt))
                pos += 2
                continue
            out.append(char)
            pos += 1
        values[key.replace('\\', '')] = ''.join(out)
    return values


def _read_props(path):
    try:
        with open(path, 'r', encoding='latin-1') as handle:
            return java_properties(handle.read())
    except OSError as ex:
        logfunc(f'LimeWire Settings: could not read {os.path.basename(path)}: {ex}')
        return None


_SETTING_COLUMNS = ('SESSIONS', 'TOTAL_UPTIME', 'CLIENT_ID', 'DIRECTORY_FOR_SAVING_FILES',
                    'DIRETORY_FOR_SAVING_LWS_FILES', 'LAST_FILECHOOSER_DIR', 'PORT', 'KEEP_SEARCH_HISTORY',
                    'RUN_ON_STARTUP', 'ALLOW_ANONYMOUS_STATISTICS_GATHERING')
_INSTALL_COLUMNS = ('LAST_VERSION_RUN', 'PREVIOUS_RAN_VERSIONS', 'LAST_JAVA_VERSION_RUN')


@artifact_processor
def limewireSettings(context):
    data_list, sources = [], []
    for folder, group in _group(context).items():
        files = group['files']
        if 'limewire.props' not in files:
            continue
        props = _read_props(files['limewire.props'])
        if props is None:
            continue
        sources.append(files['limewire.props'])
        install = {}
        if 'installation.props' in files:
            install = _read_props(files['installation.props']) or {}
            sources.append(files['installation.props'])
        try:
            shutdown = _ms_time(int(props.get('LAST_SHUTDOWN_TIME', '')))
        except ValueError:
            shutdown = ''
        data_list.append((shutdown,) + tuple(props.get(k, '') for k in _SETTING_COLUMNS)
                         + tuple(install.get(k, '') for k in _INSTALL_COLUMNS) + (group['user'], folder))
    data_headers = (('Last Shutdown Time', 'datetime'), 'Sessions', 'Total Uptime (seconds)', 'Client ID',
                    'Save Folder', 'Store Save Folder', 'Last File Chooser Folder', 'Port', 'Keep Search History',
                    'Run On Startup', 'Anonymous Statistics', 'Last Version Run', 'Previous Versions Run',
                    'Last Java Version Run', 'User', 'Settings Folder')
    return data_headers, data_list, '\n'.join(sources)

