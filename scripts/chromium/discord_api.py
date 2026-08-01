"""Shared parsing of Discord Desktop data held in Chromium containers.

Discord Desktop is an Electron front end for the same REST API the web client
uses, so the JSON the app rendered is still sitting in the Chromium HTTP cache
long after it left the screen. This module walks that cache once and hands the
individual artifacts a decoded view of it: messages, users, channels,
attachments, reactions, searches and the raw request index.

A single scan is memoised per file list because several artifacts share it,
and message bodies are only decompressed for endpoints that are known to carry
JSON worth keeping.
"""

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, unquote, urlparse

from scripts.chromium.simple_cache import base_time_to_datetime, iter_entries

# Snowflake IDs count milliseconds from 2015-01-01, Discord's first second.
SNOWFLAKE_EPOCH_MS = 1420070400000
_SNOWFLAKE_EPOCH = datetime(2015, 1, 1, tzinfo=timezone.utc)

_API_RE = re.compile(r"https://(?:discord|discordapp)\.com/api/v(\d+)/(.+)$")
_MESSAGES_RE = re.compile(r"^channels/(\d+)/messages(?:\?|$)")
_MESSAGE_SEARCH_RE = re.compile(r"^(channels|guilds)/(\d+)/messages/search")
_REACTIONS_RE = re.compile(r"^channels/(\d+)/messages/(\d+)/reactions/([^?]+)")
_PROFILE_RE = re.compile(r"^users/(\d+)/profile")
_CHANNEL_RE = re.compile(r"^channels/(\d+)(?:\?|$)")
_GUILD_PROFILE_RE = re.compile(r"^guilds/(\d+)/(?:profile|basic)")
_INVITE_RE = re.compile(r"^invites/([^/?]+)")
_GIF_SEARCH_RE = re.compile(r"^gifs/(search|trending)")
_NOTE_RE = re.compile(r"^users/@me/notes/(\d+)")

# Message-search parameters that describe what was looked for, as opposed to
# pagination and sort options.
_SEARCH_FILTER_PARAMS = {
    "author_id", "channel_id", "has", "mentions", "mention_everyone",
    "pinned", "link_hostname", "attachment_filename", "attachment_extension",
    "embed_provider", "embed_type",
}

_ATTACHMENT_RE = re.compile(
    r"https://(?:media\.discordapp\.net|cdn\.discordapp\.com)/attachments/"
    r"(\d+)/(\d+)/([^?]*)")
_AVATAR_RE = re.compile(r"https://cdn\.discordapp\.com/avatars/(\d+)/([^?/]+)")
_GUILD_AVATAR_RE = re.compile(
    r"https://cdn\.discordapp\.com/guilds/(\d+)/users/(\d+)/avatars/([^?/]+)")
_EMOJI_RE = re.compile(r"https://cdn\.discordapp\.com/emojis/(\d+)")
_STICKER_RE = re.compile(r"https://media\.discordapp\.net/stickers/(\d+)"
                         r"|https://cdn\.discordapp\.com/stickers/(\d+)")
_ICON_RE = re.compile(r"https://cdn\.discordapp\.com/icons/(\d+)/([^?/]+)")
_BANNER_RE = re.compile(r"https://cdn\.discordapp\.com/banners/(\d+)/([^?/]+)")
_EXTERNAL_RE = re.compile(r"https://images-ext-\d\.discordapp\.net/external/[^/]+/(.+)$")

# Versioned SPA bundle assets: high volume, no investigative value.
_STATIC_ASSET_RE = re.compile(
    r"https://(?:discord|discordapp)\.com/assets/[^?]+\.(?:js|css|woff2?|map|svg|ico)")

