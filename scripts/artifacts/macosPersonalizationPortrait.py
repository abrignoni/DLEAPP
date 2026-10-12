"""Named entities, topics and locations in the macOS Personalization Portrait database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosPortraitNamedEntities": {
        "name": "Personalization Portrait - Named Entities",
        "description": "Named entity records of PPSQLDatabase.db, one row per record, with the bundle ID, group "
                       "ID, document ID and time of the source row each record references.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Personalization Portrait (macOS)",
        "notes": "Reads PPSQLDatabase.db in a Library/PersonalizationPortrait folder, which in the tested samples "
                 "sat in a user's Library, and reports one row per row of its ne_records table. Source Time (UTC), "
                 "Bundle ID, Group ID and Document ID come from the sources row the record's source_id references, "
                 "the table's own definition tying the two: they are that row's seconds_from_1970, read as seconds "
                 "since 1970 as the column is named and as the cited post's query reads it, and its bundle_id, "
                 "group_id and doc_id. What the time marks is not established here, and a record whose source row is "
                 "missing has those four cells empty. Name is the record's name, Category, Language and Algorithm "
                 "its category, language and algorithm, and Initial Score, Decay Rate, Sentiment Score, Impression "
                 "Count and Occurrences in Source the columns of those names, all as stored; what the category "
                 "numbers stand for is not sourced here. Remote and Sync Eligible are is_remote and is_sync_eligible "
                 "as stored, Extraction OS Build is extraction_os_build and Record ID the row's id. What the numbers "
                 "of Algorithm, Initial Score and Decay Rate stand for is not sourced here. The cited post, written "
                 "about the same database on iOS, says it aggregates data from many sources and that attribution "
                 "must be done carefully: a row ties the record to a source row carrying that bundle ID, and does "
                 "not show that the user wrote, searched for or visited the item (Reference: @bizzybarney, 'A Peek "
                 "Inside the PPSQLDatabase.db Personalization Portrait Database', guest post on mac4n6.com, "
                 "https://www.mac4n6.com/blog/2020/6/2/guest-post-by-bizzybarney-a-peek-inside-the-ppsqldatabasedb-personalization-portrait-database). "
                 "When an extraction holds the database under Users and under System/Volumes/Data or "
                 "System/Volumes/Update/mnt1 with identical bytes it is read once, and when the copies differ a "
                 "record both hold is reported once with both files in Source File. dleapp_macos_bigsur (macOS "
                 "11.2.1) gives 207 rows from 8 bundle identifiers, with source times from 2020-12-12 to 2021-02-19; "
                 "10 rows have Remote 1 and an Extraction OS Build that starts with iOS, and Decay Rate held one "
                 "value, 0.0, on all 207 rows. magnet2021_macos_bigsur (macOS 11.2.1) gives 415 rows, the extraction "
                 "holding three copies of the database, two byte-identical and one whose -wal file differs, and "
                 "every record being held by both copies read and reported once; Decay Rate, Sentiment Score, Remote "
                 "and Extraction OS Build each held one value on all 415 rows. mvs2026_macbookpro_macos15 (macOS "
                 "15.4) gives 1,337 rows, likewise from two differing copies; Language, Initial Score, Decay Rate, "
                 "Remote and Extraction OS Build each held one value on all 1,337 rows. Source File held one value "
                 "on every row of each sample, a file or the same pair of files. Not exercised on real data: a "
                 "record with no source row and more than one user, which were tested with constructed input.",
        "paths": ("*/Library/PersonalizationPortrait/PPSQLDatabase.db*",),
        "output_types": "standard",
        "artifact_icon": "tag",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 207 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 415 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1337 rows",
        },
    },
    "macosPortraitTopics": {
        "name": "Personalization Portrait - Topics",
        "description": "Topic records of PPSQLDatabase.db, one row per record, with the bundle ID, group ID, "
                       "document ID and time of the source row each record references.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Personalization Portrait (macOS)",
        "notes": "Reads PPSQLDatabase.db in a Library/PersonalizationPortrait folder, which in the tested samples "
                 "sat in a user's Library, and reports one row per row of its tp_records table. Source Time (UTC), "
                 "Bundle ID, Group ID and Document ID come from the sources row the record's source_id references, "
                 "the table's own definition tying the two: they are that row's seconds_from_1970, read as seconds "
                 "since 1970 as the column is named and as the cited post's query reads it, and its bundle_id, "
                 "group_id and doc_id. What the time marks is not established here, and a record whose source row is "
                 "missing has those four cells empty. Topic ID is the record's topic_id as stored; on every tested "
                 "row it is the letter Q and a number, and what catalogue the identifier belongs to is not sourced "
                 "here. Algorithm, Initial Score, Decay Rate, Sentiment Score, Impression Count and Occurrences in "
                 "Source are the columns of those names, and Exact Match in Source Text, Result Position and Result "
                 "Count are exact_match_in_source_text, algorithm_result_position and algorithm_result_count, all as "
                 "stored. Remote and Sync Eligible are is_remote and is_sync_eligible as stored, Extraction OS Build "
                 "is extraction_os_build and Record ID the row's id. What the numbers of Algorithm, Initial Score "
                 "and Decay Rate stand for is not sourced here. The cited post, written about the same database on "
                 "iOS, says it aggregates data from many sources and that attribution must be done carefully: a row "
                 "ties the record to a source row carrying that bundle ID, and does not show that the user wrote, "
                 "searched for or visited the item (Reference: @bizzybarney, 'A Peek Inside the PPSQLDatabase.db "
                 "Personalization Portrait Database', guest post on mac4n6.com, "
                 "https://www.mac4n6.com/blog/2020/6/2/guest-post-by-bizzybarney-a-peek-inside-the-ppsqldatabasedb-personalization-portrait-database). "
                 "When an extraction holds the database under Users and under System/Volumes/Data or "
                 "System/Volumes/Update/mnt1 with identical bytes it is read once, and when the copies differ a "
                 "record both hold is reported once with both files in Source File. dleapp_macos_bigsur (macOS "
                 "11.2.1) gives 60 rows with source times from 2021-02-15 to 2021-02-19; Decay Rate, Sentiment "
                 "Score, Occurrences in Source and Remote each held one value on all 60 rows. "
                 "magnet2021_macos_bigsur (macOS 11.2.1) gives 146 rows, the extraction holding three copies of the "
                 "database, two byte-identical and one whose -wal file differs, and every record being held by both "
                 "copies read and reported once; Decay Rate, Sentiment Score, Occurrences in Source, Remote and "
                 "Extraction OS Build each held one value on all 146 rows. mvs2026_macbookpro_macos15 (macOS 15.4) "
                 "gives 161 rows, likewise from two differing copies; Decay Rate, Sentiment Score, Impression Count, "
                 "Occurrences in Source, Remote and Extraction OS Build each held one value on all 161 rows. Source "
                 "File held one value on every row of each sample, a file or the same pair of files. Not exercised "
                 "on real data: a record with no source row and more than one user, which were tested with "
                 "constructed input.",
        "paths": ("*/Library/PersonalizationPortrait/PPSQLDatabase.db*",),
        "output_types": "standard",
        "artifact_icon": "hash",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 60 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 146 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 161 rows",
        },
    },
    "macosPortraitLocations": {
        "name": "Personalization Portrait - Locations",
        "description": "Location records of PPSQLDatabase.db, one row per record, with the bundle ID, group ID, "
                       "document ID and time of the source row each record references.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Personalization Portrait (macOS)",
        "notes": "Reads PPSQLDatabase.db in a Library/PersonalizationPortrait folder, which in the tested samples "
                 "sat in a user's Library, and reports one row per row of its loc_records table. Source Time (UTC), "
                 "Bundle ID, Group ID and Document ID come from the sources row the record's source_id references, "
                 "the table's own definition tying the two: they are that row's seconds_from_1970, read as seconds "
                 "since 1970 as the column is named and as the cited post's query reads it, and its bundle_id, "
                 "group_id and doc_id. What the time marks is not established here, and a record whose source row is "
                 "missing has those four cells empty. Latitude and Longitude are cll_latitude_degrees and "
                 "cll_longitude_degrees, and Name, Street Number, Road, Sub-locality, City, Sub-administrative Area, "
                 "Administrative Area, Postal Code, Country Code and Country are clp_name, clp_subThoroughfare, "
                 "clp_thoroughfare, clp_subLocality, clp_locality, clp_subAdministrativeArea, "
                 "clp_administrativeArea, clp_postalCode, clp_ISOcountryCode and clp_country; Description is "
                 "lc_description and Category and Algorithm are category and algorithm, all as stored. "
                 "lc_description was lowercase text on every tested row, and on mvs2026_macbookpro_macos15 it "
                 "equalled the lowercased Name on all 376 rows. A record with no latitude or longitude has those "
                 "cells empty and is left out of the KML file. Remote and Sync Eligible are is_remote and "
                 "is_sync_eligible as stored, Extraction OS Build is extraction_os_build and Record ID the row's id. "
                 "What the numbers of Algorithm, Initial Score and Decay Rate stand for is not sourced here. The "
                 "cited post, written about the same database on iOS, says it aggregates data from many sources and "
                 "that attribution must be done carefully: a row ties the record to a source row carrying that "
                 "bundle ID, and does not show that the user wrote, searched for or visited the item (Reference: "
                 "@bizzybarney, 'A Peek Inside the PPSQLDatabase.db Personalization Portrait Database', guest post "
                 "on mac4n6.com, "
                 "https://www.mac4n6.com/blog/2020/6/2/guest-post-by-bizzybarney-a-peek-inside-the-ppsqldatabasedb-personalization-portrait-database). "
                 "When an extraction holds the database under Users and under System/Volumes/Data or "
                 "System/Volumes/Update/mnt1 with identical bytes it is read once, and when the copies differ a "
                 "record both hold is reported once with both files in Source File. The post adds that a location "
                 "record does not mean the device was at that place at that time. dleapp_macos_bigsur (macOS 11.2.1) "
                 "gives 17 rows, 9 with a latitude and longitude and 8 with a Name; City, Administrative Area, "
                 "Remote and Sync Eligible each held one value on all 17 rows. magnet2021_macos_bigsur (macOS "
                 "11.2.1) gives 99 rows, 96 with a latitude and longitude, the extraction holding three copies of "
                 "the database, two byte-identical and one whose -wal file differs, and every record being held by "
                 "both copies read and reported once; Category, Remote, Sync Eligible and Extraction OS Build each "
                 "held one value on all 99 rows. mvs2026_macbookpro_macos15 (macOS 15.4) gives 376 rows, likewise "
                 "from two differing copies, every one with a Name and none with coordinates or address parts: "
                 "Latitude, Longitude, Street Number, Road, Sub-locality, City, Sub-administrative Area, "
                 "Administrative Area, Postal Code, Country Code and Country are empty on all 376 rows, and "
                 "Algorithm, Initial Score, Decay Rate, Remote, Sync Eligible and Extraction OS Build each held one "
                 "value on all 376. Source File held one value on every row of each sample, a file or the same pair "
                 "of files. Not exercised on real data: a record with no source row and more than one user, which "
                 "were tested with constructed input.",
        "paths": ("*/Library/PersonalizationPortrait/PPSQLDatabase.db*",),
        "output_types": ["html", "tsv", "timeline", "lava", "kml"],
        "artifact_icon": "map-pin",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 17 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 99 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 376 rows",
        },
    },
}

import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import fold_view_rows, unique_sources

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SOURCE = 'sources.seconds_from_1970, sources.bundle_id, sources.group_id, sources.doc_id'
ENTITIES = (f'SELECT {_SOURCE}, r.name, r.category, r.language, r.algorithm, r.initial_score, r.decay_rate, '
            'r.sentiment_score, r.impression_count, r.occurrences_in_source, r.is_remote, r.is_sync_eligible, '
            'r.extraction_os_build, r.id FROM ne_records r LEFT JOIN sources ON sources.id = r.source_id ORDER BY r.id')
TOPICS = (f'SELECT {_SOURCE}, r.topic_id, r.algorithm, r.initial_score, r.decay_rate, r.sentiment_score, '
          'r.impression_count, r.occurrences_in_source, r.exact_match_in_source_text, r.algorithm_result_position, '
          'r.algorithm_result_count, r.is_remote, r.is_sync_eligible, r.extraction_os_build, r.id '
          'FROM tp_records r LEFT JOIN sources ON sources.id = r.source_id ORDER BY r.id')
LOCATIONS = (f'SELECT {_SOURCE}, r.cll_latitude_degrees, r.cll_longitude_degrees, r.clp_name, r.clp_subThoroughfare, '
             'r.clp_thoroughfare, r.clp_subLocality, r.clp_locality, r.clp_subAdministrativeArea, '
             'r.clp_administrativeArea, r.clp_postalCode, r.clp_ISOcountryCode, r.clp_country, r.lc_description, '
             'r.category, r.algorithm, r.initial_score, r.decay_rate, r.is_remote, r.is_sync_eligible, '
             'r.extraction_os_build, r.id FROM loc_records r LEFT JOIN sources ON sources.id = r.source_id ORDER BY r.id')


def utc_from_seconds(value):
    """The UTC time of a count of seconds since 1970, or '' for no value and for anything that is not a number."""
    if value is None or isinstance(value, (bytes, bool)):
        return ''
    try:
        return _EPOCH + timedelta(seconds=float(value))
    except (ValueError, OverflowError):
        return ''


def _rows(context, label, query):
    """The rows of one query from every PPSQLDatabase.db found, the source's time first and the file's path
    last, and the databases that gave rows. A database held with identical bytes under two volume views is read
    once, and a record that differing copies under two views both hold is reported once, naming both files."""
    found = [str(p) for p in context.get_files_found() if str(p).replace('\\', '/').endswith('/PPSQLDatabase.db')]
    data_list, read, counts = [], [], Counter()
    for path in sorted(unique_sources(context, found, sidecars=('-wal',), label=label)[0]):
        database = open_sqlite_db_readonly(path)
        if database is None:
            counts['databases that could not be opened'] += 1
            continue
        try:
            rows = database.execute(query).fetchall()
        except sqlite3.Error as error:
            counts[f'databases that could not be read ({type(error).__name__})'] += 1
            continue
        finally:
            database.close()
        relative = context.get_relative_path(path)
        data_list.extend((utc_from_seconds(row[0]),) + tuple(row[1:]) + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc(label + ': ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosPortraitNamedEntities(context):
    data_headers = (('Source Time (UTC)', 'datetime'), 'Bundle ID', 'Group ID', 'Document ID', 'Name',
                    'Category (as stored)', 'Language', 'Algorithm (as stored)', 'Initial Score', 'Decay Rate',
                    'Sentiment Score', 'Impression Count', 'Occurrences in Source', 'Remote', 'Sync Eligible',
                    'Extraction OS Build', 'Record ID', 'Source File')
    data_list, located = _rows(context, 'Personalization Portrait - Named Entities', ENTITIES)
    return data_headers, data_list, located


@artifact_processor
def macosPortraitTopics(context):
    data_headers = (('Source Time (UTC)', 'datetime'), 'Bundle ID', 'Group ID', 'Document ID', 'Topic ID',
                    'Algorithm (as stored)', 'Initial Score', 'Decay Rate', 'Sentiment Score', 'Impression Count',
                    'Occurrences in Source', 'Exact Match in Source Text', 'Result Position', 'Result Count',
                    'Remote', 'Sync Eligible', 'Extraction OS Build', 'Record ID', 'Source File')
    data_list, located = _rows(context, 'Personalization Portrait - Topics', TOPICS)
    return data_headers, data_list, located


@artifact_processor
def macosPortraitLocations(context):
    data_headers = (('Source Time (UTC)', 'datetime'), 'Bundle ID', 'Group ID', 'Document ID', 'Latitude',
                    'Longitude', 'Name', 'Street Number', 'Road', 'Sub-locality', 'City', 'Sub-administrative Area',
                    'Administrative Area', 'Postal Code', 'Country Code', 'Country', 'Description',
                    'Category (as stored)', 'Algorithm (as stored)', 'Initial Score', 'Decay Rate', 'Remote',
                    'Sync Eligible', 'Extraction OS Build', 'Record ID', 'Source File')
    data_list, located = _rows(context, 'Personalization Portrait - Locations', LOCATIONS)
    return data_headers, data_list, located
