"""Shared read-only handling for Threema Desktop databases.

Threema Desktop stores its application data in a SQLCipher 4 database named
``threema.sqlite``.  This module opens it from one of three examiner-supplied
inputs: the profile's local password, from which the database key is recovered by
running the Argon2id key derivation over keystorage.bin (see
``scripts/threema_keystorage.py``); the 64-character hexadecimal database key
directly; or an already-decrypted SQLite copy.  It never writes to the evidence.

Schema and cipher settings were validated against Threema Desktop source at
commit 93a6615c5567f0cf8371619dc1a5e888eed1d0b6.
"""

import atexit
import hashlib
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from scripts import threema_keystorage
from scripts.ilapfuncs import logfunc

_RAW_KEY_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_FILE_ID_RE = re.compile(r"^[0-9a-f]{48}$")
_SQLITE_MAGIC = b"SQLite format 3\x00"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

PAGE_SIZE = 4096
HMAC_ALGORITHM = "sha512"
KDF_ALGORITHM = "sha512"
FILE_CHUNK_SIZE = 1024 * 1024
FILE_TAG_SIZE = 16

CREDENTIAL_FILENAMES = (
    "threema-key.txt",
    "threema_key.txt",
    "threema-db-key.txt",
    "threema_db_key.txt",
)

_decrypted_cache = {}
_explained = set()


def _remove_decrypted_copies():
    """Delete temporary plaintext databases when the process exits."""
    for path in set(_decrypted_cache.values()):
        try:
            os.remove(path)
        except OSError:
            pass


atexit.register(_remove_decrypted_copies)


def timestamp(value):
    """Convert a Unix millisecond timestamp, leaving zero and invalid values blank."""
    if value in (None, "", 0) or isinstance(value, bool):
        return ""
    try:
        seconds, milliseconds = divmod(int(value), 1000)
        return _EPOCH + timedelta(seconds=seconds, milliseconds=milliseconds)
    except (TypeError, ValueError, OverflowError):
        return ""


