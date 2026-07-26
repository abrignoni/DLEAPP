"""Shared handling for Signal Desktop's encrypted profile.

Signal Desktop keeps its messages in a SQLCipher database at ``sql/db.sqlite``
and, on recent versions, encrypts each file in ``attachments.noindex`` as well.
Everything therefore depends on one database key, and where that key lives has
changed across releases:

* Older builds wrote the key straight into ``config.json`` as ``key``.
* Current builds store it as ``encryptedKey``, wrapped with Electron's
  safeStorage. The wrapping password lives in the OS credential store, which is
  the macOS login Keychain (service ``Signal Safe Storage``) or the Windows
  Credential Manager, and never in the profile folder.

An extraction of the profile alone therefore cannot be decrypted: the credential
has to be captured from the running host and supplied alongside. This module
resolves whichever of those inputs is present, in that order, and reports which
one it used so the report records how the database was opened.

The unwrap follows Chromium's safeStorage scheme, which Signal inherits from
Electron::

    KEK  = PBKDF2-HMAC-SHA1(credential, salt="saltysalt", 1003 iterations, 16 bytes)
    key  = AES-128-CBC-decrypt(KEK, iv=b" " * 16, encryptedKey without its "v10" prefix)

The result is the 64 character hex string Signal passes to
``PRAGMA key = "x'...'"``.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone

_SAFE_STORAGE_PREFIX = b"v10"
_SAFE_STORAGE_SALT = b"saltysalt"
_SAFE_STORAGE_ITERATIONS = 1003
_SAFE_STORAGE_KEY_LENGTH = 16
_SAFE_STORAGE_IV = b" " * 16

# Signal writes a 32 byte key, so the hex form is 64 characters.
_RAW_KEY_RE = re.compile(r"^[0-9a-fA-F]{64}$")

# Filenames an examiner may drop beside the extraction carrying either the OS
# credential or an already unwrapped database key. Content decides which it is,
# so the same names work for both and a mislabelled file still resolves.
CREDENTIAL_FILENAMES = (
    "signal-keychain.txt",
    "signal_keychain.txt",
    "signal_password.txt",
    "signal-password.txt",
    "signal_safe_storage.txt",
    "signal-safe-storage.txt",
    "signal_db_key.txt",
    "signal-db-key.txt",
)

# SQLCipher 4 defaults, which is what Signal Desktop uses.
PAGE_SIZE = 4096
HMAC_ALGORITHM = "sha512"
KDF_ALGORITHM = "sha512"


def crypto_available():
    try:
        import Crypto.Cipher.AES  # noqa: F401
        return True
    except ImportError:
        return False


def unwrap_encrypted_key(encrypted_key_hex, credential):
    """Unwrap a safeStorage-wrapped Signal database key.

    Args:
        encrypted_key_hex: the ``encryptedKey`` value from config.json.
        credential: the OS credential store password, as a string.

    Returns:
        The database key as a hex string, or None if the input does not unwrap.
    """
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA1
    from Crypto.Protocol.KDF import PBKDF2

    try:
        blob = bytes.fromhex(encrypted_key_hex)
    except (TypeError, ValueError):
        return None
    if not blob.startswith(_SAFE_STORAGE_PREFIX):
        return None
    blob = blob[len(_SAFE_STORAGE_PREFIX):]
    if not blob or len(blob) % 16:
        return None

    kek = PBKDF2(credential, _SAFE_STORAGE_SALT, dkLen=_SAFE_STORAGE_KEY_LENGTH,
                 count=_SAFE_STORAGE_ITERATIONS, hmac_hash_module=SHA1)
    plaintext = AES.new(kek, AES.MODE_CBC, _SAFE_STORAGE_IV).decrypt(blob)

    # Strip PKCS#7 padding ourselves: a wrong credential usually yields an
    # invalid pad, and that is a cleaner signal than an exception.
    pad = plaintext[-1] if plaintext else 0
    if not 1 <= pad <= 16 or plaintext[-pad:] != bytes([pad]) * pad:
        return None
    candidate = plaintext[:-pad].decode("ascii", "ignore").strip()
    return candidate if _RAW_KEY_RE.match(candidate) else None


def _read_text(path, limit=4096):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit).strip()
    except OSError:
        return ""


def _supplied_secrets(files_found):
    """Yield (path, text) for examiner-supplied credential or key files."""
    for file_found in files_found:
        file_found = str(file_found)
        if os.path.basename(file_found).lower() in CREDENTIAL_FILENAMES:
            text = _read_text(file_found)
            if text:
                yield file_found, text


def config_files(files_found):
    for file_found in files_found:
        file_found = str(file_found)
        if os.path.basename(file_found) == "config.json":
            yield file_found


_SQLITE_MAGIC = b"SQLite format 3\x00"


def is_plaintext_sqlite(path):
    """True when a file is an unencrypted SQLite database.

    A SQLCipher database has no readable header: its first bytes are the salt.
    So the magic string is a reliable way to tell a database that still needs a
    key from one that was decrypted before it reached us.
    """
    try:
        with open(path, "rb") as handle:
            return handle.read(16) == _SQLITE_MAGIC
    except OSError:
        return False


def database_files(files_found):
    """Signal's main database, ignoring its -wal and -shm siblings."""
    seen = set()
    for file_found in files_found:
        file_found = str(file_found)
        if os.path.basename(file_found) != "db.sqlite":
            continue
        real = os.path.realpath(file_found)
        if real not in seen:
            seen.add(real)
            yield file_found


