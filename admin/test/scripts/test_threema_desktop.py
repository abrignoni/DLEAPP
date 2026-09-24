"""Threema Desktop regression tests using independently authored synthetic rows."""
# pylint: disable=protected-access

import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import threema_desktop as td  # pylint: disable=wrong-import-position
from scripts.artifacts import threemaDesktop as artifacts  # pylint: disable=wrong-import-position


SCHEMA = """
CREATE TABLE contacts(uid INTEGER PRIMARY KEY, identity TEXT, createdAt INTEGER,
 firstName TEXT,lastName TEXT,nickname TEXT,verificationLevel INTEGER,identityType INTEGER,
 acquaintanceLevel INTEGER,activityState INTEGER,featureMask INTEGER,workVerificationLevel INTEGER,
 workAvailabilityStatusCategory INTEGER,workAvailabilityStatusDescription TEXT,workLastFullSyncAt INTEGER);
CREATE TABLE groups(uid INTEGER PRIMARY KEY,groupId BLOB,name TEXT,createdAt INTEGER,creatorUid INTEGER);
CREATE TABLE groupMembers(uid INTEGER PRIMARY KEY,groupUid INTEGER,contactUid INTEGER);
CREATE TABLE distributionLists(uid INTEGER PRIMARY KEY,distributionListId BLOB,name TEXT,createdAt INTEGER);
CREATE TABLE conversations(uid INTEGER PRIMARY KEY,lastUpdate INTEGER,contactUid INTEGER,groupUid INTEGER,
 distributionListUid INTEGER,category INTEGER,visibility INTEGER);
CREATE TABLE messages(uid INTEGER PRIMARY KEY,messageId BLOB,senderContactUid INTEGER,conversationUid INTEGER,
 createdAt INTEGER,processedAt INTEGER,deliveredAt INTEGER,readAt INTEGER,messageType TEXT,threadId INTEGER,
 lastEditedAt INTEGER,deletedAt INTEGER);
CREATE TABLE messageTextData(uid INTEGER PRIMARY KEY,messageUid INTEGER,text TEXT,quotedMessageId BLOB);
CREATE TABLE messageLocationData(uid INTEGER PRIMARY KEY,messageUid INTEGER,lat REAL,lon REAL,accuracy REAL,name TEXT,address TEXT);
CREATE TABLE polls(uid INTEGER PRIMARY KEY,description TEXT);
CREATE TABLE messagePollData(uid INTEGER PRIMARY KEY,messageUid INTEGER,type INTEGER,pollUid INTEGER);
CREATE TABLE messageReactions(uid INTEGER PRIMARY KEY,reactionAt INTEGER,reaction TEXT,senderIdentity TEXT,messageUid INTEGER);
CREATE TABLE fileData(uid INTEGER PRIMARY KEY,fileId TEXT,encryptionKey BLOB,unencryptedByteCount INTEGER,storageFormatVersion INTEGER);
CREATE TABLE messageFileData(uid INTEGER PRIMARY KEY,messageUid INTEGER,fileName TEXT,fileSize INTEGER,mediaType TEXT,
 caption TEXT,correlationId TEXT,fileDataUid INTEGER,blobDownloadState INTEGER,downloadFailureReason TEXT,encryptionKey BLOB);
CREATE TABLE messageImageData(uid INTEGER PRIMARY KEY,messageUid INTEGER,fileName TEXT,fileSize INTEGER,mediaType TEXT,
 caption TEXT,correlationId TEXT,fileDataUid INTEGER,blobDownloadState INTEGER,downloadFailureReason TEXT,
 height INTEGER,width INTEGER,durationSeconds REAL,encryptionKey BLOB);
CREATE TABLE messageVideoData(uid INTEGER PRIMARY KEY,messageUid INTEGER,fileName TEXT,fileSize INTEGER,mediaType TEXT,
 caption TEXT,correlationId TEXT,fileDataUid INTEGER,blobDownloadState INTEGER,downloadFailureReason TEXT,
 height INTEGER,width INTEGER,durationSeconds REAL,encryptionKey BLOB);
CREATE TABLE messageAudioData(uid INTEGER PRIMARY KEY,messageUid INTEGER,fileName TEXT,fileSize INTEGER,mediaType TEXT,
 caption TEXT,correlationId TEXT,fileDataUid INTEGER,blobDownloadState INTEGER,downloadFailureReason TEXT,
 height INTEGER,width INTEGER,durationSeconds REAL,encryptionKey BLOB);
CREATE TABLE runningGroupCalls(uid INTEGER PRIMARY KEY,groupUid INTEGER,nFailed INTEGER,startedAt INTEGER,
 creatorIdentity TEXT,protocolVersion INTEGER,gck BLOB,baseUrl TEXT);
"""


