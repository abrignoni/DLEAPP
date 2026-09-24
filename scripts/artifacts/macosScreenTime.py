"""Usage recorded in the macOS Screen Time store (RMAdminStore), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosScreenTimeAppUsage": {
        "name": "Screen Time App and Web Usage",
        "description": "App and web domain usage times in the Screen Time store (RMAdminStore), "
                       "one row per app or domain in each usage block, with the block's start, "
                       "the stored category, device and account.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Screen Time (macOS)",
        "notes": "Reads each RMAdminStore-*.sqlite under "
                 "private/var/folders/<xx>/<yyyy>/0/com.apple.ScreenTimeAgent/Store, one "
                 "row per ZUSAGETIMEDITEM row. App Bundle ID and Web Domain are "
                 "ZBUNDLEIDENTIFIER and ZDOMAIN; on dleapp_macos_bigsur 96 of the 110 rows "
                 "name an app and 14 a web domain, never both. Time (seconds, as stored) "
                 "is ZTOTALTIMEINSECONDS. Category is the ZIDENTIFIER of the "
                 "ZUSAGECATEGORY row the item belongs to, as stored, and its meaning is "
                 "not established; on all 82 categories there the category's "
                 "ZTOTALTIMEINSECONDS equals the sum of its items' times. Usage Trusted is "
                 "ZUSAGETRUSTED as stored. Block Start (UTC) is the ZSTARTDATE of the "
                 "usage block (ZUSAGEBLOCK) the row belongs to, read as seconds since "
                 "00:00:00 UTC on 1 January 2001, the reference date Apple documents for "
                 "NSDate; on dleapp_macos_bigsur the 28 blocks start on the hour between "
                 "17 January and 19 February 2021, where the 1970 epoch would place them "
                 "in 1990. Block Duration (minutes) is ZDURATIONINMINUTES as stored and "
                 "held one value on all rows of dleapp_macos_bigsur. Device and Device "
                 "Platform are ZNAME and ZPLATFORM of the ZCOREDEVICE row the block's "
                 "ZUSAGE record names; Apple ID, Account DSID and User Name are ZAPPLEID, "
                 "ZDSID and ZGIVENNAME with ZFAMILYNAME of the ZCOREUSER row it names, as "
                 "stored. On dleapp_macos_bigsur the store holds two ZUSAGE records, one "
                 "naming a device and one naming none, and their blocks and items are "
                 "identical for every hour, so each row appears twice, once with Device "
                 "filled and once with it blank; what the record with no device represents "
                 "is not established. Apple ID has no value on any row there, and Account "
                 "DSID and User Name each held one value on all rows. "
                 "RMAdminStore-Cloud.sqlite and the RMAdminStore-Local.sqlite in a second "
                 "private/var/folders subfolder hold no usage there, and the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) "
                 "holds no RMAdminStore. When a logical extraction holds the same file "
                 "with and without a System/Volumes/Data/ prefix, a byte-identical second "
                 "copy is read once and counted in the run log. Reference: Apple, "
                 "'NSDate', https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 110 rows",
                       },
        "paths": ('*/private/var/folders/*/com.apple.ScreenTimeAgent/Store/RMAdminStore-*.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "hourglass",
    },
    "macosScreenTimeCountedItems": {
        "name": "Screen Time Notifications and Pickups",
        "description": "Per-app notification and pickup counts in the Screen Time store "
                       "(RMAdminStore), one row per app in each usage block, with the block's "
                       "start, device and account.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Screen Time (macOS)",
        "notes": "Reads each RMAdminStore-*.sqlite under "
                 "private/var/folders/<xx>/<yyyy>/0/com.apple.ScreenTimeAgent/Store, one "
                 "row per ZUSAGECOUNTEDITEM row. App Bundle ID, Notifications, Pickups and "
                 "Usage Trusted are ZBUNDLEIDENTIFIER, ZNUMBEROFNOTIFICATIONS, "
                 "ZNUMBEROFPICKUPS and ZUSAGETRUSTED as stored; on dleapp_macos_bigsur "
                 "each of the two usage records' 25 rows sum to 8 notifications and 23 "
                 "pickups. Block Start (UTC) is the ZSTARTDATE of the usage block "
                 "(ZUSAGEBLOCK) the row belongs to, read as seconds since 00:00:00 UTC on "
                 "1 January 2001, the reference date Apple documents for NSDate; on "
                 "dleapp_macos_bigsur the 28 blocks start on the hour between 17 January "
                 "and 19 February 2021, where the 1970 epoch would place them in 1990. "
                 "Block Duration (minutes) is ZDURATIONINMINUTES as stored and held one "
                 "value on all rows of dleapp_macos_bigsur. Device and Device Platform are "
                 "ZNAME and ZPLATFORM of the ZCOREDEVICE row the block's ZUSAGE record "
                 "names; Apple ID, Account DSID and User Name are ZAPPLEID, ZDSID and "
                 "ZGIVENNAME with ZFAMILYNAME of the ZCOREUSER row it names, as stored. On "
                 "dleapp_macos_bigsur the store holds two ZUSAGE records, one naming a "
                 "device and one naming none, and their blocks and items are identical for "
                 "every hour, so each row appears twice, once with Device filled and once "
                 "with it blank; what the record with no device represents is not "
                 "established. Apple ID has no value on any row there, and Account DSID "
                 "and User Name each held one value on all rows. RMAdminStore-Cloud.sqlite "
                 "and the RMAdminStore-Local.sqlite in a second private/var/folders "
                 "subfolder hold no usage there, and the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) holds no "
                 "RMAdminStore. When a logical extraction holds the same file with and "
                 "without a System/Volumes/Data/ prefix, a byte-identical second copy is "
                 "read once and counted in the run log. Reference: Apple, 'NSDate', "
                 "https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 50 rows",
                       },
        "paths": ('*/private/var/folders/*/com.apple.ScreenTimeAgent/Store/RMAdminStore-*.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
    },
    "macosScreenTimeBlocks": {
        "name": "Screen Time Usage Blocks",
        "description": "Usage blocks in the Screen Time store (RMAdminStore): each block's start "
                       "and duration, stored screen time, first pickup, longest session and last "
                       "event times, with the device and account.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Screen Time (macOS)",
        "notes": "Reads each RMAdminStore-*.sqlite under "
                 "private/var/folders/<xx>/<yyyy>/0/com.apple.ScreenTimeAgent/Store, one "
                 "row per ZUSAGEBLOCK row. Screen Time (seconds, as stored) is "
                 "ZSCREENTIMEINSECONDS and Pickups Without App Usage is "
                 "ZNUMBEROFPICKUPSWITHOUTAPPLICATIONUSAGE, as stored. First Pickup, "
                 "Longest Session Start, Longest Session End and Last Event are "
                 "ZFIRSTPICKUPDATE, ZLONGESTSESSIONSTARTDATE, ZLONGESTSESSIONENDDATE and "
                 "ZLASTEVENTDATE read the same way as Block Start. On dleapp_macos_bigsur "
                 "First Pickup is blank on 2 of the 28 blocks, and on 4 blocks the longest "
                 "session starts before the block starts or ends more than 60 minutes "
                 "after it, so those times are not confined to the block. Block Start "
                 "(UTC) is the ZSTARTDATE of the usage block (ZUSAGEBLOCK) the row belongs "
                 "to, read as seconds since 00:00:00 UTC on 1 January 2001, the reference "
                 "date Apple documents for NSDate; on dleapp_macos_bigsur the 28 blocks "
                 "start on the hour between 17 January and 19 February 2021, where the "
                 "1970 epoch would place them in 1990. Block Duration (minutes) is "
                 "ZDURATIONINMINUTES as stored and held one value on all rows of "
                 "dleapp_macos_bigsur. Device and Device Platform are ZNAME and ZPLATFORM "
                 "of the ZCOREDEVICE row the block's ZUSAGE record names; Apple ID, "
                 "Account DSID and User Name are ZAPPLEID, ZDSID and ZGIVENNAME with "
                 "ZFAMILYNAME of the ZCOREUSER row it names, as stored. On "
                 "dleapp_macos_bigsur the store holds two ZUSAGE records, one naming a "
                 "device and one naming none, and their blocks and items are identical for "
                 "every hour, so each row appears twice, once with Device filled and once "
                 "with it blank; what the record with no device represents is not "
                 "established. Apple ID has no value on any row there, and Account DSID "
                 "and User Name each held one value on all rows. RMAdminStore-Cloud.sqlite "
                 "and the RMAdminStore-Local.sqlite in a second private/var/folders "
                 "subfolder hold no usage there, and the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) holds no "
                 "RMAdminStore. When a logical extraction holds the same file with and "
                 "without a System/Volumes/Data/ prefix, a byte-identical second copy is "
                 "read once and counted in the run log. Reference: Apple, 'NSDate', "
                 "https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 28 rows",
                       },
        "paths": ('*/private/var/folders/*/com.apple.ScreenTimeAgent/Store/RMAdminStore-*.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
    },
}

import os
import re

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources

_STORE = re.compile(r'^RMAdminStore-[^/\\]*\.sqlite$')
_OWNER = ('Device', 'Device Platform (as stored)', 'Apple ID', 'Account DSID (as stored)',
          'User Name (as stored)', 'Source File')


def _text(value):
    return '' if value is None else str(value)


def _select(path, table, names, order='Z_PK'):
    if not does_table_exist_in_db(path, table):
        return []
    columns = ', '.join(name if does_column_exist_in_db(path, table, name) else f'NULL AS {name}'
                        for name in names)
    return get_sqlite_db_records(path, f'SELECT {columns} FROM {table} ORDER BY {order}') or []


def _stores(context):
    return [str(p) for p in context.get_files_found()
            if _STORE.match(os.path.basename(str(p))) and not os.path.isdir(str(p))]


class _Store:
    """The block, usage, device and account rows one RMAdminStore file holds."""

    def __init__(self, path, relative):
        self.relative = relative
        self.blocks = {row[0]: row[1:] for row in _select(
            path, 'ZUSAGEBLOCK', ('Z_PK', 'ZSTARTDATE', 'ZDURATIONINMINUTES', 'ZUSAGE'))}
        self.usages = {row[0]: row[1:] for row in _select(path, 'ZUSAGE', ('Z_PK', 'ZDEVICE', 'ZUSER'))}
        self.devices = {row[0]: row[1:] for row in _select(
            path, 'ZCOREDEVICE', ('Z_PK', 'ZNAME', 'ZPLATFORM'))}
        self.users = {row[0]: row[1:] for row in _select(
            path, 'ZCOREUSER', ('Z_PK', 'ZAPPLEID', 'ZDSID', 'ZGIVENNAME', 'ZFAMILYNAME'))}

    def block(self, block_id):
        """(start, duration) of a block."""
        start, duration, _usage = self.blocks.get(block_id, (None, None, None))
        return mac_absolute_utc(start), _text(duration)

    def owner(self, block_id):
        """(device, platform, Apple ID, DSID, user name, source) for the usage a block belongs to."""
        usage = self.blocks.get(block_id, (None, None, None))[2]
        device_id, user_id = self.usages.get(usage, (None, None))
        name, platform = self.devices.get(device_id, (None, None))
        apple_id, dsid, given, family = self.users.get(user_id, (None, None, None, None))
        user_name = ' '.join(part for part in (_text(given), _text(family)) if part)
        return _text(name), _text(platform), _text(apple_id), _text(dsid), user_name, self.relative


def _collect(context, label, table, build):
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, _stores(context), sidecars=('-wal',), label=label)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, table):
            logfunc(f'{label}: no {table} table read from {relative}')
            continue
        read.append(path)
        rows = build(path, _Store(path, relative))
        if not rows:
            logfunc(f'{label}: no rows in {relative}')
        data_list.extend(rows)
    return data_list, '\n'.join(read)


@artifact_processor
def macosScreenTimeAppUsage(context):
    data_headers = (('Block Start (UTC)', 'datetime'), 'Block Duration (minutes)', 'App Bundle ID',
                    'Web Domain', 'Time (seconds, as stored)', 'Category (as stored)',
                    'Usage Trusted (as stored)') + _OWNER

    def build(path, store):
        categories = {row[0]: row[1:] for row in _select(
            path, 'ZUSAGECATEGORY', ('Z_PK', 'ZBLOCK', 'ZIDENTIFIER'))}
        rows = []
        for bundle, domain, seconds, trusted, category in _select(
                path, 'ZUSAGETIMEDITEM', ('ZBUNDLEIDENTIFIER', 'ZDOMAIN', 'ZTOTALTIMEINSECONDS',
                                          'ZUSAGETRUSTED', 'ZCATEGORY')):
            block_id, identifier = categories.get(category, (None, None))
            rows.append(store.block(block_id) + (
                _text(bundle), _text(domain), _text(seconds), _text(identifier), _text(trusted))
                + store.owner(block_id))
        return rows

    data_list, sources = _collect(context, 'Screen Time App and Web Usage', 'ZUSAGETIMEDITEM', build)
    return data_headers, data_list, sources


@artifact_processor
def macosScreenTimeCountedItems(context):
    data_headers = (('Block Start (UTC)', 'datetime'), 'Block Duration (minutes)', 'App Bundle ID',
                    'Notifications (as stored)', 'Pickups (as stored)',
                    'Usage Trusted (as stored)') + _OWNER

    def build(path, store):
        rows = []
        for bundle, notifications, pickups, trusted, block_id in _select(
                path, 'ZUSAGECOUNTEDITEM', ('ZBUNDLEIDENTIFIER', 'ZNUMBEROFNOTIFICATIONS',
                                            'ZNUMBEROFPICKUPS', 'ZUSAGETRUSTED', 'ZBLOCK')):
            rows.append(store.block(block_id) + (
                _text(bundle), _text(notifications), _text(pickups), _text(trusted))
                + store.owner(block_id))
        return rows

    data_list, sources = _collect(context, 'Screen Time Notifications and Pickups',
                                  'ZUSAGECOUNTEDITEM', build)
    return data_headers, data_list, sources


@artifact_processor
def macosScreenTimeBlocks(context):
    data_headers = (('Block Start (UTC)', 'datetime'), 'Block Duration (minutes)',
                    'Screen Time (seconds, as stored)', ('First Pickup (UTC)', 'datetime'),
                    ('Longest Session Start (UTC)', 'datetime'),
                    ('Longest Session End (UTC)', 'datetime'), ('Last Event (UTC)', 'datetime'),
                    'Pickups Without App Usage (as stored)') + _OWNER

    def build(path, store):
        rows = []
        for (block_id, screen_time, first, longest_start, longest_end, last,
             pickups) in _select(path, 'ZUSAGEBLOCK', (
                 'Z_PK', 'ZSCREENTIMEINSECONDS', 'ZFIRSTPICKUPDATE', 'ZLONGESTSESSIONSTARTDATE',
                 'ZLONGESTSESSIONENDDATE', 'ZLASTEVENTDATE',
                 'ZNUMBEROFPICKUPSWITHOUTAPPLICATIONUSAGE'), order='ZSTARTDATE'):
            rows.append(store.block(block_id) + (
                _text(screen_time), mac_absolute_utc(first), mac_absolute_utc(longest_start),
                mac_absolute_utc(longest_end), mac_absolute_utc(last), _text(pickups))
                + store.owner(block_id))
        return rows

    data_list, sources = _collect(context, 'Screen Time Usage Blocks', 'ZUSAGEBLOCK', build)
    return data_headers, data_list, sources
