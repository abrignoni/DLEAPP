__artifacts_v2__ = {
    "slackWorkspaces": {
        "name": "Slack Workspaces",
        "description": "Workspace/team enumeration parsed from the Slack "
                       "desktop app's 'localConfig_v2' Local Storage key. This "
                       "single key lists every workspace the local user account "
                       "has been signed into, each workspace's name, URL and "
                       "per-workspace user ID, which workspace was last active, "
                       "when that workspace was last used (from the client's own "
                       "mostRecentlyUsedDate/versionDataTs fields), which channel "
                       "or DM was last open in it, and a session token per "
                       "workspace. Because Local Storage is a LevelDB, "
                       "superseded versions of this key (e.g. before a "
                       "workspace was removed, or from an earlier session) can "
                       "also be recovered, giving a history of workspace usage "
                       "over time rather than only the current state.",
        "author": "@Gear-I",
        "creation_date": "2026-08-10",
        "last_update_date": "2026-08-10",
        "requirements": "none",
        "category": "Slack (Windows)",
        "notes": "Session tokens (xoxc-/xoxb-/xoxp-/xoxs-/xoxr-/xoxd- prefixed) "
                 "are masked to the first 8 and last 4 characters, both in the "
                 "Token column and inside Other Fields, since a full token is "
                 "a live credential rather than a normal artifact value. "
                 "'Most Recently Used' and 'Version Timestamp' are two "
                 "independent client-recorded times, not a range; they are "
                 "reported as separate columns to avoid implying an order that "
                 "isn't in the source data. Purely cosmetic fields (theme "
                 "colors, sidebar gradients) are dropped from 'Other Fields'; "
                 "anything else Slack stores per-team is preserved there "
                 "(token masked) since it varies by client version.",
        "paths": (
            '*/Slack/Local Storage/leveldb/*',
            '*/slack/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "briefcase",
    },
}

import json
import re
import struct
import zlib
from datetime import datetime, timezone

from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc

_TOKEN_RE = re.compile(r"xox[a-z]-[A-Za-z0-9-]+")

# Purely cosmetic localConfig_v2 fields that add noise without forensic value,
# plus fields promoted to their own columns (token/name/url/user_id/domain/
# mostRecentlyUsedDate/versionDataTs/lastRoute/lastViewState).
_NOISE_FIELDS = {
    "token", "name", "url", "user_id", "domain",
    "mostRecentlyUsedDate", "versionDataTs", "lastRoute", "lastViewState",
    "icon", "channelSidebarBackground", "teamSwitcherBackground",
    "textColor", "customTheme", "windowGradient", "iaTheming",
    "topNavBackground", "topNavTextColor",
}

# Exceptions a damaged/truncated LevelDB folder can raise while being read or
# while parsing a malformed record; caught explicitly rather than blanket
# 'except Exception' so a corrupted folder can't silently swallow bugs.
_READ_ERRORS = (OSError, ValueError, EOFError, IndexError, KeyError,
                struct.error, zlib.error)


def _mask_tokens(text):
    """Mask any Slack session token substring, keeping a recognizable prefix."""
    if not text:
        return text

    def _mask(match):
        token = match.group(0)
        if len(token) <= 12:
            return "[redacted token]"
        return f"{token[:8]}...[redacted]...{token[-4:]}"

    return _TOKEN_RE.sub(_mask, text)


def _parse_iso8601(value):
    """Parse a 'Z'-suffixed ISO 8601 string (e.g. mostRecentlyUsedDate)."""
    if not value or not isinstance(value, str):
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""


def _epoch_seconds_to_dt(value):
    """Convert a Unix epoch-seconds value (e.g. versionDataTs) to UTC."""
    if not value:
        return ""
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return ""


def _records(context):
    """All Local Storage records for the Slack origins, newest sequence first."""
    records = []
    for folder in leveldb_folders([str(f) for f in context.get_files_found()]):
        try:
            for record in read_records(folder):
                if record.origin and "slack.com" not in record.origin.lower():
                    continue
                records.append(record)
        # A damaged LevelDB (truncated log, bad checksum, malformed record)
        # must not stop the rest of the artifact from running, so the known
        # failure modes of file access and binary/record parsing are caught
        # explicitly here rather than letting one folder abort the module.
        except _READ_ERRORS as ex:
            logfunc(f"Slack Workspaces: could not read '{folder}': {ex}")
    records.sort(key=lambda record: -record.sequence)
    return records


def _load_json(record):
    """Parse a record's Local Storage value as JSON, or None if it isn't."""
    try:
        return json.loads(record.value)
    except (ValueError, TypeError):
        return None


@artifact_processor
def slackWorkspaces(context):
    data_headers = (
        "Team ID", "Team Name", "Team URL", "User ID", "Domain",
        ("Most Recently Used", "datetime"), ("Version Timestamp", "datetime"),
        "Last Viewed Channel/DM ID", "Token (masked)", "Last Active",
        "Other Fields", "LevelDB Sequence", "Record State", "Source File",
    )

    data_list = []
    seen = set()
    source_path = ""

    for record in _records(context):
        if record.key != "localConfig_v2":
            continue
        config = _load_json(record)
        if not isinstance(config, dict):
            continue
        teams = config.get("teams")
        if not isinstance(teams, dict):
            continue
        source_path = source_path or record.source
        last_active_id = config.get("lastActiveTeamId")

        for team_id, team in teams.items():
            if not isinstance(team, dict):
                continue

            token_raw = team.get("token", "")
            token_masked = _mask_tokens(token_raw) if token_raw else ""

            most_recently_used = _parse_iso8601(team.get("mostRecentlyUsedDate"))
            version_ts = _epoch_seconds_to_dt(team.get("versionDataTs"))

            last_route = team.get("lastRoute")
            last_entity_id = ""
            if isinstance(last_route, dict):
                last_entity_id = (last_route.get("params") or {}).get("entityId", "")

            other = {
                k: (_mask_tokens(v) if isinstance(v, str) else v)
                for k, v in team.items()
                if k not in _NOISE_FIELDS
            }

            key = (record.sequence, team_id, team.get("name"), team.get("url"), token_masked)
            if key in seen:
                continue
            seen.add(key)

            data_list.append((
                team_id,
                team.get("name", ""),
                team.get("url", ""),
                team.get("user_id", ""),
                team.get("domain", ""),
                most_recently_used,
                version_ts,
                last_entity_id,
                token_masked,
                "Yes" if team_id == last_active_id else "",
                json.dumps(other, ensure_ascii=False) if other else "",
                record.sequence,
                record.state,
                context.get_relative_path(record.source),
            ))

    data_list.sort(
        key=lambda row: row[5] if isinstance(row[5], datetime) else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    logfunc(f"Slack Workspaces: {len(data_list)} workspace record(s) recovered.")
    return data_headers, data_list, source_path