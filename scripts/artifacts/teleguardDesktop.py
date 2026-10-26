"""TeleGuard Windows messages, chat summaries, contacts and local media.

Author: @ForensikITGmbH.
"""
import collections
import os
import sqlite3
from functools import partial

from scripts import teleguard_desktop as tg
from scripts.filetype import guess as guess_type
from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media,
                               check_in_media, logfunc)

__artifacts_v2__ = {
    'teleguardMessages': {
        'name': 'TeleGuard Windows Messages',
        'description': 'Stored TeleGuard Windows message records with source-scoped conversations, text, timestamps, state fields and local attachment references.',
        'author': '@ForensikITGmbH',
        'creation_date': '2026-10-23', 'last_update_date': '2026-10-26',
        'requirements': 'none', 'category': 'TeleGuard Windows',
        'notes': 'Times are Unix milliseconds in UTC; zero is the epoch and null or invalid values are '
                 'blank. Direction compares sender with the unique service user serverId; missing ids leave '
                 'it blank. Conversation ID includes Source File. Localized Message prefers de, en, then the '
                 'first string; raw content and metadata are retained. Media resolves only within this '
                 "database's tree; unresolved references remain in Media Status. State codes and Media "
                 'Durations remain as stored; duration units are unverified. Media Durations is blank when '
                 'absent. No decryption, deleted-record '
                 'recovery, teleguard_temp.db drafts, channels, posts, SIP-call tables or app logs. '
                 'In the 4.0.6.2 sample, Call Participants and Parent Message ID were empty.',
        'paths': ('*/[Tt]eleguard_database.db*', '*/[Tt]eleguard_desktop/*', '*/[Tt]eleGuard/*'),
        'output_types': 'standard', 'artifact_icon': 'comments',
        'sample_data': {'teleguard_windows_private_01': 'TeleGuard Windows 4.0.6.2 | 64822 rows'},
        'data_views': {'conversation': {
            'conversationDiscriminatorColumn': 'Conversation ID',
            'conversationLabelColumn': 'Conversation', 'textColumn': 'Message',
            'senderColumn': 'Sender', 'directionColumn': 'Direction',
            'directionSentValue': 'Outgoing', 'timeColumn': 'Timestamp', 'mediaColumn': 'Media'}},
    },
    'teleguardChatOverview': {
        'name': 'TeleGuard Windows Chat Overview',
        'description': 'Per-source summaries of stored TeleGuard conversations with message counts, direction counts, distinct authors and first and last valid message times.',
        'author': '@ForensikITGmbH',
        'creation_date': '2026-10-23', 'last_update_date': '2026-10-26',
        'requirements': 'none', 'category': 'TeleGuard Windows',
        'notes': 'One row per stored chatId per database. First Message and Last Message use the minimum and '
                 'maximum valid createDate (Unix milliseconds, UTC). Direction counts compare sender with '
                 'the unique service user serverId; missing ids count as Direction Unknown. Participants '
                 'counts distinct nonempty sender ids, not group membership. Messages By Type and Chat Type '
                 'retain stored codes. Conversation ID includes Source File. Counts cover parsed records '
                 'only.',
        'paths': ('*/[Tt]eleguard_database.db*', '*/[Tt]eleguard_desktop/*', '*/[Tt]eleGuard/*'),
        'output_types': 'standard', 'artifact_icon': 'comments',
        'sample_data': {'teleguard_windows_private_01': 'TeleGuard Windows 4.0.6.2 | 198 rows'},
    },
    'teleguardContacts': {
        'name': 'TeleGuard Windows Contacts',
        'description': 'Stored TeleGuard contact records with ids, display names, embedded avatars, recorded activity fields and message-reference counts.',
        'author': '@ForensikITGmbH',
        'creation_date': '2026-10-23', 'last_update_date': '2026-10-26',
        'requirements': 'none', 'category': 'TeleGuard Windows',
        'notes': 'Last Activity and Last Visit are stored Unix milliseconds in UTC; their application '
                 'meaning is unverified. Null or invalid times are blank; zero is the epoch. The three '
                 'message counts count chatId, sender and receiver references in this database. Avatar uses '
                 'the stored blob, typed by signature. Contact Type, Options and Info remain as stored. '
                 'Source File identifies the database. Account keys are not reported. '
                 'Personal ID was empty in the 4.0.6.2 sample.',
        'paths': ('*/[Tt]eleguard_database.db*', '*/[Tt]eleguard_desktop/*', '*/[Tt]eleGuard/*'),
        'output_types': 'standard', 'artifact_icon': 'user',
        'sample_data': {'teleguard_windows_private_01': 'TeleGuard Windows 4.0.6.2 | 200 rows'},
    },
    'teleguardMediaReferences': {
        'name': 'TeleGuard Windows Media References',
        'description': 'Attachment references stored in TeleGuard message metadata, with parent-message context and explicit local-file resolution status.',
        'author': '@ForensikITGmbH',
        'creation_date': '2026-10-23', 'last_update_date': '2026-10-26',
        'requirements': 'none', 'category': 'TeleGuard Windows',
        'notes': 'One row per mediaFiles entry or additional files id-to-name entry. Resolution uses only '
                 "this database's tree. Reference Status distinguishes Matched, Missing, Ambiguous, Invalid "
                 'reference and Unreadable; unresolved Media is blank and the reference is retained. '
                 'Timestamp is the parent createDate (Unix milliseconds, UTC). Duration, Aspect Ratio and '
                 'Order remain as stored; units are unverified. Duration is blank when absent. '
                 'Cache Name and Thumbnail Cache Name are identical when the stored names are the same. '
                 'Conversation ID includes Source File. Files '
                 "outside the database's tree are not joined. In the 4.0.6.2 sample, "
                 'Reference Field was uniform (mediaFiles) and Reference Status was uniformly Missing.',
        'paths': ('*/[Tt]eleguard_database.db*', '*/[Tt]eleguard_desktop/*', '*/[Tt]eleGuard/*'),
        'output_types': 'standard', 'artifact_icon': 'image',
        'sample_data': {'teleguard_windows_private_01': 'TeleGuard Windows 4.0.6.2 | 1394 rows'},
    },
    'teleguardMediaFiles': {
        'name': 'TeleGuard Windows Media Files',
        'description': 'Local files referenced by TeleGuard messages and recognized unreferenced images, audio, video or PDF files within each database instance.',
        'author': '@ForensikITGmbH',
        'creation_date': '2026-10-23', 'last_update_date': '2026-10-26',
        'requirements': 'none', 'category': 'TeleGuard Windows',
        'notes': "Files come only from this database's tree, excluding databases, sidecars and logs. Named "
                 'files are included regardless of type; unreferenced files require an image, audio, video '
                 'or PDF signature. Stored Name References counts metadata references to the basename; '
                 'Ambiguous references indicates multiple local candidates, not a resolved join. Database '
                 'Source identifies the database; Source File identifies the file. Database Source is '
                 'constant for a single database. Unreadable Media is '
                 'blank. File presence does not establish viewing. No timestamp is inferred or added to the '
                 'timeline.',
        'paths': ('*/[Tt]eleguard_database.db*', '*/[Tt]eleguard_desktop/*', '*/[Tt]eleGuard/*'),
        'output_types': ['html', 'tsv', 'lava'], 'artifact_icon': 'photo',
        'sample_data': {'teleguard_windows_private_01': 'TeleGuard Windows 4.0.6.2 | 1 row'},
    },
}


