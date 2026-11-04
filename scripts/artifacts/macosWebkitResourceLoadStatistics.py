"""WebKit Intelligent Tracking Prevention domain statistics and relationships on macOS.

Ported from iLEAPP's webkitResourceLoadStatistics.py (@ForensikITGmbH), with macOS paths and owners."""

__artifacts_v2__ = {
    'macosWebkitObservedDomains': {
        'name': 'WebKit - Observed Domains (macOS)',
        'description': 'Observed domain statistics from each observations.db in a user\'s WebKit website data.',
        'author': '@ForensikITGmbH, @AlexisBrignoni, Claude',
        'creation_date': '2026-10-30', 'last_update_date': '2026-10-30',
        'requirements': 'none', 'category': 'Browser (macOS)',
        'notes': "Ported from iLEAPP's WebKit tracking-prevention artifacts (@ForensikITGmbH), with macOS "
                 "paths and owners. These are WebKit tracking-prevention statistics, not a complete "
                 "browsing history. A domain may be observed as a subresource. Interaction flags do not "
                 "establish a particular link click. Zero, negative and invalid time values remain in "
                 "Stored Values and are not rendered as dates. Database reads include acquired WAL files. "
                 "User is the folder after Users in the path, or root for a store under private/var/root. "
                 "Owner (from path) is the folder after Library/Containers/ (a sandboxed app's container) "
                 "or after Library/WebKit/, which WebKit names from the app's bundle identifier, or from "
                 "its process name when the app has none (WebsiteDataStoreCocoa.mm, "
                 "applicationOrProcessIdentifier, at the commit below); it is read from the path, not "
                 "from app metadata, and is blank when neither is present. On the tested images Safari's "
                 "store sat in Library/Containers/com.apple.Safari, and the other stores sat under "
                 "Library/Containers/<folder> or Library/WebKit/<folder>; a store with no ObservedDomains "
                 "rows can still contribute Operating Dates rows. When a logical extraction holds the "
                 "same file under Users/ and under System/Volumes/Data/Users/ or "
                 "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run "
                 "log counts it. On the tested images lastSeen was 0 on 7 of the 530 rows, "
                 "mostRecentUserInteractionTime was -1 on 502, and Most Recent Web Push Interaction held "
                 "no value on any row: mostRecentWebPushInteractionTime was 0 on all 312 rows whose store "
                 "has that column, and the other stores lack it. On each tested image the row count "
                 "equalled the ObservedDomains row count of the stores read. Source: "
                 "https://github.com/WebKit/WebKit/blob/47b1bf884eb5adb28e9f3316c4930f5367bac470/Source/WebKit/NetworkProcess/Classifier/ResourceLoadStatisticsStore.cpp",
        'paths': ('*/ResourceLoadStatistics/observations.db*',),
        'output_types': 'standard', 'artifact_icon': 'world',
        'sample_data': {
            'magnet2021_macos_bigsur': 'macOS 11.2.1 | 218 rows',
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 300 rows',
            'roblox_macos': 'macOS 26.5.2 | 12 rows',
        },
    },
    'macosWebkitOperatingDates': {
        'name': 'WebKit - Operating Dates (macOS)',
        'description': 'Calendar dates retained by each WebKit statistics store in a user\'s WebKit website data.',
        'author': '@ForensikITGmbH, @AlexisBrignoni, Claude',
        'creation_date': '2026-10-30', 'last_update_date': '2026-10-30',
        'requirements': 'none', 'category': 'Browser (macOS)',
        'notes': "Ported from iLEAPP's WebKit tracking-prevention artifacts (@ForensikITGmbH), with macOS "
                 "paths and owners. These are WebKit tracking-prevention statistics, not a complete "
                 "browsing history. A domain may be observed as a subresource. Interaction flags do not "
                 "establish a particular link click. Zero, negative and invalid time values remain in "
                 "Stored Values and are not rendered as dates. Database reads include acquired WAL files. "
                 "User is the folder after Users in the path, or root for a store under private/var/root. "
                 "Owner (from path) is the folder after Library/Containers/ (a sandboxed app's container) "
                 "or after Library/WebKit/, which WebKit names from the app's bundle identifier, or from "
                 "its process name when the app has none (WebsiteDataStoreCocoa.mm, "
                 "applicationOrProcessIdentifier, at the commit below); it is read from the path, not "
                 "from app metadata, and is blank when neither is present. On the tested images Safari's "
                 "store sat in Library/Containers/com.apple.Safari, and the other stores sat under "
                 "Library/Containers/<folder> or Library/WebKit/<folder>; a store with no ObservedDomains "
                 "rows can still contribute Operating Dates rows. When a logical extraction holds the "
                 "same file under Users/ and under System/Volumes/Data/Users/ or "
                 "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run "
                 "log counts it. OperatingDates.month is zero-based: OperatingDate::fromWallTime takes it "
                 "from WTF's monthFromDayInYear, which returns 0 to 11 "
                 "(https://github.com/WebKit/WebKit/blob/47b1bf884eb5adb28e9f3316c4930f5367bac470/Source/WTF/wtf/DateMath.h); "
                 "iLEAPP's tested images stored months 0 to 11, and the tested macOS images stored 1, 2, "
                 "6, 10 and 11. Dates are date-only values with no time. WebKit derives them from the UTC "
                 "wall clock (OperatingDate::fromWallTime), so a date near local midnight can differ from "
                 "the local date on the device. They do not prove foreground app use. All 37 tested rows "
                 "were valid dates. Source: "
                 "https://github.com/WebKit/WebKit/blob/47b1bf884eb5adb28e9f3316c4930f5367bac470/Source/WebKit/NetworkProcess/Classifier/ResourceLoadStatisticsStore.cpp",
        'paths': ('*/ResourceLoadStatistics/observations.db*',),
        'output_types': 'standard', 'artifact_icon': 'calendar',
        'sample_data': {
            'magnet2021_macos_bigsur': 'macOS 11.2.1 | 6 rows',
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 30 rows',
            'roblox_macos': 'macOS 26.5.2 | 1 row',
        },
    },
    'macosWebkitDomainRelationships': {
        'name': 'WebKit - Domain Relationships (macOS)',
        'description': 'Domain references in WebKit statistics tables, resolved using declared foreign keys to '
                       'ObservedDomains while retaining original fields.',
        'author': '@ForensikITGmbH, @AlexisBrignoni, Claude',
        'creation_date': '2026-10-30', 'last_update_date': '2026-10-30',
        'requirements': 'none', 'category': 'Browser (macOS)',
        'notes': "Ported from iLEAPP's WebKit tracking-prevention artifacts (@ForensikITGmbH), with macOS "
                 "paths and owners. These are WebKit tracking-prevention statistics, not a complete "
                 "browsing history. A domain may be observed as a subresource. Interaction flags do not "
                 "establish a particular link click. Zero, negative and invalid time values remain in "
                 "Stored Values and are not rendered as dates. Database reads include acquired WAL files. "
                 "User is the folder after Users in the path, or root for a store under private/var/root. "
                 "Owner (from path) is the folder after Library/Containers/ (a sandboxed app's container) "
                 "or after Library/WebKit/, which WebKit names from the app's bundle identifier, or from "
                 "its process name when the app has none (WebsiteDataStoreCocoa.mm, "
                 "applicationOrProcessIdentifier, at the commit below); it is read from the path, not "
                 "from app metadata, and is blank when neither is present. On the tested images Safari's "
                 "store sat in Library/Containers/com.apple.Safari, and the other stores sat under "
                 "Library/Containers/<folder> or Library/WebKit/<folder>; a store with no ObservedDomains "
                 "rows can still contribute Operating Dates rows. When a logical extraction holds the "
                 "same file under Users/ and under System/Volumes/Data/Users/ or "
                 "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run "
                 "log counts it. A table is read when a declared foreign key points at ObservedDomains. "
                 "Last Updated is blank for tables that have no lastUpdated column (five of the nine "
                 "seen). On the tested images the rows came from SubresourceUnderTopFrameDomains, "
                 "TopFrameLoadedThirdPartyScripts, SubresourceUniqueRedirectsFrom, "
                 "SubresourceUniqueRedirectsTo, SubframeUnderTopFrameDomains, "
                 "TopFrameUniqueRedirectsFrom, TopFrameUniqueRedirectsTo, "
                 "TopFrameUniqueRedirectsToSinceSameSiteStrictEnforcement and "
                 "TopFrameLinkDecorationsFrom. Source: "
                 "https://github.com/WebKit/WebKit/blob/47b1bf884eb5adb28e9f3316c4930f5367bac470/Source/WebKit/NetworkProcess/Classifier/ResourceLoadStatisticsStore.cpp",
        'paths': ('*/ResourceLoadStatistics/observations.db*',),
        'output_types': 'standard', 'artifact_icon': 'arrows-exchange',
        'sample_data': {
            'magnet2021_macos_bigsur': 'macOS 11.2.1 | 734 rows',
            'mvs2026_macbookpro_macos15': 'macOS 15.4 | 677 rows',
            'roblox_macos': 'macOS 26.5.2 | 20 rows',
        },
    },
}

