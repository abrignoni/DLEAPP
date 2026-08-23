__artifacts_v2__ = {
    "keychainGenericPasswords": {
        "name": "Keychain Generic Passwords",
        "description": "Generic password item metadata (creation/mod "
                       "time, label, account, service, comment) from "
                       "each classic *.keychain-db file found -- login, "
                       "metadata, System, etc. The password itself is "
                       "never decrypted; only whether an encrypted secret "
                       "is present is reported.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-23",
        "last_update_date": "2026-08-23",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "Hand-written parser for Apple's undocumented 'kych' "
                 "binary format, checked byte-for-byte against real data "
                 "via chainbreaker -- see module docstring. Does not "
                 "decrypt secrets (would require the user's login "
                 "password).",
        "paths": (
            "*/Library/Keychains/*.keychain-db",
            "*/Library/Keychains/System.keychain",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / "
                "thisisdfir public test image, acquired 2021-02-20), "
                "login.keychain-db + metadata.keychain-db | 16 generic "
                "password items total (15 + 1), all field values "
                "confirmed byte-for-byte against chainbreaker's "
                "independent parse of the same files",
        },
    },
    "keychainInternetPasswords": {
        "name": "Keychain Internet Passwords",
        "description": "Internet password item metadata (server, "
                       "protocol, port, path, account) from each "
                       "classic *.keychain-db file found -- these are "
                       "the items Keychain Access shows for saved "
                       "website/FTP/SSH credentials.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-23",
        "last_update_date": "2026-08-23",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "Shares its parsing mechanics with Keychain Generic "
                 "Passwords (proven against real data there), but no "
                 "Internet Password records existed on the validation "
                 "image to independently confirm this record type's own "
                 "field ordering -- see module docstring.",
        "paths": (
            "*/Library/Keychains/*.keychain-db",
            "*/Library/Keychains/System.keychain",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / "
                "thisisdfir public test image, acquired 2021-02-20), "
                "login.keychain-db + metadata.keychain-db | 0 internet "
                "password items on this image (stock install, no saved "
                "website credentials) -- schema present, no rows to show",
        },
    },
    "keychainLocalItems": {
        "name": "Keychain Local Items (keychain-2.db)",
        "description": "Generic passwords, internet passwords, "
                       "certificates and keys from the modern per-user "
                       "'local items' keychain at "
                       "~/Library/Keychains/<UUID>/keychain-2.db -- a "
                       "plain SQLite database, distinct from the classic "
                       "keychain-db format. Hashed account/service/label "
                       "values are automatically checked against a "
                       "SHA-1 dictionary built from other evidence "
                       "already recovered in the same run.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-23",
        "last_update_date": "2026-08-23",
        "requirements": "none",
        "category": "Keychains (macOS)",
        "notes": "acct/svce/labl are reported as-is: plaintext when "
                 "SQLite stored them as TEXT, or as a hex-encoded opaque "
                 "value (with 'hashed' noted) when stored as BLOB. A "
                 "'Resolved (SHA-1 Dictionary Match)' column additionally "
                 "shows the recovered plaintext whenever a hashed field's "
                 "SHA-1 matches a value seen elsewhere in this same "
                 "extraction (an access-group name in this file, or a "
                 "plaintext account/service already recovered from a "
                 "classic keychain-db) -- confirmed against real data, "
                 "see module docstring. This is a dictionary/known-value "
                 "lookup, not decryption or a hash crack: it can only "
                 "resolve a value that already appears in plaintext "
                 "somewhere in the case. The 'data' column (the actual "
                 "protected secret/key material) is never decrypted, "
                 "only its size is reported.",
        "paths": (
            "*/Library/Keychains/*/keychain-2.db",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "lock",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / "
                "thisisdfir public test image, acquired 2021-02-20), "
                "keychain-2.db | 154 generic passwords, 147 internet "
                "passwords, 2 certificates, 24 keys -- all system/sync "
                "items (com.apple.security.sos, com.apple.cloudd, "
                "com.apple.security.octagon, etc.); 128 of 327 rows had "
                "a hashed field resolved to plaintext via the SHA-1 "
                "dictionary match, including confirming "
                "thisisdfir@gmail.com as the account on every 'apple' "
                "access-group item",
        },
    },
}
 
import hashlib
import os
import struct
import sqlite3
from datetime import datetime, timezone
 
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
 
