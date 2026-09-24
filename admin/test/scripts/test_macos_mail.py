"""Pin the recipient columns and the two-view handling of the Mail Messages artifact.

Two copies of one Envelope Index sit under Users/ and System/Volumes/Data/Users/, as a
logical extraction of a Mac can hold them, and differ in one message's read value. The
message both copies hold identically must come back once, from the Users/ copy; the message
whose values differ must come back from each copy. Recipient rows of type 0 and 1 go to To
and Cc in position order, and any other type is kept as stored. The expected values are
written out, never read back from the code.
"""
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosMail  # pylint: disable=wrong-import-position

USERS = 'Users/someone/Library/Mail/V10/MailData/Envelope Index'
DATA_VIEW = 'System/Volumes/Data/' + USERS


def _index(path, second_read):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript('''
        CREATE TABLE messages (ROWID INTEGER PRIMARY KEY, date_received INTEGER, date_sent INTEGER,
            sender INTEGER, subject_prefix TEXT, subject INTEGER, summary INTEGER, mailbox INTEGER,
            read INTEGER, flagged INTEGER, deleted INTEGER, size INTEGER, conversation_id INTEGER);
        CREATE TABLE addresses (ROWID INTEGER PRIMARY KEY, address TEXT, comment TEXT);
        CREATE TABLE subjects (ROWID INTEGER PRIMARY KEY, subject TEXT);
        CREATE TABLE summaries (ROWID INTEGER PRIMARY KEY, summary TEXT);
        CREATE TABLE mailboxes (ROWID INTEGER PRIMARY KEY, url TEXT);
        CREATE TABLE recipients (ROWID INTEGER PRIMARY KEY, message INTEGER NOT NULL,
            address INTEGER NOT NULL, type INTEGER, position INTEGER);
        CREATE TABLE attachments (ROWID INTEGER PRIMARY KEY, message INTEGER, name TEXT);
        INSERT INTO addresses VALUES (1, 'sender@example.com', 'Sender'), (2, 'a@example.com', ''),
            (3, 'b@example.com', ''), (4, 'c@example.com', ''), (5, 'd@example.com', '');
        INSERT INTO subjects VALUES (1, 'Hello');
        INSERT INTO mailboxes VALUES (1, 'imap://mailbox');
        INSERT INTO recipients (message, address, type, position) VALUES
            (1, 3, 0, 1), (1, 2, 0, 0), (1, 4, 1, 0), (1, 5, 2, 0), (2, 4, 0, 0);
    ''')
    db.execute('INSERT INTO messages VALUES (1, 1700000000, 1700000000, 1, "", 1, NULL, 1, 1, 0, 0, 10, 7)')
    db.execute('INSERT INTO messages VALUES (2, 1700000100, 1700000100, 1, "Re: ", 1, NULL, 1, ?, 0, 0, 20, 7)',
               (second_read,))
    db.commit()
    db.close()


class MailMessagesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        _index(self.root / USERS, 0)
        _index(self.root / DATA_VIEW, 1)
        self.context = SimpleNamespace(
            get_files_found=lambda: [str(self.root / DATA_VIEW), str(self.root / USERS)],
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())

    def tearDown(self):
        self._tmp.cleanup()

    def test_recipients_split_and_identical_rows_from_the_second_view_collapse(self):
        with mock.patch.object(macosMail, 'logfunc') as log, mock.patch.object(macos_plists, 'logfunc'):
            headers, rows, _source = macosMail.macosMailMessages.__wrapped__(self.context)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        pick = ('Message Row ID', 'To', 'Cc', 'Other Recipients (type as stored)', 'Read (as stored)',
                'Source File')
        got = sorted(tuple(row[names.index(c)] for c in pick) for row in rows)
        self.assertEqual(got, [
            ('1', 'a@example.com; b@example.com', 'c@example.com', 'd@example.com (type 2)', '1', USERS),
            ('2', 'c@example.com', '', '', '0', USERS),
            ('2', 'c@example.com', '', '', '1', DATA_VIEW),
        ])
        self.assertEqual([call.args[0] for call in log.call_args_list], [
            'Mail Messages: 1 message row(s) another copy of the Envelope Index already gave, '
            'identical in every column but Source File, reported once'])


if __name__ == '__main__':
    unittest.main()
