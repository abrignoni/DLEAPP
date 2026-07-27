"""Minimal reader for a macOS keychain (``login.keychain-db``).

Some desktop applications, Signal among them, protect their data with a key
wrapped by the OS credential store. On macOS that store is the login keychain,
and the wrapping password is a generic-password item inside it. On a dead-box
image there is no ``security`` command to read that item, but the keychain file
itself is in the extraction, and with the account's login password its contents
can be recovered offline.

This module does exactly that and no more: given a keychain file, the login
password and a service name, it returns that one generic password. It does not
enumerate or dump the other secrets in the keychain, which keeps the exposure
to the single item an examiner asked for.

The format is Apple's ``securityd`` database (``AppleFileDL`` / ``CSSM``),
documented in Apple's open-source ``securityd`` ``BLOBFORMAT`` and independently
described many times. The recovery is three deterministic steps:

1. Master key = PBKDF2-HMAC-SHA1(password, DbBlob salt, 1000 iterations, 24
   bytes), then 3DES-CBC decrypt the DbBlob's crypto region with it and the
   DbBlob IV to get the 24-byte database key. Those parameters are fixed in
   securityd and never vary (see ``_KDF_DIGEST``).
2. For each symmetric-key record, unwrap its key blob with the database key
   using the CMS 3DES key-unwrap (decrypt with the magic IV, reverse the first
   32 bytes, decrypt again with the blob IV). Index the result by the record's
   ``ssgp``+label tag.
3. A generic-password record carries an SSGP blob whose ``ssgp``+label tag
   selects one unwrapped key; 3DES-CBC decrypt the SSGP body with it.

There is no key searching here: every value is computed by the documented
formula and used once. A wrong password fails the padding check at step 1 and
the whole thing returns nothing.

One caution for callers. A ``None`` means "this password did not open this
keychain", which is not the same as "the examiner typed the wrong password".
The login keychain retains its old password when the account password is reset
through Apple ID or by an administrator, and macOS keeps unlocking it from the
stashed session key, so a live host gives no hint that the two have diverged.
Report the failure in those terms rather than as a bad password.
"""

import hashlib
import importlib.util
import struct
from binascii import unhexlify

_KEYCHAIN_MAGIC = b"kych"
_COMMON_BLOB_MAGIC = 0xFADE0711
_SECURE_STORAGE_GROUP = b"ssgp"
_MAGIC_CMS_IV = unhexlify("4adda22c79e82105")
_KEY_LENGTH = 24
_BLOCK_SIZE = 8
_ATOM = 4

# CSSM record-type ids for the two tables this reader needs.
_RECORD_METADATA = 0x80008000
_RECORD_SYMMETRIC_KEY = 0x00000011  # OPEN_GROUP_START (0x0A) + 7
_RECORD_GENERIC_PASSWORD = 0x80000000  # APP_DEFINED_START

_HEADER = struct.Struct("> 4s i i i i")            # magic, version, headerSize, schemaOff, authOff
_SCHEMA = struct.Struct("> i i")                   # schemaSize, tableCount
_TABLE_HEADER = struct.Struct("> I I I I I I I")   # size, id, recordCount, records, idx, freelist, recNumCount
_UINT = struct.Struct("> I")
_KEY_BLOB = struct.Struct("> 8s I I 8s")           # commonBlob(magic+ver), startCrypto, totalLen, iv
_KEY_BLOB_REC_HEADER_SIZE = 132
_GENERIC_PW_FIELDS = 22                             # uint32 fields before the variable-length data
_SSGP_HEADER = struct.Struct("> 4s 16s 8s")        # magic, label, iv

# The DbBlob records the PBKDF2 salt but not the digest or the iteration count,
# so the reader has to carry them. These are fixed, not negotiated: Apple's
# securityd derives the database master key in DatabaseCryptoCore
# ::deriveDbMasterKey with CSSM_PKCS5_PBKDF2_PRF_HMAC_SHA1, iterationCount(1000)
# and a 24-byte key, and none of the three is conditional on anything -- not on
# the blob version, not on the keychain's age.
#
# Worth knowing, because it looks like a difference that should matter and is
# not: a real login.keychain-db carries blobVersion 0x200 (version_partition)
# while anything created today is 0x100. That version gates which *verification*
# algorithm the blob decode uses, not the key derivation.
#
# So a failure here means the password does not open this keychain, and the
# usual reason is not a typo. A login keychain keeps its old password when the
# account password is reset through Apple ID or by an administrator, and macOS
# then unlocks it silently from the stashed session key, so the divergence is
# invisible until something tries the password directly -- which is exactly what
# this reader does.
_KDF_DIGEST = "sha1"
_KDF_ROUNDS = 1000


