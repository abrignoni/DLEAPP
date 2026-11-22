"""Read an Exodus desktop wallet's stored secrets from its own files.

Exodus keeps the wallet under a folder named ``exodus.wallet`` inside a folder named
``Exodus``. The secret files use Exodus's own MIT-licensed container format, sourced here
from the published packages pinned to a commit or release:

- secure-container 2.0.0 (commit 4c005ec): the SECO container. Header (224 bytes), a
  SHA-256 checksum (32), a metadata block (256) and a length-prefixed blob. The metadata
  holds scrypt parameters (n=16384, r=8, p=1), the cipher name (aes-256-gcm), and two
  AES-256-GCM boxes: one wrapping a random 32-byte blob key with a key stretched from the
  passphrase, the other authenticating the blob. checksum = SHA-256(metadata +
  uint32be(len(blob)) + blob).
- seco-file 2.0.0 (commit 94441f8) and seco-rw 0.0.2: write/read a SECO file.
- seco-keyval 0.7.0 and buffer-noise 1.0.1: the framing the stored plaintext uses,
  ``expand(2**15)(gzip(payload))``. expand prefixes a uint32be length then the gzip data
  then random noise to a fixed 32768 bytes; shrink reads the length and slices it back. A
  seco-keyval store's own payload is JSON, but seed.seco's gunzipped payload is raw bytes,
  not that JSON; it only shares the framing.
- @exodus/bip39 1.1.1: entropy to mnemonic (BIP-39), and mnemonicToSeed = PBKDF2-HMAC-SHA512
  of the NFKD mnemonic with salt ``mnemonic`` over 2048 iterations, 64 bytes.

passphrase.json holds ``{"passphrase": <string>, "system": <bool>}``. On the known data,
a wallet where no password was set, ``system`` was true and the passphrase opened seed.seco
as stored; what ``system`` means is not sourced from Exodus code. On the known data seed.seco
decrypted to an 80-byte payload that is the 64-byte BIP-39 seed followed by the 16-byte
BIP-39 entropy. The recovery phrase is entropyToMnemonic(entropy); that it derives the
stored 64-byte seed is checked here by comparing mnemonicToSeed(phrase) with it.

No secret value is logged by this module. Callers put recovered values only into the
examiner-facing report.
"""

import hashlib
import json
import struct
import unicodedata
import zlib

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt as _scrypt

from scripts.exodus_bip39_english import WORDLIST

SECO_MAGIC = b'SECO'
_HEADER_LEN = 224
_CHECKSUM_LEN = 32
_METADATA_LEN = 256
_IV_LEN = 12
_TAG_LEN = 16
_KEY_LEN = 32

_VALID_ENTROPY_LENGTHS = (16, 20, 24, 28, 32)

# scrypt cost bounds. secure-container's default is n=16384, r=8, p=1 (about 16 MiB). A
# container carries its own scrypt parameters, so a crafted file could ask for far more work
# or memory than that. These bounds are checked before the KDF runs so an outsized request is
# refused instead of exhausting memory or CPU. scrypt's memory is about 128 * n * r bytes.
_SCRYPT_MAX_N = 2 ** 21
_SCRYPT_MAX_R = 64
_SCRYPT_MAX_P = 16
_SCRYPT_MAX_MEMORY = 512 * 1024 * 1024


class SecoError(Exception):
    """The container could not be read."""


class WrongPassphrase(SecoError):
    """The passphrase did not open the container."""


def _decode_metadata(metadata):
    offset = 0
    salt = metadata[offset:offset + 32]
    offset += 32
    n, r, p = struct.unpack('>III', metadata[offset:offset + 12])
    offset += 12
    cipher = metadata[offset:offset + 32].split(b'\x00', 1)[0].decode('ascii', 'replace')
    offset += 32
    blobkey_iv = metadata[offset:offset + _IV_LEN]
    offset += _IV_LEN
    blobkey_tag = metadata[offset:offset + _TAG_LEN]
    offset += _TAG_LEN
    blobkey_box = metadata[offset:offset + _KEY_LEN]
    offset += _KEY_LEN
    blob_iv = metadata[offset:offset + _IV_LEN]
    offset += _IV_LEN
    blob_tag = metadata[offset:offset + _TAG_LEN]
    return {
        'salt': salt, 'n': n, 'r': r, 'p': p, 'cipher': cipher,
        'blobkey_iv': blobkey_iv, 'blobkey_tag': blobkey_tag, 'blobkey_box': blobkey_box,
        'blob_iv': blob_iv, 'blob_tag': blob_tag,
    }


