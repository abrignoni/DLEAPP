"""Shared handling for Signal Desktop's encrypted profile.

Signal Desktop keeps its messages in a SQLCipher database at ``sql/db.sqlite``
and, on recent versions, encrypts each file in ``attachments.noindex`` as well.
Everything therefore depends on one database key, and where that key lives has
changed across releases:

* Older builds wrote the key straight into ``config.json`` as ``key``.
* Current builds store it as ``encryptedKey``, wrapped with Electron's
  safeStorage, whose backend differs by platform and is never in the profile:
  the macOS login Keychain (service ``Signal Safe Storage``) and Linux
  libsecret/kwallet both wrap it with a password-derived key, while Windows
  wraps it with DPAPI, bound to the user account with no password to supply.

The database parsing itself is platform-independent: the SQLCipher database and
the attachments decrypt the same way once the key is in hand, so a profile from
any desktop OS is read given its key. What differs is recovering that key from
``encryptedKey``:

* macOS and Linux use Chromium's safeStorage password scheme, implemented
  here (see ``unwrap_encrypted_key``), but with different parameters. macOS
  derives the wrapping key with 1003 iterations from the Keychain credential.
  Linux uses 1 iteration and the prefix ``v11`` for a key wrapped with the
  libsecret/kwallet secret, which has to be supplied. With no keyring, Signal
  does not wrap the key at all: it keeps ``key`` in the clear (``getSQLKey`` in
  Signal Desktop v8.33.0 ``app/main.main.ts``), which needs nothing supplied.
  The Linux unwrap follows Chromium's ``os_crypt_linux.cc`` and has been
  exercised only on keys built to that source, not on a Linux Signal profile.
* Windows uses DPAPI, which this module does NOT implement. A current Windows
  profile therefore needs the already-unwrapped 64-character database key
  supplied directly, recovered out of band (for example from the DPAPI master
  key and the user password with a separate tool). Supplying a value from the
  Windows Credential Manager will not unwrap ``encryptedKey`` here.

Older plaintext-``key`` profiles need nothing on any platform. This module
resolves whichever input is present, in that order, and reports which one it
used so the report records how the database was opened.

It does not attempt to recover the credential from a ``login.keychain-db`` with
a login password. On current macOS the login keychain is not encrypted with the
account login password, so that path fails on exactly the systems that use
``encryptedKey``; offering it only invites an examiner to burn time on an input
that cannot work. Supply the credential (or the key) instead.

The unwrap follows Chromium's safeStorage scheme, which Signal inherits from
Electron::

    KEK  = PBKDF2-HMAC-SHA1(password, salt="saltysalt", iterations, 16 bytes)
    key  = AES-128-CBC-decrypt(KEK, iv=b" " * 16, encryptedKey without its prefix)

    macOS            prefix "v10", 1003 iterations, the Keychain credential
    Linux, keyring   prefix "v11", 1 iteration, the libsecret/kwallet secret

The result is the 64 character hex string Signal passes to
``PRAGMA key = "x'...'"``.
"""

import base64
import hashlib
import hmac
import importlib.util
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone

from scripts.ilapfuncs import get_sqlite_db_path

_SAFE_STORAGE_SALT = b"saltysalt"
# (prefix, PBKDF2 iterations) for each platform's safeStorage, macOS first.
_MACOS_SCHEME = (b"v10", 1003)
_LINUX_KEYRING_SCHEME = (b"v11", 1)
_SAFE_STORAGE_SCHEMES = (_MACOS_SCHEME, _LINUX_KEYRING_SCHEME)
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
    """True when PyCryptodome is installed, which the unwrap and decrypt need."""
    return importlib.util.find_spec("Crypto.Cipher.AES") is not None


def unwrap_encrypted_key(encrypted_key_hex, credential, schemes=_SAFE_STORAGE_SCHEMES):
    """Unwrap a safeStorage-wrapped Signal database key.

    Each (prefix, iterations) scheme whose prefix the blob carries is tried in
    turn; a wrong one fails the padding or key-shape check, so trying them all
    is safe.

    Args:
        encrypted_key_hex: the ``encryptedKey`` value from config.json.
        credential: the OS credential store password, as a string.
        schemes: the (prefix, iterations) pairs to try.

    Returns:
        The database key as a hex string, or None if the input does not unwrap.
    """
    try:
        blob = bytes.fromhex(encrypted_key_hex)
    except (TypeError, ValueError):
        return None
    for prefix, iterations in schemes:
        if blob.startswith(prefix):
            key = _unwrap_with(blob[len(prefix):], credential, iterations)
            if key:
                return key
    return None


