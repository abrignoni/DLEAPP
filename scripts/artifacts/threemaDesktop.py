"""Threema Desktop artifacts. Author: @AlexisBrignoni, Codex."""

from scripts import threema_desktop as td
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media

__artifacts_v2__ = {
    "threemaProfile": {
        "name": "Threema Desktop Profile",
        "description": "Threema Desktop profile and database state, including protected key-storage presence, schema version and record totals for supported tables when the database can be opened.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted database details", "category": "Threema Desktop",
        "notes": "Key-storage contents and database keys are never reported. A locked database is still identified. Storage design source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/keystorage.bin", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "output_types": ["html", "tsv", "lava"], "artifact_icon": "user"},
    "threemaContacts": {
        "name": "Threema Desktop Contacts",
        "description": "Contacts stored by Threema Desktop, including the name, Threema ID, verification, identity, acquaintance and activity states recorded by the client.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "Integer meanings follow the official schema at https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6. Public keys and profile-picture blobs are not reported.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/keystorage.bin", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book"},
    "threemaConversations": {
        "name": "Threema Desktop Conversations",
        "description": "Direct, group and distribution-list conversations stored by Threema Desktop, with client state and message totals.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "Conversation relationships and state meanings follow https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "comments"},
    "threemaGroups": {
        "name": "Threema Desktop Groups & Members",
        "description": "Threema groups and their current stored member relationships, including the creator when available.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "Membership rows represent the database state at acquisition. Schema source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users"},
    "threemaMessages": {
        "name": "Threema Desktop Messages",
        "description": "Messages stored by Threema Desktop with direction, conversation, sender, timestamps, text, location and poll content. Locally stored attachments are decrypted, authenticated and shown against their parent message.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "Deleted and edited timestamps are reported when present. Only local files that authenticate are embedded; status explains absent and unsupported files. Encryption keys and raw protocol bytes are withheld. Schema and file format source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/data/files/??/*", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "artifact_icon": "message",
        "output_types": ["html", "tsv", "timeline", "lava"],
        "data_views": {"conversation": {
            "conversationDiscriminatorColumn": "Conversation UID",
            "conversationLabelColumn": "Conversation", "textColumn": "Content",
            "timeColumn": "Created", "directionColumn": "Direction",
            "directionSentValue": "Outbound", "senderColumn": "Sender Threema ID",
            "mediaColumn": "Attachments"}}},
    "threemaReactions": {
        "name": "Threema Desktop Message Reactions",
        "description": "Emoji reactions stored for Threema Desktop messages, with sender and parent-message context.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "Newer schemas store emoji text; older schemas store acknowledge/decline integers. Schema source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "artifact_icon": "thumbs-up",
        "output_types": ["html", "tsv", "timeline", "lava"]},
    "threemaAttachments": {
        "name": "Threema Desktop Attachments",
        "description": "File, image, video and audio metadata stored for Threema Desktop messages, including filenames, media types, sizes, captions and local file identifiers.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "This reports metadata only. File and message encryption keys are withheld. Schema source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/data/files/??/*", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "paperclip"},
    "threemaGroupCalls": {
        "name": "Threema Desktop Persisted Group Calls",
        "description": "Persisted running-group-call records stored by Threema Desktop, including group, creator, start time, protocol version and SFU base URL.",
        "author": "@AlexisBrignoni, Codex", "creation_date": "2026-09-24", "last_update_date": "2026-09-24",
        "requirements": "PyCryptodome; the 64-character database key for encrypted databases", "category": "Threema Desktop",
        "notes": "This table tracks running calls retained by the client and is not a complete call-history ledger. Group call keys are withheld. Schema source: https://github.com/threema-ch/threema-desktop/tree/93a6615c5567f0cf8371619dc1a5e888eed1d0b6.",
        "paths": ("*/threema.sqlite", "*/threema.sqlite-wal", "*/threema.sqlite-shm", "*/threema-key.txt", "*/threema_key.txt", "*/threema-db-key.txt", "*/threema_db_key.txt"),
        "artifact_icon": "phone",
        "output_types": ["html", "tsv", "timeline", "lava"]},
}

_VERIFICATION = {0: "Unverified", 1: "Server verified", 2: "Fully verified"}
_IDENTITY_TYPE = {0: "Regular", 1: "Work"}
_ACQUAINTANCE = {0: "Direct", 1: "Group"}
_ACTIVITY = {0: "Active", 1: "Inactive", 2: "Invalid"}
_CATEGORY = {0: "Default", 1: "Protected"}
_VISIBILITY = {0: "Show", 1: "Archived"}


@artifact_processor
def threemaProfile(context):
    data_headers = ("Property", "Value", "Source File")
    files_found = [str(path) for path in context.get_files_found()]
    rows, sources = [], []
    for path in files_found:
        if path.endswith("keystorage.bin"):
            rows.append(("Protected Key Storage", "Present; contents withheld",
                         context.get_relative_path(path)))
            sources.append(path)
    for path in td.database_files(files_found):
        relative = context.get_relative_path(path)
        db, note = td.open_database(path, files_found)
        if db is None:
            rows.append(("Database State", f"Encrypted; not opened: {note}", relative))
            sources.append(path)
            continue
        rows.append(("Database State", f"Opened ({note})", relative))
        try:
            rows.append(("Schema User Version", db.execute("PRAGMA user_version").fetchone()[0], relative))
            for table, label in (("contacts", "Contacts"), ("groups", "Groups"),
                                 ("conversations", "Conversations"), ("messages", "Messages"),
                                 ("messageReactions", "Message Reactions"),
                                 ("runningGroupCalls", "Persisted Group Calls")):
                if td.columns(db, table):
                    count = db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    rows.append((f"Records: {label}", count, relative))
        finally:
            db.close()
        sources.append(path)
    return data_headers, rows, "\n".join(dict.fromkeys(sources))


def _enum(value, mapping):
    return mapping.get(value, f"Unknown ({value})" if value is not None else "")


def _contacts(db):
    extras = td.optional(db, "contacts", ("nickname", "workVerificationLevel",
                         "workAvailabilityStatusCategory", "workAvailabilityStatusDescription",
                         "workLastFullSyncAt"), "c")
    for row in db.execute(f"""SELECT c.createdAt, c.uid, c.identity, c.firstName, c.lastName,
            c.verificationLevel, c.identityType, c.acquaintanceLevel, c.activityState,
            c.featureMask, {extras} FROM contacts c ORDER BY c.createdAt, c.uid"""):
        yield (td.timestamp(row["createdAt"]), row["uid"], row["identity"], row["firstName"],
               row["lastName"], row["nickname"], _enum(row["verificationLevel"], _VERIFICATION),
               _enum(row["identityType"], _IDENTITY_TYPE),
               _enum(row["acquaintanceLevel"], _ACQUAINTANCE),
               _enum(row["activityState"], _ACTIVITY), row["featureMask"],
               row["workVerificationLevel"], row["workAvailabilityStatusCategory"],
               row["workAvailabilityStatusDescription"],
               td.timestamp(row["workLastFullSyncAt"]))


@artifact_processor
def threemaContacts(context):
    data_headers = (("Created", "datetime"), "Contact UID", "Threema ID", "First Name", "Last Name", "Nickname",
               "Verification", "Identity Type", "Acquaintance", "Activity", "Feature Mask",
               "Work Verification", "Work Availability", "Work Availability Description",
               "Work Last Full Sync", "Source File")
    rows, source = td.read_databases(context, _contacts, "Threema Desktop Contacts")
    return data_headers, rows, source


def _conversation_label(row):
    if row["contactUid"] is not None:
        return "Direct", row["contactIdentity"], " ".join(
            part for part in (row["contactFirstName"], row["contactLastName"]) if part)
    if row["groupUid"] is not None:
        return "Group", td.blob_hex(row["groupId"]), row["groupName"]
    return "Distribution List", td.blob_hex(row["distributionListId"]), row["distributionListName"]


def _conversations(db):
    for row in db.execute("""SELECT cv.lastUpdate, cv.uid, cv.contactUid, cv.groupUid,
            cv.distributionListUid, cv.category, cv.visibility,
            c.identity AS contactIdentity, c.firstName AS contactFirstName,
            c.lastName AS contactLastName, g.groupId, g.name AS groupName,
            d.distributionListId, d.name AS distributionListName,
            COUNT(m.uid) AS messageCount, MIN(m.createdAt) AS firstMessage,
            MAX(m.createdAt) AS lastMessage
        FROM conversations cv LEFT JOIN contacts c ON c.uid=cv.contactUid
        LEFT JOIN groups g ON g.uid=cv.groupUid
        LEFT JOIN distributionLists d ON d.uid=cv.distributionListUid
        LEFT JOIN messages m ON m.conversationUid=cv.uid
        GROUP BY cv.uid ORDER BY cv.lastUpdate, cv.uid"""):
        kind, identifier, name = _conversation_label(row)
        yield (td.timestamp(row["lastUpdate"]), td.timestamp(row["firstMessage"]),
               td.timestamp(row["lastMessage"]), row["uid"], kind, identifier, name,
               _enum(row["category"], _CATEGORY), _enum(row["visibility"], _VISIBILITY),
               row["messageCount"])


@artifact_processor
def threemaConversations(context):
    data_headers = (("Last Updated", "datetime"), ("First Message", "datetime"),
                    ("Last Message", "datetime"), "Conversation UID", "Type",
               "Identifier", "Name", "Category", "Visibility", "Message Count", "Source File")
    rows, source = td.read_databases(context, _conversations, "Threema Desktop Conversations")
    return data_headers, rows, source


def _groups(db):
    creator = "g.creatorUid" if "creatorUid" in td.columns(db, "groups") else "NULL"
    for row in db.execute(f"""SELECT g.createdAt, g.uid, g.groupId, g.name, {creator} AS creatorUid,
            creator.identity AS creatorIdentity, member.uid AS membershipUid,
            c.uid AS memberUid, c.identity AS memberIdentity, c.firstName, c.lastName
        FROM groups g LEFT JOIN contacts creator ON creator.uid={creator}
        LEFT JOIN groupMembers member ON member.groupUid=g.uid
        LEFT JOIN contacts c ON c.uid=member.contactUid
        ORDER BY g.createdAt, g.uid, member.uid"""):
        yield (td.timestamp(row["createdAt"]), row["uid"], td.blob_hex(row["groupId"]),
               row["name"], row["creatorUid"], row["creatorIdentity"], row["membershipUid"],
               row["memberUid"], row["memberIdentity"], row["firstName"], row["lastName"])


@artifact_processor
def threemaGroups(context):
    data_headers = (("Group Created", "datetime"), "Group UID", "Group ID", "Group Name", "Creator UID",
               "Creator Threema ID", "Membership UID", "Member UID", "Member Threema ID",
               "Member First Name", "Member Last Name", "Source File")
    rows, source = td.read_databases(context, _groups, "Threema Desktop Groups & Members")
    return data_headers, rows, source


def _message_content(db):
    parts = ["t.text"]
    if td.columns(db, "messageLocationData"):
        parts.append("CASE WHEN l.uid IS NOT NULL THEN 'Location: ' || l.lat || ', ' || l.lon || COALESCE(' ' || l.name, '') || COALESCE(' ' || l.address, '') END")
    if td.columns(db, "polls"):
        parts.append("p.description")
    return "COALESCE(" + ", ".join(parts) + ", '')"


def _message_attachments(db):
    """Attachment storage records grouped by parent message UID."""
    grouped = {}
    if not td.columns(db, "fileData"):
        return grouped
    for table in ("messageFileData", "messageImageData", "messageVideoData", "messageAudioData"):
        if not td.columns(db, table) or "fileDataUid" not in td.columns(db, table):
            continue
        selected = td.optional(db, table, ("fileName", "mediaType"), "a")
        for row in db.execute(f"""SELECT a.messageUid, {selected}, f.fileId,
                f.encryptionKey, f.unencryptedByteCount, f.storageFormatVersion
            FROM {table} a JOIN fileData f ON f.uid=a.fileDataUid
            WHERE a.fileDataUid IS NOT NULL ORDER BY a.uid"""):
            grouped.setdefault(row["messageUid"], []).append(row)
    return grouped


def _messages(db, files_found=()):
    edited = "m.lastEditedAt" if "lastEditedAt" in td.columns(db, "messages") else "NULL"
    deleted = "m.deletedAt" if "deletedAt" in td.columns(db, "messages") else "NULL"
    poll_joins = "LEFT JOIN messagePollData mp ON mp.messageUid=m.uid LEFT JOIN polls p ON p.uid=mp.pollUid" if td.columns(db, "polls") else ""
    location_join = "LEFT JOIN messageLocationData l ON l.messageUid=m.uid" if td.columns(db, "messageLocationData") else ""
    content = _message_content(db)
    attachments = _message_attachments(db)
    stored_files = td.stored_file_paths(files_found)
    query = f"""SELECT m.createdAt, m.processedAt, m.deliveredAt, m.readAt,
            {edited} AS lastEditedAt, {deleted} AS deletedAt, m.uid, m.messageId,
            m.messageType, m.threadId, m.senderContactUid, sender.identity AS senderIdentity,
            sender.firstName AS senderFirstName, sender.lastName AS senderLastName,
            cv.uid AS conversationUid, cv.contactUid, cv.groupUid, cv.distributionListUid,
            contact.identity AS contactIdentity, g.name AS groupName, d.name AS distributionListName,
            {content} AS content
        FROM messages m JOIN conversations cv ON cv.uid=m.conversationUid
        LEFT JOIN contacts sender ON sender.uid=m.senderContactUid
        LEFT JOIN contacts contact ON contact.uid=cv.contactUid
        LEFT JOIN groups g ON g.uid=cv.groupUid
        LEFT JOIN distributionLists d ON d.uid=cv.distributionListUid
        LEFT JOIN messageTextData t ON t.messageUid=m.uid {location_join} {poll_joins}
        ORDER BY m.createdAt, m.uid"""
    for row in db.execute(query):
        conversation = row["contactIdentity"] or row["groupName"] or row["distributionListName"]
        sender_name = " ".join(part for part in (row["senderFirstName"], row["senderLastName"]) if part)
        media_refs, attachment_names, attachment_status = [], [], []
        for attached in attachments.get(row["uid"], []):
            file_id = attached["fileId"]
            name = attached["fileName"] or file_id
            attachment_names.append(name)
            path = stored_files.get(file_id)
            if not path:
                attachment_status.append(f"{name}: Local file not found")
                continue
            plaintext, status = td.decrypt_stored_file(
                path, file_id, attached["encryptionKey"], attached["unencryptedByteCount"],
                attached["storageFormatVersion"])
            if plaintext is None:
                attachment_status.append(f"{name}: {status}")
                continue
            reference = check_in_embedded_media(
                path, plaintext, name=name, force_type=attached["mediaType"] or None,
                force_creation_date=td.timestamp(row["createdAt"]))
            if reference:
                media_refs.append(reference)
                attachment_status.append(f"{name}: Authenticated and embedded")
            else:
                attachment_status.append(f"{name}: Authenticated; could not embed")
        yield (td.timestamp(row["createdAt"]), td.timestamp(row["processedAt"]),
               td.timestamp(row["deliveredAt"]), td.timestamp(row["readAt"]),
               td.timestamp(row["lastEditedAt"]), td.timestamp(row["deletedAt"]),
               "Inbound" if row["senderContactUid"] else "Outbound", row["senderIdentity"],
               conversation, row["content"], media_refs, ", ".join(attachment_names),
               "; ".join(attachment_status), row["uid"], td.blob_hex(row["messageId"]),
               row["messageType"], row["threadId"], row["conversationUid"],
               row["senderContactUid"], sender_name)


@artifact_processor
def threemaMessages(context):
    data_headers = (("Created", "datetime"), ("Processed", "datetime"),
                    ("Delivered", "datetime"), ("Read", "datetime"),
                    ("Last Edited", "datetime"), ("Deleted", "datetime"),
                    "Direction", "Sender Threema ID", "Conversation", "Content",
                    ("Attachments", "media"), "Attachment Names", "Attachment Status",
                    "Message UID", "Message ID", "Message Type", "Thread ID", "Conversation UID", "Sender UID",
                    "Sender Name", "Source File")
    files_found = [str(path) for path in context.get_files_found()]
    rows, source = td.read_databases(
        context, lambda db: _messages(db, files_found), "Threema Desktop Messages")
    return data_headers, rows, source


def _reactions(db):
    if not td.columns(db, "messageReactions"):
        return
    for row in db.execute("""SELECT r.reactionAt, r.uid, r.reaction, r.senderIdentity,
            m.uid AS messageUid, m.messageId, m.createdAt, m.messageType,
            COALESCE(t.text, '') AS messageText
        FROM messageReactions r JOIN messages m ON m.uid=r.messageUid
        LEFT JOIN messageTextData t ON t.messageUid=m.uid
        ORDER BY r.reactionAt, r.uid"""):
        reaction = {0: "Acknowledged", 1: "Declined"}.get(row["reaction"], row["reaction"])
        yield (td.timestamp(row["reactionAt"]), td.timestamp(row["createdAt"]), row["uid"],
               reaction, row["senderIdentity"], row["messageUid"],
               td.blob_hex(row["messageId"]), row["messageType"], row["messageText"])


@artifact_processor
def threemaReactions(context):
    data_headers = (("Reaction Time", "datetime"), ("Message Created", "datetime"),
                    "Reaction UID", "Reaction", "Sender Threema ID",
               "Message UID", "Message ID", "Message Type", "Message Text", "Source File")
    rows, source = td.read_databases(context, _reactions, "Threema Desktop Message Reactions")
    return data_headers, rows, source


def _attachments(db):
    specs = (("messageFileData", "File"), ("messageImageData", "Image"),
             ("messageVideoData", "Video"), ("messageAudioData", "Audio"))
    for table, kind in specs:
        if not td.columns(db, table):
            continue
        optional = td.optional(db, table, ("fileName", "fileSize", "mediaType", "caption",
                              "correlationId", "fileDataUid", "blobDownloadState",
                              "downloadFailureReason", "height", "width", "durationSeconds"), "a")
        query = f"""SELECT m.createdAt, a.uid, a.messageUid, m.messageId, {optional},
                f.fileId, f.unencryptedByteCount, f.storageFormatVersion
            FROM {table} a JOIN messages m ON m.uid=a.messageUid
            LEFT JOIN fileData f ON f.uid=a.fileDataUid ORDER BY m.createdAt, a.uid"""
        for row in db.execute(query):
            yield (td.timestamp(row["createdAt"]), row["uid"], row["messageUid"],
                   td.blob_hex(row["messageId"]), kind, row["fileName"], row["mediaType"],
                   row["fileSize"], row["caption"], row["correlationId"], row["fileId"],
                   row["unencryptedByteCount"], row["storageFormatVersion"],
                   row["blobDownloadState"], row["downloadFailureReason"], row["height"],
                   row["width"], row["durationSeconds"])


@artifact_processor
def threemaAttachments(context):
    data_headers = (("Message Created", "datetime"), "Attachment UID", "Message UID", "Message ID", "Type",
               "Filename", "Media Type", "Declared Size", "Caption", "Correlation ID",
               "Local File ID", "Stored Plaintext Size", "Storage Format", "Download State",
               "Download Failure", "Height", "Width", "Duration (s)", "Source File")
    rows, source = td.read_databases(context, _attachments, "Threema Desktop Attachments")
    return data_headers, rows, source


def _group_calls(db):
    if not td.columns(db, "runningGroupCalls"):
        return
    started = "c.startedAt" if "startedAt" in td.columns(db, "runningGroupCalls") else "c.receivedAt"
    for row in db.execute(f"""SELECT {started} AS startedAt, c.uid, c.groupUid, g.groupId,
            g.name, c.creatorIdentity, c.protocolVersion, c.baseUrl, c.nFailed
        FROM runningGroupCalls c LEFT JOIN groups g ON g.uid=c.groupUid
        ORDER BY startedAt, c.uid"""):
        yield (td.timestamp(row["startedAt"]), row["uid"], row["groupUid"],
               td.blob_hex(row["groupId"]), row["name"], row["creatorIdentity"],
               row["protocolVersion"], row["baseUrl"], row["nFailed"])


@artifact_processor
def threemaGroupCalls(context):
    data_headers = (("Started", "datetime"), "Call UID", "Group UID", "Group ID", "Group Name",
               "Creator Threema ID", "Protocol Version", "SFU Base URL", "Failed Peeks",
               "Source File")
    rows, source = td.read_databases(context, _group_calls, "Threema Desktop Persisted Group Calls")
    return data_headers, rows, source
