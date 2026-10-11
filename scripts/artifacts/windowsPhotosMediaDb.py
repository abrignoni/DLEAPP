"""Library database of the Windows Photos app (MediaDb.v1.sqlite), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "photosMediaDbItems": {
        "name": "Photos Library Items (MediaDb)",
        "description": "Pictures and videos the Windows Photos app indexed, one row per item of its library "
                       "database: file name, folder, size, dimensions, the dates stored for it, location, camera "
                       "and the source it came from.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Windows Photos",
        "notes": "Reads MediaDb.v1.sqlite, the library database of the Windows Photos app, in the LocalState folder "
                 "of the Microsoft.Windows.Photos package of each user, with its write-ahead log. The app's source "
                 "is not published: what a column holds rests on its name and on what was measured on "
                 "lonewolf_win10, the one tested image whose library has items. One row is reported per row of the "
                 "Item table. Date Created (UTC), Date Modified (UTC) and Date Ingested (UTC) are Item_DateCreated, "
                 "Item_DateModified and Item_DateIngested read as counts of 100 nanoseconds since 1601 in UTC. On "
                 "the image, 9 of the 28 items have a Folder Path on the local disk; for all 9 the File Size equals "
                 "the size of the file of that name and folder in the image's file system, and Date Modified (UTC) "
                 "equals that file's NTFS modified time to the second. Date Taken (As Stored) is Item_DateTaken, the "
                 "same kind of count, written as a date and time and not converted: on the 18 screenshot items of "
                 "the image it is 14,399 or 14,400 seconds before Date Created (UTC), four hours, so there it holds "
                 "a local clock time and not UTC; on the other 10 items it is 5 to 6 days before Date Created (UTC), "
                 "and what clock it follows for them is not established. Date Ingested (UTC) is on or after Date "
                 "Created (UTC) on all 28 rows. File Name, File Size, Width, Height, Media Type, Latitude, Longitude "
                 "and Storage Provider File ID are the Item columns of those names as stored; Media Type is a number "
                 "whose meaning is not established, 1 on all 28 rows, which are 20 png and 8 jpg files. Folder Path "
                 "is the Folder_Path of the item's parent folder. Camera Manufacturer and Camera Model are the text "
                 "of the rows the item refers to in the tables of those names. Source Type and Account are "
                 "Source_Type and Source_UserName of the item's source: on the image 9 items have type 1, no account "
                 "and a local Folder Path, and 19 have type 2, an account name and an empty Folder Path, their "
                 "folders having no path; every one of the 28 has a Storage Provider File ID. That pattern fits "
                 "items on the disk and items of a cloud account, which is not established from a source. Tags is "
                 "the number of rows the ItemTags table holds for the item, labels the app's image analysis gave it; "
                 "the labels' names are not in the database, only numbers, so only the count is reported: 9 items "
                 "have 1 to 7 and 19 have none. Item ID is Item_Id, User the folder under Users in the database's "
                 "path, and Source File the database. Latitude, Longitude, Camera Manufacturer and Camera Model were "
                 "empty on all 28 rows and Media Type and User each held one value on all 28, so a location and a "
                 "camera were tested with constructed input only, as were a database from an app version that lacks "
                 "one of the columns, which gives an empty cell, and one without an Item table, which is named in "
                 "the run log. The tables for faces, recognised text, albums and the user's actions in the app are "
                 "not read. pc_mus_001_win11, af_case2_win10 and szechuan_win10 hold the database with an empty Item "
                 "table and give no row. A row shows that the app indexed the file, not that the user opened it.",
        "paths": ("*/AppData/Local/Packages/Microsoft.Windows.Photos_*/LocalState/MediaDb.v1.sqlite*",),
        "output_types": "standard",
        "artifact_icon": "image",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the Item table is empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 28 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the Item table is empty)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the Item table is empty)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
    "photosMediaDbFolders": {
        "name": "Photos Library Folders (MediaDb)",
        "description": "Folders the Windows Photos app indexed, one row per folder of its library database: path, "
                       "the dates stored for it, its item count and the source it belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Windows Photos",
        "notes": "Reads MediaDb.v1.sqlite, the library database of the Windows Photos app, in the LocalState folder "
                 "of the Microsoft.Windows.Photos package of each user, with its write-ahead log. The app's source "
                 "is not published: what a column holds rests on its name and on what was measured on "
                 "lonewolf_win10, the one tested image whose library has items. One row is reported per row of the "
                 "Folder table. Date Created (UTC) and Date Modified (UTC) are Folder_DateCreated and "
                 "Folder_DateModified read as counts of 100 nanoseconds since 1601 in UTC. Path, Display Name, Item "
                 "Count, Parent Folder ID and Storage Provider File ID are the Folder columns of those names as "
                 "stored, and Source Type and Account are Source_Type and Source_UserName of the folder's source. "
                 "Folder ID is Folder_Id, User the folder under Users in the database's path, and Source File the "
                 "database. On lonewolf_win10 the 10 rows are 5 folders with a Path, the user's Pictures folder, its "
                 "OneDrive Pictures folder and three folders under them, with source type 1 and no account, and 5 "
                 "folders with an empty Path, source type 2 and an account name; Item Count is stored for the two "
                 "top folders only, 2 and 10. pc_mus_001_win11 and af_case2_win10 give 3 rows each and "
                 "szechuan_win10 6, from four users' databases, every one with a Path and no account. On "
                 "pc_mus_001_win11, af_case2_win10 and szechuan_win10 Source Type held one value, 1, on every row "
                 "and Account was empty on every row. Storage Provider File ID held one value, a hyphen, on all 3 "
                 "rows of pc_mus_001_win11 and of af_case2_win10 and was empty on all 6 rows of szechuan_win10, "
                 "where Item Count was also empty on all 6 rows. User held one value on all 10 rows of "
                 "lonewolf_win10 and on all 3 rows of pc_mus_001_win11 and of af_case2_win10. That a folder with no "
                 "Path belongs to a cloud account fits the data and is not established from a source. A database "
                 "from an app version that lacks one of the columns gives an empty cell, and one without a Folder "
                 "table is named in the run log, both tested with constructed input only. A row shows that the app "
                 "indexed the folder.",
        "paths": ("*/AppData/Local/Packages/Microsoft.Windows.Photos_*/LocalState/MediaDb.v1.sqlite*",),
        "output_types": "standard",
        "artifact_icon": "folder",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 6 rows",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import sqlite3
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)
DB_NAME = 'MediaDb.v1.sqlite'
ITEM_COLUMNS = ('Item_Id', 'Item_DateCreated', 'Item_DateModified', 'Item_DateTaken', 'Item_DateIngested',
                'Item_FileName', 'Item_ParentFolderId', 'Item_FileSize', 'Item_Width', 'Item_Height',
                'Item_MediaType', 'Item_Latitude', 'Item_Longitude', 'Item_CameraManufacturerId',
                'Item_CameraModelId', 'Item_SourceId', 'Item_StorageProviderFileId')
FOLDER_COLUMNS = ('Folder_Id', 'Folder_DateCreated', 'Folder_DateModified', 'Folder_Path', 'Folder_DisplayName',
                  'Folder_ItemCount', 'Folder_ParentFolderId', 'Folder_SourceId', 'Folder_StorageProviderFileId')


def filetime(value):
    """The UTC time of a positive count of 100-nanosecond intervals since 1601, or '' for anything else."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return ''
    try:
        return EPOCH_1601 + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def stored_clock(value):
    """A count of 100-nanosecond intervals since 1601 written out as a date and time with no zone, or ''."""
    when = filetime(value)
    return when.strftime('%Y-%m-%d %H:%M:%S') if when else ''


