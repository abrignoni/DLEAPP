"""Pin the Siri App Conversations artifact (scripts/artifacts/macosSiriAgentSessions.py).

The test database uses the table and column definitions of the four tables the artifact reads, as dumped
from the AgentSessionStore.sqlite of a macOS 27.2.1 Mac. Every row value is made up; the attachment rows
follow the shape the store wrote (one 0x01 byte, then JSON) with made-up identifiers and paths.
"""
import base64
import datetime
import fnmatch
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
# pylint: disable=wrong-import-position
from scripts.artifacts import macosSiriAgentSessions as sa
from test_macos_shared_file_lists import bookmark
# pylint: enable=wrong-import-position

SCHEMA = '''
CREATE TABLE ZAGENTPROVENANCEENTITY ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZBUNDLEID VARCHAR, ZEXTERNALPROVIDER VARCHAR );
CREATE TABLE ZAGENTSESSIONEVENTENTITY ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZISSENSITIVECONDITION INTEGER, ZSEQUENCENUMBER INTEGER, ZAGENTPROVENANCE INTEGER, ZSESSION INTEGER, ZCREATEDAT TIMESTAMP, ZCONVERSATIONFRAGMENTINDEXCONTENT VARCHAR, ZEVENTID VARCHAR, ZPREVIOUSTURNID VARCHAR, ZROLERAWVALUE VARCHAR, ZSENSITIVITYCONDITIONNAME VARCHAR, ZTEXTCONTENT VARCHAR, ZUSERTURNID VARCHAR, ZSESSIONRESUMPTIONDATA BLOB );
CREATE TABLE ZARTIFACTENTITY ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZFILESIZEBYTES INTEGER, ZISCOMPLETE INTEGER, ZISMARKEDPURGEABLE INTEGER, ZISORIGINATINGDEVICE INTEGER, ZVERSIONNUMBER INTEGER, ZEVENT INTEGER, ZSESSION INTEGER, ZTHUMBNAILBACKGROUNDIMAGEOF INTEGER, ZCREATEDAT TIMESTAMP, ZLASTACCESSEDAT TIMESTAMP, ZARTIFACTID VARCHAR, ZASSETRECORDNAME VARCHAR, ZCONTENTKIND VARCHAR, ZCONTENTTYPE VARCHAR, ZFILENAME VARCHAR, ZLOCALENTITYIDENTIFIER VARCHAR, ZOWNEDFILEPATH VARCHAR, ZVARIANT VARCHAR, ZCLOUDKITASSETIDENTIFIER BLOB, ZCONTENTDATA BLOB, ZMETADATAJSON BLOB );
CREATE TABLE ZAGENTSESSIONRECORDENTITY ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZISPINNED INTEGER, ZPERSISTABLESTATERAW INTEGER, ZTITLESOURCE INTEGER, ZSAFETYSTATE INTEGER, ZSELECTEDAGENTPROVENANCE INTEGER, ZTHUMBNAILBACKGROUNDIMAGE INTEGER, ZCREATIONDATE TIMESTAMP, ZLASTMODIFIEDDATE TIMESTAMP, ZSELECTEDAGENTPROVENANCESETAT TIMESTAMP, ZINTERNALSESSIONID VARCHAR, ZSESSIONID VARCHAR, ZSOURCEBUNDLEID VARCHAR, ZSUMMARY VARCHAR, ZTITLE VARCHAR );
'''
FILE_PATH = '/Users/a/Documents/made up.txt'


def entity(type_name, bundle, local):
    """An app-entity attachment row's ZCONTENTDATA: one 0x01 byte, then JSON."""
    value = {'persistableAppEntity': {'_0': {'stableId': {'notSyncable': {}}, 'originEntityIdentifierValue': {
        'provenance': {'clientSpecificMetadata': {}}, 'type': {'custom': {'typeName': type_name,
                                                                          'bundleIdentifier': bundle}},
        'instanceIdentifier': {'local': {'_0': local}}}}}}
    return b'\x01' + json.dumps(value).encode()


def file_entity(path=FILE_PATH):
    local = {'securityScope': 'bWFkZSB1cA==',
             'storage': {'bookmark': {'data': base64.b64encode(bookmark(path=path)).decode()}}}
    return entity('AttachmentFileEntity', 'test.attach', json.dumps(local))


# 2001-epoch seconds: 784000000 is 2025-11-05 01:46:40 UTC
BASE = 784000000


