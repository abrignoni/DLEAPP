"""Spotlight store records of files and folders on a macOS volume, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSpotlightStoreFiles": {
        "name": "Spotlight Store Files",
        "description": 'Spotlight store records of files and folders on a macOS volume, with their stored '
                       'content, added, last used and download dates, where-from and received-from details, '
                       'rebuilt path, kind and size.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Spotlight (macOS)",
        "notes": (
            'Reads the Spotlight metadata store in each .Spotlight-V100/Store-V2 folder of a '
            'volume: store.db, .store.db and the dbStr-N.map files beside them, which hold the '
            'attribute tables when a store file names no page for them, as neither store.db nor '
            ".store.db does on either tested image. The reader is DLEAPP's own, written from the "
            'store layout Joachim Metz documents (file header, map, property pages, records and '
            "attribute value types) (Reference: Joachim Metz, 'Apple Spotlight store file "
            "formats', "
            'https://github.com/libyal/dtformats/blob/308ce8c38df2eb95a71b6e832b3f9803f0c4b169/documentation/Apple%20Spotlight%20store%20database%20file%20format.asciidoc), '
            'with three rules measured on the tested stores where that document is silent or '
            'reads differently. Each value of a dbStr-N.map.data file starts with its size as a '
            'little-endian base-128 integer: the dbStr files hold 114 values on '
            'dleapp_macos_bigsur and 132 on the public MacBook Pro logical extraction (macOS '
            '15.4, not a registered corpus key) whose size takes two or more bytes, and each '
            'covers its value exactly only when read that way. A list of integers (value type 7 '
            'with the list bit of the property type set) is prefixed by a size that counts its '
            'values at eight bytes each, although each value is a variable-size integer: read as '
            "a byte count instead, 2 records of the MacBook Pro's store.db stop before their end, "
            'and read as eight bytes per value none does. A localized string is its first '
            'language version that is not empty, and the lists Kind points to hold the version '
            'with no language tag first on every tested store. The reader was compared with '
            'spotlight_parser 1.0.4 '
            '(https://github.com/ydkhatri/spotlight_parser/tree/82e80705b172489180f1a2b8c8681033a0e9c0b1), '
            'run on the same four files: it gives the same records, with the same identifier, '
            'parent, flags and update time on every one, and the same value for every attribute '
            'reported here, 1,897,948 values in all. Both copies are read. On both tested images '
            '.store.db holds the later updates: its newest record update is 2021-02-19 19:53:25 '
            'UTC against 19:23:23 in store.db on dleapp_macos_bigsur, and 2025-12-25 07:06:24 '
            'against 06:41:59 on the MacBook Pro, no record the two share was updated later in '
            'store.db, and the records only store.db holds (109 and 56) were all last updated '
            'before the earliest of those only .store.db holds (155 and 59). Why those records '
            'left the newer copy is not established. A record the two copies hold with the same '
            'values is one row whose Source File lists both, and a record they hold differently '
            'gives a row for each copy: 12,931 of the 13,677 rows on dleapp_macos_bigsur come '
            'from both copies, and 109,159 of the 109,350 on the MacBook Pro. Only a record that '
            'names a file in _kMDItemFileName gives a row, and the records that name none (2 in '
            'each copy on dleapp_macos_bigsur, 14 in each on the MacBook Pro) are counted in the '
            'run log. Path joins the names of the folders above a record, found through the '
            "parent identifier each record stores, and the record's own name. One copy can hold "
            'two records for one identifier (5 identifiers in each copy on dleapp_macos_bigsur, 2 '
            'on the MacBook Pro, where each pair has two different names), and each record gives '
            'a row ending in its own name; if such an identifier were a folder above other '
            'records, the later updated record would name it, a case no tested store holds and a '
            'constructed store tests. A chain that reaches identifier 2 or lower begins with the '
            'part of the path the store records for itself before /.Spotlight-V100, '
            '/System/Volumes/Data on both tested images, and the records whose parent is 2 there '
            'include the folders Users, System, Applications and Library. A chain that reaches an '
            'identifier with no record in the same copy begins with (file ID N) instead, as 2,909 '
            'rows on dleapp_macos_bigsur and 7,303 on the MacBook Pro do. File ID and Parent File '
            "ID are the record's identifier and parent identifier, which the documentation "
            'describes as the file system identifier (for example the CNID on HFS) of the file '
            'and of its parent. Content Modified (UTC), Content Created (UTC), Date Added (UTC), '
            'Last Used (UTC) and Downloaded (UTC) are kMDItemContentModificationDate, '
            'kMDItemContentCreationDate, kMDItemDateAdded, kMDItemLastUsedDate and '
            'kMDItemDownloadedDate, dates the documentation describes as Cocoa timestamps '
            "(seconds since 1 January 2001 UTC), read in UTC. Apple's MDItem.h header describes "
            'the two content dates as having an application specific semantic, the content '
            'modification date as not related to the file system modification date, the date '
            'added as the date the file was moved into its current location, the last used date '
            'as updated by LaunchServices every time a file is opened by double clicking or by '
            'asking LaunchServices to open it, and the downloaded date as the date the file was '
            'last downloaded or received (Reference: Apple, MDItem.h, the Metadata framework '
            'header of the macOS SDK, '
            'System/Library/Frameworks/CoreServices.framework/Frameworks/Metadata.framework/Headers/MDItem.h '
            'in MacOSX26.5.sdk). kMDItemDownloadedDate is a single date on dleapp_macos_bigsur '
            'and a list of one date on the MacBook Pro, and the first date of a list is reported, '
            'so a later date in a longer list would not be. On the MacBook Pro 27 rows hold a '
            'Content Modified (UTC) of 1970-01-01 00:00:00, Unix time 0, as stored. Used Dates '
            '(UTC) lists kMDItemUsedDates one per line, and every one on the tested images falls '
            'exactly on an hour, 05:00 or 07:00 UTC on dleapp_macos_bigsur and 05:00 or 08:00 UTC '
            'on the MacBook Pro, so the time of day of a use is not established from them. Use '
            'Count (as stored) is kMDItemUseCount, and it is not the number of used dates: the '
            'two are equal on 7 of the 22 rows holding both on dleapp_macos_bigsur and on 4 of 24 '
            'on the MacBook Pro. MDItem.h describes neither kMDItemUseCount nor kMDItemUsedDates. '
            'Where From lists kMDItemWhereFroms one entry per line, leaving out empty entries, '
            'and MDItem.h describes it as where the item was obtained from, giving as examples '
            'the site a downloaded file came from or the referring URL, and who sent a file '
            'received by email or the message subject. On dleapp_macos_bigsur 105 of the 109 '
            'records of store.db holding it hold only an empty entry. Received Date (UTC), '
            'Received Sender (as stored), Received Sender Handle (as stored) and Received '
            'Transport (as stored) are kMDItemUserSharedReceivedDate, '
            'kMDItemUserSharedReceivedSender, kMDItemUserSharedReceivedSenderHandle and '
            'kMDItemUserSharedReceivedTransport, lists shown one entry per line, and Origin '
            'Sender (as stored) and Origin Application (as stored) are kMDItemOriginSenderHandle '
            'and kMDItemOriginApplicationIdentifier. MDItem.h describes none of these six; '
            'Received Date (UTC) is converted like the other dates, and the other five are '
            'reported as stored. On dleapp_macos_bigsur 5 rows hold all six, each list with one '
            'entry, all with the transport com.apple.messages and the origin application '
            'com.apple.MobileSMS, and Received Sender Handle (as stored) and Origin Sender (as '
            'stored) hold the same value on each of those rows and are both empty on every other '
            'row. On the MacBook Pro Received Date (UTC), Received Sender (as stored), Received '
            'Sender Handle (as stored) and Received Transport (as stored) are empty on every row, '
            'as its store holds none of those four attributes, and 1 row holds an origin sender '
            "and the origin application com.apple.mail. Record Updated (UTC) is the record's last "
            'update time, which the documentation gives as microseconds since 1 January 1970 and '
            'assumes to be UTC; a value too large for a date is left blank, which no tested store '
            'holds. Read that way, 26 records of store.db on dleapp_macos_bigsur and 472 on the '
            'MacBook Pro were updated less than ten seconds after their content modification '
            'date. Name is _kMDItemFileName, Kind is kMDItemKind, Content Type is '
            'kMDItemContentType, Logical Size (as stored) is kMDItemLogicalSize and Owner UID (as '
            'stored) is _kMDItemOwnerUserID. MDItem.h describes neither of those two names: the '
            'logical size and owner user id it describes are kMDItemFSSize and '
            'kMDItemFSOwnerUserID, other names that no tested store holds. Neither tested image '
            'keeps an attribute table in the pages of store.db or .store.db or compresses a '
            'record page with zlib, so those two paths were tested only on constructed stores, as '
            'were a record page that cannot be read, which is skipped, and a record whose values '
            'cannot all be decoded, which gives a row with the attributes read before the one '
            'that failed; both are counted in the run log. The three Time Machine backups in the '
            'MacBook Pro extraction each hold a store.db and a .store.db made only of zero bytes '
            '(36,864 bytes each in two backups and 16,388,096 in the third, and the CRC-32 the '
            "extraction's zip records for each is that of zeros), which are logged as not a "
            'Spotlight store and give no row. A store file under System/Volumes/Data with the '
            'same bytes as the file at the same path outside it is not read again, as the 6 '
            'copies of those backup files there are. On the MacBook Pro the 109,350 rows exceed '
            'the 50,000-row limit of the HTML report, so the table is left off the HTML page and '
            'is in the TSV, timeline and LAVA outputs. The other attributes of a record, the '
            "store's full-text index files and its content Cache folder, and each user's "
            'CoreSpotlight store are not reported. The four registered Windows disk images and '
            'windows11_arm_parallels hold no .Spotlight-V100 folder.'
        ),
        "paths": ('*/.Spotlight-V100/Store-V2/*/store.db', '*/.Spotlight-V100/Store-V2/*/.store.db',
                  '*/.Spotlight-V100/Store-V2/*/dbStr-*.map.*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 13,677 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import unique_sources
from scripts.macos_powerlog import merge_sources
from scripts.macos_spotlight import Store, StoreError

_COCOA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_STORES = ('store.db', '.store.db')
_ROOT = 2
_DEPTH = 256
_MARKER = '/.Spotlight-V100/'


def _cocoa(value):
    """Cocoa seconds (since 2001-01-01 UTC) as a UTC datetime, from a number or from the first
    value of a list; blank when there is no number."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ''
    try:
        return _COCOA_EPOCH + timedelta(seconds=value)
    except OverflowError:
        return ''