_MESSAGE_TYPES = {
    0: "Default", 1: "Recipient Add", 2: "Recipient Remove", 3: "Call",
    4: "Channel Name Change", 5: "Channel Icon Change", 6: "Channel Pinned Message",
    7: "User Join", 8: "Guild Boost", 9: "Guild Boost Tier 1",
    10: "Guild Boost Tier 2", 11: "Guild Boost Tier 3", 12: "Channel Follow Add",
    14: "Guild Discovery Disqualified", 15: "Guild Discovery Requalified",
    18: "Thread Created", 19: "Reply", 20: "Chat Input Command",
    21: "Thread Starter Message", 22: "Guild Invite Reminder",
    23: "Context Menu Command", 24: "Auto Moderation Action",
    25: "Role Subscription Purchase", 26: "Interaction Premium Upsell",
    27: "Stage Start", 28: "Stage End", 29: "Stage Speaker",
    31: "Stage Topic", 32: "Guild Application Premium Subscription",
    36: "Guild Incident Alert Mode Enabled", 37: "Guild Incident Alert Mode Disabled",
    38: "Guild Incident Report Raid", 39: "Guild Incident Report False Alarm",
    46: "Poll Result", 47: "Changelog",
}

_CHANNEL_TYPES = {
    0: "Guild Text", 1: "Direct Message", 2: "Guild Voice", 3: "Group DM",
    4: "Guild Category", 5: "Guild Announcement", 10: "Announcement Thread",
    11: "Public Thread", 12: "Private Thread", 13: "Guild Stage Voice",
    14: "Guild Directory", 15: "Guild Forum", 16: "Guild Media",
}


def snowflake_to_datetime(snowflake):
    """Convert a Discord snowflake ID to its embedded creation time (UTC).

    The 2015-01-01 epoch and the 22-bit shift are the documented snowflake
    layout.

    Reference: Discord Developer Documentation, 'Snowflakes (ID format)',
    https://discord.com/developers/docs/reference#snowflakes
    """
    try:
        value = int(snowflake)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    try:
        return _SNOWFLAKE_EPOCH + timedelta(milliseconds=value >> 22)
    except (OverflowError, ValueError):
        return ""