def populate(db):
    db.executescript(SCHEMA)
    db.execute("INSERT INTO contacts VALUES(1,'TEST0001',1704067200123,'A','Example','synthetic',2,1,0,0,7,1,2,'Busy',1704067201123)")
    db.execute("INSERT INTO groups VALUES(2,x'0102','Synthetic Group',1704067202123,1)")
    db.execute("INSERT INTO groupMembers VALUES(3,2,1)")
    db.execute("INSERT INTO distributionLists VALUES(4,x'0304','Synthetic List',1704067203123)")
    db.execute("INSERT INTO conversations VALUES(5,1704067204123,1,NULL,NULL,1,1)")
    db.execute("INSERT INTO conversations VALUES(6,1704067205123,NULL,2,NULL,0,0)")
    db.execute("INSERT INTO messages VALUES(7,x'0506',1,6,1704067206123,1704067207123,NULL,1704067208123,'text',9,1704067209123,NULL)")
    db.execute("INSERT INTO messageTextData VALUES(8,7,'Synthetic message',NULL)")
    db.execute("INSERT INTO messageReactions VALUES(9,1704067210123,'👍','TEST0001',7)")
    db.execute("INSERT INTO fileData VALUES(10,'synthetic-file',x'00',123,1)")
    db.execute("INSERT INTO messageFileData VALUES(11,7,'synthetic.txt',123,'text/plain','Synthetic caption','synthetic-correlation',10,2,NULL,x'00')")
    db.execute("INSERT INTO runningGroupCalls VALUES(12,2,0,1704067211123,'TEST0001',1,x'00','https://sfu.invalid')")
    db.commit()


class ThreemaDesktopTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        populate(self.db)
        self.addCleanup(self.db.close)

    def test_timestamp_preserves_milliseconds(self):
        self.assertEqual(td.timestamp(1704067200123),
                         datetime(2024, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc))
        self.assertEqual(td.timestamp(0), "")

    def test_contacts_and_conversations(self):
        contact = list(artifacts._contacts(self.db))[0]
        self.assertEqual(contact[2:10], ('TEST0001', 'A', 'Example', 'synthetic',
                         'Fully verified', 'Work', 'Direct', 'Active'))
        conversations = list(artifacts._conversations(self.db))
        self.assertEqual([row[4] for row in conversations], ['Direct', 'Group'])
        self.assertEqual(conversations[1][-1], 1)

    def test_groups_messages_and_reactions(self):
        group = list(artifacts._groups(self.db))[0]
        self.assertEqual(group[2:10], ('0102', 'Synthetic Group', 1, 'TEST0001', 3, 1,
                                      'TEST0001', 'A'))
        message = list(artifacts._messages(self.db))[0]
        self.assertEqual(message[6], 'Inbound')
        self.assertEqual(message[9], 'Synthetic message')
        reaction = list(artifacts._reactions(self.db))[0]
        self.assertEqual(reaction[3:5], ('👍', 'TEST0001'))

    def test_attachment_and_persisted_call(self):
        attachment = list(artifacts._attachments(self.db))[0]
        self.assertEqual(attachment[4:8], ('File', 'synthetic.txt', 'text/plain', 123))
        self.assertNotIn('00', attachment)
        call = list(artifacts._group_calls(self.db))[0]
        self.assertEqual(call[3:8], ('0102', 'Synthetic Group', 'TEST0001', 1,
                                    'https://sfu.invalid'))

    def test_readonly_plaintext_database_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'profile' / 'data' / 'threema.sqlite'
            path.parent.mkdir(parents=True)
            disk = sqlite3.connect(path)
            populate(disk)
            disk.close()

            class Context:
                @staticmethod
                def get_files_found():
                    return [path]

                @staticmethod
                def get_relative_path(candidate):
                    return pathlib.Path(candidate).relative_to(folder)

            rows, sources = td.read_databases(Context, artifacts._messages, 'test')
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][-1], pathlib.Path('profile/data/threema.sqlite'))
            self.assertEqual(sources, str(path))

    def test_locked_profile_summary_withholds_key_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            database = root / 'data' / 'threema.sqlite'
            key_storage = root / 'data' / 'keystorage.bin'
            database.parent.mkdir(parents=True)
            database.write_bytes(b'not a plaintext database')
            key_storage.write_bytes(b'synthetic protected bytes')

            class Context:
                @staticmethod
                def get_files_found():
                    return [database, key_storage]

                @staticmethod
                def get_relative_path(candidate):
                    return pathlib.Path(candidate).relative_to(root)

            _headers, rows, _sources = artifacts.threemaProfile.__wrapped__(Context)
            rendered = repr(rows)
            self.assertIn('Present; contents withheld', rendered)
            self.assertIn('Encrypted; not opened', rendered)
            self.assertNotIn('synthetic protected bytes', rendered)

    def test_metadata_has_no_corpus_samples(self):
        self.assertEqual(len(artifacts.__artifacts_v2__), 8)
        for metadata in artifacts.__artifacts_v2__.values():
            self.assertNotIn('sample_data', metadata)
            self.assertEqual(metadata['author'], '@AlexisBrignoni, Codex')


if __name__ == '__main__':
    unittest.main()