def blob_hex(value):
    """Render an identifier blob without interpreting its byte order."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


def stored_file_paths(files_found):
    """Map Threema file IDs to encrypted files in data/files/<prefix>/<id>."""
    found = {}
    for candidate in files_found:
        path = str(candidate)
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        name = parts[-1]
        if (_FILE_ID_RE.fullmatch(name)
                and len(parts) >= 4 and parts[-4:-2] == ["data", "files"]
                and parts[-2] == name[:2]):
            found.setdefault(name, path)
    return found


def decrypt_stored_file(path, file_id, key, plaintext_size, storage_version):
    """Decrypt and authenticate a version-1 Threema local file.

    Returns ``(bytes, status)``. No partial plaintext is returned when a chunk
    fails authentication or the stored length does not match the database.
    """
    if storage_version != 1:
        return None, f"Unsupported storage format ({storage_version})"
    if not isinstance(key, bytes) or len(key) != 32:
        return None, "Invalid file encryption key"
    if not isinstance(file_id, str) or len(file_id) != 48:
        return None, "Invalid local file ID"
    try:
        size = int(plaintext_size)
    except (TypeError, ValueError):
        return None, "Invalid plaintext size"
    if size < 0:
        return None, "Invalid plaintext size"
    try:
        with open(path, "rb") as handle:
            encrypted = handle.read()
    except OSError:
        return None, "Local file not readable"
    if size == 0:
        return (b"", "Authenticated") if not encrypted else (None, "Stored length mismatch")

    from Crypto.Cipher import AES
    chunks, offset, remaining = [], 0, size
    count = (size + FILE_CHUNK_SIZE - 1) // FILE_CHUNK_SIZE
    suffix = bytes.fromhex(file_id[-8:])
    try:
        for index in range(1, count + 1):
            plain_length = min(FILE_CHUNK_SIZE, remaining)
            stored_length = plain_length + FILE_TAG_SIZE
            block = encrypted[offset:offset + stored_length]
            if len(block) != stored_length:
                return None, "Stored length mismatch"
            last = index == count
            nonce = suffix + index.to_bytes(4, "big") + b"\x00\x00\x00" + bytes([last])
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=FILE_TAG_SIZE)
            chunks.append(cipher.decrypt_and_verify(block[:-FILE_TAG_SIZE], block[-FILE_TAG_SIZE:]))
            offset += stored_length
            remaining -= plain_length
    except (ValueError, OverflowError):
        return None, "Authentication failed"
    if offset != len(encrypted):
        return None, "Stored length mismatch"
    return b"".join(chunks), "Authenticated"


def is_plaintext_sqlite(path):
    try:
        with open(path, "rb") as handle:
            return handle.read(16) == _SQLITE_MAGIC
    except OSError:
        return False


def database_files(files_found):
    """Yield each main database once, excluding sidecars."""
    seen = set()
    for candidate in files_found:
        path = str(candidate)
        if os.path.basename(path) != "threema.sqlite":
            continue
        real = os.path.realpath(path)
        if real not in seen:
            seen.add(real)
            yield path


def _read_text(path, limit=4096):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit).strip()
    except OSError:
        return ""


def _supplied_secrets():
    """(raw-key value, password value) supplied by the examiner, or (None, None)."""
    try:
        from scripts.context import Context
        return Context.get_app_secret("threema"), Context.get_app_secret("threema_password")
    except (ImportError, AttributeError):
        return None, None


def _keystorage_paths(files_found):
    names = {name.lower() for name in threema_keystorage.KEYSTORAGE_FILENAMES}
    return [str(path) for path in files_found if os.path.basename(str(path)).lower() in names]


def resolve_database_key(files_found):
    """Return (database key hex, source).

    A 64-character hexadecimal key supplied directly (``--threema-key``, the GUI
    button, or a credential text file) is used as is. Otherwise, if a password is
    supplied (``--threema-password``, or a non-hex value given to the key input),
    the key is recovered from keystorage.bin by running its Argon2id KDF and
    unwrapping the layered key storage.
    """
    supplied_key, supplied_password = _supplied_secrets()
    raw_candidates = []
    if supplied_key:
        raw_candidates.append(("--threema-key", supplied_key))
    for candidate in files_found:
        path = str(candidate)
        if os.path.basename(path).lower() in CREDENTIAL_FILENAMES:
            raw_candidates.append((os.path.basename(path), _read_text(path)))
    for source, value in raw_candidates:
        value = value.strip()
        if _RAW_KEY_RE.fullmatch(value):
            return value.lower(), source

    password_candidates = []
    if supplied_password:
        password_candidates.append(("--threema-password", supplied_password))
    # A value handed to the key input that is not a raw key may be the password.
    if supplied_key and not _RAW_KEY_RE.fullmatch(supplied_key.strip()):
        password_candidates.append(("--threema-key", supplied_key))
    keystores = _keystorage_paths(files_found)
    if password_candidates and keystores:
        last = "the password did not recover the key"
        for source, password in password_candidates:
            for keystore in keystores:
                try:
                    with open(keystore, "rb") as handle:
                        data = handle.read()
                    key, _identity = threema_keystorage.unwrap_database_key(data, password)
                    return key.hex(), f"{source} + keystorage.bin"
                except threema_keystorage.ThreemaKeystorageError as exc:
                    last = str(exc)
                except OSError as exc:
                    last = f"keystorage.bin could not be read: {exc}"
        return None, last
    if password_candidates:
        return None, "a Threema password was supplied but keystorage.bin was not found"
    if raw_candidates:
        return None, "the supplied value is not a 64-character hexadecimal database key or a password"
    return None, ("the encrypted database needs the account password (supply it with "
                  "--threema-password and DLEAPP unwraps keystorage.bin) or the 64-character "
                  "hexadecimal database key (with --threema-key)")


def explain(reason):
    """Log a shared opening condition once per run."""
    if reason not in _explained:
        _explained.add(reason)
        logfunc(f"Threema Desktop: {reason}.")


def open_database(path, files_found):
    """Open one database read-only, decrypting to a temporary copy when needed."""
    if is_plaintext_sqlite(path):
        try:
            return sqlite3.connect(f"file:{path}?mode=ro", uri=True), "already decrypted"
        except sqlite3.Error as exc:
            return None, f"the decrypted database could not be opened: {exc}"

    key_hex, how = resolve_database_key(files_found)
    if not key_hex:
        return None, how

    real = os.path.realpath(path)
    cached = _decrypted_cache.get(real)
    if cached and os.path.isfile(cached):
        try:
            return sqlite3.connect(f"file:{cached}?mode=ro", uri=True), how
        except sqlite3.Error:
            pass

    from scripts.sqlcipher_decrypt import decrypt_sqlcipher_db
    digest = hashlib.sha1(real.encode("utf-8", "replace")).hexdigest()[:12]
    folder = os.path.join(tempfile.gettempdir(), "dleapp_threema")
    os.makedirs(folder, mode=0o700, exist_ok=True)
    output = os.path.join(folder, f"threema_{digest}.sqlite")
    try:
        pages, verified = decrypt_sqlcipher_db(
            path, key_hex, output, page_size=PAGE_SIZE,
            hmac_algorithm=HMAC_ALGORITHM, kdf_algorithm=KDF_ALGORITHM,
            raw_key=True, apply_wal=True)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, f"the database could not be decrypted: {exc}"
    if not pages or not verified:
        try:
            os.remove(output)
        except OSError:
            pass
        return None, "the supplied key did not authenticate the database"

    _decrypted_cache[real] = output
    try:
        return sqlite3.connect(f"file:{output}?mode=ro", uri=True), how
    except sqlite3.Error as exc:
        return None, f"the decrypted database could not be opened: {exc}"


def columns(db, table):
    """Return column names from a fixed internal table identifier."""
    try:
        return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
    except sqlite3.Error:
        return set()


def optional(db, table, names, alias=""):
    """Build fixed-name SELECT expressions that tolerate schema revisions."""
    present = columns(db, table)
    prefix = f"{alias}." if alias else ""
    return ", ".join(
        f'{prefix}"{name}" AS "{name}"' if name in present else f'NULL AS "{name}"'
        for name in names)


def read_databases(context, reader, label):
    """Run a reader against every profile database and append source provenance."""
    files_found = [str(path) for path in context.get_files_found()]
    output, sources = [], []
    for path in database_files(files_found):
        db, note = open_database(path, files_found)
        if db is None:
            explain(note)
            continue
        db.row_factory = sqlite3.Row
        try:
            rows = list(reader(db))
        except (sqlite3.Error, ValueError, TypeError, OverflowError) as exc:
            logfunc(f"{label}: could not read database: {exc}")
            continue
        finally:
            db.close()
        relative = context.get_relative_path(path)
        output.extend(tuple(row) + (relative,) for row in rows)
        sources.append(path)
    logfunc(f"{label}: {len(output)} row(s).")
    return output, "\n".join(sources)
