import sqlite3

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               convert_cocoa_core_data_ts_to_utc, logfunc)

# macOS CoreDuet keeps interactionC.db at /private/var/db/CoreDuet/People/. It
# records per-app interactions (Messages, Mail, Calendar and other apps that
# donate to the People/interaction store): who, which app, direction, and when.

__artifacts_v2__ = {
    "interactionCContacts": {
        "name": "InteractionC - Contact Interactions",
        "description": "Interactions from interactionC.db (ZINTERACTIONS joined "
                       "to ZCONTACTS on the sender): the app, direction, the "
                       "other party's name and identifier, recipient count and "
                       "the start and end of each interaction.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none",
        "category": "InteractionC (macOS)",
        "notes": "Every interactionC.db found is parsed, tagged by Source File. "
                 "The app is ZBUNDLEID. ZSENDER links to the ZCONTACTS row for "
                 "the other party, which is populated on incoming interactions; "
                 "outgoing interactions record a Recipient Count but their "
                 "recipients live in a separate table not surfaced here, so a "
                 "blank Sender on a row with a recipient count is an outgoing "
                 "interaction. Direction and Is Response are reported as stored "
                 "(integers). Times are Mac Absolute Time (Core Data), seconds "
                 "since 2001-01-01 UTC, rendered in UTC; the -wal sidecar is "
                 "read alongside the database. Adapted from the iLEAPP "
                 "interactionC module.",
        "paths": ('*/interactionC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 64 rows (Messages and Calendar interactions; 45 in the database and 19 more applied from the -wal)",
        },
    },
}


def _cd(ts):
    return convert_cocoa_core_data_ts_to_utc(ts)


@artifact_processor
def interactionCContacts(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'), 'App',
                    'Direction (as stored)', 'Sender Name', 'Sender Identifier',
                    'Recipient Count', 'Is Response (as stored)', 'Group Name', 'Source File')
    data_list = []
    read_sources = []
    query = ('''SELECT i.ZSTARTDATE, i.ZENDDATE, i.ZBUNDLEID, i.ZDIRECTION,
                       ct.ZDISPLAYNAME, ct.ZIDENTIFIER, i.ZRECIPIENTCOUNT,
                       i.ZISRESPONSE, i.ZGROUPNAME
                FROM ZINTERACTIONS i
                LEFT JOIN ZCONTACTS ct ON i.ZSENDER = ct.Z_PK
                ORDER BY i.ZSTARTDATE, i.rowid, ct.rowid''')

    for source in [str(f) for f in context.get_files_found() if str(f).endswith('interactionC.db')]:
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            for r in database.execute(query):
                data_list.append((_cd(r[0]), _cd(r[1]), r[2] or '',
                                  '' if r[3] is None else r[3], r[4] or '', r[5] or '',
                                  '' if r[6] is None else r[6],
                                  '' if r[7] is None else r[7], r[8] or '', relative_source))
                rows_here += 1
        except sqlite3.OperationalError as exc:
            logfunc(f'interactionC {relative_source}: {exc}')
        finally:
            database.close()
        if rows_here:
            read_sources.append(relative_source)

    return data_headers, data_list, "\n".join(read_sources)
