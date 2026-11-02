"""Escrow records of the macOS TrustedPeersHelper database, for DLEAPP.

Ported from iLEAPP's trustedPeers.py (Heather Charpentier), read at iLEAPP
da155d0e0155a7321ae3e278bf6b0dea3e9c2bd4.
"""

__artifacts_v2__ = {
    "macosTrustedPeers": {
        "name": "Trusted Peers (macOS)",
        "description": "Rows of the ZESCROWCLIENTMETADATA table of each user's TrustedPeersHelper.db joined to "
                       "ZESCROWMETADATA, with the device model, name and serial values they store. What relation "
                       "a listed device has to the examined Mac is not established.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Ported from iLEAPP's trustedPeers.py by Heather Charpentier (https://github.com/abrignoni/iLEAPP/blob/da155d0e0155a7321ae3e278bf6b0dea3e9c2bd4/scripts/artifacts/trustedPeers.py), which reads the same tables on iOS. Reads every TrustedPeersHelper.db under each user's ~/Library/Keychains/<UUID>/ folder (a defaultContext database and, on some images, an empty-named context beside it), one row per distinct combination of the columns shown in ZESCROWCLIENTMETADATA joined to its ZESCROWMETADATA row, with the database's write-ahead log applied. Secure Backup Metadata Timestamp is ZSECUREBACKUPMETADATATIMESTAMP read as seconds since 2001-01-01 UTC, as the iLEAPP module reads it; read that way the tested values fall from 2020 to 2025, inside each image's period of use. Device Model, Device Model Version, Device Name, Secure Backup Numeric Passphrase Length, Device Color and Device Enclosure Color are ZDEVICEMODEL, ZDEVICEMODELVERSION, ZDEVICENAME, ZSECUREBACKUPNUMERICPASSPHRASELENGTH, ZDEVICECOLOR and ZDEVICEENCLOSURECOLOR as stored, and Serial Number is the ZSERIAL of the joined ZESCROWMETADATA row. Peer OS Version and Peer Model Name are the strings that follow OSVersion and ModelName among the DER-encoded strings of ZPEERINFO, as in the iLEAPP module. No Apple documentation of these columns is cited here; the headers repeat the stored names, and what each value means beyond its name is not established. On the tested images Peer OS Version and Peer Model Name held no value on any row of evidencelocker_macos14 and mvs2026_macbookpro_macos15, whose ZPEERINFO is empty. ZPEERINFO's SerialNumber held no value on any tested row and its ComputerName equalled Device Name on every row where it held one, so neither is shown. User held one value on every row of each image. Source File names the database each row came from; a copy under System/Volumes/Data/ with the same database and write-ahead log is read once, and a row held by more than one copy lists each file. Not read: the ZPEER, ZMACHINE and other tables of the same database.",
        "paths": ('*/Library/Keychains/*/*TrustedPeersHelper.db*',),
        "output_types": "standard",
        "artifact_icon": "circle-check",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 5 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
        },
    }
}

import os

from scripts.ilapfuncs import (artifact_processor, convert_cocoa_core_data_ts_to_utc, does_column_exist_in_db,
                               does_table_exist_in_db, get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'Trusted Peers (macOS)'
_PEER_INFO_KEYS = ('OSVersion', 'ModelName')


def _read_der_length(data, offset):
    if offset >= len(data):
        return None, offset
    length = data[offset]
    offset += 1
    if length < 0x80:
        return length, offset
    length_bytes = length & 0x7f
    if length_bytes == 0 or offset + length_bytes > len(data):
        return None, offset
    return int.from_bytes(data[offset:offset + length_bytes], 'big'), offset + length_bytes


def _read_der_strings(data, start=0, end=None):
    """The UTF8String, PrintableString, IA5String and VisibleString values of a DER encoding, in order."""
    end = len(data) if end is None else end
    offset = start
    strings = []
    while offset < end:
        if offset + 2 > end:
            break
        tag = data[offset]
        offset += 1
        length, offset = _read_der_length(data, offset)
        if length is None or offset + length > end:
            break
        value = data[offset:offset + length]
        if tag in (0x0c, 0x13, 0x16, 0x1a):
            strings.append(value.decode('utf-8', errors='ignore'))
        elif tag & 0x20:
            strings.extend(_read_der_strings(data, offset, offset + length))
        offset += length
    return strings


def _peer_info_values(peer_info):
    """The value that follows each of _PEER_INFO_KEYS among the strings of ZPEERINFO."""
    values = {key: '' for key in _PEER_INFO_KEYS}
    if not peer_info:
        return values
    strings = _read_der_strings(bytes(peer_info))
    for index, item in enumerate(strings[:-1]):
        if item in values:
            values[item] = strings[index + 1]
    return values


def _column(path, table, column, alias):
    return f'{alias}.{column}' if does_column_exist_in_db(path, table, column) else 'NULL'


@artifact_processor
def macosTrustedPeers(context):
    data_list = []
    read = []
    databases = [p for p in context.get_files_found()
                 if str(p).endswith('TrustedPeersHelper.db') and os.path.isfile(str(p))]
    # One database per trust context (defaultContext beside an empty-named one), so every one is read.
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    for path in sorted(paths):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ZESCROWCLIENTMETADATA'):
            logfunc(f'{_LABEL}: {relative} has no ZESCROWCLIENTMETADATA table; no rows reported')
            continue
        query = f'''
            SELECT DISTINCT client.ZSECUREBACKUPMETADATATIMESTAMP, client.ZDEVICEMODEL, client.ZDEVICEMODELVERSION,
                   client.ZDEVICENAME, metadata.ZSERIAL, client.ZSECUREBACKUPNUMERICPASSPHRASELENGTH,
                   {_column(path, 'ZESCROWCLIENTMETADATA', 'ZDEVICECOLOR', 'client')},
                   {_column(path, 'ZESCROWCLIENTMETADATA', 'ZDEVICEENCLOSURECOLOR', 'client')},
                   {_column(path, 'ZESCROWMETADATA', 'ZPEERINFO', 'metadata')}
            FROM ZESCROWCLIENTMETADATA AS client
            LEFT JOIN ZESCROWMETADATA AS metadata ON client.ZESCROWMETADATA = metadata.Z_PK
            ORDER BY client.ZSECUREBACKUPMETADATATIMESTAMP'''
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(path, query):
            peer = _peer_info_values(row[8])
            timestamp = convert_cocoa_core_data_ts_to_utc(row[0]) if row[0] is not None else ''
            data_list.append((timestamp,) + tuple('' if value is None else value for value in row[1:8])
                             + (peer['OSVersion'], peer['ModelName'], user, relative))
    data_headers = (('Secure Backup Metadata Timestamp', 'datetime'), 'Device Model', 'Device Model Version',
                    'Device Name', 'Serial Number', 'Secure Backup Numeric Passphrase Length', 'Device Color',
                    'Device Enclosure Color', 'Peer OS Version', 'Peer Model Name', 'User', 'Source File')
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
