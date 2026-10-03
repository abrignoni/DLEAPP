"""Saved Application State on macOS, for DLEAPP: the titled windows each savedState folder's
windows.plist lists, and Terminal tab state decrypted from its data.data.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSavedStateWindows": {
        "name": "Saved Application State Windows",
        "description": "Titled windows listed in the windows.plist of each Saved Application State "
                       "folder, with the application its folder name or ApplicationMapping.plist "
                       "gives and the user it belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Saved Application State (macOS)",
        "notes": "Reads the windows.plist in each savedState folder of a Saved Application State "
                 "folder and reports one row per entry that carries an NSTitle, with that entry's "
                 "NSWindowID as Window ID and its NSTitle as Window Title, as stored. Mothers Ruin "
                 "Software's 'Saved Application State' (revised 2025-08-02, "
                 "https://www.mothersruin.com/software/Archaeology/reverse/appstate.html) "
                 "describes these folders as where macOS stores state for its Resume feature: "
                 "under Library/Saved Application State in the home folder or in a sandboxed app's "
                 "container through macOS 14, and inside the talagentd daemon container under "
                 "Library/Daemon Containers from macOS 15. The declared path matches all three "
                 "places. Entries without a title are not reported; in both files on "
                 "dleapp_macos_bigsur those were the entry marked NSIsMainMenuBar and the entry "
                 "marked NSIsGlobal. Application is the savedState folder's name without its "
                 ".savedState extension unless an ApplicationMapping.plist names the folder, as "
                 "described next, and User is the folder name after Users in the path. Under the "
                 "talagentd container the folders are named by a unique identifier rather than a "
                 "bundle identifier, and the ApplicationMapping.plist in the same Saved "
                 "Application State folder maps them: its root is an array in which the dictionary "
                 "describing an app comes before the name of that app's folder (Mothers Ruin, same "
                 "page; Velociraptor's MacOS.Applications.SavedState by Wes Lambert, "
                 "https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.SavedState.yaml#L30). "
                 "Application takes the identifier that dictionary holds under protected, "
                 "signingIdentifier, or under unprotected, bundleIdentifier; a folder the file "
                 "does not name keeps its own name, State Folder always shows the folder's own "
                 "name, and a mapping file that is not a plist array is logged. Both forms of the "
                 "dictionary, and the file naming every folder beside it, were measured locally on "
                 "a private macOS 26 system, where the rows equalled an independent parse of the "
                 "same files; counts and values from it are not published. Velociraptor's "
                 "description adds that reading the daemon container path requires Full Disk "
                 "Access, so a collection made without it can come back empty "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.SavedState.yaml#L5). "
                 "Two copies whose paths differ only by a leading System/Volumes/Data and whose "
                 "windows.plist is byte-identical are read once, and a windows.plist that is not a "
                 "plist array is logged and skipped. dleapp_macos_bigsur held a windows.plist in "
                 "the com.apple.Terminal savedState folder and in the com.apple.iCal one inside "
                 "its container: the Terminal one listed one titled window, which gave the 1 row, "
                 "and the com.apple.iCal one listed none. The com.apple.Maps~iosmac and "
                 "com.apple.MobileSMS~iosmac folders there hold a KnownSceneSessions/data.data and "
                 "no windows.plist, and are not read. The public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15) holds no Saved Application State "
                 "folder, so the talagentd location was tested only on that private system.",
        "paths": (
            '*/Saved Application State/*.savedState/windows.plist',
            '*/Saved Application State/ApplicationMapping.plist',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "app-window",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
        },
    },
    "macosTerminalSavedState": {
        "name": "Terminal Saved State",
        "description": "Terminal tabs decrypted from Terminal's Saved Application State data.data, "
                       "with each tab's working directory and saved text.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Command Line (macOS)",
        "notes": "Decrypts the data.data in each savedState folder that has a windows.plist beside "
                 "it and reports each Terminal window record found, one row per dictionary in the "
                 "record's Window Settings list. Following Mothers Ruin Software's 'Saved "
                 "Application State' (revised 2025-08-02, "
                 "https://www.mothersruin.com/software/Archaeology/reverse/appstate.html) and "
                 "Velociraptor's MacOS.Applications.SavedState by Wes Lambert "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.SavedState.yaml#L25-L28), "
                 "data.data is a sequence of records, each the magic NSCR1000, a big-endian window "
                 "id and a big-endian length that counts the 16-byte header, followed by "
                 "AES-128-CBC ciphertext under that window's NSDataKey from windows.plist with a "
                 "zero IV; the plaintext is a 4-byte field, a big-endian length and an identifier, "
                 "then values each made of a 4-letter type, a big-endian length and the data. A "
                 "record is taken as a Terminal window when its first rchv value is a keyed "
                 "archive holding a TTWindowState with a Window Settings list, the structure "
                 "CrowdStrike describes in 'Saved by the Shell: Reconstructing Command-Line "
                 "Activity on MacOS' "
                 "(https://www.crowdstrike.com/en-us/blog/reconstructing-command-line-activity-on-macos/), "
                 "so the folder's name plays no part. User, Application and State Folder are read "
                 "as in Saved Application State Windows, including the names "
                 "ApplicationMapping.plist gives. Window Title is the archive's NSTitle, Tab is "
                 "the dictionary's 1-based position in Window Settings, and Tab Selected, Working "
                 "Directory URL (the Tab Working Directory URL String value), Tab Scrollback "
                 "Restorable and Tab Session ID are those keys as stored. Saved Text is built from "
                 "the dictionary's Tab Contents v2 list, which CrowdStrike decodes into the text "
                 "of the Terminal session and notes carries no timestamps. On the tested records "
                 "that list alternated a text item and a descriptor made of 24-byte records. On "
                 "dleapp_macos_bigsur every descriptor was one record whose bytes 8 to 11 held, "
                 "little-endian, the length of the text item before it; on a private macOS 26 "
                 "system, measured locally, a descriptor could also be several such records, whose "
                 "fields are not interpreted. Saved Text joins the text items when every "
                 "descriptor is a whole number of 24-byte records and each one-record descriptor "
                 "holds its text item's length, and otherwise is left blank and the run log says "
                 "so. Latest Record is Yes on the last record, by position in the file, among the "
                 "decoded records with the same window id and identifier, since the file is "
                 "append-only and the last record for a window id and identifier is the current "
                 "one "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/MacOS.Applications.SavedState.yaml#L27; "
                 "Mothers Ruin), and Record Offset is the record's byte offset in data.data. "
                 "Records for a window id that windows.plist holds no NSDataKey for, and records "
                 "that do not decrypt with it, are counted in the run log and not reported, and "
                 "play no part in Latest Record; Mothers Ruin notes that the encryption keys are "
                 "refreshed on some schedule. A header other than NSCR1000 ends the reading of "
                 "that file and is logged; CrowdStrike also names a record version 0006, which is "
                 "not read. The window_N.data files, which both Mothers Ruin and Velociraptor "
                 "describe as window images encrypted with a key kept in the keychain rather than "
                 "an NSDataKey, are not read. Two copies whose paths differ only by a leading "
                 "System/Volumes/Data and whose windows.plist and data.data are byte-identical are "
                 "read once. On dleapp_macos_bigsur the com.apple.Terminal data.data held 4 "
                 "records, all of which decrypted, and its one Terminal window record gave the 1 "
                 "row: Saved Text is a Last login line and a prompt followed by 22 empty lines, 91 "
                 "characters, the same as an independent decryption that found the records by "
                 "their magic and each archive by the length stored before it, and its Tab "
                 "Contents v2 held 24 text items each followed by a 24-byte item of the layout "
                 "above. The com.apple.iCal data.data there held 9 records, 6 of them for a window "
                 "its windows.plist holds no key for. No window with more than one tab was tested. "
                 "On the private macOS 26 system, Terminal wrote its window record while it ran, "
                 "the record decrypted with the key its windows.plist gave, and a command typed "
                 "there for the test came back in Saved Text; counts and values from it are not "
                 "published. Mothers Ruin describes this state as kept when an app quits only "
                 "while Close windows when quitting an application is off, and on that system "
                 "Terminal's folder was empty after Terminal was quit, so an empty or missing "
                 "Terminal folder does not show that Terminal went unused. The public MacBook Pro "
                 "logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) holds no Saved "
                 "Application State folder.",
        "paths": (
            '*/Saved Application State/*.savedState/windows.plist',
            '*/Saved Application State/*.savedState/data.data',
            '*/Saved Application State/ApplicationMapping.plist',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
        },
    },
}

import hashlib
import os
import plistlib
import struct

from Crypto.Cipher import AES

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative, load_plist, resolve_keyed_archive, user_from_path

_RECORD_HEADER = struct.Struct('>8sII')
_RECORD_MAGIC = b'NSCR1000'


def stored_text(value):
    """A stored value as report text: Yes or No for a boolean, '' for None, else as stored."""
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return '' if value is None else str(value)


def application_name(folder):
    """A savedState folder's name without its .savedState extension."""
    name = os.path.basename(str(folder).replace('\\', '/').rstrip('/'))
    return name[:-len('.savedState')] if name.endswith('.savedState') else name


