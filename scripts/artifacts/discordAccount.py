__artifacts_v2__ = {
    "discordAccount": {
        "name": "Discord Account & Application",
        "description": "Values the Discord client recorded about its account, application, device and operating "
                       "system, from its Sentry scope file, settings.json, Preferences and ShipIt_request.json "
                       "and the MultiAccountStore, tokens and fingerprint keys in Local Storage.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "sentry/scope_v3.json has the name, folder and layout (a scope and an event) of the file "
                 "Sentry's Electron SDK keeps to persist context beyond a crash "
                 "(https://github.com/getsentry/sentry-electron/blob/630c5533d6e750c897c26ecc88558e60e32c53e1/src/main/integrations/sentry-minidump/index.ts#L40), "
                 "writing the current scope with the default event values each time the scope changes "
                 "(https://github.com/getsentry/sentry-electron/blob/630c5533d6e750c897c26ecc88558e60e32c53e1/src/main/integrations/sentry-minidump/index.ts#L61-L68, "
                 "https://github.com/getsentry/sentry-electron/blob/630c5533d6e750c897c26ecc88558e60e32c53e1/src/main/integrations/sentry-minidump/index.ts#L226 "
                 "and "
                 "https://github.com/getsentry/sentry-electron/blob/630c5533d6e750c897c26ecc88558e60e32c53e1/src/main/store.ts#L40, "
                 "in the sentry folder of the app's user data folder: "
                 "https://github.com/getsentry/sentry-electron/blob/630c5533d6e750c897c26ecc88558e60e32c53e1/src/main/electron-normalize.ts#L19-L20), "
                 "so its rows describe the client as of the last such write. Account ID, Username and "
                 "Email Address come from the scope's user, and Account Created is the timestamp in that "
                 "ID, read with the layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156). "
                 "The other scope rows are the event's context values (such as Application Version, "
                 "Operating System, CPU and Time Zone), its release and environment, and the scope's "
                 "nativeBuildNumber tag, as stored. Time Zone is the scope's culture time zone as of that "
                 "write; the renderer log records no offset, so it does not show which zone the device "
                 "used when a log line was written (see Discord Channel Navigation). settings.json gives "
                 "Window Bounds and the listed settings as stored, and Preferences the spellcheck "
                 "dictionaries and the media device ID salt. ShipIt_request.json holds the fields of a "
                 "Squirrel.Mac ShipIt request, whose source describes updateBundleURL as the update bundle "
                 "that will replace targetBundleURL, targetBundleURL as where the update should be "
                 "installed, and bundleIdentifier as the bundle whose instances the installer waits to "
                 "terminate "
                 "(https://github.com/Squirrel/Squirrel.Mac/blob/5c9e2133c09d6f8e2e3c5a45c5b0ffc00448c58a/Squirrel/SQRLShipItRequest.h#L66-L73, "
                 "with the JSON keys at "
                 "https://github.com/Squirrel/Squirrel.Mac/blob/5c9e2133c09d6f8e2e3c5a45c5b0ffc00448c58a/Squirrel/SQRLShipItRequest.m#L62-L69); "
                 "they are reported as Update Bundle, Installed Bundle and Bundle Identifier. From Local "
                 "Storage come each MultiAccountStore user as Local Storage Account, each key of the "
                 "tokens key as Authentication Token Stored For (an account ID, or another key marked "
                 "client) without the token itself, and the fingerprint key as Client Fingerprint, each "
                 "from the stored value with the highest sequence number, deletion markers aside. Source "
                 "File names the file each row came from, and the report's located-at line lists every "
                 "such file.",
        "paths": (
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/settings.json',
            '*/discord*/Preferences',
            '*/discord*/ShipIt_request.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 41 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 36 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 6 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json
import os

from scripts.chromium import discord_api
from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc

# Sentry context blocks worth surfacing, and the fields to take from each.
_CONTEXT_FIELDS = {
    "app": [("app_name", "Application"), ("app_version", "Application Version"),
            ("app_arch", "Application Architecture"),
            ("app_start_time", "Application Start Time")],
    "device": [("family", "Device Family"), ("arch", "Device Architecture"),
               ("cpu_description", "CPU"), ("processor_count", "CPU Cores"),
               ("memory_size", "Memory (bytes)"), ("boot_time", "Device Boot Time")],
    "os": [("name", "Operating System"), ("version", "OS Version"),
           ("build", "OS Build"), ("kernel_version", "Kernel Version")],
    "runtime": [("name", "Runtime"), ("version", "Runtime Version")],
    "chrome": [("version", "Chromium Version")],
    "node": [("version", "Node.js Version")],
    "culture": [("locale", "Locale"), ("timezone", "Time Zone")],
}


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


@artifact_processor
def discordAccount(context):
    data_headers = ("Property", "Value", "Source File")
    data_list = []
    sources = set()
    files_found = [str(f) for f in context.get_files_found()]

    def add(prop, value, path):
        if value not in (None, "", [], {}):
            data_list.append((prop, str(value), context.get_relative_path(path)))
            sources.add(path)

    for file_found in files_found:
        name = os.path.basename(file_found)

        if name == "scope_v3.json":
            scope = _read_json(file_found)
            if not scope:
                continue
            user = (scope.get("scope") or {}).get("user") or {}
            add("Account ID", user.get("id"), file_found)
            add("Username", user.get("username"), file_found)
            add("Email Address", user.get("email"), file_found)
            add("Account Created", discord_api.snowflake_to_datetime(user.get("id")),
                file_found)

            event = scope.get("event") or {}
            contexts = event.get("contexts") or {}
            for block, fields in _CONTEXT_FIELDS.items():
                values = contexts.get(block) or {}
                for key, label in fields:
                    add(label, values.get(key), file_found)
            add("Release", event.get("release"), file_found)
            add("Environment", event.get("environment"), file_found)
            add("Native Build Number",
                ((scope.get("scope") or {}).get("tags") or {}).get("nativeBuildNumber"),
                file_found)

        elif name == "settings.json":
            settings = _read_json(file_found)
            if not isinstance(settings, dict):
                continue
            bounds = settings.get("WINDOW_BOUNDS") or {}
            if bounds:
                add("Window Bounds",
                    f"x={bounds.get('x')} y={bounds.get('y')} "
                    f"{bounds.get('width')}x{bounds.get('height')}", file_found)
            for key in ("enableHardwareAcceleration", "openH264Enabled",
                        "MinimizeToTray", "OPEN_ON_STARTUP", "START_MINIMIZED",
                        "SKIP_HOST_UPDATE", "IS_MAXIMIZED", "IS_MINIMIZED"):
                if key in settings:
                    add(f"Setting: {key}", settings[key], file_found)

        elif name == "Preferences":
            prefs = _read_json(file_found)
            if not isinstance(prefs, dict):
                continue
            dictionaries = ((prefs.get("spellcheck") or {}).get("dictionaries") or [])
            add("Spellcheck Dictionaries", ", ".join(dictionaries), file_found)
            salt = ((prefs.get("electron") or {}).get("media") or {}).get("device_id_salt")
            add("Media Device ID Salt", salt, file_found)

        elif name == "ShipIt_request.json":
            request = _read_json(file_found)
            if not isinstance(request, dict):
                continue
            add("Installed Bundle", request.get("targetBundleURL"), file_found)
            add("Update Bundle", request.get("updateBundleURL"), file_found)
            add("Bundle Identifier", request.get("bundleIdentifier"), file_found)

    for folder in leveldb_folders(files_found):
        try:
            records = sorted(read_records(folder), key=lambda r: -r.sequence)
        # Deliberately broad: a damaged LevelDB must not stop the artifact.
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Discord Account: could not read Local Storage '{folder}': {ex}")
            continue
        reported = set()
        for record in records:
            if record.key in reported or not record.is_live:
                continue
            if record.key == "MultiAccountStore":
                try:
                    users = (json.loads(record.value).get("_state") or {}).get("users") or []
                except ValueError:
                    continue
                reported.add(record.key)
                for user in users:
                    label = user.get("username") or user.get("id")
                    add(f"Local Storage Account: {label}",
                        f"id={user.get('id')} discriminator={user.get('discriminator')}",
                        record.source)
            elif record.key == "tokens":
                try:
                    tokens = json.loads(record.value)
                except ValueError:
                    continue
                reported.add(record.key)
                # The token itself is a live credential; report only its presence.
                for token_key in tokens:
                    add("Authentication Token Stored For",
                        token_key if token_key.isdigit() else f"{token_key} (client)",
                        record.source)
            elif record.key == "fingerprint" and record.value:
                reported.add(record.key)
                add("Client Fingerprint", record.value.strip('"'), record.source)

    logfunc(f"Discord Account & Application: {len(data_list)} property value(s).")
    return data_headers, data_list, "\n".join(sorted(sources))
