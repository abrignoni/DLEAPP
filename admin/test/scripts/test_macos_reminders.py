"""Pin the Reminders artifact in scripts/artifacts/macosReminders.py.

Every store, cached model and CloudKit record below is built by the test; no row comes from a
real device. The models mirror the two layouts the artifact reads: reminders in their own
ZREMCDREMINDER table, and reminders as rows of ZREMCDOBJECT beside other entities, where a
property name several entities define is stored in numbered columns. Expected values are
literals.
"""
import fnmatch
import os
import pathlib
import plistlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosReminders as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
NEWER = 'Users/alex/Library/Group Containers/group.com.apple.reminders/Container_v1/Stores/'
OLDER = 'Users/sam/Library/Reminders/Container_v1/Stores/'
ATTRIBUTES = ('creationDate', 'lastModifiedDate', 'title', 'notes', 'allDay', 'dueDate', 'timeZone',
              'completed', 'completionDate', 'flagged', 'priority', 'lastBannerPresentationDate')


def model_cache(entities, style):
    """A Z_MODELCACHE blob: raw deflate of an NSKeyedArchiver archive of entity descriptions.

    entities is [(name, parent, {property: kind})] with kind 'attr', ('one', destination) or
    ('many', destination). A subentity lists its parent's properties as well as its own, as
    _NSPropertyDescriptionProxy objects (style 'proxy') or as copies (style 'copy')."""
    uid = plistlib.UID
    objects, classes = ['$null'], {}

    def add(value):
        objects.append(value)
        return uid(len(objects) - 1)

    def cls(name):
        if name not in classes:
            classes[name] = add({'$classname': name, '$classes': [name, 'NSObject']})
        return classes[name]

    def description(prop, kind):
        if kind == 'attr':
            return add({'$class': cls('NSAttributeDescription'), 'NSPropertyName': add(prop), 'NSAttributeType': 700})
        return add({'$class': cls('NSRelationshipDescription'), 'NSPropertyName': add(prop),
                    'NSMaxCount': 1 if kind[0] == 'one' else 0, '_NSDestinationEntityName': add(kind[1])})

    spec = {name: (parent, props) for name, parent, props in entities}
    slots = {name: add({}) for name in spec}
    own = {}

    def build(name):
        if name in own:
            return own[name]
        parent, props = spec[name]
        listed = {}
        if parent:
            for prop, (desc, kind) in build(parent).items():
                listed[prop] = ((add({'$class': cls('_NSPropertyDescriptionProxy'), 'NSUnderlyingProperty': desc,
                                      'NSEntityDescription': slots[name]}) if style == 'proxy'
                                 else description(prop, kind)), kind)
        for prop, kind in props.items():
            listed[prop] = (description(prop, kind), kind)
        own[name] = listed
        return listed

    for name in spec:
        listed = build(name)
        table = add({'$class': cls('NSDictionary'), 'NS.keys': [add(p) for p in listed],
                     'NS.objects': [desc for desc, _ in listed.values()]})
        parent = spec[name][0]
        objects[slots[name].data] = {'$class': cls('NSEntityDescription'), 'NSEntityName': add(name),
                                     'NSSuperentity': slots[parent] if parent else uid(0), 'NSProperties': table}
    root = add({'$class': cls('NSManagedObjectModel'), 'NSEntities': [slots[name] for name in spec]})
    archive = plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': root},
                              '$objects': objects}, fmt=plistlib.PlistFormat.FMT_BINARY)
    packer = zlib.compressobj(9, zlib.DEFLATED, -15)
    return packer.compress(archive) + packer.flush()


def record(device):
    """A CloudKit record archive with a ModifiedByDevice value."""
    uid = plistlib.UID
    return plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver',
                           '$top': {'ModifiedByDevice': uid(1), 'RecordCtime': uid(2)},
                           '$objects': ['$null', device, {'NS.time': 788054402.0, '$class': uid(3)},
                                        {'$classname': 'NSDate', '$classes': ['NSDate', 'NSObject']}]},
                          fmt=plistlib.PlistFormat.FMT_BINARY)