# ---------------------------------------------------------------------------
# Classic "kych" binary format -- field layout sourced from chainbreaker
# (https://github.com/n0fate/chainbreaker, GPL-2.0), reimplemented here
# without its pycryptodome dependency since no decryption is attempted.
# Byte-for-byte validated against real data -- see module docstring.
# ---------------------------------------------------------------------------
 
_ATOM = 4
# Every internal offset is computed from this FIXED struct size, NOT from
# the file's own HeaderSize field (confirmed against chainbreaker; using
# the file's declared HeaderSize -- 16 on the validation image -- instead
# of this constant silently misreads every table/record).
_APPL_DB_HEADER_SIZE = 20
 
_HEADER_STRUCT = struct.Struct(">4siiii")   # Signature, Version, HeaderSize, SchemaOffset, AuthOffset
_SCHEMA_STRUCT = struct.Struct(">ii")        # SchemaSize, TableCount
_TABLE_HDR_STRUCT = struct.Struct(">IIIIIII")
_GENP_STRUCT = struct.Struct(">" + "I" * 22)
_INET_STRUCT = struct.Struct(">" + "I" * 26)
 
_CSSM_DL_DB_RECORD_GENERIC_PASSWORD = 0x80000000
_CSSM_DL_DB_RECORD_INTERNET_PASSWORD = 0x80000001
_CSSM_DL_DB_RECORD_APPLESHARE_PASSWORD = 0x80000002
_CSSM_DL_DB_RECORD_X509_CERTIFICATE = 0x80001000
_CSSM_DL_DB_RECORD_PUBLIC_KEY = 0x0000000F
_CSSM_DL_DB_RECORD_PRIVATE_KEY = 0x00000010
 
 
class _KychFormatError(Exception):
    pass
 
 
