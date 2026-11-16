"""Siri app conversation history from a macOS AgentSessionStore.sqlite database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSiriAgentSessions": {
        "name": "Siri App Conversations",
        "description": "Sessions and events in AgentSessionStore.sqlite under a Daemon Containers folder, one row "
                       "per event with its session's title, summary, creation and last-modified times, agent "
                       "bundle IDs and source bundle ID, and the app-entity attachment rows the store links to the event, or one "
                       "row for a session that has no event. An event whose session record is absent is not "
                       "reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Siri (macOS)",
        "platforms": ("macOS",),
        "notes": 'Reads the Core Data store AgentSessionStore.sqlite in Library/Daemon '
                 'Containers/<UUID>/Data/AgentSessionKit. The path is matched on the AgentSessionKit folder; the '
                 "container's .com.apple.containermanagerd.metadata.plist identifier is not checked. Sources: the "
                 'published description by Yogesh Khatri (Swift Forensics, 15 November 2026), the mac_apt siri.py '
                 'plugin (MIT), and test conversations made for this artifact in the Siri app of a private macOS '
                 '27.2.1 (26B131) system on 16 November 2026, whose counts and values are not published. '
                 'Observations below are from that system. Sentences that say what the artifact does describe its '
                 'code. Every date is read as seconds since 2001-01-01 UTC, and the event and session times of the '
                 'test conversations, read that way, fell inside the minutes between the copies of the store taken '
                 'before and after each step. Role (as stored) is ZROLERAWVALUE: user on the three requests and '
                 "assistant on Siri's events. Each Siri reply wrote two assistant events: one with the reply text "
                 'and the Event Agent com.apple.siri, which carried the reply payload row, and one with no text and '
                 "no agent, which carried the reply's app-entity attachment rows when it had any (an attached file, "
                 'selected text, a window). Every test session held one request. A blank Text is reported blank; '
                 'mac_apt skips assistant events with no text, so its row count can be lower. State (as stored) is '
                 'ZPERSISTABLESTATERAW, reported as stored: it was 0 on the session present after the app was first '
                 'opened and on one later session with no event, and 1 on the four other sessions, three of which '
                 'held a request. The published description reports, without citing an Apple source, that a session '
                 'with state 0 does not show in the app and can be removed later, and shows a state-0 session that '
                 'kept events; that case was not reproduced. Two requests that Siri refused because of a Screen Time '
                 'restriction stored no event. One session with no event had state 1 and no title; its record was '
                 'created about two minutes before the single update the history holds for it, and which refused '
                 'request that update belongs to is not established. A session with no event can therefore stand for '
                 'an exchange whose turns were not stored. Pinned (as stored) is ZISPINNED, 1 on the pinned test '
                 "session. A request made with Ask Siri from another app's contextual menu (TextEdit) was stored as "
                 'its own session whose Source Bundle ID was com.apple.campo, the bundle ID of the Siri app (Siri '
                 'AI.app) on that system, not the app it was asked from; Source Bundle ID held com.apple.campo on '
                 'every row of the test store. That reply carried a SelectedText and a WindowEntity attachment. User '
                 "is the folder after Users in the store's path; User held one value on every row because the test "
                 "run read one store. Attachments lists each attachment row (ZARTIFACTENTITY) linked to the row's "
                 'event that is an app entity: its type name and bundle ID as stored and, for a file, the path its '
                 'bookmark records, read with the bookmark reader the Shared File Lists artifact uses. Those rows '
                 'hold one leading byte (0x01 on every row seen) and then JSON; a row that cannot be read that way '
                 'is listed as not decoded and logged. A short text file attached in the Siri app was stored as an '
                 "attachment row holding a bookmark to the file where it was. The row's owned-file path, file name "
                 "and file size columns were empty and the store's external data folder was empty. The file's text "
                 "was also in the store: in Siri's reply text, in the session summary, and in ZSESSIONRESUMPTIONDATA "
                 "of that session's two assistant events. Other file types and larger files were not tried. That "
                 "attachment was linked to Siri's reply event with no text, not to the request. Attachment File is a "
                 'file the extraction holds at the bookmarked path, matched on that path below any folder (the '
                 'shortest match when there are several). Nothing checks that it is the file as it was when '
                 'attached. When the extraction holds no file there, the column is blank and the path stays in '
                 'Attachments. Not reported, among other columns: the payload rows linked to the reply text event '
                 '(content kind data, a binary property list with a commands list whose entries hold archived data, '
                 'not decoded), the session-level AgentMediaEntity rows (heroMedia in their metadata), seen on the '
                 'test session whose reply showed images, the other ZARTIFACTENTITY columns, ZTITLESOURCE, '
                 'ZTHUMBNAILBACKGROUNDIMAGE, ZSESSIONRESUMPTIONDATA (binary, populated on every event; see the '
                 'attached-file note), ZCONVERSATIONFRAGMENTINDEXCONTENT, the turn ID columns, ZINTERNALSESSIONID, '
                 'ZEXTERNALPROVIDER, the sensitivity and safety-state columns and table, the sync tables '
                 '(ZCLOUDKITSYNCENGINESTATEENTITY and the four other sync entity tables), '
                 'ZCASCADEDONATIONSTATEENTITY, and the persistent-history tables (ACHANGE, ATRANSACTION, '
                 'ATRANSACTIONSTRING). Deleting a conversation in the app removed its session, event and attachment '
                 'rows, so a deleted conversation is not reported here; the persistent history kept tombstones '
                 "holding the deleted session's and events' IDs with the time of the delete. In a copy taken within "
                 'about a minute of the delete, text from the deleted conversation was still in the database file '
                 'and in its -wal file. The delete was only in the -wal at that point: the database file read '
                 "without it still held the conversation's rows. How long either lasts was not measured. A -wal file "
                 'staged beside the database is opened with it. Not exercised: requests from the search bar (Command '
                 '+ Space), spoken requests, sessions with more than one request, an external provider, attachments '
                 'other than a short text file, and retention expiry. Whether iOS or iPadOS 27 carries the same '
                 'store is not established.',
        "paths": ("*/Library/Daemon Containers/*/Data/AgentSessionKit/AgentSessionStore.sqlite*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Session ID",
                "conversationLabelColumn": "Title",
                "textColumn": "Text",
                "timeColumn": "Event Created (UTC)",
                "directionColumn": "Role (as stored)",
                "directionSentValue": "user",
                "mediaColumn": "Attachment File",
            }
        },
    },
    "macosSiriAgentAttachments": {
        "name": "Siri App Attachments",
        "description": "App-entity attachment rows in AgentSessionStore.sqlite under a Daemon Containers folder, with "
                       "the path from an attached file's bookmark, the file when the extraction holds it, and the "
                       "session and event each row is linked to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-16",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Siri (macOS)",
        "platforms": ("macOS",),
        "notes": 'Reads ZARTIFACTENTITY in the Core Data store AgentSessionStore.sqlite in Library/Daemon '
                 'Containers/<UUID>/Data/AgentSessionKit, the store the Siri App Conversations artifact reads; see '
                 'its notes for the sources and the private macOS 27.2.1 (26B131) system whose test conversations of '
                 '16 November 2026 were used, whose counts and values are not published. One row per attachment row '
                 'that is an app entity, including rows linked to a session and to no event. Rows whose JSON has no '
                 'persistableAppEntity key are not reported; on that system those were the rows with content kind '
                 'data, each a binary property list with a commands list whose entries hold archived data, not '
                 "decoded. Each row's data is one leading byte (0x01 on every row seen) and then JSON. Created is "
                 'ZCREATEDAT read as seconds since 2001-01-01 UTC. On that system a row linked to an event was '
                 'created within 10 milliseconds after that event, the Siri reply event with no text, and about two '
                 'seconds after the request; the rows linked to no event were created within a second after their '
                 "session's reply. Type and Bundle ID are the entity's type name and bundle identifier as stored. "
                 'Types seen: AttachmentFileEntity (com.apple.campo) for a file attached in the Siri app, '
                 'SelectedText and WindowEntity (com.apple.intelligenceflow) for text sent with Ask Siri from '
                 "another app's contextual menu, and AgentMediaEntity (com.apple.CampoServices) on the session whose "
                 "reply showed images. File Path and Volume Name come from the file entity's bookmark, read with the "
                 'bookmark reader the Shared File Lists artifact uses. Attachment File is a file the extraction '
                 'holds at the bookmarked path, matched on that path below any folder (the shortest match when there '
                 "are several); nothing checks that it is the file as it was when attached. The row's owned-file "
                 "path, file name and file size columns were empty; the file's text was elsewhere in the store (see "
                 "the Siri App Conversations notes). Identifier is the entity's instance identifier as stored, for "
                 'entities with no readable bookmark; its meaning per type is not established. A row that cannot be '
                 'read as one leading byte and JSON, or whose entity lacks the expected keys, is reported with the '
                 "type 'attachment row not decoded' and logged; no such row was seen on that system. User is the "
                 "folder after Users in the store's path; User held one value on every row because the test run read "
                 'one store. Deleting a conversation in the app removed its attachment rows. The persistent history '
                 'recorded delete changes for attachment rows with an empty ZTOMBSTONE0, so it kept no ID for them; '
                 'such delete changes were also present before any conversation was deleted, so they do not mark a '
                 'delete made in the app. Not exercised: attached files other than one short text file, photos '
                 'included.',
        "paths": ("*/Library/Daemon Containers/*/Data/AgentSessionKit/AgentSessionStore.sqlite*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "paperclip",
    },
    "macosSiriAgentDeletions": {
        "name": "Siri App Deleted Conversations",
        "description": "Session and event deletes recorded in the persistent history of AgentSessionStore.sqlite "
                       "under a Daemon Containers folder, one row per transaction, with the time and the IDs the "
                       "history kept for the deleted rows.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-16",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Siri (macOS)",
        "platforms": ("macOS",),
        "notes": 'Reads the persistent-history tables (ACHANGE and ATRANSACTION) of the Core Data store '
                 'AgentSessionStore.sqlite in Library/Daemon Containers/<UUID>/Data/AgentSessionKit, the store the '
                 'Siri App Conversations artifact reads; see its notes for the sources and the private macOS 27.2.1 '
                 '(26B131) system whose test conversations of 16 November 2026 were used, whose counts and values '
                 'are not published. One row per history transaction that holds a delete change (ZCHANGETYPE 2, the '
                 "delete value of Core Data's NSPersistentHistoryChangeType) of a session or an event. A row shows "
                 'that a session or event record was deleted; it does not show what deleted it. The entity numbers '
                 "are read from the store's Z_PRIMARYKEY table by entity name. Session IDs and Event IDs are the "
                 'ZTOMBSTONE0 values of those changes. On that system each conversation deleted in the app was one '
                 'transaction, each tombstone equalled the ZSESSIONID or ZEVENTID the deleted row had held, and '
                 'Deleted At (ZTIMESTAMP of the transaction, read as seconds since 2001-01-01 UTC) fell inside the '
                 'minute noted for each delete. Events Deleted counts the event deletes in the same transaction; '
                 'which deleted session each deleted event belonged to is not recorded here when a transaction '
                 'deletes more than one session, which was not seen on that system. On that system the deleted '
                 'session that held no event has a row with Events Deleted 0 and no Event IDs. On that system these '
                 'tables held only the ID for a deleted session or event, not its text, title or attachments. The '
                 "transactions' bundle ID and process held one value each on that system, and their author was "
                 "empty; none is reported. User is the folder after Users in the store's path; User held one value "
                 'on every row because the test run read one store. Core Data can prune persistent history, so a '
                 "store without a delete row does not show that nothing was deleted; when and whether this store's "
                 'history is pruned was not measured. Not exercised: deletes made by a retention setting and deletes '
                 'made on another device.',
        "paths": ("*/Library/Daemon Containers/*/Data/AgentSessionKit/AgentSessionStore.sqlite*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "trash-2",
    },
}

import base64
import json
import os

from scripts.ilapfuncs import (artifact_processor, check_in_media, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import (bookmark_fields, fold_view_rows, mac_absolute_utc, unique_sources,
                                  user_from_path)

_LABEL = 'Siri App Conversations'
_STORE = 'AgentSessionStore.sqlite'
_ARTIFACTS = 'ZARTIFACTENTITY'

# (alias, table, column): the columns read. A column the store lacks is selected as NULL, except the
# keys of the joins and the ORDER BY (Z_PK, ZSESSION, ZAGENTPROVENANCE, ZSELECTEDAGENTPROVENANCE,
# ZSEQUENCENUMBER): without one of those the query fails and the file reads as zero rows. The last
# column, the event's Z_PK, joins the attachments and is not reported.
_SELECT = (
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZCREATEDAT'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZCREATIONDATE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZLASTMODIFIEDDATE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSELECTEDAGENTPROVENANCESETAT'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZROLERAWVALUE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZTITLE'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZTEXTCONTENT'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSUMMARY'),
    ('pe', 'ZAGENTPROVENANCEENTITY', 'ZBUNDLEID'),
    ('ps', 'ZAGENTPROVENANCEENTITY', 'ZBUNDLEID'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSOURCEBUNDLEID'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZISPINNED'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZPERSISTABLESTATERAW'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSESSIONID'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZEVENTID'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZSEQUENCENUMBER'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'Z_PK'),
)
_DATES = (0, 1, 2, 3)
_UNDECODED = 'attachment row not decoded'


def _text(value):
    return '' if value is None else str(value)


def _query(path):
    """The join query for the columns this store has; None when a table the join needs is missing."""
    for table in ('ZAGENTSESSIONRECORDENTITY', 'ZAGENTSESSIONEVENTENTITY'):
        if not does_table_exist_in_db(path, table):
            return None
    have_provenance = does_table_exist_in_db(path, 'ZAGENTPROVENANCEENTITY')
    parts = []
    for alias, table, column in _SELECT:
        if alias in ('pe', 'ps') and not have_provenance:
            parts.append(f'NULL AS {alias}_{column}')
        elif does_column_exist_in_db(path, table, column):
            parts.append(f'{alias}.{column} AS {alias}_{column}')
        else:
            parts.append(f'NULL AS {alias}_{column}')
    provenance = ('LEFT JOIN ZAGENTPROVENANCEENTITY pe ON pe.Z_PK = ee.ZAGENTPROVENANCE '
                  'LEFT JOIN ZAGENTPROVENANCEENTITY ps ON ps.Z_PK = re.ZSELECTEDAGENTPROVENANCE'
                  if have_provenance else '')
    return (f"SELECT {', '.join(parts)} FROM ZAGENTSESSIONRECORDENTITY re "
            f"LEFT JOIN ZAGENTSESSIONEVENTENTITY ee ON ee.ZSESSION = re.Z_PK {provenance} "
            "ORDER BY re.Z_PK, ee.ZSEQUENCENUMBER, ee.Z_PK")


def _bookmark(local):
    """bookmark_fields() of a file entity's bookmark, or None when the identifier holds none."""
    if not isinstance(local, str) or not local.startswith('{'):
        return None
    try:
        storage = json.loads(local).get('storage')
        data = base64.b64decode(storage['bookmark']['data'], validate=True)
    except (ValueError, TypeError, KeyError, AttributeError):
        return None
    return bookmark_fields(data)


