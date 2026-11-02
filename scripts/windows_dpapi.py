"""Clean-room offline DPAPI chain for Windows: boot key, DPAPI_SYSTEM, SYSTEM master key, blob.
Written from the documented registry/DPAPI structures and algorithms (not from any GPL source),
validated against real Windows data. PyCryptodome + python-registry only.

The DPAPI master-key KDF is Microsoft's iterated-HMAC derivation, which folds each round into the
running accumulator (T ^= HMAC(pwd, T)); it is not RFC 2898 PBKDF2, and standard PBKDF2 does not
decrypt real master keys. CryptDeriveKey follows the documented ipad/opad expansion, used only when
the hash output is shorter than the key.
"""
import hashlib
import hmac
import struct

from Crypto.Cipher import AES, DES3
from Registry import Registry

_PERM = [0x8, 0x5, 0x4, 0x2, 0xb, 0x9, 0xd, 0x3, 0x0, 0x6, 0x1, 0xc, 0xe, 0xa, 0xf, 0x7]
SHA1, SHA512 = 0x8004, 0x800e
DES3_ALG, AES256 = 0x6603, 0x6610
_HNAME = {SHA1: 'sha1', SHA512: 'sha512'}
_HLEN = {SHA1: 20, SHA512: 64}
_BLOCK = {SHA1: 64, SHA512: 128}
_CIPHER = {AES256: (32, 16), DES3_ALG: (24, 8)}


def get_bootkey(system_path):
    with open(system_path, 'rb') as handle:
        reg = Registry.Registry(handle)
        cs = 'ControlSet%03d' % reg.open('Select').value('Current').value()
        lsa = reg.open(cs + '\\Control\\Lsa')
        return _bootkey_from_lsa(lsa)


def _bootkey_from_lsa(lsa):
    # python-registry exposes the key class name only on the underlying NK record
    scrambled = b''.join(bytes.fromhex(lsa.subkey(n)._nkrecord.classname())  # pylint: disable=protected-access
                         for n in ('JD', 'Skew1', 'GBG', 'Data'))
    return bytes(scrambled[_PERM[i]] for i in range(16))


def _aes_ecb_blocks(key, data):
    out = b''
    for i in range(0, len(data), 16):
        out += AES.new(key, AES.MODE_CBC, b'\x00' * 16).decrypt(data[i:i + 16].ljust(16, b'\x00'))
    return out


def _sha256_rounds(key, value, rounds=1000):
    h = hashlib.sha256()
    h.update(key)
    for _ in range(rounds):
        h.update(value)
    return h.digest()


def get_dpapi_system(security_path, bootkey):
    with open(security_path, 'rb') as handle:
        reg = Registry.Registry(handle)
        pol = reg.open('Policy\\PolEKList').value('').value()
        lsa_key = _aes_ecb_blocks(_sha256_rounds(bootkey, pol[28:60]), pol[60:])[68:100]
        rec = reg.open('Policy\\Secrets\\DPAPI_SYSTEM\\CurrVal').value('').value()
    plain = _aes_ecb_blocks(_sha256_rounds(lsa_key, rec[28:60]), rec[60:])
    length = struct.unpack('<L', plain[:4])[0]
    return plain[16:16 + length]


def _xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _dpapi_kdf(password, salt, dklen, iterations, hname):
    """Microsoft's iterated-HMAC key derivation (folds each round into the accumulator)."""
    out = b''
    i = 1
    while len(out) < dklen:
        t = hmac.new(password, salt + struct.pack('!L', i), hname).digest()
        u = t
        for _ in range(iterations - 1):
            u = hmac.new(password, t, hname).digest()
            t = _xor(t, u)
        out += t
        i += 1
    return out[:dklen]


def _crypt_derive_key(digest, alg_hash, need):
    """CryptDeriveKey: the hash output when it is long enough, else the ipad/opad expansion."""
    hname, block = _HNAME[alg_hash], _BLOCK[alg_hash]
    if len(digest) > block:
        digest = hashlib.new(hname, digest).digest()
    if len(digest) >= need:
        return digest
    padded = digest.ljust(block, b'\x00')
    ipad = bytes(b ^ 0x36 for b in padded)
    opad = bytes(b ^ 0x5c for b in padded)
    return hashlib.new(hname, ipad).digest() + hashlib.new(hname, opad).digest()


