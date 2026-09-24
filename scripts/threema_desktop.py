"""Shared read-only handling for Threema Desktop databases.

Threema Desktop stores its application data in a SQLCipher 4 database named
``threema.sqlite``.  This module accepts an examiner-supplied 32-byte raw key,
or reads an already-decrypted SQLite copy.  It never writes to the evidence.

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

from scripts.ilapfuncs import logfunc

_RAW_KEY_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SQLITE_MAGIC = b"SQLite format 3\x00"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

PAGE_SIZE = 4096
HMAC_ALGORITHM = "sha512"
KDF_ALGORITHM = "sha512"

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


def resolve_database_key(files_found):
    """Return an explicitly supplied raw database key and its source."""
    candidates = []
    try:
        from scripts.context import Context
        supplied = Context.get_app_secret("threema")
    except (ImportError, AttributeError):
        supplied = None
    if supplied:
        candidates.append(("--threema-key", supplied))
    for candidate in files_found:
        path = str(candidate)
        if os.path.basename(path).lower() in CREDENTIAL_FILENAMES:
            candidates.append((os.path.basename(path), _read_text(path)))
    for source, value in candidates:
        value = value.strip()
        if _RAW_KEY_RE.fullmatch(value):
            return value.lower(), source
    if candidates:
        return None, "the supplied value is not a 64-character hexadecimal database key"
    return None, ("the encrypted database needs its 64-character hexadecimal key; supply it "
                  "with --threema-key, the Threema key button, or threema-key.txt")


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