REMINDER_PROPS = {**{name: 'attr' for name in ATTRIBUTES}, 'ckServerRecordData': 'attr',
                  'markedForDeletion': 'attr', 'list': ('one', 'REMCDList'),
                  'account': ('one', 'REMCDAccount'), 'parentReminder': ('one', 'REMCDReminder'),
                  'children': ('many', 'REMCDReminder')}
NEWER_MODEL = [
    ('REMCDBaseList', None, {'name': 'attr', 'account': ('one', 'REMCDAccount')}),
    ('REMCDList', 'REMCDBaseList', {'reminders': ('many', 'REMCDReminder')}),
    ('REMCDObject', None, {'account': ('one', 'REMCDAccount'), 'markedForDeletion': 'attr'}),
    ('REMCDAccount', 'REMCDObject', {'name': 'attr', 'reminders': ('many', 'REMCDReminder')}),
    ('REMCDAlarmLocationTrigger', 'REMCDObject', {'title': 'attr'}),
    ('REMCDReminder', None, REMINDER_PROPS)]
NEWER_NUMBERS = {'REMCDBaseList': 2, 'REMCDList': 3, 'REMCDObject': 14, 'REMCDAccount': 15,
                 'REMCDAlarmLocationTrigger': 19, 'REMCDReminder': 39}
OLDER_MODEL = [
    ('REMCDObject', None, {'account': ('one', 'REMCDAccount'), 'markedForDeletion': 'attr', 'ckServerRecordData': 'attr'}),
    ('REMCDAccount', 'REMCDObject', {'name': 'attr', 'reminders': ('many', 'REMCDReminder')}),
    ('REMCDAlarmLocationTrigger', 'REMCDObject', {'title': 'attr'}),
    ('REMCDList', 'REMCDObject', {'name': 'attr', 'reminders': ('many', 'REMCDReminder')}),
    ('REMCDReminder', 'REMCDObject', {name: kind for name, kind in REMINDER_PROPS.items()
                                      if name not in ('account', 'markedForDeletion', 'ckServerRecordData')}),
    ('REMCDSharee', 'REMCDObject', {'list': ('one', 'REMCDList')}),
    ('REMCDSmartListOrder', 'REMCDObject', {'lastModifiedDate': 'attr'})]
OLDER_NUMBERS = {'REMCDObject': 3, 'REMCDAccount': 4, 'REMCDAlarmLocationTrigger': 8, 'REMCDList': 22,
                 'REMCDReminder': 24, 'REMCDSharee': 25, 'REMCDSmartListOrder': 27}
REMINDER_COLUMNS = ('ZCREATIONDATE, ZLASTMODIFIEDDATE, ZTITLE, ZNOTES, ZALLDAY, ZDUEDATE, ZTIMEZONE, ZCOMPLETED, '
                    'ZCOMPLETIONDATE, ZFLAGGED, ZPRIORITY, ZLASTBANNERPRESENTATIONDATE, ZCKSERVERRECORDDATA, '
                    'ZMARKEDFORDELETION, ZLIST, ZACCOUNT, ZPARENTREMINDER')

