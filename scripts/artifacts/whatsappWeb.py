__artifacts_v2__ = {
    'whatsappWebAccount': {
        'name': 'WhatsApp Web - Account',
        'description': 'The WhatsApp account linked to a browser profile through WhatsApp Web: its '
                       'phone-number and LID device ids, push name, the browser family and profile, '
                       'and the time span and count of the messages the profile holds.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. Device ID (phone number) is the last-wid-md localStorage value and Device ID (LID) is WALid; WhatsApp Web's WAWebUserPrefsMeUser sets and reads them as the account's own device ids. Phone Number is the user part of the first. Push Name is the pushname of the account's own contact record, blank when that record holds none (the Chrome profile in the sample held none, the Firefox one did). Earliest and Latest Message are the oldest and newest t of the stored messages: what the browser holds, not the account's history. Stores not reported: signal-storage and wawc_db_enc hold key material; fts-storage holds 9-byte truncated HMAC-SHA256 values of word prefixes, not words; Of the 111 object stores in model-storage, seven are read (message, contact, chat, group-metadata, participant, reactions, blocklist). The rest are not reported; among them pinned-messages and poll-votes held rows from the scripted pin and poll vote. The wawc logs, sync, abprops, device-list, label and profile-pic-thumb stores were left out as client state.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'user',
    },
    'whatsappWebContacts': {
        'name': 'WhatsApp Web - Contacts',
        'description': 'Contacts held by WhatsApp Web in a browser profile: WhatsApp id, phone '
                       'number, address-book name, push name, username, about text, whether the '
                       'contact is in the phone\'s address book, and whether it is blocked.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. One row per contact record. WhatsApp ID is the record's id as stored; in the sample these were phone-number ids ending @s.whatsapp.net and LIDs ending @lid, while the chat and message stores write phone-number ids ending @c.us. Ids are matched across stores the way WhatsApp Web's WAWebWidFactory.createWid does, by reading @s.whatsapp.net as @c.us. Phone Number is the user part of a phone-number id or the phoneNumber a LID record carries. Name, Short Name, Push Name, Username and About are the stored name, shortName, pushname, username and textStatusString. In Address Book is isAddressBookContact, blank where the record holds none. Blocked is Yes when the id or its phone number is in the blocklist store. Type is the record's type value as stored; in the sample it held in on every address-book contact and nothing on the rest.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'users',
    },
    'whatsappWebChats': {
        'name': 'WhatsApp Web - Chats',
        'description': 'The chat list WhatsApp Web holds in a browser profile: chat id and name, '
                       'kind, the time of its latest stored message, message and unread counts, '
                       'and its archived, pinned, muted and locked state.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. Kind is read from the id's server part: c.us, s.whatsapp.net and lid are Individual, g.us Group, newsletter Channel, broadcast Broadcast. Latest Stored Message and Stored Messages are worked out from the message records whose key names the chat. Pinned At is the pin value read as epoch milliseconds, blank when the record holds no pin or 0. The scripted pin did not move this value: on both profiles the self chat's pin read as a time about two years before the window, so the reading is not confirmed by the scripted steps. Mute Expiration is reported as stored; in the sample it held 0 on most chats, -1 on two and nothing on the rest, and what -1 means is not established. Archived and Locked were identical on every chat in the sample: blank where the record holds no value, and No on every chat that held one.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'message-square',
    },
    'whatsappWebGroups': {
        'name': 'WhatsApp Web - Groups',
        'description': 'Group chats WhatsApp Web holds in a browser profile: creation time, '
                       'subject and when it was set, owner, description, members, admins and '
                       'past members with when and why they left.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. Created, Subject Set and Description Set are the creation, subjectTime and descTime values read as epoch seconds, blank when 0. Members, Member List, Admins and Super Admins come from the group's participant record. Past Members lists the pastParticipants entries with their stored leaveReason and leaveTs. Owner is the group's owner field, not established to be who created the group. Only Admins Send and Only Admins Edit Info are the announce and restrict values; Only Admins Send held No on all rows in the sample.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'users',
    },
    'whatsappWebMessages': {
        'name': 'WhatsApp Web - Messages',
        'description': 'Messages WhatsApp Web holds in a browser profile: time, chat, direction, '
                       'sender, type, delivery state, the text this artifact reads from outside the encrypted '
                       'column (document file names, contact card names, group invite names and '
                       'comments), media '
                       'details with the SHA-256 of the media file, replies, edits, reactions, '
                       'stars and forwards. Message text is encrypted at rest and is not decrypted.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. Timestamp is t read as epoch seconds; the scripted messages sent from Chrome came out in the order they were sent and inside the recorded window; the one text sent from Firefox (step 13) did not come out in either profile. Outgoing and Chat ID come from the message key, which WhatsApp Web's WAWebMsgKey builds as fromMe, chat id and message id joined by underscores. Sender is the account for outgoing messages, the record's author where it holds one (incoming group messages), and the chat otherwise; (me) marks the account. Message Body says Encrypted when the record holds msgRowOpaqueData, the one column WAWebSchemaMessage declares encrypted. Message Body held Encrypted on every row in the sample, and the text is not decrypted here. Mihir Singh Choudhary's research reports that the key for it is derived with HKDF from a root key and a salt on disk and a companion_enc_static that the server issues and the browser does not write to disk (https://github.com/Mihir-Choudhary/Whatsapp-Web-Extractor/blob/ce71414c569081b2449b99df50031c96d969c505/scripts/wa_decrypt.py#L1129-L1152; https://github.com/Mihir-Choudhary/Whatsapp-Web-Extractor/blob/ce71414c569081b2449b99df50031c96d969c505/docs/key.md); that was not tested here. Stored Text holds four plain fields WhatsApp keeps outside that column: a document's file name, a contact card's name and a group invite's name and comment. Other plain fields on message records (a base64 JPEG thumbnail on link-preview messages, a video's accessibility label, a group invite code) are not reported. Ack is the ack code named from WhatsApp Web's WAWebAck ACK list. Media SHA-256 is the stored filehash in hex; for a document sent in the sample it equalled the SHA-256 of the original file, so it can be matched against hash sets. Media is the cached file whose SHA-256 is the message's filehash, or else its thumbnailSha256, read from the origin's CacheStorage and kept only when the bytes hash to that value; WhatsApp caches these already decrypted, and only a few files are cached. Last Edited is latestEditSenderTimestampMs read as milliseconds; it is set on the scripted message that was edited, and in Chrome also on the message_edit_encrypted row that records the edit; on no other scripted message. Revoked At is revokeTimestamp read as epoch seconds; the scripted steps did not exercise it (Delete for everyone was not offered). Reactions lists the reactions store's reactionText, sender and timestamp (milliseconds) for the message; the scripted reaction appears on the message it was put on. Starred is Yes when isStarred is true; it is Yes on the scripted starred message and on no other scripted message. Media Size and Media Duration are the stored size and duration values; their units are not established. Reply To Message ID is quotedStanzaID. A message deleted for the account alone left no live record in the sample and is not recovered. Chrome stored the scripted edit as its own message_edit_encrypted row as well; Firefox did not.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/Service Worker/CacheStorage/*/*/*_0',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/cache/caches.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/cache/morgue/*/*.final'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'message-circle',
        'data_views': {
            'conversation': {
                'conversationDiscriminatorColumn': 'Chat ID',
                'conversationLabelColumn': 'Chat',
                'textColumn': 'Stored Text',
                'directionColumn': 'Outgoing',
                'directionSentValue': 1,
                'timeColumn': 'Timestamp',
                'senderColumn': 'Sender',
                'mediaColumn': 'Media',
            }
        },
    },
    'whatsappWebMedia': {
        'name': 'WhatsApp Web - Media',
        'description': 'Media files WhatsApp Web cached in a browser profile, already decrypted, '
                       'each matched to its message by the SHA-256 WhatsApp records for the file or '
                       'its thumbnail: the file, whether it is the full file or a thumbnail, its '
                       'message time, chat and sender, and cached files no stored message names.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. The origin's CacheStorage (Service Worker/CacheStorage in Chromium, storage/default/https+++web.whatsapp.com/cache in Firefox, whose bodies are Snappy-framed files under morgue) holds entries under _media_cache_v2_.whatsapp.com keyed by a SHA-256. An entry is reported only when the SHA-256 of its bytes equals that key; every entry in the sample did, and every one matched a message's filehash (Full file) or thumbnailSha256 (Thumbnail). A file no stored message names would still get a row, marked as such; the sample held none. Only a small part of a profile's media is cached: the rest exists on disk only as hashes (reported in WhatsApp Web - Messages) and media keys (not reported).",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/Service Worker/CacheStorage/*/*/*_0',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/cache/caches.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/cache/morgue/*/*.final'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'image',
    },
    'whatsappWebCalls': {
        'name': 'WhatsApp Web - Calls',
        'description': 'Call log entries WhatsApp Web holds in a browser profile: time, chat, '
                       'direction, caller, voice or video, outcome, duration and participants.',
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-10-19',
        'last_update_date': '2026-10-19',
        'requirements': 'none',
        'category': 'WhatsApp Web',
        'notes': "Read from WhatsApp Web's IndexedDB database model-storage and the localStorage of https://web.whatsapp.com, in a Chromium profile (IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb and Local Storage/leveldb) or a Firefox profile (storage/default/https+++web.whatsapp.com). Each browser profile is read on its own and named in Browser Profile; profiles are never merged. Field meanings come from WhatsApp Web's own code, named by module below where one is established, read from the client bundle the browsers cached on 2026-10-19; that code is minified, and no permalink is given for it. Fields mapped from a private sample: a personal account linked to Chrome 155 and Firefox 158 on macOS 27, with a scripted set of messages, an edit, a reaction, a star, a poll, a pin, two photos, a document and a voice note sent in a recorded time window. Edge, Brave, Opera, WebView2 hosts and Windows and Linux paths are covered by the path patterns but not exercised. One row per message of type call_log. Outcome is the stored callOutcome, one of the names in WhatsApp Web's WAWebCallLogMsgData CallOutcome list. Duration is callDuration in seconds, the unit WAWebClockDurationFormatters formats it in. Caller is callCreator. Call Type is Video when isVideoCall is true and Voice otherwise. Each participant's outcome code is reported as stored; its meaning is not established. Call Link is isCallLink and held No on every row in the sample. No call was placed during the scripted steps, so the call rows were checked for shape, not against a known call.",
        'paths': ('*/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb/*',
                  '*/Local Storage/leveldb/*',
                  '*/storage/default/https+++web.whatsapp.com/idb/*.sqlite*',
                  '*/storage/default/https+++web.whatsapp.com/ls/data.sqlite*'),
        'sample_data': {
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 0 rows (no web.whatsapp.com storage in the image)',
        },
        'output_types': 'standard',
        'artifact_icon': 'phone-call',
    },
}

import base64
import binascii
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, check_in_embedded_media
from scripts.whatsapp_web import jid, media, profiles, records

# WAWebAck ACK: the message state codes WhatsApp Web stores in a message's ack field.
_ACK = {-6: 'Inactive', -5: 'Content unuploadable', -4: 'Content too big', -3: 'Content gone',
        -2: 'Expired', -1: 'Failed', 0: 'Clock', 1: 'Sent', 2: 'Received',
        3: 'Read', 4: 'Played', 5: 'Peer'}


def _when(seconds):
    """Epoch seconds as a UTC datetime, or '' when absent or zero."""
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return ''
    if value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _when_ms(milliseconds):
    try:
        return _when(float(milliseconds) / 1000)
    except (TypeError, ValueError):
        return ''


def _hex_sha256(value):
    """A base64 SHA-256 as stored, as hex; '' when it is not one."""
    if not isinstance(value, str):
        return ''
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return ''
    return raw.hex() if len(raw) == 32 else ''


def _user(wid):
    """'<user>@<server>' without the device part of a device jid ('<user>:<device>@<server>')."""
    if not isinstance(wid, str) or '@' not in wid:
        return ''
    user, server = wid.split('@', 1)
    return f"{user.split(':', 1)[0]}@{server}"


def _key_parts(key):
    """(fromMe, chat id) from a message key string: fromMe, remote, id, then optional parts."""
    if not isinstance(key, str):
        return None, ''
    parts = key.split('_')
    if len(parts) < 3 or parts[0] not in ('true', 'false'):
        return None, ''
    return parts[0] == 'true', parts[1]


def _wid(value):
    """An id as WhatsApp Web's WAWebWidFactory.createWid keys it: @s.whatsapp.net becomes @c.us."""
    return value.replace('@s.whatsapp.net', '@c.us') if isinstance(value, str) else ''


def _yes(value):
    return 'Yes' if value else ''


def _bool(value):
    if value is None or value == '':
        return ''
    return 'Yes' if value else 'No'


class _People:
    """Names for WhatsApp ids, from one profile's own contact and group records."""

    def __init__(self, profile):
        self.contacts = {_wid(c.get('id')): c for c in records(profile, 'contact') if c.get('id')}
        self.groups = {g.get('id'): g for g in records(profile, 'group-metadata') if g.get('id')}
        self.chats = {c.get('id'): c for c in records(profile, 'chat') if c.get('id')}
        ls = profile.local_storage
        self.me_pn = _user(_json(ls.get('last-wid-md')))
        self.me_lid = _user(_json(ls.get('WALid')))
        self.me = {x for x in (self.me_pn, self.me_lid) if x}
        # A LID contact record carries the matching phone number.
        self.pn_of = {cid: _wid(c.get('phoneNumber')) for cid, c in self.contacts.items()
                      if isinstance(c.get('phoneNumber'), str)}
        self.lid_of = {pn: cid for cid, pn in self.pn_of.items()}

    def name(self, wid):
        if not wid:
            return ''
        wid = _wid(wid)
        if wid in self.groups and isinstance(self.groups[wid].get('subject'), str):
            return self.groups[wid]['subject']
        for candidate in (wid, self.pn_of.get(wid), self.lid_of.get(wid)):
            contact = self.contacts.get(candidate) or {}
            for field in ('name', 'shortName', 'pushname'):
                if isinstance(contact.get(field), str) and contact.get(field):
                    return contact[field]
        chat = self.chats.get(wid) or {}
        if isinstance(chat.get('name'), str) and chat.get('name'):
            return chat['name']
        return self.phone(wid) or wid

    def phone(self, wid):
        wid = _wid(wid)
        pn = wid if isinstance(wid, str) and wid.endswith('@c.us') else self.pn_of.get(wid, '')
        return pn.split('@', 1)[0] if pn else ''

    def label(self, wid):
        name = self.name(wid)
        return f'{name} (me)' if _wid(wid) in self.me else name


def _json(value):
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return value


def _profile_label(context, profile):
    return context.get_relative_path(profile.profile_dir)


def _sources(context, found):
    return '\n'.join(context.get_relative_path(path) for p in found for path in p.sources)


def _chat_kind(wid):
    server = wid.rsplit('@', 1)[-1] if isinstance(wid, str) and '@' in wid else ''
    return {'c.us': 'Individual', 's.whatsapp.net': 'Individual', 'lid': 'Individual', 'g.us': 'Group',
            'newsletter': 'Channel', 'broadcast': 'Broadcast'}.get(server, server)


@artifact_processor
def whatsappWebAccount(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        messages = records(profile, 'message')
        times = sorted(t for t in (m.get('t') for m in messages) if isinstance(t, (int, float)) and t > 0)
        device_pn = _json(profile.local_storage.get('last-wid-md'))
        device_lid = _json(profile.local_storage.get('WALid'))
        me_contact = people.contacts.get(people.me_pn) or people.contacts.get(people.me_lid) or {}
        rows.append((
            _when(times[0]) if times else '',
            _when(times[-1]) if times else '',
            people.phone(people.me_pn),
            device_pn if isinstance(device_pn, str) else '',
            device_lid if isinstance(device_lid, str) else '',
            me_contact.get('pushname') if isinstance(me_contact.get('pushname'), str) else '',
            len(messages),
            len(records(profile, 'chat')),
            len(records(profile, 'contact')),
            profile.kind,
            _profile_label(context, profile),
        ))
    headers = (('Earliest Message', 'datetime'), ('Latest Message', 'datetime'), 'Phone Number',
               'Device ID (phone number)', 'Device ID (LID)', 'Push Name', 'Messages', 'Chats',
               'Contacts', 'Browser', 'Browser Profile')
    return headers, rows, _sources(context, found)


@artifact_processor
def whatsappWebContacts(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        blocked = {_wid(b.get('id')) for b in records(profile, 'blocklist')}
        for cid, c in sorted(people.contacts.items()):
            text = lambda f, c=c: c.get(f) if isinstance(c.get(f), str) else ''  # noqa: E731
            book = c.get('isAddressBookContact')
            rows.append((
                c.get('id'),
                people.phone(cid),
                text('name'),
                text('shortName'),
                text('pushname'),
                text('username'),
                text('textStatusString'),
                '' if book is None else ('Yes' if book else 'No'),
                'Yes' if cid in blocked or _wid(c.get('phoneNumber')) in blocked else '',
                text('type'),
                _profile_label(context, profile),
            ))
    headers = ('WhatsApp ID', 'Phone Number', 'Name', 'Short Name', 'Push Name', 'Username',
               'About', 'In Address Book', 'Blocked', 'Type (as stored)', 'Browser Profile')
    return headers, rows, _sources(context, found)


@artifact_processor
def whatsappWebChats(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        latest, count = {}, defaultdict(int)
        for m in records(profile, 'message'):
            _from_me, chat = _key_parts(m.get('id'))
            t = m.get('t')
            if chat:
                count[chat] += 1
                if isinstance(t, (int, float)) and t > latest.get(chat, 0):
                    latest[chat] = t
        for cid, c in sorted(people.chats.items()):
            rows.append((
                _when(latest.get(cid)),
                _when_ms(c.get('pin')),
                cid,
                people.label(cid),
                _chat_kind(cid),
                count.get(cid, 0),
                c.get('unreadCount', ''),
                _bool(c.get('archive')),
                c.get('muteExpiration', ''),
                _bool(c.get('isLocked')),
                _profile_label(context, profile),
            ))
    headers = (('Latest Stored Message', 'datetime'), ('Pinned At', 'datetime'), 'Chat ID', 'Chat',
               'Kind', 'Stored Messages', 'Unread', 'Archived', 'Mute Expiration (as stored)',
               'Locked', 'Browser Profile')
    return headers, rows, _sources(context, found)


def _names(people, ids):
    return '\n'.join(f'{people.label(i)} [{i}]' for i in ids if isinstance(i, str))


@artifact_processor
def whatsappWebGroups(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        members = {p.get('groupId'): p for p in records(profile, 'participant') if p.get('groupId')}

        for gid, g in sorted(people.groups.items()):
            p = members.get(gid, {})
            past = []
            for item in p.get('pastParticipants') or []:
                if isinstance(item, dict):
                    left = _when(item.get('leaveTs'))
                    past.append(f"{people.label(item.get('jid'))} [{item.get('jid')}]: "
                                f"{item.get('leaveReason', '')}"
                                f"{' at ' + left.strftime('%Y-%m-%d %H:%M:%S UTC') if left else ''}")
            current = p.get('participants') or []
            rows.append((
                _when(g.get('creation')),
                _when(g.get('subjectTime')),
                _when(g.get('descTime')),
                gid,
                g.get('subject') if isinstance(g.get('subject'), str) else '',
                people.label(g.get('owner')) if g.get('owner') else '',
                g.get('desc') if isinstance(g.get('desc'), str) else '',
                people.label(g.get('descOwner')) if g.get('descOwner') else '',
                len(current),
                _names(people, current),
                _names(people, p.get('admins') or []),
                _names(people, p.get('superAdmins') or []),
                '\n'.join(past),
                _bool(g.get('announce')),
                _bool(g.get('restrict')),
                _profile_label(context, profile),
            ))
    headers = (('Created', 'datetime'), ('Subject Set', 'datetime'), ('Description Set', 'datetime'),
               'Group ID', 'Subject', 'Owner', 'Description', 'Description Set By', 'Members',
               'Member List', 'Admins', 'Super Admins', 'Past Members', 'Only Admins Send',
               'Only Admins Edit Info', 'Browser Profile')
    return headers, rows, _sources(context, found)


def _stored_text(m):
    """Text WhatsApp keeps outside the encrypted column, labelled by the field it came from."""
    out = []
    for field, label in (('filename', 'File name'), ('vcardFormattedName', 'Contact card'),
                         ('inviteGrpName', 'Group invite'), ('comment', 'Invite comment')):
        value = m.get(field)
        if isinstance(value, str) and value:
            out.append(f'{label}: {value}')
    return '\n'.join(out)


def _media_ref(profile, sha, label):
    """The checked-in media reference for a cached file with this SHA-256, or ''."""
    item = media(profile).get(sha) if isinstance(sha, str) else None
    if not item:
        return ''
    path, body = item
    return check_in_embedded_media(path, body, label) or ''


@artifact_processor
def whatsappWebMessages(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        reactions = defaultdict(list)
        for r in records(profile, 'reactions'):
            parent = r.get('parentMsgKey')
            text = r.get('reactionText')
            if isinstance(parent, str) and isinstance(text, str) and text:
                when = _when_ms(r.get('timestamp'))
                reactions[parent].append(
                    f"{text} {people.label(r.get('senderUserJid'))}"
                    f"{' ' + when.strftime('%Y-%m-%d %H:%M:%S UTC') if when else ''}")
        for m in records(profile, 'message'):
            key = m.get('id')
            from_me, chat = _key_parts(key)
            if from_me is None:
                continue
            if from_me:
                sender = people.me_lid if chat.endswith('@lid') and people.me_lid else people.me_pn
            else:
                sender = jid(m.get('author')) or chat
            ack = m.get('ack')
            ack_text = ''
            if isinstance(ack, (int, float)):
                ack_text = _ACK.get(int(ack), str(int(ack)))
            width, height = m.get('width'), m.get('height')
            rows.append((
                _when(m.get('t')),
                _when_ms(m.get('latestEditSenderTimestampMs')),
                _when(m.get('revokeTimestamp')),
                people.label(chat),
                1 if from_me else 0,
                people.label(sender),
                m.get('type', ''),
                _stored_text(m),
                'Encrypted' if m.get('msgRowOpaqueData') else '',
                ack_text,
                m.get('mimetype', '') if isinstance(m.get('mimetype'), str) else '',
                m.get('size', '') if isinstance(m.get('size'), (int, float)) else '',
                m.get('duration', '') if m.get('duration') is not None else '',
                f'{int(width)}x{int(height)}' if isinstance(width, (int, float)) and isinstance(height, (int, float)) else '',
                _hex_sha256(m.get('filehash')),
                _media_ref(profile, m.get('filehash'), key) or _media_ref(profile, m.get('thumbnailSha256'), key),
                m.get('quotedStanzaID', '') if isinstance(m.get('quotedStanzaID'), str) else '',
                '\n'.join(reactions.get(key, [])),
                _yes(m.get('isStarred')),
                _yes(m.get('isForwarded')),
                _yes(m.get('isViewOnce')),
                chat,
                sender,
                key,
                _profile_label(context, profile),
            ))
    rows.sort(key=lambda r: (r[0] if isinstance(r[0], datetime) else datetime.min.replace(tzinfo=timezone.utc)))
    headers = (('Timestamp', 'datetime'), ('Last Edited', 'datetime'), ('Revoked At', 'datetime'),
               'Chat', 'Outgoing', 'Sender', 'Type', 'Stored Text', 'Message Body', 'Ack',
               'Media Type', 'Media Size (as stored)', 'Media Duration (as stored)', 'Media Dimensions', 'Media SHA-256',
               ('Media', 'media'), 'Reply To Message ID', 'Reactions', 'Starred', 'Forwarded', 'View Once', 'Chat ID',
               'Sender ID', 'Message Key', 'Browser Profile')
    return headers, rows, _sources(context, found)


@artifact_processor
def whatsappWebMedia(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        by_hash = {}
        for m in records(profile, 'message'):
            for field, kind in (('filehash', 'Full file'), ('thumbnailSha256', 'Thumbnail')):
                if isinstance(m.get(field), str):
                    by_hash.setdefault(m[field], (m, kind))
        for sha, (path, body) in sorted(media(profile).items()):
            m, kind = by_hash.get(sha, ({}, ''))
            from_me, chat = _key_parts(m.get('id'))
            if from_me:
                sender = people.me_lid if chat.endswith('@lid') and people.me_lid else people.me_pn
            else:
                sender = jid(m.get('author')) or chat
            rows.append((
                _when(m.get('t')),
                check_in_embedded_media(path, body, m.get('id') or sha) or '',
                kind or 'No stored message names this file',
                people.label(chat) if chat else '',
                people.label(sender) if m else '',
                m.get('type', ''),
                m.get('mimetype', '') if isinstance(m.get('mimetype'), str) else '',
                len(body),
                hashlib.sha256(body).hexdigest(),
                m.get('id', ''),
                context.get_relative_path(path),
                _profile_label(context, profile),
            ))
    rows.sort(key=lambda r: (r[0] if isinstance(r[0], datetime) else datetime.min.replace(tzinfo=timezone.utc)))
    headers = (('Message Timestamp', 'datetime'), ('Media', 'media'), 'Cached As', 'Chat', 'Sender',
               'Message Type', 'Message Media Type', 'Cached Size', 'Cached SHA-256', 'Message Key',
               'Cache Entry', 'Browser Profile')
    return headers, rows, _sources(context, found)


@artifact_processor
def whatsappWebCalls(context):
    found = profiles(context)
    rows = []
    for profile in found:
        people = _People(profile)
        for m in records(profile, 'message'):
            if m.get('type') != 'call_log':
                continue
            from_me, chat = _key_parts(m.get('id'))
            creator = jid(m.get('callCreator'))
            participants = []
            for item in m.get('callParticipants') or []:
                if isinstance(item, dict):
                    who = jid(item.get('participant'))
                    participants.append(f"{people.label(who)} [{who}] (outcome code {item.get('outcome')})")
            duration = m.get('callDuration')
            rows.append((
                _when(m.get('t')),
                people.label(chat),
                '' if from_me is None else (1 if from_me else 0),
                people.label(creator) if creator else '',
                'Video' if m.get('isVideoCall') else 'Voice',
                m.get('callOutcome', '') if isinstance(m.get('callOutcome'), str) else '',
                int(duration) if isinstance(duration, (int, float)) else '',
                '\n'.join(participants),
                _bool(m.get('isCallLink')),
                chat,
                creator,
                m.get('id', ''),
                _profile_label(context, profile),
            ))
    rows.sort(key=lambda r: (r[0] if isinstance(r[0], datetime) else datetime.min.replace(tzinfo=timezone.utc)))
    headers = (('Timestamp', 'datetime'), 'Chat', 'Outgoing', 'Caller', 'Call Type', 'Outcome',
               'Duration (seconds)', 'Participants', 'Call Link', 'Chat ID', 'Caller ID',
               'Message Key', 'Browser Profile')
    return headers, rows, _sources(context, found)
