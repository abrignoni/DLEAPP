"""Discord's HTTP cache in Chromium's blockfile format (Discord on Windows).

The caches are built here byte by byte: an ``index`` hash table, ``data_0``
(36-byte rankings blocks), ``data_1`` (256-byte entry blocks), ``data_2``
(1 KiB blocks) and ``f_XXXXXX`` files for bodies kept outside the block files,
laid out as scripts/chromium/blockfile_cache.py reads them. A simple cache
entry file is built the same way for the mixed-format case.
"""

import gzip
import json
import os
import pathlib
import struct
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from scripts.artifacts import discordCacheRecords, discordContacts, discordMedia, discordMessages
from scripts.chromium import blockfile_cache, discord_api
from scripts.chromium.simple_cache import SIMPLE_EOF_MAGIC, SIMPLE_HEADER_MAGIC

_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)
REQUESTED = datetime(2024, 5, 1, 12, 0, 0, 250000, tzinfo=timezone.utc)
RECEIVED = datetime(2024, 5, 1, 12, 0, 1, 500000, tzinfo=timezone.utc)

CHANNEL = "1100000000000000001"
MESSAGE_ID = "1100000000000000011"
ATTACHMENT = "1100000000000000021"
SECOND_ATTACHMENT = "1100000000000000022"
AUTHOR = "1100000000000000031"
FRIEND = "1100000000000000041"

API_URL = f"https://discord.com/api/v9/channels/{CHANNEL}/messages?limit=50"
ATTACHMENT_URL = f"https://cdn.discordapp.com/attachments/{CHANNEL}/{ATTACHMENT}/photo.png"
# Real media URLs carry signed query parameters, so their cache keys pass the
# 160 bytes an entry block holds and are stored as a long key.
LONG_ATTACHMENT_URL = (f"https://media.discordapp.net/attachments/{CHANNEL}/{SECOND_ATTACHMENT}/"
                       "second_picture.png?ex=6650a1b2&is=664f5032&hm=" + "0123456789abcdef" * 4)
PROFILE_URL = f"https://discord.com/api/v9/users/{FRIEND}/profile?with_mutual_guilds=true"
AVATAR_URL = f"https://cdn.discordapp.com/avatars/{FRIEND}/abc123.png?size=128"
INVITE_URL = "https://discord.com/api/v9/invites/testcode?with_counts=true"

PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(40))
SECOND_PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(60, 110))
AVATAR_PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(120, 150))
MESSAGE = {
    "id": MESSAGE_ID, "channel_id": CHANNEL, "type": 0,
    "content": "cache test message", "timestamp": "2024-05-01T11:59:00.000000+00:00",
    "edited_timestamp": None,
    "author": {"id": AUTHOR, "username": "tester", "global_name": "Tester"},
    "attachments": [
        {"id": ATTACHMENT, "filename": "photo.png", "size": len(PNG), "content_type": "image/png"},
        {"id": SECOND_ATTACHMENT, "filename": "second_picture.png", "size": len(SECOND_PNG),
         "content_type": "image/png"},
    ],
    "mentions": [], "embeds": [], "pinned": False,
}
PROFILE = {
    "user": {"id": FRIEND, "username": "friend", "global_name": "Friend", "avatar": "abc123"},
    "user_profile": {"bio": "about me", "pronouns": "they/them"},
    "connected_accounts": [{"type": "steam", "name": "friend_on_steam"}],
}


def _base_time(moment):
    """base::Time's internal value: microseconds since 1601-01-01 UTC."""
    return (moment - _EPOCH_1601) // timedelta(microseconds=1)


def _cache_key(url):
    return f"1/0/_dk_https://discord.com https://discord.com {url}".encode()


def _response_info(status, content_type, encoding, requested=REQUESTED, received=RECEIVED):
    """An HttpResponseInfo stream 0: payload size, flags, two times, then the headers."""
    lines = [f"HTTP/1.1 {status}", f"content-type: {content_type}"]
    if encoding:
        lines.append(f"content-encoding: {encoding}")
    block = b"\x00".join(line.encode("latin-1") for line in lines) + b"\x00\x00"
    return (struct.pack("<Iiqq", 0, 0, _base_time(requested), _base_time(received))
            + struct.pack("<I", len(block)) + block)


