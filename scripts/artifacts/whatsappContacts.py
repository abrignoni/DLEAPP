__artifacts_v2__ = {
    "whatsappContacts": {
        "name": "WhatsApp Contacts",
        "description": "Address book entries WhatsApp keeps in ContactsV2.sqlite, "
                       "including the display name, phone number, WhatsApp id and "
                       "any business name, status text and note the database holds.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "These are the contacts WhatsApp stored, which is not necessarily "
                 "the same set as the device address book. A row can exist for a "
                 "correspondent the account never messaged.",
        "paths": ('*/ContactsV2.sqlite*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 244 rows"},
    },
    "whatsappChatSessions": {
        "name": "WhatsApp Chat Sessions",
        "description": "The conversation list from ChatStorage.sqlite: one row per "
                       "chat with its display name, JID, last message text and date, "
                       "unread count and archived/hidden/removed flags.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "The last message text and date are a summary the chat row caches; "
                 "the full messages are in the WhatsApp Messages artifact.",
        "paths": ('*/ChatStorage.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "list",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 159 rows"},
    },
    "whatsappGroupMembers": {
        "name": "WhatsApp Group Members",
        "description": "Membership of group chats from ChatStorage.sqlite: each "
                       "member's JID and name against the group's name, with the "
                       "admin and active flags the database records.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "A member row reflects the membership WhatsApp last recorded for "
                 "the group, not necessarily the membership at any earlier time.",
        "paths": ('*/ChatStorage.sqlite*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 1033 rows"},
    },
    "whatsappBlocked": {
        "name": "WhatsApp Blocked Contacts",
        "description": "JIDs on WhatsApp's block list, from the ZWABLACKLISTITEM "
                       "table in ChatStorage.sqlite.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "The table stores the JID only. A matching name, where shown, is "
                 "looked up from the push-name and chat tables in the same database.",
        "paths": ('*/ChatStorage.sqlite*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "slash",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 45 rows"},
    },
    "whatsappPushNames": {
        "name": "WhatsApp Push Names",
        "description": "The JID-to-display-name mapping WhatsApp caches in "
                       "ZWAPROFILEPUSHNAME. A push name is the name a correspondent "
                       "set for themselves, as their client advertised it.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "A push name is chosen by the correspondent, not by the account "
                 "holder or their address book, so it can differ from a saved "
                 "contact name and is not a verified identity.",
        "paths": ('*/ChatStorage.sqlite*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "tag",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 493 rows"},
    },
}

from scripts import whatsapp
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly


@artifact_processor
def whatsappContacts(context):
    data_headers = (
        "Full Name", "Given Name", "Last Name", "Business Name", "Phone Number",
        "WhatsApp ID", "Linked ID", "Status Text", "Note", ("Last Updated", "datetime"),
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.contacts_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    query = """SELECT ZFULLNAME, ZGIVENNAME, ZLASTNAME, ZBUSINESSNAME, ZPHONENUMBER,
                      ZWHATSAPPID, ZLID, ZABOUTTEXT, ZNOTES, ZLASTUPDATED
               FROM ZWAADDRESSBOOKCONTACT"""
    for (full, given, last, business, phone, wa_id, lid, about, note, updated) in database.execute(query):
        data_list.append((
            full or "", given or "", last or "", business or "", phone or "",
            wa_id or "", lid or "", about or "", note or "",
            whatsapp.cocoa_to_datetime(updated), relative_source,
        ))
    database.close()
    logfunc(f"WhatsApp Contacts: {len(data_list)} contact(s).")
    return data_headers, data_list, source


@artifact_processor
def whatsappChatSessions(context):
    data_headers = (
        ("Last Message Date", "datetime"), "Chat", "Chat Type", "Last Message",
        "Unread Count", "Archived", "Hidden", "Removed", "Message Count",
        "Chat JID", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    query = """SELECT ZLASTMESSAGEDATE, ZPARTNERNAME, ZCONTACTJID, ZLASTMESSAGETEXT,
                      ZUNREADCOUNT, ZARCHIVED, ZHIDDEN, ZREMOVED, ZMESSAGECOUNTER
               FROM ZWACHATSESSION"""
    for (last_date, partner, jid, last_text, unread, archived, hidden, removed, counter) in database.execute(query):
        data_list.append((
            whatsapp.cocoa_to_datetime(last_date),
            partner or jid or "",
            whatsapp.jid_kind(jid),
            last_text or "",
            unread if unread is not None else "",
            "Yes" if archived else "",
            "Yes" if hidden else "",
            "Yes" if removed else "",
            counter if counter is not None else "",
            jid or "",
            relative_source,
        ))
    database.close()
    logfunc(f"WhatsApp Chat Sessions: {len(data_list)} chat(s).")
    return data_headers, data_list, source


@artifact_processor
def whatsappGroupMembers(context):
    data_headers = (
        "Group", "Member Name", "Member JID", "Is Admin", "Is Active",
        "Group JID", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    query = """SELECT cs.ZPARTNERNAME, cs.ZCONTACTJID,
                      gm.ZCONTACTNAME, gm.ZFIRSTNAME, gm.ZMEMBERJID,
                      gm.ZISADMIN, gm.ZISACTIVE
               FROM ZWAGROUPMEMBER gm
               LEFT JOIN ZWACHATSESSION cs ON gm.ZCHATSESSION = cs.Z_PK"""
    for (group_name, group_jid, member_name, first_name, member_jid, is_admin, is_active) in database.execute(query):
        data_list.append((
            group_name or group_jid or "",
            member_name or first_name or "",
            member_jid or "",
            "Yes" if is_admin else "",
            "Yes" if is_active else "",
            group_jid or "",
            relative_source,
        ))
    database.close()
    logfunc(f"WhatsApp Group Members: {len(data_list)} membership row(s).")
    return data_headers, data_list, source


@artifact_processor
def whatsappBlocked(context):
    data_headers = ("Blocked JID", "Name", "JID Type", "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    # Names for the blocked JIDs, drawn from the same database.
    names = {}
    for table, jid_col, name_col in (
            ("ZWACHATSESSION", "ZCONTACTJID", "ZPARTNERNAME"),
            ("ZWAPROFILEPUSHNAME", "ZJID", "ZPUSHNAME")):
        try:
            for jid, name in database.execute(
                    f"SELECT {jid_col}, {name_col} FROM {table} WHERE {jid_col} IS NOT NULL"):
                if jid and name and jid not in names:
                    names[jid] = name
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    data_list = []
    for (jid,) in database.execute("SELECT ZJID FROM ZWABLACKLISTITEM"):
        data_list.append((jid or "", names.get(jid, ""), whatsapp.jid_kind(jid), relative_source))
    database.close()
    logfunc(f"WhatsApp Blocked Contacts: {len(data_list)} blocked JID(s).")
    return data_headers, data_list, source


@artifact_processor
def whatsappPushNames(context):
    data_headers = ("JID", "Push Name", "JID Type", "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    data_list = []
    for (jid, push_name) in database.execute(
            "SELECT ZJID, ZPUSHNAME FROM ZWAPROFILEPUSHNAME"):
        data_list.append((jid or "", push_name or "", whatsapp.jid_kind(jid), relative_source))
    database.close()
    logfunc(f"WhatsApp Push Names: {len(data_list)} push name(s).")
    return data_headers, data_list, source
