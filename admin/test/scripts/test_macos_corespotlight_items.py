"""Pin the CoreSpotlight Items artifact (scripts/artifacts/macosCoreSpotlight.py).

Every store below is written by the Spotlight store test's writer: a file header, a map page, the
attribute tables as property pages or as dbStr-N.map files beside the store, and record pages. No value
comes from a real store. Expected values are literals.
"""
import fnmatch
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from admin.test.scripts.test_macos_spotlight_store import (  # pylint: disable=wrong-import-position
    Context, date, dates, page, raw_page, record, string, strings, sv, walk, write_store)
from scripts.artifacts import macosCoreSpotlight as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
INDEX = 'Users/pat/Library/Metadata/CoreSpotlight/index.spotlightV3/'
RECORDED = '/Users/pat/Library/Metadata/CoreSpotlight/index.spotlightV3/store.db'

# Attribute types: index -> (value type, property type, name).
TYPES = {
    1: (0x0B, 0x00, '_kMDItemBundleID'),
    2: (0x0C, 0x00, '_kMDItemInterestingDate'),
    3: (0x0C, 0x00, 'kMDItemContentCreationDate'),
    4: (0x0C, 0x00, 'kMDItemContentModificationDate'),
    5: (0x0C, 0x00, 'kMDItemLastUsedDate'),
    6: (0x0C, 0x02, 'kMDItemUsedDates'),
    7: (0x06, 0x08, 'kMDItemUseCount'),
    8: (0x0C, 0x00, 'kMDItemStartDate'),
    9: (0x0C, 0x00, 'kMDItemEndDate'),
    10: (0x0C, 0x00, 'com_apple_mail_dateReceived'),
    11: (0x0B, 0x00, 'kMDItemTitle'),
    12: (0x0B, 0x03, 'kMDItemDisplayName'),
    13: (0x0B, 0x00, 'kMDItemSubject'),
    14: (0x0B, 0x00, '_kMDItemSnippet'),
    15: (0x0B, 0x02, 'kMDItemAuthors'),
    16: (0x0B, 0x02, 'kMDItemAuthorAddresses'),
    17: (0x0B, 0x02, 'kMDItemAuthorEmailAddresses'),
    18: (0x0B, 0x02, 'kMDItemRecipients'),
    19: (0x0B, 0x02, 'kMDItemRecipientAddresses'),
    20: (0x0B, 0x02, 'kMDItemPrimaryRecipientEmailAddresses'),
    21: (0x0B, 0x02, 'kMDItemAccountHandles'),
    22: (0x00, 0x08, 'com_apple_mobilesms_fromMe'),
    23: (0x0B, 0x00, 'kMDItemContentURL'),
    24: (0x0B, 0x00, 'kMDItemDescription'),
    25: (0x0B, 0x00, '_kMDItemDomainIdentifier'),
    26: (0x0B, 0x00, '_kMDItemExternalID'),
    27: (0x0C, 0x00, '_kMDItemExpirationDate'),
    28: (0x0B, 0x00, '_kMDItemHelpTitle'),
    29: (0x0B, 0x00, 'kMDStoreUUID'),
}
HEADERS = [
    'Interesting Date (UTC)', 'Content Created (UTC)', 'Content Modified (UTC)', 'Last Used (UTC)',
    'Used Dates (UTC)', 'Use Count (as stored)', 'Start (UTC)', 'End (UTC)', 'Mail Received (UTC)', 'App', 'Title',
    'Display Name', 'Subject', 'Snippet', 'Authors', 'Author Addresses', 'Author Email Addresses', 'Recipients',
    'Recipient Addresses', 'Primary Recipient Email Addresses', 'Account Handles', 'From Me (as stored)',
    'Content URL', 'Description', 'Domain Identifier (as stored)', 'External ID (as stored)', 'Expiration (UTC)',
    'Record Updated (UTC)', 'User', 'Source File']


def item(identifier, updated, attributes):
    return record(identifier, 2, updated, attributes)