def application_mapping(path):
    """{savedState folder name: app identifier} from an ApplicationMapping.plist, or None.

    Its root is an array in which a dictionary describing an app is followed by the name of that
    app's savedState folder. The dictionary names the app under protected, signingIdentifier, or
    under unprotected, bundleIdentifier. None when the file is not a plist array.
    """
    mapping = load_plist(path)
    if not isinstance(mapping, list):
        return None
    names = {}
    for info, folder in zip(mapping, mapping[1:]):
        if not (isinstance(info, dict) and isinstance(folder, str)):
            continue
        for side, key in (('protected', 'signingIdentifier'), ('unprotected', 'bundleIdentifier')):
            inner = info.get(side)
            if isinstance(inner, dict) and isinstance(inner.get(key), str):
                names[folder] = inner[key]
                break
    return names


def application_names(context, folders, label):
    """{folder: (application, mapping file or '')} for savedState folders.

    A folder named in the ApplicationMapping.plist beside it takes the identifier given there,
    with that file's path; any other folder takes its own name without the .savedState extension.
    """
    mappings, names = {}, {}
    for folder in folders:
        parent = os.path.dirname(folder)
        path = os.path.join(parent, 'ApplicationMapping.plist')
        if parent not in mappings:
            mapping = application_mapping(path) if os.path.isfile(path) else {}
            if mapping is None:
                logfunc(f'{label}: {context.get_relative_path(path)} is not a plist array, so '
                        'the folders beside it keep their own names')
                mapping = {}
            mappings[parent] = mapping
        stem = application_name(folder)
        names[folder] = (mappings[parent][stem], path) if stem in mappings[parent] else (stem, '')
    return names