def _unix_micro(value):
    """Microseconds since 1970-01-01 UTC as a UTC datetime; blank when too large for a date."""
    try:
        return _UNIX_EPOCH + timedelta(microseconds=value)
    except OverflowError:
        return ''


def _cocoa_text(value):
    """A date or list of dates as UTC text, one per line."""
    dates = [_cocoa(v) for v in (value if isinstance(value, list) else [value])]
    return '\n'.join(str(d.replace(tzinfo=None)) for d in dates if d != '')


def _text(value):
    """A value as stored, or a list's entries one per line, leaving out empty entries."""
    if value is None:
        return ''
    if isinstance(value, list):
        return '\n'.join(str(v) for v in value if v != '')
    return value


def _locator(items, mount):
    """A function giving a record's path from its identifier, parent and name. The folders above
    it are found through the parent identifier each record stores, and where a copy holds two
    records for one identifier the later updated one names that folder. A chain that reaches the
    volume's root folder (identifier 2 or lower) starts with mount; one that reaches an identifier
    with no record starts with (file ID N)."""
    names = {}
    for item in items:
        name = item.attributes.get('_kMDItemFileName')
        if isinstance(name, str) and (item.identifier not in names or item.updated > names[item.identifier][2]):
            names[item.identifier] = (item.parent, name, item.updated)

    def locate(identifier, parent, name):
        parts, seen = [name], {identifier}
        while True:
            if parent <= _ROOT:
                parts.append(mount)
                break
            if parent in seen or len(parts) >= _DEPTH or parent not in names:
                parts.append(f'(file ID {parent})')
                break
            seen.add(parent)
            parent, name, _updated = names[parent]
            parts.append(name)
        return '/'.join(reversed(parts))
    return locate