# A message, held the same way by both copies.
MESSAGE = item(20, 1766644919000000, [
    (1, string('com.apple.MobileSMS')), (2, date(788000000.0)), (3, date(788000000.0)), (5, date(788100000.0)),
    (6, dates(787968000.0, 788054400.0)), (7, sv(3)), (12, strings('', 'Pat\x16\x02', 'Pat\x16\x02fr')),
    (14, string('See you at noon')), (15, strings('Sam', '')), (16, strings('+15555550100')),
    (18, strings('Pat')), (19, strings('+15555550101')), (21, strings('+15555550101')), (22, sv(1)),
    (25, string('chat0')), (26, string('A1B2C3D4-0000-4000-8000-000000000001')), (27, date(790592000.0))])
# A mail item whose record the newer copy updated since the older copy was written.
MAIL_FIELDS = [
    (1, string('com.apple.mail')), (2, date(787950000.0)), (4, date(787950100.0)), (10, date(787950000.0)),
    (11, string('Quarterly report')), (13, string('Quarterly report')), (17, strings('sam@example.com')),
    (20, strings('pat@example.com')), (26, string('mail-42'))]
# A calendar event with no content dates.
EVENT = item(22, 1766644919000000, [
    (1, string('com.apple.CalendarUI')), (2, date(788200000.0)), (8, date(788200000.0)), (9, date(788203600.0)),
    (11, string('Dentist')), (23, string('https://example.com/event')), (24, string('Checkup'))])