def _file_type(path):
    try:
        with open(path, 'rb') as handle:
            kind = guess_type(handle.read(8192))
    except OSError as exc:
        logfunc(f'TeleGuard: a staged attachment could not be read: {exc}')
        return None
    return kind


def check_media_file(path, name):
    """Register a file through the real helper, using its bytes for type/extension."""
    if not path:
        return None
    kind = _file_type(path)
    return check_in_media(path, name=name, force_type=kind.mime if kind else None,
                          force_extension=kind.extension if kind else None)


def embedded_media(source_file, data, label):
    if not isinstance(data, (bytes, bytearray)) or not data:
        return None
    kind = guess_type(bytes(data[:8192]))
    if kind is None:
        logfunc(f'{label}: an avatar blob has no recognized type; not shown')
        return None
    return check_in_embedded_media(source_file, data, name=f'embedded.{kind.extension}',
                                   force_type=kind.mime, force_extension=kind.extension)


def _collect(context, label, reader, required=('messages',)):
    rows, sources = [], []
    for path, relative in tg.databases(context):
        sources.append(path)
        db = tg.open_db(path, label, required)
        if db is None:
            continue
        try:
            store_rows = list(reader(db, path, relative))
        except sqlite3.Error as exc:
            logfunc(f'{label}: {relative} could not be parsed: {exc}')
        else:
            rows.extend(store_rows)
        finally:
            db.close()
    return rows, '\n'.join(sources)


