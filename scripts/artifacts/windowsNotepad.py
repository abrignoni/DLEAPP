__artifacts_v2__ = {
    "windowsNotepadTabs": {
        "name": "Windows Notepad Tabs",
        "description": "Tabs of Windows 11 Notepad from its TabState files: the file path a tab is "
                       "tied to, the text the tab file stores (which need not have been saved to "
                       "disk), unsaved edits recorded after it, the stored saved-file size and "
                       "SHA-256, selection, the time unsaved changes began, and each block's "
                       "CRC-32 check.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Reads each tab file (<tab id>.bin) in LocalState/TabState under a user's "
                 "Packages/Microsoft.WindowsNotepad_* folder, one row per tab file, with the layout "
                 "ogmini's Notepad-State-Library documents (MIT; "
                 "https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L87-L203),"
                 " read by DLEAPP's own code in scripts/windows_notepad.py. Tab Kind is File for type flag"
                 " 1, a tab saved to or opened from a file on disk, and No file for type flag 0, a tab "
                 "that exists only in Notepad's files (README.md lines 96 to 113). Stored Text is the text"
                 " the tab file holds; for a No file tab Notepad has not saved it to a file on disk, and "
                 "for a File tab it is empty once every change is saved (README.md lines 123 to 143). Text"
                 " With Unsaved Edits Applied is derived: Stored Text with each unsaved buffer chunk after"
                 " the tab's CRC applied in order, each chunk deleting its count of characters at its "
                 "position and inserting its characters there (README.md lines 194 to 203); Notepad writes"
                 " those chunks while it is open and folds them into the stored text when it closes or the"
                 " file is saved (README.md line 361). Unsaved Edit Count is the number of chunks. Unsaved"
                 " Changes Started is the tab's timestamp, a FILETIME that Notepad sets when the first "
                 "unsaved change is made to a File tab and resets to 0 when the file is saved (README.md "
                 "line 351); a 0 is shown blank. Saved File Size (bytes, as stored) and Saved File SHA-256"
                 " (as stored) describe the file on disk and are 0 once all changes are saved (README.md "
                 "lines 130 and 134); a zero hash is shown blank. Encoding and Line Ending are named from "
                 "README.md lines 131 and 132. Unsaved Flag (as stored), Word Wrap, Right To Left, Show "
                 "Unicode and More Options are the stored bytes, More Options in hex. Window Tab Position "
                 "and Active Tab come from the current WindowState file of the same package folder, the "
                 "one of each window's pair with the higher sequence number (README.md line 355), whose "
                 "tab ids name the tab files; Window Tab Position is 1-based, and a tab no window lists "
                 "has them blank. CRC-32 Check is the result of recomputing each block's CRC-32 (the zlib "
                 "polynomial) over the bytes it covers and comparing it with the stored value, most "
                 "significant byte first "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/NPTabState.cs#L285-L479,"
                 " "
                 "https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/CRC32Check.cs#L9);"
                 " State Files gives the same check for the tab's <tab id>.0.bin and <tab id>.1.bin state "
                 "files, which the row does not otherwise report. A file that ends early or lacks the NP "
                 "signature is logged and not reported. Tested on hexordia_mvs2025_win11, whose "
                 "ProgramData/Microsoft/Windows/AppRepository folder names Notepad package 11.2409.9.0: 4 "
                 "File tabs, each showing the saved condition README.md lines 123 to 143 describe: Unsaved"
                 " Changes Started, Stored Text, Text With Unsaved Edits Applied and Saved File SHA-256 "
                 "(as stored) held no value on any row, and Unsaved Edit Count, Unsaved Flag (as stored) "
                 "and Saved File Size (bytes, as stored) held 0 on every row; Tab Kind held File, Encoding"
                 " UTF-8 (5), Line Ending Windows (CRLF) (1), Word Wrap (as stored) 1, Right To Left (as "
                 "stored) 0, Show Unicode (as stored) 0, CRC-32 Check pass and User one value on every "
                 "row, and Selection Start and Selection End were equal on every row. On that image each "
                 "tab's .0.bin state file passes its CRC-32 and each .1.bin is empty. The No file tab, "
                 "unsaved text, unsaved buffer chunk and non-zero timestamp paths were not exercised by "
                 "any of the 10 Windows images run; they were run on the 25 published test files of "
                 "Notepad-State-Library (NotepadStateLibrary/TestApp/TestFiles at the same commit), where "
                 "every block of the 21 non-empty files passed its CRC-32, the stored SHA-256 equalled the"
                 " SHA-256 of the published saved text on 12 of the 15 File tabs that have one (on the "
                 "other 3 the published text is shorter than the saved size the tab records), and applying"
                 " the 3 chunks of SavedFile-LargeCopyPaste-NotClosed.bin gave the stored text of "
                 "SavedFile-LargeCopyPaste-Closed.bin exactly. The other published pair, "
                 "SavedFile-UnsavedChanges-NotClosed.bin and -Closed.bin, does not match after replay; "
                 "their timestamps differ, so they are not one capture. Settings/settings.dat, which "
                 "Notepad-State-Library describes as holding the recent files list and the last find and "
                 "replace strings (README.md lines 260 to 347), is read by Windows Notepad Settings.",
        "paths": ('*/AppData/Local/Packages/Microsoft.WindowsNotepad_*/LocalState/TabState/*.bin',
                  '*/AppData/Local/Packages/Microsoft.WindowsNotepad_*/LocalState/WindowState/*.bin'),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Notepad 11.2409.9.0 | 4 rows (4 File tabs)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no file matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no file matches the declared paths)",
        },
    },
    "windowsNotepadWindows": {
        "name": "Windows Notepad Windows",
        "description": "Windows of Windows 11 Notepad from its WindowState files: the tabs each "
                       "window lists in order, the active tab, window position and size, and the "
                       "CRC-32 check.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Reads each WindowState file (<window id>.0.bin and <window id>.1.bin) in "
                 "LocalState/WindowState under a user's Packages/Microsoft.WindowsNotepad_* folder, one "
                 "row per file, with the layout ogmini's Notepad-State-Library documents (MIT; "
                 "https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L205-L245)"
                 " and parses "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/NPWindowState.cs#L159-L228)."
                 " Notepad alternates updates between a window's two files, and Current File is Yes for "
                 "the one with the higher sequence number (README.md line 355). Tab IDs In Order are the "
                 "window's tab ids in view order, each the name of a tab file in TabState when that file "
                 "still exists; Active Tab Index is 0-based. Top Left, Bottom Right and Window Size are "
                 "the stored unsigned 32-bit values. Bytes After CRC counts the bytes after the CRC, which"
                 " may hold ids of tabs closed since (README.md lines 247 to 251); they are counted, not "
                 "decoded. CRC-32 Check is as in Windows Notepad Tabs. An empty file is logged and not "
                 "reported. Tested on hexordia_mvs2025_win11 (Notepad package 11.2409.9.0, named in the "
                 "image's AppRepository folder), one window, 2 rows, both passing; Sequence Number and "
                 "Active Tab Index are identical on both rows of that image because the stored values "
                 "coincide on each row, not by derivation, and Bytes After CRC held 0 on both.",
        "paths": ('*/AppData/Local/Packages/Microsoft.WindowsNotepad_*/LocalState/WindowState/*.bin',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "layout",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Notepad 11.2409.9.0 | 2 rows (one window)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no file matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no file matches the declared paths)",
        },
    },
    "windowsNotepadSettings": {
        "name": "Windows Notepad Settings",
        "description": "Settings of Windows 11 Notepad from its Settings/settings.dat hive, one row "
                       "per stored value with the time stored with it, among them the recent files "
                       "list and the last Find and Replace strings, which hold free text typed into Notepad.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Reads every value of every key in Settings/settings.dat under a user's "
                 "Packages/Microsoft.WindowsNotepad_* folder, one row per value, from the hive opened and "
                 "decoded as in Phone Link Linked Devices (scripts/windows_app_settings.py). "
                 "Notepad-State-Library describes the file as an application hive in which a setting "
                 "that is absent has not been changed from its default "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L269), "
                 "so a missing row is the default in effect, not a record that the feature was unused. "
                 "Value Written is the FILETIME stored at the end of the value, which the same README "
                 "describes as the time of the setting's change (lines 298 to 307 and 353); Key Last "
                 "Written is the key's own last-written time. Free Text (Find or Replace) is Yes for "
                 "FindString and ReplaceString, which the README describes as the last string searched with "
                 "Find and the last replacement string (lines 313 and 330): free text typed into Notepad, not a setting Notepad chooses. "
                 "RecentFiles, the recent files list, most recently closed first (line 327), is shown as "
                 "stored and not split into files, since the README calls it a CSV array and no tested "
                 "image holds one to check the separator against. Documented Meaning gives the README's "
                 "description for the names it describes (lines 311 to 347), with the line; Value is "
                 "the decoded value as stored, and Type is the packaged-app type it is stored as. Type "
                 "0x5F5E104 (Int32) is read as signed, as python-registry reads it; the README lists it as "
                 "unsigned (line 302). Tested on hexordia_mvs2025_win11 (Notepad package 11.2409.9.0): 9 "
                 "rows, all in LocalState: six WindowPosition values and three TeachingTip values. That "
                 "hive holds no FindString, ReplaceString or RecentFiles value, so Free Text (Find or Replace) "
                 "held no value on any row, and Documented Meaning held no value on any row because the "
                 "README describes none of those 9 names; Key, Key Last Written and User held one value on "
                 "every row (one key, one home folder). On pc_mus_001_win11 the hive holds no values (0 rows). The Find, Replace "
                 "and recent files rows were run only on synthetic hives built for the tests.",
        "paths": ('*/AppData/Local/Packages/Microsoft.WindowsNotepad_*/Settings/settings.dat*',),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Notepad 11.2409.9.0 | 9 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (hive holds no values)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no file matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no file matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no file matches the declared paths)",
        },
    },
}

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_notepad import NotepadError, apply_chunks, parse_tab, parse_window
from scripts.windows_app_settings import HIVE_ERRORS, keys, open_settings, package_hives, settings
from scripts.windows_registry import filetime_utc, user_from_path

