"""Shared helpers for WhatsApp's Core Data databases.

The native macOS WhatsApp app and the iOS app store their data in the same
Core Data SQLite schema, unencrypted, so one set of readers serves both. On
macOS the databases live in the app group container
``group.net.whatsapp.WhatsApp.shared``; on iOS they live in the app's shared
group container under ``.../Shared/AppGroup/<uuid>/``. The filenames are the
same either way, which is why the artifact path globs match on the filename
rather than the platform-specific parent directory.

This module holds only what the artifacts share: locating the databases and the
on-disk media folder, turning a Core Data timestamp into a datetime, and
describing a WhatsApp JID by its documented suffix. Everything interpretive
beyond the JID suffix is left to the individual artifacts, which derive it from
values the database actually holds.
"""

import os

from scripts.ilapfuncs import convert_cocoa_core_data_ts_to_utc

CHAT_STORAGE = "ChatStorage.sqlite"
CONTACTS_DB = "ContactsV2.sqlite"
CALL_HISTORY_DB = "CallHistory.sqlite"


def _databases(files_found, name):
    """Yield each real copy of a named database, ignoring -wal/-shm siblings."""
    seen = set()
    for file_found in files_found:
        file_found = str(file_found)
        if os.path.basename(file_found) != name:
            continue
        real = os.path.realpath(file_found)
        if real not in seen:
            seen.add(real)
            yield file_found


def chat_storage_files(files_found):
    """Every ChatStorage.sqlite in the extraction."""
    return _databases(files_found, CHAT_STORAGE)


def contacts_files(files_found):
    """Every ContactsV2.sqlite in the extraction."""
    return _databases(files_found, CONTACTS_DB)


def call_history_files(files_found):
    """Every CallHistory.sqlite in the extraction."""
    return _databases(files_found, CALL_HISTORY_DB)


def media_root(chat_storage_path, files_found):
    """The 'Message' folder that ZMEDIALOCALPATH values are relative to.

    ZMEDIALOCALPATH holds a path like ``Media/<jid>/<a>/<b>/<hash>.jpg``, rooted
    at the container's ``Message`` folder, which sits beside ChatStorage.sqlite.
    Returns that folder's path when it is present in the extraction, else None.
    """
    container = os.path.dirname(str(chat_storage_path))
    candidate = os.path.join(container, "Message")
    if os.path.isdir(candidate):
        return candidate
    # Fall back to any collected file that sits under a Message/Media folder.
    for file_found in files_found:
        file_found = str(file_found)
        marker = os.path.join("Message", "Media") + os.sep
        if marker in file_found:
            return file_found.split(marker)[0] + "Message"
    return None


def cocoa_to_datetime(value):
    """Convert a Core Data (Cocoa, 2001-epoch) timestamp to a datetime, or ''."""
    if value in (None, "", 0):
        return ""
    return convert_cocoa_core_data_ts_to_utc(value)


def jid_kind(jid):
    """Describe a JID by its documented suffix; '' when it is not recognised.

    This is a statement about the address format, not about the correspondent:
    a suffix is exactly what the stored string ends with.
    """
    if not jid:
        return ""
    if jid == "status@broadcast":
        return "Status"
    if jid.endswith("@g.us"):
        return "Group"
    if jid.endswith("@s.whatsapp.net"):
        return "Individual"
    if jid.endswith("@lid"):
        return "Linked ID"
    if jid.endswith("@broadcast"):
        return "Broadcast"
    if jid.endswith("@call"):
        return "Call"
    return ""