def _entity(blob):
    """An app-entity attachment row as {'label', 'path', 'type', 'bundle', 'identifier', 'volume'},
    None for a row that is not one, or a dict labelled _UNDECODED for a row that cannot be read as
    one leading byte and JSON."""
    undecoded = {'label': _UNDECODED, 'path': '', 'type': '', 'bundle': '', 'identifier': '', 'volume': ''}
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 2 or blob[0] != 1:
        return undecoded
    try:
        content = json.loads(bytes(blob[1:]).decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return undecoded
    if not isinstance(content, dict) or 'persistableAppEntity' not in content:
        return None
    try:
        origin = content['persistableAppEntity']['_0']['originEntityIdentifierValue']
        custom = origin['type']['custom']
        type_name, bundle = _text(custom.get('typeName')), _text(custom.get('bundleIdentifier'))
        local = origin['instanceIdentifier']['local']['_0']
    except (KeyError, TypeError, AttributeError):
        return undecoded
    fields = _bookmark(local)
    path = fields['path'] if fields else ''
    label = f'{type_name} ({bundle})' if bundle else type_name
    return {'label': f'{label}: {path}' if path else label, 'path': path, 'type': type_name, 'bundle': bundle,
            'identifier': '' if fields is not None else _text(local), 'volume': fields['volume_name'] if fields else ''}


def _has_attachment_columns(path, columns=('ZEVENT', 'ZCONTENTDATA')):
    return does_table_exist_in_db(path, _ARTIFACTS) and all(
        does_column_exist_in_db(path, _ARTIFACTS, column) for column in columns)


def _attachments(path):
    """{event Z_PK: [entity, ...]} from the store's attachment rows, and the count of rows that
    could not be decoded."""
    if not _has_attachment_columns(path):
        return {}, 0
    found, undecoded = {}, 0
    for event, blob in get_sqlite_db_records(
            path, f'SELECT ZEVENT, ZCONTENTDATA FROM {_ARTIFACTS} WHERE ZEVENT IS NOT NULL ORDER BY ZEVENT, Z_PK') or []:
        item = _entity(blob)
        if item is None:
            continue
        if item['label'] == _UNDECODED:
            undecoded += 1
        found.setdefault(event, []).append(item)
    return found, undecoded


def _escape_fnmatch(value):
    return value.replace('[', '[[]').replace('*', '[*]').replace('?', '[?]')


def _media(context, file_path, cache):
    """The media reference for the extraction's file at a bookmarked path, or None."""
    if file_path in cache:
        return cache[file_path]
    cache[file_path] = None
    seeker = context.get_seeker() if hasattr(context, 'get_seeker') else None
    relative = file_path.lstrip('/')
    if seeker is None or not relative:
        return None
    matches = sorted(seeker.search('*/' + _escape_fnmatch(relative)) or [], key=lambda p: (len(str(p)), str(p)))
    if matches:
        cache[file_path] = check_in_media(matches[0], name=os.path.basename(file_path))
    return cache[file_path]


def _rows(context, path, cache):
    query = _query(path)
    if query is None:
        return None
    attachments, undecoded = _attachments(path)
    if undecoded:
        logfunc(f'{_LABEL}: {undecoded} attachment row(s) in {context.get_relative_path(path)} could not be decoded')
    rows = []
    for record in get_sqlite_db_records(path, query) or []:
        values = [mac_absolute_utc(v) if i in _DATES else _text(v) for i, v in enumerate(record[:-1])]
        items = attachments.get(record[-1], []) if record[-1] is not None else []
        media = [ref for ref in (_media(context, item['path'], cache) for item in items if item['path']) if ref]
        # A tuple until the rows are folded, which needs them hashable; the media column takes a list.
        values[7:7] = [tuple(media) or '', '\n'.join(item['label'] for item in items)]
        rows.append(tuple(values))
    return rows


@artifact_processor
def macosSiriAgentSessions(context):
    data_headers = (('Event Created (UTC)', 'datetime'), ('Session Created (UTC)', 'datetime'),
                    ('Session Last Modified (UTC)', 'datetime'), ('Selected Agent Set At (UTC)', 'datetime'),
                    'Role (as stored)', 'Title', 'Text', ('Attachment File', 'media'), 'Attachments', 'Summary',
                    'Event Agent', 'Selected Agent', 'Source Bundle ID', 'Pinned (as stored)', 'State (as stored)',
                    'Session ID', 'Event ID', 'Sequence Number', 'User', 'Source File')
    data_list = []
    read = []
    cache = {}
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == _STORE]
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        rows = _rows(context, path, cache)
        if rows is None:
            logfunc(f'{_LABEL}: the session or event table is missing from {relative}')
            continue
        read.append(path)
        data_list.extend(row + (user_from_path(relative), relative) for row in rows)
    rows = [row[:7] + ((list(row[7]) if row[7] else ''),) + row[8:] for row in fold_view_rows(data_list)]
    return data_headers, rows, '\n'.join(read)