def _unwrap_with(blob, password, iterations):
    """AES-128-CBC unwrap of a prefix-stripped blob; the key hex string or None."""
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA1
    from Crypto.Protocol.KDF import PBKDF2

    if not blob or len(blob) % 16:
        return None

    kek = PBKDF2(password, _SAFE_STORAGE_SALT, dkLen=_SAFE_STORAGE_KEY_LENGTH,
                 count=iterations, hmac_hash_module=SHA1)
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


def _profile_root(database_path):
    """The profile folder of a db.sqlite: the folder holding its sql folder."""
    folder = os.path.dirname(str(database_path))
    if os.path.basename(folder) == "sql":
        folder = os.path.dirname(folder)
    return folder


def profiles(context, files_found):
    """The matched files split into one list per Signal Desktop profile.

    A computer can hold several profiles, one per user account. Each list holds one
    profile's db.sqlite with the files under that profile's folder, plus every credential
    file the examiner placed in the extraction, which is tried on each profile. A file under
    two profile folders goes to the deeper one. A profile held again under
    System/Volumes/Data or System/Volumes/Update/mnt1 with identical bytes is read once.
    With no database, the matched files are returned as one list, so the reason no
    database was opened is still reported.
    """
    files_found = [str(path) for path in files_found]
    databases = list(database_files(files_found))
    if databases and context is not None:
        from scripts.macos_plists import unique_sources
        databases, _skipped = unique_sources(context, databases, sidecars=("-wal",),
                                             label="Signal Desktop")
    if not databases:
        return [files_found]
    roots = sorted({_profile_root(path) for path in databases}, key=len, reverse=True)
    credentials = [path for path in files_found
                   if os.path.basename(path).lower() in CREDENTIAL_FILENAMES]
    grouped = {root: [] for root in roots}
    for path in files_found:
        for root in roots:
            if path.startswith(root + os.sep) or path.startswith(root + "/"):
                grouped[root].append(path)
                break
    result = []
    for database in databases:
        root = _profile_root(database)
        members = [path for path in grouped[root]
                   if os.path.basename(path) != "db.sqlite" or path == database]
        result.append(members + [path for path in credentials if path not in members])
    return result


def _supplied_values():
    """The secrets given at invocation for Signal, as a tuple (empty when none)."""
    try:
        from scripts.context import Context
        supplied = Context.get_app_secret("signal")
    except (ImportError, AttributeError):
        # Older cores have no app-secret store; the other inputs still work.
        return ()
    if not supplied:
        return ()
    return tuple(supplied) if isinstance(supplied, (list, tuple)) else (supplied,)


def candidate_keys(files_found):
    """Every SQLCipher key a Signal Desktop profile could open with, in the order to try.

    Returns (candidates, reason): candidates is a list of (key_hex, how), where ``how``
    describes the source, and reason says, for an examiner reading the report, why the
    list is empty. A key is only a candidate until it authenticates the database: several
    secrets may be given for several profiles, and each is tried on each profile.
    """
    configs = list(config_files(files_found))
    secrets = list(_supplied_secrets(files_found))

    # The secrets given at invocation, with --signal-key or the GUI field, come
    # first, in the order given: they are the examiner's explicit choice for this run.
    secrets[0:0] = [("--signal-key", supplied) for supplied in _supplied_values()]

    candidates = []

    def add(key, how):
        if key and key.lower() not in [known for known, _how in candidates]:
            candidates.append((key.lower(), how))

    def source_of(path, quoted=False):
        if path == "--signal-key":
            return path
        return f"'{os.path.basename(path)}'" if quoted else os.path.basename(path)

    # 1. A raw key handed to us directly needs nothing else.
    for path, text in secrets:
        if _RAW_KEY_RE.match(text):
            add(text, f"key supplied by {source_of(path)}")

    parsed = []
    for path in configs:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                config = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(config, dict):
            parsed.append(config)

    # 2. Older profiles carry the key in the clear.
    for config in parsed:
        plain = config.get("key")
        if isinstance(plain, str) and _RAW_KEY_RE.match(plain.strip()):
            add(plain.strip(), "plaintext key in config.json")

    # 3. Current profiles need the OS credential to unwrap encryptedKey.
    wrapped = next((config["encryptedKey"] for config in parsed
                    if isinstance(config.get("encryptedKey"), str)), None)

    if wrapped and not crypto_available():
        return candidates, "PyCryptodome is not installed, so encryptedKey cannot be unwrapped"

    if wrapped and secrets:
        # The secret is the safeStorage credential itself (or a raw key, which
        # section 1 already took). Anything that unwraps encryptedKey is a candidate.
        for path, text in secrets:
            key = unwrap_encrypted_key(wrapped, text)
            if key:
                add(key, f"encryptedKey unwrapped with the credential from "
                         f"{source_of(path, quoted=True)}")
        if not candidates and len(secrets) == 1:
            return candidates, ("the supplied secret did not unwrap encryptedKey; it may be the "
                                "wrong credential, or belong to a different profile or host")
        if not candidates:
            return candidates, (f"none of the {len(secrets)} supplied secrets unwrapped "
                                "encryptedKey; each may be the wrong credential, or belong to a "
                                "different profile or host")

    if candidates:
        return candidates, ""

    if wrapped:
        return candidates, (
            "config.json holds an encryptedKey, wrapped by the OS and not part of the "
            "profile. On macOS, supply the password from the Keychain item 'Signal Safe "
            "Storage', and on Linux the libsecret or kwallet secret Signal stored, and it "
            "is unwrapped here. On Windows the wrapping depends on DPAPI, which is not "
            "unwrapped here: supply the already-recovered 64-character database key "
            "instead. Provide the value via --signal-key, the Signal key button in the "
            "GUI, or a file named signal_password.txt placed inside the extraction")

    if configs:
        return candidates, "config.json carries neither a plaintext key nor an encryptedKey"
    return candidates, "no Signal Desktop config.json was found"


