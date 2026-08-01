__artifacts_v2__ = {
    "signalAccount": {
        "name": "Signal Account & Application",
        "description": "The account registered to this Signal Desktop "
                       "installation and how the client is configured, from the "
                       "database's own key-value store together with the "
                       "unencrypted profile files. Includes the linked device "
                       "name and the time the client stored for this linked "
                       "device record.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "PyCryptodome; the Signal database credential for the "
                        "account fields",
        "category": "Signal (macOS)",
        "notes": "Key material is reported as present or absent, never printed: "
                 "the store also holds the account password, master key, "
                 "profile key and storage keys, which would let the account be "
                 "impersonated. The unencrypted profile files are reported even "
                 "when no credential is available.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/Signal*/ephemeral.json',
            '*/Signal*/Preferences',
            '*/Signal*/Local State',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 35 rows",
        },
    },
}

import json
import os

from scripts import signal_desktop
from scripts.ilapfuncs import artifact_processor, logfunc

# Items whose value is key material or a credential. Their presence is
# evidence the account is registered; their value would allow impersonation.
_SECRET_ITEMS = {
    "password", "masterKey", "profileKey", "storageKey", "accountEntropyPool",
    "backupMediaRootKey", "identityKeyMap", "storageCredentials", "groupCredentials",
    "callLinkAuthCredentials", "senderCertificate", "senderCertificateNoE164",
    "usernameLink", "manifestRecordIkm", "signedKeyId", "subscriberId",
}

# Items worth reporting by value, with a readable label.
_REPORTED_ITEMS = {
    "uuid_id": "Account Service ID (ACI)",
    "pni": "Account Phone Number Identity (PNI)",
    "number_id": "Registered Phone Number",
    "device_name": "Linked Device Name",
    "deviceCreatedAt": "Device Linked",
    "regionCode": "Region Code",
    "synced_at": "Last Storage Sync",
    "unreadCount": "Unread Count",
    "universalExpireTimer": "Default Disappearing Timer (s)",
    "phoneNumberSharingMode": "Phone Number Sharing",
    "phoneNumberDiscoverability": "Phone Number Discoverability",
    "read-receipt-setting": "Read Receipts Enabled",
    "typingIndicators": "Typing Indicators Enabled",
    "sealedSenderIndicators": "Sealed Sender Indicators",
    "linkPreviews": "Link Previews Enabled",
    "hasStoriesDisabled": "Stories Disabled",
    "backupTier": "Backup Tier",
    "blocked": "Blocked Numbers",
    "blocked-uuids": "Blocked Service IDs",
    "blocked-groups": "Blocked Groups",
    "pinnedConversationIds": "Pinned Conversations",
    "emojiSkinToneDefault": "Default Emoji Skin Tone",
    "keepMutedChatsArchived": "Keep Muted Chats Archived",
}

_TIMESTAMP_ITEMS = {"deviceCreatedAt", "synced_at"}


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


@artifact_processor
def signalAccount(context):
    data_headers = ("Property", "Value", "Source File")
    data_list = []
    files_found = [str(f) for f in context.get_files_found()]
    source_path = ""

    def add(prop, value, path):
        if value not in (None, "", [], {}):
            data_list.append((prop, str(value), context.get_relative_path(path)))

    # Unencrypted profile files first, so the artifact still reports something
    # useful when no credential was supplied.
    for file_found in files_found:
        name = os.path.basename(file_found)
        if name == "config.json":
            config = _read_json(file_found)
            if not isinstance(config, dict):
                continue
            source_path = source_path or file_found
            if config.get("key"):
                add("Database Key Storage", "Plaintext 'key' in config.json",
                    file_found)
            if config.get("encryptedKey"):
                add("Database Key Storage", "'encryptedKey', wrapped with the OS "
                    "credential store", file_found)
            for setting in ("mediaPermissions", "mediaCameraPermissions"):
                if setting in config:
                    add(f"Setting: {setting}", config[setting], file_found)
        elif name == "ephemeral.json":
            ephemeral = _read_json(file_found)
            if not isinstance(ephemeral, dict):
                continue
            source_path = source_path or file_found
            for key in ("theme-setting", "spell-check", "localeOverride", "system-tray-setting"):
                if key in ephemeral:
                    add(f"Setting: {key}", ephemeral[key], file_found)
            window = ephemeral.get("window") or {}
            if window:
                add("Window Bounds",
                    f"{window.get('width')}x{window.get('height')} "
                    f"at x={window.get('x')} y={window.get('y')} "
                    f"maximized={window.get('maximized')}", file_found)

    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        add("Database", f"Not opened: {note}", source_path or "config.json")
        return data_headers, data_list, source_path

    database_path = next(iter(signal_desktop.database_files(files_found)), "")
    source_path = database_path or source_path
    add("Database", f"Opened, {note}", database_path)

    present_secrets = []
    for item_id, blob in connection.execute("SELECT id, json FROM items"):
        try:
            value = json.loads(blob).get("value")
        except (ValueError, TypeError):
            continue
        if item_id in _SECRET_ITEMS:
            if value:
                present_secrets.append(item_id)
            continue
        label = _REPORTED_ITEMS.get(item_id)
        if not label:
            continue
        if item_id in _TIMESTAMP_ITEMS:
            add(label, signal_desktop.js_ms_to_datetime(value), database_path)
        elif isinstance(value, (list, dict)):
            add(label, json.dumps(value)[:500], database_path)
        else:
            add(label, value, database_path)

    if present_secrets:
        add("Key Material Present (values withheld)",
            ", ".join(sorted(present_secrets)), database_path)

    for label, query in (
            ("Conversations", "SELECT COUNT(*) FROM conversations"),
            ("Messages", "SELECT COUNT(*) FROM messages"),
            ("Attachments", "SELECT COUNT(*) FROM message_attachments"),
            ("Calls", "SELECT COUNT(*) FROM callsHistory"),
            ("Protocol Sessions", "SELECT COUNT(*) FROM sessions")):
        try:
            add(f"Records: {label}", connection.execute(query).fetchone()[0], database_path)
        # Deliberately broad: a missing table must not stop the summary.
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    connection.close()
    logfunc(f"Signal Account & Application: {len(data_list)} property value(s).")
    return data_headers, data_list, source_path