def crypto_available():
    """True when PyCryptodome's DES3 is importable, which the decrypt needs."""
    return importlib.util.find_spec("Crypto.Cipher.DES3") is not None


def is_keychain(path):
    """True when a file starts with the macOS keychain magic."""
    try:
        with open(path, "rb") as handle:
            return handle.read(4) == _KEYCHAIN_MAGIC
    except OSError:
        return False


def _des3_decrypt(key, iv, data):
    """3DES-CBC decrypt and strip PKCS#7 padding; return None on bad padding.

    PyCryptodome rejects a key whose halves collide (it degenerates to single
    DES); a real keychain never uses one, so treat that as a decrypt failure.
    """
    if not data or len(data) % _BLOCK_SIZE:
        return None
    from Crypto.Cipher import DES3

    try:
        plain = DES3.new(key, DES3.MODE_CBC, iv).decrypt(data)
    except ValueError:
        return None
    pad = plain[-1]
    if not 1 <= pad <= _BLOCK_SIZE or plain[-pad:] != bytes([pad]) * pad:
        return None
    return plain[:-pad]


class _Keychain:
    """Just enough of the keychain database to walk its tables and records."""

    def __init__(self, data):
        self.data = data
        # Addresses in this format are all relative to the fixed header struct
        # size (20), not to the HeaderSize field the header also stores (16).
        # Using the field value throws every table offset off by four.
        self.base = _HEADER.size
        signature, _version, _header_size, schema_off, _auth = _HEADER.unpack_from(data, 0)
        if signature != _KEYCHAIN_MAGIC:
            raise ValueError("not a macOS keychain")
        _size, table_count = _SCHEMA.unpack_from(data, schema_off)
        first_table = self.base + _SCHEMA.size
        self.tables = {}
        for i in range(table_count):
            offset, = _UINT.unpack_from(data, first_table + _ATOM * i)
            base = self.base + offset
            table_id, = _UINT.unpack_from(data, base + 4)
            self.tables[table_id] = offset

    def records(self, record_type):
        """Yield the absolute base address of each record in a table."""
        offset = self.tables.get(record_type)
        if offset is None:
            return
        base = self.base + offset
        _size, _tid, record_count, _r, _idx, _fl, number_count = _TABLE_HEADER.unpack_from(self.data, base)
        cursor = base + _TABLE_HEADER.size
        seen = 0
        index = 0
        while seen < record_count and index < number_count + record_count + 8:
            rec_off, = _UINT.unpack_from(self.data, cursor + _ATOM * index)
            index += 1
            if rec_off and rec_off % 4 == 0:
                seen += 1
                yield base + rec_off

    def db_blob(self):
        """Locate the DbBlob via the metadata table, at record + 0x38."""
        offset = self.tables.get(_RECORD_METADATA)
        if offset is None:
            return None
        base = self.base + offset + 0x38
        magic, = struct.unpack_from("> I", self.data, base)
        if magic != _COMMON_BLOB_MAGIC:
            return None
        return base


def _database_key(data, blob_base, password):
    """Step 1: password + DbBlob -> 24-byte database key, or None."""
    _common, start_crypto, total_len, _sig, _seq, _params, salt, iv, _bsig = struct.unpack_from(
        "> 8s I I 16s I 8s 20s 8s 20s", data, blob_base)
    ciphertext = data[blob_base + start_crypto:blob_base + total_len]
    master = hashlib.pbkdf2_hmac(
        _KDF_DIGEST, password.encode("utf-8"), salt, _KDF_ROUNDS, _KEY_LENGTH)
    plain = _des3_decrypt(master, iv, ciphertext)
    if not plain or len(plain) < _KEY_LENGTH:
        return None
    return plain[:_KEY_LENGTH]