# README.md, lines 131 and 132 (EncodingType, CarriageReturnType), commit ce53f9d6.
ENCODINGS = {1: 'ANSI', 2: 'UTF-16LE', 3: 'UTF-16BE', 4: 'UTF-8 with BOM', 5: 'UTF-8'}
LINE_ENDINGS = {1: 'Windows (CRLF)', 2: 'Macintosh (CR)', 3: 'Unix (LF)'}
TAB_KINDS = {0: 'No file', 1: 'File'}

_STATE_NAME = re.compile(r'^(?P<id>.+)\.(?P<slot>[01])\.bin$', re.IGNORECASE)


def _label(names, value):
    if value is None:
        return ''
    return f'{names.get(value, "unknown")} ({value})'


def _folder_kind(relative):
    parts = relative.replace('\\', '/').split('/')
    return parts[-2].lower() if len(parts) >= 2 else ''


def _files(context):
    """(path, relative) of each staged state file, once each, sorted by relative path."""
    seen, out = set(), []
    for item in context.get_files_found():
        path = str(item)
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        out.append((path, context.get_relative_path(path)))
    return sorted(out, key=lambda entry: entry[1])


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _crc_text(ok, chunks):
    failed = sum(1 for chunk in chunks if not chunk['crc_ok'])
    text = 'pass' if ok else 'FAIL'
    if chunks:
        text += f'; unsaved buffer chunks {len(chunks) - failed} of {len(chunks)} pass'
    return text