def resolve_database_key(files_found, log=None):
    """Work out the SQLCipher key for a Signal Desktop profile.

    Returns (key_hex, how) where ``how`` describes the source, or (None, reason)
    when no key could be produced. The reason is written for an examiner reading
    the report, not for a developer.
    """
    def note(message):
        if log:
            log(message)

    configs = list(config_files(files_found))
    secrets = list(_supplied_secrets(files_found))

    # A secret given at invocation, with --signal-key or the GUI field, comes
    # first: it is the examiner's explicit choice for this run.
    try:
        from scripts.context import Context
        supplied = Context.get_app_secret("signal")
    except Exception:
        supplied = None
    if supplied:
        secrets.insert(0, ("--signal-key", supplied))

    # 1. A raw key handed to us directly needs nothing else.
    for path, text in secrets:
        if _RAW_KEY_RE.match(text):
            source = path if path == "--signal-key" else os.path.basename(path)
            note(f"Signal Desktop: using the database key supplied by {source}.")
            return text.lower(), f"key supplied by {source}"

    # 2. Older profiles carry the key in the clear.
    for path in configs:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                config = json.load(handle)
        except (OSError, ValueError):
            continue
        plain = config.get("key")
        if isinstance(plain, str) and _RAW_KEY_RE.match(plain.strip()):
            note("Signal Desktop: config.json holds the database key in the clear.")
            return plain.strip().lower(), "plaintext key in config.json"

    # 3. Current profiles need the OS credential to unwrap encryptedKey.
    wrapped = None
    for path in configs:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                config = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(config.get("encryptedKey"), str):
            wrapped = config["encryptedKey"]
            break

    if wrapped and secrets:
        if not crypto_available():
            return None, "PyCryptodome is not installed, so encryptedKey cannot be unwrapped"
        for path, text in secrets:
            key = unwrap_encrypted_key(wrapped, text)
            if key:
                source = path if path == "--signal-key" else f"'{os.path.basename(path)}'"
                note(f"Signal Desktop: unwrapped encryptedKey with the credential from {source}.")
                return key.lower(), f"encryptedKey unwrapped with the credential from {source}"
        return None, ("the supplied credential did not unwrap encryptedKey; it may belong to a "
                      "different profile or host")

    if wrapped:
        return None, ("config.json holds an encryptedKey, which is wrapped with the OS credential "
                      "store. That credential is not part of the profile, so capture it from the "
                      "host (macOS login Keychain service 'Signal Safe Storage', or Windows "
                      "Credential Manager) and pass it with --signal-key, the Signal key field in "
                      "the GUI, or a file named signal_password.txt beside the extraction")

    if configs:
        return None, "config.json carries neither a plaintext key nor an encryptedKey"
    return None, "no Signal Desktop config.json was found"


def js_ms_to_datetime(value):
    """Convert a JavaScript millisecond timestamp to an aware UTC datetime."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ""


def attachments_root(files_found):
    """Locate the attachments.noindex folder within the extraction."""
    for file_found in files_found:
        parts = str(file_found).replace("\\", "/").split("/")
        if "attachments.noindex" in parts:
            index = parts.index("attachments.noindex")
            return "/".join(parts[:index + 1])
    return None


def decrypt_attachment(root, relative_path, local_key, size, verify_hash=None):
    """Decrypt one file from attachments.noindex.

    Signal encrypts each stored attachment with a key held in the database, so
    the files are unreadable on their own. The layout is::

        IV (16) || AES-256-CBC ciphertext || HMAC-SHA256 (32)

    where the base64 ``localKey`` is 64 bytes: the AES key followed by the MAC
    key. The plaintext is then padded with zeroes to hide its true length, so
    the real file is the first ``size`` bytes.

    Returns (plaintext, authenticated, hash_matches). ``plaintext`` is None when
    the file is missing or too short to be an attachment.
    """
    if not root or not relative_path or not local_key:
        return None, False, None
    full_path = os.path.join(root, relative_path.replace("/", os.sep))
    try:
        with open(full_path, "rb") as handle:
            blob = handle.read()
    except OSError:
        return None, False, None
    if len(blob) <= 48:
        return None, False, None

    try:
        keys = base64.b64decode(local_key)
    except (ValueError, TypeError):
        return None, False, None
    if len(keys) < 64:
        return None, False, None

    from Crypto.Cipher import AES

    iv, ciphertext, stored_mac = blob[:16], blob[16:-32], blob[-32:]
    calculated = hmac.new(keys[32:64], blob[:-32], hashlib.sha256).digest()
    authenticated = hmac.compare_digest(calculated, stored_mac)
    try:
        plaintext = AES.new(keys[:32], AES.MODE_CBC, iv).decrypt(ciphertext)
    except ValueError:
        return None, authenticated, None

    pad = plaintext[-1] if plaintext else 0
    if 1 <= pad <= 16 and plaintext[-pad:] == bytes([pad]) * pad:
        plaintext = plaintext[:-pad]
    if size and 0 < size <= len(plaintext):
        plaintext = plaintext[:size]

    hash_matches = None
    if verify_hash:
        hash_matches = hashlib.sha256(plaintext).hexdigest() == verify_hash
    return plaintext, authenticated, hash_matches


def conversation_labels(connection):
    """Map conversation id to the best available human-readable name."""
    labels = {}
    try:
        rows = connection.execute(
            "SELECT id, type, name, profileFullName, profileName, e164 FROM conversations")
    except sqlite3.Error:
        return labels
    for cid, ctype, name, full, profile, e164 in rows:
        label = name or full or profile or e164 or cid
        if ctype == "group" and name:
            label = f"{name} (group)"
        labels[cid] = label
    return labels


def self_service_ids(connection):
    """The local account's own service ids, used to mark outgoing messages."""
    ids = set()
    try:
        rows = connection.execute("SELECT id, json FROM items WHERE id IN ('uuid_id','pni')")
    except sqlite3.Error:
        return ids
    for _key, blob in rows:
        try:
            value = json.loads(blob).get("value")
        except (ValueError, TypeError):
            continue
        if isinstance(value, str):
            ids.add(value.split(".")[0].replace("PNI:", "").lower())
    return ids


