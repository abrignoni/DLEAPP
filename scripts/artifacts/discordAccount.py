__artifacts_v2__ = {
    "discordAccount": {
        "name": "Discord Account & Application",
        "description": "The account signed in to Discord Desktop together with "
                       "the application, device and operating system values the "
                       "client itself recorded about the machine it was running "
                       "on. They identify the installation that the other "
                       "artifacts in this category were parsed from. The "
                       "time zone recorded here is the one the log-derived "
                       "artifacts (Channel Navigation, Gateway Sessions) must "
                       "be read against, since those are written in device "
                       "local time. The "
                       "Sentry crash-reporting scope is the richest single "
                       "source: it names the account, the app build and the "
                       "hardware, and it is written on every run.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Reads sentry/scope_v3.json, settings.json, Preferences, "
                 "Local State, ShipIt_request.json and the account stores in "
                 "Local Storage. Authentication tokens are reported as present "
                 "or absent, never printed.",
        "paths": (
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/settings.json',
            '*/discord*/Preferences',
            '*/discord*/Local State',
            '*/discord*/ShipIt_request.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
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
    source_path = ""
    files_found = [str(f) for f in context.get_files_found()]

    def add(prop, value, path):
        if value not in (None, "", [], {}):
            data_list.append((prop, str(value), context.get_relative_path(path)))

    for file_found in files_found:
        name = os.path.basename(file_found)

        if name == "scope_v3.json":
            scope = _read_json(file_found)
            if not scope:
                continue
            source_path = source_path or file_found
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
            source_path = source_path or file_found
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
            source_path = source_path or file_found
            dictionaries = ((prefs.get("spellcheck") or {}).get("dictionaries") or [])
            add("Spellcheck Dictionaries", ", ".join(dictionaries), file_found)
            salt = ((prefs.get("electron") or {}).get("media") or {}).get("device_id_salt")
            add("Media Device ID Salt", salt, file_found)

        elif name == "ShipIt_request.json":
            request = _read_json(file_found)
            if not isinstance(request, dict):
                continue
            source_path = source_path or file_found
            add("Installed Bundle", request.get("targetBundleURL"), file_found)
            add("Update Bundle", request.get("updateBundleURL"), file_found)
            add("Bundle Identifier", request.get("bundleIdentifier"), file_found)

    for folder in leveldb_folders(files_found):
        try:
            records = sorted(read_records(folder), key=lambda r: -r.sequence)
        except Exception as ex:
            logfunc(f"Discord Account: could not read Local Storage '{folder}': {ex}")
            continue
        source_path = source_path or folder
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
    return data_headers, data_list, source_path