def _windows_by_tab(files, label):
    """{(folder, tab id): (position, is active, window file)} from each window's current file.

    A window keeps two files, <id>.0.bin and <id>.1.bin, and the one with the higher
    sequence number is the current one (README.md, line 355).
    """
    current = {}
    for path, relative in files:
        if _folder_kind(relative) != 'windowstate':
            continue
        match = _STATE_NAME.match(os.path.basename(relative))
        data = _read(path)
        if not match or not data:
            continue
        try:
            window = parse_window(data)
        except NotepadError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        key = (os.path.dirname(os.path.dirname(relative)), match.group('id'))
        if key not in current or window['sequence'] > current[key][0]['sequence']:
            current[key] = (window, relative)
    placed = {}
    for (folder, _window_id), (window, relative) in current.items():
        for index, tab_id in enumerate(window['tabs']):
            placed[(folder, tab_id.lower())] = (index + 1, index == window['active'], relative)
    return placed


@artifact_processor
def windowsNotepadTabs(context):
    label = 'Windows Notepad Tabs'
    files = _files(context)
    placed = _windows_by_tab(files, label)
    states = {}
    for path, relative in files:
        match = _STATE_NAME.match(os.path.basename(relative))
        if _folder_kind(relative) == 'tabstate' and match:
            states.setdefault((os.path.dirname(relative), match.group('id').lower()), []).append(
                (path, relative))
    data_list = []
    sources = []
    for path, _staged_relative in files:
        relative = context.get_relative_path(path)
        name = os.path.basename(relative)
        if _folder_kind(relative) != 'tabstate' or _STATE_NAME.match(name) \
                or not name.lower().endswith('.bin'):
            continue
        data = _read(path)
        try:
            tab = parse_tab(data)
        except NotepadError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        if tab['type_flag'] not in (0, 1):
            logfunc(f'{label}: {relative} has type flag {tab["type_flag"]}, not a tab file; not read')
            continue
        sources.append(path)
        tab_id = name[:-4]
        folder = os.path.dirname(relative)
        package = os.path.dirname(folder)
        position, active, _window_file = placed.get((package, tab_id.lower()), ('', '', ''))
        state_crc = []
        for state_path, state_relative in sorted(states.get((folder, tab_id.lower()), [])):
            state_data = _read(state_path)
            if not state_data:
                state_crc.append(f'{os.path.basename(state_relative)} empty')
                continue
            try:
                state = parse_tab(state_data)
                state_crc.append(f'{os.path.basename(state_relative)} '
                                 f'{"pass" if state["crc_ok"] else "FAIL"}')
            except NotepadError as ex:
                state_crc.append(f'{os.path.basename(state_relative)} unreadable ({ex})')
        chunks = tab['chunks']
        replayed = apply_chunks(tab['content'], chunks) if chunks else ''
        if chunks and replayed is None:
            replayed = ''
            logfunc(f'{label}: {relative}: an unsaved buffer chunk falls outside the stored text; '
                    f'edits not applied')
        file_hash = tab['file_hash']
        data_list.append((
            filetime_utc(tab['timestamp']) if tab['timestamp'] else '',
            TAB_KINDS.get(tab['type_flag'], ''),
            tab['file_path'] or '',
            tab['content'] or '',
            replayed,
            len(chunks),
            tab['unsaved_flag'] if tab['unsaved_flag'] is not None else '',
            tab['saved_length'] if tab['saved_length'] is not None else '',
            file_hash.hex() if file_hash and any(file_hash) else '',
            _label(ENCODINGS, tab['encoding']),
            _label(LINE_ENDINGS, tab['line_ending']),
            tab['selection_start'],
            tab['selection_end'],
            tab['word_wrap'],
            tab['right_to_left'],
            tab['show_unicode'],
            tab['options'].hex(),
            position,
            'Yes' if active is True else ('No' if active is False else ''),
            _crc_text(tab['crc_ok'], chunks),
            '; '.join(state_crc),
            tab_id,
            user_from_path(relative),
            relative,
        ))
    data_headers = (
        ('Unsaved Changes Started', 'datetime'),
        'Tab Kind',
        'File Path',
        'Stored Text',
        'Text With Unsaved Edits Applied',
        'Unsaved Edit Count',
        'Unsaved Flag (as stored)',
        'Saved File Size (bytes, as stored)',
        'Saved File SHA-256 (as stored)',
        'Encoding',
        'Line Ending',
        'Selection Start',
        'Selection End',
        'Word Wrap (as stored)',
        'Right To Left (as stored)',
        'Show Unicode (as stored)',
        'More Options (as stored)',
        'Window Tab Position',
        'Active Tab',
        'CRC-32 Check',
        'State Files',
        'Tab ID',
        'User',
        'Source File',
    )
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsNotepadWindows(context):
    label = 'Windows Notepad Windows'
    files = [(p, r) for p, r in _files(context) if _folder_kind(r) == 'windowstate']
    parsed = []
    for path, relative in files:
        match = _STATE_NAME.match(os.path.basename(relative))
        if not match:
            continue
        data = _read(path)
        if not data:
            logfunc(f'{label}: {relative} is empty')
            continue
        try:
            window = parse_window(data)
        except NotepadError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        parsed.append((path, relative, match.group('id'), window))
    highest = {}
    for _path, relative, window_id, window in parsed:
        key = (os.path.dirname(relative), window_id.lower())
        highest[key] = max(highest.get(key, -1), window['sequence'])
    data_list = []
    sources = []
    for path, _staged_relative, window_id, window in parsed:
        relative = context.get_relative_path(path)
        sources.append(path)
        key = (os.path.dirname(relative), window_id.lower())
        tabs = window['tabs']
        active = tabs[window['active']] if window['active'] < len(tabs) else ''
        data_list.append((
            window['sequence'],
            'Yes' if window['sequence'] == highest[key] else 'No',
            len(tabs),
            '\n'.join(tabs),
            window['active'],
            active,
            f'{window["top_left"][0]}, {window["top_left"][1]}',
            f'{window["bottom_right"][0]}, {window["bottom_right"][1]}',
            f'{window["size"][0]} x {window["size"][1]}',
            'pass' if window['crc_ok'] else 'FAIL',
            window['slack'],
            window_id,
            user_from_path(relative),
            relative,
        ))
    data_headers = (
        'Sequence Number',
        'Current File',
        'Tab Count',
        'Tab IDs In Order',
        'Active Tab Index',
        'Active Tab ID',
        'Top Left (x, y)',
        'Bottom Right (x, y)',
        'Window Size',
        'CRC-32 Check',
        'Bytes After CRC',
        'Window ID',
        'User',
        'Source File',
    )
    return data_headers, data_list, '\n'.join(sources)


