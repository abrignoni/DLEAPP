import sqlite3

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               convert_cocoa_core_data_ts_to_utc, logfunc)

# macOS keeps knowledgeC.db in two places, and they carry different streams:
# the per-user store at ~/Library/Application Support/Knowledge/knowledgeC.db
# and the system store at /private/var/db/CoreDuet/Knowledge/knowledgeC.db. The
# pattern '*/Knowledge/knowledgeC.db*' matches both (and the CoreDuet spelling
# used on iOS). Each processor reads every knowledgeC.db found and tags each row
# with its Source File, so both the system/per-user split and a Mac with more
# than one user account are reported. Start and end times are Mac Absolute Time
# (Core Data), seconds since 2001-01-01 UTC, rendered in UTC. knowledgeC.db
# keeps its live rows in a write-ahead log, so the -wal sidecar is read too.
#
# The forensic value of knowledgeC.db is documented by Sarah Edwards in
# 'Knowledge is Power! Using the knowledgeC.db Database on macOS and iOS'
# (mac4n6.com). Each artifact below cites that research. The SQL here was
# written against the live schema of the validation image, not taken from
# another tool.

__artifacts_v2__ = {
    "knowledgeCInFocus": {
        "name": "KnowledgeC - App In Focus",
        "description": "/app/inFocus events from knowledgeC.db: the bundle "
                       "identifier of the application that was frontmost, with "
                       "the start, end and duration of each focus interval.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The bundle identifier is in ZVALUESTRING. Times are Mac "
                 "Absolute Time (Core Data) in UTC; the -wal sidecar is read "
                 "alongside the database. Reference: Sarah Edwards, 'Knowledge "
                 "is Power', https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "eye",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 135 rows",
        },
    },
    "knowledgeCAppUsage": {
        "name": "KnowledgeC - App Usage",
        "description": "/app/usage events from knowledgeC.db: the bundle "
                       "identifier of the application in use, with the start, "
                       "end and duration of each usage interval.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The bundle identifier is in ZVALUESTRING. Times are Mac "
                 "Absolute Time (Core Data) in UTC; the -wal sidecar is read "
                 "alongside the database. Reference: Sarah Edwards, 'Knowledge "
                 "is Power', https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 220 rows",
        },
    },
    "knowledgeCWebUsage": {
        "name": "KnowledgeC - Web Usage",
        "description": "/app/webUsage events from knowledgeC.db: the browser "
                       "bundle identifier, the web domain and page URL from the "
                       "structured metadata, and the recorded duration.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The browser bundle is in ZVALUESTRING; the domain and page "
                 "URL are in the structured metadata (Screen Time / Digital "
                 "Health keys). The Browser Bundle ID column is uniform when "
                 "only one browser recorded web usage. Times are Mac Absolute "
                 "Time (Core Data) in UTC; the -wal sidecar is read alongside "
                 "the database. Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 21 rows",
        },
    },
    "knowledgeCSafariHistory": {
        "name": "KnowledgeC - Safari History",
        "description": "/safari/history events from knowledgeC.db: the URL "
                       "Safari recorded and the page title from the structured "
                       "metadata. This is CoreDuet's own record, separate from "
                       "Safari's History.db.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The URL is in ZVALUESTRING; the page title is in the "
                 "structured metadata. Visit Time is Mac Absolute Time (Core "
                 "Data) in UTC; the -wal sidecar is read alongside the "
                 "database. Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "compass",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 10 rows",
        },
    },
    "knowledgeCAppIntents": {
        "name": "KnowledgeC - App Intents",
        "description": "/app/intents events from knowledgeC.db: donated "
                       "Siri/Shortcuts intents, with the intent class, verb, "
                       "direction and derived identifier from the structured "
                       "metadata.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The app short name is in ZVALUESTRING; the intent class, "
                 "verb, direction and derived identifier are in the structured "
                 "metadata. The derived identifier is reported as stored and is "
                 "URL-encoded; it can name a message recipient or conversation. "
                 "Intent direction is reported as stored (integer); its values "
                 "are not documented here. Times are Mac Absolute Time (Core "
                 "Data) in UTC; the -wal sidecar is read alongside the "
                 "database. Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "zap",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 134 rows",
        },
    },
    "knowledgeCNotificationUsage": {
        "name": "KnowledgeC - Notification Usage",
        "description": "/notification/usage events from knowledgeC.db: the "
                       "notification action (Receive, Clear, IndirectClear, "
                       "Dismiss, Hidden) and, where recorded, the bundle "
                       "identifier of the app whose notification it was.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The action is in ZVALUESTRING; the App Bundle ID is in the "
                 "structured metadata and is not recorded on every row (blank "
                 "where absent). Event Time is Mac Absolute Time (Core Data) in "
                 "UTC; the -wal sidecar is read alongside the database. "
                 "Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "bell",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 323 rows",
        },
    },
    "knowledgeCAppMediaUsage": {
        "name": "KnowledgeC - App Media Usage",
        "description": "/app/mediaUsage events from knowledgeC.db: the app bundle "
                       "identifier, start and end times, and the URL and media URL "
                       "from the structured metadata where present.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "One row per ZOBJECT record whose ZSTREAMNAME is /app/mediaUsage. "
                 "App Bundle ID is ZVALUESTRING; URL and Media URL are the "
                 "structured metadata columns Z_DKAPPMEDIAUSAGEMETADATAKEY__URL "
                 "and Z_DKAPPMEDIAUSAGEMETADATAKEY__MEDIAURL as stored, and are "
                 "blank when the store has no such column. What media activity a "
                 "row records is not established. Times are Mac Absolute Time "
                 "(Core Data) in UTC; the -wal sidecar is read alongside the "
                 "database. Public regression cases are independently authored "
                 "synthetic data; local private validation details are not "
                 "published. Sarah Edwards' APOLLO also reads this stream, in its "
                 "knowledge_app_media_usage module: "
                 "https://github.com/mac4n6/APOLLO/blob/bd725461fbd22c8ceadd04f0c4ded49b66147439/modules/knowledge_app_media_usage.txt#L59-L101",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "player-play",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows",
        },
    },
    "knowledgeCMediaPlaying": {
        "name": "KnowledgeC - Media Playing",
        "description": "/media/nowPlaying events from knowledgeC.db: playing "
                       "state, the app bundle identifier, and the artist, "
                       "album, title and genre of the media from the structured "
                       "metadata.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The playing state and media metadata are in the structured "
                 "metadata. Times are Mac Absolute Time (Core Data) in UTC; the "
                 "-wal sidecar is read alongside the database. References: Sarah "
                 "Edwards, 'Knowledge is Power', https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage"
                 " and Ian Whiffin, https://www.doubleblak.com/blogPosts.php?id=29",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "music",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 2 rows",
        },
    },
    "knowledgeCIsBacklit": {
        "name": "KnowledgeC - Display Backlit",
        "description": "/display/isBacklit events from knowledgeC.db: whether "
                       "the display backlight was on, with the start and end of "
                       "each interval.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The Screen Status is read from ZVALUEINTEGER (0 backlight "
                 "off, 1 backlight on). Times are Mac Absolute Time (Core Data) "
                 "in UTC; the -wal sidecar is read alongside the database. "
                 "Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "sun",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 225 rows",
        },
    },
    "knowledgeCIsLocked": {
        "name": "KnowledgeC - Device Locked",
        "description": "/device/isLocked events from knowledgeC.db: the device "
                       "lock status, with the start and end of each interval.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The Lock Status is read from ZVALUEINTEGER (0 unlocked, 1 "
                 "locked). Times are Mac Absolute Time (Core Data) in UTC; the "
                 "-wal sidecar is read alongside the database. Reference: Sarah "
                 "Edwards, 'Knowledge is Power', https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 37 rows",
        },
    },
    "knowledgeCIsPluggedIn": {
        "name": "KnowledgeC - Device Plugged In",
        "description": "/device/isPluggedIn events from knowledgeC.db: whether "
                       "the device was on external power, with the start and "
                       "end of each interval.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "notes": "The Charging State is read from ZVALUEINTEGER (0 not plugged "
                 "in, 1 plugged in). A desktop, or a Mac left on a charger, "
                 "records long plugged-in intervals, so the Charging State "
                 "column can be uniform. Times are Mac Absolute Time (Core "
                 "Data) in UTC; the -wal sidecar is read alongside the "
                 "database. Reference: Sarah Edwards, 'Knowledge is Power', "
                 "https://www.mac4n6.com/blog/2018/8/5/knowledge-is-power-using-the-knowledgecdb-database-on-macos-and-ios-to-determine-precise-user-and-application-usage",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "battery-charging",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 5 rows",
        },
    },
}