def _cbc_decrypt(alg_crypt, key, iv, data):
    if alg_crypt == AES256:
        return AES.new(key, AES.MODE_CBC, iv).decrypt(data)
    return DES3.new(key, DES3.MODE_CBC, iv).decrypt(data)


def decrypt_master_key(mk_file, candidates):
    """The 64-byte master key from a master-key file, using the first credential that verifies."""
    mklen = struct.unpack('<Q', mk_file[96:104])[0]
    mk = mk_file[128:128 + mklen]
    salt, rounds = mk[4:20], struct.unpack('<L', mk[20:24])[0]
    alg_hash, alg_crypt = struct.unpack('<L', mk[24:28])[0], struct.unpack('<L', mk[28:32])[0]
    ciphertext = mk[32:]
    key_len, iv_len = _CIPHER[alg_crypt]
    for pwdhash in candidates:
        dk = _dpapi_kdf(pwdhash, salt, key_len + iv_len, rounds, _HNAME[alg_hash])
        clear = _cbc_decrypt(alg_crypt, dk[:key_len], dk[key_len:key_len + iv_len], ciphertext)
        hmac_salt, key, stored = clear[:16], clear[-64:], clear[16:16 + _HLEN[alg_hash]]
        tmp = hmac.new(pwdhash, hmac_salt, _HNAME[alg_hash]).digest()
        if hmac.new(tmp, key, _HNAME[alg_hash]).digest() == stored:
            return key
    return None


def _u32(b, o):
    return struct.unpack('<L', b[o:o + 4])[0]


def parse_blob_mkguid(raw):
    b = raw[24:40]
    d1, d2, d3 = struct.unpack('<LHH', b[:8])
    return '%08x-%04x-%04x-%s-%s' % (d1, d2, d3, b[8:10].hex(), b[10:16].hex())


def _session_key_t1(masterkey, nonce, alg_hash, verif=None):
    """Microsoft's non-RFC session key (older blobs): inner pad over the nonce, outer pad over that."""
    hname, block = _HNAME[alg_hash], _BLOCK[alg_hash]
    mk = hashlib.sha1(masterkey).digest() if len(masterkey) > 20 else masterkey
    mk = mk.ljust(block, b'\x00')
    ipad = bytes(mk[i] ^ 0x36 for i in range(block))
    opad = bytes(mk[i] ^ 0x5c for i in range(block))
    inner = hashlib.new(hname, ipad); inner.update(nonce)
    outer = hashlib.new(hname, opad); outer.update(inner.digest())
    if verif is not None:
        outer.update(verif)
    return outer.digest()


def _session_key_t2(masterkey, nonce, alg_hash, verif=None):
    """RFC-HMAC session key (newer blobs)."""
    mk = hashlib.sha1(masterkey).digest() if len(masterkey) > 20 else masterkey
    d = hmac.new(mk, nonce, _HNAME[alg_hash])
    if verif is not None:
        d.update(verif)
    return d.digest()


def decrypt_blob(raw, master_key):
    """The cleartext of a DPAPI blob with no optional entropy, or None if neither session type verifies."""
    blob_start = 20
    o = 44  # version(4)+provider(16)+mkversion(4)+mkguid(16)+flags(4)
    desc_len = _u32(raw, o); o += 4 + desc_len
    alg_crypt = _u32(raw, o); o += 8  # CryptAlgo + keyLen
    salt_len = _u32(raw, o); o += 4
    salt = raw[o:o + salt_len]; o += salt_len
    strong_len = _u32(raw, o); o += 4 + strong_len
    alg_hash = _u32(raw, o); o += 8  # HashAlgo + hashLen
    hmac_len = _u32(raw, o); o += 4
    hmac_val = raw[o:o + hmac_len]; o += hmac_len
    data_len = _u32(raw, o); o += 4
    data = raw[o:o + data_len]; o += data_len
    verif = raw[blob_start:o]
    key_len, iv_len = _CIPHER[alg_crypt]
    for algo in (_session_key_t1, _session_key_t2):
        session = algo(master_key, salt, alg_hash)
        derived = _crypt_derive_key(session, alg_hash, key_len + iv_len)
        clear = _cbc_decrypt(alg_crypt, derived[:key_len], b'\x00' * iv_len, data)
        pad = clear[-1] if clear else 0
        if 0 < pad <= 16:
            clear = clear[:-pad]
        if algo(master_key, hmac_val, alg_hash, verif) == raw[o + 4:o + 4 + _u32(raw, o)]:
            return clear
    return None
