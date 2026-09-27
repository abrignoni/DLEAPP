__artifacts_v2__ = {
    "discordDrafts": {
        "name": "Discord Message Drafts",
        "description": "Message drafts from Discord's DraftStore key in Local Storage: each stored version of a "
                       "draft, with the time the client saved it and the channel it was for. Whether a draft was "
                       "ever sent cannot be determined from this artifact.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Discord's client script saves a draft whenever a DRAFT_CHANGE or DRAFT_SAVE action "
                 "carries text that differs from the stored draft, stamping it with the time of that "
                 "change, and removes it when the text is empty or a DRAFT_CLEAR arrives (DraftStore in "
                 "https://discord.com/assets/web.b8b5ddfa0f88ae29.js, the newest client build in the "
                 "tested macOS profile's cache). LevelDB keeps a superseded value until a compaction drops "
                 "it "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/doc/impl.md#L104), "
                 "so every surviving version of the DraftStore key is read and a draft appears once for "
                 "each distinct text and time stored: on discord_macos the 64 rows were versions of drafts "
                 "for 5 channels, up to 36 for one channel. Draft Saved is the stored timestamp of that "
                 "version. Draft Type names the draft type with the client's own DraftType names in the "
                 "same script, and a number outside them is shown as Type and the number; Draft Type was "
                 "Channel message on all 64 rows of discord_macos. Account ID is the account the draft is "
                 "stored under, and Account ID held one value on all 64 rows of discord_macos. LevelDB "
                 "Sequence is the record's sequence number, which LevelDB assigns in increasing order as "
                 "it writes "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/db/db_impl.cc#L1223-L1228), "
                 "so the highest one for a draft is its latest stored version. Record State is the record "
                 "type, Live for a stored value and Deleted for a deletion marker "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/db/dbformat.h#L54), "
                 "and Record State was Live on all 64 rows of discord_macos. Source File names the LevelDB "
                 "file each version was read from.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "edit-3",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 64 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 64 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordActivity": {
        "name": "Discord Client Activity",
        "description": "Channel and server selection state from Discord's Local Storage: channels and servers "
                       "the client moved to, the last channel per server, recent text, voice and selected "
                       "channels, the selected voice channel and the client's session times.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Each row comes from one Local Storage key, and the event names follow what Discord's "
                 "client script does with that key (https://discord.com/assets/web.b8b5ddfa0f88ae29.js, "
                 "the newest client build in the tested macOS profile's cache). Channel or server selected "
                 "is an entry of FrecencyStore's pendingUsages, which the client records with the channel "
                 "or server ID that a CHANNEL_SELECT or VOICE_CHANNEL_SELECT moved to and clears once it "
                 "has saved those usages to its settings; at least 13 of the 83 such rows on discord_macos "
                 "named a server, their IDs being servers in SelectedGuildStore. Server selected or left "
                 "is SelectedGuildStore's selectedGuildTimestampMillis, which the client sets for a server "
                 "when a channel selection moves into or out of it, and for the selected server when a "
                 "connection opens. Last channel for server is SelectedChannelStore's selectedChannelIds, "
                 "pairing a server with a channel. Recent voice channel and Recent text channel are "
                 "RecentVoiceChannelStore's lists, which the client updates when a voice channel or a "
                 "server text channel is selected, keeping the ten most recent with the latest at position "
                 "1. Recently selected channel is QuickSwitcherStore's channelHistory, which the client "
                 "updates on every channel selection, not only through the quick switcher, keeping the "
                 "eight most recent with the latest at position 1. Selected voice channel (state) is "
                 "SelectedChannelStore's selectedVoiceChannelId with its lastConnectedTime; the client "
                 "sets lastConnectedTime when its own voice state changes and every 60 seconds while it "
                 "stays in a voice channel, so the time is the last such update rather than a join time. "
                 "Client session started and Client session last used come from the "
                 "LAST_CLIENT_HEARTBEAT_SESSION key: the client starts a new session when it is active and "
                 "30 minutes have passed since the last one was used, updates lastUsedTimestamp while "
                 "active, and counts itself active only when in the foreground or connected to a call. "
                 "Rows come from every surviving version of each key, as the Discord Message Drafts notes "
                 "describe, and a row repeated across versions is reported once. Entries with no stored "
                 "time are reported without one; a list entry carries its position in Detail, and Last "
                 "channel for server carries the server.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 303 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 303 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordLocalStorage": {
        "name": "Discord Local Storage",
        "description": "Local Storage records from Discord's LevelDB store, including superseded values and "
                       "deletion markers it still holds.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Reads the Local Storage LevelDB table and log files directly rather than a compacted "
                 "view. A LevelDB entry is a value or a deletion marker "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/doc/impl.md#L24-L26), "
                 "and a value that was overwritten or deleted stays until a compaction drops it "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/doc/impl.md#L104), "
                 "so a value the app has since changed or deleted can still appear here. Record State is "
                 "Live for a stored value and Deleted for a deletion marker "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/db/dbformat.h#L54), "
                 "and the highest LevelDB Sequence for a key is its latest write "
                 "(https://github.com/google/leveldb/blob/7ee830d02b623e8ffe0b95d59a74db1e58da04c5/db/db_impl.cc#L1223-L1228): "
                 "discord_macos held 654 records of 192 keys, 60 of them deletion markers. Origin is the "
                 "site the key belongs to, and Origin held https://discordapp.com on all 92 rows of "
                 "pc_mus_001_win11. Values are cut at 5,000 characters in the report, Value Length gives "
                 "the full length, and the value of the tokens key is replaced with a redaction note.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 654 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 654 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 92 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json
from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc

_VALUE_LIMIT = 5000
_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)
_REDACTED_KEYS = {"tokens"}

# DraftStore keeps each draft under a draft type number; these are the names the
# client's own DraftType enumeration gives them (Discord's client script
# https://discord.com/assets/web.b8b5ddfa0f88ae29.js). Other numbers are shown as stored.
_DRAFT_TYPES = {
    "0": "Channel message", "1": "Thread settings", "2": "First thread message",
    "3": "Application launcher command", "4": "Poll", "5": "Slash command",
    "6": "Forward context message", "7": "Interaction modal",
}


def _records(context):
    """All Local Storage records for the Discord origins, newest sequence first."""
    records = []
    for folder in leveldb_folders([str(f) for f in context.get_files_found()]):
        try:
            records.extend(read_records(folder))
        # Deliberately broad: a damaged LevelDB must not stop the artifact.
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Discord Local Storage: could not read '{folder}': {ex}")
    records.sort(key=lambda record: -record.sequence)
    return records


def _load_state(record):
    try:
        payload = json.loads(record.value)
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload.get("_state", payload)


@artifact_processor
def discordDrafts(context):
    data_headers = (
        ("Draft Saved", "datetime"), "Draft Text", "Channel ID", "Account ID",
        "Draft Type", "LevelDB Sequence", "Record State", "Source File",
    )

    data_list = []
    seen = set()
    sources = set()
    for record in _records(context):
        if record.key != "DraftStore":
            continue
        state = _load_state(record)
        if not isinstance(state, dict):
            continue
        for account_id, channels in state.items():
            if not isinstance(channels, dict):
                continue
            for channel_id, drafts in channels.items():
                if not isinstance(drafts, dict):
                    continue
                for draft_type, draft in drafts.items():
                    if not isinstance(draft, dict) or not draft.get("draft"):
                        continue
                    key = (account_id, channel_id, draft_type,
                           draft.get("timestamp"), draft["draft"])
                    if key in seen:
                        continue
                    seen.add(key)
                    sources.add(record.source)
                    data_list.append((
                        discord_api.epoch_ms_to_datetime(draft.get("timestamp")),
                        draft["draft"],
                        channel_id,
                        account_id,
                        _DRAFT_TYPES.get(str(draft_type), f"Type {draft_type}"),
                        record.sequence,
                        record.state,
                        context.get_relative_path(record.source),
                    ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Discord Message Drafts: {len(data_list)} draft version(s) recovered.")
    return data_headers, data_list, "\n".join(sorted(sources))


@artifact_processor
def discordActivity(context):
    data_headers = (
        ("Timestamp", "datetime"), "Event", "Target ID", "Detail",
        "Local Storage Key", "LevelDB Sequence", "Source File",
    )

    data_list = []
    seen = set()
    sources = set()

    def add(timestamp, event, target, detail, record):
        key = (timestamp, event, target, detail)
        if key in seen:
            return
        seen.add(key)
        sources.add(record.source)
        data_list.append((timestamp, event, target, detail, record.key,
                          record.sequence, context.get_relative_path(record.source)))

    for record in _records(context):
        state = None
        if record.key in ("FrecencyStore", "SelectedGuildStore", "RecentVoiceChannelStore",
                          "QuickSwitcherStore", "SelectedChannelStore",
                          "LAST_CLIENT_HEARTBEAT_SESSION"):
            state = _load_state(record)
        if state is None:
            continue

        # The labels follow what Discord's client script does with each store
        # (https://discord.com/assets/web.b8b5ddfa0f88ae29.js): FrecencyStore
        # records the channel or server a CHANNEL_SELECT or VOICE_CHANNEL_SELECT
        # moved to, SelectedGuildStore stamps a server when a selection moves into
        # or out of it, and QuickSwitcherStore keeps the latest selected channels.
        if record.key == "FrecencyStore":
            for usage in state.get("pendingUsages") or []:
                if not isinstance(usage, dict):
                    continue
                add(discord_api.epoch_ms_to_datetime(usage.get("timestamp")),
                    "Channel or server selected", str(usage.get("key") or ""), "", record)

        elif record.key == "SelectedGuildStore":
            for guild_id, when in (state.get("selectedGuildTimestampMillis") or {}).items():
                add(discord_api.epoch_ms_to_datetime(when), "Server selected or left",
                    str(guild_id), "", record)

        elif record.key == "SelectedChannelStore":
            connected = state.get("lastConnectedTime") if isinstance(state, dict) else None
            if state.get("selectedVoiceChannelId"):
                # lastConnectedTime and selectedVoiceChannelId are independent
                # members of one rolling state object. The store does not record
                # that this time belongs to this channel, so the row is labelled
                # as state rather than as a join event.
                add(discord_api.epoch_ms_to_datetime(connected),
                    "Selected voice channel (state)",
                    str(state["selectedVoiceChannelId"]),
                    "timestamp is the store's lastConnectedTime", record)
            for guild_id, channel_id in (state.get("selectedChannelIds") or {}).items():
                add("", "Last channel for server", str(channel_id),
                    f"server {guild_id}", record)

        elif record.key == "RecentVoiceChannelStore":
            for position, channel_id in enumerate(state.get("voiceChannelHistory") or [], 1):
                add("", "Recent voice channel", str(channel_id),
                    f"position {position}", record)
            for position, channel_id in enumerate(state.get("textChannelHistory") or [], 1):
                add("", "Recent text channel", str(channel_id),
                    f"position {position}", record)

        elif record.key == "QuickSwitcherStore":
            for position, channel_id in enumerate(state.get("channelHistory") or [], 1):
                add("", "Recently selected channel", str(channel_id),
                    f"position {position}", record)

        elif record.key == "LAST_CLIENT_HEARTBEAT_SESSION":
            session = state if isinstance(state, dict) else {}
            add(discord_api.epoch_ms_to_datetime(session.get("createdAtTimestamp")),
                "Client session started", session.get("uuid", ""), "", record)
            add(discord_api.epoch_ms_to_datetime(session.get("lastUsedTimestamp")),
                "Client session last used", session.get("uuid", ""), "", record)

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN,
                   reverse=True)
    logfunc(f"Discord Client Activity: {len(data_list)} event(s) recovered.")
    return data_headers, data_list, "\n".join(sorted(sources))


@artifact_processor
def discordLocalStorage(context):
    data_headers = (
        "Origin", "Key", "Value", "Value Length", "LevelDB Sequence",
        "Record State", "Source File",
    )

    data_list = []
    sources = set()
    for record in _records(context):
        sources.add(record.source)
        if record.key in _REDACTED_KEYS and record.value:
            value = "[redacted: authentication token]"
        else:
            value = record.value
            if len(value) > _VALUE_LIMIT:
                value = f"{value[:_VALUE_LIMIT]}... [truncated]"
        data_list.append((
            record.origin,
            record.key,
            value,
            len(record.value),
            record.sequence,
            record.state,
            context.get_relative_path(record.source),
        ))

    logfunc(f"Discord Local Storage: {len(data_list)} record version(s).")
    return data_headers, data_list, "\n".join(sorted(sources))
