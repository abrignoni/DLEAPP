"""Phone Link (Your Phone) databases: the copy a Windows PC keeps of a linked phone's data.

Author: @AlexisBrignoni, Claude.

Phone Link keeps its databases in a folder under the user's package folder,
AppData/Local/Packages/Microsoft.YourPhone_8wekyb3d8bbwe/LocalCache/Indexed/<device>/System/Database,
holding phone.db (SMS and MMS), photos.db, phoneapps.db, contacts.db, calling.db and
other SQLite databases. The folder layout and file names were read from the
hexordia_mvs2025_win11 image (Phone Link 1.24101.61.0); the column meanings stated in
the notes were measured by comparing those databases with the Android image of the
same exercise, userb2_a13, row for row.
"""

import os
import sqlite3

from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media, logfunc,
                               open_sqlite_db_readonly)
from scripts.filetype import guess as guess_type
from scripts.windows_registry import filetime_utc, user_from_path

__artifacts_v2__ = {
    "phoneLinkMessages": {
        "name": "Phone Link Messages",
        "description": "SMS and MMS messages of a phone linked to the PC with Phone Link, from "
                       "each linked phone's phone.db: time, direction, sender, conversation, the "
                       "text of the message or its text parts, and any MMS part stored as bytes.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the message (SMS) and mms tables of each phone.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per table row, ordered by "
                 "time within each database. The folder under LocalCache/Indexed that holds "
                 "the database is named in Device Folder (the tested image holds one linked "
                 "phone, so one such folder); User is the home folder the package sits in. "
                 "Measured on hexordia_mvs2025_win11 (Phone Link 1.24101.61.0, one linked "
                 "phone, 15 SMS and 2 MMS rows) against the sms, pdu and part tables of the "
                 "Android image of the same exercise, userb2_a13: message_id equals the "
                 "phone's sms _id on all 15 SMS rows, and thread_id, type and body are equal "
                 "on all 15; from_address equals the phone's address on the 12 received rows "
                 "and is empty on the 3 sent rows. Timestamp is message.timestamp read as a "
                 "FILETIME (100-nanosecond intervals since 1601-01-01 UTC), and it equals the "
                 "phone's sms date (milliseconds since 1970-01-01 UTC) on all 15 rows. The "
                 "phone holds 19 SMS; the 4 the PC lacks are the 4 newest. Both MMS rows "
                 "equal the phone's pdu rows of the same _id on thread_id, msg_box and date, "
                 "read the same way at whole seconds, and both parts equal the phone's part "
                 "rows on message id and text. Domingues et al. describe the same columns for "
                 "the 2019 Your Phone app: a FILETIME timestamp, type 1 for received and 2 "
                 "for sent, status 1 for unread and 2 for read, an empty from_address on a "
                 "sent SMS, and pc_status of unestablished purpose (Digital Investigation 30, "
                 "2019, section 3.6.2, https://doi.org/10.1016/j.diin.2019.06.003). Type is "
                 "the stored type named by Android's Telephony.TextBasedSmsColumns "
                 "MESSAGE_TYPE_* constants for SMS "
                 "(https://developer.android.com/reference/android/provider/Telephony.TextBasedSmsColumns) "
                 "and Telephony.BaseMmsColumns MESSAGE_BOX_* constants for MMS "
                 "(https://developer.android.com/reference/android/provider/Telephony.BaseMmsColumns), "
                 "since it equals the phone's own value; Direction is Incoming for 1 and "
                 "Outgoing for 2 and blank otherwise. Only the values 1 and 2 (SMS) and 1 "
                 "(MMS) occur on the tested image, so the other names are unexercised. "
                 "Sender is from_address as stored; it held an empty string on each of the 3 "
                 "Outgoing rows. Conversation is the send_address values of the "
                 "conversation's participant rows, else the conversation's recipient_list. "
                 "Status (as stored) is message.status or mms.status; on the tested image it "
                 "held 1 on each of the 11 SMS rows the phone's sms table marks unread (read "
                 "0) and 2 on each of the 6 SMS and MMS rows the phone marks read, as the "
                 "2019 description has it. PC Status (as stored) is pc_status, whose meaning "
                 "is not established. An MMS row's Message is the text of its text/ parts in "
                 "sequence order, so a SMIL layout part is not shown as text; Attachments "
                 "shows each part that stores bytes in its blob column, sniffed for type, on "
                 "the row of the message it belongs to (mms_part.message_id is the recorded "
                 "link). Both MMS parts on the tested image are text with no blob, and the "
                 "2019 study found the blob column always NULL, so Attachments and Attachment "
                 "Types held no value on any row and the "
                 "rendering path is unexercised. Recipients (as stored) lists the "
                 "message_to_address rows of an SMS and the mms_address rows of an MMS. "
                 "Recipients (as stored) held no value on any row of the tested image, where "
                 "both tables were empty. Subject held an empty string on every row. SIM "
                 "Subscription ID is subscription_id, an id of the Phone Link SIM "
                 "Subscriptions artifact; SIM Subscription ID, Device Folder and User each "
                 "held one value on every row of the tested image, which holds one linked "
                 "phone with one SIM in one home folder. Not read: rcs_chat, rcs_filetransfer and rcs_conversation, which "
                 "held no rows on the tested image, so neither their times nor their type "
                 "values could be checked; conversation_attribute, sending_message and sync, "
                 "also empty; and two conversation rows with no messages whose recipient_list "
                 "is a placeholder rather than an address. Each database was also read with "
                 "its -wal ignored and gave the same rows; earlier states held in the -wal "
                 "frames are not recovered. Phone Link folders with no LocalCache/Indexed "
                 "databases (only a Settings folder) were found on af_case2_win10, "
                 "pc_mus_001_win11 and szechuan_win10; Settings/settings.dat, a registry hive "
                 "that on the tested image holds a key named for the Device Folder id under "
                 "LocalState/Devices, is not "
                 "read, because its values use packaged-app value types this module does not "
                 "decode.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/phone.db*',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 17 rows (15 SMS, 2 MMS)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no phone.db; Phone Link Settings folder only)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no phone.db; Phone Link Settings folder only)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no phone.db; Phone Link Settings folder only)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no Microsoft.YourPhone_* folder found)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (no Microsoft.YourPhone_* folder found)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no Microsoft.YourPhone_* folder found)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no Microsoft.YourPhone_* folder found)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (no Microsoft.YourPhone_* folder found)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no Microsoft.YourPhone_* folder found)",
        },
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Conversation ID",
                "conversationLabelColumn": "Conversation",
                "textColumn": "Message",
                "timeColumn": "Timestamp",
                "directionColumn": "Direction",
                "directionSentValue": "Outgoing",
                "senderColumn": "Sender",
                "mediaColumn": "Attachments",
            }
        },
    },
    "phoneLinkPhotos": {
        "name": "Phone Link Photos",
        "description": "Photos of a phone linked to the PC with Phone Link, from each linked "
                       "phone's photos.db: taken and modified times, name, type, size and the "
                       "thumbnail stored with each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the media table of each photos.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per table row. Measured on "
                 "hexordia_mvs2025_win11 (Phone Link 1.24101.61.0, 4 rows) against the "
                 "MediaStore files table of the Android image of the same exercise, "
                 "userb2_a13: Media ID equals the phone's files _id on all 4 rows, and Name, "
                 "MIME Type, Width, Height and Size (bytes) equal its _display_name, "
                 "mime_type, width, height and _size. Taken Time is taken_time read as a "
                 "FILETIME (100-nanosecond intervals since 1601-01-01 UTC) and equals the "
                 "phone's datetaken (milliseconds since 1970-01-01 UTC) on all 4 rows; "
                 "Modified Time is last_updated_time read the same way and equals the "
                 "phone's date_modified (seconds) on all 4. Last Seen Time is last_seen_time "
                 "read the same way; what event it records is not established, and its 4 "
                 "values on the tested image lie within 2 milliseconds of each other. Image "
                 "shows the media blob when the row stores one and the thumbnail blob "
                 "otherwise, each sniffed for its type; Image Stored says which blobs the row "
                 "holds. Image Stored held thumbnail on every row of the tested image: all 4 "
                 "rows store a JPEG thumbnail and no media blob, including the one whose MIME "
                 "Type is image/png, so a full-size image was not shown on any row. Device "
                 "Folder and User each held one value on every row of the tested image, "
                 "which holds one linked phone in one home folder. URI is the phone's content URI as stored, and "
                 "Orientation is as stored. Phone Link has been described as also saving "
                 "photos to a Recent Photos folder (kacos2000, "
                 "https://github.com/kacos2000/Win10/blob/d39f62d323b320bf55cd2e9c643aa3feaed54eb8/YourPhone/readme.md#L50); "
                 "no such folder is in the tested image, and none is read.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/photos.db*',),
        "output_types": "standard",
        "artifact_icon": "image",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no photos.db; Phone Link Settings folder only)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no photos.db; Phone Link Settings folder only)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no photos.db; Phone Link Settings folder only)",
        },
    },
    "phoneLinkPhoneApps": {
        "name": "Phone Link Phone Apps",
        "description": "Apps listed for a phone linked to the PC with Phone Link, from each "
                       "linked phone's phoneapps.db: app name, package name, version, the time "
                       "stored with each and its icon.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the phone_apps table of each phoneapps.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per table row. Measured on "
                 "hexordia_mvs2025_win11 (Phone Link 1.24101.61.0, 42 rows) against the "
                 "phoneAppsTable of the Link to Windows app's PhoneAppsDatabase on the "
                 "Android image of the same exercise, userb2_a13: all 42 package names are "
                 "there, and App Name, Version and Last Updated Time equal its appName, "
                 "appVersion and lastUpdatedTime on all 42. Last Updated Time is "
                 "last_updated_time read as milliseconds since 1970-01-01 UTC, a different "
                 "unit from the FILETIME times of phone.db and photos.db. It held 3 distinct "
                 "values across the 42 rows; what event it records is not established, and "
                 "it should not be read as each app's install or update time. Icon renders the blob "
                 "column, a PNG on all 42 rows. The list matches the phoneAppsTable of the "
                 "phone's com.microsoft.appmanager (Link to Windows) database; it does not "
                 "record that any app was used. Device Folder and User each held "
                 "one value on every row of the tested image, which holds one linked phone in "
                 "one home folder. Not shown: etag (0 on every "
                 "row), phoneapp_web_url (empty on every row), checksum (equal to "
                 "last_updated_time on every row), and favorite_rank, which held -1 on every "
                 "row while the phone's favoriteRank differs from it on all 42. Not read: "
                 "recent_apps and pcapp_data, both empty on the tested image.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/phoneapps.db*',),
        "output_types": "standard",
        "artifact_icon": "grid",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 42 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no phoneapps.db; Phone Link Settings folder only)",
        },
    },
    "phoneLinkSubscriptions": {
        "name": "Phone Link SIM Subscriptions",
        "description": "SIM subscriptions of a phone linked to the PC with Phone Link, from the "
                       "subscription table of each linked phone's phone.db: subscription id, "
                       "SIM slot, number, display name and country code.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the subscription table of each phone.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per table row. Measured on "
                 "hexordia_mvs2025_win11 (1 row) against the siminfo table of telephony.db "
                 "on the Android image of the same exercise, userb2_a13: Subscription ID "
                 "equals siminfo _id, SIM Slot equals sim_id, Number equals number and "
                 "Display Name equals display_name (not carrier_name); Country ISO is "
                 "country_iso as stored. SIM Subscription ID in Phone Link Messages refers "
                 "to Subscription ID here. Not shown: the messaging limits and capability "
                 "columns (maximum message and image sizes, MMS and RCS flags, the default "
                 "subscription flags), which describe the carrier configuration, and "
                 "is_roaming, whose 1 on the tested image matches the phone's data_roaming "
                 "setting, so it is not established that it records the phone was roaming.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/phone.db*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no phone.db; Phone Link Settings folder only)",
        },
    },
    "phoneLinkContacts": {
        "name": "Phone Link Contacts",
        "description": "Contacts of a phone linked to the PC with Phone Link, from each linked "
                       "phone's contacts.db: names, company, notes, phone numbers, email and "
                       "postal addresses, dates, web addresses and the stored thumbnail.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the contact table of each contacts.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per contact, with the "
                 "phonenumber, emailaddress, postaladdress, contactdate and contacturl rows "
                 "of that contact_id listed in their own columns, each value followed by its "
                 "label in parentheses when one is stored and its stored type number in "
                 "brackets. Unexercised: every one of these tables is "
                 "empty on hexordia_mvs2025_win11, the only tested image holding a contacts.db, and "
                 "the code was run only on a synthetic database built with that file's "
                 "schema. Last Updated Time is last_updated_time read as a FILETIME "
                 "(100-nanosecond intervals since 1601-01-01 UTC), as SQLECmd's Phone Link "
                 "contacts map reads it "
                 "(https://github.com/EricZimmerman/SQLECmd/blob/4e77e17dfd5c2ff4cbeacaed86d51f05f35244d3/SQLMap/Maps/Windows_YourPhone_ContactsDB.smap#L17) "
                 "and as phone.db stores its measured times; no populated row confirmed it. "
                 "Thumbnail renders the thumbnail blob when the row stores one, sniffed for "
                 "its type. The type numbers are not given names, since no source here "
                 "establishes them for this schema.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/contacts.db*',),
        "output_types": "standard",
        "artifact_icon": "users",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 0 rows (contact table present, empty)",
        },
    },
    "phoneLinkCalls": {
        "name": "Phone Link Call History",
        "description": "Call history of a phone linked to the PC with Phone Link, from the "
                       "call_history table of each linked phone's calling.db: start time, "
                       "number, duration and the stored call type.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Phone Link",
        "notes": "Reads the call_history table of each calling.db under a user's "
                 "Packages/Microsoft.YourPhone_* folder, one row per table row. Unexercised: "
                 "the table is empty on hexordia_mvs2025_win11, the only tested image holding a "
                 "calling.db (the phone of the same exercise, userb2_a13, holds no calls "
                 "either), and the code was run only on a synthetic database built with "
                 "that file's schema. Start Time and Last Updated Time are start_time and "
                 "last_updated_time read as FILETIMEs (100-nanosecond intervals since "
                 "1601-01-01 UTC), as kacos2000's call history query reads them "
                 "(https://github.com/kacos2000/Win10/blob/d39f62d323b320bf55cd2e9c643aa3feaed54eb8/YourPhone/yourphone_calls.sql#L6-L7) "
                 "and as phone.db stores its measured times; no populated row confirmed it, "
                 "and Start Time (as stored) keeps the raw value. Duration (as stored) and "
                 "Call Type (as stored) are the duration and call_type columns; that query "
                 "describes call_type as following Android's CallLog.Calls types, which this "
                 "module does not apply without a populated row to check it against. Read "
                 "(as stored) is is_read.",
        "paths": ('*/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/calling.db*',),
        "output_types": "standard",
        "artifact_icon": "phone",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, Phone Link 1.24101.61.0 | 0 rows (call_history table present, empty)",
        },
    },
}