def build(path, with_rows=True, tables=True):
    database = sqlite3.connect(path)
    if not tables:
        database.execute('CREATE TABLE other (x INTEGER)')
    else:
        database.executescript(SCHEMA)
    if tables and with_rows:
        database.execute("INSERT INTO ZAGENTPROVENANCEENTITY (Z_PK, ZBUNDLEID) VALUES (1, 'test.agent.one')")
        database.execute("INSERT INTO ZAGENTPROVENANCEENTITY (Z_PK, ZBUNDLEID) VALUES (2, 'test.agent.two')")
        database.executemany(
            "INSERT INTO ZAGENTSESSIONRECORDENTITY (Z_PK, ZISPINNED, ZPERSISTABLESTATERAW, ZSELECTEDAGENTPROVENANCE, "
            "ZCREATIONDATE, ZLASTMODIFIEDDATE, ZSELECTEDAGENTPROVENANCESETAT, ZSESSIONID, ZSOURCEBUNDLEID, ZSUMMARY, "
            "ZTITLE) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(1, 1, 1, 1, BASE, BASE + 60, BASE + 1, 'S-1', 'test.source', 'sum one', 'title one'),
             (2, 0, 0, 2, BASE + 100, BASE + 100, None, 'S-2', 'test.source', None, None),
             (3, 0, 1, None, BASE + 200, BASE + 200, None, 'S-3', None, None, 'empty session')])
        database.executemany(
            "INSERT INTO ZAGENTSESSIONEVENTENTITY (Z_PK, ZSEQUENCENUMBER, ZAGENTPROVENANCE, ZSESSION, ZCREATEDAT, "
            "ZEVENTID, ZROLERAWVALUE, ZTEXTCONTENT) VALUES (?,?,?,?,?,?,?,?)",
            [(1, 2, 1, 1, BASE + 30, 'E-2', 'assistant', 'made up answer'),
             (2, 1, 1, 1, BASE + 10, 'E-1', 'user', 'made up question'),
             (3, 1, 2, 2, BASE + 110, 'E-3', 'assistant', None)])
        database.executemany(
            "INSERT INTO ZARTIFACTENTITY (Z_PK, ZEVENT, ZSESSION, ZCONTENTKIND, ZCONTENTDATA) VALUES (?,?,?,?,?)",
            [(1, 1, 1, 'appEntityNonSyncable', file_entity()),
             (2, 1, 1, 'appEntityNonSyncable', entity('SelectedText', 'test.flow', 'made-up-id')),
             (3, 1, 1, 'data', b'\x01' + json.dumps({'data': {'_0': 'bWFkZSB1cA=='}}).encode()),
             (4, None, 1, 'appEntityNonSyncable', entity('AgentMediaEntity', 'test.media', 'x')),
             (5, 3, 2, 'appEntityNonSyncable', b'\x02 not json')])
    database.commit()
    database.close()


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.seeker = None
        self.media = None

    def database(self, user='a', **kw):
        folder = os.path.join(self.folder.name, 'Users', user, 'Library', 'Daemon Containers', 'UUID-1',
                              'Data', 'AgentSessionKit')
        os.makedirs(folder)
        path = os.path.join(folder, 'AgentSessionStore.sqlite')
        build(path, **kw)
        return path

    def run_artifact(self, found, extraction=()):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        seeker = mock.Mock()
        seeker.search.side_effect = lambda pattern: [p for p in extraction if fnmatch.fnmatchcase('root/' + p, pattern)]
        context.get_seeker.return_value = seeker
        self.seeker = seeker
        with mock.patch.object(sa, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'), \
                mock.patch.object(sa, 'check_in_media', side_effect=lambda p, name='': f'media:{p}') as media:
            result = sa.macosSiriAgentSessions.__wrapped__(context)
        self.media = media
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows(self):
        path = self.database()
        (headers, rows, located), log = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        utc = datetime.timezone.utc
        at = lambda s: datetime.datetime(2001, 1, 1, tzinfo=utc) + datetime.timedelta(seconds=s)
        self.assertEqual(headers[0], ('Event Created (UTC)', 'datetime'))
        self.assertEqual(headers[7], ('Attachment File', 'media'))
        self.assertEqual(len(headers), 20)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(len(r) == 20 for r in rows))
        # session 1: events in sequence order, user event first
        self.assertEqual(rows[0], (at(BASE + 10), at(BASE), at(BASE + 60), at(BASE + 1), 'user', 'title one',
                                   'made up question', '', '', 'sum one', 'test.agent.one', 'test.agent.one',
                                   'test.source', '1', '1', 'S-1', 'E-1', '1', 'a', rel))
        self.assertEqual(rows[1][4:7], ('assistant', 'title one', 'made up answer'))
        # the event's app-entity rows, in Z_PK order; the data row and the session-level row are not listed
        self.assertEqual(rows[1][8], f'AttachmentFileEntity (test.attach): {FILE_PATH}\nSelectedText (test.flow)')
        # the bookmarked file is not in this extraction, so no media
        self.assertEqual(rows[1][7], '')
        self.seeker.search.assert_called_once_with('*/Users/a/Documents/made up.txt')
        # session 2: an event with no text keeps a blank Text; no title or summary; an undecodable attachment row
        self.assertEqual(rows[2][4:7], ('assistant', '', ''))
        self.assertEqual(rows[2][8], 'attachment row not decoded')
        self.assertEqual(rows[2][10:12], ('test.agent.two', 'test.agent.two'))
        self.assertTrue(any('1 attachment row(s)' in m for m in log))
        # session 3 has no event: event columns blank, session columns kept
        self.assertEqual(rows[3][0], '')
        self.assertEqual(rows[3][1], at(BASE + 200))
        self.assertEqual(rows[3][5], 'empty session')
        self.assertEqual(rows[3][7:9], ('', ''))
        self.assertEqual(located, path)

    def test_bookmarked_file_in_extraction_is_media(self):
        path = self.database()
        held = ['Users/a/Documents/made up.txt', 'System/Volumes/Data/Users/a/Documents/made up.txt',
                'Users/b/Documents/made up.txt']
        (_, rows, _), _ = self.run_artifact([path], extraction=held)
        self.assertEqual(rows[1][7], ['media:Users/a/Documents/made up.txt'])
        self.media.assert_called_once_with('Users/a/Documents/made up.txt', name='made up.txt')

    def test_glob_characters_in_a_path_are_literal(self):
        path = self.database()
        database = sqlite3.connect(path)
        database.execute('UPDATE ZARTIFACTENTITY SET ZCONTENTDATA = ? WHERE Z_PK = 1',
                         (file_entity('/Users/a/[x]*.txt'),))
        database.commit()
        database.close()
        (_, rows, _), _ = self.run_artifact([path], extraction=['Users/a/x1.txt', 'Users/a/[x]*.txt'])
        self.assertEqual(rows[1][7], ['media:Users/a/[x]*.txt'])

    def test_no_attachment_table(self):
        path = self.database()
        database = sqlite3.connect(path)
        database.execute('DROP TABLE ZARTIFACTENTITY')
        database.commit()
        database.close()
        (_, rows, _), _ = self.run_artifact([path])
        self.assertEqual(len(rows), 4)
        self.assertEqual({r[8] for r in rows}, {''})

    def test_no_rows_is_empty(self):
        path = self.database(with_rows=False)
        (_, rows, located), _ = self.run_artifact([path])
        self.assertEqual(rows, [])
        self.assertEqual(located, path)

    def test_missing_tables_skipped(self):
        path = self.database(tables=False)
        (_, rows, located), log = self.run_artifact([path])
        self.assertEqual(rows, [])
        self.assertEqual(located, '')
        self.assertTrue(any('missing' in m for m in log))

    def test_missing_column_and_provenance_table_degrade(self):
        path = self.database()
        database = sqlite3.connect(path)
        database.execute('DROP TABLE ZAGENTPROVENANCEENTITY')
        database.execute('ALTER TABLE ZAGENTSESSIONRECORDENTITY DROP COLUMN ZSUMMARY')
        database.commit()
        database.close()
        (_, rows, _), _ = self.run_artifact([path])
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0][5:12], ('title one', 'made up question', '', '', '', '', ''))

    def test_two_users_are_separate_and_sidecars_ignored(self):
        first = self.database('a')
        second = self.database('b')
        (_, rows, _), _ = self.run_artifact([first, second, first + '-wal'])
        self.assertEqual(sorted({r[18] for r in rows}), ['a', 'b'])
        self.assertEqual(len(rows), 8)

    def test_path_pattern(self):
        pattern = sa.__artifacts_v2__['macosSiriAgentSessions']['paths'][0]
        good = 'root/Users/a/Library/Daemon Containers/ABC/Data/AgentSessionKit/AgentSessionStore.sqlite-wal'
        bad = 'root/Users/a/Library/Daemon Containers/ABC/Data/Other/AgentSessionStore.sqlite'
        self.assertTrue(fnmatch.fnmatchcase(good, pattern))
        self.assertFalse(fnmatch.fnmatchcase(bad, pattern))


if __name__ == '__main__':
    unittest.main()
