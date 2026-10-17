"""Small synthetic BitLocker metadata images; never contain casework or real keys."""

import hashlib
import io
import json
import struct
import uuid
import zlib

from scripts.bitlocker_metadata import capture_ranges


VOLUME_GUID = uuid.UUID('11111111-2222-3333-4444-555555555555')
TPM_GUID = uuid.UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
RECOVERY_GUID = uuid.UUID('99999999-8888-7777-6666-555555555555')
OFFSETS = (4096, 69632, 135168)
RAW_TIME = 133801632000000000  # 2025-01-01 00:00:00 UTC


def datum(role, kind, value, version=1):
    return struct.pack('<HHHH', len(value) + 8, role, kind, version) + value


def tpm_value(bitmap=0x805, inner=None):
    """A shape-valid opaque TPM payload. It is not a usable TPM sealed object."""
    selected = bitmap if inner is None else inner
    return (struct.pack('<I', bitmap) + b'\x00\x04TEST\x00\x04FAKE'
            + b'\x00\x20' + bytes(range(32)) + b'\x03' + selected.to_bytes(3, 'little'))


def vmk(identifier, protection, properties, stamp=RAW_TIME):
    return datum(2, 8, identifier.bytes_le + struct.pack('<QHH', stamp, 0, protection) + properties)


def block(bitmap=0x805, counter=1, bad_crc=False, broken_entry=False,
          unknown=False, clear=False, inner=None, protectors=None):
    body = datum(7, 2, 'SYNTHETIC TEST VOLUME\x00'.encode('utf-16-le'))
    if protectors is None:
        body += vmk(TPM_GUID, 0x100, datum(0, 6, tpm_value(bitmap, inner)))
        # Opaque bytes only: no real recovery password or encrypted VMK.
        body += vmk(RECOVERY_GUID, 0x800, datum(0, 5, bytes(40)))
    else:
        for identifier, protection, properties in protectors:
            body += vmk(identifier, protection, properties)
    if clear:
        body += vmk(uuid.UUID(int=42), 0, datum(0, 1, bytes(36)))
    if unknown:
        body += datum(0x1234, 0x5678, b'UNINTERPRETED')
    if broken_entry:
        body += b'\x04\x00\x02\x00\x08\x00\x01\x00'
    dataset_size = 48 + len(body)
    info_size = (64 + dataset_size + 15) & ~15
    out = bytearray(65536)
    struct.pack_into('<8sHHHHQIIQQQQ', out, 0, b'-FVE-FS-', info_size // 16,
                     2, 4, 4, 1048576, 0, 16, *OFFSETS, 1040384)
    struct.pack_into('<IIII16sIIQ', out, 64, dataset_size, 1, 48, dataset_size,
                     VOLUME_GUID.bytes_le, counter, 0x8005, RAW_TIME)
    out[112:112 + len(body)] = body
    checksum = zlib.crc32(out[:info_size]) & 0xffffffff
    struct.pack_into('<HHI', out, info_size, 8, 1, checksum ^ int(bad_crc))
    return bytes(out)


def volume(bitmap=0x805, base=0, copies=None, truncated=None, **kwargs):
    """An unmounted metadata-only volume, optionally in a synthetic MBR partition."""
    raw = bytearray(base + 1048576)
    if base:
        struct.pack_into('<B3sB3sII', raw, 446, 0, bytes(3), 7, bytes(3), base // 512, 2048)
        raw[510:512] = b'\x55\xaa'
    head = bytearray(512)
    head[:11] = b'\xeb\x58\x90-FVE-FS-'
    struct.pack_into('<H', head, 11, 512)
    head[13] = 8
    head[160:176] = bytes.fromhex('3bd66749292ed84a8399f6a339e3d001')
    struct.pack_into('<QQQ', head, 176, *OFFSETS)
    head[510:512] = b'\x55\xaa'
    raw[base:base + 512] = head
    blocks = copies or [block(bitmap, **kwargs)] * 3
    for off, payload in zip(OFFSETS, blocks):
        raw[base + off:base + off + len(payload)] = payload
    return bytes(raw if truncated is None else raw[:base + truncated])


def capture(raw, base=0, source='synthetic.img', volume_name='lba0'):
    handle = io.BytesIO(raw)

    def read_at(offset, length):
        handle.seek(offset)
        return handle.read(length)

    return capture_ranges(read_at, base, 1048576, len(raw), source, volume_name)


def capture_result(raw, base=0):
    files = capture(raw, base)
    manifest = json.loads(files['ranges.json'])
    return manifest, {name: data for name, data in files.items() if name != 'ranges.json'}


def write_capture(folder, raw, base=0, source='synthetic.img', volume_name='lba0'):
    """Write byte ranges as test input, never to a source image."""
    target = folder / volume_name / '$BitLocker'
    target.mkdir(parents=True, exist_ok=True)
    files = capture(raw, base, source, volume_name)
    for name, data in files.items():
        (target / name).write_bytes(data)
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def protector_variants():
    """Synthetic labels/properties; not Windows-written or decryptable TPM objects."""
    codes = (0, 0x100, 0x200, 0x300, 0x500, 0x700, 0x800, 0x2000, 0x1234)
    return [(uuid.UUID(int=0x1000 + i), code,
             datum(0, 6, tpm_value(0x880)) if code in (0x100, 0x300, 0x500, 0x700)
             else datum(0, 5, bytes(40))) for i, code in enumerate(codes)]
