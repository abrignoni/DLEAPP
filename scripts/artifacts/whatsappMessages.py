__artifacts_v2__ = {
    "whatsappMessages": {
        "name": "WhatsApp Messages",
        "description": "Messages from WhatsApp's ChatStorage.sqlite. Each row is "
                       "joined to its chat session for the conversation name, to "
                       "the group member record where the message was sent in a "
                       "group, and to its media item where one is attached. The "
                       "attached file, when present in the extraction, is embedded "
                       "against the message.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "Direction is taken from the ZISFROMME column: a set flag is "
                 "reported as Outgoing, a clear flag as Incoming. It is left "
                 "blank where ZISFROMME is NULL and on ZMESSAGETYPE 6 rows, "
                 "which in the tested corpus occurred only in group chats and "
                 "never carried a set flag, so reporting them as Incoming "
                 "would present a system entry as a received message. "
                 "Type Code is the "
                 "ZMESSAGETYPE value the database stores and is left as the integer "
                 "rather than a guessed label; where a message carries a file, the "
                 "file itself is embedded so its kind is visible directly. A row "
                 "with an empty message body may be a media message, a system entry "
                 "such as a group change, or a message whose body the database does "
                 "not hold.",
        "paths": (
            '*/ChatStorage.sqlite*',
            '*/Message/Media/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
        "sample_data": {
            "whatsapp_macos": "WhatsApp macOS | 45363 rows",
        },
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Chat JID",
                "conversationLabelColumn": "Chat",
                "textColumn": "Message",
                "timeColumn": "Message Date",
                "directionColumn": "Direction",
                "directionSentValue": "Outgoing",
                "senderColumn": "Sender",
                "mediaColumn": "Media",
            }
        },
    },
}

import os
from datetime import datetime, timezone

from scripts import whatsapp
from scripts.ilapfuncs import (artifact_processor, check_in_media,
                               logfunc, open_sqlite_db_readonly)

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)

# ZMESSAGETYPE values that are not a sent or received message. Established by
# testing: every type 6 row in the tested corpus sat in a group chat and had
# ZISFROMME clear, which is the shape of a system entry rather than a message.
_NON_MESSAGE_TYPES = {6}

_QUERY = """
    SELECT
        m.Z_PK,
        m.ZMESSAGEDATE, m.ZSENTDATE, m.ZISFROMME, m.ZMESSAGETYPE, m.ZSTARRED,
        m.ZTEXT, m.ZFROMJID, m.ZPUSHNAME, m.ZSTANZAID,
        cs.ZPARTNERNAME, cs.ZCONTACTJID,
        gm.ZMEMBERJID, gm.ZCONTACTNAME,
        mi.ZMEDIALOCALPATH
    FROM ZWAMESSAGE m
    LEFT JOIN ZWACHATSESSION cs ON m.ZCHATSESSION = cs.Z_PK
    LEFT JOIN ZWAGROUPMEMBER  gm ON m.ZGROUPMEMBER = gm.Z_PK
    LEFT JOIN ZWAMEDIAITEM    mi ON m.ZMEDIAITEM   = mi.Z_PK
"""


def _direction(is_from_me, message_type):
    """Direction only where the row is a message and the flag was recorded.

    A NULL ZISFROMME and a non-message row both fall through to Incoming if
    the flag is read as a plain boolean, which would show a system entry as a
    message the account received.
    """
    if is_from_me is None or message_type in _NON_MESSAGE_TYPES:
        return ""
    return "Outgoing" if is_from_me else "Incoming"


def _sender(is_from_me, chat_jid, partner_name, contact_jid, from_jid,
            push_name, member_name, member_jid):
    """Best available human label for who sent the message."""
    if is_from_me:
        return "Local user"
    if chat_jid and chat_jid.endswith("@g.us"):
        return push_name or member_name or member_jid or from_jid or ""
    return partner_name or contact_jid or from_jid or ""


@artifact_processor
def whatsappMessages(context):
    data_headers = (
        ("Message Date", "datetime"), "Direction", "Sender", "Chat",
        ("Media", "media"), "Message", "Media Filename", "Type Code", "Starred",
        ("Sent Date", "datetime"), "Chat Type", "Sender JID", "Chat JID",
        "Message ID", "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""

    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    root = whatsapp.media_root(source, files_found)
    relative_source = context.get_relative_path(source)

    data_list = []
    embedded = 0
    for row in database.execute(_QUERY):
        (_pk, message_date, sent_date, is_from_me, message_type, starred,
         text, from_jid, push_name, stanza_id,
         partner_name, contact_jid, member_jid, member_name,
         media_local_path) = row

        media_ref = ""
        media_name = ""
        if media_local_path:
            media_name = os.path.basename(media_local_path)
            if root:
                reference = check_in_media(media_local_path, name=media_name)
                if reference:
                    media_ref = reference
                    embedded += 1

        direction = _direction(is_from_me, message_type)
        sender = _sender(is_from_me, contact_jid, partner_name, contact_jid,
                         from_jid, push_name, member_name, member_jid)
        sender_jid = "" if is_from_me else (
            member_jid or from_jid or contact_jid or "")

        data_list.append((
            whatsapp.cocoa_to_datetime(message_date),
            direction,
            sender,
            partner_name or contact_jid or "",
            media_ref,
            text or "",
            media_name,
            message_type if message_type is not None else "",
            "Yes" if starred else "",
            whatsapp.cocoa_to_datetime(sent_date),
            whatsapp.jid_kind(contact_jid),
            sender_jid,
            contact_jid or "",
            stanza_id or "",
            relative_source,
        ))

    database.close()
    data_list.sort(key=lambda r: (r[12], r[0] if isinstance(r[0], datetime) else _EPOCH_MIN))
    logfunc(f"WhatsApp Messages: {len(data_list)} message(s); "
            f"{embedded} carry an embedded media file.")
    return data_headers, data_list, source