def _references(index, entries, checked):
    refs, statuses = [], collections.Counter()
    for entry in entries:
        name = entry.get('name')
        path, status = tg.resolve_media(index, name)
        if path:
            if path not in checked:
                checked[path] = check_media_file(path, name)
            if checked[path]:
                refs.append(checked[path])
            else:
                status = 'Unreadable'
        statuses[status] += 1
    status_text = '; '.join(f'{key}: {value}' for key, value in sorted(statuses.items()))
    return refs or None, status_text or None


def _message_records(context, db, path, relative):
    index = tg.media_index(context, path)
    local_id, local_alias = tg.local_account(db)
    labels, checked = tg.contact_labels(db), {}
    for row in tg.message_rows(db):
        metadata = row['metadata_json']
        entries = tg.attachment_entries(metadata)
        media, status = _references(index, entries, checked)
        forward = metadata.get('forward')
        forward = forward if isinstance(forward, dict) else {}
        yield (
            tg.utc(row['createDate']), tg.utc(row['userTime']), tg.utc(forward.get('originDate')),
            tg.direction(row['sender'], local_id),
            tg.display_name(row['sender'], labels, local_id, local_alias),
            tg.display_name(row['chatId'], labels, local_id, local_alias),
            tg.localized_text(row['content'], metadata), media,
            ' | '.join(tg.media_names(metadata)) or None, status,
            tg.conversation_id(relative, row['chatId']), row['id'], row['type'],
            tg.display_name(row['receiver'], labels, local_id, local_alias),
            metadata.get('mediaType'),
            ' | '.join(str(entry['duration']) for entry in entries
                       if entry.get('duration') is not None) or None,
            metadata.get('quote'), metadata.get('messageId'), metadata.get('quotedMessageType'),
            tg.display_name(metadata.get('author'), labels, local_id, local_alias),
            metadata.get('replyType'), metadata.get('callType'), metadata.get('membersText'),
            metadata.get('isSuccessfull'), row['status'], row['isEdited'],
            metadata.get('isContentExpired'), metadata.get('client-version'), row['parentId'],
            row['content'], row['metadata'], row['sender'], row['receiver'], row['chatId'], relative)


@artifact_processor
def teleguardMessages(context):
    data_headers = (('Timestamp', 'datetime'), ('Client Time', 'datetime'),
                    ('Forwarded Time', 'datetime'), 'Direction', 'Sender', 'Conversation',
                    'Message', ('Media', 'media'), 'Media File Names', 'Media Status',
                    'Conversation ID', 'Message ID', 'Message Type', 'Recipient', 'Media Type',
                    'Media Durations', 'Quoted Text', 'Quoted Message ID', 'Quoted Message Type',
                    'Quote Author', 'Reply Type', 'Call Type', 'Call Participants',
                    'Call Result (as stored)', 'Status (as stored)', 'Edited (as stored)',
                    'Content Expired (as stored)', 'Client Version', 'Parent Message ID',
                    'Content (as stored)', 'Metadata (as stored)', 'Sender ID', 'Recipient ID', 'Chat ID', 'Source File')
    rows, sources = _collect(context, 'TeleGuard Messages', partial(_message_records, context))
    return data_headers, rows, sources


def _chat_records(db, _path, relative):
    local_id, local_alias = tg.local_account(db)
    labels, types, chats = tg.contact_labels(db), tg.contact_types(db), {}
    for row in tg.message_rows(db):
        chat = chats.setdefault(row['chatId'], {'total': 0, 'out': 0, 'in': 0, 'unknown': 0,
                                             'authors': set(), 'first': None, 'last': None,
                                             'types': collections.Counter()})
        chat['total'] += 1
        resolved = tg.direction(row['sender'], local_id)
        chat[{'Outgoing': 'out', 'Incoming': 'in'}.get(resolved, 'unknown')] += 1
        if row['sender']:
            chat['authors'].add(row['sender'])
        chat['types'][row['type']] += 1
        created = tg.utc(row['createDate'])
        if created:
            chat['first'] = min(chat['first'], created) if chat['first'] else created
            chat['last'] = max(chat['last'], created) if chat['last'] else created
    for chat_id, counts in sorted(chats.items(), key=lambda item: str(item[0])):
        yield (counts['first'], counts['last'],
               tg.display_name(chat_id, labels, local_id, local_alias),
               tg.conversation_id(relative, chat_id), chat_id, types.get(chat_id), counts['total'],
               counts['out'], counts['in'], counts['unknown'], len(counts['authors']),
               ', '.join(f'{name}: {count}' for name, count in
                         sorted(counts['types'].items(), key=lambda item: str(item[0]))), relative)


