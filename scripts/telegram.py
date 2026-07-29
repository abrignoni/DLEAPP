"""Offline readers for Telegram Desktop's native ``tdata`` storage.

The helpers intentionally expose account and evidence metadata, never MTProto
authorization keys or the decrypted local storage key.

Format references:
* Telegram Desktop ``storage/localstorage.cpp`` and ``storage_account.cpp``
* Desktop App Toolkit ``lib_storage/storage/cache``
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path

from Crypto.Cipher import AES


class TelegramDataError(ValueError):
    """Raised when a Telegram storage object cannot be validated or decoded."""


class QtReader:
    """Small big-endian QDataStream (Qt 5.1) reader."""

    def __init__(self, data, offset=0):
        self.data = memoryview(data)
        self.pos = offset

    def remaining(self):
        return len(self.data) - self.pos

    def raw(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise TelegramDataError("Truncated QDataStream value")
        value = bytes(self.data[self.pos:self.pos + size])
        self.pos += size
        return value

    def u8(self):
        return self.raw(1)[0]

    def i8(self):
        return struct.unpack(">b", self.raw(1))[0]

    def u16(self):
        return struct.unpack(">H", self.raw(2))[0]

    def i32(self):
        return struct.unpack(">i", self.raw(4))[0]

    def u32(self):
        return struct.unpack(">I", self.raw(4))[0]

    def u64(self):
        return struct.unpack(">Q", self.raw(8))[0]

    def qbytes(self):
        size = self.u32()
        if size == 0xFFFFFFFF:
            return b""
        return self.raw(size)

    def qstring(self):
        size = self.u32()
        if size == 0xFFFFFFFF:
            return ""
        if size % 2:
            raise TelegramDataError("Invalid QString byte length")
        return self.raw(size).decode("utf-16-be", errors="replace")


def _aes_ige_decrypt(ciphertext, key, iv):
    if len(ciphertext) % 16 or len(iv) != 32:
        raise TelegramDataError("Invalid AES-IGE input size")
    aes = AES.new(key, AES.MODE_ECB)
    previous_cipher = iv[:16]
    previous_plain = iv[16:]
    result = bytearray()
    for offset in range(0, len(ciphertext), 16):
        cipher_block = ciphertext[offset:offset + 16]
        mixed = bytes(a ^ b for a, b in zip(cipher_block, previous_plain))
        decoded = aes.decrypt(mixed)
        plain_block = bytes(a ^ b for a, b in zip(decoded, previous_cipher))
        result.extend(plain_block)
        previous_cipher = cipher_block
        previous_plain = plain_block
    return bytes(result)


def _oldmtp_aes(key, message_key):
    x = 8
    sha1_a = hashlib.sha1(message_key[:16] + key[x:x + 32]).digest()
    sha1_b = hashlib.sha1(
        key[x + 32:x + 48] + message_key[:16] + key[x + 48:x + 64]
    ).digest()
    sha1_c = hashlib.sha1(key[x + 64:x + 96] + message_key[:16]).digest()
    sha1_d = hashlib.sha1(message_key[:16] + key[x + 96:x + 128]).digest()
    aes_key = sha1_a[:8] + sha1_b[8:20] + sha1_c[4:16]
    aes_iv = sha1_a[8:20] + sha1_b[:8] + sha1_c[16:20] + sha1_d[:8]
    return aes_key, aes_iv


def decrypt_local(encrypted, key):
    """Integrity-check and decrypt a Telegram local encrypted QByteArray."""
    if len(encrypted) <= 16 or len(encrypted) % 16:
        raise TelegramDataError("Invalid Telegram encrypted blob size")
    message_key = encrypted[:16]
    aes_key, aes_iv = _oldmtp_aes(key, message_key)
    clear = _aes_ige_decrypt(encrypted[16:], aes_key, aes_iv)
    if hashlib.sha1(clear).digest()[:16] != message_key:
        raise TelegramDataError("Telegram local decryption integrity check failed")
    size = int.from_bytes(clear[:4], "little")
    if size < 4 or size > len(clear) or size <= len(clear) - 16:
        raise TelegramDataError("Invalid Telegram decrypted data size")
    return clear[4:size]


def read_tdf(path):
    """Read and MD5-validate a traditional ``TDF$`` storage file."""
    data = Path(path).read_bytes()
    if len(data) < 24 or data[:4] != b"TDF$":
        raise TelegramDataError("Not a Telegram TDF$ file")
    version = int.from_bytes(data[4:8], "little")
    payload, stored_md5 = data[8:-16], data[-16:]
    check = hashlib.md5(
        payload
        + len(payload).to_bytes(4, "little")
        + version.to_bytes(4, "little")
        + b"TDF$"
    ).digest()
    if check != stored_md5:
        raise TelegramDataError("Telegram TDF$ checksum mismatch")
    return version, payload


def read_encrypted_tdf(path, key):
    version, payload = read_tdf(path)
    encrypted = QtReader(payload).qbytes()
    return version, decrypt_local(encrypted, key)


def to_file_part(value):
    result = []
    for _ in range(16):
        result.append("0123456789ABCDEF"[value & 0xF])
        value >>= 4
    return "".join(result)


def _data_name(index):
    return "data" if index == 0 else f"data#{index + 1}"


def _account_file_part(index):
    digest = hashlib.md5(_data_name(index).encode("utf-8")).digest()
    return to_file_part(int.from_bytes(digest, "little"))


def _find_variant(base):
    base = Path(base)
    if base.is_file():
        return base
    for suffix in ("s", "1", "0"):
        candidate = Path(str(base) + suffix)
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(str(base))


def _derive_passcode_key(salt, passcode):
    passcode = passcode.encode("utf-8") if isinstance(passcode, str) else passcode
    digest = hashlib.sha512(salt + passcode + salt).digest()
    iterations = 1 if not passcode else 100_000
    return hashlib.pbkdf2_hmac("sha512", digest, salt, iterations, 256)


def _peer_id(serialized):
    reserved = 0x80 << 48
    if serialized & reserved:
        value = serialized & ~reserved
        kind_code = (value >> 48) & 0xFF
        return {0: "User", 1: "Chat", 2: "Channel"}.get(
            kind_code, "Unknown"
        ), value & 0xFFFFFFFFFFFF
    kind_code = (serialized & 0xF00000000) >> 32
    return {0: "User", 1: "Chat", 2: "Channel"}.get(
        kind_code, "Unknown"
    ), serialized & 0xFFFFFFFF


def read_peer(reader, stream_version):
    """Read the current Telegram serialized PeerData fields."""
    kind, peer_id = _peer_id(reader.u64())
    version_tag = reader.u64()
    version = 0
    if version_tag == 0x77FFFFFFFFFFFFFF:
        version = reader.i32()
        photo_id = reader.u64()
    else:
        photo_id = version_tag

    width_or_tag = reader.i32()
    if width_or_tag == -0x80000000:
        reader.qbytes()  # Modern serialized ImageLocation.
    else:
        reader.i32()  # height
        reader.i32()  # dc
        reader.u64()  # volume
        reader.i32()  # local
        reader.u64()  # secret
        if stream_version >= 1_003_013:
            reader.qbytes()
    if version > 0:
        reader.i32()  # userpic has video

    record = {
        "peer_type": kind,
        "peer_id": peer_id,
        "photo_id": photo_id or "",
    }
    if kind == "User":
        record.update({
            "first_name": reader.qstring(),
            "last_name": reader.qstring(),
            "phone": reader.qstring(),
            "username": reader.qstring(),
        })
        reader.u64()  # access hash: deliberately not returned
        if stream_version >= 9012:
            record["flags"] = reader.i32()
        if stream_version >= 9016:
            record["inline_placeholder"] = reader.qstring()
        record["last_seen"] = reader.u32()
        record["is_contact"] = reader.i32() == 1
        record["bot_info_version"] = reader.i32()
        if version > 2:
            reader.i32()  # supports guest chat
    elif kind == "Chat":
        record["name"] = reader.qstring()
        record["member_count"] = reader.i32()
        record["created"] = reader.i32()
        reader.i32()
        reader.i32()
        reader.i32()
        record["flags"] = reader.u32()
        record["invite_link"] = reader.qstring()
    elif kind == "Channel":
        record["name"] = reader.qstring()
        reader.u64()  # access hash: deliberately not returned
        record["created"] = reader.i32()
        reader.i32()
        reader.i32()
        record["flags"] = reader.u32()
        record["invite_link"] = reader.qstring()
    else:
        raise TelegramDataError("Unsupported serialized Telegram peer type")
    return record


_MAP_SINGLE_KEYS = {
    0x04: "locations",
    0x09: "user_settings",
    0x0A: "recent_hashtags_and_bots",
    0x0F: "saved_gifs",
    0x11: "trusted_bots",
    0x12: "favorite_stickers",
    0x13: "export_settings",
    0x18: "search_suggestions",
    0x1A: "round_placeholder",
    0x1B: "inline_bot_downloads",
    0x1C: "media_playback_positions",
    0x1E: "preferences",
}


def parse_map(data):
    reader = QtReader(data)
    keys = {}
    drafts = []
    bot_storages = []
    self_serialized = b""
    while reader.remaining() >= 4:
        entry_type = reader.u32()
        if entry_type in (0x01, 0x02, 0x1D):
            count = reader.u32()
            target = bot_storages if entry_type == 0x1D else drafts
            for _ in range(count):
                target.append((reader.u64(), reader.u64()))
        elif entry_type == 0x15:
            self_serialized = reader.qbytes()
        elif entry_type in (0x03, 0x05, 0x06):
            for _ in range(reader.u32()):
                reader.raw(28)
        elif entry_type in _MAP_SINGLE_KEYS:
            keys[_MAP_SINGLE_KEYS[entry_type]] = reader.u64()
        elif entry_type in (0x07, 0x08, 0x0B, 0x0C, 0x0D, 0x0E):
            reader.u64()
        elif entry_type in (0x10,):
            values = [reader.u64() for _ in range(4)]
            for name, value in zip((
                    "installed_stickers", "featured_stickers",
                    "recent_stickers", "archived_stickers"), values):
                keys[name] = value
        elif entry_type in (0x16, 0x17):
            values = [reader.u64() for _ in range(3)]
            prefix = "masks" if entry_type == 0x16 else "custom_emoji"
            for name, value in zip(("installed", "recent", "archived"), values):
                keys[f"{prefix}_{name}"] = value
        elif entry_type == 0x14:
            keys["background_day"] = reader.u64()
            keys["background_night"] = reader.u64()
        elif entry_type == 0x19:
            reader.qbytes()
            reader.qbytes()
        else:
            raise TelegramDataError(
                f"Unsupported Telegram map entry 0x{entry_type:02x}"
            )
    return {
        "keys": keys,
        "drafts": drafts,
        "bot_storages": bot_storages,
        "self_serialized": self_serialized,
    }


class TDataProfile:
    """Validated offline view of a Telegram Desktop tdata directory."""

    def __init__(self, tdata, passcode="", load_accounts=True):
        self.tdata = Path(tdata)
        self.passcode_protected = bool(passcode)
        self.version = 0
        self.local_key = b""
        self.active_index = 0
        self.accounts = []
        self._load(passcode, load_accounts)

    def _load(self, passcode, load_accounts):
        key_path = _find_variant(self.tdata / "key_data")
        self.version, payload = read_tdf(key_path)
        stream = QtReader(payload)
        salt = stream.qbytes()
        key_encrypted = stream.qbytes()
        info_encrypted = stream.qbytes()
        passcode_key = _derive_passcode_key(salt, passcode)
        self.local_key = decrypt_local(key_encrypted, passcode_key)[:256]
        info = QtReader(decrypt_local(info_encrypted, self.local_key))
        count = info.i32()
        indexes = [info.i32() for _ in range(count)]
        if info.remaining() >= 4:
            self.active_index = info.i32()
        valid_indexes = [index for index in indexes if 0 <= index < 3]
        if valid_indexes and self.active_index not in valid_indexes:
            # Telegram falls back to the first loaded account when the stored
            # active index is absent (commonly -1 in a single-account profile).
            self.active_index = valid_indexes[0]
        if load_accounts:
            for index in valid_indexes:
                self.accounts.append(self._load_account(index))

    def _load_account(self, index):
        part = _account_file_part(index)
        account_dir = self.tdata / part
        _, mtp = read_encrypted_tdf(_find_variant(self.tdata / part), self.local_key)
        stream = QtReader(mtp)
        if stream.i32() != 75:
            raise TelegramDataError("Unsupported Telegram MTP data version")
        authorization = QtReader(stream.qbytes())
        first = authorization.i32()
        main_dc = authorization.i32()
        if first == -1 and main_dc == -1:
            user_id = authorization.u64()
            main_dc = authorization.i32()
        else:
            user_id = first

        _, map_payload = read_tdf(_find_variant(account_dir / "map"))
        map_stream = QtReader(map_payload)
        map_stream.qbytes()
        map_stream.qbytes()
        map_data = decrypt_local(map_stream.qbytes(), self.local_key)
        parsed_map = parse_map(map_data)
        self_peer = {}
        if parsed_map["self_serialized"]:
            self_peer = read_peer(
                QtReader(parsed_map["self_serialized"]), self.version
            )
        return {
            "index": index,
            "active": index == self.active_index,
            "user_id": user_id,
            "main_dc": main_dc,
            "directory": account_dir,
            "map": parsed_map,
            "self": self_peer,
        }

    def referenced_file(self, account, name):
        key = account["map"]["keys"].get(name)
        if not key:
            return None
        try:
            return _find_variant(account["directory"] / to_file_part(key))
        except FileNotFoundError:
            return None

    def decrypt_referenced(self, account, name):
        path = self.referenced_file(account, name)
        if not path:
            return None, b""
        _, data = read_encrypted_tdf(path, self.local_key)
        return path, data


def find_tdata(files):
    for value in map(str, files):
        parts = Path(value).parts
        if "tdata" in parts:
            position = len(parts) - 1 - parts[::-1].index("tdata")
            return Path(*parts[:position + 1])
    return None


def load_profile(files, load_accounts=True):
    tdata = find_tdata(files)
    if not tdata:
        raise TelegramDataError("Telegram tdata directory not found")
    passcode = ""
    passcode_file = tdata.parent / "telegram_local_passcode.txt"
    if passcode_file.is_file():
        passcode = passcode_file.read_text(
            encoding="utf-8", errors="replace"
        ).rstrip("\r\n")
    return TDataProfile(tdata, passcode, load_accounts=load_accounts)


def parse_search_suggestions(profile, account):
    path, data = profile.decrypt_referenced(account, "search_suggestions")
    if not data:
        return path, [], []
    outer = QtReader(data)
    top = outer.qbytes()
    recent = outer.qbytes() if outer.remaining() >= 4 else b""
    settings = outer.qbytes() if outer.remaining() >= 4 else b""
    if outer.remaining() >= 4:
        outer.qbytes()  # Guest-chat bots use the same peer format.

    peers = []
    for collection, payload in (("Top Peer", top), ("Recent Peer", recent)):
        if not payload:
            continue
        reader = QtReader(payload)
        stream_version = reader.u32()
        disabled = reader.u32()
        count = min(reader.u32(), 64)
        for rank in range(1, count + 1):
            peer = read_peer(reader, stream_version)
            peer.update({
                "collection": collection,
                "rank": rank,
                "rating": reader.u64() / 1_000_000,
                "disabled": bool(disabled),
            })
            peers.append(peer)

    searches = []
    if settings:
        reader = QtReader(settings)
        stream_version = reader.u32()
        for rank in range(1, min(reader.u32(), 32) + 1):
            searches.append({
                "rank": rank,
                "entry_id": reader.qstring(),
                "version": stream_version,
            })
    return path, peers, searches


def _qt_datetime(reader):
    julian_day = struct.unpack(">q", reader.raw(8))[0]
    milliseconds = reader.i32()
    spec = reader.i8()
    if spec == 2 and reader.remaining() >= 4:
        reader.i32()
    if julian_day <= 0 or milliseconds < 0:
        return ""
    try:
        day = date.fromordinal(julian_day - 1_721_425)
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1_000)
        timezone_info = timezone.utc if spec == 1 else None
        return datetime.combine(
            day, time(hours, minutes, seconds, millis * 1000),
            tzinfo=timezone_info,
        )
    except (ValueError, OverflowError):
        return ""


def parse_locations(profile, account):
    path, data = profile.decrypt_referenced(account, "locations")
    if not data:
        return path, []
    reader = QtReader(data)
    records = []
    while reader.remaining() >= 16:
        first, second = reader.u64(), reader.u64()
        if not first and not second:
            break
        legacy_type = reader.u32()
        filename = reader.qstring()
        if profile.version > 9013:
            reader.qbytes()  # macOS security-scoped bookmark
        modified = _qt_datetime(reader)
        size = reader.u32()
        if filename and not filename.startswith("*"):
            records.append({
                "media_key": f"{first:016X}:{second:016X}",
                "legacy_type": legacy_type,
                "filename": filename,
                "modified": modified,
                "size": size,
            })
    return path, records


def _increment_counter(iv, blocks):
    return ((int.from_bytes(iv, "big") + blocks) % (1 << 128)).to_bytes(
        16, "big"
    )


def decrypt_tdef(path, key):
    """Decrypt and authenticate a Desktop App Toolkit ``TDEF`` file."""
    data = Path(path).read_bytes()
    if len(data) < 116 or data[:4] != b"TDEF":
        raise TelegramDataError("Not a Telegram TDEF cache file")
    salt = data[4:68]
    aes_key = hashlib.sha256(key[:128] + salt[:32]).digest()
    iv = hashlib.sha256(key[128:] + salt[32:]).digest()[:16]
    header = AES.new(
        aes_key, AES.MODE_CTR, nonce=b"",
        initial_value=int.from_bytes(iv, "big"),
    ).decrypt(data[68:116])
    if header[16:] != hashlib.sha256(key + salt + header[:16]).digest():
        raise TelegramDataError("Telegram TDEF header integrity check failed")
    encrypted = data[116:116 + ((len(data) - 116) // 16 * 16)]
    clear = AES.new(
        aes_key, AES.MODE_CTR, nonce=b"",
        initial_value=int.from_bytes(_increment_counter(iv, 3), "big"),
    ).decrypt(encrypted)
    return clear


@dataclass
class CacheEntry:
    key_high: int
    key_low: int
    place: bytes
    tag: int
    size: int
    checksum: int
    used: int


def _cache_store(record, timed):
    expected = 48 if timed else 32
    if len(record) < expected:
        raise TelegramDataError("Truncated Telegram cache store record")
    tag = record[1]
    size = int.from_bytes(record[2:5], "little")
    place = record[5:12]
    checksum = int.from_bytes(record[12:16], "little")
    high, low = struct.unpack("<QQ", record[16:32])
    used = struct.unpack("<I", record[40:44])[0] if timed else 0
    return CacheEntry(high, low, place, tag, size, checksum, used)


def parse_cache_binlog(path, key):
    data = decrypt_tdef(path, key)
    if len(data) < 16:
        return {}
    format_flags, _system, _reserved1, _reserved2 = struct.unpack(
        "<IIII", data[:16]
    )
    timed = bool((format_flags >> 8) & 1)
    stores = {}
    position = 16
    while position < len(data):
        record_type = data[position]
        if record_type == 1:
            size = 48 if timed else 32
            entry = _cache_store(data[position:position + size], timed)
            stores[(entry.key_high, entry.key_low)] = entry
            position += size
        elif record_type == 2:
            count = int.from_bytes(data[position + 1:position + 4], "little")
            position += 16
            part_size = 48 if timed else 32
            for _ in range(count):
                entry = _cache_store(
                    data[position:position + part_size], timed
                )
                stores[(entry.key_high, entry.key_low)] = entry
                position += part_size
        elif record_type == 3:
            count = int.from_bytes(data[position + 1:position + 4], "little")
            position += 16
            for _ in range(count):
                stores.pop(struct.unpack("<QQ", data[position:position + 16]), None)
                position += 16
        elif record_type == 4:
            count = int.from_bytes(data[position + 1:position + 4], "little")
            used = struct.unpack("<I", data[position + 12:position + 16])[0]
            position += 16
            for _ in range(count):
                item_key = struct.unpack("<QQ", data[position:position + 16])
                if item_key in stores:
                    stores[item_key].used = used
                position += 16
        elif record_type == 0 and not any(data[position:]):
            break
        else:
            raise TelegramDataError(
                f"Unknown Telegram cache binlog record 0x{record_type:02x}"
            )
    return stores


def cache_place_path(place):
    encoded = "".join(f"{value:02X}"[::-1] for value in place)
    return f"{encoded[:2]}/{encoded[2:]}"


def xxh32(data, seed=0):
    """XXH32 used by Telegram's cache index for clear-object integrity."""
    mask = 0xFFFFFFFF
    prime1 = 0x9E3779B1
    prime2 = 0x85EBCA77
    prime3 = 0xC2B2AE3D
    prime4 = 0x27D4EB2F
    prime5 = 0x165667B1

    def rotate(value, count):
        return ((value << count) | (value >> (32 - count))) & mask

    def round_value(accumulator, lane):
        accumulator = (accumulator + lane * prime2) & mask
        return (rotate(accumulator, 13) * prime1) & mask

    data = memoryview(data)
    position = 0
    if len(data) >= 16:
        values = [
            (seed + prime1 + prime2) & mask,
            (seed + prime2) & mask,
            seed & mask,
            (seed - prime1) & mask,
        ]
        while position <= len(data) - 16:
            for index in range(4):
                lane = int.from_bytes(
                    data[position + index * 4:position + index * 4 + 4],
                    "little",
                )
                values[index] = round_value(values[index], lane)
            position += 16
        result = (
            rotate(values[0], 1) + rotate(values[1], 7)
            + rotate(values[2], 12) + rotate(values[3], 18)
        ) & mask
    else:
        result = (seed + prime5) & mask

    result = (result + len(data)) & mask
    while position <= len(data) - 4:
        lane = int.from_bytes(data[position:position + 4], "little")
        result = (result + lane * prime3) & mask
        result = (rotate(result, 17) * prime4) & mask
        position += 4
    while position < len(data):
        result = (result + data[position] * prime5) & mask
        result = (rotate(result, 11) * prime1) & mask
        position += 1
    result ^= result >> 15
    result = (result * prime2) & mask
    result ^= result >> 13
    result = (result * prime3) & mask
    result ^= result >> 16
    return result & mask


