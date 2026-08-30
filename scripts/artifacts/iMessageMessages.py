__artifacts_v2__ = {
    "imessageMessages": {
        "name": "iMessage Messages",
        "description": "Each row in chat.db's message table: composed/read/"
                       "delivered time, direction, sender, the chat it "
                       "belongs to, body text, service (iMessage vs SMS/"
                       "RCS), whether it carries an attachment, and tapback/"
                       "reaction labels where the message is one.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-22",
        "last_update_date": "2026-08-22",
        "requirements": "none",
        "category": "iMessage (macOS)",
        "notes": "Timestamp math and column presence validated against a "
                 "real chat.db (see module docstring) -- higher confidence "
                 "than a documentation-only parser. attributedBody is not "
                 "decoded; a row with empty text but a non-null "
                 "attributedBody is flagged in Body Source rather than "
                 "silently shown as an empty message.",
        "paths": (
            "*/Library/Messages/chat.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "message-circle",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / thisisdfir "
                "public test image, acquired 2021-02-20), chat.db + chat.db-wal | "
                "25 messages, 1 chat, 1 handle",
        },
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Chat Identifier",
                "conversationLabelColumn": "Chat Identifier",
                "textColumn": "Text",
                "timeColumn": "Date",
                "directionColumn": "Direction",
                "directionSentValue": "Outgoing",
                "senderColumn": "Sender",
            }
        },
    },
    "imessageAttachments": {
        "name": "iMessage Attachments",
        "description": "Each row in chat.db's attachment table: filename, "
                       "MIME type, size and created/start time, linked back "
                       "to the message it was sent or received on. The file "
                       "itself is embedded when it's present in the "
                       "extraction.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-22",
        "last_update_date": "2026-08-22",
        "requirements": "none",
        "category": "iMessage (macOS)",
        "notes": "created_date/start_date use the SECONDS Mac-Absolute-Time "
                 "converter, not the nanosecond one Messages uses -- see "
                 "module docstring. Embedding relies on attachment files "
                 "being present under Library/Messages/Attachments in the "
                 "extraction, which this artifact's paths glob picks up.",
        "paths": (
            "*/Library/Messages/chat.db*",
            "*/Library/Messages/Attachments/*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "paperclip",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / thisisdfir "
                "public test image, acquired 2021-02-20), chat.db + Attachments "
                "folder | 5 attachments, all 5 present and embeddable from the "
                "extraction",
        },
    },

    "imessageChats": {
        "name": "iMessage Chat Threads",
        "description": "One row per chat.db chat: identifier, display "
                       "name, service, group/1:1 style, and the "
                       "participant handles joined via chat_handle_join.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-22",
        "last_update_date": "2026-08-22",
        "requirements": "none",
        "category": "iMessage (macOS)",
        "notes": "Validated against the same real chat.db as the other "
                 "iMessage artifacts in this file.",
        "paths": (
            "*/Library/Messages/chat.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / thisisdfir "
                "public test image, acquired 2021-02-20), chat.db | 1 chat "
                "thread, 1 participant handle",
        },
    },
    "imessageDeletedItems": {
        "name": "iMessage Deletion Tombstones",
        "description": "GUIDs recorded in chat.db's deleted_messages, "
                       "sync_deleted_chats, sync_deleted_messages and "
                       "sync_deleted_attachments tables -- tombstones "
                       "Messages keeps after a chat, message or attachment "
                       "is deleted, even though the content itself is "
                       "gone.",
        "author": "Gear-I & Claude",
        "creation_date": "2026-08-22",
        "last_update_date": "2026-08-22",
        "requirements": "none",
        "category": "iMessage (macOS)",
        "notes": "All four tables were empty on the validation image (no "
                 "deletions had occurred), so only the schema -- not real "
                 "tombstone data -- was confirmed. Forensically these rows "
                 "matter precisely when something WAS deleted, so this is "
                 "included even though the tested sample had none.",
        "paths": (
            "*/Library/Messages/chat.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "macos_bigsur_thisisdfir": "macOS Big Sur (Josh Hickman / thisisdfir "
                "public test image, acquired 2021-02-20), chat.db | 0 rows in "
                "deleted_messages, sync_deleted_chats, sync_deleted_messages and "
                "sync_deleted_attachments (no deletions had occurred on this "
                "image -- table schemas confirmed present, tombstone data was "
                "not)",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, check_in_media, logfunc,
                               open_sqlite_db_readonly)

# Seconds between the Unix epoch (1970-01-01) and the Mac/Cocoa epoch
# (2001-01-01). message.date and friends are nanoseconds past this epoch;
# attachment.created_date/start_date are seconds past it. Confirmed against
# real data -- see module docstring.
_MAC_EPOCH_OFFSET = 978307200

_TAPBACK_LABELS = {
    2000: "Loved", 2001: "Liked", 2002: "Disliked", 2003: "Laughed",
    2004: "Emphasized", 2005: "Questioned",
    3000: "Removed Loved", 3001: "Removed Liked", 3002: "Removed Disliked",
    3003: "Removed Laughed", 3004: "Removed Emphasized",
    3005: "Removed Questioned",
}


def _mac_abs_ns_to_utc(value):
    """message.date / date_read / date_delivered / date_played: Mac
    Absolute Time in NANOSECONDS since 2001-01-01."""
    if not value:
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(
            value / 1_000_000_000 + _MAC_EPOCH_OFFSET, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _mac_abs_s_to_utc(value):
    """attachment.created_date / start_date: Mac Absolute Time in SECONDS
    since 2001-01-01 -- NOT the same unit as the message table's dates."""
    if not value:
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(value + _MAC_EPOCH_OFFSET, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _find_chat_db(files_found):
    for path in files_found:
        if os.path.basename(path) == "chat.db":
            return path
    return None


_MESSAGES_QUERY = """
    SELECT
        m.ROWID, m.guid, m.date, m.date_read, m.date_delivered,
        m.is_from_me, m.service, m.text, m.attributedBody,
        m.cache_has_attachments, m.item_type, m.group_action_type,
        m.associated_message_type, m.associated_message_guid,
        m.is_audio_message, m.is_system_message,
        h.id AS handle_id,
        c.chat_identifier, c.display_name, c.service_name, c.style
    FROM message m
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    LEFT JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
    LEFT JOIN chat c ON c.ROWID = cmj.chat_id
    ORDER BY m.date
"""


@artifact_processor
def imessageMessages(context):
    data_headers = (
        ("Date", "datetime"), ("Date Read", "datetime"),
        ("Date Delivered", "datetime"), "Direction", "Sender",
        "Chat Identifier", "Chat Display Name", "Text", "Body Source",
        "Service", "Has Attachment", "Tapback", "Associated Message GUID",
        "Item Type (raw)", "Group Action Type (raw)", "Message GUID",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = _find_chat_db(files_found)
    if not source:
        return data_headers, [], ""

    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    for row in database.execute(_MESSAGES_QUERY):
        (_pk, guid, date, date_read, date_delivered, is_from_me, service,
         text, attributed_body, has_attachments, item_type,
         group_action_type, assoc_type, assoc_guid, _is_audio,
         _is_system, handle_id, chat_identifier, display_name,
         _service_name, _style) = row

        body_source = ""
        display_text = text or ""
        if not text and attributed_body:
            body_source = "attributedBody only (not decoded)"
        elif text:
            body_source = "text"

        direction = "" if is_from_me is None else ("Outgoing" if is_from_me else "Incoming")
        sender = "Local User" if is_from_me else (handle_id or "")

        data_list.append((
            _mac_abs_ns_to_utc(date), _mac_abs_ns_to_utc(date_read),
            _mac_abs_ns_to_utc(date_delivered), direction, sender,
            chat_identifier or "", display_name or "", display_text,
            body_source, service or "",
            "Yes" if has_attachments else "",
            _TAPBACK_LABELS.get(assoc_type, ""),
            assoc_guid or "",
            item_type if item_type is not None else "",
            group_action_type if group_action_type is not None else "",
            guid or "", relative_source,
        ))

    database.close()
    logfunc(f"iMessage Messages: {len(data_list)} message(s).")
    return data_headers, data_list, source


_ATTACHMENTS_QUERY = """
    SELECT
        a.ROWID, a.guid, a.filename, a.transfer_name, a.mime_type,
        a.total_bytes, a.created_date, a.start_date, a.is_sticker,
        a.transfer_state, maj.message_id, m.guid AS message_guid
    FROM attachment a
    LEFT JOIN message_attachment_join maj ON maj.attachment_id = a.ROWID
    LEFT JOIN message m ON m.ROWID = maj.message_id
    ORDER BY a.created_date
"""


@artifact_processor
def imessageAttachments(context):
    data_headers = (
        ("Created", "datetime"), ("Start", "datetime"), "Filename",
        ("File", "media"), "MIME Type", "Size (bytes)", "Is Sticker",
        "Transfer State (raw)", "Attachment GUID", "Message GUID",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = _find_chat_db(files_found)
    if not source:
        return data_headers, [], ""

    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    embedded = 0
    for row in database.execute(_ATTACHMENTS_QUERY):
        (_pk, guid, filename, transfer_name, mime_type, total_bytes,
         created_date, start_date, is_sticker, transfer_state,
         _message_id, message_guid) = row

        media_ref = ""
        if filename:
            reference = check_in_media(filename, name=transfer_name or os.path.basename(filename))
            if reference:
                media_ref = reference
                embedded += 1

        data_list.append((
            _mac_abs_s_to_utc(created_date), _mac_abs_s_to_utc(start_date),
            filename or "", media_ref, mime_type or "",
            total_bytes if total_bytes is not None else "",
            "Yes" if is_sticker else "",
            transfer_state if transfer_state is not None else "",
            guid or "", message_guid or "", relative_source,
        ))

    database.close()
    logfunc(f"iMessage Attachments: {len(data_list)} attachment(s); "
            f"{embedded} embedded from the extraction.")
    return data_headers, data_list, source


_CHATS_QUERY = """
    SELECT c.ROWID, c.guid, c.chat_identifier, c.display_name,
           c.service_name, c.style, c.is_archived
    FROM chat c
    ORDER BY c.ROWID
"""


@artifact_processor
def imessageChats(context):
    data_headers = ("Chat Identifier", "Display Name", "Service", "Style (raw)",
                     "Archived", "Participants", "Chat GUID", "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    source = _find_chat_db(files_found)
    if not source:
        return data_headers, [], ""

    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    for row in database.execute(_CHATS_QUERY):
        chat_pk, guid, chat_identifier, display_name, service_name, style, is_archived = row
        participants = [r[0] for r in database.execute(
            "SELECT h.id FROM chat_handle_join chj "
            "JOIN handle h ON h.ROWID = chj.handle_id WHERE chj.chat_id = ?",
            (chat_pk,))]
        data_list.append((
            chat_identifier or "", display_name or "", service_name or "",
            style if style is not None else "", "Yes" if is_archived else "",
            ", ".join(p for p in participants if p), guid or "", relative_source,
        ))

    database.close()
    logfunc(f"iMessage Chat Threads: {len(data_list)} chat(s).")
    return data_headers, data_list, source


_DELETED_QUERIES = (
    ("deleted_messages", "SELECT guid, NULL, NULL FROM deleted_messages"),
    ("sync_deleted_chats", "SELECT guid, recordID, timestamp FROM sync_deleted_chats"),
    ("sync_deleted_messages", "SELECT guid, recordID, NULL FROM sync_deleted_messages"),
    ("sync_deleted_attachments", "SELECT guid, recordID, NULL FROM sync_deleted_attachments"),
)


@artifact_processor
def imessageDeletedItems(context):
    data_headers = ("Tombstone Table", "GUID", "CloudKit Record ID",
                     ("Timestamp", "datetime"), "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    source = _find_chat_db(files_found)
    if not source:
        return data_headers, [], ""

    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    for table_name, query in _DELETED_QUERIES:
        try:
            rows = database.execute(query).fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"iMessage Deletion Tombstones: could not read '{table_name}': {ex}")
            continue
        for guid, record_id, timestamp in rows:
            # sync_deleted_chats.timestamp -- unit not independently verified
            # (table was empty on the validation image); reported as the
            # nanosecond Mac Absolute Time format used elsewhere in this
            # schema, but treat with more caution than the message dates.
            data_list.append((
                table_name, guid or "", record_id or "",
                _mac_abs_ns_to_utc(timestamp), relative_source,
            ))

    database.close()
    logfunc(f"iMessage Deletion Tombstones: {len(data_list)} tombstone(s).")
    return data_headers, data_list, source