@artifact_processor
def teleguardChatOverview(context):
    data_headers = (('First Message', 'datetime'), ('Last Message', 'datetime'), 'Conversation',
                    'Conversation ID', 'Chat ID', 'Chat Type', 'Messages Total', 'Outgoing',
                    'Incoming', 'Direction Unknown', 'Participants', 'Messages By Type', 'Source File')
    rows, sources = _collect(context, 'TeleGuard Chat Overview', _chat_records)
    return data_headers, rows, sources


def _contact_records(db, path, relative):
    counts = tg.reference_counts(db)
    for row in tg.select(db, 'contacts', ('serverId', 'alias', 'type', 'personalId', 'avatar',
                                        'lastActivityTime', 'lastVisitTime', 'options', 'info'),
                         'ORDER BY serverId'):
        chat_count, sent, received = counts.get(row['serverId'], (0, 0, 0))
        yield (tg.utc(row['lastActivityTime']), tg.utc(row['lastVisitTime']),
               embedded_media(path, row['avatar'], 'TeleGuard Contacts'), row['serverId'],
               row['alias'], row['type'], row['personalId'], chat_count, sent, received,
               row['options'], row['info'], relative)


@artifact_processor
def teleguardContacts(context):
    data_headers = (('Last Activity', 'datetime'), ('Last Visit', 'datetime'), ('Avatar', 'media'),
                    'Contact ID', 'Display Name', 'Contact Type', 'Personal ID',
                    'Messages In This Chat', 'Messages Sent', 'Messages Received',
                    'Options (as stored)', 'Info (as stored)', 'Source File')
    rows, sources = _collect(context, 'TeleGuard Contacts', _contact_records, ('contacts',))
    return data_headers, rows, sources


def _media_reference_records(context, db, path, relative):
    index = tg.media_index(context, path)
    local_id, local_alias = tg.local_account(db)
    labels, checked = tg.contact_labels(db), {}
    for row in tg.message_rows(db):
        for entry in tg.attachment_entries(row['metadata_json']):
            name = entry.get('name')
            candidate, status = tg.resolve_media(index, name)
            media = None
            if candidate:
                if candidate not in checked:
                    checked[candidate] = check_media_file(candidate, name)
                media = checked[candidate]
                if not media:
                    status = 'Unreadable'
            yield (tg.utc(row['createDate']), tg.direction(row['sender'], local_id),
                   tg.display_name(row['sender'], labels, local_id, local_alias),
                   tg.display_name(row['chatId'], labels, local_id, local_alias), media, name,
                   entry.get('id'), entry.get('mediaType'), entry.get('duration'),
                   entry.get('aspectRatio'), entry.get('blurHash'), entry.get('cacheName'),
                   entry.get('thumbnailCacheName'), entry.get('order'), row['id'],
                   tg.conversation_id(relative, row['chatId']), entry['reference_field'], status, relative)


@artifact_processor
def teleguardMediaReferences(context):
    data_headers = (('Timestamp', 'datetime'), 'Direction', 'Sender', 'Conversation', ('Media', 'media'),
                    'Media File Name', 'Media ID', 'Media Type', 'Duration (as stored)',
                    'Aspect Ratio (as stored)', 'Blur Hash (as stored)', 'Cache Name',
                    'Thumbnail Cache Name', 'Order (as stored)', 'Message ID', 'Conversation ID',
                    'Reference Field', 'Reference Status', 'Source File')
    rows, sources = _collect(context, 'TeleGuard Media References', partial(_media_reference_records, context))
    return data_headers, rows, sources


def _media_file_records(context, db, path, relative):
    index = tg.media_index(context, path)
    references = collections.Counter(name.casefold() for row in tg.message_rows(db)
                                      for name in tg.media_names(row['metadata_json']))
    for name, candidates in sorted(index.items()):
        count = references[name]
        for candidate in candidates:
            kind = _file_type(candidate)
            recognized = kind and (kind.mime.startswith(('image/', 'audio/', 'video/'))
                                   or kind.mime == 'application/pdf')
            if not count and not recognized:
                continue
            status = 'Ambiguous references' if count and len(candidates) > 1 else (
                'Referenced' if count else 'Unreferenced')
            yield (check_media_file(candidate, os.path.basename(candidate)), os.path.basename(candidate),
                   kind.mime if kind else None, count, status, relative,
                   context.get_relative_path(candidate).replace('\\', '/'))


@artifact_processor
def teleguardMediaFiles(context):
    data_headers = (('Media', 'media'), 'File Name', 'MIME Type', 'Stored Name References',
                    'Reference Status', 'Database Source', 'Source File')
    rows, sources = _collect(context, 'TeleGuard Media Files', partial(_media_file_records, context))
    return data_headers, rows, sources
