"""Ares Galaxy shared library, search history and client settings, for DLEAPP.

Author: @AlexisBrignoni, Claude.

ShareL.dat is decoded with the cipher Ares 2.4.6 uses (helper_library_db.pas); the search history and settings are values under
Software\\Ares in the user's NTUSER.DAT. Field meanings are from the Ares 2.4.6 source cited in the notes.
"""

import os
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key, user_from_path

__artifacts_v2__ = {
    "aresLibrary": {
        "name": "Ares Shared Library",
        "description": "Files in Ares's shared library, read from ShareL.dat: path, size, SHA-1, media type and the "
                       "title, artist and other details Ares kept for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Ares",
        "notes": "Line references are to the Ares 2.4.6 source, AresRegular246_082217.zip in https://sourceforge.net/projects/aresgalaxy/files/aresgalaxy/AresRegular246_082217/ (SHA-1 8df4ea53e24b09f1a235fbdd01724ee6e03e1c09); its newest file, const_ares.pas, is dated 2017-08-22 and declares version 2.4.6.3072 (line 34), the version the tested build reports; that the binary was built from this source is not proven. The known data (windows11_arm_ares_known_20261108) is Ares 2.4.6.3072 run on Windows 11 ARM64 with the computer's network cut for the run (a default route came back for part of it; see the known data's README). User is the account folder name taken from the file path. One row per record in ShareL.dat in Ares's Data folder, by default AppData\\Local\\Ares\\Data (ufrmmain.pas line 1632, helper_urls.pas line 83). The file starts with __ARESDB1.04L_; each record is a 47-byte head and a detail block, each scrambled with a fixed 16-bit key (13871 for the head, 13872 for the detail), decoded here with the cipher Ares uses (helper_library_db.pas lines 386 to 420 and 479 to 483). Every record in the file is listed, including a record Ares itself would skip (a file over 256 KB with no entry in PHashIdx.dat, lines 448 to 449), and where a field appears twice the first is shown. SHA-1, Media Type and File Size come from the head (Media Type is Ares's media type number, named from const_ares.pas lines 62 to 69); File Path, Title, Artist, Album, Category, Year, Language, URL and Comment are detail fields 1 to 6 and 8 to 10 (field 7, video information, and field 18, a partial-hash digest, are not shown), and Marked Corrupt is Yes when field 17 is present (lines 496 to 510). Ares lists only files whose extension it shares (helper_share_misc.pas line 169, called at thread_share.pas line 1074). On the known data the shared folder held a .txt file, which is the one row, its SHA-1 matching the file, and a .bin file that is not in ShareL.dat; the published source lists .bin among the extensions Ares shares (helper_mimetypes.pas line 37), so why it was left out is not established. Artist, Album, Category, Year, Language, URL, Comment and Marked Corrupt were empty on the one row of the known data, a text file with no details set, so they are source-verified only. ShareL.dat holds no time. Not read: ShareH.dat, the store of details Ares keeps per SHA-1 when a file's details are edited (helper_library_db.pas lines 555 to 690), which held only its header on the known data; PHashIdx.dat, the partial hashes of files over 256 KB; DHTnodes.dat, a list of DHT nodes. A row records a file in the shared library, not that anyone downloaded it.",
        "paths": ('*/Ares/[Dd]ata/[Ss]hare[Ll].dat',),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "windows11_arm_ares_known_20261108": "Windows 11 build 26200 (ARM64), Ares 2.4.6.3072 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "aresSearchHistory": {
        "name": "Ares Search History",
        "description": "Search text Ares saved from its search fields, under Software\\Ares\\Search.History in the "
                       "user's registry hive.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none (vendored regfprobe)",
        "category": "Ares",
        "notes": "Line references are to the Ares 2.4.6 source, AresRegular246_082217.zip in https://sourceforge.net/projects/aresgalaxy/files/aresgalaxy/AresRegular246_082217/ (SHA-1 8df4ea53e24b09f1a235fbdd01724ee6e03e1c09); its newest file, const_ares.pas, is dated 2017-08-22 and declares version 2.4.6.3072 (line 34), the version the tested build reports; that the binary was built from this source is not proven. The known data (windows11_arm_ares_known_20261108) is Ares 2.4.6.3072 run on Windows 11 ARM64 with the computer's network cut for the run (a default route came back for part of it; see the known data's README). User is the account folder name taken from the file path. One row per value under Software\\Ares\\Search.History in each user's NTUSER.DAT. When a search starts, Ares stores the text of each search field it used as a value name, the hexadecimal of its UTF-8 bytes, in a key named for the media type and the field (helper_search_gui.pas lines 1008 to 1170, called at line 1748 when a search starts). A value is written only when the text is new to that field's drop-down list, compared without case (helper_combos.pas lines 401 to 412), so a repeated search adds no value. Search Text is that name decoded. Media Type is the first part of the key name (gen is All) and Field the second (gen the main search box, tit Title, aut Artist or author, alb Album, dat Date); Field is this artifact's label for the key suffix, and the Key column keeps the stored name. Ares trims a key to 99 values before adding a new one (helper_combos.pas lines 183 to 188), so a key holds at most 100 and its clear-history command deletes the whole Search.History key (helper_search_gui.pas line 1286). The values carry no time; Key Last Written (UTC) is the key's last-written time, the time of the latest change to that key, not of each search. On the known data the search box was set to a test term and Search Now clicked with the computer offline: Ares saved the term under gen.gen, so a row does not show that a search reached the network or returned anything. The known data's NTUSER.DAT is not a full user hive: it was saved from a copy of HKCU\\Software\\Ares, so its Key Last Written (UTC) times are the time of that copy, the same on every row, and the key times were not tested. In a real hive a key's last-written time changes whenever any of its values is written. User held one value on all rows of the known data.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "windows11_arm_ares_known_20261108": "Windows 11 build 26200 (ARM64), Ares 2.4.6.3072 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no user hive holds Software\\Ares)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "aresSettings": {
        "name": "Ares Settings",
        "description": "Ares's nickname, client GUID and shared folder, from Software\\Ares in the user's registry "
                       "hive.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none (vendored regfprobe)",
        "category": "Ares",
        "notes": "Line references are to the Ares 2.4.6 source, AresRegular246_082217.zip in https://sourceforge.net/projects/aresgalaxy/files/aresgalaxy/AresRegular246_082217/ (SHA-1 8df4ea53e24b09f1a235fbdd01724ee6e03e1c09); its newest file, const_ares.pas, is dated 2017-08-22 and declares version 2.4.6.3072 (line 34), the version the tested build reports; that the binary was built from this source is not proven. The known data (windows11_arm_ares_known_20261108) is Ares 2.4.6.3072 run on Windows 11 ARM64 with the computer's network cut for the run (a default route came back for part of it; see the known data's README). User is the account folder name taken from the file path. Rows from values of Software\\Ares in each user's NTUSER.DAT. Nickname is Personal.Nickname and Shared Folder is Download.Folder, both stored as the hexadecimal of their UTF-8 bytes and shown decoded (helper_registry.pas lines 1242 and 1394; ufrm_settings.pas lines 1066, 1082 and 1607); Ares reads only the first 20 characters of the nickname (line 1395). Client GUID is Personal.GUID, 32 hexadecimal characters, shown as the registry string, not decoded from hexadecimal (lines 1371 to 1372). On the known data Shared Folder was the folder the test script set before the first start, and Nickname, which nobody set, held the Windows account name, an underscore and the first six characters of the Client GUID in lower case; the code that writes a default nickname was not found in the published source, so how it was formed is not established. The known data's NTUSER.DAT is not a full user hive: it was saved from a copy of HKCU\\Software\\Ares, so its Key Last Written (UTC) times are the time of that copy, the same on every row, and the key times were not tested. In a real hive a key's last-written time changes whenever any of its values is written. User held one value on all rows.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "windows11_arm_ares_known_20261108": "Windows 11 build 26200 (ARM64), Ares 2.4.6.3072 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no user hive holds Software\\Ares)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
}