def _columns(db, table):
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def _records(db, table, wanted):
    """Each row of table as a dict of the wanted columns; a column the table lacks is None."""
    have = _columns(db, table)
    chosen = [name for name in wanted if name in have]
    if wanted[0] not in chosen:
        return None
    query = f'SELECT {", ".join(chosen)} FROM "{table}" ORDER BY {wanted[0]}'
    return [dict(dict.fromkeys(wanted), **dict(zip(chosen, row))) for row in db.execute(query)]


def _lookup(db, table, key, text):
    if not {key, text} <= _columns(db, table):
        return {}
    return dict(db.execute(f'SELECT {key}, {text} FROM "{table}"'))


def _text(value):
    return '' if value is None else value


def item_rows(db):
    """The rows for the Item table: (date created, date modified, date taken as stored, date ingested, file name,
    folder path, file size, width, height, media type, latitude, longitude, camera manufacturer, camera model,
    source type, account, storage provider file id, tags, item id). None when the database has no Item table."""
    items = _records(db, 'Item', ITEM_COLUMNS)
    if items is None:
        return None
    folders = _lookup(db, 'Folder', 'Folder_Id', 'Folder_Path')
    makers = _lookup(db, 'CameraManufacturer', 'CameraManufacturer_Id', 'CameraManufacturer_Text')
    models = _lookup(db, 'CameraModel', 'CameraModel_Id', 'CameraModel_Text')
    kinds = _lookup(db, 'Source', 'Source_Id', 'Source_Type')
    accounts = _lookup(db, 'Source', 'Source_Id', 'Source_UserName')
    tags = {}
    if 'ItemTags_ItemId' in _columns(db, 'ItemTags'):
        tags = dict(db.execute('SELECT ItemTags_ItemId, COUNT(*) FROM ItemTags GROUP BY ItemTags_ItemId'))
    rows = []
    for item in items:
        source = item['Item_SourceId']
        rows.append((filetime(item['Item_DateCreated']), filetime(item['Item_DateModified']),
                     stored_clock(item['Item_DateTaken']), filetime(item['Item_DateIngested']),
                     _text(item['Item_FileName']), _text(folders.get(item['Item_ParentFolderId'])),
                     _text(item['Item_FileSize']), _text(item['Item_Width']), _text(item['Item_Height']),
                     _text(item['Item_MediaType']), _text(item['Item_Latitude']), _text(item['Item_Longitude']),
                     _text(makers.get(item['Item_CameraManufacturerId'])),
                     _text(models.get(item['Item_CameraModelId'])), _text(kinds.get(source)),
                     _text(accounts.get(source)), _text(item['Item_StorageProviderFileId']),
                     tags.get(item['Item_Id'], 0), item['Item_Id']))
    return rows