# Android Telephony.TextBasedSmsColumns MESSAGE_TYPE_* and BaseMmsColumns MESSAGE_BOX_*
# constant values, from developer.android.com (fetched 2026-10-17).
SMS_TYPES = {0: 'MESSAGE_TYPE_ALL', 1: 'MESSAGE_TYPE_INBOX', 2: 'MESSAGE_TYPE_SENT',
             3: 'MESSAGE_TYPE_DRAFT', 4: 'MESSAGE_TYPE_OUTBOX', 5: 'MESSAGE_TYPE_FAILED',
             6: 'MESSAGE_TYPE_QUEUED'}
MMS_BOXES = {0: 'MESSAGE_BOX_ALL', 1: 'MESSAGE_BOX_INBOX', 2: 'MESSAGE_BOX_SENT',
             3: 'MESSAGE_BOX_DRAFTS', 4: 'MESSAGE_BOX_OUTBOX', 5: 'MESSAGE_BOX_FAILED'}
DIRECTIONS = {1: 'Incoming', 2: 'Outgoing'}

_DATABASE_PARENTS = ('system', 'database')


def _type_label(names, value):
    if value is None or value == '':
        return ''
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    return f'{names.get(number, "unknown")} ({number})'


def databases(context, name):
    """(staged path, relative path, device folder, user) for each staged `name` database.

    A database is one whose path ends Indexed/<device>/System/Database/<name>; the
    device folder is the one Phone Link names for the linked phone. Sidecars are
    left to SQLite, which reads them beside the database.
    """
    found = []
    seen = set()
    for item in context.get_files_found():
        path = str(item)
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        if os.path.basename(path).lower() != name:
            continue
        relative = context.get_relative_path(path)
        parts = relative.replace('\\', '/').split('/')
        if len(parts) < 5 or [p.lower() for p in parts[-3:-1]] != list(_DATABASE_PARENTS) \
                or parts[-5].lower() != 'indexed':
            continue
        found.append((path, relative, parts[-4], user_from_path(relative)))
    return sorted(found, key=lambda entry: entry[1])


