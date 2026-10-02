"""OneDrive client log records for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the OneDrive client's own log files under AppData\\Local\\Microsoft\\OneDrive\\logs on
Windows and Library/Logs/OneDrive on macOS with scripts/onedrive_odl.py, one row per record
whose parameters hold text, and decodes obfuscated words with the general.keystore of the
file's folder or the user's ObfuscationStringMap.txt.
"""

import os
import zlib
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.onedrive_odl import (LOG_EXTENSIONS, OdlFile, decode_text, logs_root, param_texts,
                                  read_keystore, read_string_map, string_map)
from scripts.windows_registry import user_from_path

__artifacts_v2__ = {
    "oneDriveLogs": {
        "name": "OneDrive Logs",
        "description": "Records from the OneDrive sync client's own log files that hold text in "
                       "their parameters: each record's time, the code file and function it names, "
                       "and its parameter text as stored and with obfuscated words decoded where a "
                       "keystore or string map allows.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "PyCryptodome",
        "category": "OneDrive (Desktop)",
        "notes": "Reads the OneDrive sync client's own logs, the .odl, .odlgz, .odlsent and .aodl "
                 "files under AppData\\Local\\Microsoft\\OneDrive\\logs on Windows or "
                 "Library/Logs/OneDrive on macOS, the two locations Khatri gives ('Reading "
                 "OneDrive Logs', below), and their subfolders, with scripts/onedrive_odl.py. It "
                 "follows Yogesh Khatri's description of the format ('Reading OneDrive Logs', "
                 "https://www.swiftforensics.com/2022/02/reading-onedrive-logs.html, and 'Reading "
                 "OneDrive Logs Part 2', "
                 "https://www.swiftforensics.com/2022/11/reading-onedrive-logs-part-2.html) and "
                 "his MIT-licensed reader odl.py, whose lines are cited below at commit "
                 "9ad135ecf56cd2086256cf8440b98b5eaa50c0ab "
                 "(https://github.com/ydkhatri/OneDrive/blob/9ad135ecf56cd2086256cf8440b98b5eaa50c0ab/odl.py); "
                 "no code is copied from it. A file is a 256-byte header (odl.py L99-L108) "
                 "followed by records, as they are or as one gzip stream (odl.py L472-L485). Each "
                 "record carries a timestamp and the length of its data (odl.py L74-L97), and the "
                 "data holds a code file name, a function name and then the record's parameters "
                 "(odl.py L407-L413). One row is reported for each record whose parameters hold "
                 "text: 101,699 of the 245,173 records in the 290 log files read on the four tested "
                 "images. The run log gives each file's format version, its record count and how "
                 "many of its records held text, and says when a file's records stop before its "
                 "end, when its last bytes are zeros (two .aodl files: the last 1,454 bytes of one "
                 "on szechuan_win10 and the last 64,366 of the 129,947 bytes of one on "
                 "pc_mus_001_win11) or when its gzip stream ends early. A file that does not begin "
                 "with an OneDrive log header is logged as not read and gives no rows: one .aodl "
                 "file on lonewolf_win10 is 61,521 bytes of zeros as staged. The Sleuth Kit "
                 "4.15.0's icat returned the same bytes as the staged copies of that file and of "
                 "the pc_mus_001_win11 one (SHA-256 compared). All 290 files read are format "
                 "version 2; version 3 "
                 "files are read as odl.py reads them, skipping each record's context block "
                 "(odl.py L372-L404), and do not occur on the tested images. The macOS location is "
                 "read the same way but is not exercised by the tested images: "
                 "dleapp_macos_bigsur, the tested macOS image, holds no OneDrive logs. Time (UTC) "
                 "is the record's timestamp read as milliseconds since 1970 (odl.py L62-L68), "
                 "taken as UTC. On 247 of the 289 tested log files holding timed records, the last "
                 "record's time was within a minute of the file's NTFS modified time, on machines "
                 "whose registry sets Pacific time (af_case2_win10, szechuan_win10) or Eastern "
                 "time (lonewolf_win10, pc_mus_001_win11); 40 files were modified later than their "
                 "last record, 15 of them an hour later to within a minute (all SyncEngine logs on "
                 "lonewolf_win10), and on two files, the two whose last bytes are zeros, the last "
                 "record is after the modified time, by ten minutes on szechuan_win10 and by 6.7 "
                 "minutes on pc_mus_001_win11. Code File and Function are the names the record "
                 "stores. The "
                 "parameters can be of several types whose layout has not been fully worked out "
                 "(Khatri, 'Reading OneDrive Logs'), so only text is read: a 32-bit length "
                 "followed by that many bytes of printable UTF-8 of at least three characters, one "
                 "trailing NUL dropped, the approach of odl.py's extract_strings (odl.py "
                 "L276-L299), which reads ASCII only. Shorter text is not read: on the tested "
                 "images two-character candidates included pairs such as *_ and $_ in timer "
                 "records (TimerQueue::InsertWithTimeout), while all 56 distinct three-character "
                 "values were readable text such as GET, url, x64 or a file extension. Numbers are "
                 "not reported. Parameters joins a record's text values with ' | ' after decoding, "
                 "and Parameters (as stored) joins them as they are in the file; the client itself "
                 "wrote one value holding ' | ', QuotaAllowanceChange | QuotaStateChange, on 22 "
                 "rows on pc_mus_001_win11. Words in the text, split on the separators odl.py uses "
                 "(odl.py L233-L274), can be obfuscated. Newer clients encrypt each word with AES "
                 "in CBC mode with an IV of zeros under the key in general.keystore (odl.py "
                 "L141-L198), read here from the log file's folder or, when the folder has none, "
                 "from its EncryptionKeyStoreCopy subfolder (odl.py L553-L560), which no tested "
                 "image has; both keystores on pc_mus_001_win11 are version 1 JSON whose key "
                 "decodes to 32 bytes. A word of at least 22 characters is decrypted when it "
                 "decodes as base64 with '_' and '-' in place of '/' and '+', to whole cipher "
                 "blocks with valid padding and printable text, read as UTF-16LE and then as "
                 "UTF-32LE, the two plain text encodings odl.py decodes (odl.py L176-L180, L192), "
                 "where odl.py picks one per keystore from its key text; all 27,385 words "
                 "decrypted on the tested images are UTF-16LE. A word holding plus signs that does "
                 "not decrypt whole has each part between them decrypted where the part decrypts: "
                 "on pc_mus_001_win11, 77 words are stored as 101+ and an encrypted part that "
                 "decrypts to LM, which odl.py keeps as stored. Older clients replace words with "
                 "tokens listed in ObfuscationStringMap.txt (odl.py L200-L231), usually one file "
                 "used for all of a user's log folders (odl.py L26-L33), and the first entry for a "
                 "token is used, as odl.py does. Khatri notes that a token listed more than once "
                 "cannot always be resolved (Part 2); Uncertain Words counts the words replaced "
                 "from a token the map lists with more than one text, on 1,215 rows on "
                 "lonewolf_win10, whose map lists 5 of its 777 tokens that way. Words Decoded "
                 "counts every word replaced, and any other word is kept as stored. Words were "
                 "decoded on 4,628 rows on lonewolf_win10 (string map) and 7,416 on "
                 "pc_mus_001_win11 (keystores). On both, every decoded path named a file or folder "
                 "present on the image (17 and 7 distinct paths), apart from source code paths "
                 "under C:\\dbs ending in .cpp and files in the OneDriveTemp folder with a .temp "
                 "extension. af_case2_win10 and szechuan_win10 hold neither a keystore nor a "
                 "string map, and 400 and 603 of their rows keep words that lonewolf_win10's map "
                 "lists as tokens; so do 40 rows on pc_mus_001_win11, which holds no string map. "
                 "Words Decoded is 0 on every row of af_case2_win10 and szechuan_win10, and "
                 "Parameters is the same as Parameters (as stored) on every row of those two "
                 "images. Uncertain Words is 0 on every row outside lonewolf_win10. Compared "
                 "record by record with odl.py on all 245,173 records of the tested images, the "
                 "times, code files and functions agreed on every record and the parameter text on "
                 "235,744. The others differ because odl.py reads three-character text only when "
                 "the byte after it happens to be printable, and removes trailing line feeds and "
                 "then trailing carriage returns, where this artifact reads all such text and "
                 "keeps line breaks as stored (8,224 records differ only by three-character text, "
                 "573 only by line breaks, 247 by both); because odl.py also returns runs of four "
                 "or five printable bytes whose preceding 32-bit length does not match them (310 "
                 "runs on 302 records); because odl.py reads ASCII only and splits a value holding "
                 "curly quotes, which is read whole here (6 records); and because of the 77 words "
                 "holding plus signs above (77 records). Record is the record's position in its "
                 "file, counting from 1. Log File is the file's name and Log Folder its folder "
                 "within the logs folder, such as Personal, Common or ListSync/Business1. OneDrive "
                 "Version is the client version in the file's header (odl.py L99-L108), as stored. "
                 "User is the profile folder the file sits under. User holds one value on every "
                 "row of af_case2_win10, lonewolf_win10 and pc_mus_001_win11, whose logs sit under "
                 "one profile each, and four values on szechuan_win10. Log Folder is Personal on "
                 "every row of szechuan_win10. Not read: the other files in the logs folders, such "
                 "as SyncDiagnostics.log, the .loggz and .etl files, the .ini and .json files and "
                 "the SQLite .db, .otc and .session files, and OneDrive's settings and sync "
                 "databases outside the logs folders.",
        "paths": ('*/AppData/Local/Microsoft/OneDrive/logs/*', '*/Library/Logs/OneDrive/*'),
        "output_types": ["standard"],
        "artifact_icon": "cloud",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 5959 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 29864 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 52152 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 13724 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _time(milliseconds):
    try:
        return _EPOCH + timedelta(milliseconds=milliseconds) if milliseconds else ''
    except OverflowError:
        return ''


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _decoders(context, files):
    """({folder: keystore key}, {logs root: (string map, repeated tokens)}) from the files found.

    A folder's own general.keystore is used before one in its EncryptionKeyStoreCopy
    subfolder, the order odl.py L553-L560 follows.
    """
    own, copies, entries = {}, {}, {}
    for path in files:
        name = os.path.basename(path).lower()
        relative = context.get_relative_path(path)
        try:
            if name == 'general.keystore':
                folder = os.path.dirname(path)
                keys = own
                if os.path.basename(folder).lower() == 'encryptionkeystorecopy':
                    folder, keys = os.path.dirname(folder), copies
                key = read_keystore(_read(path))
                if key is None:
                    logfunc(f'OneDrive Logs: {relative} holds no version 1 key; its words are '
                            f'not decrypted')
                keys[folder] = key
            elif name == 'obfuscationstringmap.txt':
                entries.setdefault(logs_root(path), []).append(read_string_map(_read(path)))
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            logfunc(f'OneDrive Logs: could not read {relative}: {exc}')
    return {**copies, **own}, {root: string_map(lists) for root, lists in entries.items()}


@artifact_processor
def oneDriveLogs(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Code File', 'Function', 'Parameters',
                    'Parameters (as stored)', 'Words Decoded', 'Uncertain Words', 'Record',
                    'Log File', 'Log Folder', 'OneDrive Version', 'User')
    data_list = []
    sources = []
    files = sorted({str(f) for f in context.get_files_found() if os.path.isfile(str(f))})
    keys, maps = _decoders(context, files)
    for path in files:
        if not path.lower().endswith(LOG_EXTENSIONS):
            continue
        relative = context.get_relative_path(path)
        try:
            log = OdlFile(_read(path))
        except (OSError, ValueError, zlib.error) as exc:
            logfunc(f'OneDrive Logs: {relative} not read: {exc}')
            continue
        sources.append(path)
        key = keys.get(os.path.dirname(path))
        mapping, repeated = maps.get(logs_root(path), ({}, set()))
        folder = os.path.relpath(os.path.dirname(path), logs_root(path)).replace('\\', '/')
        user = user_from_path(relative)
        reported = 0
        for index, record in enumerate(log.records, 1):
            texts = param_texts(record['params'])
            if not texts:
                continue
            decoded = [decode_text(text, key, mapping, repeated) for text in texts]
            data_list.append((_time(record['timestamp']), record['code_file'], record['function'],
                              ' | '.join(text for text, _, _ in decoded), ' | '.join(texts),
                              sum(count for _, count, _ in decoded),
                              sum(count for _, _, count in decoded), index, os.path.basename(path),
                              folder, log.onedrive_version, user))
            reported += 1
        note = ''
        if log.stopped_at is not None:
            note = (f'; reading stopped at byte {log.stopped_at:,} of {log.body_size:,} of its '
                    f'records, where no further record header was found')
        elif log.zero_bytes:
            note = f'; its last {log.zero_bytes:,} bytes are zeros'
        if log.gzip_cut_short:
            note += '; its gzip stream ends before its end marker'
        count = len(log.records)
        logfunc(f'OneDrive Logs: {relative}: format version {log.version}, {count:,} '
                f'record{"" if count == 1 else "s"}, {reported:,} with parameter text{note}')
    return data_headers, data_list, '\n'.join(sources)
