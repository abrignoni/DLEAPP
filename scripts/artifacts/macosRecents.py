"""Recent contacts macOS keeps for its apps (the CoreRecents database), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosRecents": {
        "name": "Recents (CoreRecents)",
        "description": "Recent contacts the system keeps per app bundle identifier (com.apple.mail, "
                       "com.apple.messages, com.apple.eventkit.osx and com.apple.passbook in the tested samples), "
                       "one row per contact of a recent entry: the app, the dates stored with the entry, the "
                       "contact's address and name, and the details stored with it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-11",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Recents (macOS)",
        "notes": "Reads the Recents database in the com.apple.corerecents.recentsd container of each user, a SQLite "
                 "database with the tables recents, contacts and metadata, the last two tied to a recents row by "
                 "their recent_id column in the tables' own definitions. One row is reported per contacts row of an "
                 "entry, and one for an entry with no contact. Last Date (UTC) is recents.last_date and Dates (UTC) "
                 "every value of recents.dates, both read as milliseconds since 1970: no Apple description of the "
                 "columns was found, a public query for the same database on iOS reads them that way "
                 "(https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/recents.sql, "
                 "lines 12 and 13), and under that reading every tested value falls in 2020 or 2021 on the first "
                 "sample and in 2025 on the second. The dates of an entry are separated by colons in both tested "
                 "databases; a comma, the separator the iLEAPP module for the iOS database splits on, is accepted "
                 "too. A value of dates that is not a number is left out, a last_date that is not a number leaves "
                 "Last Date (UTC) empty, and both are counted in the run log. App is recents.bundle_identifier, "
                 "Entry Name recents.display_name, Sending Address, Original Source, Count, Weight and Group Kind "
                 "the recents columns of those names, and Recent ID the row's ROWID. Contact Kind, Contact Address "
                 "and Contact Name are the kind, address and display_name of the contacts row. Metadata is every "
                 "metadata row of the entry as key=value: a value stored as a binary property list is shown as the "
                 "value it holds, and bytes, also inside such a value, in hexadecimal. Latitude and Longitude are "
                 "the metadata values with those keys, when the entry has them. What Count, Weight, Group Kind and "
                 "Original Source record is not sourced here, and they are shown as stored. A contacts or metadata "
                 "row with no recents row is not reported; neither tested database holds one. The properties table "
                 "and recents.record_hash are not read. When an extraction holds the same database, with its -wal "
                 "file, under Users and under System/Volumes/Data/Users with identical bytes, it is read once, and "
                 "the run log says so; when the copies differ, a record both hold is reported once, with both files "
                 "in Source File, and a record one copy holds twice stays twice, cases tested with constructed "
                 "input. On dleapp_macos_bigsur (macOS 11.2.1) the 5 rows are 5 entries with one contact each: one "
                 "of com.apple.mail and one of com.apple.messages, each with a Sending Address, one of "
                 "com.apple.eventkit.osx whose contact is a map location, with a Latitude and a Longitude from its 7 "
                 "metadata values, and two of com.apple.passbook with Weight 10.0 and 5 metadata values each. "
                 "Contact Kind is email on 2 rows, phone on 2 and map-location on 1. The Messages entry has 5 dates "
                 "and the others 1, and on every row Last Date (UTC) is the latest of its Dates (UTC). In both "
                 "images the rows are in the database's write-ahead log: the database file read without its -wal "
                 "file has no recents table. On mvs2026_macbookpro_macos15 (macOS 15.4) the 3 rows are one entry "
                 "each of com.apple.passbook, com.apple.messages, with 5 dates, and com.apple.mail; the extraction "
                 "holds the database under both paths and it is read once; Latitude and Longitude are empty on all 3 "
                 "rows. On both, Entry Name and Contact Name are identical on every row (both empty on one row of "
                 "the second sample), each entry having one contact, and Count, Group Kind and Source File each held "
                 "one value on every row, 1, 0 and the one database. Not exercised on real data: an entry with "
                 "several contacts or with none, a comma between dates, a date that is not a number, a metadata "
                 "value that is not a property list or that holds a dictionary or an array, copies of the database "
                 "under the two paths that differ, and more than one user, which were tested with constructed input. "
                 "A row shows that the database holds the contact under that app identifier with those dates; what "
                 "the dates record is not sourced here, and a row does not show what was sent or to whom it was "
                 "delivered.",
        "paths": ("*/Library/Containers/com.apple.corerecents.recentsd/Data/Library/Recents/Recents*",),
        "output_types": "standard",
        "artifact_icon": "users",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 5 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 3 rows",
        },
    },
}

import plistlib
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import fold_view_rows, unique_sources

_LABEL = 'Recents (CoreRecents)'
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
# the dates of an entry are separated by colons in the macOS samples; the iLEAPP module for iOS splits on commas
_DATE_SEPARATOR = re.compile(r'[:,]')
_QUERY = '''
    SELECT recents.ROWID, recents.last_date, recents.dates, recents.bundle_identifier, recents.display_name,
           contacts.kind, contacts.address, contacts.display_name, recents.sending_address,
           recents.original_source, recents.count, recents.weight, recents.group_kind
    FROM recents LEFT JOIN contacts ON contacts.recent_id = recents.ROWID
    ORDER BY recents.ROWID, contacts.ROWID
'''


def utc_from_milliseconds(value):
    """The UTC time of a count of milliseconds since 1970, or '' for anything that is not such a number."""
    try:
        return _EPOCH + timedelta(milliseconds=float(str(value).strip()))
    except (ValueError, OverflowError):
        return ''


def all_dates(text):
    """Every date of a list of millisecond counts, separated by colons or commas, that converts, in the list's
    order, joined with ' | ', and how many items did not convert."""
    shown, failed = [], 0
    for item in _DATE_SEPARATOR.split(str(text or '')):
        if not item.strip():
            continue
        when = utc_from_milliseconds(item)
        if when == '':
            failed += 1
        else:
            shown.append(when.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    return ' | '.join(shown), failed


def metadata_value(value):
    """A metadata value as text: a binary property list is shown as the value it holds, bytes inside it, at any
    depth, and bytes that are not a property list in hexadecimal, anything else as stored."""
    if isinstance(value, bytes):
        try:
            value = _plain(plistlib.loads(value))
        except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError, RecursionError):
            return value.hex()
    return '' if value is None else str(value)


def _plain(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def recents_rows(database, counts):
    """The rows for one open Recents database."""
    details = {}
    for recent_id, key, value in database.execute('SELECT recent_id, key, value FROM metadata ORDER BY ROWID'):
        details.setdefault(recent_id, []).append((str(key), metadata_value(value)))
    rows = []
    for (recent_id, last_date, dates, bundle, name, kind, address, contact_name, sending, source, count, weight,
         group_kind) in database.execute(_QUERY):
        shown, failed = all_dates(dates)
        if failed:
            counts['dates that are not a number, left out of Dates (UTC)'] += failed
        metadata = details.get(recent_id, [])
        found = dict(metadata)
        last = utc_from_milliseconds(last_date)
        if last == '' and last_date is not None:
            counts['last dates that are not a number, Last Date (UTC) left blank'] += 1
        rows.append((last, shown, bundle, name, kind,
                     address, contact_name, sending, source, count, weight, group_kind,
                     found.get('latitude', ''), found.get('longitude', ''),
                     ' | '.join(f'{key}={value}' for key, value in metadata), recent_id))
    return rows


@artifact_processor
def macosRecents(context):
    data_headers = (('Last Date (UTC)', 'datetime'), 'Dates (UTC)', 'App', 'Entry Name', 'Contact Kind',
                    'Contact Address', 'Contact Name', 'Sending Address', 'Original Source', 'Count', 'Weight',
                    'Group Kind', 'Latitude', 'Longitude', 'Metadata', 'Recent ID', 'Source File')
    data_list, read, counts = [], [], Counter()
    found = [str(p) for p in context.get_files_found() if str(p).replace('\\', '/').endswith('/Recents/Recents')]
    for path in sorted(unique_sources(context, found, sidecars=('-wal',), label=_LABEL)[0]):
        database = open_sqlite_db_readonly(path)
        if database is None:
            counts['databases that could not be opened'] += 1
            continue
        try:
            rows = recents_rows(database, counts)
        except sqlite3.Error as error:
            counts[f'databases that could not be read ({type(error).__name__})'] += 1
            continue
        finally:
            database.close()
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc(_LABEL + ': ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