def _open(path, label):
    db = open_sqlite_db_readonly(path)
    if db is None:
        logfunc(f'{label}: could not open {path}')
        return None
    try:
        db.execute('SELECT count(*) FROM sqlite_master').fetchone()
    except sqlite3.DatabaseError as ex:
        logfunc(f'{label}: could not read {path}: {ex}')
        db.close()
        return None
    return db


def _columns(db, table):
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def _select(db, table, wanted, order=''):
    """Rows of `table` as dicts holding each wanted column, None for one the table lacks."""
    present = _columns(db, table)
    if not present:
        return None
    names = ', '.join(f'"{c}"' if c in present else f'NULL AS "{c}"' for c in wanted)
    cursor = db.execute(f'SELECT {names} FROM "{table}" {order}')
    return [dict(zip(wanted, row)) for row in cursor]


def _media(source, data, name, label):
    """A media reference for blob bytes whose type the content names, else None."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        return None, ''
    kind = guess_type(bytes(data[:8192]))
    mime = kind.mime if kind else ''
    if not mime:
        logfunc(f'{label}: a {len(data)}-byte blob in {source} has no recognised type; not shown')
        return None, 'unrecognised'
    extension = kind.extension if kind else None
    return check_in_embedded_media(source, bytes(data), name, force_type=mime,
                                   force_extension=extension), mime


def _unix_ms_utc(value):
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return filetime_utc(value * 10_000 + 116444736000000000)
    except (OverflowError, ValueError):
        return ''


def _conversation_labels(db):
    labels = {}
    for row in _select(db, 'conversation', ('thread_id', 'recipient_list')) or []:
        labels[row['thread_id']] = row['recipient_list'] or ''
    participants = {}
    for row in _select(db, 'participant', ('thread_id', 'send_address'), 'ORDER BY id') or []:
        if row['send_address']:
            participants.setdefault(row['thread_id'], []).append(row['send_address'])
    for thread_id, addresses in participants.items():
        labels[thread_id] = ', '.join(addresses)
    return labels


def _addresses(rows, key):
    grouped = {}
    for row in rows or []:
        if row.get('address'):
            grouped.setdefault(row[key], []).append(str(row['address']))
    return grouped


@artifact_processor
def phoneLinkMessages(context):
    data_headers = (
        ('Timestamp', 'datetime'),
        'Direction',
        'Sender',
        'Conversation',
        'Message',
        ('Attachments', 'media'),
        'Attachment Types',
        'Subject',
        'Kind',
        'Type',
        'Status (as stored)',
        'PC Status (as stored)',
        'Recipients (as stored)',
        'SIM Subscription ID',
        'Conversation ID',
        'Message ID',
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link Messages'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'phone.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        rows = []
        try:
            labels = _conversation_labels(db)
            sms_to = _addresses(_select(db, 'message_to_address', ('message_id', 'address')),
                                'message_id')
            for row in _select(db, 'message', (
                    'message_id', 'thread_id', 'status', 'from_address', 'type', 'subject',
                    'body', 'timestamp', 'pc_status', 'subscription_id')) or []:
                rows.append((
                    filetime_utc(row['timestamp']),
                    DIRECTIONS.get(row['type'], ''),
                    row['from_address'] if row['from_address'] is not None else '',
                    labels.get(row['thread_id'], ''),
                    row['body'] if row['body'] is not None else '',
                    [],
                    '',
                    row['subject'] if row['subject'] is not None else '',
                    'SMS',
                    _type_label(SMS_TYPES, row['type']),
                    row['status'] if row['status'] is not None else '',
                    row['pc_status'] if row['pc_status'] is not None else '',
                    ', '.join(sms_to.get(row['message_id'], [])),
                    row['subscription_id'] if row['subscription_id'] is not None else '',
                    row['thread_id'],
                    row['message_id'],
                    device, user, relative,
                ))
            mms_to = _addresses(_select(db, 'mms_address', ('message_id', 'address', 'type')),
                                'message_id')
            parts = {}
            for part in _select(db, 'mms_part', (
                    'part_id', 'message_id', 'sequence_num', 'content_type', 'text', 'name',
                    'blob'), 'ORDER BY message_id, sequence_num, part_id') or []:
                parts.setdefault(part['message_id'], []).append(part)
            for row in _select(db, 'mms', (
                    'message_id', 'thread_id', 'status', 'type', 'subscription_id', 'subject',
                    'timestamp', 'pc_status', 'from_address')) or []:
                texts, media, kinds = [], [], []
                for part in parts.get(row['message_id'], []):
                    if part['text'] and str(part['content_type'] or '').lower().startswith('text/'):
                        texts.append(part['text'])
                    reference, mime = _media(path, part['blob'],
                                             part['name'] or f'mms_part_{part["part_id"]}', label)
                    if reference:
                        media.append(reference)
                    if mime:
                        kinds.append(mime)
                rows.append((
                    filetime_utc(row['timestamp']),
                    DIRECTIONS.get(row['type'], ''),
                    row['from_address'] if row['from_address'] is not None else '',
                    labels.get(row['thread_id'], ''),
                    '\n'.join(texts),
                    media,
                    ', '.join(kinds),
                    row['subject'] if row['subject'] is not None else '',
                    'MMS',
                    _type_label(MMS_BOXES, row['type']),
                    row['status'] if row['status'] is not None else '',
                    row['pc_status'] if row['pc_status'] is not None else '',
                    ', '.join(mms_to.get(row['message_id'], [])),
                    row['subscription_id'] if row['subscription_id'] is not None else '',
                    row['thread_id'],
                    row['message_id'],
                    device, user, relative,
                ))
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
        finally:
            db.close()
        rows.sort(key=lambda r: (r[0].isoformat() if r[0] else '', r[8], r[15]))
        data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def phoneLinkPhotos(context):
    data_headers = (
        ('Taken Time', 'datetime'),
        ('Modified Time', 'datetime'),
        ('Last Seen Time', 'datetime'),
        ('Image', 'media'),
        'Image Stored',
        'Name',
        'MIME Type',
        'Width',
        'Height',
        'Size (bytes)',
        'Orientation',
        'URI',
        'Media ID',
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link Photos'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'photos.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        try:
            records = _select(db, 'media', (
                'id', 'name', 'last_updated_time', 'taken_time', 'orientation', 'last_seen_time',
                'mime_type', 'height', 'width', 'size', 'uri', 'thumbnail', 'media'),
                'ORDER BY id') or []
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            records = []
        finally:
            db.close()
        for row in records:
            stored = []
            if row['media']:
                stored.append('media')
            if row['thumbnail']:
                stored.append('thumbnail')
            image = None
            name = row['name'] or str(row['id'])
            if row['media']:
                image, _ = _media(path, row['media'], name, label)
            if image is None and row['thumbnail']:
                image, _ = _media(path, row['thumbnail'], f'thumbnail_{name}', label)
            data_list.append((
                filetime_utc(row['taken_time']),
                filetime_utc(row['last_updated_time']),
                filetime_utc(row['last_seen_time']),
                image or '',
                ' and '.join(stored),
                row['name'] or '',
                row['mime_type'] or '',
                row['width'] if row['width'] is not None else '',
                row['height'] if row['height'] is not None else '',
                row['size'] if row['size'] is not None else '',
                row['orientation'] if row['orientation'] is not None else '',
                row['uri'] or '',
                row['id'],
                device, user, relative,
            ))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def phoneLinkPhoneApps(context):
    data_headers = (
        ('Last Updated Time', 'datetime'),
        'App Name',
        'Package Name',
        'Version',
        ('Icon', 'media'),
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link Phone Apps'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'phoneapps.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        try:
            records = _select(db, 'phone_apps', (
                'app_id', 'app_name', 'package_name', 'version', 'blob', 'last_updated_time'),
                'ORDER BY app_name, package_name') or []
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            records = []
        finally:
            db.close()
        for row in records:
            icon, _ = _media(path, row['blob'], f'{row["package_name"]}_icon', label)
            data_list.append((
                _unix_ms_utc(row['last_updated_time']),
                row['app_name'] or '',
                row['package_name'] or '',
                row['version'] or '',
                icon or '',
                device, user, relative,
            ))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def phoneLinkSubscriptions(context):
    data_headers = (
        'Subscription ID',
        'SIM Slot',
        'Number',
        'Display Name',
        'Country ISO',
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link SIM Subscriptions'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'phone.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        try:
            records = _select(db, 'subscription', (
                'subscription_id', 'sim_slot_index', 'number', 'name', 'country_iso'),
                'ORDER BY subscription_id') or []
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            records = []
        finally:
            db.close()
        for row in records:
            data_list.append((
                row['subscription_id'],
                row['sim_slot_index'] if row['sim_slot_index'] is not None else '',
                row['number'] or '',
                row['name'] or '',
                row['country_iso'] or '',
                device, user, relative,
            ))
    return data_headers, data_list, '\n'.join(sources)


def _grouped(db, table, value_column, type_column, extra=None):
    """{contact_id: ['value [type]', ...]} for one contact detail table."""
    wanted = ['contact_id', value_column, type_column] + ([extra] if extra else [])
    grouped = {}
    for row in _select(db, table, tuple(wanted), 'ORDER BY rowid') or []:
        value = row[value_column]
        if value in (None, ''):
            continue
        text = str(value)
        if extra and row[extra]:
            text = f'{text} ({row[extra]})'
        if row[type_column] is not None:
            text = f'{text} [{row[type_column]}]'
        grouped.setdefault(row['contact_id'], []).append(text)
    return grouped


@artifact_processor
def phoneLinkContacts(context):
    data_headers = (
        ('Last Updated Time', 'datetime'),
        'Display Name',
        'Given Name',
        'Middle Name',
        'Family Name',
        'Nickname',
        'Company',
        'Job Title',
        'Notes',
        'Phone Numbers',
        'Email Addresses',
        'Postal Addresses',
        'Dates',
        'Web Addresses',
        ('Thumbnail', 'media'),
        'Contact ID',
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link Contacts'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'contacts.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        try:
            numbers = _grouped(db, 'phonenumber', 'phone_number', 'phone_number_type', 'label')
            emails = _grouped(db, 'emailaddress', 'address', 'type', 'label')
            postal = _grouped(db, 'postaladdress', 'display_address', 'type', 'label')
            dates = _grouped(db, 'contactdate', 'display_date', 'date_type', 'label')
            urls = _grouped(db, 'contacturl', 'url_address', 'type', 'label')
            records = _select(db, 'contact', (
                'contact_id', 'display_name', 'nickname', 'last_updated_time', 'thumbnail',
                'company', 'job_title', 'notes', 'given_name', 'middle_name', 'family_name'),
                'ORDER BY contact_id') or []
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            records = []
        finally:
            db.close()
        for row in records:
            contact_id = row['contact_id']
            thumbnail, _ = _media(path, row['thumbnail'], f'contact_{contact_id}', label)
            data_list.append((
                filetime_utc(row['last_updated_time']),
                row['display_name'] or '',
                row['given_name'] or '',
                row['middle_name'] or '',
                row['family_name'] or '',
                row['nickname'] or '',
                row['company'] or '',
                row['job_title'] or '',
                row['notes'] or '',
                '\n'.join(numbers.get(contact_id, [])),
                '\n'.join(emails.get(contact_id, [])),
                '\n'.join(postal.get(contact_id, [])),
                '\n'.join(dates.get(contact_id, [])),
                '\n'.join(urls.get(contact_id, [])),
                thumbnail or '',
                contact_id,
                device, user, relative,
            ))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def phoneLinkCalls(context):
    data_headers = (
        ('Start Time', 'datetime'),
        ('Last Updated Time', 'datetime'),
        'Start Time (as stored)',
        'Phone Number',
        'Duration (as stored)',
        'Call Type (as stored)',
        'Read (as stored)',
        'Phone Account ID',
        'Call ID',
        'Device Folder',
        'User',
        'Source File',
    )
    label = 'Phone Link Call History'
    data_list = []
    sources = []
    for path, relative, device, user in databases(context, 'calling.db'):
        db = _open(path, label)
        if db is None:
            continue
        sources.append(path)
        try:
            records = _select(db, 'call_history', (
                'call_id', 'phone_number', 'duration', 'call_type', 'start_time', 'is_read',
                'phone_account_id', 'last_updated_time'), 'ORDER BY start_time, call_id') or []
        except sqlite3.DatabaseError as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            records = []
        finally:
            db.close()
        for row in records:
            data_list.append((
                filetime_utc(row['start_time']),
                filetime_utc(row['last_updated_time']),
                row['start_time'] if row['start_time'] is not None else '',
                row['phone_number'] or '',
                row['duration'] if row['duration'] is not None else '',
                row['call_type'] if row['call_type'] is not None else '',
                row['is_read'] if row['is_read'] is not None else '',
                row['phone_account_id'] or '',
                row['call_id'],
                device, user, relative,
            ))
    return data_headers, data_list, '\n'.join(sources)