def _kc_sources(context):
    return [str(f) for f in context.get_files_found() if str(f).endswith('knowledgeC.db')]


def _collect(context, query, transform):
    '''Run query against every knowledgeC.db found, tag each row with its
    relative Source File, and return (data_list, newline-joined sources). A
    store missing a column logs and is skipped rather than costing every row.'''
    data_list = []
    read_sources = []
    for source in _kc_sources(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            for row in database.execute(query):
                built = transform(row)
                if built is None:
                    continue
                data_list.append(built + (relative_source,))
                rows_here += 1
        except sqlite3.OperationalError as exc:
            logfunc(f'knowledgeC {relative_source}: {exc}')
        finally:
            database.close()
        if rows_here:
            read_sources.append(relative_source)
    return data_list, "\n".join(read_sources)


def _cd(ts):
    return convert_cocoa_core_data_ts_to_utc(ts)


def _dur(start, end):
    if start is None or end is None:
        return ''
    return int(round(end - start))


_MEDIA_USAGE_KEYS = ('Z_DKAPPMEDIAUSAGEMETADATAKEY__URL',
                     'Z_DKAPPMEDIAUSAGEMETADATAKEY__MEDIAURL')


@artifact_processor
def knowledgeCAppMediaUsage(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    'App Bundle ID', 'URL', 'Media URL', 'Duration (s)', 'Source File')
    data_list = []
    read_sources = []
    for source in _kc_sources(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        try:
            present = {row[1] for row in database.execute('PRAGMA table_info(ZSTRUCTUREDMETADATA)')}
            wanted = ', '.join(f'sm."{key}"' if key in present else 'NULL'
                               for key in _MEDIA_USAGE_KEYS)
            join = ('LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK'
                    if present else '')
            rows = database.execute(
                f'SELECT o.ZSTARTDATE, o.ZENDDATE, o.ZVALUESTRING, {wanted} FROM ZOBJECT o '
                f"{join} WHERE o.ZSTREAMNAME = '/app/mediaUsage' ORDER BY o.ZSTARTDATE").fetchall()
        except sqlite3.OperationalError as exc:
            logfunc(f'knowledgeC {relative_source}: {exc}')
            continue
        finally:
            database.close()
        for row in rows:
            data_list.append((_cd(row[0]), _cd(row[1]), row[2] or '', row[3] or '',
                              row[4] or '', _dur(row[0], row[1]), relative_source))
        if rows:
            read_sources.append(relative_source)
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def knowledgeCInFocus(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    'App Bundle ID', 'Duration (s)', 'Source File')
    query = ("SELECT ZSTARTDATE, ZENDDATE, ZVALUESTRING FROM ZOBJECT "
             "WHERE ZSTREAMNAME = '/app/inFocus' ORDER BY ZSTARTDATE")
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), _cd(r[1]), r[2], _dur(r[0], r[1])))
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCAppUsage(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    'Application', 'Duration (s)', 'Source File')
    query = ("SELECT ZSTARTDATE, ZENDDATE, ZVALUESTRING FROM ZOBJECT "
             "WHERE ZSTREAMNAME = '/app/usage' ORDER BY ZSTARTDATE")
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), _cd(r[1]), r[2], _dur(r[0], r[1])))
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCWebUsage(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    'Browser Bundle ID', 'Web Domain', 'Web Page URL',
                    'Duration (s)', 'Source File')
    query = ('''SELECT o.ZSTARTDATE, o.ZENDDATE, o.ZVALUESTRING,
                       sm.Z_DKDIGITALHEALTHMETADATAKEY__WEBDOMAIN,
                       sm.Z_DKDIGITALHEALTHMETADATAKEY__WEBPAGEURL
                FROM ZOBJECT o
                LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK
                WHERE o.ZSTREAMNAME = '/app/webUsage' ORDER BY o.ZSTARTDATE''')
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), _cd(r[1]), r[2], r[3] or '', r[4] or '', _dur(r[0], r[1])))
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCSafariHistory(context):
    data_headers = (('Visit Time', 'datetime'), 'URL', 'Page Title', 'Source File')
    query = ('''SELECT o.ZSTARTDATE, o.ZVALUESTRING,
                       sm.Z_DKSAFARIHISTORYMETADATAKEY__TITLE
                FROM ZOBJECT o
                LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK
                WHERE o.ZSTREAMNAME = '/safari/history' ORDER BY o.ZSTARTDATE''')
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), r[1] or '', r[2] or ''))
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCAppIntents(context):
    data_headers = (('Start Time', 'datetime'), 'App', 'Intent Class', 'Intent Verb',
                    'Intent Direction (as stored)', 'Derived Intent Identifier (as stored)',
                    'Source File')
    query = ('''SELECT o.ZSTARTDATE, o.ZVALUESTRING,
                       sm.Z_DKINTENTMETADATAKEY__INTENTCLASS,
                       sm.Z_DKINTENTMETADATAKEY__INTENTVERB,
                       sm.Z_DKINTENTMETADATAKEY__DIRECTION,
                       sm.Z_DKINTENTMETADATAKEY__DERIVEDINTENTIDENTIFIER
                FROM ZOBJECT o
                LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK
                WHERE o.ZSTREAMNAME = '/app/intents' ORDER BY o.ZSTARTDATE''')
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), r[1] or '', r[2] or '', r[3] or '',
                   '' if r[4] is None else r[4], r[5] or ''))
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCNotificationUsage(context):
    data_headers = (('Event Time', 'datetime'), 'Notification Action', 'App Bundle ID',
                    'Source File')
    query = ('''SELECT o.ZSTARTDATE, o.ZVALUESTRING,
                       sm.Z_DKNOTIFICATIONUSAGEMETADATAKEY__BUNDLEID
                FROM ZOBJECT o
                LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK
                WHERE o.ZSTREAMNAME = '/notification/usage' ORDER BY o.ZSTARTDATE''')
    data_list, sources = _collect(context, query,
        lambda r: (_cd(r[0]), r[1] or '', r[2] or ''))
    return data_headers, data_list, sources