OLDER_COLUMNS = ('Z_PK, Z_ENT, ZACCOUNT, ZMARKEDFORDELETION, ZCKSERVERRECORDDATA, ZNAME, ZTITLE, ZNAME1, ZTITLE1, '
                 'ZNOTES, ZCREATIONDATE, ZLASTMODIFIEDDATE, ZALLDAY, ZDUEDATE, ZTIMEZONE, ZCOMPLETED, ZCOMPLETIONDATE, '
                 'ZFLAGGED, ZPRIORITY, ZLASTBANNERPRESENTATIONDATE, ZLIST, ZPARENTREMINDER, ZLIST1, ZLASTMODIFIEDDATE1')


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        for module in (artifact, sys.modules['scripts.macos_plists']):
            patcher = patch.object(module, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def store(self, relative, numbers, cache, statements):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)')
            db.executemany('INSERT INTO Z_PRIMARYKEY VALUES (?, ?, 0, 0)', [(n, name) for name, n in numbers.items()])
            if cache is not None:
                db.execute('CREATE TABLE Z_MODELCACHE (Z_CONTENT BLOB)')
                db.execute('INSERT INTO Z_MODELCACHE VALUES (?)', (cache,))
            for statement, *rows in statements:
                if rows:
                    db.executemany(statement, rows)
                else:
                    db.execute(statement)
        db.close()
        return path

    def run_artifact(self, extra=()):
        return artifact.macosReminders.__wrapped__(Context(self.root, walk(self.root) + list(extra)))

    def newer_store(self, relative):
        return self.store(relative, NEWER_NUMBERS, model_cache(NEWER_MODEL, 'copy'), [
            ('CREATE TABLE ZREMCDBASELIST (Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, ZNAME VARCHAR, ZACCOUNT INTEGER)',),
            # Row 7 is the abstract base entity, not a list.
            ('INSERT INTO ZREMCDBASELIST VALUES (?, ?, ?, ?)', (1, 3, 'Groceries', 1), (2, 3, 'Work', 1),
             (7, 2, 'Base', 1)),
            ('CREATE TABLE ZREMCDOBJECT (Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, ZACCOUNT INTEGER, '
             'ZMARKEDFORDELETION INTEGER, ZNAME VARCHAR, ZTITLE VARCHAR)',),
            ('INSERT INTO ZREMCDOBJECT VALUES (?, ?, ?, ?, ?, ?)', (1, 15, None, 0, 'iCloud', None),
             (2, 19, 1, 0, None, 'Home')),
            (f'CREATE TABLE ZREMCDREMINDER (Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, {REMINDER_COLUMNS})',),
            (f'INSERT INTO ZREMCDREMINDER (Z_PK, Z_ENT, {REMINDER_COLUMNS}) VALUES ({", ".join("?" * 19)})',
             # All day, due at midnight UTC, with a banner and a CloudKit record.
             (1, 39, 788000000.0, 788000000.0, 'Pay rent', 'By transfer', 1, 788054400.0, None, 0, None, 0, 0,
              788104800.5, record('Test Mac'), 0, 1, 1, None),
             # A time and a stored time zone, completed, a child of the first.
             (2, 39, 790000000.0, 790000001.0, 'Call back', None, 0, 800000000.25, 'America/New_York', 1,
              800100000.0, 1, 5, None, b'not a plist', 0, 2, 1, 1),
             # A time and no time zone, and an all-day date that is not midnight UTC: neither is reported.
             (3, 39, 790000000.0, 790000000.0, 'No zone', None, 0, 800000000.0, None, 0, None, 0, 0, None, None, 1,
              1, 1, None),
             (4, 39, 810000000.0, 810000000.0, 'Odd day', None, 1, 810003600.0, None, 0, None, 0, 0, None, None, 0,
              7, 1, None))])

    def test_newer_layout(self):
        path = self.newer_store(NEWER + 'Data-A.sqlite')
        headers, rows, source = self.run_artifact()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Created (UTC)', 'Last Modified (UTC)', 'Title', 'Notes', 'List', 'Account', 'Due (UTC)',
                          'Due Date (All Day)', 'Due Time Zone (as stored)', 'Completed (as stored)',
                          'Completion Date (UTC)', 'Flagged (as stored)', 'Priority (as stored)', 'Parent Reminder',
                          'Marked for Deletion (as stored)', 'Last Banner Presentation (UTC)',
                          'CloudKit ModifiedByDevice (as stored)', 'User', 'Source File'])
        where = NEWER + 'Data-A.sqlite'
        self.assertEqual(rows, [
            (datetime(2025, 12, 21, 8, 53, 20, tzinfo=UTC), datetime(2025, 12, 21, 8, 53, 20, tzinfo=UTC), 'Pay rent',
             'By transfer', 'Groceries', 'iCloud', '', '2025-12-22', '', 0, '', 0, 0, '', 0,
             datetime(2025, 12, 22, 14, 0, 0, 500000, tzinfo=UTC), 'Test Mac', 'alex', where),
            (datetime(2026, 1, 13, 12, 26, 40, tzinfo=UTC), datetime(2026, 1, 13, 12, 26, 41, tzinfo=UTC), 'Call back',
             '', 'Work', 'iCloud', datetime(2026, 5, 9, 6, 13, 20, 250000, tzinfo=UTC), '', 'America/New_York', 1,
             datetime(2026, 5, 10, 10, 0, tzinfo=UTC), 1, 5, 'Pay rent', 0, '', '', 'alex', where),
            (datetime(2026, 1, 13, 12, 26, 40, tzinfo=UTC), datetime(2026, 1, 13, 12, 26, 40, tzinfo=UTC), 'No zone',
             '', 'Groceries', 'iCloud', '', '', '', 0, '', 0, 0, '', 1, '', '', 'alex', where),
            # Its list relationship points at a row of another entity.
            (datetime(2026, 9, 2, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC), 'Odd day', '', '', 'iCloud', '', '', '',
             0, '', 0, 0, '', 0, '', '', 'alex', where)])
        self.assertEqual(source, path)
        self.assertEqual(sorted(self.logged), sorted([
            f'Reminders: 1 due date(s) in {where} marked all day and not at midnight UTC, not reported',
            f'Reminders: 1 due date(s) in {where} with a time and no stored time zone, not reported']))

    def test_older_layout(self):
        columns = OLDER_COLUMNS

        def row(**values):
            return tuple(values.get(name.strip(), None) for name in columns.split(','))

        self.store(OLDER + 'Data-B.sqlite', OLDER_NUMBERS, model_cache(OLDER_MODEL, 'proxy'), [
            (f'CREATE TABLE ZREMCDOBJECT ({columns})',),
            (f'INSERT INTO ZREMCDOBJECT ({columns}) VALUES ({", ".join("?" * 24)})',
             row(Z_PK=1, Z_ENT=4, ZNAME='iCloud'),
             row(Z_PK=2, Z_ENT=8, ZACCOUNT=1, ZTITLE='Home'),
             row(Z_PK=3, Z_ENT=22, ZACCOUNT=1, ZNAME1='Errands'),
             row(Z_PK=4, Z_ENT=24, ZACCOUNT=1, ZTITLE1='Buy milk', ZNOTES='two', ZCREATIONDATE=600000000.0,
                 ZLASTMODIFIEDDATE=600000100.5, ZALLDAY=0, ZDUEDATE=600086400.0, ZTIMEZONE='Europe/Madrid',
                 ZCOMPLETED=0, ZFLAGGED=0, ZPRIORITY=0, ZMARKEDFORDELETION=0, ZLIST=3),
             row(Z_PK=5, Z_ENT=25, ZACCOUNT=1, ZLIST1=3),
             row(Z_PK=6, Z_ENT=27, ZACCOUNT=1, ZLASTMODIFIEDDATE1=700000000.0),
             # Created before row 4, so it is reported first.
             row(Z_PK=7, Z_ENT=24, ZACCOUNT=1, ZTITLE1='Oat milk', ZCREATIONDATE=590000000.0,
                 ZLASTMODIFIEDDATE=600000000.0, ZCOMPLETED=0, ZFLAGGED=0, ZPRIORITY=0, ZMARKEDFORDELETION=0,
                 ZLIST=2, ZPARENTREMINDER=4))])
        _, rows, _ = self.run_artifact()
        where = OLDER + 'Data-B.sqlite'
        self.assertEqual(rows, [
            # Its list relationship points at the alarm trigger row, which is not a list.
            (datetime(2019, 9, 12, 16, 53, 20, tzinfo=UTC), datetime(2020, 1, 6, 10, 40, tzinfo=UTC), 'Oat milk', '', '',
             'iCloud', '', '', '', 0, '', 0, 0, 'Buy milk', 0, '', '', 'sam', where),
            (datetime(2020, 1, 6, 10, 40, tzinfo=UTC), datetime(2020, 1, 6, 10, 41, 40, 500000, tzinfo=UTC), 'Buy milk',
             'two', 'Errands', 'iCloud', datetime(2020, 1, 7, 10, 40, tzinfo=UTC), '', 'Europe/Madrid', 0, '', 0, 0, '', 0,
             '', '', 'sam', where)])
        self.assertEqual(self.logged, [])

    def test_copies_and_stores_that_cannot_be_read(self):
        self.newer_store(NEWER + 'Data-A.sqlite')
        # A byte-identical copy under System/Volumes/Data is not read again.
        os.makedirs(os.path.join(self.root, 'System/Volumes/Data', NEWER))
        shutil.copy(os.path.join(self.root, NEWER, 'Data-A.sqlite'), os.path.join(self.root, 'System/Volumes/Data', NEWER))
        # A copy that differs holds the same reminders: each is reported once, naming both copies.
        other = 'Users/alex/Backup/Library/Group Containers/group.com.apple.reminders/Container_v1/Stores/Data-A.sqlite'
        self.newer_store(other)
        with sqlite3.connect(os.path.join(self.root, other)) as db:
            db.execute('CREATE TABLE extra (a TEXT)')
        db.close()
        self.store(NEWER + 'Data-none.sqlite', NEWER_NUMBERS, None, [])
        self.store(NEWER + 'Data-junk.sqlite', NEWER_NUMBERS, b'not deflate', [])
        self.store(NEWER + 'Data-noreminder.sqlite', {'REMCDObject': 1},
                   model_cache([('REMCDObject', None, {'name': 'attr'})], 'copy'), [])
        # A sibling entity of the older layout that defines notes as a to-many relationship leaves
        # the reminder's notes column undecided, so it is reported blank.
        ambiguous = OLDER_MODEL + [('REMCDTemplate', 'REMCDObject', {'notes': ('many', 'REMCDReminder')})]
        self.store(OLDER + 'Data-C.sqlite', {**OLDER_NUMBERS, 'REMCDTemplate': 30}, model_cache(ambiguous, 'proxy'), [
            (f'CREATE TABLE ZREMCDOBJECT ({OLDER_COLUMNS})',),
            ('INSERT INTO ZREMCDOBJECT (Z_PK, Z_ENT, ZTITLE1, ZNOTES, ZCREATIONDATE) VALUES (1, 24, ?, ?, ?)',
             ('Kept', 'hidden', 788000000.0))])
        folder = os.path.join(self.root, NEWER, 'Data-dir.sqlite')
        os.makedirs(folder)
        # A sidecar with no database beside it, and an AppleDouble file, are not stores.
        for name in ('Data-orphan.sqlite-shm', '._Data-A.sqlite'):
            with open(os.path.join(self.root, NEWER, name), 'wb') as handle:
                handle.write(b'\x00\x05\x16\x07 not a database')
        _, rows, source = self.run_artifact([folder])
        both = f'{NEWER}Data-A.sqlite\n{other}'
        # Stores are read shortest path first, so the older-layout store comes first.
        self.assertEqual([(r[2], r[-1]) for r in rows],
                         [('Kept', OLDER + 'Data-C.sqlite'), ('Pay rent', both), ('Call back', both), ('No zone', both),
                          ('Odd day', both)])
        self.assertEqual(rows[0][3], '')
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, p) for p in
                                                            (NEWER + 'Data-A.sqlite', other, OLDER + 'Data-C.sqlite')))
        self.assertEqual(sorted(line for line in self.logged if 'due date' not in line), sorted([
            'Reminders: 1 byte-identical copy(ies) under System/Volumes/Data not read again',
            f'Reminders: no readable Core Data model in {NEWER}Data-none.sqlite',
            f'Reminders: no readable Core Data model in {NEWER}Data-junk.sqlite',
            f'Reminders: no REMCDReminder entity in the model of {NEWER}Data-noreminder.sqlite',
            f'Reminders: no column found for notes in {OLDER}Data-C.sqlite; reported blank']))

    def test_declared_paths(self):
        paths = artifact.__artifacts_v2__['macosReminders']['paths']
        for member in (OLDER + 'Data-B.sqlite', NEWER + 'Data-A.sqlite-wal',
                       'System/Volumes/Data/' + NEWER + 'Data-local.sqlite'):
            self.assertTrue(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)
        for member in ('Users/alex/Library/Other/Container_v1/Stores/Data-A.sqlite', NEWER + 'Data-A.plist'):
            self.assertFalse(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)


if __name__ == '__main__':
    unittest.main()
