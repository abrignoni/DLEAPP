import re
import sqlite3
import zlib

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               get_sqlite_db_records, convert_cocoa_core_data_ts_to_utc,
                               logfunc)

# Apple Notes on macOS stores each note's body as a zlib/gzip-compressed
# protobuf in ZICNOTEDATA.ZDATA. The decompression and the manual protobuf walk
# below are adapted from the iLEAPP notes module, itself derived from Yogesh
# Khatri's mac_apt Notes plugin (https://github.com/ydkhatri/mac_apt), MIT
# licensed. Password-protected note bodies are not decoded.

__artifacts_v2__ = {
    "notes": {
        "name": "Notes",
        "description": "Apple Notes from NoteStore.sqlite: the note title, "
                       "snippet and decoded body text, its folder and account, "
                       "and its creation and modification dates.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "Notes (macOS)",
        "notes": "Every NoteStore.sqlite found is parsed, tagged by Source "
                 "File. The body text is zlib-decompressed from ZICNOTEDATA and "
                 "the readable text is walked out of the note protobuf. "
                 "Password-protected notes (Password Protected = Yes) are not "
                 "decoded; their Note Contents is blank, as is a note whose "
                 "ZICNOTEDATA row carries no body blob (ZDATA null). Times are "
                 "Mac Absolute Time (Core Data), seconds since 2001-01-01 UTC, "
                 "rendered in UTC; the -wal sidecar is read alongside the "
                 "database. Within each NoteStore.sqlite, rows are listed by "
                 "creation date, then by the note's Z_PK, then by the "
                 "ZICNOTEDATA row's Z_PK. The decompression "
                 "and protobuf walk are adapted "
                 "from the iLEAPP notes module, derived from Yogesh Khatri's "
                 "mac_apt Notes plugin (https://github.com/ydkhatri/mac_apt), "
                 "MIT. Needs Initial Fetch From Cloud (as stored) is "
                 "ZNEEDSINITIALFETCHFROMCLOUD, blank when the store has no such "
                 "column. On a private sample, every row with it set to 1 had no "
                 "title, snippet, body, folder or dates, and the row with 0 had "
                 "all of them. Its meaning is not established here; a "
                 "third-party Notes tool describes such records as CloudKit "
                 "records whose contents were never fetched and which Notes.app "
                 "does not display (iangray001, 'applenotes-mcp NOTES.md', "
                 "https://github.com/iangray001/applenotes-mcp/blob/"
                 "74a2bb8d9e69d9ab254d10bd89830861dbec4011/NOTES.md#L100). "
                 "The decode was verified against a private macOS Notes "
                 "sample; the public test image below holds no notes.",
        "paths": ('*/NoteStore.sqlite*',),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (NoteStore.sqlite present, no notes stored)",
        },
    },
}


def _read_length_field(blob):
    length = 0
    skip = 0
    try:
        data_length = int(blob[0])
        length = data_length & 0x7F
        while data_length > 0x7F:
            skip += 1
            data_length = int(blob[skip])
            length = ((data_length & 0x7F) << (skip * 7)) + length
    except (IndexError, ValueError):
        logfunc('Notes: error reading length field in note data blob')
    skip += 1
    return length, skip


def _get_uncompressed_data(compressed):
    if compressed is None:
        return None
    try:
        return zlib.decompress(compressed, 15 + 32)
    except zlib.error:
        logfunc('Notes: zlib decompression failed')
        return None


def _process_note_body_blob(blob):
    if blob is None:
        return ''
    try:
        pos = 0
        if blob[0:3] != b'\x08\x00\x12':                       # header
            return ''
        pos += 3
        _, skip = _read_length_field(blob[pos:])
        pos += skip
        if blob[pos:pos + 3] != b'\x08\x00\x10':               # header 2
            return ''
        pos += 3
        _, skip = _read_length_field(blob[pos:])
        pos += skip
        if blob[pos] != 0x1A:                                  # text header
            return ''
        pos += 1
        _, skip = _read_length_field(blob[pos:])
        pos += skip
        if blob[pos] != 0x12:                                  # text tag
            return ''
        pos += 1
        length, skip = _read_length_field(blob[pos:])
        pos += skip
        return blob[pos:pos + length].decode('utf-8', 'backslashreplace')
    except (IndexError, ValueError):
        logfunc('Notes: error processing note data blob')
        return ''