# What Notepad-State-Library says each setting holds, by value name (README.md lines 311 to
# 347, commit ce53f9d6). Names it lists without a description are left out.
_SETTING_MEANINGS = {
    'AutoCorrect': ('0 = Off / 1 = On', 311),
    'FindMatchCase': ('0 = Off / 1 = On; default 0', 312),
    'FindString': ('the last string searched with Find (free text)', 313),
    'FindWrapAround': ('0 = Off / 1 = On; default 1', 314),
    'FormattingEnabled': ('Markdown formatting enabled', 320),
    'GhostFile': ('0 = open in a new window / 1 = open content from a previous session', 322),
    'OpenFile': ('0 = new tab / 1 = new window', 325),
    'RecentFiles': ('the recent files list, most recently closed file first', 327),
    'RecentFilesEnabled': ('0 = Off / 1 = On', 328),
    'ReplaceString': ('the last replacement string (free text)', 330),
    'RewriteEnabled': ('0 = Off / 1 = On', 331),
    'SpellCheckState': ('spell check state, as JSON', 333),
    'StatusBarShown': ('0 = Off / 1 = On', 334),
    'Theme': ('0 = System / 1 = Light / 2 = Dark', 338),
    'WordWrap': ('0 = Off / 1 = On', 347),
}

_USER_TEXT = {'FindString', 'ReplaceString'}


