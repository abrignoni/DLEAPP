__artifacts_v2__ = {
    "signalMessages": {
        "name": "Signal Messages",
        "description": "Messages from the Signal Desktop database. Signal keeps "
                       "them in a SQLCipher database whose key is wrapped with "
                       "the OS credential store, so the credential has to be "
                       "supplied with --signal-key, the Signal key field in the "
                       "GUI, or a file beside the extraction. Attachments that "
                       "decrypt are embedded against their message.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (macOS)",
        "notes": "Message bodies come from the messages table. A row with an "
                 "empty body is not necessarily an empty message: it may be a "
                 "view-once message that was opened, a message whose body was "
                 "erased, or an event such as a key change. The message type is "
                 "reported so those cases are distinguishable.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/Signal*/attachments.noindex/*/*',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-square",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 3837 rows",
        },
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Conversation ID",
                "conversationLabelColumn": "Conversation",
                "textColumn": "Message",
                "timeColumn": "Sent",
                "directionColumn": "Direction",
                "directionSentValue": "Outgoing",
                "senderColumn": "Sender",
                "mediaColumn": "Attachments",
            }
        },
    },
    "signalAttachments": {
        "name": "Signal Attachments",
        "description": "Files shared in Signal conversations, decrypted from "
                       "attachments.noindex. Each stored file is encrypted with "
                       "its own key held in the database, so the files cannot be "
                       "read without it. Each recovered file is checked against "
                       "the message authentication code and, where the database "
                       "recorded one, its SHA-256.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (macOS)",
        "notes": "The stored plaintext is longer than the recorded size, so it "
                 "is truncated to the size the database records. The Verified "
                 "column reports whether the recovered bytes matched the "
                 "SHA-256 the database holds for the original. Where no file "
                 "was recovered it names only the causes that can be told "
                 "apart here (no attachments folder, no key or no path in the "
                 "database, or the file absent from disk); every other failure "
                 "is reported as 'Could not decrypt' rather than asserting a "
                 "single cause for all of them.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/Signal*/attachments.noindex/*/*',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "paperclip",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 297 rows",
        },
    },
    "signalReactions": {
        "name": "Signal Reactions",
        "description": "Emoji reactions recorded against messages, with the "
                       "account that sent each one and the message it targets.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (macOS)",
        "notes": "A reaction is stored separately from the message it targets, "
                 "so it survives here even where the message body is empty.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smile",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 390 rows",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts import signal_desktop
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


def _sender(labels, self_ids, message_type, source_service_id, conversation_id):
    if message_type == "outgoing":
        return "Local user"
    if source_service_id:
        key = source_service_id.lower()
        if key in self_ids:
            return "Local user"
        for cid, label in labels.items():
            if cid == source_service_id:
                return label
    return labels.get(conversation_id, conversation_id or "")


def _service_id_labels(connection, labels):
    """Map a service id to its conversation label, for sender resolution."""
    mapping = {}
    try:
        rows = connection.execute(
            "SELECT serviceId, id FROM conversations WHERE serviceId IS NOT NULL")
    # Deliberately broad: an older schema may lack the attachment table.
    except Exception:  # pylint: disable=broad-exception-caught
        return mapping
    for service_id, cid in rows:
        if service_id:
            mapping[service_id.lower()] = labels.get(cid, cid)
    return mapping


def _recovery_failure(root, relative_path, local_key):
    """Why decrypt_attachment recovered nothing, limited to what is knowable.

    That function returns no plaintext for several distinct reasons: no
    attachments root, no stored path, no key held in the database, the file
    not being readable, a blob too short to hold the IV and MAC, key material
    that is not valid base64 or is under 64 bytes, and an AES failure. Only
    the causes that can be told apart from here are named. Everything else is
    reported as a failed decryption rather than asserting one specific cause
    for all of them.
    """
    if not root:
        return "Attachments folder not in extraction"
    if not local_key:
        return "No key recorded"
    if not relative_path:
        return "No stored path recorded"
    if not os.path.exists(os.path.join(root, relative_path.replace("/", os.sep))):
        return "File not in extraction"
    return "Could not decrypt"


@artifact_processor
def signalMessages(context):
    data_headers = (
        ("Sent", "datetime"),
        ("Received", "datetime"),
        ("Server Timestamp", "datetime"),
        ("Expires At", "datetime"),
        "Direction",
        "Sender",
        "Conversation",
        "Message",
        ("Attachments", "media"),
        "Attachment Names",
        "Message Type",
        "Read Status",
        "View Once",
        "Erased",
        "Expires In (s)",
        "Conversation ID",
        "Message ID",
        "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    labels = signal_desktop.conversation_labels(connection)
    self_ids = signal_desktop.self_service_ids(connection)
    by_service = _service_id_labels(connection, labels)
    root = signal_desktop.attachments_root(files_found)

    # Attachments belonging to each message, decrypted once and shared with the
    # attachment artifact through the media store's own de-duplication.
    attachments = {}
    try:
        rows = connection.execute("""
            SELECT messageId, path, localKey, size, contentType, fileName, plaintextHash
            FROM message_attachments WHERE path IS NOT NULL ORDER BY orderInMessage""")
        for message_id, path, local_key, size, content_type, file_name, plain_hash in rows:
            attachments.setdefault(message_id, []).append(
                (path, local_key, size, content_type, file_name, plain_hash))
    # Deliberately broad: an older schema may lack the attachment table.
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Signal Messages: attachment table unavailable ({ex}).")

    data_list = []
    query = """SELECT id, conversationId, type, body, sent_at, received_at_ms, serverTimestamp,
                      sourceServiceId, readStatus, isViewOnce, isErased, expireTimer, expires_at
               FROM messages"""
    for (message_id, conversation_id, message_type, body, sent_at, received_at,
         server_ts, source_service_id, read_status, view_once, erased,
         expire_timer, expires_at) in connection.execute(query):

        media_refs, names = [], []
        for path, local_key, size, content_type, file_name, plain_hash in attachments.get(message_id, []):
            plaintext, _authenticated, _matched = signal_desktop.decrypt_attachment(
                root, path, local_key, size, verify_hash=plain_hash)
            if not plaintext:
                continue
            name = file_name or os.path.basename(path)
            names.append(name)
            extension = (content_type or "").split("/")[-1] if "/" in (content_type or "") else None
            reference = check_in_embedded_media(
                path, plaintext, name, force_type=content_type or None,
                force_extension=extension)
            if reference:
                media_refs.append(reference)

        if message_type == "outgoing":
            sender = "Local user"
        else:
            sender = by_service.get((source_service_id or "").lower()) or _sender(
                labels, self_ids, message_type, source_service_id, conversation_id)

        # Only real messages carry a direction. Rows such as a key change or a
        # profile change are events Signal records in the conversation, and
        # calling those incoming would overstate what the record shows.
        if message_type == "outgoing":
            direction = "Outgoing"
        elif message_type == "incoming":
            direction = "Incoming"
        else:
            direction = ""

        data_list.append((
            signal_desktop.js_ms_to_datetime(sent_at),
            signal_desktop.js_ms_to_datetime(received_at),
            signal_desktop.js_ms_to_datetime(server_ts),
            signal_desktop.js_ms_to_datetime(expires_at),
            direction,
            sender,
            labels.get(conversation_id, conversation_id or ""),
            body or "",
            media_refs,
            ", ".join(names),
            message_type or "",
            read_status if read_status is not None else "",
            "Yes" if view_once else "",
            "Yes" if erased else "",
            expire_timer if expire_timer else "",
            conversation_id or "",
            message_id or "",
            context.get_relative_path(next(iter(signal_desktop.database_files(files_found)), "")),
        ))

    connection.close()
    data_list.sort(key=lambda row: (row[15], row[0] if isinstance(row[0], datetime) else _EPOCH_MIN))
    with_media = sum(1 for row in data_list if row[5])
    logfunc(f"Signal Messages: {len(data_list)} message(s) across {len(labels)} conversation(s); "
            f"{with_media} carry a recovered attachment.")
    return data_headers, data_list, next(iter(signal_desktop.database_files(files_found)), "")


@artifact_processor
def signalAttachments(context):
    data_headers = (
        ("Sent", "datetime"), "Conversation", "Filename", ("File", "media"),
        "Content Type", "Size (bytes)", "Dimensions", "Duration (s)", "Verified",
        "View Once", "Stored Path", "SHA-256 Of Original", "Message ID",
        "Conversation ID", "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    labels = signal_desktop.conversation_labels(connection)
    root = signal_desktop.attachments_root(files_found)
    if not root:
        logfunc("Signal Attachments: the extraction has no attachments.noindex folder, "
                "so only the database's record of each file is reported.")

    data_list = []
    query = """SELECT messageId, conversationId, sentAt, path, localKey, size, contentType,
                      fileName, plaintextHash, width, height, duration, isViewOnce
               FROM message_attachments WHERE path IS NOT NULL"""
    for (message_id, conversation_id, sent_at, path, local_key, size, content_type,
         file_name, plain_hash, width, height, duration, view_once) in connection.execute(query):

        plaintext, authenticated, matched = signal_desktop.decrypt_attachment(
            root, path, local_key, size, verify_hash=plain_hash)
        reference = None
        if plaintext:
            name = file_name or os.path.basename(path)
            extension = (content_type or "").split("/")[-1] if "/" in (content_type or "") else None
            reference = check_in_embedded_media(
                path, plaintext, name, force_type=content_type or None,
                force_extension=extension)

        if plaintext is None:
            verified = _recovery_failure(root, path, local_key)
        elif matched is True:
            verified = "Yes, SHA-256 matched"
        elif matched is False:
            verified = "No, SHA-256 differed"
        else:
            verified = "Authenticated" if authenticated else "Not authenticated"

        data_list.append((
            signal_desktop.js_ms_to_datetime(sent_at),
            labels.get(conversation_id, conversation_id or ""),
            file_name or "",
            reference,
            content_type or "",
            size if size else "",
            f"{width}x{height}" if width and height else "",
            duration if duration else "",
            verified,
            "Yes" if view_once else "",
            path or "",
            plain_hash or "",
            message_id or "",
            conversation_id or "",
            context.get_relative_path(next(iter(signal_desktop.database_files(files_found)), "")),
        ))

    connection.close()
    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    recovered = sum(1 for row in data_list if row[3])
    logfunc(f"Signal Attachments: {len(data_list)} attachment(s), {recovered} decrypted.")
    return data_headers, data_list, next(iter(signal_desktop.database_files(files_found)), "")


@artifact_processor
def signalReactions(context):
    data_headers = (
        ("Reacted", "datetime"), "Emoji", "From", "Conversation",
        ("Target Message Sent", "datetime"), "Target Author", "Unread",
        "Message ID", "Conversation ID", "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    labels = signal_desktop.conversation_labels(connection)
    by_service = _service_id_labels(connection, labels)

    data_list = []
    query = """SELECT emoji, fromId, conversationId, targetAuthorAci, targetTimestamp,
                      messageReceivedAt, unread, messageId, timestamp
               FROM reactions"""
    for (emoji, from_id, conversation_id, target_author, target_ts,
         received_at, unread, message_id, timestamp) in connection.execute(query):
        data_list.append((
            signal_desktop.js_ms_to_datetime(timestamp or received_at),
            emoji or "",
            by_service.get((from_id or "").lower()) or labels.get(from_id, from_id or ""),
            labels.get(conversation_id, conversation_id or ""),
            signal_desktop.js_ms_to_datetime(target_ts),
            by_service.get((target_author or "").lower()) or (target_author or ""),
            "Yes" if unread else "",
            message_id or "",
            conversation_id or "",
            context.get_relative_path(next(iter(signal_desktop.database_files(files_found)), "")),
        ))

    connection.close()
    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Signal Reactions: {len(data_list)} reaction(s).")
    return data_headers, data_list, next(iter(signal_desktop.database_files(files_found)), "")