# An item sharing the event's interesting date sorts after it by app, though written before it.
NOTE = item(24, 1766644919000000, [(1, string('com.apple.Notes')), (2, date(788200000.0)), (11, string('Groceries'))])
# An item with no interesting date sorts last.
CONTACT = item(23, 1766644919000000, [(1, string('com.apple.spotlight.contacts')), (12, strings('Sam\x16\x02'))])
HELP = item(30, 1766644919000000, [(1, string('com.apple.helpviewer')), (28, string('Use the Dock'))])
STORE_RECORD = item(1, 1766644919000000, [(29, string('0A1B2C3D-0000-4000-8000-000000000001'))])


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        for module in (artifact, sys.modules['scripts.macos_plists']):
            patcher = patch.object(module, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_artifact(self):
        return artifact.macosCoreSpotlightItems.__wrapped__(Context(self.root, walk(self.root)))

    def write(self, name, pages, folder=INDEX, tables='pages'):
        write_store(os.path.join(self.root, folder, name), pages, recorded=RECORDED, tables=tables, types=TYPES)

    def test_items(self):
        self.write('store.db', [raw_page(STORE_RECORD, MESSAGE, item(21, 5, MAIL_FIELDS), HELP, NOTE, EVENT, CONTACT)])
        # The newer copy names no table page: its tables come from the dbStr files beside it.
        self.write('.store.db', [raw_page(STORE_RECORD, MESSAGE, item(21, 6, MAIL_FIELDS), HELP, HELP, NOTE, EVENT, CONTACT)],
                   tables='dbstr')
        # A byte-identical copy under System/Volumes/Data is not read again.
        shutil.copytree(os.path.join(self.root, 'Users'), os.path.join(self.root, 'System/Volumes/Data/Users'))
        headers, rows, source = self.run_artifact()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers], HEADERS)
        both = f'{INDEX}store.db\n{INDEX}.store.db'
        blank = ''
        mail = (datetime(2025, 12, 20, 19, 0, tzinfo=UTC), blank, datetime(2025, 12, 20, 19, 1, 40, tzinfo=UTC), blank,
                blank, blank, blank, blank, datetime(2025, 12, 20, 19, 0, tzinfo=UTC), 'com.apple.mail',
                'Quarterly report', blank, 'Quarterly report', blank, blank, blank, 'sam@example.com', blank, blank,
                'pat@example.com', blank, blank, blank, blank, blank, 'mail-42', blank)
        self.assertEqual(rows, [
            # Sorted by interesting date, then app; the mail record updated between the two copies is a row per copy.
            mail + (datetime(1970, 1, 1, 0, 0, 0, 5, tzinfo=UTC), 'pat', INDEX + 'store.db'),
            mail + (datetime(1970, 1, 1, 0, 0, 0, 6, tzinfo=UTC), 'pat', INDEX + '.store.db'),
            (datetime(2025, 12, 21, 8, 53, 20, tzinfo=UTC), datetime(2025, 12, 21, 8, 53, 20, tzinfo=UTC), blank,
             datetime(2025, 12, 22, 12, 40, tzinfo=UTC), '2025-12-21 00:00:00\n2025-12-22 00:00:00', 3, blank, blank,
             blank, 'com.apple.MobileSMS', blank, 'Pat', blank, 'See you at noon', 'Sam', '+15555550100', blank,
             'Pat', '+15555550101', blank, '+15555550101', 1, blank, blank, 'chat0',
             'A1B2C3D4-0000-4000-8000-000000000001', datetime(2026, 1, 20, 8, 53, 20, tzinfo=UTC),
             datetime(2025, 12, 25, 6, 41, 59, tzinfo=UTC), 'pat', both),
            (datetime(2025, 12, 23, 16, 26, 40, tzinfo=UTC), blank, blank, blank, blank, blank,
             datetime(2025, 12, 23, 16, 26, 40, tzinfo=UTC), datetime(2025, 12, 23, 17, 26, 40, tzinfo=UTC), blank,
             'com.apple.CalendarUI', 'Dentist', blank, blank, blank, blank, blank, blank, blank, blank, blank, blank,
             blank, 'https://example.com/event', 'Checkup', blank, blank, blank,
             datetime(2025, 12, 25, 6, 41, 59, tzinfo=UTC), 'pat', both),
            (datetime(2025, 12, 23, 16, 26, 40, tzinfo=UTC),) + (blank,) * 8 + ('com.apple.Notes', 'Groceries')
            + (blank,) * 16 + (datetime(2025, 12, 25, 6, 41, 59, tzinfo=UTC), 'pat', both),
            (blank,) * 9 + ('com.apple.spotlight.contacts', blank, 'Sam') + (blank,) * 15
            + (datetime(2025, 12, 25, 6, 41, 59, tzinfo=UTC), 'pat', both)])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, INDEX, n) for n in ('store.db', '.store.db')))
        self.assertEqual(sorted(self.logged), sorted([
            'CoreSpotlight Items: 2 byte-identical copy(ies) under System/Volumes/Data or System/Volumes/Update/mnt1 not read again',
            f'CoreSpotlight Items: {INDEX}store.db: 1 Help Viewer record(s) and 1 record(s) with no app not reported',
            f'CoreSpotlight Items: {INDEX}.store.db: 2 Help Viewer record(s) and 1 record(s) with no app not reported']))

    def test_unreadable_page_and_not_a_store(self):
        bad = page(0x09, b'\x10\x11', uncompressed=100)
        self.write('store.db', [raw_page(item(20, 2 ** 60, [(1, string('com.apple.Notes'))])), bad])
        other = os.path.join(self.root, 'Users/sam/Library/Metadata/CoreSpotlight/index.spotlightV3/.store.db')
        os.makedirs(os.path.dirname(other))
        with open(other, 'wb') as handle:
            handle.write(bytes(36864))
        _headers, rows, _source = self.run_artifact()
        # An update time too large for a date leaves Record Updated blank.
        self.assertEqual([(row[9], row[27], row[28]) for row in rows], [('com.apple.Notes', '', 'pat')])
        self.assertEqual(sorted(self.logged), sorted([
            f'CoreSpotlight Items: {INDEX}store.db: 1 record page(s) not read, 0 record(s) not fully decoded',
            'CoreSpotlight Items: Users/sam/Library/Metadata/CoreSpotlight/index.spotlightV3/.store.db not read: '
            'not a Spotlight store database']))

    def test_declared_paths(self):
        paths = artifact.__artifacts_v2__['macosCoreSpotlightItems']['paths']
        for member in (INDEX + 'store.db', INDEX + '.store.db', INDEX + 'dbStr-1.map.data', INDEX + 'dbStr-5.map.offsets',
                       'System/Volumes/Data/' + INDEX + 'store.db'):
            self.assertTrue(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)
        knowledge = 'Users/pat/Library/Metadata/CoreSpotlight/SpotlightKnowledgeEvents/index.V2/sdb/12/cs_default/'
        for member in ('.Spotlight-V100/Store-V2/0A1B2C3D-0000-4000-8000-000000000001/store.db',
                       INDEX + 'live.0.indexHead', 'Users/pat/Library/Caches/store.db', knowledge + 'skg_store.db',
                       knowledge + '.skg_store.db', knowledge + 'skg_store.dbStr-1.map.data'):
            self.assertFalse(any(fnmatch.fnmatch(member, pattern) for pattern in paths), member)


if __name__ == '__main__':
    unittest.main()
