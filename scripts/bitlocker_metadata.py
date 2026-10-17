"""Read-only BitLocker metadata inventory; no key unsealing or password recovery.

The report uses CRC-valid, structurally bounded v2 information blocks. Each copy
keeps its own findings; the first valid copy supplies the volume summary, without
claiming it is newer than the others. See admin/docs/bitlocker_metadata.md.
"""

import datetime
import hashlib
import json
import struct
import uuid
import zlib


SIGNATURE = b'-FVE-FS-'
INFORMATION_GUID = bytes.fromhex('3bd66749292ed84a8399f6a339e3d001')
EOW_GUID = bytes.fromhex('3b4da89280dd0e4d9e4eb1e3284eaed8')
CAPTURE_SCHEMA = 'dleapp.bitlocker.ranges.v1'
CAPTURE_FOLDER = '$BitLocker'
CAPTURE_MANIFEST = 'ranges.json'
BLOCK_LIMIT = 65536
METHODS = {
    0x0000: 'None',
    0x8000: 'AES-128-CBC with Elephant diffuser',
    0x8001: 'AES-256-CBC with Elephant diffuser',
    0x8002: 'AES-128-CBC', 0x8003: 'AES-256-CBC',
    0x8004: 'AES-128-XTS', 0x8005: 'AES-256-XTS',
}
PROTECTORS = {
    0x0000: 'Clear key', 0x0100: 'TPM', 0x0200: 'External key',
    0x0300: 'TPM and external startup key', 0x0500: 'TPM and PIN',
    0x0700: 'TPM, PIN and external startup key',
    0x0800: 'Recovery password', 0x2000: 'Password',
}
STATES = {1: 'Decrypted', 2: 'Conversion in progress (dirty)',
          3: 'Paused', 4: 'Encrypted', 5: 'Conversion in progress'}
VALUE_TYPES = {
    0: 'Erased', 1: 'Key', 2: 'UTF-16 string', 3: 'Stretch key',
    4: 'Use key', 5: 'AES-CCM encrypted key', 6: 'TPM encoded key',
    7: 'Validation', 8: 'Volume master key information', 9: 'External key information',
    10: 'Update', 11: 'Error', 12: 'Asymmetric encrypted key', 13: 'Exported key',
    14: 'Public key information', 15: 'Virtualization information',
    21: 'Backup information',
}
PCR_MEANINGS = {
    0: 'Core firmware code', 1: 'Core firmware data and configuration',
    2: 'Additional firmware / UEFI driver code',
    3: 'Additional firmware data and configuration',
    4: 'Boot manager code', 5: 'Boot configuration / GPT partition table',
    6: 'Platform state / resume events', 7: 'Secure Boot policy',
    8: 'Operating-system defined', 9: 'Operating-system defined',
    10: 'Operating-system defined', 11: 'BitLocker access control',
    12: 'Windows data and volatile events', 13: 'Windows boot-module details',
    14: 'Windows boot authorities', 15: 'Operating-system defined',
    16: 'Debug', 17: 'Dynamic root of trust', 18: 'Dynamic root of trust',
    19: 'Dynamic root of trust', 20: 'Dynamic root of trust',
    21: 'Dynamic root of trust', 22: 'Dynamic root of trust',
    23: 'Application support',
}
_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)