def _unwrap_key(ciphertext, iv, db_key):
    """Step 2: CMS 3DES key-unwrap of one symmetric key blob."""
    from Crypto.Cipher import DES3

    try:
        first = DES3.new(db_key, DES3.MODE_CBC, _MAGIC_CMS_IV).decrypt(ciphertext)
    except ValueError:
        return None
    # No padding on the intermediate: the CMS scheme reverses the leading block
    # then decrypts again to reveal the key.
    reversed_head = bytes(reversed(first[:32]))
    second = _des3_decrypt(db_key, iv, reversed_head)
    if not second:
        return None
    key = second[4:]
    return key if len(key) == _KEY_LENGTH else None


def _key_list(keychain, db_key):
    """All unwrapped item keys, indexed by their ssgp+label tag."""
    keys = {}
    for base in keychain.records(_RECORD_SYMMETRIC_KEY):
        record_size, = _UINT.unpack_from(keychain.data, base)
        record = keychain.data[base + _KEY_BLOB_REC_HEADER_SIZE:base + record_size]
        if len(record) < _KEY_BLOB.size:
            continue
        _common, start_crypto, total_len, iv = _KEY_BLOB.unpack_from(record, 0)
        tag = record[total_len + 8:total_len + 8 + 20]
        if tag[:4] != _SECURE_STORAGE_GROUP:
            continue
        ciphertext = record[start_crypto:total_len]
        if not ciphertext or len(ciphertext) % _BLOCK_SIZE:
            continue
        unwrapped = _unwrap_key(ciphertext, iv, db_key)
        if unwrapped:
            keys[tag] = unwrapped
    return keys


def _generic_passwords(keychain, key_list):
    """Yield (service, account, decrypted secret) for generic-password records."""
    for base in keychain.records(_RECORD_GENERIC_PASSWORD):
        header_len = _GENERIC_PW_FIELDS * 4
        meta = struct.unpack_from("> %dI" % _GENERIC_PW_FIELDS, keychain.data, base)
        ssgp_area = meta[4]
        service = _read_field(keychain.data, base, meta[20])   # Service
        account = _read_field(keychain.data, base, meta[19])   # Account
        if not ssgp_area:
            continue
        # SSGPArea is the length of the ssgp blob measured from the end of the
        # fixed header, not an absolute record offset.
        body = keychain.data[base + header_len:base + header_len + ssgp_area]
        if len(body) < _SSGP_HEADER.size:
            continue
        magic, label, iv = _SSGP_HEADER.unpack_from(body, 0)
        encrypted = body[_SSGP_HEADER.size:]
        item_key = key_list.get(magic + label)
        if not item_key:
            continue
        secret = _des3_decrypt(item_key, iv, encrypted)
        if secret is not None:
            yield service, account, secret


def _read_field(data, base, field_offset):
    """Read a length-prefixed keychain attribute; '' when absent."""
    field_offset &= 0xFFFFFFFE
    if not field_offset:
        return ""
    pos = base + field_offset
    length, = _UINT.unpack_from(data, pos)
    return data[pos + 4:pos + 4 + length].decode("utf-8", "replace")


def find_generic_password(keychain_path, password, service):
    """Return the secret of a generic-password item, or None.

    Args:
        keychain_path: path to a login.keychain-db.
        password: the account login password.
        service: the service name to match, e.g. 'Signal Safe Storage'.
    """
    if not crypto_available():
        return None
    try:
        with open(keychain_path, "rb") as handle:
            data = handle.read()
    except OSError:
        return None
    try:
        keychain = _Keychain(data)
    except (ValueError, struct.error):
        return None

    blob_base = keychain.db_blob()
    if blob_base is None:
        return None
    db_key = _database_key(data, blob_base, password)
    if db_key is None:
        return None  # wrong password, almost always

    try:
        key_list = _key_list(keychain, db_key)
        for found_service, _account, secret in _generic_passwords(keychain, key_list):
            if found_service == service:
                return secret.decode("utf-8", "replace")
    except (struct.error, ValueError):
        return None
    return None