def state_folders(context, files, names):
    """The savedState folders holding a windows.plist, shortest path first.

    Two folders whose paths differ only by a leading System/Volumes/Data/ and whose files in
    `names` are byte-identical are read once, the way macos_plists.unique_sources reads files.
    """
    folders = sorted({os.path.dirname(str(f)) for f in files
                      if os.path.basename(str(f)) == 'windows.plist' and os.path.isfile(str(f))},
                     key=lambda folder: (len(folder), folder))
    kept, seen = [], set()
    for folder in folders:
        digest = hashlib.sha256()
        for name in names:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                with open(path, 'rb') as handle:
                    digest.update(handle.read())
            digest.update(b'|')
        key = (canonical_relative(context.get_relative_path(folder)), digest.hexdigest())
        if key not in seen:
            seen.add(key)
            kept.append(folder)
    return kept


def titled_windows(windows):
    """(window id, title) for each windows.plist entry that carries an NSTitle."""
    rows = []
    for entry in windows if isinstance(windows, list) else []:
        if isinstance(entry, dict) and 'NSTitle' in entry:
            window_id = entry.get('NSWindowID')
            rows.append(('' if window_id is None else window_id, stored_text(entry['NSTitle'])))
    return rows


def data_keys(windows):
    """{window id: NSDataKey} for the windows.plist entries that carry a 16-byte NSDataKey."""
    keys = {}
    for entry in windows if isinstance(windows, list) else []:
        if isinstance(entry, dict):
            window_id, key = entry.get('NSWindowID'), entry.get('NSDataKey')
            if isinstance(window_id, int) and isinstance(key, bytes) and len(key) == 16:
                keys[window_id] = key
    return keys