def filetime(value):
    """A stored FILETIME as UTC, or None for zero / out-of-range values."""
    if not value:
        return None
    try:
        return _EPOCH + datetime.timedelta(microseconds=value // 10)
    except OverflowError:
        return None


def volume_header(data):
    """Recognise the header and return its three volume-relative offsets."""
    if len(data) < 512:
        raise ValueError('volume header is shorter than 512 bytes')
    if data[3:11] == SIGNATURE:
        if data[:3] == b'\xeb\x52\x90':
            return {'layout': 'Windows Vista (not decoded)', 'offsets': (),
                    'sector_size': struct.unpack_from('<H', data, 11)[0]}
        if data[160:176] not in (INFORMATION_GUID, EOW_GUID):
            raise ValueError('BitLocker recognition GUID is not supported')
        layout = 'Encrypt-on-Write' if data[160:176] == EOW_GUID else 'Windows 7 and later'
        offset = 176
    elif data[3:11] == b'MSWIN4.1' and data[424:440] == INFORMATION_GUID:
        layout, offset = 'BitLocker To Go', 440
    else:
        raise ValueError('not a recognised BitLocker volume header')
    return {'layout': layout, 'offsets': struct.unpack_from('<QQQ', data, offset),
            'sector_size': struct.unpack_from('<H', data, 11)[0]}


def capture_ranges(read_at, base, volume_size, image_size, source_image, volume_name):
    """Capture bounded on-image ranges and a provenance manifest.

    read_at(offset, length) reads the original logical image, before a BitLocker
    decryption wrapper can zero the metadata. The manifest is generated, not an
    on-disk file; .bin members preserve the bytes returned by the image reader.
    """
    files = {}
    manifest = {'schema': CAPTURE_SCHEMA, 'source_image': source_image,
                'volume_name': volume_name, 'volume_offset': base,
                'volume_size': volume_size, 'image_size': image_size,
                'ranges': []}

    def take(name, relative, wanted):
        available = min(max(0, volume_size - relative),
                        max(0, image_size - base - relative), wanted)
        record = {'file': name, 'volume_offset': relative,
                  'image_offset': base + relative, 'requested_bytes': wanted,
                  'captured_bytes': 0, 'status': 'outside captured image or volume'}
        if available:
            try:
                data = bytes(read_at(base + relative, available))
                if len(data) > available:
                    raise ValueError('reader returned more than requested')
                files[name] = data
                record.update(captured_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              status='captured' if len(data) == wanted else 'partial capture')
            except (OSError, ValueError, OverflowError) as exc:
                record['status'] = f'read failed: {type(exc).__name__}'
        manifest['ranges'].append(record)
        return files.get(name, b'')

    head = take('volume-header.bin', 0, 512)
    header = volume_header(head)
    manifest['layout'] = header['layout']
    for number, offset in enumerate(header['offsets'], 1):
        if offset:
            take(f'metadata-{number}.bin', offset, BLOCK_LIMIT)
        else:
            manifest['ranges'].append({'file': f'metadata-{number}.bin',
                                      'volume_offset': 0, 'image_offset': base,
                                      'requested_bytes': BLOCK_LIMIT, 'captured_bytes': 0,
                                      'status': 'metadata pointer is zero'})
    files[CAPTURE_MANIFEST] = json.dumps(manifest, sort_keys=True, indent=2).encode('utf-8')
    return files


def tpm_policy(data):
    """Stored outer bitmap plus the inner TPM2-shaped selection when it fits.

    The inner layout is two length-prefixed opaque blobs, a length-prefixed PCR
    digest, and a one-byte-length PCR selection. The two blobs are not unsealed.
    A disagreement is reported and is never reduced to an apparently good policy.
    """
    if len(data) < 4:
        return {'status': 'TPM entry is shorter than its outer PCR bitmap',
                'bitmap': None, 'pcrs': [], 'digest': ''}
    bitmap = int.from_bytes(data[:4], 'little')
    result = {'status': 'outer bitmap only; inner TPM layout not decoded',
              'bitmap': bitmap, 'pcrs': [n for n in range(32) if bitmap & (1 << n)],
              'digest': ''}
    position = 4
    try:
        for _ in range(2):
            size = int.from_bytes(data[position:position + 2], 'big')
            if len(data[position:position + 2]) != 2 or not size:
                return result
            position += 2 + size
            if position > len(data):
                return result
        digest_size = int.from_bytes(data[position:position + 2], 'big')
        if len(data[position:position + 2]) != 2 or digest_size not in (20, 32, 48, 64):
            return result
        position += 2
        digest = data[position:position + digest_size]
        position += digest_size
        if len(digest) != digest_size or position >= len(data):
            return result
        select_size = data[position]
        position += 1
        if not 1 <= select_size <= 4 or position + select_size != len(data):
            return result
        inner = int.from_bytes(data[position:position + select_size], 'little')
        result['digest'] = digest.hex()
        if inner != bitmap:
            result.update(status='outer and inner PCR bitmaps disagree', pcrs=[])
        else:
            result['status'] = 'outer and inner PCR bitmaps agree'
    except (IndexError, OverflowError):
        return result
    return result


def _guid(data):
    return str(uuid.UUID(bytes_le=bytes(data)))


def _entries(data, start, end, block, parent='', depth=0):
    """Bounded datum traversal. Unknown datums retain type, size and offset."""
    position = start
    while position < end:
        if not any(data[position:end]):
            break
        if depth > 8 or len(block['entries']) >= 8192:
            block['issues'].append('metadata entry depth or count limit reached')
            return
        if position + 8 > end:
            block['issues'].append(f'truncated entry header at block byte {position}')
            return
        size, role, kind, version = struct.unpack_from('<HHHH', data, position)
        if size < 8 or position + size > end:
            block['issues'].append(f'invalid entry bounds at block byte {position}')
            return
        value = data[position + 8:position + size]
        entry = {'offset': block['offset'] + position, 'size': size,
                 'role': role, 'type': kind, 'version': version, 'parent': parent}
        block['entries'].append(entry)
        if role == 7 and kind == 2:
            block['description'] = value.decode('utf-16-le', 'replace').rstrip('\x00')
        if kind == 8:
            if len(value) < 28:
                block['issues'].append(f'truncated VMK entry at block byte {position}')
            else:
                identifier = _guid(value[:16])
                code = struct.unpack_from('<H', value, 26)[0]
                protector = {'id': identifier, 'type': code, 'offset': entry['offset'],
                             'modified_raw': struct.unpack_from('<Q', value, 16)[0],
                             'policies': []}
                # Parse nested metadata even for unknown protection codes.
                block['protectors'].append(protector)
                _entries(data, position + 36, position + size, block, identifier, depth + 1)
        elif kind == 6 and parent:
            policy = tpm_policy(value)
            policy['offset'] = entry['offset'] + 8
            protector = next((p for p in reversed(block['protectors']) if p['id'] == parent), None)
            if protector is not None:
                protector['policies'].append(policy)
        position += size


def parse_block(data, offset, number):
    """Validate one v2 information block; no semantic parsing after a bad CRC."""
    block = {'number': number, 'offset': offset, 'captured': len(data),
             'status': 'not captured', 'issues': [], 'entries': [], 'protectors': [],
             'description': '', 'valid': False}
    if not data:
        return block
    if len(data) < 112 or data[:8] != SIGNATURE:
        block['status'] = 'invalid or truncated metadata header'
        return block
    block['version'] = struct.unpack_from('<H', data, 10)[0]
    if block['version'] != 2:
        block['status'] = f"unsupported metadata version {block['version']}"
        return block
    length = struct.unpack_from('<H', data, 8)[0] * 16
    block['information_size'] = length
    if length < 112 or length + 8 > len(data) or length + 8 > BLOCK_LIMIT:
        block['status'] = 'information or validation extends beyond captured block'
        return block
    block['crc_stored'] = struct.unpack_from('<I', data, length + 4)[0]
    block['crc_computed'] = zlib.crc32(data[:length]) & 0xffffffff
    block['information_sha256'] = hashlib.sha256(data[:length]).hexdigest()
    if block['crc_stored'] != block['crc_computed']:
        block['status'] = 'CRC32 mismatch'
        return block
    size, version, header_size, size_copy = struct.unpack_from('<IIII', data, 64)
    block.update(dataset_size=size, dataset_version=version)
    if version != 1 or header_size < 48 or size < header_size or 64 + size > length:
        block['status'] = 'invalid or unsupported dataset bounds / version'
        return block
    if size != size_copy:
        block['status'] = 'dataset size and size copy disagree'
        return block
    block.update(volume_id=_guid(data[80:96]), counter=struct.unpack_from('<I', data, 96)[0],
                 method_raw=struct.unpack_from('<I', data, 100)[0],
                 created_raw=struct.unpack_from('<Q', data, 104)[0],
                 current_state=struct.unpack_from('<H', data, 12)[0],
                 next_state=struct.unpack_from('<H', data, 14)[0],
                 state_offset=struct.unpack_from('<Q', data, 16)[0],
                 state_size=struct.unpack_from('<I', data, 24)[0],
                 virtualized_sectors=struct.unpack_from('<I', data, 28)[0],
                 virtualized_offset=struct.unpack_from('<Q', data, 56)[0],
                 dataset_sha256=hashlib.sha256(data[64:64 + size]).hexdigest())
    _entries(data, 64 + header_size, 64 + size, block)
    block['valid'] = not block['issues']
    block['status'] = 'CRC32 and structure valid' if block['valid'] else 'CRC32 valid; malformed entries'
    return block


def analyze_capture(manifest, files):
    """Read a generated range manifest and its byte-preserving .bin members."""
    if not isinstance(manifest, dict) or manifest.get('schema') != CAPTURE_SCHEMA:
        raise ValueError('unrecognised BitLocker range-manifest schema')
    for field in ('volume_offset', 'volume_size', 'image_size'):
        value = manifest.get(field)
        if type(value) is not int or not 0 <= value < (1 << 64):
            raise ValueError(f'invalid {field} in range manifest')
    header = volume_header(files.get('volume-header.bin', b''))
    if manifest.get('layout') != header['layout']:
        raise ValueError('range manifest and volume header disagree on layout')
    records = manifest.get('ranges')
    if not isinstance(records, list) or len(records) > 4:
        raise ValueError('invalid range list')
    allowed = {'volume-header.bin', 'metadata-1.bin', 'metadata-2.bin', 'metadata-3.bin'}
    ranges = {}
    for record in records:
        if not isinstance(record, dict) or record.get('file') not in allowed:
            raise ValueError('invalid range record')
        name = record['file']
        if name in ranges:
            raise ValueError('duplicate range filename')
        for key in ('volume_offset', 'image_offset', 'captured_bytes', 'requested_bytes'):
            if type(record.get(key)) is not int or not 0 <= record[key] < (1 << 64):
                raise ValueError('invalid range coordinates')
        if record['captured_bytes'] > BLOCK_LIMIT:
            raise ValueError('captured range exceeds the size limit')
        ranges[name] = record
    head_range = ranges.get('volume-header.bin', {})
    if head_range.get('volume_offset') != 0 or head_range.get('image_offset') != manifest['volume_offset']:
        raise ValueError('volume header range offset is inconsistent')
    for key in ('source_image', 'volume_name'):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise ValueError(f'invalid {key}')
    for name, record in ranges.items():
        if record['captured_bytes'] and name not in files:
            raise ValueError(f'captured range missing: {name}')
    for name, data in files.items():
        if name == CAPTURE_MANIFEST:
            continue
        record = ranges.get(name)
        if record is None or record.get('captured_bytes') != len(data):
            raise ValueError(f'range size does not match {name}')
        if hashlib.sha256(data).hexdigest() != record.get('sha256'):
            raise ValueError(f'range hash does not match {name}')
    copies = []
    for number, offset in enumerate(header['offsets'], 1):
        name = f'metadata-{number}.bin'
        record = ranges.get(name, {})
        if record.get('volume_offset') != offset:
            raise ValueError('range manifest and volume header disagree on metadata offset')
        if record.get('image_offset') != manifest['volume_offset'] + offset:
            raise ValueError('range manifest image offset is inconsistent')
        block = parse_block(files.get(name, b''), offset, number)
        block['capture_status'] = record.get('status', 'range not listed')
        copies.append(block)
    selected = next((b for b in copies if b['valid']), None)
    return {'manifest': manifest, 'header': header, 'copies': copies, 'selected': selected,
            'copies_agree': len({b['dataset_sha256'] for b in copies if b['valid']}) <= 1}