# Cache of source database path -> decrypted copy, so several artifacts sharing
# one profile decrypt it once per run.
_decrypted_cache = {}

# Every Signal artifact hits the same missing credential, and repeating the full
# explanation once per artifact buries the rest of the log. Say it once.
_explained = set()


def explain(reason, log):
    """Log a shared condition once, not once per artifact.

    Every Signal artifact opens the same database, so without this each of them
    repeats the same sentence and buries the rest of the log.
    """
    if not log or reason in _explained:
        return
    _explained.add(reason)
    log(f"Signal Desktop: {reason}.")


def open_database(files_found, log=None):
    """Decrypt and open the Signal database. Returns (connection, note).

    The connection is None when the database could not be opened, and the note
    then explains why in terms an examiner can act on.
    """
    databases = list(database_files(files_found))
    if not databases:
        return None, "no Signal Desktop database (sql/db.sqlite) was found"

    database_path = databases[0]
    cached = _decrypted_cache.get(os.path.realpath(database_path))
    if cached:
        try:
            return sqlite3.connect(f"file:{cached}?mode=ro", uri=True), "decrypted earlier this run"
        except sqlite3.Error:
            pass

    # An examiner may have decrypted the database already, with DB Browser for
    # SQLCipher or another tool, and be parsing that copy. It is then a plain
    # SQLite file and needs no key, so read it as it is rather than refusing.
    if is_plaintext_sqlite(database_path):
        explain("the database is already decrypted, so no credential is needed", log)
        try:
            return (sqlite3.connect(f"file:{database_path}?mode=ro", uri=True),
                    "already decrypted before parsing")
        except sqlite3.Error as ex:
            return None, f"the decrypted database could not be opened: {ex}"

    key_hex, how = resolve_database_key(files_found, log=log)
    if not key_hex:
        return None, how

    digest = hashlib.sha1(database_path.encode("utf-8", "replace")).hexdigest()[:12]
    output_path = os.path.join(tempfile.gettempdir(), "dleapp_signal", f"signal_{digest}.db")
    if not decrypt_database(database_path, key_hex, output_path, log=log):
        return None, "the database did not decrypt with the key that was resolved"

    _decrypted_cache[os.path.realpath(database_path)] = output_path
    try:
        return sqlite3.connect(f"file:{output_path}?mode=ro", uri=True), how
    except sqlite3.Error as ex:
        return None, f"the decrypted database could not be opened: {ex}"


def decrypt_database(database_path, key_hex, output_path, log=None):
    """Decrypt db.sqlite to a plaintext copy. Returns the path or None."""
    from scripts.sqlcipher_decrypt import decrypt_sqlcipher_db

    try:
        pages, verified = decrypt_sqlcipher_db(
            database_path, key_hex, output_path,
            page_size=PAGE_SIZE, hmac_algorithm=HMAC_ALGORITHM,
            kdf_algorithm=KDF_ALGORITHM, raw_key=True, apply_wal=True)
    except Exception as ex:  # a malformed image should not stop the module
        if log:
            log(f"Signal Desktop: could not decrypt '{database_path}': {ex}")
        return None
    if not pages:
        if log:
            log(f"Signal Desktop: '{database_path}' is too small to be a database.")
        return None
    if not verified:
        if log:
            log("Signal Desktop: the key did not authenticate any page of the database. "
                "It belongs to a different profile, or the file is damaged.")
        return None
    if log:
        log(f"Signal Desktop: decrypted {pages} page(s), {verified} authenticated.")
    return output_path
