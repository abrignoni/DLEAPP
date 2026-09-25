"""Recover the Threema Desktop database key from ``keystorage.bin``.

Threema Desktop protects its SQLCipher database key with a layered key storage
file. For a consumer profile the chain is: the user's local password is run
through Argon2id (parameters and salt stored in the file) to derive a 32-byte
key, which opens a NaCl secretbox (nonce ahead) over the encrypted intermediate
layer; the intermediate carries the inner layer in the clear, and the inner
layer holds the 32-byte ``database_key``. Each layer is a two-byte little-endian
version header followed by a protobuf message.

Format sourced from threema-ch/threema-desktop at commit
93a6615c5567f0cf8371619dc1a5e888eed1d0b6:
- internal-protobuf/key-storage-file.proto (message field numbers)
- common/node/key-storage/crypto.ts (Argon2id parameter mapping, secretbox)
- common/key-storage/layers/{outer,intermediate,inner} (the two-byte headers)

This module never writes to evidence. The password is supplied by the examiner.
"""

try:
    from argon2.low_level import Type, hash_secret_raw
    _ARGON2_AVAILABLE = True
except ImportError:
    _ARGON2_AVAILABLE = False

try:
    from nacl.exceptions import CryptoError
    from nacl.secret import SecretBox
    _NACL_AVAILABLE = True
except ImportError:
    _NACL_AVAILABLE = False

KEYSTORAGE_FILENAMES = ('keystorage.bin',)

MISSING_DEPS_MESSAGE = (
    'recovering the key from keystorage.bin needs the argon2-cffi and PyNaCl packages; '
    'install them, or supply the raw database key with --threema-key')

_ARGON2_VERSION_1_3 = 0x13
_NACL_KEY_LENGTH = 32
_DATABASE_KEY_LENGTH = 32


class ThreemaKeystorageError(Exception):
    """The key storage could not be parsed or decrypted."""


def deps_available():
    """Whether the optional crypto packages needed for the password path are present."""
    return _ARGON2_AVAILABLE and _NACL_AVAILABLE


def _read_varint(buf, index):
    shift = result = 0
    while True:
        if index >= len(buf):
            raise ThreemaKeystorageError('truncated varint in key storage')
        byte = buf[index]
        index += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, index
        shift += 7


def _read_fields(buf):
    """Parse a protobuf message into {field number: value}; last write wins."""
    fields = {}
    index = 0
    while index < len(buf):
        tag, index = _read_varint(buf, index)
        field_number, wire_type = tag >> 3, tag & 7
        if wire_type == 2:
            length, index = _read_varint(buf, index)
            if index + length > len(buf):
                raise ThreemaKeystorageError('truncated length-delimited field in key storage')
            fields[field_number] = buf[index:index + length]
            index += length
        elif wire_type == 0:
            fields[field_number], index = _read_varint(buf, index)
        elif wire_type == 5:
            index += 4
        elif wire_type == 1:
            index += 8
        else:
            raise ThreemaKeystorageError(f'unsupported wire type {wire_type} in key storage')
    return fields


def _after_header(layer):
    """Strip the two-byte layer version header before protobuf decoding."""
    if len(layer) < 2:
        raise ThreemaKeystorageError('key storage layer shorter than its version header')
    return layer[2:]


def _argon2_parameters(argon_bytes):
    fields = _read_fields(argon_bytes)
    salt = fields.get(2)
    memory_bytes = fields.get(3)
    iterations = fields.get(4)
    parallelism = fields.get(5)
    version = fields.get(1, 0)
    if not isinstance(salt, (bytes, bytearray)) or len(salt) < 16:
        raise ThreemaKeystorageError('key storage Argon2id salt is missing or too short')
    if not (isinstance(memory_bytes, int) and isinstance(iterations, int)
            and isinstance(parallelism, int)):
        raise ThreemaKeystorageError('key storage Argon2id parameters are missing')
    if version != 0:
        raise ThreemaKeystorageError(f'unsupported Argon2id version {version} in key storage')
    return bytes(salt), memory_bytes, iterations, parallelism


def parse_outer(keystorage_bytes):
    """(argon2 cost parameters, encrypted intermediate) from a keystorage.bin.

    The cost parameters are returned as (salt_length, memory_bytes, iterations,
    parallelism); the salt bytes themselves are not returned by this helper so
    callers can describe the KDF without handling key material.
    """
    outer = _read_fields(_after_header(keystorage_bytes))
    blob = outer.get(1)
    argon_bytes = outer.get(2)
    if not isinstance(blob, (bytes, bytearray)):
        raise ThreemaKeystorageError('key storage has no encrypted payload')
    if not isinstance(argon_bytes, (bytes, bytearray)):
        raise ThreemaKeystorageError('key storage has no Argon2id parameters (unsupported layout)')
    salt, memory_bytes, iterations, parallelism = _argon2_parameters(argon_bytes)
    return (len(salt), memory_bytes, iterations, parallelism), bytes(blob)


def unwrap_database_key(keystorage_bytes, password):
    """Return (database_key bytes, threema_identity str) from keystorage.bin.

    Raises ThreemaKeystorageError if the packages are missing, the file cannot be
    parsed, or the password does not decrypt it.
    """
    if not deps_available():
        raise ThreemaKeystorageError(MISSING_DEPS_MESSAGE)
    outer = _read_fields(_after_header(keystorage_bytes))
    blob = outer.get(1)
    argon_bytes = outer.get(2)
    if not isinstance(blob, (bytes, bytearray)) or not isinstance(argon_bytes, (bytes, bytearray)):
        raise ThreemaKeystorageError('key storage layout is not the supported password-protected form')
    salt, memory_bytes, iterations, parallelism = _argon2_parameters(argon_bytes)
    if isinstance(password, str):
        password = password.encode('utf-8')
    derived = hash_secret_raw(
        password, salt, time_cost=iterations, memory_cost=memory_bytes // 1024,
        parallelism=parallelism, hash_len=_NACL_KEY_LENGTH, type=Type.ID,
        version=_ARGON2_VERSION_1_3)
    try:
        intermediate = SecretBox(derived).decrypt(bytes(blob))
    except CryptoError as exc:
        raise ThreemaKeystorageError(
            'the password did not decrypt the key storage') from exc
    inner_layer = _read_fields(_after_header(intermediate)).get(1)
    if not isinstance(inner_layer, (bytes, bytearray)):
        raise ThreemaKeystorageError(
            'the key storage protects the inner layer with a remote secret, which is not supported')
    inner = _read_fields(_after_header(inner_layer))
    database_key = inner.get(3)
    if not isinstance(database_key, (bytes, bytearray)) or len(database_key) != _DATABASE_KEY_LENGTH:
        raise ThreemaKeystorageError('no 32-byte database key in the key storage')
    identity = ''
    identity_data = inner.get(1)
    if isinstance(identity_data, (bytes, bytearray)):
        raw_identity = _read_fields(identity_data).get(1)
        if isinstance(raw_identity, (bytes, bytearray)):
            identity = raw_identity.decode('utf-8', 'replace')
    return bytes(database_key), identity
