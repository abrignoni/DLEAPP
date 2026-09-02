__artifacts_v2__ = {
    "keychainGenericPasswords": {
        "name": "Keychain Generic Passwords",
        "description": "Generic password item metadata (creation/mod "
                       "time, label, account, service, comment) from "
                       "each classic keychain file found: login, "
                       "metadata, System. The password itself is never "
                       "decrypted; only whether an encrypted secret is "
                       "present is reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "Reads Apple's classic 'kych' keychain format (the "
                 "AppleDatabase on-disk layout: 16-byte header, schema "
                 "section, per-relation tables, length-prefixed attribute "
                 "values). Only cleartext attribute metadata is read; the "
                 "SSGP secret area is never decrypted, only its presence is "
                 "reported. Every generic-password record's account, service "
                 "and dates were checked against macOS's own "
                 "'security dump-keychain' on the validation image and match "
                 "exactly.",
        "paths": (
            "*/Library/Keychains/*.keychain-db",
            "*/Library/Keychains/System.keychain",
        ),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "dleapp_keychains_bigsur": "macOS Big Sur (Josh Hickman public "
                "test image, thisisdfir), login.keychain-db + "
                "metadata.keychain-db + System.keychain | 18 generic password "
                "items (15 + 1 + 2), account/service/dates confirmed against "
                "security dump-keychain",
        },
    },
    "keychainInternetPasswords": {
        "name": "Keychain Internet Passwords",
        "description": "Internet password item metadata (server, "
                       "protocol, port, path, account) from each "
                       "classic keychain file found: the items Keychain "
                       "Access shows for saved website/FTP/SSH "
                       "credentials.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "Shares the classic-keychain parser with Keychain Generic "
                 "Passwords, which is confirmed against security "
                 "dump-keychain. The validation image held no internet "
                 "password records, so this record type's own attribute "
                 "layout (server, protocol, port, path added after the shared "
                 "attributes) follows Apple's internet-password relation "
                 "schema but was not exercised against real data.",
        "paths": (
            "*/Library/Keychains/*.keychain-db",
            "*/Library/Keychains/System.keychain",
        ),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "dleapp_keychains_bigsur": "macOS Big Sur (Josh Hickman public "
                "test image, thisisdfir), login.keychain-db + "
                "metadata.keychain-db + System.keychain | 0 internet password "
                "items (none present; security dump-keychain reports none "
                "either). Attribute layout confirmed present in schema, "
                "record contents not exercised",
        },
    },
    "keychainLocalItems": {
        "name": "Keychain Local Items (keychain-2.db)",
        "description": "Generic passwords, internet passwords, "
                       "certificates and keys from the modern per-user "
                       "'local items' keychain at "
                       "Library/Keychains/<UUID>/keychain-2.db, a plain "
                       "SQLite database distinct from the classic "
                       "keychain format. Hashed account/service/label "
                       "values are checked against a SHA-1 dictionary "
                       "built from other evidence recovered in the same "
                       "run.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "acct/svce/labl are reported as-is: plaintext when SQLite "
                 "stored them as TEXT, or as a hex value flagged 'hashed' "
                 "when stored as BLOB. A 'Resolved (SHA-1 Dictionary Match)' "
                 "column shows the recovered plaintext when a hashed field's "
                 "SHA-1 matches a value seen elsewhere in the same extraction "
                 "(an access-group name in this file, or a plaintext value "
                 "already recovered from a classic keychain). This is a "
                 "known-value lookup, not decryption or a hash crack: it can "
                 "only resolve a value that already appears in plaintext "
                 "somewhere in the case. The 'data' column (the protected "
                 "secret) is never decrypted, only its size is reported. The "
                 "classic keychain files are matched too, purely as a source "
                 "of plaintext candidates for the dictionary; only "
                 "keychain-2.db rows are reported here.",
        "paths": (
            "*/Library/Keychains/*/keychain-2.db",
            "*/Library/Keychains/*.keychain-db",
            "*/Library/Keychains/System.keychain",
        ),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "dleapp_keychains_bigsur": "macOS Big Sur (Josh Hickman public "
                "test image, thisisdfir), keychain-2.db | 327 items (154 "
                "generic passwords, 147 internet passwords, 2 certificates, "
                "24 keys); 128 rows had a hashed field resolved to plaintext "
                "via the SHA-1 dictionary match",
        },
    },
}

import hashlib
import os
import sqlite3
import struct
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