def _store_paths(context, label):
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == _STORE]
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'), label=label)
    return paths


@artifact_processor
def macosSiriAgentAttachments(context):
    data_headers = (('Created (UTC)', 'datetime'), 'Type (as stored)', 'Bundle ID (as stored)', 'File Path (bookmark)',
                    ('Attachment File', 'media'), 'Volume Name (bookmark)', 'Identifier (as stored)', 'Session Title',
                    'Session ID', 'Event ID', 'User', 'Source File')
    data_list, read, cache = [], [], {}
    label = 'Siri App Attachments'
    for path in _store_paths(context, label):
        relative = context.get_relative_path(path)
        if not _has_attachment_columns(path, ('ZSESSION', 'ZEVENT', 'ZCONTENTDATA')) or not all(
                does_table_exist_in_db(path, table)
                for table in ('ZAGENTSESSIONRECORDENTITY', 'ZAGENTSESSIONEVENTENTITY')):
            logfunc(f'{label}: the attachment, session or event table is missing from {relative}')
            continue
        read.append(path)
        created = 'a.ZCREATEDAT' if does_column_exist_in_db(path, _ARTIFACTS, 'ZCREATEDAT') else 'NULL'
        title = 'r.ZTITLE' if does_column_exist_in_db(path, 'ZAGENTSESSIONRECORDENTITY', 'ZTITLE') else 'NULL'
        session = 'r.ZSESSIONID' if does_column_exist_in_db(path, 'ZAGENTSESSIONRECORDENTITY', 'ZSESSIONID') else 'NULL'
        event = 'e.ZEVENTID' if does_column_exist_in_db(path, 'ZAGENTSESSIONEVENTENTITY', 'ZEVENTID') else 'NULL'
        undecoded = 0
        for stamp, blob, session_title, session_id, event_id in get_sqlite_db_records(
                path, f'SELECT {created}, a.ZCONTENTDATA, {title}, {session}, {event} FROM {_ARTIFACTS} a '
                      'LEFT JOIN ZAGENTSESSIONRECORDENTITY r ON r.Z_PK = a.ZSESSION '
                      'LEFT JOIN ZAGENTSESSIONEVENTENTITY e ON e.Z_PK = a.ZEVENT ORDER BY a.Z_PK') or []:
            item = _entity(blob)
            if item is None:
                continue
            if item['label'] == _UNDECODED:
                undecoded += 1
            media = _media(context, item['path'], cache) if item['path'] else None
            data_list.append((mac_absolute_utc(stamp), item['type'] or item['label'], item['bundle'], item['path'],
                              media or '', item['volume'], item['identifier'], _text(session_title),
                              _text(session_id), _text(event_id), user_from_path(relative), relative))
        if undecoded:
            logfunc(f'{label}: {undecoded} attachment row(s) in {relative} could not be decoded')
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