@artifact_processor
def windowsNotepadSettings(context):
    data_headers = (
        ('Value Written', 'datetime'),
        'Setting',
        'Value',
        'Free Text (Find or Replace)',
        'Documented Meaning',
        'Type',
        'Key',
        ('Key Last Written', 'datetime'),
        'User',
        'Source File',
    )
    label = 'Windows Notepad Settings'
    data_list = []
    sources = []
    for path, relative, _package, user in package_hives(context, 'Microsoft.WindowsNotepad'):
        rows = []
        try:
            reg = open_settings(path, context)
            for key_path, key, key_written in keys(reg):
                for name, setting in settings(key).items():
                    if setting.error:
                        logfunc(f'{label}: {relative}: {key_path}\\{name} not decoded, '
                                f'reported as stored: {setting.error}')
                    meaning = _SETTING_MEANINGS.get(name)
                    rows.append((
                        setting.written,
                        name,
                        setting.text(),
                        'Yes' if name in _USER_TEXT else '',
                        f'{meaning[0]} (Notepad-State-Library README.md line {meaning[1]})'
                        if meaning else '',
                        setting.type_name,
                        key_path,
                        key_written,
                        user,
                        relative,
                    ))
        except HIVE_ERRORS as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        sources.append(path)
        rows.sort(key=lambda r: (r[6].lower(), r[1].lower()))
        data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)
