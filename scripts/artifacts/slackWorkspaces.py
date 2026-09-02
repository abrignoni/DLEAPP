__artifacts_v2__ = {
    "slackWorkspaces": {
        "name": "Slack Workspaces",
        "description": "Workspaces the Slack desktop app has been signed into, "
                       "parsed from its 'localConfig_v2' Local Storage key: "
                       "each workspace's name, URL, per-workspace user ID and "
                       "domain, which workspace was last active, the client's "
                       "own most-recently-used and version timestamps, the "
                       "channel or DM last open in it, and a per-workspace "
                       "session token. Because Local Storage is a LevelDB, "
                       "superseded versions of the key are recovered too, so "
                       "an earlier set of workspaces can appear alongside the "
                       "current one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Slack (Desktop)",
        "notes": "Session tokens (xoxc-/xoxb-/xoxp-/xoxs-/xoxr-/xoxd- prefixed) "
                 "are masked to the first 8 and last 4 characters, in the "
                 "Token column and inside Other Fields, since a full token is "
                 "a live credential. 'Most Recently Used' and 'Version "
                 "Timestamp' are two independent client-recorded times, not a "
                 "range, and are reported as separate columns. Purely cosmetic "
                 "fields (theme colours, sidebar gradients) are dropped from "
                 "Other Fields; anything else stored per workspace is kept "
                 "there. Slack Desktop is closed source, so the field meanings "
                 "follow the observed localConfig_v2 structure; they were "
                 "validated against a constructed known-data fixture, not "
                 "confirmed against Slack's own documentation.",
        "paths": (
            "*/Slack/Local Storage/leveldb/*",
            "*/slack/Local Storage/leveldb/*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "briefcase",
        "sample_data": {
            "dleapp_slack_known": "Constructed known-data Slack Local Storage "
                "fixture (authored, not from a real device) | 3 workspace "
                "records: a current config with 2 workspaces and one "
                "superseded config with 1",
        },
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

# localConfig_v2 fields promoted to their own columns, plus purely cosmetic
# fields dropped from Other Fields.
_NOISE_FIELDS = {
    "token", "name", "url", "user_id", "domain",
    "mostRecentlyUsedDate", "versionDataTs", "lastRoute", "lastViewState",
    "icon", "channelSidebarBackground", "teamSwitcherBackground",
    "textColor", "customTheme", "windowGradient", "iaTheming",
    "topNavBackground", "topNavTextColor", "theme",
}

_READ_ERRORS = (OSError, ValueError, EOFError, IndexError, KeyError,
                struct.error, zlib.error)


def _mask_tokens(text):
    if not text:
        return text

    def _mask(match):
        token = match.group(0)
        if len(token) <= 12:
            return "[redacted token]"
        return f"{token[:8]}...[redacted]...{token[-4:]}"

    return _TOKEN_RE.sub(_mask, text)


def _parse_iso8601(value):
    if not value or not isinstance(value, str):
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""


def _epoch_seconds_to_dt(value):
    if not value:
        return ""
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return ""


def _records(context):
    records = []
    for folder in leveldb_folders([str(f) for f in context.get_files_found()]):
        try:
            for record in read_records(folder):
                if record.origin and "slack.com" not in record.origin.lower():
                    continue
                records.append(record)
        except _READ_ERRORS as ex:
            logfunc(f"Slack Workspaces: could not read '{folder}': {ex}")
    records.sort(key=lambda record: -record.sequence)
    return records


def _load_json(record):
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
        source_path = source_path or context.get_relative_path(record.source)
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
        key=lambda row: row[5] if isinstance(row[5], datetime)
        else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    logfunc(f"Slack Workspaces: {len(data_list)} workspace record(s) recovered.")
    return data_headers, data_list, source_path