def split_records(data):
    """(records, problem): (offset, window id, ciphertext) for each record of a data.data.

    A record is the magic NSCR1000, a big-endian window id and a big-endian length that counts
    the 16-byte header. Reading stops at the first header that does not fit that description.
    """
    records, offset = [], 0
    while offset < len(data):
        if len(data) - offset < _RECORD_HEADER.size:
            return records, f'the {len(data) - offset} bytes at offset {offset} are too few for a record'
        magic, window_id, length = _RECORD_HEADER.unpack_from(data, offset)
        if magic != _RECORD_MAGIC:
            return records, f'the record at offset {offset} does not start with NSCR1000'
        if length < _RECORD_HEADER.size or offset + length > len(data):
            return records, f'the record at offset {offset} gives a length of {length}, past the end'
        records.append((offset, window_id, data[offset + _RECORD_HEADER.size:offset + length]))
        offset += length
    return records, ''


def decrypt_record(key, ciphertext):
    """(identifier, [(type, value)]) from a record's ciphertext, or None when it does not decode.

    The plaintext is a 4-byte field, a big-endian key length and the UTF-8 key, then values of a
    4-letter type, a big-endian length and the data, then zero padding.
    """
    if not ciphertext or len(ciphertext) % 16:
        return None
    plain = AES.new(key, AES.MODE_CBC, iv=bytes(16)).decrypt(ciphertext)
    key_length = struct.unpack_from('>I', plain, 4)[0]
    position = 8 + key_length
    if position > len(plain):
        return None
    try:
        identifier = plain[8:position].decode('utf-8')
    except UnicodeDecodeError:
        return None
    values = []
    while position + 8 <= len(plain):
        kind, length = struct.unpack_from('>4sI', plain, position)
        if not kind.isalpha() or position + 8 + length > len(plain):
            break
        values.append((kind.decode('ascii'), plain[position + 8:position + 8 + length]))
        position += 8 + length
    return identifier, values


def archive_of(values):
    """The first rchv value of a record as a parsed keyed archive, or None."""
    for kind, value in values:
        if kind == 'rchv':
            try:
                archive = plistlib.loads(value)
            except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
                return None
            return archive if isinstance(archive, dict) else None
    return None


def terminal_window(archive):
    """(window title, [tab dictionaries]) when an archive holds a TTWindowState, else None."""
    state = resolve_keyed_archive(archive, 'TTWindowState')
    if not isinstance(state, dict):
        return None
    tabs = state.get('Window Settings')
    tabs = [tab for tab in tabs if isinstance(tab, dict)] if isinstance(tabs, list) else []
    return stored_text(resolve_keyed_archive(archive, 'NSTitle')), tabs


def saved_text(items):
    """The text of a Tab Contents v2 list, or None when the list does not follow its layout.

    The list alternates a text item and a descriptor of one or more 24-byte records. A
    descriptor of one record holds, little-endian at bytes 8 to 11, the length of the text item
    before it; a longer descriptor is not interpreted. The text items are joined in order.
    """
    if not isinstance(items, list) or len(items) % 2:
        return None
    parts = []
    for text, descriptor in zip(items[0::2], items[1::2]):
        if not isinstance(text, bytes) or not isinstance(descriptor, bytes):
            return None
        if not descriptor or len(descriptor) % 24:
            return None
        if len(descriptor) == 24 and int.from_bytes(descriptor[8:12], 'little') != len(text):
            return None
        parts.append(text.decode('utf-8', 'replace'))
    return ''.join(parts)