def resolve_database_key(files_found, log=None):
    """The first candidate key for a Signal Desktop profile.

    Returns (key_hex, how), or (None, reason) when there is no candidate. open_database
    tries every candidate; this is the first of them.
    """
    candidates, reason = candidate_keys(files_found)
    if not candidates:
        return None, reason
    key, how = candidates[0]
    if log:
        log(f"Signal Desktop: first candidate database key: {how}.")
    return key, how


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



def clear_decrypted_copies():
    """Forget and delete this run's decrypted copies, so the next run decrypts afresh."""
    for entry in set(_decrypted_cache.values()):
        path = entry[0] if isinstance(entry, tuple) else entry
        try:
            os.remove(path)
        except OSError:
            pass
    _decrypted_cache.clear()


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
    # A copy decrypted earlier is reused only with the same secrets, the credential files
    # in the extraction included: the window runs several times in one process, and a
    # secret given for one run must not open the next.
    cache_key = (os.path.realpath(database_path), _supplied_values(),
                 tuple(_supplied_secrets(files_found)))
    cached = _decrypted_cache.get(cache_key)
    if cached:
        cached_path, cached_how = cached if isinstance(cached, tuple) else (cached, "")
        try:
            return (sqlite3.connect(f"file:{get_sqlite_db_path(cached_path)}?mode=ro", uri=True),
                    cached_how or "decrypted earlier this run")
        except sqlite3.Error:
            pass

    # An examiner may have decrypted the database already, with DB Browser for
    # SQLCipher or another tool, and be parsing that copy. It is then a plain
    # SQLite file and needs no key, so read it as it is rather than refusing.
    if is_plaintext_sqlite(database_path):
        explain("the database is already decrypted, so no credential is needed", log)
        try:
            return (sqlite3.connect(f"file:{get_sqlite_db_path(database_path)}?mode=ro", uri=True),
                    "already decrypted before parsing")
        except sqlite3.Error as ex:
            return None, f"the decrypted database could not be opened: {ex}"

    candidates, reason = candidate_keys(files_found)
    if not candidates:
        return None, reason

    digest = hashlib.sha1(database_path.encode("utf-8", "replace")).hexdigest()[:12]
    output_path = os.path.join(tempfile.gettempdir(), "dleapp_signal", f"signal_{digest}.db")
    for key_hex, how in candidates:
        if log:
            log(f"Signal Desktop: trying the {how} on '{database_path}'.")
        if decrypt_database(database_path, key_hex, output_path, log=log):
            break
    else:
        try:
            os.remove(output_path)
        except OSError:
            pass
        if len(candidates) == 1:
            return None, "the database did not decrypt with the key that was resolved"
        return None, (f"the database did not decrypt with any of the {len(candidates)} "
                      "candidate keys")

    _decrypted_cache[cache_key] = (output_path, how)
    try:
        return sqlite3.connect(f"file:{get_sqlite_db_path(output_path)}?mode=ro", uri=True), how
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
    # Deliberately broad: a malformed database image must not stop the module.
    except Exception as ex:  # a malformed image should not stop the module  # pylint: disable=broad-exception-caught
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