def is_seco_container(data):
    """True when the bytes begin with the SECO magic and are long enough to decode."""
    minimum = _HEADER_LEN + _CHECKSUM_LEN + _METADATA_LEN + 4
    return len(data) >= minimum and data[0:4] == SECO_MAGIC


def _check_scrypt_params(n, r, p):
    """Refuse scrypt parameters that are invalid or ask for too much work or memory."""
    if not (isinstance(n, int) and isinstance(r, int) and isinstance(p, int)):
        raise SecoError('scrypt parameters are not integers')
    if n < 2 or (n & (n - 1)) != 0 or n > _SCRYPT_MAX_N:
        raise SecoError(f'scrypt n out of range: {n}')
    if not 1 <= r <= _SCRYPT_MAX_R:
        raise SecoError(f'scrypt r out of range: {r}')
    if not 1 <= p <= _SCRYPT_MAX_P:
        raise SecoError(f'scrypt p out of range: {p}')
    if 128 * n * r > _SCRYPT_MAX_MEMORY:
        raise SecoError('scrypt parameters exceed the memory bound')


def validate_container(data):
    """Structural checks that need no passphrase, returning (metadata, blob).

    Verifies the SECO magic, the declared blob length and the SHA-256 checksum, so a
    non-SECO or corrupt file is rejected before any passphrase is tried. Raises SecoError.
    """
    if not is_seco_container(data):
        raise SecoError('not a SECO container')
    offset = _HEADER_LEN
    checksum = data[offset:offset + _CHECKSUM_LEN]
    offset += _CHECKSUM_LEN
    metadata = data[offset:offset + _METADATA_LEN]
    offset += _METADATA_LEN
    (blob_len,) = struct.unpack('>I', data[offset:offset + 4])
    offset += 4
    blob = data[offset:offset + blob_len]
    if len(blob) != blob_len:
        raise SecoError('blob is shorter than its declared length')
    expected = hashlib.sha256(metadata + struct.pack('>I', len(blob)) + blob).digest()
    if expected != checksum:
        raise SecoError('checksum does not match; data may be corrupted')
    return metadata, blob


def secure_container_decrypt(data, passphrase):
    """Decrypt a SECO container and return the plaintext bytes.

    Raises WrongPassphrase when the passphrase does not unwrap the blob key, and SecoError
    for a malformed or corrupted container.
    """
    metadata, blob = validate_container(data)
    meta = _decode_metadata(metadata)
    if meta['cipher'] != 'aes-256-gcm':
        raise SecoError(f"unsupported cipher {meta['cipher']!r}")
    _check_scrypt_params(meta['n'], meta['r'], meta['p'])
    if isinstance(passphrase, str):
        try:
            secret = passphrase.encode('utf-8')
        except UnicodeError as exc:
            raise WrongPassphrase('passphrase is not UTF-8 encodable') from exc
    else:
        secret = bytes(passphrase)
    try:
        key = _scrypt(secret, meta['salt'], _KEY_LEN, meta['n'], meta['r'], meta['p'])
    except (ValueError, OverflowError, MemoryError) as exc:
        raise SecoError(f'scrypt key derivation failed: {exc}') from exc
    try:
        blob_key = AES.new(key, AES.MODE_GCM, nonce=meta['blobkey_iv']).decrypt_and_verify(
            meta['blobkey_box'], meta['blobkey_tag'])
    except ValueError as exc:
        raise WrongPassphrase('passphrase did not unwrap the blob key') from exc
    try:
        return AES.new(blob_key, AES.MODE_GCM, nonce=meta['blob_iv']).decrypt_and_verify(
            blob, meta['blob_tag'])
    except ValueError as exc:
        raise SecoError('blob authentication failed') from exc


def _buffer_noise_shrink(buffer):
    if len(buffer) < 4:
        raise SecoError('noise buffer too short for its length prefix')
    (length,) = struct.unpack('>I', buffer[0:4])
    if 4 + length > len(buffer):
        raise SecoError('noise length runs past the buffer')
    return buffer[4:4 + length]