@artifact_processor
def macosSavedStateWindows(context):
    data_headers = ('User', 'Application', 'Window ID', 'Window Title', 'State Folder')
    data_list, sources = [], []
    folders = state_folders(context, context.get_files_found(), ('windows.plist',))
    applications = application_names(context, folders, 'Saved Application State Windows')
    for folder in folders:
        path = os.path.join(folder, 'windows.plist')
        relative = context.get_relative_path(folder)
        windows = load_plist(path)
        if not isinstance(windows, list):
            logfunc(f'Saved Application State Windows: {relative}/windows.plist is not a plist array')
            continue
        application, mapping_path = applications[folder]
        rows = [(user_from_path(relative), application, window_id, title, relative)
                for window_id, title in titled_windows(windows)]
        data_list.extend(rows)
        sources.append(path)
        if rows and mapping_path and mapping_path not in sources:
            sources.append(mapping_path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosTerminalSavedState(context):
    data_headers = ('User', 'Application', 'Window ID', 'Window Title', 'Tab', 'Tab Selected',
                    'Working Directory URL', 'Saved Text', 'Tab Scrollback Restorable',
                    'Tab Session ID', 'Latest Record', 'Record Offset', 'State Folder')
    data_list, sources = [], []
    folders = state_folders(context, context.get_files_found(), ('windows.plist', 'data.data'))
    applications = application_names(context, folders, 'Terminal Saved State')
    for folder in folders:
        application, mapping_path = applications[folder]
        data_path = os.path.join(folder, 'data.data')
        if not os.path.isfile(data_path):
            continue
        relative = context.get_relative_path(folder)
        keys = data_keys(load_plist(os.path.join(folder, 'windows.plist')))
        with open(data_path, 'rb') as handle:
            records, problem = split_records(handle.read())
        if problem:
            logfunc(f'Terminal Saved State: {relative}/data.data: {problem}; the rest is not read')
        decoded, no_key, undecoded = [], 0, 0
        for offset, window_id, ciphertext in records:
            if window_id not in keys:
                no_key += 1
                continue
            plain = decrypt_record(keys[window_id], ciphertext)
            if plain is None:
                undecoded += 1
                continue
            decoded.append((offset, window_id) + plain)
        if no_key or undecoded:
            logfunc(f'Terminal Saved State: {relative}/data.data: {no_key} record(s) for a window '
                    f'windows.plist holds no key for and {undecoded} that did not decrypt, not read')
        latest = {(window_id, identifier): offset for offset, window_id, identifier, _ in decoded}
        rows = []
        for offset, window_id, identifier, values in decoded:
            archive = archive_of(values)
            window = terminal_window(archive) if archive else None
            if window is None:
                continue
            title, tabs = window
            is_latest = 'Yes' if latest[(window_id, identifier)] == offset else 'No'
            for position, tab in enumerate(tabs, 1):
                text = ''
                if 'Tab Contents v2' in tab:
                    text = saved_text(tab['Tab Contents v2'])
                    if text is None:
                        logfunc(f'Terminal Saved State: {relative}/data.data: the Tab Contents v2 of '
                                f'tab {position} in the record at offset {offset} does not follow '
                                'the text and descriptor layout, so Saved Text is left blank')
                        text = ''
                rows.append((user_from_path(relative), application, window_id, title,
                             position, stored_text(tab.get('TabSelected')),
                             stored_text(tab.get('Tab Working Directory URL String')), text,
                             stored_text(tab.get('Tab Scrollback Restorable')),
                             stored_text(tab.get('Tab Session ID')), is_latest, offset, relative))
        if rows:
            data_list.extend(rows)
            sources.extend((os.path.join(folder, 'windows.plist'), data_path))
            if mapping_path and mapping_path not in sources:
                sources.append(mapping_path)
    return data_headers, data_list, '\n'.join(sources)