# ---------------------------------------------------------------------------
# Classic "kych" keychain reader.
#
# Implements Apple's AppleDatabase on-disk format directly, sourced from the
# Security framework (libsecurity_filedb, AppleDatabase.h/.cpp on
# opensource.apple.com) and from Apple's CSSM record-type constants. The
# extracted account/service/date values are validated against macOS's own
# 'security dump-keychain'. No decryption is performed, so no crypto library
# is needed.
# ---------------------------------------------------------------------------

_ATOM = 4                    # AppleDatabase atom size
_DB_HEADER_SIZE = 16         # magic, version, authOffset, schemaOffset
_TABLE_HEADER_SIZE = 28      # size, id, recCount, recOff, idxOff, freeList, recNumCount
_RECORD_HEADER_ATOMS = 6     # size, number, createVer, recordVer, +2 reserved

# CSSM_DL_DB_RECORD_* relation ids (Apple cssmapple.h).
_REC_GENERIC_PASSWORD = 0x80000000
_REC_INTERNET_PASSWORD = 0x80000001

# Attribute order for the generic-password relation. Confirmed field-for-field
# against security dump-keychain on the validation image.
_GENP_SCHEMA = (
    "cdat", "mdat", "desc", "icmt", "crtr", "type", "scrp", "labl",
    "alias", "invi", "nega", "cusi", "prot", "acct", "svce", "gena",
)
# Attribute order for the internet-password relation: the shared prefix through
# acct, then the internet-specific attributes. Follows Apple's schema; not
# exercised against real data (no internet passwords on the validation image).
_INET_SCHEMA = (
    "cdat", "mdat", "desc", "icmt", "crtr", "type", "scrp", "labl",
    "alias", "invi", "nega", "cusi", "prot", "acct", "sdmn", "srvr",
    "ptcl", "atyp", "port", "path",
)

_STRING_ATTRS = {"desc", "icmt", "crtr", "acct", "svce", "labl", "alias",
                 "gena", "sdmn", "srvr", "path"}
_FOURCC_ATTRS = {"ptcl", "atyp"}
_TIME_ATTRS = {"cdat", "mdat"}


class _KeychainFormatError(Exception):
    pass


