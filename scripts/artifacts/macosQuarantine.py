import sqlite3

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               convert_cocoa_core_data_ts_to_utc, logfunc)

# macOS records a quarantine event for files written by "quarantine-aware" apps
# (browsers, mail, messaging, AirDrop), in a per-user SQLite store at
# ~/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2. Each row is
# the provenance of a downloaded/received file: which app wrote it, when, and,
# for web downloads, the source and referrer URLs.

__artifacts_v2__ = {
    "quarantineEvents": {
        "name": "LaunchServices Quarantine Events",
        "description": "Downloaded and received files recorded in the "
                       "LSQuarantineEvent table: the agent app, the source and "
                       "referrer URLs where present, and the event timestamp.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none",
        "category": "Quarantine (macOS)",
        "notes": "Every QuarantineEventsV2 store found is parsed, one per user, "
                 "tagged by Source File. Timestamp is CFAbsoluteTime (seconds "
                 "since 2001-01-01 UTC), rendered in UTC. Agent Name is the app "
                 "that wrote the file. Data URL is the file's source URL and "
                 "Origin URL is the referrer; both are populated for web "
                 "downloads and are blank for files received by messaging or "
                 "AirDrop, so a row with a blank Data URL and an Agent Name of a "
                 "messaging app is a received file rather than a web download. "
                 "Type Number is reported as stored. When every event on a "
                 "system was received the same way, Agent Bundle ID is uniform "
                 "and Origin Title and Sender Name are blank; these vary once "
                 "web downloads are present. The -wal sidecar is read alongside "
                 "the database.",
        "paths": ('*/com.apple.LaunchServices.QuarantineEventsV2*',),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 10 rows (all iChat-received on this image; no web downloads)",
        },
    },
}


@artifact_processor
def quarantineEvents(context):
    data_headers = (('Timestamp', 'datetime'), 'Agent Name', 'Agent Bundle ID',
                    'Data URL', 'Origin URL', 'Origin Title', 'Sender Name',
                    'Type Number (as stored)', 'Event Identifier', 'Source File')
    data_list = []
    read_sources = []

    for source in [str(f) for f in context.get_files_found()
                   if str(f).endswith('QuarantineEventsV2')]:
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            query = ('''SELECT LSQuarantineTimeStamp, LSQuarantineAgentName,
                               LSQuarantineAgentBundleIdentifier, LSQuarantineDataURLString,
                               LSQuarantineOriginURLString, LSQuarantineOriginTitle,
                               LSQuarantineSenderName, LSQuarantineTypeNumber,
                               LSQuarantineEventIdentifier
                        FROM LSQuarantineEvent ORDER BY LSQuarantineTimeStamp''')
            for r in database.execute(query):
                ts = convert_cocoa_core_data_ts_to_utc(r[0]) if r[0] else ''
                data_list.append((ts, r[1] or '', r[2] or '', r[3] or '', r[4] or '',
                                  r[5] or '', r[6] or '',
                                  '' if r[7] is None else r[7], r[8] or '', relative_source))
                rows_here += 1
        except sqlite3.Error as exc:
            logfunc(f'Quarantine {relative_source}: {exc}')
        finally:
            database.close()
        if rows_here:
            read_sources.append(relative_source)

    return data_headers, data_list, "\n".join(read_sources)