def _gunzip_bounded(gzipped, limit):
    """Gunzip to at most ``limit`` bytes, raising SecoError past it or on bad data.

    The gzip output is decoded with a cap rather than all at once, so an authenticated
    container whose payload decompresses to far more than a wallet ever holds cannot exhaust
    memory before a caller checks the length.
    """
    decompressor = zlib.decompressobj(zlib.MAX_WBITS | 16)
    try:
        out = decompressor.decompress(gzipped, limit + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise SecoError('store payload is not gzip') from exc
    if len(out) > limit:
        raise SecoError('store payload exceeds the size limit')
    if not decompressor.eof:
        raise SecoError('store payload did not end within the size limit')
    # A seco store holds exactly one gzip member. Reject a second member or trailing bytes,
    # so a first member cannot be read as the whole payload with more data hidden after it.
    if decompressor.unused_data or decompressor.unconsumed_tail:
        raise SecoError('store payload has data after the gzip member')
    return out


def seco_store_payload(data, passphrase):
    """Decrypt a seco-rw store file and return its gunzipped payload bytes.

    A wallet store is small (seed.seco's payload is 80 bytes; storage.seco's is a few
    kilobytes), so the gunzip is bounded to 1 MiB.
    """
    plaintext = secure_container_decrypt(data, passphrase)
    inner = _buffer_noise_shrink(plaintext)
    return _gunzip_bounded(inner, 1024 * 1024)


def entropy_to_mnemonic(entropy):
    """BIP-39 entropy (16, 20, 24, 28 or 32 bytes) to its space-joined mnemonic."""
    if len(entropy) not in _VALID_ENTROPY_LENGTHS:
        raise ValueError('invalid entropy length')
    checksum = hashlib.sha256(entropy).digest()
    checksum_bits = len(entropy) // 4
    bits = ''.join(f'{byte:08b}' for byte in entropy)
    bits += ''.join(f'{byte:08b}' for byte in checksum)[:checksum_bits]
    return ' '.join(WORDLIST[int(bits[i:i + 11], 2)] for i in range(0, len(bits), 11))


def mnemonic_to_seed(mnemonic, password=''):
    """BIP-39 mnemonic to its 64-byte seed (PBKDF2-HMAC-SHA512, 2048 iterations)."""
    normalized = unicodedata.normalize('NFKD', mnemonic)
    salt = unicodedata.normalize('NFKD', 'mnemonic' + password).encode('utf-8')
    return hashlib.pbkdf2_hmac('sha512', normalized.encode('utf-8'), salt, 2048, 64)


def parse_seed_payload(payload):
    """Split an Exodus seed payload into seed, entropy, mnemonic and a verified flag.

    The payload is the 64-byte BIP-39 seed followed by the 16-byte BIP-39 entropy. The
    mnemonic is derived from the entropy and verified by re-deriving the seed from it. An
    unexpected length yields ``recognised`` False and no secrets.
    """
    result = {'length': len(payload), 'recognised': False, 'seed': None,
              'mnemonic': None, 'verified': False}
    if len(payload) == 80:
        seed = payload[0:64]
        entropy = payload[64:80]
        mnemonic = entropy_to_mnemonic(entropy)
        result.update(recognised=True, seed=seed, mnemonic=mnemonic,
                      verified=(mnemonic_to_seed(mnemonic) == seed))
    return result


def read_passphrase_file(raw_bytes):
    """Return (passphrase, system_flag) from passphrase.json bytes.

    passphrase is the string or None. system_flag is only a JSON boolean: True or False
    when the field is a bool, and None when it is missing or any other type, so a caller
    cannot read a string such as ``"false"`` as a set flag.
    """
    try:
        parsed = json.loads(raw_bytes)
    except (ValueError, TypeError, RecursionError):
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    passphrase = parsed.get('passphrase')
    system = parsed.get('system')
    if not isinstance(passphrase, str):
        passphrase = None
    else:
        # A JSON string can hold an unpaired surrogate that strict UTF-8 cannot encode.
        # Treat such a stored passphrase as unavailable so the supplied-password path still runs.
        try:
            passphrase.encode('utf-8')
        except UnicodeError:
            passphrase = None
    if not isinstance(system, bool):
        system = None
    return passphrase, system