def _entity_numbers(path):
    """{entity name: Z_ENT} from the store's Z_PRIMARYKEY table."""
    if not does_table_exist_in_db(path, 'Z_PRIMARYKEY'):
        return {}
    return {name: number for number, name in get_sqlite_db_records(path, 'SELECT Z_ENT, Z_NAME FROM Z_PRIMARYKEY') or []}


@artifact_processor
def macosSiriAgentDeletions(context):
    data_headers = (('Deleted At (UTC)', 'datetime'), 'Session IDs', 'Events Deleted', 'Event IDs',
                    'Transaction ID', 'User', 'Source File')
    data_list, read = [], []
    label = 'Siri App Deleted Conversations'
    for path in _store_paths(context, label):
        relative = context.get_relative_path(path)
        numbers = _entity_numbers(path)
        session_ent, event_ent = numbers.get('AgentSessionRecordEntity'), numbers.get('AgentSessionEventEntity')
        if (session_ent is None or event_ent is None or not does_table_exist_in_db(path, 'ACHANGE')
                or not does_table_exist_in_db(path, 'ATRANSACTION')):
            logfunc(f'{label}: no persistent history or entity table in {relative}')
            continue
        read.append(path)
        tombstone = 'c.ZTOMBSTONE0' if does_column_exist_in_db(path, 'ACHANGE', 'ZTOMBSTONE0') else 'NULL'
        transactions = {}
        for transaction, stamp, entity, value in get_sqlite_db_records(
                path, f'SELECT c.ZTRANSACTIONID, t.ZTIMESTAMP, c.ZENTITY, {tombstone} FROM ACHANGE c '
                      'LEFT JOIN ATRANSACTION t ON t.Z_PK = c.ZTRANSACTIONID '
                      f'WHERE c.ZCHANGETYPE = 2 AND c.ZENTITY IN ({int(session_ent)}, {int(event_ent)}) '
                      'ORDER BY c.ZTRANSACTIONID, c.Z_PK') or []:
            entry = transactions.setdefault(transaction, {'stamp': stamp, 'sessions': [], 'events': []})
            entry['sessions' if entity == session_ent else 'events'].append(_text(value))
        for transaction, entry in transactions.items():
            data_list.append((mac_absolute_utc(entry['stamp']), '\n'.join(entry['sessions']), len(entry['events']),
                              '\n'.join(entry['events']), _text(transaction), user_from_path(relative), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
