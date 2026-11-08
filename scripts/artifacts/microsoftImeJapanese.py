"""Microsoft IME (Japanese) input history on Windows, for DLEAPP.

Two per-user stores the Microsoft IME for Japanese writes as text is converted: JpnIHDS.dat
(AppData\\Roaming\\Microsoft\\InputMethod\\Shared), a binary file of conversion records, and
JpnDdds.dat (AppData\\Local\\Microsoft\\input\\neutral), an MSZIP-compressed XML document
with a word list and a history of converted sentences. Microsoft publishes neither format;
JpnIHDS.dat follows the layout published by 4n6ist (kazamiya), and both were checked
against known data.
"""

__artifacts_v2__ = {
    "microsoftImeJapaneseHistory": {
        "name": "Microsoft IME Japanese Conversion History (JpnIHDS)",
        "description": "Text converted with the Microsoft IME for Japanese, from JpnIHDS.dat: the reading typed, the converted text and its segments, with the time each record was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Japanese IME",
        "notes": "Reads JpnIHDS.dat in AppData\\Roaming\\Microsoft\\InputMethod\\Shared. Microsoft publishes no format for it; the layout is the one published by 4n6ist (kazamiya) as an 010 Editor template and a parser, worked out from observed files (https://github.com/4n6ist/JpnIHDS/blob/e3a249b2b6e492f74309987a26ef83a90a666bfb/JpnIHDS.bt, BSD-2-Clause): a 32-byte file header (a FILETIME, the file size, a count of records and the header size among its fields), then records of a FILETIME, the record size, the record header size and a count of segments, each segment holding its size, the lengths in characters of the reading and of the converted text, then both as UTF-16LE (a converted length of 0 means the segment was kept as typed). This artifact reads it with its own code and walks the records up to the file size in the header; a record that does not fit inside the file, or whose segments run past it, stops the walk and is logged. One row per record. Reading joins the segments' readings; Converted Text joins each segment's converted text, or its reading when it has none; Segments lists each segment as reading, an arrow and the converted text, separated by ' | '. Record Written (UTC) is the record's FILETIME. It is not the time the text was committed: on the known data windows11_arm_japanese_ime_known_20261108 (Microsoft IME, IMJPTIP.DLL 10.0.26100.9711, on Windows 11 ARM64 build 26200, text typed offline with the commit and next keys logged), each record's time was when the next conversion began (within 0.25 s of the first key of the next word) or, for the last one, when the input window closed; a word committed at 20:11:33.7 had the record time 20:12:17.47, after 44 seconds without typing. So the text was committed at or before the Record Written time. The file header's FILETIME (the last write, the input window's close on the known data) and the per-segment value the template leaves unnamed are not shown. The header carries a second count, which 4n6ist's parser names learn records and which was 0 on the known data; records counted there, if any, are walked like the others but were not exercised. On the known data every record walked, the header count and the file size agreed with the walk (11 records), and every Reading and Converted Text matched what was typed, including a five-segment sentence. Records were also written while the text was typed in a program running as a second account on the signed-in account's desktop, and they went into the signed-in account's file, not the second account's. User is the account folder name from the path; User was uniform on the known data. The file is opened read only.",
        "paths": (
            '*/AppData/Roaming/Microsoft/InputMethod/Shared/JpnIHDS.dat',
        ),
        "output_types": "standard",
        "artifact_icon": "type",
        "sample_data": {
            "windows11_arm_japanese_ime_known_20261108": "Windows 11 build 26200 (ARM64), Microsoft IME (Japanese) 10.0.26100.9711 | 11 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
        },
    },
    "microsoftImeJapaneseDdds": {
        "name": "Microsoft IME Japanese Sentence History (JpnDdds)",
        "description": "Sentences converted with the Microsoft IME for Japanese, from the history kept in JpnDdds.dat: the text, its reading and its words, with the time stored for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Japanese IME",
        "notes": "Reads JpnDdds.dat in AppData\\Local\\Microsoft\\input\\neutral. Microsoft publishes no format for it. On the known data it was a 24-byte header holding the size of the uncompressed content, then blocks of a 4-byte length and an MSZIP block (the bytes CK and raw DEFLATE data, the history kept from one block to the next; Microsoft [MS-MCI], https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69), which decompress to an XML document whose root is ddds: a word list with readings, n-gram counts and History, a list of HistorySentence elements, each with a FILETIME attribute t and its words (HRWord, with disp and a reading). This artifact decompresses the blocks with zlib, each block using the output so far as its history, refuses a file whose output length differs from the header's size (logged), and parses the XML with ElementTree. One row per HistorySentence. Text joins the words' disp, Reading joins their readings, Words lists the words separated by ' | '. Recorded (UTC) is t. On the known data windows11_arm_japanese_ime_known_20261108 (Microsoft IME, IMJPTIP.DLL 10.0.26100.9711, on Windows 11 ARM64 build 26200, text typed offline with the commit and next keys logged), t was the first key pressed after the commit, not the commit: two words committed and then left 20 seconds before the next key had t within 0.25 s of that next key, so the commit came at or before the Recorded time. The file appeared only after the Microsoft IME was used; which component writes it was not established. The word list and n-gram counts are not shown: on the known data they held the same words as the history. Each file on the known data was one block; files of several blocks were not exercised. On the known data the 11 sentences matched the 11 records of JpnIHDS.dat and what was typed, and sentences typed in a program running as a second account went into the signed-in account's file. User is the account folder name from the path; User was uniform on the known data. The file is opened read only.",
        "paths": (
            '*/AppData/Local/Microsoft/input/neutral/JpnDdds.dat',
        ),
        "output_types": "standard",
        "artifact_icon": "type",
        "sample_data": {
            "windows11_arm_japanese_ime_known_20261108": "Windows 11 build 26200 (ARM64), Microsoft IME (Japanese) 10.0.26100.9711 | 11 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
        },
    },
}