def identify_media(data):
    """Return (kind, MIME, extension) only for validated useful media."""
    if data.startswith(b"\xff\xd8\xff"):
        return "Image", "image/jpeg", "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "Image", "image/png", "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "Image", "image/gif", "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "Image/Animation", "image/webp", "webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "Video", "video/mp4", "mp4"
    if data.startswith(b"OggS"):
        return "Audio", "audio/ogg", "ogg"
    if data.startswith(b"ID3") or data[:2] in (b"\xff\xfb", b"\xff\xf3"):
        return "Audio", "audio/mpeg", "mp3"
    if data.startswith(b"%PDF-"):
        return "Document", "application/pdf", "pdf"
    if data.startswith(b"PK\x03\x04"):
        return "Archive/Document", "application/zip", "zip"
    if data.lstrip().startswith(b"<svg"):
        return "Image", "image/svg+xml", "svg"
    return "", "", ""


def iter_cache_media(profile):
    for cache_name in ("cache", "media_cache"):
        base = profile.tdata / "user_data" / cache_name
        if not base.is_dir():
            continue
        versions = [
            child for child in base.iterdir()
            if child.is_dir() and child.name.isdigit()
        ]
        for version_dir in sorted(versions, key=lambda p: int(p.name)):
            binlog = version_dir / "binlog"
            if not binlog.is_file():
                continue
            for entry in parse_cache_binlog(binlog, profile.local_key).values():
                source = version_dir / cache_place_path(entry.place)
                if not source.is_file():
                    continue
                try:
                    clear = decrypt_tdef(source, profile.local_key)[:entry.size]
                except (OSError, TelegramDataError):
                    continue
                if xxh32(clear) != entry.checksum:
                    continue
                kind, mime, extension = identify_media(clear)
                if not kind:
                    continue
                yield {
                    "cache": cache_name,
                    "source": source,
                    "binlog": binlog,
                    "key": f"{entry.key_high:016X}:{entry.key_low:016X}",
                    "tag": entry.tag,
                    "size": entry.size,
                    "used": (
                        datetime.fromtimestamp(entry.used, tz=timezone.utc)
                        if entry.used else ""
                    ),
                    "kind": kind,
                    "mime": mime,
                    "extension": extension,
                    "data": clear,
                }