def folder_rows(db):
    """The rows for the Folder table: (date created, date modified, path, display name, item count, parent folder
    id, source type, account, storage provider file id, folder id). None when there is no Folder table."""
    folders = _records(db, 'Folder', FOLDER_COLUMNS)
    if folders is None:
        return None
    kinds = _lookup(db, 'Source', 'Source_Id', 'Source_Type')
    accounts = _lookup(db, 'Source', 'Source_Id', 'Source_UserName')
    return [(filetime(folder['Folder_DateCreated']), filetime(folder['Folder_DateModified']),
             _text(folder['Folder_Path']), _text(folder['Folder_DisplayName']), _text(folder['Folder_ItemCount']),
             _text(folder['Folder_ParentFolderId']), _text(kinds.get(folder['Folder_SourceId'])),
             _text(accounts.get(folder['Folder_SourceId'])), _text(folder['Folder_StorageProviderFileId']),
             folder['Folder_Id']) for folder in folders]


def _collect(context, label, reader):
    data_list, read = [], []
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.basename(path) != DB_NAME or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            logfunc(f'{label}: could not open {relative} as SQLite')
            continue
        try:
            rows = reader(db)
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        finally:
            db.close()
        if rows is None:
            logfunc(f'{label}: {relative} does not have the table this artifact reads')
            continue
        user = _user(relative)
        data_list.extend(row + (user, relative) for row in rows)
        if rows:
            read.append(path)
    return data_list, '\n'.join(read)


def _user(relative):
    """The folder name after the first folder named Users in a path within the extraction, or ''."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'users':
            return parts[index + 1]
    return ''


@artifact_processor
def photosMediaDbItems(context):
    data_headers = (('Date Created (UTC)', 'datetime'), ('Date Modified (UTC)', 'datetime'),
                    'Date Taken (As Stored)', ('Date Ingested (UTC)', 'datetime'), 'File Name', 'Folder Path',
                    'File Size', 'Width', 'Height', 'Media Type', 'Latitude', 'Longitude', 'Camera Manufacturer',
                    'Camera Model', 'Source Type', 'Account', 'Storage Provider File ID', 'Tags', 'Item ID', 'User',
                    'Source File')
    data_list, located = _collect(context, 'Photos Library Items (MediaDb)', item_rows)
    return data_headers, data_list, located


@artifact_processor
def photosMediaDbFolders(context):
    data_headers = (('Date Created (UTC)', 'datetime'), ('Date Modified (UTC)', 'datetime'), 'Path', 'Display Name',
                    'Item Count', 'Parent Folder ID', 'Source Type', 'Account', 'Storage Provider File ID',
                    'Folder ID', 'User', 'Source File')
    data_list, located = _collect(context, 'Photos Library Folders (MediaDb)', folder_rows)
    return data_headers, data_list, located