import json
import math
import os
import re
from datetime import date, datetime, timezone

from scripts.ilapfuncs import artifact_processor, get_sqlite_db_records
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'WebKit Resource Load Statistics'
# ~/Library/WebKit/<bundle>/WebsiteData/... and ~/Library/Containers/<bundle>/Data/Library/WebKit/...
_WEBKIT_OWNER = re.compile(r'/Library/WebKit/([^/]+)/WebsiteData/')
_CONTAINER_OWNER = re.compile(r'/Library/Containers/([^/]+)/Data/')
OWNER_HEADERS = ('User', 'Owner (from path)')


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def _json_value(value):
    if isinstance(value, bytes):
        return {'hex': value.hex()}
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _stored_values(row):
    return json.dumps({key: _json_value(row[key]) for key in row.keys()},
                      ensure_ascii=False, sort_keys=True, allow_nan=False)


def _unix(value):
    """UTC for positive, finite Unix seconds; None otherwise (the value stays in Stored Values)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _owner(relative):
    path = '/' + relative.replace('\\', '/').lstrip('/')
    match = _CONTAINER_OWNER.search(path) or _WEBKIT_OWNER.search(path)
    return (user_from_path(relative), match.group(1) if match else '')


def _get(row, field):
    fields = {key.lower(): key for key in row.keys()}
    key = fields.get(field.lower())
    return row[key] if key is not None else None


def _databases(context):
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'observations.db']
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        tables = {row['name'].lower(): row['name'] for row in get_sqlite_db_records(
            path, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        yield path, relative, tables, _owner(relative)


@artifact_processor
def macosWebkitObservedDomains(context):
    headers = (
        ('Last Seen', 'datetime'), ('Most Recent User Interaction', 'datetime'),
        ('Most Recent Web Push Interaction', 'datetime'), 'Domain', 'Domain ID',
        'Had User Interaction', 'Is Prevalent', 'Is Very Prevalent', 'Grandfathered',
        'Data Records Removed', 'First Party Accesses Due To User Interaction',
        'First Party Accesses Due To Storage Access API', 'Scheduled For All-But-Cookie Data Removal',
    ) + OWNER_HEADERS + ('Stored Values', 'Source File')
    rows, read = [], []
    for path, relative, tables, owner in _databases(context):
        table = tables.get('observeddomains')
        if not table:
            continue
        read.append(path)
        for row in get_sqlite_db_records(path, f'SELECT * FROM {_quote(table)}'):
            rows.append((
                _unix(_get(row, 'lastSeen')), _unix(_get(row, 'mostRecentUserInteractionTime')),
                _unix(_get(row, 'mostRecentWebPushInteractionTime')),
                _get(row, 'registrableDomain'), _get(row, 'domainID'),
                _get(row, 'hadUserInteraction'), _get(row, 'isPrevalent'), _get(row, 'isVeryPrevalent'),
                _get(row, 'grandfathered'), _get(row, 'dataRecordsRemoved'),
                _get(row, 'timesAccessedAsFirstPartyDueToUserInteraction'),
                _get(row, 'timesAccessedAsFirstPartyDueToStorageAccessAPI'),
                _get(row, 'isScheduledForAllButCookieDataRemoval'),
            ) + owner + (_stored_values(row), relative))
    return headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosWebkitOperatingDates(context):
    headers = (('Operating Date', 'date'), 'Year', 'Month (Zero-Based)', 'Month Day', 'Date Status') \
        + OWNER_HEADERS + ('Stored Values', 'Source File')
    rows, read = [], []
    for path, relative, tables, owner in _databases(context):
        table = tables.get('operatingdates')
        if not table:
            continue
        read.append(path)
        for row in get_sqlite_db_records(path, f'SELECT * FROM {_quote(table)}'):
            year, month, day = (_get(row, field) for field in ('year', 'month', 'monthDay'))
            converted = None
            try:
                if all(isinstance(value, int) and not isinstance(value, bool) for value in (year, month, day)):
                    converted = date(year, month + 1, day)
            except ValueError:
                pass
            rows.append((converted, year, month, day, 'Valid' if converted else 'Invalid stored date')
                        + owner + (_stored_values(row), relative))
    return headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosWebkitDomainRelationships(context):
    headers = (('Last Updated', 'datetime'), 'Relationship Table', 'Domain 1 Field', 'Domain 1',
               'Domain 2 Field', 'Domain 2', 'Resolved Domain Fields') \
        + OWNER_HEADERS + ('Stored Values', 'Source File')
    rows, read = [], []
    for path, relative, tables, owner in _databases(context):
        observed = tables.get('observeddomains')
        if not observed:
            continue
        domains = {_get(row, 'domainID'): _get(row, 'registrableDomain')
                   for row in get_sqlite_db_records(path, f'SELECT * FROM {_quote(observed)}')}
        used = False
        for table in sorted(tables.values()):
            if table.lower() in ('observeddomains', 'operatingdates'):
                continue
            references = {row['from'] for row in get_sqlite_db_records(path, f'PRAGMA foreign_key_list({_quote(table)})')
                          if row['table'].lower() == 'observeddomains'
                          and (row['to'] is None or row['to'].lower() == 'domainid')}
            if not references:
                continue
            used = True
            for row in get_sqlite_db_records(path, f'SELECT * FROM {_quote(table)}'):
                resolved = {key: domains.get(row[key]) for key in row.keys() if key in references}
                fields = list(resolved)
                pairs = tuple(value for key in fields[:2] for value in (key, resolved[key]))
                pairs += ('',) * (4 - len(pairs))
                rows.append((_unix(_get(row, 'lastUpdated')), table) + pairs
                            + (json.dumps(resolved, ensure_ascii=False, sort_keys=True),)
                            + owner + (_stored_values(row), relative))
        if used:
            read.append(path)
    return headers, fold_view_rows(rows), '\n'.join(read)