_BASE = 'Software\\Ares'
_LIBRARY_MAGIC = b'__ARESDB1.04L_'
# const_ares.pas ARES_MIME_*
_MEDIA = {0: 'Other', 1: 'Audio (MP3)', 2: 'Audio', 3: 'Software', 4: 'Audio', 5: 'Video', 6: 'Document', 7: 'Image'}
# helper_library_db.pas, the str_detail field numbers of a ShareL.dat record
_FIELDS = {1: 'path', 2: 'title', 3: 'artist', 4: 'album', 5: 'category', 6: 'year', 7: 'video', 8: 'language',
           9: 'url', 10: 'comment', 17: 'corrupt'}
_FIELD_NAMES = {'gen': 'Search box', 'tit': 'Title', 'aut': 'Artist or author', 'alb': 'Album', 'dat': 'Date'}


def descramble(data, key):
    """The cipher Ares applies to each part of a ShareL.dat record (helper_library_db.pas): each byte XOR the high
    byte of a 16-bit word that is advanced with the scrambled byte."""
    word, out = key, bytearray()
    for byte in data:
        out.append(byte ^ (word >> 8))
        word = ((byte + word) * 23219 + 36126) & 0xFFFF
    return bytes(out)


def _text(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', 'replace')


def read_library(data):
    """Records of a ShareL.dat as dicts, and the number of bytes left unread when a record is cut short."""
    if not data.startswith(_LIBRARY_MAGIC):
        raise ValueError('not an Ares ShareL.dat')
    records, pos = [], len(_LIBRARY_MAGIC)
    while pos + 47 <= len(data):
        head = descramble(data[pos:pos + 47], 13871)
        pos += 47
        length = struct.unpack_from('<H', head, 45)[0]
        if length == 0:
            continue
        if length > 2048 or pos + length > len(data):
            return records, len(data) - pos + 47
        detail = descramble(data[pos:pos + length], 13872)
        pos += length
        record = {'sha1': head[:20].hex(), 'media': head[20], 'size': struct.unpack_from('<Q', head, 25)[0]}
        at = 0
        while at + 3 <= len(detail):
            kind = detail[at]
            size = struct.unpack_from('<H', detail, at + 1)[0]
            value = detail[at + 3:at + 3 + size]
            at += 3 + size
            if kind in _FIELDS and _FIELDS[kind] not in record:
                record[_FIELDS[kind]] = True if kind == 17 else _text(value)
        records.append(record)
    return records, len(data) - pos


def _hex_text(value):
    """A registry string Ares stores as the hexadecimal of its UTF-8 bytes (bytestr_to_hexstr)."""
    if not isinstance(value, str):
        return ''
    try:
        return _text(bytes.fromhex(value.strip()))
    except ValueError:
        return ''


@artifact_processor
def aresLibrary(context):
    data_headers = ('File Path', ('File Size (bytes)', 'number'), ('SHA-1', 'hash'), 'Media Type', 'Title',
                    'Artist', 'Album', 'Category', 'Year', 'Language', 'URL', 'Comment', 'Marked Corrupt', 'User')
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found()):
        if os.path.basename(path).lower() != 'sharel.dat' or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                records, left = read_library(handle.read())
        except (OSError, ValueError) as exc:
            logfunc(f'Ares Shared Library: {relative} not read ({exc})')
            continue
        if left:
            logfunc(f'Ares Shared Library: {relative} has {left} bytes after its last whole record, not read')
        user = user_from_path(relative)
        for record in records:
            data_list.append((record.get('path', ''), record['size'], record['sha1'],
                              _MEDIA.get(record['media'], str(record['media'])), record.get('title', ''),
                              record.get('artist', ''), record.get('album', ''), record.get('category', ''),
                              record.get('year', ''), record.get('language', ''), record.get('url', ''),
                              record.get('comment', ''), 'Yes' if record.get('corrupt') else '', user))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def aresSearchHistory(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Search Text', 'Media Type', 'Field', 'Key', 'User')
    data_list, sources, problems = [], [], Counter()
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        try:
            history = open_key(open_hive(source, context), _BASE + '\\Search.History')
            if history is None:
                continue
            rows = []
            for key in history.subkeys():
                scope, _, field = key.name().partition('.')
                for value in key.values():
                    text = _hex_text(value.name())
                    if not text and value.name():
                        problems['value names that are not hexadecimal, not read'] += 1
                        continue
                    rows.append((key_written_utc(key), text, 'All' if scope == 'gen' else scope,
                                 _FIELD_NAMES.get(field, field), key.name()))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Ares Search History: could not read {relative}: {exc}')
            continue
        user = user_from_path(relative)
        data_list.extend(row + (user,) for row in rows)
        if rows:
            sources.append(source)
    if problems:
        logfunc('Ares Search History: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def aresSettings(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Setting', 'Value', 'User')
    data_list, sources = [], []
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), _BASE)
            if key is None:
                continue
            values = {value.name().lower(): value.value() for value in key.values()}
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Ares Settings: could not read {relative}: {exc}')
            continue
        written, user = key_written_utc(key), user_from_path(relative)
        rows = []
        for name, label, decode in (('personal.nickname', 'Nickname', True), ('personal.guid', 'Client GUID', False),
                                    ('download.folder', 'Shared Folder', True)):
            value = values.get(name)
            shown = _hex_text(value) if decode else (value if isinstance(value, str) else '')
            if shown:
                rows.append((written, label, shown, user))
        data_list.extend(rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