class _KeychainReader:
    """Read-only reader for Apple's classic 'kych' keychain format. Extracts
    unencrypted attribute metadata only."""

    def __init__(self, path):
        with open(path, "rb") as handle:
            self.buf = handle.read()
        if self.buf[:4] != b"kych":
            raise _KeychainFormatError(f"not a kych keychain: {path!r}")
        self.schema_offset = self._u32(12)
        self.tables = self._read_schema()

    def _u32(self, offset):
        return struct.unpack_from(">I", self.buf, offset)[0]

    def _read_schema(self):
        """Map relation id -> table base offset (absolute in the file)."""
        base = self.schema_offset
        table_count = self._u32(base + _ATOM)
        tables = {}
        for i in range(table_count):
            table_offset = self._u32(base + 2 * _ATOM + _ATOM * i)
            table_base = self.schema_offset + table_offset
            relation_id = self._u32(table_base + _ATOM)
            tables[relation_id] = table_base
        return tables

    def _record_offsets(self, table_base):
        record_number_count = self._u32(table_base + 6 * _ATOM)
        offsets = []
        for i in range(record_number_count):
            record_offset = self._u32(table_base + _TABLE_HEADER_SIZE + _ATOM * i)
            if record_offset:
                offsets.append(table_base + record_offset)
        return offsets

    def _string(self, position):
        length = self._u32(position)
        return self.buf[position + _ATOM:position + _ATOM + length]

    def _fourcc(self, position):
        raw = self.buf[position:position + _ATOM]
        try:
            return raw.decode("ascii").strip("\x00").strip()
        except UnicodeDecodeError:
            return raw.hex()

    def _time(self, position):
        raw = self.buf[position:position + 16].split(b"\x00", 1)[0]
        if not raw:
            return None
        try:
            return datetime.strptime(raw.decode("ascii"),
                                     "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)
        except (ValueError, UnicodeDecodeError):
            return None

    def _records(self, relation_id, schema):
        table_base = self.tables.get(relation_id)
        if table_base is None:
            return
        for record_base in self._record_offsets(table_base):
            record_size = self._u32(record_base)
            item = {}
            for index, name in enumerate(schema):
                raw_offset = self._u32(record_base + _RECORD_HEADER_ATOMS * _ATOM
                                       + _ATOM * index)
                offset = raw_offset & 0xFFFFFFFE     # low bit is a present-flag
                if not offset:
                    item[name] = None
                    continue
                position = record_base + offset
                if name in _TIME_ATTRS:
                    item[name] = self._time(position)
                elif name in _FOURCC_ATTRS:
                    item[name] = self._fourcc(position)
                elif name in _STRING_ATTRS:
                    item[name] = self._string(position)
                else:
                    item[name] = self._u32(position)
            # The record's data area carries the encrypted secret as an 'ssgp'
            # block; report only its presence.
            item["has_secret"] = b"ssgp" in self.buf[record_base:record_base + record_size]
            yield item

    def generic_passwords(self):
        return self._records(_REC_GENERIC_PASSWORD, _GENP_SCHEMA)

    def internet_passwords(self):
        return self._records(_REC_INTERNET_PASSWORD, _INET_SCHEMA)


def _text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    return value or ""


def _classic_keychains(files_found):
    out = []
    for path in files_found:
        name = os.path.basename(path).lower()
        if name.endswith(".keychain-db") or name == "system.keychain":
            out.append(path)
    return out


def _local_items_dbs(files_found):
    return [p for p in files_found if os.path.basename(p) == "keychain-2.db"]


@artifact_processor
def keychainGenericPasswords(context):
    data_headers = (
        ("Created", "datetime"), ("Modified", "datetime"), "Print Name",
        "Account", "Service", "Description", "Comment", "Creator (raw)",
        "Type (raw)", "Invisible", "Negative", "Encrypted Secret Present",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    keychains = _classic_keychains(files_found)

    data_list = []
    read_sources = []
    for path in keychains:
        relative_source = context.get_relative_path(path)
        try:
            reader = _KeychainReader(path)
        except (_KeychainFormatError, struct.error, OSError) as ex:
            logfunc(f"Keychain Generic Passwords: could not parse "
                    f"'{relative_source}': {ex}")
            continue
        rows_here = 0
        for item in reader.generic_passwords():
            data_list.append((
                item.get("cdat"), item.get("mdat"), _text(item.get("labl")),
                _text(item.get("acct")), _text(item.get("svce")),
                _text(item.get("desc")), _text(item.get("icmt")),
                item.get("crtr") if item.get("crtr") is not None else "",
                item.get("type") if item.get("type") is not None else "",
                "Yes" if item.get("invi") else "", "Yes" if item.get("nega") else "",
                "Yes" if item.get("has_secret") else "", relative_source,
            ))
            rows_here += 1
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Keychain Generic Passwords: {len(data_list)} item(s) across "
            f"{len(read_sources)} keychain file(s).")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def keychainInternetPasswords(context):
    data_headers = (
        ("Created", "datetime"), ("Modified", "datetime"), "Print Name",
        "Account", "Server", "Protocol", "Port", "Path", "Auth Type",
        "Security Domain", "Description", "Comment", "Encrypted Secret Present",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    keychains = _classic_keychains(files_found)

    data_list = []
    read_sources = []
    for path in keychains:
        relative_source = context.get_relative_path(path)
        try:
            reader = _KeychainReader(path)
        except (_KeychainFormatError, struct.error, OSError) as ex:
            logfunc(f"Keychain Internet Passwords: could not parse "
                    f"'{relative_source}': {ex}")
            continue
        rows_here = 0
        for item in reader.internet_passwords():
            data_list.append((
                item.get("cdat"), item.get("mdat"), _text(item.get("labl")),
                _text(item.get("acct")), _text(item.get("srvr")),
                item.get("ptcl") or "",
                item.get("port") if item.get("port") is not None else "",
                _text(item.get("path")), item.get("atyp") or "",
                _text(item.get("sdmn")), _text(item.get("desc")),
                _text(item.get("icmt")),
                "Yes" if item.get("has_secret") else "", relative_source,
            ))
            rows_here += 1
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Keychain Internet Passwords: {len(data_list)} item(s) across "
            f"{len(read_sources)} keychain file(s).")
    return data_headers, data_list, "\n".join(read_sources)


# ---------------------------------------------------------------------------
# Local items keychain (keychain-2.db): plain SQLite, no binary parsing.
# ---------------------------------------------------------------------------

_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _mac_abs_s_to_utc(value):
    if not value:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    try:
        from datetime import timedelta
        return _MAC_EPOCH + timedelta(seconds=value)
    except (OverflowError, OSError, ValueError):
        return None


def _sqlite_field(value):
    """TEXT columns come back readable; BLOB columns are the SHA-1-hashed form
    Apple stores for many system items, shown as hex flagged 'hashed'."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return f"{value.hex()} (hashed)"
    return value


def _sha1(text):
    return hashlib.sha1(text.encode("utf-8", "ignore")).digest()


def _build_hash_dictionary(files_found, db_paths):
    """SHA-1(candidate) -> candidate, where every candidate is a value that
    already appears in plaintext somewhere in this same extraction: an access
    group in keychain-2.db, or a value recovered from a classic keychain. No
    external wordlist, so every match is traceable to real evidence in the
    case. This is a known-value lookup, not a hash crack."""
    candidates = {""}
    for path in _classic_keychains(files_found):
        try:
            reader = _KeychainReader(path)
        except (_KeychainFormatError, struct.error, OSError):
            continue
        for item in reader.generic_passwords():
            for key in ("labl", "acct", "svce", "desc", "icmt", "alias"):
                candidates.add(_text(item.get(key)))
        for item in reader.internet_passwords():
            for key in ("labl", "acct", "srvr", "sdmn", "desc", "icmt", "alias"):
                candidates.add(_text(item.get(key)))
    for path in db_paths:
        database = open_sqlite_db_readonly(path)
        if database is None:
            continue
        for table in ("genp", "inet"):
            try:
                rows = database.execute(f"SELECT DISTINCT agrp FROM {table}").fetchall()
            except sqlite3.OperationalError:
                continue
            for (agrp,) in rows:
                if agrp:
                    candidates.add(agrp)
        database.close()
    return {_sha1(c): c for c in candidates}


def _resolve(hash_dict, **fields):
    resolved = []
    for name, value in fields.items():
        if isinstance(value, bytes) and value in hash_dict:
            match = hash_dict[value]
            resolved.append(f"{name}={match!r}" if match else f"{name}=(empty string)")
    return "; ".join(resolved)


_LOCAL_ITEMS_QUERIES = (
    ("Generic Password",
     "SELECT cdat, mdat, labl, acct, svce, agrp, pdmn, length(data) FROM genp"),
    ("Internet Password",
     "SELECT cdat, mdat, labl, acct, srvr, agrp, pdmn, length(data) FROM inet"),
    ("Certificate",
     "SELECT cdat, mdat, labl, NULL, NULL, agrp, pdmn, length(data) FROM cert"),
    ("Key",
     "SELECT cdat, mdat, labl, NULL, NULL, agrp, pdmn, length(data) FROM keys"),
)


@artifact_processor
def keychainLocalItems(context):
    data_headers = (
        "Item Class", ("Created", "datetime"), ("Modified", "datetime"),
        "Label", "Account", "Service/Server", "Resolved (SHA-1 Dictionary Match)",
        "Access Group", "Protection Domain (raw)", "Encrypted Data Size (bytes)",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    db_paths = _local_items_dbs(files_found)
    hash_dict = _build_hash_dictionary(files_found, db_paths)

    data_list = []
    read_sources = []
    for path in db_paths:
        relative_source = context.get_relative_path(path)
        database = open_sqlite_db_readonly(path)
        if database is None:
            continue
        rows_here = 0
        for item_class, query in _LOCAL_ITEMS_QUERIES:
            try:
                rows = database.execute(query).fetchall()
            except sqlite3.OperationalError as ex:
                logfunc(f"Keychain Local Items: '{item_class}' table "
                        f"unavailable in '{relative_source}': {ex}")
                continue
            for cdat, mdat, labl, acct, svce, agrp, pdmn, data_len in rows:
                resolved = _resolve(hash_dict, Label=labl, Account=acct, Service=svce)
                data_list.append((
                    item_class, _mac_abs_s_to_utc(cdat), _mac_abs_s_to_utc(mdat),
                    _sqlite_field(labl), _sqlite_field(acct), _sqlite_field(svce),
                    resolved, agrp or "", pdmn or "",
                    data_len if data_len is not None else "", relative_source,
                ))
                rows_here += 1
        database.close()
        if rows_here:
            read_sources.append(relative_source)

    resolved_count = sum(1 for row in data_list if row[6])
    logfunc(f"Keychain Local Items: {len(data_list)} item(s) across "
            f"{len(read_sources)} keychain-2.db file(s); {resolved_count} "
            f"resolved via the SHA-1 dictionary match.")
    return data_headers, data_list, "\n".join(read_sources)