class BlockfileCache:
    """Writes a minimal blockfile cache folder."""

    _FILES = {0: (1, 36), 1: (2, 256), 2: (3, 1024)}   # selector: (file type, block size)

    def __init__(self, folder, table_length=8):
        self.folder = str(folder)
        os.makedirs(self.folder, exist_ok=True)
        self.table = [0] * table_length
        self.data = {selector: bytearray() for selector in self._FILES}
        self.used = dict.fromkeys(self._FILES, 0)
        self.externals = 0

    def _store(self, selector, payload):
        file_type, block_size = self._FILES[selector]
        blocks = max(1, -(-len(payload) // block_size))
        assert blocks <= 4, "a block file address spans at most four blocks"
        first = self.used[selector]
        self.used[selector] += blocks
        data = self.data[selector]
        data.extend(bytes((first + blocks) * block_size - len(data)))
        data[first * block_size:first * block_size + len(payload)] = payload
        return 0x80000000 | file_type << 28 | (blocks - 1) << 24 | selector << 16 | first

    def _store_external(self, payload):
        self.externals += 1
        with open(os.path.join(self.folder, f"f_{self.externals:06x}"), "wb") as handle:
            handle.write(payload)
        return 0x80000000 | self.externals

    def add(self, url, body, content_type, *, status=200, encoding=None, bucket=0,
            external_body=False, requested=REQUESTED, received=RECEIVED):
        """Add one entry at the head of ``bucket``'s chain and return its address."""
        key = _cache_key(url)
        stream0 = _response_info(status, content_type, encoding, requested, received)
        rankings = self._store(0, struct.pack("<Q", _base_time(received)))
        stream0_address = self._store(2, stream0)
        body_address = self._store_external(body) if external_body else self._store(2, body)
        record = bytearray(256)
        struct.pack_into("<I", record, 4, self.table[bucket])
        struct.pack_into("<I", record, 8, rankings)
        struct.pack_into("<Q", record, 24, _base_time(requested))
        if len(key) <= 160:
            struct.pack_into("<iI", record, 32, len(key), 0)
            record[96:96 + len(key)] = key
        else:
            struct.pack_into("<iI", record, 32, len(key), self._store(2, key))
        struct.pack_into("<4i", record, 40, len(stream0), len(body), 0, 0)
        struct.pack_into("<4I", record, 56, stream0_address, body_address, 0, 0)
        address = self._store(1, bytes(record))
        self.table[bucket] = address
        return address

    def write(self):
        """Write the index and data files; return every file, as a seeker would list them."""
        index = bytearray(368)
        struct.pack_into("<II", index, 0, 0xC103CAC3, 0x30000)
        struct.pack_into("<I", index, 28, len(self.table))
        index += struct.pack(f"<{len(self.table)}I", *self.table)
        with open(os.path.join(self.folder, "index"), "wb") as handle:
            handle.write(index)
        for selector, data in self.data.items():
            with open(os.path.join(self.folder, f"data_{selector}"), "wb") as handle:
                handle.write(bytes(8192) + data)
        return sorted(os.path.join(self.folder, name) for name in os.listdir(self.folder))


def _simple_entry(folder, name, url, body, content_type):
    """One simple cache ``*_0`` file: header, key, body, EOF, stream 0, EOF."""
    os.makedirs(folder, exist_ok=True)
    key = _cache_key(url)
    stream0 = _response_info(200, content_type, None)
    data = (struct.pack("<QIII", SIMPLE_HEADER_MAGIC, 5, len(key), 0) + bytes(4) + key + body
            + struct.pack("<QIII", SIMPLE_EOF_MAGIC, 0, 0, len(body)) + bytes(4)
            + stream0 + struct.pack("<QIII", SIMPLE_EOF_MAGIC, 0, 0, len(stream0)) + bytes(4))
    path = os.path.join(folder, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def _windows_cache(folder):
    """A Discord Windows cache holding a messages response and its two attachments.

    The messages response and the second attachment keep their bodies in data_2
    and the first attachment in f_000001; every entry is recorded in data_1.
    """
    cache = BlockfileCache(folder)
    cache.add(API_URL, gzip.compress(json.dumps([MESSAGE]).encode()), "application/json",
              encoding="gzip", bucket=1)
    first = cache.add(ATTACHMENT_URL, PNG, "image/png", external_body=True, bucket=2)
    # Chained behind the first attachment, so both sit in one bucket and one data file.
    second = cache.add(LONG_ATTACHMENT_URL, SECOND_PNG, "image/png", bucket=2)
    return cache.write(), first, second


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class DiscordBlockfileScanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.cache_dir = os.path.join(self.root, "Users", "u", "AppData", "Roaming", "discord", "Cache")
        self.files, self.first, self.second = _windows_cache(self.cache_dir)
        self.data_1 = os.path.join(self.cache_dir, "data_1")
        self.data_2 = os.path.join(self.cache_dir, "data_2")
        self.f_1 = os.path.join(self.cache_dir, "f_000001")

    def tearDown(self):
        self._tmp.cleanup()

    def test_messages_and_both_attachments_are_read(self):
        scan = discord_api.scan_cache(self.files)
        self.assertEqual(scan.entry_count, 3)
        self.assertEqual(list(scan.messages), [MESSAGE_ID])
        # The message was read from the response body, which this cache keeps in data_2.
        self.assertEqual(scan.messages[MESSAGE_ID]["source"], self.data_2)
        self.assertEqual(scan.messages[MESSAGE_ID]["cached"], RECEIVED)
        self.assertEqual(scan.messages[MESSAGE_ID]["message"]["content"], "cache test message")

        # Both attachment entries are recorded in data_1, so each is keyed by its address as well.
        self.assertEqual(sorted(scan.media), sorted([f"{self.data_1}#{self.first:08x}",
                                                     f"{self.data_1}#{self.second:08x}"]))
        by_owner = {media["owner_id"]: (key, media) for key, media in scan.media.items()}
        self.assertEqual(sorted(by_owner), [ATTACHMENT, SECOND_ATTACHMENT])
        for owner, body, holder in ((ATTACHMENT, PNG, self.f_1),
                                    (SECOND_ATTACHMENT, SECOND_PNG, self.data_2)):
            key, media = by_owner[owner]
            self.assertEqual(media["source"], holder)
            self.assertEqual(media["status"], 200)
            self.assertEqual(media["size"], len(body))
            self.assertEqual(discord_api.cached_entry(key).decoded_body(), body)

    def test_records_carry_times_status_and_the_entry_file(self):
        scan = discord_api.scan_cache(self.files)
        self.assertEqual(sorted(record["url"] for record in scan.records),
                         sorted([API_URL, ATTACHMENT_URL, LONG_ATTACHMENT_URL]))
        for record in scan.records:
            self.assertEqual((record["requested"], record["cached"]), (REQUESTED, RECEIVED))
            self.assertEqual(record["status"], 200)
            self.assertEqual(record["source"], self.data_1)

    def test_an_error_response_is_listed_but_not_parsed(self):
        folder = os.path.join(self.root, "Users", "v", "AppData", "Roaming", "discord", "Cache")
        cache = BlockfileCache(folder)
        cache.add(API_URL, json.dumps([MESSAGE]).encode(), "application/json", status=404)
        scan = discord_api.scan_cache(cache.write())
        self.assertEqual(scan.messages, {})
        self.assertEqual([record["status"] for record in scan.records], [404])

    def test_each_cache_folder_gets_its_own_scan(self):
        # Without data_0 (the rankings file, whose name also ends in _0) only the
        # index path tells the two folders apart in the scan's memo key.
        folder = os.path.join(self.root, "Users", "v", "AppData", "Roaming", "discordptb", "Cache")
        cache = BlockfileCache(folder)
        cache.add(ATTACHMENT_URL, PNG, "image/png")
        other_files = [f for f in cache.write() if os.path.basename(f) != "data_0"]
        first_files = [f for f in self.files if os.path.basename(f) != "data_0"]
        for path in (os.path.join(folder, "data_0"), os.path.join(self.cache_dir, "data_0")):
            os.remove(path)
        other = discord_api.scan_cache(other_files)
        first = discord_api.scan_cache(first_files)
        self.assertEqual(other.entry_count, 1)
        self.assertEqual(first.entry_count, 3)

    def test_a_blockfile_cache_in_cache_data_is_read(self):
        folder = os.path.join(self.root, "Users", "w", "AppData", "Roaming", "discord", "Cache",
                              "Cache_Data")
        files, _first, _second = _windows_cache(folder)
        self.assertEqual(list(discord_api.scan_cache(files).messages), [MESSAGE_ID])

    def test_an_unknown_reference_reads_nothing(self):
        self.assertIsNone(discord_api.cached_entry(f"{self.data_1}#ffffffff"))


class RequestClassificationTest(unittest.TestCase):
    def test_only_listed_asset_extensions_are_left_out(self):
        with tempfile.TemporaryDirectory() as root:
            cache = BlockfileCache(os.path.join(root, "discord", "Cache"))
            for name in ("app.js", "strings.json", "notes.js.txt", "logo.png"):
                cache.add(f"https://discord.com/assets/{name}", b"x", "text/plain")
            scan = discord_api.scan_cache(cache.write())
        self.assertEqual(scan.entry_count, 4)
        self.assertEqual(sorted(record["url"].rsplit("/", 1)[1] for record in scan.records),
                         ["logo.png", "notes.js.txt"])

    def test_a_search_on_a_documented_filter_alone_is_kept(self):
        url = ("https://discord.com/api/v9/guilds/1100000000000000051/messages/search"
               f"?replied_to_user_id={AUTHOR}")
        with tempfile.TemporaryDirectory() as root:
            cache = BlockfileCache(os.path.join(root, "discord", "Cache"))
            cache.add(url, json.dumps({"total_results": 0, "messages": []}).encode(),
                      "application/json")
            scan = discord_api.scan_cache(cache.write())
        self.assertEqual([(search["terms"], search["filters"]) for search in scan.searches],
                         [("", f"replied_to_user_id={AUTHOR}")])

    def test_message_types_follow_the_documented_table(self):
        self.assertEqual(discord_api.message_type_name(44), "Purchase Notification")
        self.assertEqual(discord_api.message_type_name(46), "Poll Result")
        self.assertEqual(discord_api.message_type_name(47), "Type 47")


class MixedFormatTest(unittest.TestCase):
    """A macOS-style simple cache and a Windows blockfile cache in one file list."""

    def test_both_formats_are_read_and_recovered(self):
        with tempfile.TemporaryDirectory() as root:
            simple_dir = os.path.join(root, "Users", "m", "Library", "Application Support",
                                      "discord", "Cache", "Cache_Data")
            simple = _simple_entry(simple_dir, "0123456789abcdef_0", ATTACHMENT_URL, PNG, "image/png")
            # A simple cache folder also holds a file named index, in its own format.
            with open(os.path.join(simple_dir, "index"), "wb") as handle:
                handle.write(bytes(400))
            cache_dir = os.path.join(root, "Users", "u", "AppData", "Roaming", "discord", "Cache")
            blockfile_files, _first, second = _windows_cache(cache_dir)
            files = [simple, os.path.join(simple_dir, "index")] + blockfile_files

            scan = discord_api.scan_cache(files)
            self.assertEqual(scan.entry_count, 4)
            self.assertIn(simple, scan.media)
            self.assertEqual(scan.media[simple]["source"], simple)
            self.assertEqual(scan.media[simple]["cached"], RECEIVED)
            self.assertEqual(discord_api.cached_entry(simple).decoded_body(), PNG)
            data_1 = os.path.join(cache_dir, "data_1")
            self.assertEqual(discord_api.cached_entry(f"{data_1}#{second:08x}").decoded_body(),
                             SECOND_PNG)
            self.assertEqual(sorted({record["source"] for record in scan.records}),
                             sorted([simple, data_1]))


class FolderNameTest(unittest.TestCase):
    def test_the_default_reads_only_cache_data(self):
        with tempfile.TemporaryDirectory() as root:
            cache = BlockfileCache(os.path.join(root, "app", "Cache"))
            cache.add(ATTACHMENT_URL, PNG, "image/png")
            files = cache.write()
            self.assertEqual(list(blockfile_cache.iter_entries(files)), [])
            entries = list(blockfile_cache.iter_entries(files, folder_names=("Cache",)))
            self.assertEqual([entry.url for entry in entries], [ATTACHMENT_URL])


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.cache_dir = os.path.join(self.root, "Users", "u", "AppData", "Roaming", "discord", "Cache")
        self.files, _first, _second = _windows_cache(self.cache_dir)
        self.folder = "Users/u/AppData/Roaming/discord/Cache"
        self.calls = []

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self, name):
        return os.path.join(self.cache_dir, name)

    def _check_in(self, source, body, name, **_kwargs):
        self.calls.append((source, body, name))
        return f"ref{len(self.calls)}"

    def _run(self, module, processor, files=None):
        with mock.patch.object(module, "check_in_embedded_media", self._check_in, create=True), \
                mock.patch.object(module, "logfunc", lambda *_args: None):
            return processor.__wrapped__(FakeContext(self.root, files or self.files))

    @staticmethod
    def _rows(headers, rows):
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        return [dict(zip(names, row)) for row in rows]

    def test_messages_recover_both_attachments(self):
        headers, rows, source = self._run(discordMessages, discordMessages.discordMessages)
        (row,) = self._rows(headers, rows)
        self.assertEqual(row["Message"], "cache test message")
        self.assertEqual(row["Attachments"], ["ref1", "ref2"])
        self.assertEqual(row["Source Cache File"], f"{self.folder}/data_2")
        self.assertEqual(source, self._path("data_2"))
        self.assertEqual(self.calls, [(self._path("f_000001"), PNG, "photo.png"),
                                      (self._path("data_2"), SECOND_PNG, "second_picture.png")])

    def test_attachments_name_the_file_holding_each_copy(self):
        headers, rows, _source = self._run(discordMessages, discordMessages.discordAttachments)
        by_id = {row["Attachment ID"]: row for row in self._rows(headers, rows)}
        self.assertEqual(by_id[ATTACHMENT]["Source Cache File"], f"{self.folder}/f_000001")
        self.assertEqual(by_id[SECOND_ATTACHMENT]["Source Cache File"], f"{self.folder}/data_2")
        self.assertEqual({row["Cached Copy"] for row in by_id.values()}, {"Yes"})

    def test_recovered_media_names_the_file_holding_each_body(self):
        headers, rows, source = self._run(discordMedia, discordMedia.discordRecoveredMedia)
        by_owner = {row["Owner ID"]: row for row in self._rows(headers, rows)}
        self.assertEqual(sorted(by_owner), [ATTACHMENT, SECOND_ATTACHMENT])
        self.assertEqual(by_owner[ATTACHMENT]["Source Cache File"], f"{self.folder}/f_000001")
        self.assertEqual(by_owner[SECOND_ATTACHMENT]["Source Cache File"], f"{self.folder}/data_2")
        self.assertEqual({row["Message Recovered"] for row in by_owner.values()}, {"Yes"})
        self.assertEqual(source, "\n".join(sorted([self._path("data_2"), self._path("f_000001")])))
        self.assertEqual(sorted(call[1] for call in self.calls), sorted([PNG, SECOND_PNG]))

    def test_cache_records_list_every_response(self):
        headers, rows, source = self._run(discordCacheRecords, discordCacheRecords.discordCacheRecords)
        records = self._rows(headers, rows)
        self.assertEqual(sorted(record["Host"] for record in records),
                         ["cdn.discordapp.com", "discord.com", "media.discordapp.net"])
        self.assertEqual({record["Source Cache File"] for record in records}, {f"{self.folder}/data_1"})
        self.assertEqual({record["HTTP Status"] for record in records}, {200})
        self.assertEqual(source, self._path("data_1"))

    def test_a_cached_profile_and_avatar_describe_the_user(self):
        folder = os.path.join(self.root, "Users", "p", "AppData", "Roaming", "discord", "Cache")
        cache = BlockfileCache(folder)
        cache.add(PROFILE_URL, json.dumps(PROFILE).encode(), "application/json")
        cache.add(AVATAR_URL, AVATAR_PNG, "image/png", external_body=True, bucket=3)
        headers, rows, _source = self._run(discordContacts, discordContacts.discordUsers,
                                           files=cache.write())
        (row,) = self._rows(headers, rows)
        self.assertEqual(row["User ID"], FRIEND)
        self.assertEqual(row["Seen As"], "Profile fetched")
        self.assertEqual((row["Pronouns"], row["Bio"]), ("they/them", "about me"))
        self.assertEqual(row["Connected Accounts"], "steam:friend_on_steam")
        self.assertEqual(row["Avatar"], "ref1")
        self.assertEqual(self.calls, [(os.path.join(folder, "f_000001"), AVATAR_PNG,
                                       f"avatar_{FRIEND}")])

    def test_an_invite_is_reported_from_its_latest_lookup(self):
        folder = os.path.join(self.root, "Users", "i", "AppData", "Roaming", "discord", "Cache")
        cache = BlockfileCache(folder)
        earlier = datetime(2024, 5, 1, 9, 0, tzinfo=timezone.utc)
        later = datetime(2024, 5, 3, 9, 0, tzinfo=timezone.utc)
        for bucket, moment, members in ((0, earlier, 10), (1, later, 20)):
            invite = {"code": "testcode", "approximate_member_count": members,
                      "guild": {"id": "1100000000000000051", "name": "Test server"}}
            cache.add(INVITE_URL, json.dumps(invite).encode(), "application/json",
                      bucket=bucket, requested=moment, received=moment)
        headers, rows, _source = self._run(discordContacts, discordContacts.discordInvites,
                                           files=cache.write())
        (row,) = self._rows(headers, rows)
        self.assertEqual((row["Looked Up"], row["Members (approx.)"]), (later, 20))


if __name__ == "__main__":
    unittest.main()
