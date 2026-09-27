"""Reminders in the macOS Reminders stores, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The stores are Core Data SQLite databases. The table and column that hold each reminder
property are worked out from the store's own cached model (Z_MODELCACHE, a raw deflate
stream holding an NSKeyedArchiver of the model), so the older layout, where reminders are
rows of ZREMCDOBJECT beside other entities, and the newer ZREMCDREMINDER table are read the
same way. The artifact notes say how the column names are derived and how that was checked.
"""

__artifacts_v2__ = {
    "macosReminders": {
        "name": "Reminders",
        "description": "Reminders in each user's Reminders stores, with title, notes, list, account, the stored "
                       'creation, modification, due and completion dates, flag, priority, parent reminder and '
                       "the ModifiedByDevice value of each reminder's CloudKit record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Reminders (macOS)",
        "notes": (
            (
            (
            'Reads the Core Data stores of the Reminders app in each home folder, the '
            'Data-<UUID>.sqlite files, each of which holds one account on the tested images, and '
            'Data-local.sqlite, under Library/Reminders/Container_v1/Stores, where '
            'dleapp_macos_bigsur (macOS 11.2.1) keeps them, and under Library/Group '
            'Containers/group.com.apple.reminders/Container_v1/Stores, where the public MacBook '
            'Pro logical extraction (macOS 15.4, not a registered corpus key) keeps them. One row '
            'is reported per row of the REMCDReminder entity. On the MacBook Pro those rows are '
            'in a ZREMCDREMINDER table. The stores on dleapp_macos_bigsur have no such table: '
            'their model makes REMCDReminder a subentity of REMCDObject, so a reminder would be a '
            'row of ZREMCDOBJECT, which also holds the accounts, lists and other entities, and a '
            'property name that several of those entities define is kept in numbered columns such '
            'as ZTITLE and ZTITLE1. The column each property is read from is worked out from the '
            'Core Data model the store caches in Z_MODELCACHE, a raw deflate stream holding an '
            'NSKeyedArchiver archive of the model: Z followed by the property name in capitals, '
            'with 1, 2 and so on added when entities of the same table with lower numbers in '
            'Z_PRIMARYKEY define a property of that name themselves. That rule comes from '
            'measurement, not from a published source. On the 78 stores of dleapp_macos_bigsur, '
            'the MacBook Pro and 16 registered iOS images it names a column that exists for all '
            '75,737 attributes and to-one relationships of their entities, and in all 415 checks '
            'of a name that several entities share, the rows of an entity leave the other '
            "entities' columns of that name empty. On dleapp_macos_bigsur it places a reminder's "
            "title in ZTITLE1, the column a guest post on Ciofeca Forensics read a reminder's "
            'title from in the Reminders database of an iPhone in the Cellebrite 2020 CTF '
            "(Reference: Ciofeca Forensics, 'Cellebrite CTF 2020: Ruth Langmore', "
            'https://www.ciofecaforensics.com/2020/11/02/cellebrite-ctf-ruth/). A store whose '
            'model cannot be read is logged and not read, and a property whose column cannot be '
            'decided is logged and reported blank. List, Account and Parent Reminder are the name '
            "of the row the reminder's list relationship points to, the name of the row its "
            'account relationship points to, and the title of the reminder its parentReminder '
            'relationship points to, with the entity each relationship points to, REMCDList, '
            'REMCDAccount and REMCDReminder, taken from the model. On the MacBook Pro the list of '
            "each reminder belongs to the reminder's own account on all 37 rows, and Parent "
            'Reminder has no value on any row, since no tested reminder has a parent reminder. '
            'Created (UTC), Last Modified (UTC), Completion Date (UTC) and Last Banner '
            'Presentation (UTC) are creationDate, lastModifiedDate, completionDate and '
            'lastBannerPresentationDate read as seconds since 00:00:00 UTC on 1 January 2001, the '
            "reference date Apple documents for NSDate (Reference: Apple, 'NSDate', "
            'https://developer.apple.com/documentation/foundation/nsdate). Read that way the 37 '
            'reminders on the MacBook Pro were created on 26 November 2025, where the 1970 epoch '
            'would place them in 1994, and the CloudKit record each row keeps in '
            'ckServerRecordData, an NSKeyedArchiver archive, holds a RecordCtime between 2 '
            'seconds and 5 days after Created, never before it. Last Modified equals Created on '
            '33 of the 37 rows. A reminder whose allDay is 1 has its due date in Due Date (All '
            'Day), written as a date. On the one such reminder, on the MacBook Pro, dueDate is '
            "midnight UTC on that date and the row's displayDateDate is midnight at the offset of "
            '-18,000 seconds the row records in displayDateUpdatedForSecondsFromGMT, so the date '
            'is not reported as a time. For a reminder with a time, Due (UTC) is dueDate read as '
            'the dates above and Due Time Zone (as stored) is its timeZone. No reminder on the '
            'MacBook Pro has a time, so Due (UTC) and Due Time Zone (as stored) have no value on '
            'any row there; the 4 reminders with a time in the registered iOS images '
            'cookbook_ios1751 and otto_ios17 each store a time zone and a displayDateDate equal '
            'to dueDate. A due date marked all day that is not at midnight UTC, or one with a '
            'time and no stored time zone, is not reported and the run log counts it; no tested '
            'reminder has either. Title and Notes are title and notes as stored; the '
            'titleDocument and notesDocument data beside them are not read. Completed (as '
            'stored), Flagged (as stored), Priority (as stored) and Marked for Deletion (as '
            'stored) are completed, flagged, priority and markedForDeletion as stored, and what '
            'markedForDeletion records is not established. On the MacBook Pro Completed, Flagged, '
            'Priority and Marked for Deletion hold 0 on every row and Completion Date has no '
            'value on any row; in the registered iOS images one reminder is completed with a '
            'completion date (otto_ios17), one has a priority other than 0 (cookbook_ios1751) and '
            'one is marked for deletion (fsfull002_ios17). What sets lastBannerPresentationDate '
            'is not established. On the MacBook Pro one reminder has one, 9 hours after that '
            "reminder's displayDateDate, and the registered iPhone 14 Plus image "
            'iphone14plus_ios18, whose store holds the same 37 reminders by CloudKit identifier, '
            'with the same Created, Last Modified, Title, Notes, due date and list on all 37, has '
            'a value 2.2 seconds later on that reminder. CloudKit ModifiedByDevice (as stored) is '
            'the ModifiedByDevice value of that CloudKit record. A post on Ciofeca Forensics '
            'reported that this field of an Apple Notes record holds the hostname of a device '
            'used by the account, and cautioned that there can be false positives (Reference: '
            "Ciofeca Forensics, 'Revisiting Apple Notes (7): Cloudkit Data', "
            'https://www.ciofecaforensics.com/2020/10/20/apple-notes-cloudkit-data/). On the '
            'MacBook Pro CloudKit ModifiedByDevice holds one value on every row, a name ending in '
            'MacBook Pro, and the iPhone 14 Plus copies hold the same value; in cookbook_ios1751 '
            'one record holds the string CKDatabaseRpc. User is the folder after Users in the '
            'source path. On the MacBook Pro every row comes from one store of one user with one '
            'account, so Account, User and Source File each hold one value there. When a logical '
            'extraction holds the same store under Users/ and under System/Volumes/Data/Users/, a '
            'second copy whose database and -wal file are both byte-identical to the first is not '
            'read again and is counted in the run log, as the 4 copies on the MacBook Pro are; a '
            'row that differing copies both hold with the same values is reported once, and '
            'Source File lists every copy. The five stores on dleapp_macos_bigsur hold 4 accounts '
            'and 4 lists and no reminder. Alarms and their triggers, attachments, recurrence '
            'rules, hashtags, assignments and sharees, REMCDAuxiliaryReminderChangeInfo and its '
            "delete and move subentities, templates, saved reminders and Core Data's persistent "
            'history tables (ACHANGE and ATRANSACTION) are not reported.'
        )
        )
        ),
        "paths": ('*/Library/Reminders/Container_v1/Stores/*.sqlite*',
                  '*/Library/Group Containers/group.com.apple.reminders/Container_v1/Stores/*.sqlite*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (five Reminders stores in the older layout, none holding a reminder)",
        },
    },
}

