"""Siri app conversation history from a macOS AgentSessionStore.sqlite database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSiriAgentSessions": {
        "name": "Siri App Conversations",
        "description": "Sessions and events in AgentSessionStore.sqlite under a Daemon Containers folder, one row "
                       "per event with its session's title, summary, creation and last-modified times, agent "
                       "bundle IDs and source bundle ID, or one row for a session that has no event. An event whose "
                       "session record is absent is not reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Siri (macOS)",
        "notes": "Reads the Core Data store AgentSessionStore.sqlite in "
                 "Library/Daemon Containers/<UUID>/Data/AgentSessionKit. The path is matched on the "
                 "AgentSessionKit folder; the container's .com.apple.containermanagerd.metadata.plist identifier "
                 "is not checked. Every date is read as seconds since 2001-01-01 UTC. The tables and columns "
                 "come from the published description by Yogesh Khatri (Swift Forensics, 15 November 2026) and "
                 "the mac_apt siri.py plugin (MIT), and from the store schema of a macOS 27.2.1 Mac. "
                 "Evidence tier: the three table definitions the artifact reads are data-proven on that Mac, whose "
                 "store held no session or event rows. The 2001 epoch is source-verified for the four reported "
                 "date columns: the published query and mac_apt read them that way, and the store's own model "
                 "declares them as Core Data Date attributes; no stored value of those columns was available "
                 "to check. The store's ATRANSACTION times, read on the same epoch, match the file's "
                 "last-written time on that Mac. The join and the columns the published query names are "
                 "source-verified; Selected Agent, State, Event ID and Sequence Number come from the store's "
                 "schema and model only. All of it was exercised only on a test database built with that schema "
                 "and made-up values, so no real conversation has been read by this artifact. Event Created is "
                 "ZCREATEDAT of the event; Session Created and Session Last Modified are ZCREATIONDATE and "
                 "ZLASTMODIFIEDDATE of the session record; Selected Agent Set At is "
                 "ZSELECTEDAGENTPROVENANCESETAT. Role (as stored) is ZROLERAWVALUE and State (as stored) is "
                 "ZPERSISTABLESTATERAW, reported as stored; the artifact maps neither to a meaning. The "
                 "published description reports, without citing an Apple source, that a session with a state of "
                 "0 does not show in the app's conversations and can be removed later. Pinned is ZISPINNED as "
                 "stored. Event Agent is the ZBUNDLEID of the event's provenance row and Selected Agent that of "
                 "the session's selected provenance row. A session with no event reports blank event columns, "
                 "including a blank first column. An event with no text (ZTEXTCONTENT NULL) is reported with a "
                 "blank Text; mac_apt skips assistant events with no text, so its row count can be lower. A "
                 "row shows that the event was written to this store, not that the user saw or typed it. Not "
                 "reported, among other columns: attachment rows (ZARTIFACTENTITY; the published description "
                 "says they usually hold a JSON string with embedded bookmarks and plists; not decoded here), "
                 "ZSESSIONRESUMPTIONDATA, ZCONVERSATIONFRAGMENTINDEXCONTENT, the turn ID columns, "
                 "ZINTERNALSESSIONID, ZEXTERNALPROVIDER, the sensitivity and safety-state columns and table, "
                 "the sync tables (ZCLOUDKITSYNCENGINESTATEENTITY and the four other sync entity tables), "
                 "ZCASCADEDONATIONSTATEENTITY, and the persistent-history tables (ACHANGE, ATRANSACTION, "
                 "ATRANSACTIONSTRING). A -wal file staged beside the database is opened with it; this was not "
                 "exercised, since neither test store had a -wal. Whether iOS or iPadOS 27 carries the same "
                 "store is not established.",
        "paths": ("*/Library/Daemon Containers/*/Data/AgentSessionKit/AgentSessionStore.sqlite*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
    },
}

import os

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, mac_absolute_utc, unique_sources, user_from_path

_LABEL = 'Siri App Conversations'
_STORE = 'AgentSessionStore.sqlite'

# (alias, table, column): the columns read. A column the store lacks is selected as NULL, except the
# keys of the joins and the ORDER BY (Z_PK, ZSESSION, ZAGENTPROVENANCE, ZSELECTEDAGENTPROVENANCE,
# ZSEQUENCENUMBER): without one of those the query fails and the file reads as zero rows.
_SELECT = (
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZCREATEDAT'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZCREATIONDATE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZLASTMODIFIEDDATE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSELECTEDAGENTPROVENANCESETAT'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZROLERAWVALUE'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZTEXTCONTENT'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZTITLE'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSUMMARY'),
    ('pe', 'ZAGENTPROVENANCEENTITY', 'ZBUNDLEID'),
    ('ps', 'ZAGENTPROVENANCEENTITY', 'ZBUNDLEID'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSOURCEBUNDLEID'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZISPINNED'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZPERSISTABLESTATERAW'),
    ('re', 'ZAGENTSESSIONRECORDENTITY', 'ZSESSIONID'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZEVENTID'),
    ('ee', 'ZAGENTSESSIONEVENTENTITY', 'ZSEQUENCENUMBER'),
)
_DATES = (0, 1, 2, 3)


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


def _rows(path):
    query = _query(path)
    if query is None:
        return None
    return [tuple(mac_absolute_utc(v) if i in _DATES else _text(v) for i, v in enumerate(row))
            for row in (get_sqlite_db_records(path, query) or [])]


@artifact_processor
def macosSiriAgentSessions(context):
    data_headers = (('Event Created (UTC)', 'datetime'), ('Session Created (UTC)', 'datetime'),
                    ('Session Last Modified (UTC)', 'datetime'), ('Selected Agent Set At (UTC)', 'datetime'),
                    'Role (as stored)', 'Text', 'Title', 'Summary', 'Event Agent', 'Selected Agent',
                    'Source Bundle ID', 'Pinned (as stored)', 'State (as stored)', 'Session ID', 'Event ID',
                    'Sequence Number', 'User', 'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == _STORE]
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        rows = _rows(path)
        if rows is None:
            logfunc(f'{_LABEL}: the session or event table is missing from {relative}')
            continue
        read.append(path)
        data_list.extend(row + (user_from_path(relative), relative) for row in rows)
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
