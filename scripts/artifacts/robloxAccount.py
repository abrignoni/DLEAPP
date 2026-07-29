__artifacts_v2__ = {
    "robloxAccount": {
        "name": "Roblox Account & Application",
        "description": "Account identity and application state retained by Roblox "
                       "Desktop, including the user and display names, numeric user "
                       "ID, age bracket, locale, country, installation identifiers, "
                       "theme, subscription state and installed client version.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "Values are reported verbatim for evidentiary analysis, including "
                 "PlayerHydrationBlob and PlayerHydrationSignature. These values can "
                 "contain sensitive account state, but the parser does not classify "
                 "the signature as a reusable authentication credential. Timestamps "
                 "are UTC.",
        "paths": (
            "*/Library/Roblox/LocalStorage/appStorage.json",
            "*/Library/Preferences/com.roblox.RobloxPlayer.plist",
            "*/Library/Preferences/com.roblox.RobloxPlayerChannel.plist",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 28 rows",
        },
    },
    "robloxSettings": {
        "name": "Roblox Player Settings",
        "description": "Roblox player preferences from GlobalBasicSettings XML, "
                       "including chat, privacy-adjacent, accessibility, graphics, "
                       "audio, input and window settings.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "Compound XML values such as vectors are flattened into a compact "
                 "name=value representation.",
        "paths": (
            "*/Library/Roblox/GlobalBasicSettings_*.xml",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 74 rows",
        },
    },
}

import json
import os
import plistlib
import xml.etree.ElementTree as ET

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.roblox import compact_value, epoch_datetime, read_json


_ACCOUNT_ITEMS = {
    "UserId": "User ID",
    "Username": "Username",
    "DisplayName": "Display Name",
    "CountryCode": "Country Code",
    "RobloxLocaleId": "Roblox Locale",
    "GameLocaleId": "Game Locale",
    "Membership": "Membership",
    "HasRobloxSubscription": "Has Roblox Subscription",
    "IsUnder13": "Under 13",
    "AppInstallationId": "App Installation ID",
    "BrowserTrackerId": "Browser Tracker ID",
    "WebViewUserAgent": "WebView User Agent",
    "AuthenticatedTheme": "Authenticated Theme",
    "DeviceLevelTheme": "Device Theme",
    "PreviousAccountsList": "Previous Accounts",
    "UpdateControllerCacheChannel": "Update Channel",
    "AccountBlob": "Account Blob",
    "PlayerHydrationBlob": "Player Hydration Blob",
    "PlayerHydrationSignature": "Player Hydration Signature",
}


def _add(data, prop, value, path, context):
    if value not in (None, "", [], {}):
        data.append((prop, compact_value(value), context.get_relative_path(path)))


@artifact_processor
def robloxAccount(context):
    data_headers = ("Property", "Value", "Source File")
    data_list = []
    source_paths = []

    for file_found in map(str, context.get_files_found()):
        name = os.path.basename(file_found)
        if name == "appStorage.json":
            payload = read_json(file_found)
            if not isinstance(payload, dict):
                continue
            source_paths.append(file_found)
            for key, label in _ACCOUNT_ITEMS.items():
                _add(data_list, label, payload.get(key), file_found, context)

            hydration = payload.get("PlayerHydrationBlob")
            try:
                hydration = json.loads(hydration) if hydration else {}
            except (TypeError, ValueError):
                hydration = {}
            if isinstance(hydration, dict):
                for key, label in (
                        ("lastPerformed", "Account Hydration Time"),
                        ("ageBracket", "Age Bracket"),
                        ("gender", "Gender"),
                        ("platform", "Platform")):
                    value = hydration.get(key)
                    if key == "lastPerformed":
                        value = epoch_datetime(value)
                    _add(data_list, label, value, file_found, context)

            update = payload.get("UpdateControllerCacheJsonPayload")
            try:
                update = json.loads(update) if update else {}
            except (TypeError, ValueError):
                update = {}
            if isinstance(update, dict):
                _add(data_list, "Client Version", update.get("version"),
                     file_found, context)
                _add(data_list, "Client Version Upload",
                     update.get("clientVersionUpload"), file_found, context)
            _add(data_list, "Update Cache Time",
                 epoch_datetime(payload.get("UpdateControllerCacheTimestamp")),
                 file_found, context)

        elif name.endswith(".plist"):
            try:
                with open(file_found, "rb") as handle:
                    payload = plistlib.load(handle)
            except (OSError, plistlib.InvalidFileException):
                continue
            source_paths.append(file_found)
            for key, value in payload.items():
                label = {
                    "DeviceIdV2": "Roblox Device ID",
                    "NSWindow Frame Main Window": "Main Window Frame",
                    "www.roblox.com": "Website Update Channel",
                }.get(key)
                if label:
                    _add(data_list, label, value, file_found, context)
        elif name == "AnalysticsSettings.xml":
            try:
                root = ET.parse(file_found).getroot()
            except (OSError, ET.ParseError):
                continue
            source_paths.append(file_found)
            ga_id = root.find(".//string[@name='gaID']")
            if ga_id is not None:
                _add(data_list, "Google Analytics ID", ga_id.text,
                     file_found, context)

    logfunc(f"Roblox Account & Application: {len(data_list)} property value(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _xml_value(element):
    if len(element):
        return ", ".join(
            f"{child.tag}={child.text or ''}" for child in element)
    return element.text or ""


@artifact_processor
def robloxSettings(context):
    data_headers = ("Setting", "Value", "Value Type", "Source File")
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        try:
            root = ET.parse(file_found).getroot()
        except (OSError, ET.ParseError) as ex:
            logfunc(f"Roblox settings: could not parse '{file_found}': {ex}")
            continue
        source_paths.append(file_found)
        for properties in root.findall(".//Properties"):
            for item in properties:
                name = item.attrib.get("name")
                if name:
                    data_list.append((
                        name, _xml_value(item), item.tag,
                        context.get_relative_path(file_found),
                    ))
    logfunc(f"Roblox Player Settings: {len(data_list)} setting(s).")
    return data_headers, data_list, "\n".join(source_paths)