_PLAYING_STATE = {0: 'Stop', 1: 'Play', 2: 'Pause', 3: 'Loading', 4: 'Interruption'}


@artifact_processor
def knowledgeCMediaPlaying(context):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'), 'Playing State',
                    'App Bundle ID', 'Artist', 'Album', 'Title', 'Genre', 'Source File')
    query = ('''SELECT o.ZSTARTDATE, o.ZENDDATE,
                       sm.Z_DKNOWPLAYINGMETADATAKEY__PLAYING, o.ZVALUESTRING,
                       sm.Z_DKNOWPLAYINGMETADATAKEY__ARTIST,
                       sm.Z_DKNOWPLAYINGMETADATAKEY__ALBUM,
                       sm.Z_DKNOWPLAYINGMETADATAKEY__TITLE,
                       sm.Z_DKNOWPLAYINGMETADATAKEY__GENRE
                FROM ZOBJECT o
                LEFT JOIN ZSTRUCTUREDMETADATA sm ON o.ZSTRUCTUREDMETADATA = sm.Z_PK
                WHERE o.ZSTREAMNAME = '/media/nowPlaying' AND o.ZVALUESTRING != ''
                ORDER BY o.ZSTARTDATE''')

    def _row(r):
        state = _PLAYING_STATE.get(r[2], r[2] if r[2] is not None else '')
        return (_cd(r[0]), _cd(r[1]), state, r[3], r[4] or '', r[5] or '',
                r[6] or '', r[7] or '')
    data_list, sources = _collect(context, query, _row)
    return data_headers, data_list, sources


def _state_rows(context, stream, status_header, off_label, on_label):
    data_headers = (('Start Time', 'datetime'), ('End Time', 'datetime'),
                    status_header, 'Source File')
    query = (f"SELECT ZSTARTDATE, ZENDDATE, ZVALUEINTEGER FROM ZOBJECT "
             f"WHERE ZSTREAMNAME = '{stream}' ORDER BY ZSTARTDATE")

    def _row(r):
        status = {0: off_label, 1: on_label}.get(r[2], r[2] if r[2] is not None else '')
        return (_cd(r[0]), _cd(r[1]), status)
    data_list, sources = _collect(context, query, _row)
    return data_headers, data_list, sources


@artifact_processor
def knowledgeCIsBacklit(context):
    return _state_rows(context, '/display/isBacklit', 'Screen Status',
                       'Backlight off', 'Backlight on')


@artifact_processor
def knowledgeCIsLocked(context):
    return _state_rows(context, '/device/isLocked', 'Lock Status',
                       'Unlocked', 'Locked')


@artifact_processor
def knowledgeCIsPluggedIn(context):
    return _state_rows(context, '/device/isPluggedIn', 'Charging State',
                       'Not plugged in', 'Plugged in')
