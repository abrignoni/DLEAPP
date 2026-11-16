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
                 '(content kind data, a binary property list of archived Siri command objects, not decoded), the '
                 'session-level AgentMediaEntity rows (heroMedia in their metadata), seen on the test session whose '
                 'reply showed images, the other ZARTIFACTENTITY columns, ZTITLESOURCE, ZTHUMBNAILBACKGROUNDIMAGE, '
                 'ZSESSIONRESUMPTIONDATA (binary, populated on every event; see the attached-file note), '
                 'ZCONVERSATIONFRAGMENTINDEXCONTENT, the turn ID columns, ZINTERNALSESSIONID, ZEXTERNALPROVIDER, the '
                 'sensitivity and safety-state columns and table, the sync tables (ZCLOUDKITSYNCENGINESTATEENTITY '
                 'and the four other sync entity tables), ZCASCADEDONATIONSTATEENTITY, and the persistent-history '
                 'tables (ACHANGE, ATRANSACTION, ATRANSACTIONSTRING). Deleting a conversation in the app removed its '
                 'session, event and attachment rows, so a deleted conversation is not reported here; the persistent '
                 "history kept tombstones holding the deleted session's and events' IDs with the time of the delete. "
                 'In a copy taken within about a minute of the delete, text from the deleted conversation was still '
                 'in the database file and in its -wal file. The delete was only in the -wal at that point: the '
                 "database file read without it still held the conversation's rows. How long either lasts was not "
                 'measured. A -wal file staged beside the database is opened with it. Not exercised: requests from '
                 'the search bar (Command + Space), spoken requests, sessions with more than one request, an '
                 'external provider, attachments other than a short text file, and retention expiry. Whether iOS or '
                 'iPadOS 27 carries the same store is not established.',
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


def _bookmark_path(local):
    """The path a file entity's bookmark records, or '' when the identifier holds none."""
    if not isinstance(local, str) or not local.startswith('{'):
        return ''
    try:
        storage = json.loads(local).get('storage')
        data = base64.b64decode(storage['bookmark']['data'], validate=True)
    except (ValueError, TypeError, KeyError, AttributeError):
        return ''
    fields = bookmark_fields(data)
    return fields['path'] if fields else ''


def _entity(blob):
    """(label, file path) for an app-entity attachment row, None for a row that is not one,
    or (_UNDECODED, '') for a row that cannot be read as one leading byte and JSON."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 2 or blob[0] != 1:
        return _UNDECODED, ''
    try:
        content = json.loads(bytes(blob[1:]).decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return _UNDECODED, ''
    if not isinstance(content, dict) or 'persistableAppEntity' not in content:
        return None
    try:
        origin = content['persistableAppEntity']['_0']['originEntityIdentifierValue']
        custom = origin['type']['custom']
        type_name, bundle = _text(custom.get('typeName')), _text(custom.get('bundleIdentifier'))
        local = origin['instanceIdentifier']['local']['_0']
    except (KeyError, TypeError, AttributeError):
        return _UNDECODED, ''
    path = _bookmark_path(local)
    label = f'{type_name} ({bundle})' if bundle else type_name
    return (f'{label}: {path}' if path else label), path


def _attachments(path):
    """{event Z_PK: [(label, file path), ...]} from the store's attachment rows, and the count of
    rows that could not be decoded."""
    if not does_table_exist_in_db(path, _ARTIFACTS) or not all(
            does_column_exist_in_db(path, _ARTIFACTS, column) for column in ('ZEVENT', 'ZCONTENTDATA')):
        return {}, 0
    found, undecoded = {}, 0
    for event, blob in get_sqlite_db_records(
            path, f'SELECT ZEVENT, ZCONTENTDATA FROM {_ARTIFACTS} WHERE ZEVENT IS NOT NULL ORDER BY ZEVENT, Z_PK') or []:
        item = _entity(blob)
        if item is None:
            continue
        if item[0] == _UNDECODED:
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
        media = [ref for ref in (_media(context, item[1], cache) for item in items if item[1]) if ref]
        # A tuple until the rows are folded, which needs them hashable; the media column takes a list.
        values[7:7] = [tuple(media) or '', '\n'.join(item[0] for item in items)]
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
