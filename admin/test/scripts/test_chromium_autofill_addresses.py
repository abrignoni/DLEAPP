"""Pin the address readers in scripts/artifacts/chromiumAutofill.py.

The tables follow the Web Data schemas measured on registered images: autofill_profiles
and its name, email and phone side tables (versions 60 and 104), local_addresses and
contact_info with their type token tables (version 120), addresses and
address_type_tokens (version 135). Expected values are written out.
"""
import pathlib
import sqlite3
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumAutofill as af  # pylint: disable=wrong-import-position
from scripts.chromium.browser_profiles import Store  # pylint: disable=wrong-import-position

STORE = Store('/staged/Web Data', 'Users/u/AppData/Local/Google/Chrome/User Data/Default/Web Data',
              'Google Chrome', 'Default', 'u', 'container', 'Web Data')
TAIL = ('Google Chrome', 'Default', 'u', STORE.relative)


def _legacy_db():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE autofill_profiles (guid VARCHAR PRIMARY KEY, company_name VARCHAR, '
               'street_address VARCHAR, dependent_locality VARCHAR, city VARCHAR, state VARCHAR, '
               'zipcode VARCHAR, sorting_code VARCHAR, country_code VARCHAR, '
               'date_modified INTEGER NOT NULL DEFAULT 0, origin VARCHAR DEFAULT \'\', '
               'language_code VARCHAR, use_count INTEGER NOT NULL DEFAULT 0, '
               'use_date INTEGER NOT NULL DEFAULT 0, label VARCHAR)')
    db.execute('CREATE TABLE autofill_profile_names (guid VARCHAR, first_name VARCHAR, '
               'middle_name VARCHAR, last_name VARCHAR, full_name VARCHAR)')
    db.execute('CREATE TABLE autofill_profile_emails (guid VARCHAR, email VARCHAR)')
    db.execute('CREATE TABLE autofill_profile_phones (guid VARCHAR, number VARCHAR)')
    db.execute("INSERT INTO autofill_profiles VALUES ('g1', 'Org', '1 Main St', '', 'Town', 'ST', "
               "'00001', '', 'US', 200, '', 'en', 3, 300, 'home')")
    db.execute("INSERT INTO autofill_profiles (guid, city, date_modified) VALUES ('g2', 'Other', 0)")
    db.execute("INSERT INTO autofill_profile_names VALUES ('g1', 'A', '', 'B', 'A B')")
    db.executemany('INSERT INTO autofill_profile_emails VALUES (?, ?)',
                   [('g1', 'one@example.com'), ('g1', 'two@example.com')])
    db.execute("INSERT INTO autofill_profile_phones VALUES ('g1', X'0102')")
    return db


def _token_db(meta, tokens, record_type_column):
    db = sqlite3.connect(':memory:')
    extra = ', record_type INTEGER' if record_type_column else ''
    db.execute(f'CREATE TABLE {meta} (guid VARCHAR PRIMARY KEY, use_count INTEGER NOT NULL DEFAULT 0, '
               f'use_date INTEGER NOT NULL DEFAULT 0, date_modified INTEGER NOT NULL DEFAULT 0, '
               f'language_code VARCHAR, label VARCHAR{extra})')
    db.execute(f'CREATE TABLE {tokens} (guid VARCHAR, type INTEGER, value VARCHAR, '
               f'PRIMARY KEY (guid, type))')
    if record_type_column:
        db.execute(f"INSERT INTO {meta} VALUES ('g3', 1, 500, 400, '', '', 1)")
    else:
        db.execute(f"INSERT INTO {meta} VALUES ('g3', 1, 500, 400, '', '')")
    db.executemany(f'INSERT INTO {tokens} VALUES (?, ?, ?)', [
        ('g3', 7, 'Full Name'), ('g3', 3, 'Full'), ('g3', 36, 'CA'), ('g3', 999, 'later'),
        ('g3', 33, '')])
    return db


