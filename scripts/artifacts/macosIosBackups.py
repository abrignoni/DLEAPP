"""Backups of iPhone, iPad and iPod touch devices kept on a computer, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosIosBackups": {
        "name": "iOS Device Backups",
        "description": "Backups of iOS devices stored on the computer, with the device's name, "
                       "model, iOS version, serial number, identifiers and phone number, the "
                       "backup dates and the encryption and passcode flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per backup folder directly inside a MobileSync/Backup folder, read from "
                 "the Info.plist, Manifest.plist and Status.plist at the top of that folder. Apple "
                 "names ~/Library/Application Support/MobileSync/Backup/ as where a Mac keeps these "
                 "backups. Last Backup Date is the Info.plist Last Backup Date, Status Date the "
                 "Status.plist Date and Manifest Date the Manifest.plist Date, each a plist date "
                 "read as UTC. Encrypted and Passcode Set are the Manifest.plist IsEncrypted and "
                 "WasPasscodeSet values, and Full Backup, Backup State and Snapshot State the "
                 "Status.plist IsFullBackup, BackupState and SnapshotState values, all as stored. "
                 "The device columns are the Info.plist values of the same names, and macOS "
                 "Version and macOS Build Version are its macOS Version and macOS Build Version "
                 "values as stored. Applications Listed counts the bundle IDs in Info.plist's "
                 "Installed Applications and Applications; the iOS Device Backup Applications "
                 "artifact lists them. A column is blank when its file or key is absent, and a "
                 "missing Manifest.plist or Status.plist is logged. The backup's own content "
                 "(Manifest.db and the hashed files) is not read here: iLEAPP parses a backup "
                 "folder with -t itunes, and the Backup Folder column names the folder to give it. "
                 "Whether an encrypted backup's Info.plist carries the same fields is not "
                 "established. The pattern keys on the MobileSync/Backup folder, which is also "
                 "the name of the folder iTunes and the Apple Devices app use on Windows; no "
                 "Windows backup has been run through it. Info.plist files found deeper inside a "
                 "backup folder are not read and are counted in the run log. User is the folder "
                 "after Users in the source path, or root under private/var/root, and is blank "
                 "when the input is one user's home folder whose path names no user. Public "
                 "regression cases are independently authored synthetic data; local private "
                 "validation details are not published. Reference: Apple, 'Locate and manage "
                 "backups of your iPhone, iPad, and iPod touch', "
                 "https://support.apple.com/en-us/108809.",
        "paths": ('*/MobileSync/Backup/*/Info.plist',
                  '*/MobileSync/Backup/*/Manifest.plist',
                  '*/MobileSync/Backup/*/Status.plist'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smartphone",
        "sample_data": {},
    },
    "macosIosBackupApps": {
        "name": "iOS Device Backup Applications",
        "description": "Apps listed in the Info.plist of each iOS device backup on the computer, "
                       "with the app name, bundle ID, version, seller, purchase date and the "
                       "Apple ID and account identifiers recorded for its download as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per bundle ID in the Installed Applications list or the Applications "
                 "dictionary of each backup's Info.plist, with Listed In naming which of the two "
                 "holds it. The other columns come from the entry's iTunesMetadata plist: App Name "
                 "is itemName, Version bundleShortVersionString, Bundle Version bundleVersion, "
                 "Seller artistName, Genre genre, Store Item ID itemId, Storefront "
                 "storefrontCountryCode, Source App sourceApp, and Redownload, Auto Download and "
                 "Factory Install the is-purchased-redownload, is-auto-download and "
                 "isFactoryInstall values. Purchase Date is the purchaseDate string in its "
                 "com.apple.iTunesStore.downloadInfo, read as UTC because it ends in Z; which "
                 "purchase or download it records is not established. Apple ID, DS Person ID, "
                 "Purchaser ID, Downloader ID, Family ID and Alt DSID are the AppleID, DSPersonID, "
                 "PurchaserID, DownloaderID, FamilyID and AltDSID values of its accountInfo, as "
                 "stored. A bundle ID with no Applications entry, or whose iTunesMetadata cannot "
                 "be read, is reported with those columns blank, and an unreadable iTunesMetadata "
                 "or purchaseDate is logged. The list is what the backup's Info.plist names; it "
                 "is not a check of what the backup's own files hold. Device Name, Unique "
                 "Identifier and Backup Folder tie each row to its row in iOS Device Backups. "
                 "User is the folder after Users in the source path, or root under "
                 "private/var/root, and is blank when the input is one user's home folder whose "
                 "path names no user. Public regression cases are independently authored "
                 "synthetic data; local private validation details are not published.",
        "paths": ('*/MobileSync/Backup/*/Info.plist',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "package",
        "sample_data": {},
    },
}

import os
import plistlib
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources, user_from_path


def _text(value):
    return '' if value is None else str(value)


def _flag(value):
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return _text(value)


def _backup_infos(context, label):
    """(Info.plist paths directly inside a MobileSync/Backup/<folder>, count of deeper ones)."""
    infos, deeper = [], 0
    candidates = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'Info.plist']
    paths, _skipped = unique_sources(context, candidates, label=label)
    for path in paths:
        parts = context.get_relative_path(path).replace('\\', '/').split('/')
        if len(parts) >= 4 and parts[-3] == 'Backup' and parts[-4] == 'MobileSync':
            infos.append(path)
        else:
            deeper += 1
    if deeper:
        logfunc(f'{label}: {deeper} Info.plist file(s) deeper inside a backup folder not read')
    return infos


def _app_ids(info):
    listed = info.get('Installed Applications')
    listed = [str(b) for b in listed] if isinstance(listed, list) else []
    apps = info.get('Applications')
    apps = apps if isinstance(apps, dict) else {}
    ordered = list(dict.fromkeys(listed + [str(b) for b in apps]))
    return ordered, set(listed), apps


@artifact_processor
def macosIosBackups(context):
    data_headers = (('Last Backup Date (UTC)', 'datetime'), ('Status Date (UTC)', 'datetime'),
                    ('Manifest Date (UTC)', 'datetime'), 'Device Name', 'Display Name',
                    'Product Type', 'Product Name', 'Product Version', 'Build Version',
                    'Serial Number', 'Unique Identifier', 'Target Identifier', 'IMEI', 'IMEI 2',
                    'MEID', 'ICCID', 'Phone Number', 'Encrypted', 'Passcode Set', 'Full Backup',
                    'Backup State', 'Snapshot State', 'Applications Listed', 'macOS Version',
                    'macOS Build Version', 'Backup Folder', 'User')
    data_list = []
    read = []
    for path in _backup_infos(context, 'iOS Device Backups'):
        relative = context.get_relative_path(path)
        folder = os.path.dirname(relative.replace('\\', '/'))
        info = load_plist(path)
        if not isinstance(info, dict):
            logfunc(f'iOS Device Backups: could not read {relative}')
            continue
        read.append(path)
        extra = {}
        for name in ('Manifest.plist', 'Status.plist'):
            other = os.path.join(os.path.dirname(path), name)
            loaded = load_plist(other) if os.path.isfile(other) else None
            if isinstance(loaded, dict):
                extra[name] = loaded
                read.append(other)
            else:
                logfunc(f'iOS Device Backups: no readable {name} in {folder}')
        manifest = extra.get('Manifest.plist', {})
        status = extra.get('Status.plist', {})
        ids, _listed, _apps = _app_ids(info)
        data_list.append((
            as_utc(info.get('Last Backup Date')), as_utc(status.get('Date')),
            as_utc(manifest.get('Date')),
            *(_text(info.get(key)) for key in (
                'Device Name', 'Display Name', 'Product Type', 'Product Name', 'Product Version',
                'Build Version', 'Serial Number', 'Unique Identifier', 'Target Identifier', 'IMEI',
                'IMEI 2', 'MEID', 'ICCID', 'Phone Number')),
            _flag(manifest.get('IsEncrypted')), _flag(manifest.get('WasPasscodeSet')),
            _flag(status.get('IsFullBackup')), _text(status.get('BackupState')),
            _text(status.get('SnapshotState')), len(ids), _text(info.get('macOS Version')),
            _text(info.get('macOS Build Version')), folder, user_from_path(relative)))
    return data_headers, data_list, '\n'.join(read)


def _purchase_date(value, label):
    if not value:
        return ''
    try:
        return datetime.strptime(str(value), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        logfunc(f'iOS Device Backup Applications: purchaseDate not read for {label}')
        return ''


@artifact_processor
def macosIosBackupApps(context):
    data_headers = (('Purchase Date (UTC)', 'datetime'), 'App Name', 'Bundle ID', 'Version',
                    'Bundle Version', 'Seller', 'Genre', 'Apple ID', 'DS Person ID',
                    'Purchaser ID', 'Downloader ID', 'Family ID', 'Alt DSID', 'Redownload',
                    'Auto Download', 'Factory Install', 'Storefront', 'Source App',
                    'Store Item ID', 'Listed In', 'Device Name', 'Unique Identifier',
                    'Backup Folder', 'User')
    data_list = []
    read = []
    for path in _backup_infos(context, 'iOS Device Backup Applications'):
        relative = context.get_relative_path(path)
        folder = os.path.dirname(relative.replace('\\', '/'))
        info = load_plist(path)
        if not isinstance(info, dict):
            logfunc(f'iOS Device Backup Applications: could not read {relative}')
            continue
        read.append(path)
        ids, listed, apps = _app_ids(info)
        for bundle in ids:
            where = [name for name, present in (('Installed Applications', bundle in listed),
                                                ('Applications', bundle in apps)) if present]
            meta = {}
            entry = apps.get(bundle)
            raw = entry.get('iTunesMetadata') if isinstance(entry, dict) else None
            if isinstance(raw, (bytes, bytearray)):
                try:
                    meta = plistlib.loads(bytes(raw))
                except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
                    logfunc(f'iOS Device Backup Applications: iTunesMetadata not read for {bundle}')
                meta = meta if isinstance(meta, dict) else {}
            download = meta.get('com.apple.iTunesStore.downloadInfo')
            download = download if isinstance(download, dict) else {}
            account = download.get('accountInfo')
            account = account if isinstance(account, dict) else {}
            data_list.append((
                _purchase_date(download.get('purchaseDate'), bundle), _text(meta.get('itemName')),
                bundle, _text(meta.get('bundleShortVersionString')),
                _text(meta.get('bundleVersion')), _text(meta.get('artistName')),
                _text(meta.get('genre')), _text(account.get('AppleID')),
                _text(account.get('DSPersonID')), _text(account.get('PurchaserID')),
                _text(account.get('DownloaderID')), _text(account.get('FamilyID')),
                _text(account.get('AltDSID')), _flag(meta.get('is-purchased-redownload')),
                _flag(meta.get('is-auto-download')), _flag(meta.get('isFactoryInstall')),
                _text(meta.get('storefrontCountryCode')), _text(meta.get('sourceApp')),
                _text(meta.get('itemId')), ', '.join(where), _text(info.get('Device Name')),
                _text(info.get('Unique Identifier')), folder, user_from_path(relative)))
    return data_headers, data_list, '\n'.join(read)