def iso_to_datetime(value):
    """Convert a Discord ISO-8601 timestamp to an aware UTC datetime."""
    if not value or not isinstance(value, str):
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def epoch_ms_to_datetime(value):
    """Convert a JavaScript millisecond timestamp to an aware UTC datetime."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ""


def message_type_name(value):
    return _MESSAGE_TYPES.get(value, f"Type {value}" if value is not None else "")


def channel_type_name(value):
    return _CHANNEL_TYPES.get(value, f"Type {value}" if value is not None else "")


def user_display(user):
    """Best available human-readable name for a Discord user object."""
    if not isinstance(user, dict):
        return ""
    name = user.get("global_name") or user.get("username") or ""
    handle = user.get("username") or ""
    if name and handle and name != handle:
        return f"{name} ({handle})"
    return name or handle or user.get("id", "")


def media_kind(url):
    """Classify a Discord CDN URL. Returns (kind, owner id, related id)."""
    match = _ATTACHMENT_RE.search(url)
    if match:
        return "Attachment", match.group(2), match.group(1)
    match = _GUILD_AVATAR_RE.search(url)
    if match:
        return "Guild Avatar", match.group(2), match.group(1)
    match = _AVATAR_RE.search(url)
    if match:
        return "Avatar", match.group(1), ""
    match = _EMOJI_RE.search(url)
    if match:
        return "Emoji", match.group(1), ""
    match = _STICKER_RE.search(url)
    if match:
        return "Sticker", match.group(1) or match.group(2), ""
    match = _ICON_RE.search(url)
    if match:
        return "Guild Icon", match.group(1), ""
    match = _BANNER_RE.search(url)
    if match:
        return "Banner", match.group(1), ""
    match = _EXTERNAL_RE.search(url)
    if match:
        return "External Image", "", ""
    return "", "", ""


def attachment_filename(url):
    match = _ATTACHMENT_RE.search(url)
    return unquote(match.group(3)) if match else ""


class DiscordCacheScan:
    """Everything the Discord artifacts need from one pass over the cache."""

    def __init__(self):
        self.records = []          # lightweight row per cached response
        self.messages = {}         # message id -> {"message", "source", "cached"}
        self.profiles = {}         # user id -> {"profile", "source"}
        self.users = {}            # user id -> merged user object + provenance
        self.channels = {}         # channel id -> merged channel object
        self.guilds = {}           # guild id -> merged guild object
        self.reactions = []
        self.searches = []
        self.notes = []
        self.invites = []
        self.media = {}            # cache path -> media descriptor
        self.entry_count = 0
        self.source_paths = set()

    # -- population helpers ------------------------------------------------ #

    def note_user(self, user, seen_in, when):
        if not isinstance(user, dict) or not user.get("id"):
            return
        uid = user["id"]
        record = self.users.setdefault(uid, {
            "id": uid, "username": "", "global_name": "", "discriminator": "",
            "bot": False, "avatar": "", "seen_in": set(), "first_seen": None,
            "last_seen": None,
        })
        for field in ("username", "global_name", "discriminator", "avatar"):
            if user.get(field) and not record[field]:
                record[field] = user[field]
        if user.get("bot"):
            record["bot"] = True
        record["seen_in"].add(seen_in)
        if isinstance(when, datetime):
            if record["first_seen"] is None or when < record["first_seen"]:
                record["first_seen"] = when
            if record["last_seen"] is None or when > record["last_seen"]:
                record["last_seen"] = when

    def note_channel(self, channel, source=""):
        if not isinstance(channel, dict) or not channel.get("id"):
            return
        cid = channel["id"]
        record = self.channels.setdefault(cid, {
            "id": cid, "name": "", "type": None, "guild_id": "", "topic": "",
            "recipients": "", "parent_id": "", "source": source,
        })
        if channel.get("name") and not record["name"]:
            record["name"] = channel["name"]
        if record["type"] is None and channel.get("type") is not None:
            record["type"] = channel["type"]
        for field in ("guild_id", "topic", "parent_id"):
            if channel.get(field) and not record[field]:
                record[field] = channel[field]
        recipients = channel.get("recipients") or []
        if recipients and not record["recipients"]:
            record["recipients"] = ", ".join(
                user_display(r) for r in recipients if isinstance(r, dict))
        for recipient in recipients:
            self.note_user(recipient, "DM channel", None)
        if channel.get("guild_id"):
            self.note_guild({"id": channel["guild_id"]}, source)

    def note_guild(self, guild, source=""):
        if not isinstance(guild, dict) or not guild.get("id"):
            return
        gid = str(guild["id"])
        record = self.guilds.setdefault(gid, {
            "id": gid, "name": "", "description": "", "member_count": None,
            "features": "", "vanity_url": "", "icon": "", "source": source,
        })
        for field in ("name", "description", "icon", "vanity_url_code"):
            key = "vanity_url" if field == "vanity_url_code" else field
            if guild.get(field) and not record[key]:
                record[key] = guild[field]
        for field in ("member_count", "approximate_member_count"):
            if guild.get(field) and record["member_count"] is None:
                record["member_count"] = guild[field]
        if guild.get("features") and not record["features"]:
            record["features"] = ", ".join(
                str(f) for f in guild["features"] if isinstance(f, str))

    def add_message(self, message, source, cached_at):
        if not isinstance(message, dict) or not message.get("id"):
            return
        mid = message["id"]
        existing = self.messages.get(mid)
        # Keep the most recently cached copy: it reflects the latest edit state.
        if existing and isinstance(existing["cached"], datetime) \
                and isinstance(cached_at, datetime) and existing["cached"] >= cached_at:
            return
        self.messages[mid] = {"message": message, "source": source, "cached": cached_at}
        sent = iso_to_datetime(message.get("timestamp")) or snowflake_to_datetime(mid)
        self.note_user(message.get("author"), "Message author", sent)
        for mention in message.get("mentions") or []:
            self.note_user(mention, "Mentioned", sent)
        if message.get("channel_id"):
            self.note_channel({"id": message["channel_id"]}, source)


def _decode_json(entry):
    body = entry.decoded_body()
    if not body:
        return None
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None


def find_local_account(files_found):
    """Identify the signed-in account from the Sentry scope and Local Storage.

    Returns a dict with whatever could be established: ``id``, ``username``,
    ``email`` and ``ids`` (every account id seen, for multi-account installs).
    """
    account = {"id": "", "username": "", "email": "", "ids": set()}

    for file_found in files_found:
        file_found = str(file_found)
        if not file_found.endswith("scope_v3.json"):
            continue
        try:
            with open(file_found, "r", encoding="utf-8", errors="replace") as handle:
                scope = json.load(handle)
        except (OSError, ValueError):
            continue
        user = (scope.get("scope") or {}).get("user") or {}
        if user.get("id"):
            account["id"] = account["id"] or str(user["id"])
            account["ids"].add(str(user["id"]))
        account["username"] = account["username"] or user.get("username", "")
        account["email"] = account["email"] or user.get("email", "")

    try:
        from scripts.chromium.local_storage import leveldb_folders, read_records
    except ImportError:
        return account

    for folder in leveldb_folders(files_found):
        try:
            records = list(read_records(folder))
        # Deliberately broad: one malformed cached response must not stop the scan.
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        for record in sorted(records, key=lambda r: -r.sequence):
            if record.key == "MultiAccountStore":
                try:
                    state = json.loads(record.value).get("_state") or {}
                except ValueError:
                    continue
                for user in state.get("users") or []:
                    if user.get("id"):
                        account["ids"].add(str(user["id"]))
                        if not account["id"]:
                            account["id"] = str(user["id"])
                        if not account["username"]:
                            account["username"] = user.get("username", "")
            elif record.key == "tokens":
                try:
                    tokens = json.loads(record.value)
                except ValueError:
                    continue
                for key in tokens:
                    if key.isdigit():
                        account["ids"].add(key)
                        if not account["id"]:
                            account["id"] = key
    return account


_scan_cache = {}


def scan_cache(files_found, log=None):
    """Parse every Discord response in the cache.

    Memoised on the cache entry files alone, so artifacts that also search for
    logs or Local Storage share one scan with those that only search the cache.
    """
    entry_files = sorted(str(f) for f in files_found if str(f).endswith("_0"))
    digest = hashlib.sha1(
        "\n".join(entry_files).encode("utf-8", "replace")).hexdigest()
    cached = _scan_cache.get(digest)
    if cached is not None:
        return cached

    scan = DiscordCacheScan()
    for entry in iter_entries(entry_files):
        url = entry.url
        if not url:
            continue
        scan.entry_count += 1
        cached_at = base_time_to_datetime(entry.response_time)
        requested_at = base_time_to_datetime(entry.request_time)

        kind, owner_id, related_id = media_kind(url)
        if kind:
            scan.media[entry.path] = {
                "kind": kind, "owner_id": owner_id, "related_id": related_id,
                "url": url, "content_type": entry.content_type,
                "size": entry.body_size, "requested": requested_at,
                "cached": cached_at, "status": entry.status_code,
            }

        if not _STATIC_ASSET_RE.match(url):
            parsed = urlparse(url)
            scan.records.append({
                "requested": requested_at, "cached": cached_at,
                "host": parsed.netloc, "path": parsed.path,
                "query": parsed.query, "url": url,
                "status": entry.status_code,
                "content_type": entry.content_type,
                "size": entry.body_size, "kind": kind,
                "source": entry.path,
            })

        api_match = _API_RE.match(url)
        if not api_match:
            continue
        endpoint = api_match.group(2)
        if entry.status_code and entry.status_code >= 400:
            continue
        scan.source_paths.add(entry.path)

        try:
            _parse_api_entry(scan, entry, endpoint, cached_at, requested_at)
        # Deliberately broad: a damaged LevelDB must not stop key discovery.
        except Exception as ex:  # a single malformed response must not stop the scan  # pylint: disable=broad-exception-caught
            if log:
                log(f"Discord: could not parse cached '{endpoint}': {ex}")

    _scan_cache[digest] = scan
    return scan


def _parse_api_entry(scan, entry, endpoint, cached_at, requested_at):
    """Route one cached API response to the collection that understands it."""
    match = _MESSAGES_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, list):
            for message in payload:
                scan.add_message(message, entry.path, cached_at)
        return

    match = _MESSAGE_SEARCH_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        query = parse_qs(urlparse(entry.url).query)
        terms = ", ".join(query.get("content", []))
        hits = []
        # Discord searches can filter without a search term at all (everything
        # from an author, everything with an attachment, and so on).
        filters = "; ".join(
            f"{name}={', '.join(values)}"
            for name, values in sorted(query.items())
            if name in _SEARCH_FILTER_PARAMS)
        if isinstance(payload, dict):
            for group in payload.get("messages") or []:
                for message in (group if isinstance(group, list) else [group]):
                    scan.add_message(message, entry.path, cached_at)
                    if isinstance(message, dict) and message.get("hit"):
                        hits.append(message)
            for channel in payload.get("channels") or []:
                scan.note_channel(channel, entry.path)
        scan.searches.append({
            "type": "Message search",
            "scope": f"{match.group(1).rstrip('s')} {match.group(2)}",
            "terms": terms,
            "filters": filters,
            "results": (payload or {}).get("total_results") if isinstance(payload, dict) else None,
            "requested": requested_at, "cached": cached_at,
            "url": entry.url, "source": entry.path,
            "hits": hits,
        })
        return

    match = _REACTIONS_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        emoji = unquote(match.group(3))
        if isinstance(payload, list):
            for user in payload:
                scan.note_user(user, "Reacted to message", cached_at)
                scan.reactions.append({
                    "channel_id": match.group(1), "message_id": match.group(2),
                    "emoji": emoji, "user": user,
                    "cached": cached_at, "source": entry.path,
                })
        return

    match = _PROFILE_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, dict) and payload.get("user"):
            scan.profiles[match.group(1)] = {"profile": payload, "source": entry.path,
                                             "cached": cached_at}
            scan.note_user(payload["user"], "Profile viewed", cached_at)
        return

    match = _CHANNEL_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, dict):
            scan.note_channel(payload, entry.path)
        return

    match = _GUILD_PROFILE_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, dict) and payload.get("name"):
            scan.note_guild(payload, entry.path)
        return

    match = _INVITE_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, dict) and payload.get("code"):
            scan.invites.append({"invite": payload, "cached": cached_at,
                                 "source": entry.path})
            scan.note_user(payload.get("inviter"), "Invite creator", cached_at)
            guild = payload.get("guild")
            if guild:
                guild = dict(guild)
                guild.setdefault("approximate_member_count",
                                 payload.get("approximate_member_count"))
                scan.note_guild(guild, entry.path)
            if payload.get("channel"):
                channel = dict(payload["channel"])
                if guild and guild.get("id"):
                    channel.setdefault("guild_id", guild["id"])
                scan.note_channel(channel, entry.path)
        return

    match = _GIF_SEARCH_RE.match(endpoint)
    if match:
        query = parse_qs(urlparse(entry.url).query)
        scan.searches.append({
            "type": "GIF search" if match.group(1) == "search" else "GIF trending",
            "scope": ", ".join(query.get("provider", [])),
            "terms": ", ".join(query.get("q", [])),
            "filters": "",
            "results": None, "requested": requested_at, "cached": cached_at,
            "url": entry.url, "source": entry.path, "hits": [],
        })
        return

    match = _NOTE_RE.match(endpoint)
    if match:
        payload = _decode_json(entry)
        if isinstance(payload, dict) and payload.get("note"):
            scan.notes.append({"user_id": match.group(1), "note": payload["note"],
                               "cached": cached_at, "source": entry.path})
