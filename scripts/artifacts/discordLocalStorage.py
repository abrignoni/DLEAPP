__artifacts_v2__ = {
    "discordDrafts": {
        "name": "Discord Message Drafts",
        "description": "Message drafts held in Local Storage. Discord saves the "
                       "draft box as text is typed, and Local Storage is a "
                       "LevelDB, so superseded versions of the key stay on "
                       "disk. The result is successive saved versions of the "
                       "draft text, each with its own stored timestamp and "
                       "target channel. A row records what was in "
                       "the compose box at that time; whether it was ever sent "
                       "cannot be determined from this artifact alone.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Rows come from every surviving version of the DraftStore key, "
                 "so the same draft usually appears several times as it grew. "
                 "The highest sequence number is the most recent version.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "edit-3",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 64 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 64 rows",
        },
    },
    "discordActivity": {
        "name": "Discord Client Activity",
        "description": "Application usage reconstructed from the Local Storage "
                       "state Discord keeps between runs: channels opened and "
                       "when, servers selected, the selected voice channel, "
                       "quick switcher history and client session heartbeats. "
                       "This is "
                       "usage state that exists independently of any message "
                       "content: it records when the client opened channels, "
                       "selected servers and started sessions, whether or not "
                       "any message from those channels was cached.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Channel-open events come from the frecency store, which keeps "
                 "a rolling window of recent usages; older versions of the key "
                 "extend that window further back. Entries without a stored "
                 "timestamp are reported in order with no time. The 'Selected "
                 "voice channel (state)' row pairs the store's "
                 "lastConnectedTime with its selectedVoiceChannelId: both are "
                 "co-resident fields of one rolling state object, so the "
                 "pairing is inferred rather than a recorded association "
                 "between that time and that channel.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 303 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 303 rows",
        },
    },
    "discordLocalStorage": {
        "name": "Discord Local Storage",
        "description": "Raw Local Storage keys and values for the Discord "
                       "origins, including superseded and deleted versions "
                       "recovered from the LevelDB table and log files. Because "
                       "LevelDB does not overwrite in place, a value the app "
                       "has since changed or deleted can still be read here. "
                       "Use this when a store is not yet parsed into its own "
                       "artifact.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Values are truncated in the report at 5,000 characters. "
                 "Authentication token values are redacted.",
        "paths": ('*/discord*/Local Storage/leveldb/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 654 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 654 rows",
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
    source_path = ""
    for record in _records(context):
        if record.key != "DraftStore":
            continue
        state = _load_state(record)
        if not isinstance(state, dict):
            continue
        source_path = source_path or record.source
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
                    data_list.append((
                        discord_api.epoch_ms_to_datetime(draft.get("timestamp")),
                        draft["draft"],
                        channel_id,
                        account_id,
                        "Channel message" if draft_type == "0" else f"Type {draft_type}",
                        record.sequence,
                        record.state,
                        context.get_relative_path(record.source),
                    ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Discord Message Drafts: {len(data_list)} draft version(s) recovered.")
    return data_headers, data_list, source_path


@artifact_processor
def discordActivity(context):
    data_headers = (
        ("Timestamp", "datetime"), "Event", "Target ID", "Detail",
        "Local Storage Key", "LevelDB Sequence", "Source File",
    )

    data_list = []
    seen = set()
    source_path = ""

    def add(timestamp, event, target, detail, record):
        key = (timestamp, event, target, detail)
        if key in seen:
            return
        seen.add(key)
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
        source_path = source_path or record.source

        if record.key == "FrecencyStore":
            for usage in state.get("pendingUsages") or []:
                if not isinstance(usage, dict):
                    continue
                add(discord_api.epoch_ms_to_datetime(usage.get("timestamp")),
                    "Channel opened", str(usage.get("key") or ""), "", record)

        elif record.key == "SelectedGuildStore":
            for guild_id, when in (state.get("selectedGuildTimestampMillis") or {}).items():
                add(discord_api.epoch_ms_to_datetime(when), "Server selected",
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
                add("", "Quick switcher history", str(channel_id),
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
    return data_headers, data_list, source_path


@artifact_processor
def discordLocalStorage(context):
    data_headers = (
        "Origin", "Key", "Value", "Value Length", "LevelDB Sequence",
        "Record State", "Source File",
    )

    data_list = []
    source_path = ""
    for record in _records(context):
        source_path = source_path or record.source
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
    return data_headers, data_list, source_path