import struct
import zlib
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path

_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _filetime(value):
    if not value:
        return ''
    try:
        return _EPOCH_1601 + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


class FormatError(ValueError):
    """The bytes do not follow the expected layout."""


def parse_ihds(data):
    """JpnIHDS.dat records as (FILETIME, [(reading, converted)]), and a list of problems."""
    if len(data) < 32:
        raise FormatError('shorter than the 32-byte header')
    _modified, file_size, _u1, _count, header_size = struct.unpack_from('<QIIII', data, 0)
    end = min(file_size, len(data))
    problems = []
    if file_size != len(data):
        problems.append(f'header file size {file_size}, file holds {len(data)} bytes')
    pos, records = header_size, []
    while pos + 16 <= end:
        ftime, rec_size, rec_header, _u2, seg_count = struct.unpack_from('<QHHBB', data, pos)
        if rec_size < rec_header or rec_header < 16 or pos + rec_size > end:
            problems.append(f'record at offset {pos} does not fit (size {rec_size}, header {rec_header})')
            break
        seg_pos, segments = pos + rec_header, []
        for _ in range(seg_count):
            if seg_pos + 8 > pos + rec_size:
                break
            seg_size, in_len, conv_len = struct.unpack_from('<HBB', data, seg_pos)
            text_end = seg_pos + 8 + 2 * (in_len + conv_len)
            if seg_size < 8 or text_end > pos + rec_size:
                break
            reading = data[seg_pos + 8:seg_pos + 8 + 2 * in_len].decode('utf-16-le', 'replace')
            converted = data[seg_pos + 8 + 2 * in_len:text_end].decode('utf-16-le', 'replace')
            segments.append((reading, converted))
            seg_pos += seg_size
        if len(segments) != seg_count:
            problems.append(f'record at offset {pos}: {len(segments)} of {seg_count} segments fit')
            break
        records.append((ftime, segments))
        pos += rec_size
    return records, problems


def ddds_xml(data):
    """The XML bytes of a JpnDdds.dat file."""
    if len(data) < 28:
        raise FormatError('shorter than the header')
    header_size = struct.unpack_from('<H', data, 4)[0]
    expected = struct.unpack_from('<Q', data, 8)[0]
    pos, out = header_size, b''
    while pos + 4 <= len(data):
        block_len = struct.unpack_from('<I', data, pos)[0]
        block = data[pos + 4:pos + 4 + block_len]
        if len(block) != block_len or block[:2] != b'CK':
            raise FormatError(f'no MSZIP block at offset {pos}')
        try:
            inflater = zlib.decompressobj(-15, zdict=out[-32768:]) if out else zlib.decompressobj(-15)
            out += inflater.decompress(block[2:]) + inflater.flush()
        except zlib.error as ex:
            raise FormatError(f'MSZIP block at offset {pos}: {ex}') from ex
        pos += 4 + block_len
    if len(out) != expected:
        raise FormatError(f'decompressed {len(out)} bytes, header says {expected}')
    return out


def parse_ddds(xml_bytes):
    """(FILETIME, [(disp, reading)]) per HistorySentence."""
    root = ElementTree.fromstring(xml_bytes)
    sentences = []
    for sentence in root.iter('HistorySentence'):
        try:
            ftime = int(sentence.get('t', '0'))
        except ValueError:
            ftime = 0
        words = []
        for word in sentence.iter('HRWord'):
            reading = word.find('reading')
            words.append((word.get('disp', ''), reading.get('value', '') if reading is not None else ''))
        sentences.append((ftime, words))
    return sentences


def _read(context, name):
    for found in sorted((str(f) for f in context.get_files_found()), key=context.get_relative_path):
        if found.replace('\\', '/').rsplit('/', 1)[-1] != name:
            continue
        with open(found, 'rb') as handle:
            data = handle.read()
        yield found, context.get_relative_path(found), data


@artifact_processor
def microsoftImeJapaneseHistory(context):
    data_headers = (('Record Written (UTC)', 'datetime'), 'Reading', 'Converted Text', 'Segments', 'User')
    data_list, sources = [], []
    for path, relative, data in _read(context, 'JpnIHDS.dat'):
        try:
            records, problems = parse_ihds(data)
        except FormatError as ex:
            logfunc(f'Microsoft IME Japanese Conversion History: {relative}: {ex}')
            continue
        for problem in problems:
            logfunc(f'Microsoft IME Japanese Conversion History: {relative}: {problem}')
        sources.append(path)
        user = user_from_path(relative)
        for ftime, segments in records:
            data_list.append((_filetime(ftime), ''.join(r for r, _c in segments),
                              ''.join(c or r for r, c in segments),
                              ' | '.join(f'{r} → {c}' if c else r for r, c in segments), user))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def microsoftImeJapaneseDdds(context):
    data_headers = (('Recorded (UTC)', 'datetime'), 'Text', 'Reading', 'Words', 'User')
    data_list, sources = [], []
    for path, relative, data in _read(context, 'JpnDdds.dat'):
        try:
            sentences = parse_ddds(ddds_xml(data))
        except (FormatError, ElementTree.ParseError) as ex:
            logfunc(f'Microsoft IME Japanese Sentence History: {relative}: {ex}')
            continue
        sources.append(path)
        user = user_from_path(relative)
        for ftime, words in sentences:
            data_list.append((_filetime(ftime), ''.join(d for d, _r in words), ''.join(r for _d, r in words),
                              ' | '.join(d for d, _r in words), user))
    return data_headers, data_list, '\n'.join(sources)