import os
import plistlib
import zlib
from datetime import timedelta

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import (EPOCH_2001, mac_absolute_utc, resolve_keyed_archive,
                                  unique_sources, user_from_path)
from scripts.macos_powerlog import merge_sources

_REMINDER = 'REMCDReminder'
# REMCDReminder properties read into each row, with the name each takes in the query.
_PROPERTIES = (('creationDate', 'created'), ('lastModifiedDate', 'modified'),
               ('title', 'title'), ('notes', 'notes'), ('allDay', 'all_day'),
               ('dueDate', 'due'), ('timeZone', 'time_zone'), ('completed', 'completed'),
               ('completionDate', 'completion'), ('flagged', 'flagged'),
               ('priority', 'priority'), ('markedForDeletion', 'marked'),
               ('lastBannerPresentationDate', 'banner'), ('ckServerRecordData', 'record'))
# To-one relationships of REMCDReminder, the property read from the row they point to, and
# the name that takes in the query.
_JOINS = (('list', 'name', 'list_name'), ('account', 'name', 'account_name'),
          ('parentReminder', 'title', 'parent_title'))
_COLUMN_KINDS = ('attribute', 'to-one')
_DAY = 86400


def _model(blob):
    """{entity: (superentity or None, {property: (owned, kind, destination)})} from a
    Z_MODELCACHE blob, or None when it cannot be read. kind is 'attribute', 'to-one',
    'to-many' or the class name of anything else. owned is False for a property its
    superentity also lists: a subentity lists its superentity's properties as well as its own,
    and archives differ in how they store an inherited one (a _NSPropertyDescriptionProxy of
    the superentity's description, or a copy of it), so the name is what decides."""
    try:
        archive = plistlib.loads(zlib.decompress(bytes(blob), -15))
    except (zlib.error, plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return None
    objects = archive.get('$objects') if isinstance(archive, dict) else None
    if not isinstance(objects, list):
        return None

    def get(value):
        if isinstance(value, plistlib.UID):
            return objects[value.data] if value.data < len(objects) else None
        return value

    def class_name(item):
        meta = get(item.get('$class')) if isinstance(item, dict) else None
        return meta.get('$classname') if isinstance(meta, dict) else None

    def entity_name(value):
        value = get(value)
        return get(value.get('NSEntityName')) if isinstance(value, dict) else None

    def describe(item):
        kind = class_name(item)
        if kind == 'NSAttributeDescription':
            return 'attribute', None
        if kind == 'NSRelationshipDescription':
            destination = get(item.get('_NSDestinationEntityName')) or \
                entity_name(item.get('NSDestinationEntity'))
            return ('to-one' if get(item.get('NSMaxCount')) == 1 else 'to-many'), destination
        return kind, None

    model = {}
    for item in objects:
        if class_name(item) != 'NSEntityDescription':
            continue
        properties = {}
        table = get(item.get('NSProperties'))
        if isinstance(table, dict):
            for key, value in zip(table.get('NS.keys', []), table.get('NS.objects', [])):
                prop = get(value)
                if class_name(prop) == '_NSPropertyDescriptionProxy':
                    prop = get(prop.get('NSUnderlyingProperty'))
                properties[get(key)] = describe(prop)
        name = get(item.get('NSEntityName'))
        if isinstance(name, str):
            model[name] = (entity_name(item.get('NSSuperentity')), properties)
    return {name: (parent, {prop: (not (parent in model and prop in model[parent][1]), *kind)
                            for prop, kind in props.items()})
            for name, (parent, props) in model.items()} or None


def _root(model, entity):
    seen = set()
    while model.get(entity, (None,))[0] in model and entity not in seen:
        seen.add(entity)
        entity = model[entity][0]
    return entity


def _descends(model, entity, ancestor):
    seen = set()
    while entity in model and entity not in seen:
        if entity == ancestor:
            return True
        seen.add(entity)
        entity = model[entity][0]
    return False


def _owner(model, entity, prop):
    """The entity that defines prop for entity: itself, or the ancestor it inherits it from."""
    seen = set()
    while entity in model and entity not in seen:
        seen.add(entity)
        owned = model[entity][1].get(prop, (False,))[0]
        if owned:
            return entity
        entity = model[entity][0]
    return None


def _column(model, order, entity, prop):
    """The column Core Data stores prop of entity in: Z and the property name in capitals,
    followed by 1, 2, ... when entities of the same table with lower entity numbers define a
    property of that name themselves. None when prop has no column of its own (to-many and
    other kinds), when an entity of the table defines that name as anything other than an
    attribute or a to-one relationship, or when an entity number is missing."""
    owner = _owner(model, entity, prop)
    if owner is None or model[owner][1][prop][1] not in _COLUMN_KINDS:
        return None
    root = _root(model, entity)
    owners = [name for name, (_parent, props) in model.items()
              if _root(model, name) == root and props.get(prop, (False,))[0]]
    if any(model[name][1][prop][1] not in _COLUMN_KINDS for name in owners):
        return None
    if any(name not in order for name in owners):
        return None
    owners.sort(key=lambda name: order[name])
    index = owners.index(owner)
    return f'Z{prop.upper()}{index if index else ""}'


def _columns(path, table):
    return {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}


def _modified_by_device(blob):
    """ModifiedByDevice from the CloudKit record archive in ckServerRecordData, or ''."""
    if not isinstance(blob, (bytes, bytearray)):
        return ''
    try:
        archive = plistlib.loads(bytes(blob))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return ''
    value = resolve_keyed_archive(archive, 'ModifiedByDevice')
    return value if isinstance(value, str) else ''


def _blank(value):
    return '' if value is None else value


def _query(path, relative):
    """(query, unresolved property names) for the reminders of one store, or (None, reason)."""
    rows = get_sqlite_db_records(path, 'SELECT Z_CONTENT FROM Z_MODELCACHE') \
        if does_table_exist_in_db(path, 'Z_MODELCACHE') else []
    model = _model(rows[0][0]) if rows and rows[0][0] else None
    if not model:
        return None, f'no readable Core Data model in {relative}'
    if _REMINDER not in model:
        return None, f'no {_REMINDER} entity in the model of {relative}'
    order = {row['Z_NAME']: row['Z_ENT'] for row in get_sqlite_db_records(
        path, 'SELECT Z_NAME, Z_ENT FROM Z_PRIMARYKEY')} \
        if does_table_exist_in_db(path, 'Z_PRIMARYKEY') else {}
    table = f'Z{_root(model, _REMINDER).upper()}'
    if _REMINDER not in order or not does_table_exist_in_db(path, table):
        return None, f'no {table} table for {_REMINDER} in {relative}'
    columns = _columns(path, table)
    select, joins, unresolved = ['r.Z_PK AS pk'], [], []
    for prop, alias in _PROPERTIES:
        column = _column(model, order, _REMINDER, prop)
        if column in columns:
            select.append(f'r."{column}" AS {alias}')
        else:
            select.append(f'NULL AS {alias}')
            unresolved.append(prop)
    for index, (relation, target, alias) in enumerate(_JOINS):
        key = _column(model, order, _REMINDER, relation)
        owner = _owner(model, _REMINDER, relation)
        destination = model[owner][1][relation][2] if owner else None
        found = None
        if key in columns and destination in model:
            other = f'Z{_root(model, destination).upper()}'
            column = _column(model, order, destination, target)
            numbers = sorted(order[name] for name in model
                             if name in order and _descends(model, name, destination))
            if numbers and does_table_exist_in_db(path, other) and column in _columns(path, other):
                found = (other, column, numbers)
        if found is None:
            select.append(f'NULL AS {alias}')
            unresolved.append(relation)
            continue
        other, column, numbers = found
        name = f'j{index}'
        joins.append(f'LEFT JOIN "{other}" {name} ON {name}.Z_PK = r."{key}" AND '
                     f'{name}.Z_ENT IN ({", ".join(str(number) for number in numbers)})')
        select.append(f'{name}."{column}" AS {alias}')
    query = (f'SELECT {", ".join(select)} FROM "{table}" r {" ".join(joins)} '
             f'WHERE r.Z_ENT = {int(order[_REMINDER])} ORDER BY created, pk')
    return query, unresolved


def _due(row, counts):
    """(due instant, all-day date, stored time zone) for one reminder row."""
    due, time_zone = row['due'], _blank(row['time_zone'])
    if due is None:
        return '', '', time_zone
    if isinstance(due, bool) or not isinstance(due, (int, float)):
        counts['that are not numbers'] += 1
        return '', '', time_zone
    if row['all_day'] == 1:
        if due % _DAY == 0:
            return '', (EPOCH_2001 + timedelta(seconds=due)).date().isoformat(), time_zone
        counts['marked all day and not at midnight UTC'] += 1
        return '', '', time_zone
    if time_zone:
        return mac_absolute_utc(due), '', time_zone
    counts['with a time and no stored time zone'] += 1
    return '', '', time_zone


@artifact_processor
def macosReminders(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Last Modified (UTC)', 'datetime'), 'Title',
                    'Notes', 'List', 'Account', ('Due (UTC)', 'datetime'), 'Due Date (All Day)',
                    'Due Time Zone (as stored)', 'Completed (as stored)',
                    ('Completion Date (UTC)', 'datetime'), 'Flagged (as stored)',
                    'Priority (as stored)', 'Parent Reminder', 'Marked for Deletion (as stored)',
                    ('Last Banner Presentation (UTC)', 'datetime'),
                    'CloudKit ModifiedByDevice (as stored)', 'User', 'Source File')
    stores = [path for path in context.get_files_found()
              if str(path).endswith('.sqlite') and not os.path.basename(str(path)).startswith('._')]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label='Reminders')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        query, detail = _query(path, relative)
        if query is None:
            logfunc(f'Reminders: {detail}')
            continue
        if detail:
            logfunc(f'Reminders: no column found for {", ".join(detail)} in {relative}; '
                    'reported blank')
        rows = get_sqlite_db_records(path, query)
        if rows:
            read.append(path)
        counts = {'that are not numbers': 0, 'marked all day and not at midnight UTC': 0,
                  'with a time and no stored time zone': 0}
        for row in rows:
            due, day, time_zone = _due(row, counts)
            records.append(((mac_absolute_utc(row['created']), mac_absolute_utc(row['modified']),
                             _blank(row['title']), _blank(row['notes']),
                             _blank(row['list_name']), _blank(row['account_name']), due, day,
                             time_zone, _blank(row['completed']),
                             mac_absolute_utc(row['completion']), _blank(row['flagged']),
                             _blank(row['priority']), _blank(row['parent_title']),
                             _blank(row['marked']), mac_absolute_utc(row['banner']),
                             _modified_by_device(row['record']), user_from_path(relative)),
                            relative))
        for reason, count in counts.items():
            if count:
                logfunc(f'Reminders: {count} due date(s) in {relative} {reason}, not reported')
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)