def _pick_note_column(source, prefix, default):
    '''The note creation-date and note->account columns have drifted across
    releases (ZACCOUNT2/4/7...), and several same-prefixed columns coexist with
    all but one NULL on note rows. Pick the candidate that is non-null on rows
    that have note data, preferring the highest-suffixed on a tie.'''
    candidates = [row[0] for row in get_sqlite_db_records(
        source,
        "SELECT name FROM pragma_table_info('ZICCLOUDSYNCINGOBJECT') "
        f"WHERE name LIKE '{prefix}%'")
        if re.fullmatch(re.escape(prefix) + r'\d*', row[0])]
    best, best_count, best_suffix = default, 0, -1
    for col in candidates:
        records = list(get_sqlite_db_records(
            source,
            'SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT TabA '
            'INNER JOIN ZICNOTEDATA TabF ON TabF.ZNOTE = TabA.Z_PK '
            f'WHERE TabA.{col} IS NOT NULL'))
        count = records[0][0] if records else 0
        suffix = int(re.sub(r'\D', '', col) or -1)
        if count > best_count or (count == best_count > 0 and suffix > best_suffix):
            best, best_count, best_suffix = col, count, suffix
    return best


def _has_note_column(source, name):
    return bool(list(get_sqlite_db_records(
        source,
        "SELECT name FROM pragma_table_info('ZICCLOUDSYNCINGOBJECT') "
        f"WHERE name = '{name}'")))


def _build_query(creation_col, account_col, fetch_col):
    fetch_expr = f'TabA.{fetch_col}' if fetch_col else 'NULL'
    return f'''
    SELECT
        TabA.{creation_col},
        TabA.ZTITLE1,
        TabA.ZSNIPPET,
        TabB.ZTITLE2,
        TabC.ZNAME,
        TabA.ZMODIFICATIONDATE1,
        CASE TabA.ZISPASSWORDPROTECTED WHEN 0 THEN 'No' WHEN 1 THEN 'Yes' END,
        TabA.ZPASSWORDHINT,
        CASE TabA.ZMARKEDFORDELETION WHEN 0 THEN 'No' WHEN 1 THEN 'Yes' END,
        CASE TabA.ZISPINNED WHEN 0 THEN 'No' WHEN 1 THEN 'Yes' END,
        TabF.ZDATA,
        {fetch_expr}
    FROM ZICCLOUDSYNCINGOBJECT TabA
    LEFT JOIN ZICCLOUDSYNCINGOBJECT TabB ON TabA.ZFOLDER = TabB.Z_PK
    LEFT JOIN ZICCLOUDSYNCINGOBJECT TabC ON TabA.{account_col} = TabC.Z_PK
    INNER JOIN ZICNOTEDATA TabF ON TabF.ZNOTE = TabA.Z_PK
    ORDER BY TabA.{creation_col}, TabA.Z_PK, TabF.Z_PK
    '''


@artifact_processor
def notes(context):
    data_headers = (('Creation Date', 'datetime'), 'Note Title', 'Snippet', 'Note Contents',
                    'Folder', 'Account', ('Last Modified', 'datetime'), 'Password Protected',
                    'Password Hint', 'Marked for Deletion', 'Pinned',
                    'Needs Initial Fetch From Cloud (as stored)', 'Source File')
    data_list = []
    read_sources = []

    for source in [str(f) for f in context.get_files_found() if str(f).endswith('NoteStore.sqlite')]:
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        database.close()
        rows_here = 0
        try:
            query = _build_query(_pick_note_column(source, 'ZCREATIONDATE', 'ZCREATIONDATE1'),
                                 _pick_note_column(source, 'ZACCOUNT', 'ZACCOUNT2'),
                                 'ZNEEDSINITIALFETCHFROMCLOUD'
                                 if _has_note_column(source, 'ZNEEDSINITIALFETCHFROMCLOUD')
                                 else None)
            for row in get_sqlite_db_records(source, query):
                contents = ''
                if row[6] == 'No' and row[10] is not None:
                    contents = _process_note_body_blob(_get_uncompressed_data(row[10]))
                data_list.append((
                    convert_cocoa_core_data_ts_to_utc(row[0]), row[1] or '', row[2] or '',
                    contents, row[3] or '', row[4] or '',
                    convert_cocoa_core_data_ts_to_utc(row[5]), row[6] or '', row[7] or '',
                    row[8] or '', row[9] or '',
                    row[11] if row[11] is not None else '', relative_source))
                rows_here += 1
        except sqlite3.Error as exc:
            logfunc(f'Notes {relative_source}: {exc}')
        if rows_here:
            read_sources.append(relative_source)

    return data_headers, data_list, "\n".join(read_sources)