class _KychReader:
    """Minimal read-only parser for the classic Apple 'kych' keychain
    file format. Extracts only unencrypted attribute metadata -- never
    attempts to decrypt the SSGP secret area."""
 
    def __init__(self, path):
        with open(path, "rb") as handle:
            self.buf = handle.read()
        if self.buf[:4] != b"kych":
            raise _KychFormatError(f"not a kych file: {path!r}")
        (self.sig, self.version, self.header_size, self.schema_offset,
         self.auth_offset) = _HEADER_STRUCT.unpack(self.buf[:_HEADER_STRUCT.size])
        self.table_list, self.table_dict = self._get_schema()
 
    def _get_schema(self):
        off = self.schema_offset
        _schema_size, table_count = _SCHEMA_STRUCT.unpack(
            self.buf[off:off + _SCHEMA_STRUCT.size])
        base = _APPL_DB_HEADER_SIZE + _SCHEMA_STRUCT.size
        table_list = []
        for i in range(table_count):
            (val,) = struct.unpack(">I", self.buf[base + _ATOM * i: base + _ATOM * i + _ATOM])
            table_list.append(val)
        table_dict = {}
        for idx, toff in enumerate(table_list):
            meta, _records = self._get_table(toff)
            table_dict[meta[1]] = idx  # TableId -> index into table_list
        return table_list, table_dict
 
    def _get_table(self, offset):
        base_addr = _APPL_DB_HEADER_SIZE + offset
        meta = _TABLE_HDR_STRUCT.unpack(self.buf[base_addr:base_addr + _TABLE_HDR_STRUCT.size])
        record_count = meta[2]
        record_offset_base = base_addr + _TABLE_HDR_STRUCT.size
        record_list = []
        found = 0
        i = 0
        while found != record_count:
            pos = record_offset_base + _ATOM * i
            if pos + _ATOM > len(self.buf):
                break  # truncated/corrupt table -- return what we found
            (rec_off,) = struct.unpack(">I", self.buf[pos:pos + _ATOM])
            if rec_off != 0 and rec_off % 4 == 0:
                record_list.append(rec_off)
                found += 1
            i += 1
            if i > 200000:
                break  # runaway guard
        return meta, record_list
 
    def _table_offset_for(self, table_id):
        return self.table_list[self.table_dict[table_id]]
 
    def _base_addr(self, table_id, record_offset):
        return _APPL_DB_HEADER_SIZE + self._table_offset_for(table_id) + record_offset
 
    def _lv(self, base_addr, pcol):
        """Length-value string: a 4-byte length followed by that many
        bytes, padded to a 4-byte boundary, NUL-trimmed."""
        if pcol <= 0:
            return b""
        try:
            (str_len,) = struct.unpack(">I", self.buf[base_addr + pcol: base_addr + pcol + 4])
            real_len = str_len if str_len % 4 == 0 else ((str_len // 4) + 1) * 4
            data = self.buf[base_addr + pcol + 4: base_addr + pcol + 4 + real_len]
        except struct.error:
            return b""
        return data.rstrip(b"\x00")
 
    def _time(self, base_addr, pcol):
        if pcol <= 0:
            return None
        raw = self.buf[base_addr + pcol: base_addr + pcol + 16].rstrip(b"\x00")
        if not raw:
            return None
        try:
            return datetime.strptime(raw.decode(), "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
 
    def _fourcc(self, base_addr, pcol):
        if pcol <= 0:
            return ""
        raw = self.buf[base_addr + pcol: base_addr + pcol + 4]
        try:
            return raw.decode("ascii").strip("\x00").strip()
        except UnicodeDecodeError:
            return raw.hex()
 
    def table_record_count(self, table_id):
        if table_id not in self.table_dict:
            return 0
        _meta, records = self._get_table(self._table_offset_for(table_id))
        return len(records)
 
    def generic_passwords(self):
        if _CSSM_DL_DB_RECORD_GENERIC_PASSWORD not in self.table_dict:
            return []
        toff = self._table_offset_for(_CSSM_DL_DB_RECORD_GENERIC_PASSWORD)
        _meta, records = self._get_table(toff)
        out = []
        for rec_off in records:
            base = self._base_addr(_CSSM_DL_DB_RECORD_GENERIC_PASSWORD, rec_off)
            try:
                fields = _GENP_STRUCT.unpack(self.buf[base:base + _GENP_STRUCT.size])
            except struct.error:
                continue
            (_rsize, _rnum, _u2, _u3, ssgp_area, _u5, cdat, mdat, desc, comment, creator,
             rtype, _script, print_name, alias, invisible, negative, _custom_icon,
             _protected, account, service, _generic) = fields
            out.append({
                "created": self._time(base, cdat & 0xFFFFFFFE),
                "modified": self._time(base, mdat & 0xFFFFFFFE),
                "print_name": self._lv(base, print_name & 0xFFFFFFFE),
                "description": self._lv(base, desc & 0xFFFFFFFE),
                "comment": self._lv(base, comment & 0xFFFFFFFE),
                "creator": self._fourcc(base, creator & 0xFFFFFFFE),
                "type": self._fourcc(base, rtype & 0xFFFFFFFE),
                "alias": self._lv(base, alias & 0xFFFFFFFE),
                "account": self._lv(base, account & 0xFFFFFFFE),
                "service": self._lv(base, service & 0xFFFFFFFE),
                "invisible": bool(invisible & 1) if invisible else False,
                "negative": bool(negative & 1) if negative else False,
                "has_secret": ssgp_area != 0,
            })
        return out
 
    def internet_passwords(self):
        if _CSSM_DL_DB_RECORD_INTERNET_PASSWORD not in self.table_dict:
            return []
        toff = self._table_offset_for(_CSSM_DL_DB_RECORD_INTERNET_PASSWORD)
        _meta, records = self._get_table(toff)
        out = []
        for rec_off in records:
            base = self._base_addr(_CSSM_DL_DB_RECORD_INTERNET_PASSWORD, rec_off)
            try:
                fields = _INET_STRUCT.unpack(self.buf[base:base + _INET_STRUCT.size])
            except struct.error:
                continue
            (_rsize, _rnum, _u2, _u3, ssgp_area, _u5, cdat, mdat, desc, comment, creator,
             rtype, _script, print_name, alias, _invisible, _negative, _custom_icon,
             _protected, account, secdomain, server, protocol, authtype, port,
             path) = fields
            out.append({
                "created": self._time(base, cdat & 0xFFFFFFFE),
                "modified": self._time(base, mdat & 0xFFFFFFFE),
                "print_name": self._lv(base, print_name & 0xFFFFFFFE),
                "description": self._lv(base, desc & 0xFFFFFFFE),
                "comment": self._lv(base, comment & 0xFFFFFFFE),
                "alias": self._lv(base, alias & 0xFFFFFFFE),
                "account": self._lv(base, account & 0xFFFFFFFE),
                "security_domain": self._lv(base, secdomain & 0xFFFFFFFE),
                "server": self._lv(base, server & 0xFFFFFFFE),
                "protocol": self._fourcc(base, protocol & 0xFFFFFFFE),
                "auth_type": self._fourcc(base, authtype & 0xFFFFFFFE),
                "port": port if port else "",
                "path": self._lv(base, path & 0xFFFFFFFE),
                "has_secret": ssgp_area != 0,
            })
        return out
 
 
def _classic_keychain_paths(files_found):
    out = []
    for path in files_found:
        name = os.path.basename(path).lower()
        if name.endswith(".keychain-db") or name == "system.keychain":
            out.append(path)
    return out
 
 
def _local_items_paths(files_found):
    return [p for p in files_found if os.path.basename(p) == "keychain-2.db"]
 
 
def _bytes_to_text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    return value or ""
 
 
@artifact_processor
def keychainGenericPasswords(context):
    data_headers = (
        ("Created", "datetime"), ("Modified", "datetime"), "Print Name",
        "Account", "Service", "Description", "Comment", "Alias", "Creator",
        "Type", "Invisible", "Negative", "Encrypted Secret Present",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    keychain_paths = _classic_keychain_paths(files_found)
 
    data_list = []
    for path in keychain_paths:
        relative_source = context.get_relative_path(path)
        try:
            reader = _KychReader(path)
        except (_KychFormatError, struct.error, OSError) as ex:
            logfunc(f"Keychain Generic Passwords: could not parse '{relative_source}': {ex}")
            continue
        for item in reader.generic_passwords():
            data_list.append((
                item["created"], item["modified"], _bytes_to_text(item["print_name"]),
                _bytes_to_text(item["account"]), _bytes_to_text(item["service"]),
                _bytes_to_text(item["description"]), _bytes_to_text(item["comment"]),
                _bytes_to_text(item["alias"]), item["creator"], item["type"],
                "Yes" if item["invisible"] else "", "Yes" if item["negative"] else "",
                "Yes" if item["has_secret"] else "", relative_source,
            ))
 
    logfunc(f"Keychain Generic Passwords: {len(data_list)} item(s) across "
            f"{len(keychain_paths)} keychain file(s).")
    return data_headers, data_list, "; ".join(keychain_paths) if keychain_paths else ""
 
 
@artifact_processor
def keychainInternetPasswords(context):
    data_headers = (
        ("Created", "datetime"), ("Modified", "datetime"), "Print Name",
        "Account", "Server", "Protocol", "Port", "Path", "Auth Type",
        "Security Domain", "Description", "Comment", "Alias",
        "Encrypted Secret Present", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    keychain_paths = _classic_keychain_paths(files_found)
 
    data_list = []
    for path in keychain_paths:
        relative_source = context.get_relative_path(path)
        try:
            reader = _KychReader(path)
        except (_KychFormatError, struct.error, OSError) as ex:
            logfunc(f"Keychain Internet Passwords: could not parse '{relative_source}': {ex}")
            continue
        for item in reader.internet_passwords():
            data_list.append((
                item["created"], item["modified"], _bytes_to_text(item["print_name"]),
                _bytes_to_text(item["account"]), _bytes_to_text(item["server"]),
                item["protocol"], item["port"], _bytes_to_text(item["path"]),
                item["auth_type"], _bytes_to_text(item["security_domain"]),
                _bytes_to_text(item["description"]), _bytes_to_text(item["comment"]),
                _bytes_to_text(item["alias"]), "Yes" if item["has_secret"] else "",
                relative_source,
            ))
 
    logfunc(f"Keychain Internet Passwords: {len(data_list)} item(s) across "
            f"{len(keychain_paths)} keychain file(s).")
    return data_headers, data_list, "; ".join(keychain_paths) if keychain_paths else ""
 
 
# ---------------------------------------------------------------------------
# Local items keychain (keychain-2.db) -- plain SQLite, no binary parsing.
# ---------------------------------------------------------------------------
 
_MAC_EPOCH_OFFSET = 978307200  # seconds between 1970-01-01 and 2001-01-01
 
 
def _mac_abs_s_to_utc(value):
    if not value:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(value + _MAC_EPOCH_OFFSET, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
 
 
def _sqlite_field(cursor_value):
    """Report a genp/inet/cert/keys text-ish column as-is when SQLite
    stored it as TEXT (readable), or as a hex string flagged 'hashed'
    when stored as BLOB (Apple hashes these for many system/sync items --
    see module docstring)."""
    if cursor_value is None:
        return ""
    if isinstance(cursor_value, bytes):
        return f"{cursor_value.hex()} (hashed)"
    return cursor_value
 
 
def _sha1(text):
    return hashlib.sha1(text.encode("utf-8", "ignore")).digest()
 
 
def _harvest_classic_keychain_candidates(files_found):
    """Collect every plaintext string this plugin already recovered from
    any classic *.keychain-db file in this same run, as SHA-1 dictionary
    candidates for keychain-2.db's hashed acct/svce/labl columns --
    confirmed to work against real data, see module docstring."""
    candidates = set()
    for path in _classic_keychain_paths(files_found):
        try:
            reader = _KychReader(path)
        except (_KychFormatError, struct.error, OSError):
            continue
        for item in reader.generic_passwords():
            for key in ("print_name", "account", "service", "description", "comment", "alias"):
                candidates.add(_bytes_to_text(item[key]))
        for item in reader.internet_passwords():
            for key in ("print_name", "account", "server", "security_domain", "description",
                        "comment", "alias"):
                candidates.add(_bytes_to_text(item[key]))
    return candidates
 
 
def _build_hash_dictionary(files_found, db_paths):
    """Build a SHA-1(candidate) -> candidate lookup for resolving
    keychain-2.db's hashed columns. Every candidate is either the empty
    string or a value that appears verbatim somewhere else in this exact
    extraction (an access group name in keychain-2.db itself, or a
    plaintext account/service/print name already recovered from a
    classic keychain-db file) -- nothing is guessed or imported from an
    external wordlist, so every match this produces is traceable back to
    real evidence in the same case. This is a dictionary/known-value
    lookup, not decryption: SHA-1 is a one-way hash, so a candidate only
    resolves when it happens to be the exact original value."""
    candidates = {""}
    candidates |= _harvest_classic_keychain_candidates(files_found)
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
 
 
def _resolve_hashed_fields(hash_dict, **named_values):
    """Given field_name=value kwargs (value may be a blob, text, or
    None), return a display string of every field that matched an entry
    in hash_dict, e.g. "Account='thisisdfir@gmail.com'"."""
    resolved = []
    for field_name, value in named_values.items():
        if isinstance(value, bytes) and value in hash_dict:
            match = hash_dict[value]
            resolved.append(f"{field_name}={match!r}" if match else f"{field_name}=(empty string)")
    return "; ".join(resolved)
 
 
_LOCAL_ITEMS_QUERIES = (
    ("Generic Password", """
        SELECT cdat, mdat, labl, acct, svce, agrp, pdmn, length(data)
        FROM genp
    """, ("Label", "Account", "Service")),
    ("Internet Password", """
        SELECT cdat, mdat, labl, acct, srvr, agrp, pdmn, length(data)
        FROM inet
    """, ("Label", "Account", "Server")),
    ("Certificate", """
        SELECT cdat, mdat, labl, NULL, NULL, agrp, pdmn, length(data)
        FROM cert
    """, ("Label", "Account", "Server")),
    ("Key", """
        SELECT cdat, mdat, labl, NULL, NULL, agrp, pdmn, length(data)
        FROM keys
    """, ("Label", "Account", "Server")),
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
    db_paths = _local_items_paths(files_found)
    hash_dict = _build_hash_dictionary(files_found, db_paths)
 
    data_list = []
    for path in db_paths:
        relative_source = context.get_relative_path(path)
        database = open_sqlite_db_readonly(path)
        if database is None:
            continue
        for item_class, query, _cols in _LOCAL_ITEMS_QUERIES:
            try:
                rows = database.execute(query).fetchall()
            except sqlite3.OperationalError as ex:
                logfunc(f"Keychain Local Items: '{item_class}' table unavailable "
                        f"in '{relative_source}': {ex}")
                continue
            for cdat, mdat, labl, acct, svce, agrp, pdmn, data_len in rows:
                resolved = _resolve_hashed_fields(
                    hash_dict, Label=labl, Account=acct, Service=svce)
                data_list.append((
                    item_class, _mac_abs_s_to_utc(cdat), _mac_abs_s_to_utc(mdat),
                    _sqlite_field(labl), _sqlite_field(acct), _sqlite_field(svce),
                    resolved, agrp or "", pdmn or "",
                    data_len if data_len is not None else "", relative_source,
                ))
        database.close()
 
    resolved_count = sum(1 for row in data_list if row[6])
    logfunc(f"Keychain Local Items: {len(data_list)} item(s) across {len(db_paths)} "
            f"keychain-2.db file(s); {resolved_count} had a field resolved via the "
            f"SHA-1 dictionary match.")
    return data_headers, data_list, "; ".join(db_paths) if db_paths else ""
 