class LegacyAddressesTest(unittest.TestCase):
    def test_one_row_per_profile_with_side_tables_joined(self):
        rows = af._legacy_addresses(_legacy_db(), STORE)  # pylint: disable=protected-access
        self.assertEqual(len(rows), 2)
        by_city = {row[6]: row for row in rows}
        full = by_city['Town']
        self.assertEqual(full[2:16], (3, 'A B', 'Org', '1 Main St', 'Town', 'ST', '00001', 'US',
                                      'one@example.com; two@example.com', '[2 bytes, not decoded]',
                                      'NAME_FIRST: A; NAME_LAST: B', '', 'home', 'autofill_profiles'))
        self.assertEqual(full[16:], TAIL)
        self.assertEqual(full[0].timestamp(), 300)
        self.assertEqual(full[1].timestamp(), 200)

    def test_full_name_with_honorific_prefix_goes_to_other_values(self):
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE autofill_profiles (guid VARCHAR PRIMARY KEY, use_date INTEGER, '
                   'date_modified INTEGER, use_count INTEGER)')
        db.execute('CREATE TABLE autofill_profile_names (guid VARCHAR, full_name VARCHAR, '
                   'full_name_with_honorific_prefix VARCHAR)')
        db.execute("INSERT INTO autofill_profiles VALUES ('g1', 0, 0, 1)")
        db.execute("INSERT INTO autofill_profile_names VALUES ('g1', 'A B', 'Dr A B')")
        rows = af._legacy_addresses(db, STORE)  # pylint: disable=protected-access
        self.assertEqual(rows[0][3], 'A B')
        self.assertEqual(rows[0][12], 'NAME_FULL_WITH_HONORIFIC_PREFIX (deprecated): Dr A B')

    def test_zero_dates_are_blank(self):
        rows = af._legacy_addresses(_legacy_db(), STORE)  # pylint: disable=protected-access
        bare = {row[6]: row for row in rows}['Other']
        self.assertEqual((bare[0], bare[1]), ('', ''))
        self.assertEqual(bare[3], '')


class TokenAddressesTest(unittest.TestCase):
    def test_addresses_table_record_type_and_other_values(self):
        db = _token_db('addresses', 'address_type_tokens', True)
        rows = af._token_addresses(db, STORE, 'addresses', 'address_type_tokens', None)  # pylint: disable=protected-access
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[3], 'Full Name')
        self.assertEqual(row[9], 'CA')
        self.assertEqual(row[6], '')
        self.assertEqual(row[12], 'NAME_FIRST: Full; type 999: later')
        self.assertEqual(row[13], 'kAccount (1)')
        self.assertEqual(row[15], 'addresses')

    def test_legacy_token_tables_take_their_table_record_type(self):
        db = _token_db('contact_info', 'contact_info_type_tokens', False)
        rows = af._token_addresses(db, STORE, 'contact_info', 'contact_info_type_tokens',  # pylint: disable=protected-access
                                   'kAccount or kAccountHome or kAccountWork')
        self.assertEqual(rows[0][13], 'kAccount or kAccountHome or kAccountWork')

    def test_missing_tables_yield_nothing(self):
        db = sqlite3.connect(':memory:')
        self.assertEqual(af._token_addresses(db, STORE, 'addresses', 'address_type_tokens', None), [])  # pylint: disable=protected-access
        self.assertEqual(af._legacy_addresses(db, STORE), [])  # pylint: disable=protected-access


class FieldTypesTest(unittest.TestCase):
    def test_shown_types_are_named(self):
        self.assertEqual([af._FIELD_TYPES[t] for t in af._SHOWN_TYPES], [  # pylint: disable=protected-access
            'NAME_FULL', 'COMPANY_NAME', 'ADDRESS_HOME_STREET_ADDRESS', 'ADDRESS_HOME_CITY',
            'ADDRESS_HOME_STATE', 'ADDRESS_HOME_ZIP', 'ADDRESS_HOME_COUNTRY', 'EMAIL_ADDRESS',
            'PHONE_HOME_WHOLE_NUMBER'])

    def test_record_types(self):
        self.assertEqual(af._RECORD_TYPES, {0: 'kLocalOrSyncable', 1: 'kAccount', 2: 'kAccountHome',  # pylint: disable=protected-access
                                            3: 'kAccountWork', 4: 'kAccountNameEmail'})


if __name__ == '__main__':
    unittest.main()