@artifact_processor
def macosSpotlightStoreFiles(context):
    data_headers = (('Content Modified (UTC)', 'datetime'), ('Content Created (UTC)', 'datetime'),
                    ('Date Added (UTC)', 'datetime'), ('Last Used (UTC)', 'datetime'), 'Used Dates (UTC)',
                    'Use Count (as stored)', ('Downloaded (UTC)', 'datetime'), 'Where From',
                    'Received Date (UTC)', 'Received Sender (as stored)', 'Received Sender Handle (as stored)',
                    'Received Transport (as stored)', 'Origin Sender (as stored)',
                    'Origin Application (as stored)', ('Record Updated (UTC)', 'datetime'), 'Name', 'Path',
                    'Kind', 'Content Type', 'Logical Size (as stored)', 'Owner UID (as stored)', 'File ID',
                    'Parent File ID', 'Source File')
    files = [str(path) for path in context.get_files_found()
             if os.path.basename(str(path)) in _STORES and os.path.isfile(str(path))]
    paths, _skipped = unique_sources(context, files, label='Spotlight Store Files')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        try:
            store = Store(path)
        except (OSError, StoreError) as error:
            logfunc(f'Spotlight Store Files: {relative} not read: {error}')
            continue
        items = list(store.items())
        if store.unreadable_pages or store.incomplete:
            logfunc(f'Spotlight Store Files: {relative}: {store.unreadable_pages} record page(s) not read, '
                    f'{store.incomplete} record(s) not fully decoded')
        mount = store.recorded_path.split(_MARKER, 1)[0] if _MARKER in store.recorded_path else ''
        locate = _locator(items, mount)
        unnamed = 0
        for item in items:
            attributes = item.attributes
            name = attributes.get('_kMDItemFileName')
            if not isinstance(name, str):
                unnamed += 1
                continue
            records.append(((
                _cocoa(attributes.get('kMDItemContentModificationDate')),
                _cocoa(attributes.get('kMDItemContentCreationDate')),
                _cocoa(attributes.get('kMDItemDateAdded')),
                _cocoa(attributes.get('kMDItemLastUsedDate')),
                _cocoa_text(attributes.get('kMDItemUsedDates')),
                _text(attributes.get('kMDItemUseCount')),
                _cocoa(attributes.get('kMDItemDownloadedDate')),
                _text(attributes.get('kMDItemWhereFroms')),
                _cocoa_text(attributes.get('kMDItemUserSharedReceivedDate')),
                _text(attributes.get('kMDItemUserSharedReceivedSender')),
                _text(attributes.get('kMDItemUserSharedReceivedSenderHandle')),
                _text(attributes.get('kMDItemUserSharedReceivedTransport')),
                _text(attributes.get('kMDItemOriginSenderHandle')),
                _text(attributes.get('kMDItemOriginApplicationIdentifier')),
                _unix_micro(item.updated),
                name, locate(item.identifier, item.parent, name),
                _text(attributes.get('kMDItemKind')), _text(attributes.get('kMDItemContentType')),
                _text(attributes.get('kMDItemLogicalSize')), _text(attributes.get('_kMDItemOwnerUserID')),
                item.identifier, item.parent), relative))
        read.append(path)
        if unnamed:
            logfunc(f'Spotlight Store Files: {relative}: {unnamed} record(s) with no file name not reported')
    merged = merge_sources(records)
    merged.sort(key=lambda entry: (entry[0][0] == '', str(entry[0][0]), entry[0][16], str(entry[0][14])))
    data_list = [values + ('\n'.join(sources),) for values, sources in merged]
    return data_headers, data_list, '\n'.join(read)
